import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from normalize import CYRILLIC, normalize_text
from parsers.bank423 import parse

SOURCE = ROOT / 'sources/Банк вопросов — лингвострановедение (423, с ответами).docx'


class TranslationsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.translations = json.loads((ROOT / 'data/translations.json').read_text('utf-8'))
        cls.records = parse(SOURCE)

    def test_keyed_by_normalised_chinese(self):
        key = normalize_text('现在中国的人口总数是多少？')
        self.assertEqual(self.translations[key], 'Какова общая численность населения Китая в настоящее время?')

    def test_covers_every_chinese_only_question(self):
        missing = [r['questionZh'] for r in self.records
                   if r['questionRu'] is None and normalize_text(r['questionZh']) not in self.translations]
        self.assertEqual(missing, [], f'без перевода осталось {len(missing)} вопросов')

    def test_every_translation_is_russian(self):
        for chinese, russian in self.translations.items():
            self.assertTrue(CYRILLIC.search(russian), chinese)


if __name__ == '__main__':
    unittest.main()
