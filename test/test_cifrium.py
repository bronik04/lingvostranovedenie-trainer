import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from parsers.cifrium import parse

PAPER = ROOT / 'sources/Муниципальный этап 2026-27, 9–11 классы (Цифриум).pdf'


class CifriumTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = parse(PAPER, year='2026-27')

    def test_reads_only_the_country_studies_section(self):
        self.assertEqual([r['number'] for r in self.records], list(range(1, 11)))
        self.assertEqual({r['year'] for r in self.records}, {'2026-27'})
        self.assertEqual({r['stageCode'] for r in self.records}, {'mun'})
        self.assertEqual({r['grades'] for r in self.records}, {'9-11'})

    def test_follows_the_raw_contract(self):
        required = {'sourceFile', 'year', 'stage', 'stageCode', 'grades', 'number',
                    'questionRu', 'questionZh', 'options', 'officialKeyIndex', 'topic', 'parseWarnings',
                    'sourceOrdinal'}
        for record in self.records:
            self.assertEqual(set(record), required)
            self.assertEqual(record['parseWarnings'], [], record['questionRu'])

    def test_key_is_the_option_marked_green(self):
        keys = [r['options'][r['officialKeyIndex']] for r in self.records]
        self.assertEqual(keys, ['丝绸', '戈壁', '1958', '特别行政区', '教师节', '1905 年',
                                '邓小平', '火', '在恰克图', '伞'])

    def test_kangxi_radicals_become_ordinary_characters(self):
        """Шрифт выгрузки отдаёт 大, 火, 马 знаками-ключами (⼤, ⽕, ⻢) — в банк они попасть не должны."""
        first, desert = self.records[0], self.records[1]
        self.assertEqual(first['questionRu'], 'Что из перечисленного НЕ является одним из «四大发明» Древнего Китая?')
        self.assertEqual(first['options'], ['印刷术', '丝绸', '指南针', '火药'])
        self.assertEqual(desert['options'], ['阿塔卡马利亚', '戈壁', '撒哈拉', '那泊'])

    def test_multiline_question_is_joined_without_instruction(self):
        deng = self.records[6]
        self.assertEqual(deng['questionRu'],
                         'Имя какого политического деятеля связано с началом проведения в КНР политики «改革开放»？')
        self.assertTrue(all('Выберите верный' not in r['questionRu'] for r in self.records))


if __name__ == '__main__':
    unittest.main()
