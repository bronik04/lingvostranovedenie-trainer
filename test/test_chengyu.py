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

    def test_tampered_option_is_caught(self):
        record = copy.deepcopy(self.olympiad[0])
        record['options'][1]['text'] = 'Такого варианта в бланке нет'
        self.assertTrue(any('нет варианта' in m for m in chengyu.check_sources([record])))

    def test_visual_keys_are_few_and_listed(self):
        self.assertLessEqual(len(chengyu.visual_keys(self.olympiad)), 4)


if __name__ == '__main__':
    unittest.main()
