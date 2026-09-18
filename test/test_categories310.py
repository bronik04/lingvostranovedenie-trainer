import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from parsers.categories310 import parse

SOURCE = ROOT / 'sources/Вопросы по категориям (310 шт).docx'
TOPICS = {
    'География и административное устройство',
    'Россия и межкультурный блок',
    'Литература, язык, искусство и философия',
    'История и государство',
    'Общество: население, этносы и религии',
    'Экономика, образование, наука и спорт',
    'Культура, традиции и праздники',
}


class Categories310Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = parse(SOURCE)

    def test_parses_every_question(self):
        self.assertEqual(len(self.records), 310)

    def test_every_record_carries_one_of_seven_topics(self):
        self.assertEqual({r['topic'] for r in self.records}, TOPICS)

    def test_year_is_normalised_to_short_form(self):
        self.assertTrue(all(len(r['year']) == 7 and r['year'][4] == '-' for r in self.records))

    def test_holds_the_whole_wording_cut_in_bank423(self):
        wanted = 'Административный центр провинции Цзянсу, одна из четырех древних столиц Китая.'
        self.assertIn(wanted, [r['questionRu'] for r in self.records])

    def test_questions_are_russian_and_options_chinese(self):
        for record in self.records:
            self.assertIsNotNone(record['questionRu'], record['number'])
            self.assertEqual(len(record['options']), 4, record['number'])

    def test_stage_codes_are_known(self):
        self.assertTrue({r['stageCode'] for r in self.records} <= {'pri', 'shk', 'mun', 'reg', 'zak'})


if __name__ == '__main__':
    unittest.main()
