import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from parsers.cifrium import _is_key, _joined, parse, records

PAPER = ROOT / 'sources/Муниципальный этап 2026-27, 9–11 классы (Цифриум).pdf'


def task(*options):
    """Строки одного задания раздела: (левый край, текст, отмечена ли зелёным)."""
    return [(125, 'Муниципальный этап по китайскому языку', False), (125, 'Китайский язык. 9–11 классы.', False),
            (125, 'ЛИНГВОСТРАНОВЕДЕНИЕ / 国情知识 #1', False), (125, 'Какая пустыня расположена в Китае?', False),
            *((170, text, marked) for text, marked in options), (125, 'За решение задачи 1 балл', False)]


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


class CifriumRulesTest(unittest.TestCase):
    def test_space_comes_from_the_gap_not_from_the_piece(self):
        """Другая версия poppler может отдать «1905» без хвостового пробела — вариант не должен слипнуться."""
        self.assertEqual(_joined([(1, 294, 170, 32, '1905', True), (1, 297, 210, 18, '年', True)]), '1905 年')
        self.assertEqual(_joined([(1, 294, 170, 40, '1905 ', True), (1, 297, 210, 18, '年', True)]), '1905 年')
        self.assertEqual(_joined([(1, 389, 170, 18, '邓', True), (1, 389, 188, 36, '小平', True)]), '邓小平')

    def test_any_green_marks_the_key(self):
        self.assertTrue(_is_key('#85d16a'))
        self.assertTrue(_is_key('#7ec82e'))  # зелёный ключей ЛГ-теста в той же выгрузке
        for color in ('#333333', '#404040', '#1a95f6', '#000000', ''):
            self.assertFalse(_is_key(color), color)

    def test_unreadable_task_is_flagged_not_guessed(self):
        both = records(task(('戈壁', True), ('撒哈拉', True), ('纳米布', False), ('阿塔卡马', False)), 'x.pdf', '2026-27')
        self.assertIsNone(both[0]['officialKeyIndex'])
        self.assertIn('отмечено вариантов: 2', both[0]['parseWarnings'])
        radical = records(task(('戈壁', True), ('⺁', False), ('纳米布', False), ('阿塔卡马', False)), 'x.pdf', '2026-27')
        self.assertIn('знаки-ключи без замены: ⺁', radical[0]['parseWarnings'])
        self.assertEqual((radical[0]['stageCode'], radical[0]['grades']), ('mun', '9-11'))


if __name__ == '__main__':
    unittest.main()
