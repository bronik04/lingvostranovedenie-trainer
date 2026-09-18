import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from docx_text import paragraphs
from parsers.vsosh import parse, parse_keys

SOURCE = ROOT / 'sources/Лингвострановедение ВсОШ.docx'


class VsoshKeysTest(unittest.TestCase):
    def test_reads_key_table_rows(self):
        keys = parse_keys([
            '2024–2025 уч. г.',
            'Региональный этап: 1—B, 2—C, 3—A, 4—A, 5—D',
            '2025–2026 уч. г.',
            'Школьный этап: 28—B, 29—C',
        ])
        self.assertEqual(keys[('2024-25', 'reg', 1)], 1)
        self.assertEqual(keys[('2024-25', 'reg', 4)], 0)
        self.assertEqual(keys[('2025-26', 'shk', 29)], 2)

    def test_ignores_the_note_about_missing_keys(self):
        keys = parse_keys(['Примечание: ответы отсутствуют или неполные для этапов: 15-16 — Заключительный'])
        self.assertEqual(keys, {})


class VsoshParseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = parse(SOURCE)

    def test_parses_about_three_hundred_questions(self):
        self.assertGreaterEqual(len(self.records), 300)

    def test_first_record_carries_year_stage_and_number(self):
        first = self.records[0]
        self.assertEqual(first['year'], '2015-16')
        self.assertEqual(first['stageCode'], 'shk')
        self.assertEqual(first['number'], 56)
        self.assertEqual(first['questionZh'], '现在中国的人口总数是多少？')

    def test_keys_are_attached_where_the_table_has_them(self):
        with_keys = [r for r in self.records if r['officialKeyIndex'] is not None]
        self.assertGreater(len(with_keys), 100)

    def test_every_record_has_four_options(self):
        for record in self.records:
            self.assertEqual(len(record['options']), 4, (record['year'], record['number']))


if __name__ == '__main__':
    unittest.main()
