import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from docx_text import paragraphs
from parsers.bank423 import parse

SOURCE = ROOT / 'sources/Банк вопросов — лингвострановедение (423, с ответами).docx'


class DocxTextTest(unittest.TestCase):
    def test_reads_paragraphs_without_python_docx(self):
        lines = paragraphs(SOURCE)
        self.assertGreater(len(lines), 1000)
        self.assertEqual(lines[0], 'БАНК ЗАДАНИЙ: ЛИНГВОСТРАНОВЕДЕНИЕ')
        self.assertTrue(all(line == line.strip() for line in lines))


class Bank423Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = parse(SOURCE)

    def test_parses_every_question(self):
        self.assertEqual(len(self.records), 423)

    def test_first_record_is_complete(self):
        first = self.records[0]
        self.assertIsNone(first['number'])  # номер в бланке из этого файла неизвестен
        self.assertEqual(first['sourceOrdinal'], 1)
        self.assertEqual(first['year'], '2015-16')
        self.assertEqual(first['stage'], 'школьный')
        self.assertEqual(first['stageCode'], 'shk')
        self.assertEqual(first['grades'], '9-11')
        self.assertEqual(first['questionZh'], '现在中国的人口总数是多少？')
        self.assertIsNone(first['questionRu'])
        self.assertEqual(first['options'], ['接近 20 亿', '接近 1 亿', '接近 15 亿', '超过 18 亿'])
        self.assertEqual(first['officialKeyIndex'], 2)

    def test_keeps_the_first_letter_of_russian_questions(self):
        """Старый импортёр съедал первый символ: 'дминистративный центр…'."""
        russian = [r['questionRu'] for r in self.records if r['questionRu']]
        self.assertTrue(any(q.startswith('Административный центр провинции Цзянсу') for q in russian))
        self.assertFalse(any(q[0].islower() for q in russian))

    def test_missing_key_becomes_none(self):
        without_key = [r for r in self.records if r['officialKeyIndex'] is None]
        self.assertEqual(len(without_key), 118)

    def test_two_known_broken_option_lines_are_reported_not_silently_padded(self):
        """В источнике две испорченные строки вариантов — парсер обязан о них сказать."""
        broken = [r for r in self.records if not all(option.strip() for option in r['options'])]
        self.assertEqual(len(broken), 2)
        for record in broken:
            self.assertEqual(len(record['options']), 4, record['number'])
            self.assertTrue(record['parseWarnings'], record['number'])

    def test_repeated_letter_does_not_overwrite_the_first_option(self):
        """Строка 'A) 兵马俑 B) 十三陵 C) 大唐芙蓉园 A) 大唐芙蓉园': первый вариант остаётся 兵马俑."""
        record = next(r for r in self.records if '兵马俑' in ' '.join(r['options']))
        self.assertEqual(record['options'][0], '兵马俑')
        self.assertIn('буква варианта повторяется: A', record['parseWarnings'])

    def test_every_other_record_has_four_filled_options(self):
        healthy = [r for r in self.records if not r['parseWarnings']]
        self.assertEqual(len(healthy), 421)
        for record in healthy:
            self.assertEqual(len(record['options']), 4, record['number'])
            self.assertTrue(all(option.strip() for option in record['options']), record['number'])


if __name__ == '__main__':
    unittest.main()
