import copy
import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import chengyu  # noqa: E402

GOOD = {
    'id': 'cy-一举两得', 'kind': 'analog', 'chengyu': '一举两得', 'pinyin': 'yī jǔ liǎng dé',
    'options': [{'id': 'A', 'text': 'раз'}, {'id': 'B', 'text': 'два'},
                {'id': 'C', 'text': 'три'}, {'id': 'D', 'text': 'четыре'}],
    'answer': 'C', 'group': 'measure', 'literal': 'буквально', 'meaning': 'смысл', 'trap': 'ловушка',
    'occurrences': [{'year': '2018-19', 'stageCode': 'zak', 'number': 15, 'keyCheck': 'table',
                     'instruction': 'Подберите аналог фразеологизму в русском языке',
                     'tasks': 'a.pdf', 'answers': 'b.pdf'}],
}
DRAFT = {key: value for key, value in GOOD.items() if key != 'occurrences'} | {
    'id': 'cy-画蛇添足', 'chengyu': '画蛇添足', 'status': 'draft'}


class ValidateTest(unittest.TestCase):
    def errors(self, olympiad=(), drafts=()):
        return chengyu.validate(list(olympiad), list(drafts))

    def test_good_records_pass(self):
        self.assertEqual(self.errors([GOOD], [DRAFT]), [])

    def test_broken_records_are_reported(self):
        cases = {
            'тема вне списка': {'group': 'другое'},
            'четырёх иероглифов': {'chengyu': '一举两', 'id': 'cy-一举两'},
            'id должен быть': {'id': 'cy-другое'},
            'одной из букв': {'answer': 'E'},
            'A, B, C, D': {'options': GOOD['options'][:3]},
            'повторяющийся вариант': {'options': [dict(o, text='раз') for o in GOOD['options']]},
            'без occurrences': {'occurrences': []},
            'keyCheck': {'occurrences': [dict(GOOD['occurrences'][0], keyCheck='угадано')]},
            'формулировки задания': {'occurrences': [dict(GOOD['occurrences'][0], instruction='')]},
            'у обратного задания ответ': {'kind': 'reverse', 'prompt': 'Пословица', 'answer': 'E'},
        }
        for expected, change in cases.items():
            with self.subTest(expected):
                messages = self.errors([GOOD | change])
                self.assertTrue(any(expected in m for m in messages), messages)

    def test_reverse_needs_prompt_and_glosses(self):
        reverse = copy.deepcopy(GOOD) | {'kind': 'reverse', 'chengyu': '细水长流', 'id': 'cy-细水长流'}
        reverse['options'] = [{'id': 'A', 'text': '马到成功'}, {'id': 'B', 'text': '细水长流'},
                              {'id': 'C', 'text': '三长两短'}, {'id': 'D', 'text': '马不停蹄'}]
        reverse['answer'] = 'B'
        messages = self.errors([reverse])
        self.assertTrue(any('prompt' in m for m in messages))
        self.assertTrue(any('нет подписи' in m for m in messages))

    def test_draft_rules(self):
        self.assertTrue(any('принятый черновик' in m for m in self.errors(drafts=[DRAFT | {'status': 'accepted'}])))
        self.assertTrue(any('status' in m for m in self.errors(drafts=[DRAFT | {'status': 'готово'}])))

    def test_draft_cannot_repeat_olympiad_chengyu(self):
        clash = DRAFT | {'id': GOOD['id'], 'chengyu': GOOD['chengyu']}
        self.assertTrue(any('повторяющийся id' in m for m in self.errors([GOOD], [clash])))

    def test_only_accepted_drafts_are_published(self):
        accepted = DRAFT | {'status': 'accepted', 'check': {'verdict': 'accept', 'note': ''}}
        unchecked = DRAFT | {'id': 'cy-亡羊补牢', 'chengyu': '亡羊补牢', 'status': 'accepted'}
        ids = [r['id'] for r in chengyu.published([GOOD], [DRAFT, accepted, unchecked])]
        self.assertEqual(ids, [GOOD['id'], accepted['id']])


class RealDataTest(unittest.TestCase):
    def test_project_data_is_valid(self):
        olympiad, drafts = chengyu.load('olympiad.json'), chengyu.load('drafts.json')
        self.assertEqual(len(olympiad), 35)
        self.assertEqual(chengyu.validate(olympiad, drafts), [])
        # принятые составленные — только с вердиктом проверки и словарными источниками
        for draft in drafts:
            if draft['status'] == 'accepted':
                self.assertEqual(draft['check']['verdict'], 'accept', draft['id'])
                self.assertTrue(draft.get('sources'), draft['id'])


@unittest.skipUnless(shutil.which('pdftotext') and shutil.which('pdftohtml'), 'нужен poppler (pdftotext, pdftohtml)')
class SourcesTest(unittest.TestCase):
    """Сверка с бланками олимпиады в sources/chengyu/."""

    def setUp(self):
        self.olympiad = chengyu.load('olympiad.json')

    def test_every_task_matches_its_pdf(self):
        self.assertEqual(chengyu.check_sources(self.olympiad), [])

    def test_tampered_key_is_caught(self):
        for record in self.olympiad:
            for occurrence in record['occurrences']:
                if occurrence['keyCheck'] == 'visual':
                    continue
                with self.subTest(record=record['id'], year=occurrence['year']):
                    wrong = 'A' if record['answer'] != 'A' else 'B'
                    tampered = record | {'answer': wrong, 'occurrences': [occurrence]}
                    messages = chengyu.check_sources([tampered])
                    self.assertTrue(messages, 'подменённый ключ прошёл проверку')

    def tampered(self, change):
        """Каждое появление с изменением change; возвращает те, что прошли проверку."""
        missed = []
        for record in self.olympiad:
            for occurrence in record['occurrences']:
                one = copy.deepcopy(record | {'occurrences': [occurrence]})
                change(one)
                if not chengyu.check_sources([one]):
                    missed.append(f'{record["id"]} {occurrence["year"]}')
        return missed

    def test_swapped_answer_text_is_caught(self):
        # буква ключа прежняя, но под ней другой текст: таблица ключей этого не видит,
        # поэтому порядок вариантов сверяется с бланком
        def swap(record):
            i = chengyu.LETTERS.index(record['answer'])
            j = (i + 1) % 4
            options = record['options']
            options[i]['text'], options[j]['text'] = options[j]['text'], options[i]['text']
        self.assertEqual(self.tampered(swap), [])

    def test_wrong_task_number_is_caught(self):
        def shift(record):
            record['occurrences'][0]['number'] += 1
        self.assertEqual(self.tampered(shift), [])

    def test_option_from_another_task_is_caught(self):
        record = copy.deepcopy(self.olympiad[0])
        other = next(r for r in self.olympiad[1:] if r['kind'] == record['kind'])
        record['options'][1]['text'] = other['options'][0]['text']
        self.assertTrue(chengyu.check_sources([record]))

    def test_visual_keys_are_few_and_listed_in_report(self):
        visual = chengyu.visual_keys(self.olympiad)
        self.assertLessEqual(len(visual), 4)
        report = (ROOT / 'data/review/chengyu.md').read_text('utf-8')
        for record in self.olympiad:
            for occurrence in record['occurrences']:
                if occurrence['keyCheck'] == 'visual':
                    line = f'{record["chengyu"]} — {occurrence["year"]}, {occurrence["stageCode"]}, задание {occurrence["number"]}'
                    self.assertIn(line, report)


if __name__ == '__main__':
    unittest.main()
