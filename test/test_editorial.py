import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from editorial import apply_editorial, validate_editorial


def record(**overrides):
    item = {
        'id': '2015-16-mun-1',
        'topic': 'История и государство',
        'topicSource': 'assigned',
        'questionRu': 'Как называлась самая ранняя династия Китая?',
        'questionZh': None,
        'options': [
            {'id': 'o1', 'zh': '夏'},
            {'id': 'o2', 'zh': '明'},
            {'id': 'o3', 'zh': '清'},
            {'id': 'o4', 'zh': '隋'},
        ],
        'answer': {'optionId': 'o1', 'state': 'verified'},
        'explanation': {'ru': 'Первой династией считается Ся.'},
    }
    item.update(overrides)
    return item


class EditorialTest(unittest.TestCase):
    def test_applies_question_option_explanation_and_topic(self):
        edits = {'2015-16-mun-1': {
            'reason': 'опечатка',
            'questionRu': 'Какая династия считается первой в истории Китая?',
            'options': {'o4': '秦'},
            'explanation': 'Первой династией считается Ся (夏).',
            'topic': 'Культура, традиции и праздники',
        }}
        [result] = apply_editorial([record()], edits)
        self.assertEqual(result['questionRu'], 'Какая династия считается первой в истории Китая?')
        self.assertEqual([o['zh'] for o in result['options']], ['夏', '明', '清', '秦'])
        self.assertEqual(result['explanation']['ru'], 'Первой династией считается Ся (夏).')
        self.assertEqual(result['topic'], 'Культура, традиции и праздники')
        self.assertEqual(result['topicSource'], 'editorial')
        self.assertEqual(result['answer'], {'optionId': 'o1', 'state': 'verified'})
        self.assertEqual(result['editorial'], {'reason': 'опечатка'})

    def test_keeps_id_and_untouched_records(self):
        other = record(id='other')
        edits = {'2015-16-mun-1': {'reason': 'x', 'options': {'o2': '元'}}}
        result = apply_editorial([record(), other], edits)
        self.assertEqual([r['id'] for r in result], ['2015-16-mun-1', 'other'])
        self.assertIs(result[1], other)

    def test_rejects_invalid_edits(self):
        bank = [record()]
        self.assertTrue(validate_editorial({'missing': {'reason': 'x', 'options': {'o1': '夏'}}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x'}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'options': {'o2': '元'}}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'options': {'o9': '元'}}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'options': {'o2': 'Мин'}}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'options': {'o2': '夏'}}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'questionRu': '朝代？'}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'topic': 'Нет такой'}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'explanation': ' '}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'surprise': 1}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'explanation': 'Ся — — первая.'}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'explanation': 'Ся  первая.'}}, bank))

    def test_applies_chinese_question_text(self):
        edits = {'2015-16-mun-1': {'reason': 'опечатка в оригинале',
                                   'questionZh': '中国最早的王朝叫什么？'}}
        [result] = apply_editorial([record(questionZh='中国最早的王潮叫什么？')], edits)
        self.assertEqual(result['questionZh'], '中国最早的王朝叫什么？')

    def test_rejects_chinese_question_without_chinese(self):
        bank = [record(questionZh='中国最早的王潮叫什么？')]
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'questionZh': 'Какая?'}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'questionZh': ' '}}, bank))


class EditorialInBankTest(unittest.TestCase):
    """Каждая правка из data/review/editorial.json должна дойти до data/bank.json —
    в том числе правки дополнений, которые попадают в банк позже олимпиадных вопросов."""

    def test_every_edit_reaches_the_bank(self):
        edits = json.loads((ROOT / 'data/review/editorial.json').read_text('utf-8'))
        bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        merges = json.loads((ROOT / 'data/review/merges.json').read_text('utf-8'))
        absorbed = {record_id for item in merges.values() for record_id in item['absorbs']}
        # удалённая запись (retired.json) — правка остаётся в файле, но в банк не попадает
        retired_file = ROOT / 'data/review/retired.json'
        if retired_file.exists():
            absorbed |= set(json.loads(retired_file.read_text('utf-8')))
        # отложенное задание (withheld.json) — тоже: правка ждёт в файле, пока автор не снимет сомнение
        withheld_file = ROOT / 'data/review/withheld.json'
        if withheld_file.exists():
            absorbed |= set(json.loads(withheld_file.read_text('utf-8')))
        for record_id, edit in edits.items():
            if record_id in absorbed:
                # запись влита в другую склейкой дублей: правка сделала своё дело до склейки
                self.assertNotIn(record_id, bank)
                continue
            record = bank[record_id]
            self.assertEqual(record.get('editorial', {}).get('reason'), edit['reason'].strip(), record_id)
            if 'questionRu' in edit:
                self.assertEqual(record['questionRu'], edit['questionRu'], record_id)
            if 'questionZh' in edit:
                self.assertEqual(record['questionZh'], edit['questionZh'].strip(), record_id)
            if 'explanation' in edit:
                self.assertEqual(record['explanation']['ru'], edit['explanation'].strip(), record_id)
            if 'topic' in edit:
                self.assertEqual(record['topic'], edit['topic'], record_id)
                self.assertEqual(record['topicSource'], 'editorial', record_id)
            for option_id, text in edit.get('options', {}).items():
                option = next(o for o in record['options'] if o['id'] == option_id)
                self.assertEqual(option['zh'], text.strip(), record_id)


class QuestionHintsTest(unittest.TestCase):
    """Текст вопроса не подсказывает ответ: ученик в раунде видит только questionRu."""

    HINTS = {
        '2019-20-reg-5': '河',
        'addition-b1-08': '天京',
        'addition-b1-11': '神武门',
        '2022-23-reg-2': '高中',
    }

    def setUp(self):
        self.bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}

    def test_question_text_has_no_hint(self):
        for record_id, hint in self.HINTS.items():
            self.assertNotIn(hint, self.bank[record_id]['questionRu'], record_id)
        self.assertNotIn('玄烨', self.bank['addition-b1-11']['questionRu'])

    def test_huanghe_question_does_not_call_bohai_a_sea(self):
        # по-русски Бохай — залив Жёлтого моря, по-китайски — внутреннее море
        record = self.bank['2018-19-mun-52']
        self.assertNotIn('море', record['questionRu'])
        self.assertNotIn('海', record['questionZh'].replace('入海', ''))
        # Бохай по-русски — часть Жёлтого моря, так что 黄海 был бы вторым верным ответом
        self.assertNotIn('黄海', [option['zh'] for option in record['options']])


if __name__ == '__main__':
    unittest.main()
