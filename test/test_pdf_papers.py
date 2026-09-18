import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from parsers.pdf_papers import parse

MUNICIPAL = ROOT / 'sources/Лингвострановедение 2022-23 — Муниципальный.pdf'
LATEST = ROOT / 'sources/Лингвострановедение 2024-25.pdf'


class PdfPapersTest(unittest.TestCase):
    def test_reads_header_year_and_stage(self):
        records = parse(MUNICIPAL)
        self.assertTrue(records)
        self.assertEqual(records[0]['year'], '2022-23')
        self.assertEqual(records[0]['stageCode'], 'mun')
        self.assertEqual(records[0]['number'], 1)
        self.assertEqual(
            records[0]['questionRu'],
            'В каком климатическом поясе находится большая часть территории Китая?')
        self.assertEqual(records[0]['options'], ['赤道带', '热带', '寒带', '温带'])

    def test_handles_zadanie_numbering(self):
        records = parse(LATEST)
        numbers = {record['number'] for record in records}
        self.assertIn(28, numbers)
        first = next(r for r in records if r['number'] == 28)
        self.assertEqual(first['questionRu'], 'Кто считается основателем российского флота?')

    def test_never_invents_keys(self):
        self.assertTrue(all(r['officialKeyIndex'] is None for r in parse(MUNICIPAL)))

    def test_multiline_question_is_joined_whole(self):
        """В бланке формулировка переносится на несколько строк — она должна склеиться целиком."""
        records = parse(MUNICIPAL)
        third = next(r for r in records if r['number'] == 3)
        self.assertTrue(third['questionRu'].endswith('?'))
        self.assertIn('классическим', third['questionRu'].lower())


if __name__ == '__main__':
    unittest.main()
