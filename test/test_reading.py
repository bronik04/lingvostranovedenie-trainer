import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading import reading_links, validate_catalog


def link(title='Конфуций', url='https://ru.wikipedia.org/wiki/Конфуций'):
    return {'title': title, 'url': url}


def question(**extra):
    return {'id': 'q1', 'factRow': 'people/thinkers/kongzi', 'evidence': [], **extra}


class ReadingTest(unittest.TestCase):
    def test_question_link_overrides_row_and_evidence(self):
        chosen = link('Лунь юй', 'https://ru.wikipedia.org/wiki/Лунь_юй')
        catalog = {'questions': {'q1': chosen}, 'rows': {'people/thinkers/kongzi': link()}}
        self.assertEqual(reading_links([question(evidence=[link()])], catalog), {'q1': [chosen]})

    def test_reuses_links_for_fact_rows_without_mutating_bank(self):
        bank = [question(), question(id='q2', factRow=['people/thinkers/kongzi', 'unknown'])]
        before = copy.deepcopy(bank)
        result = reading_links(bank, {'rows': {'people/thinkers/kongzi': link()}})
        self.assertEqual(result, {'q1': [link()], 'q2': [link()]})
        self.assertEqual(bank, before)

    def test_prefers_russian_wikipedia_to_other_evidence(self):
        sources = [link('中文', 'https://example.org/article'), link()]
        self.assertEqual(reading_links([question(evidence=sources)], {}), {'q1': [link()]})

    def test_fallback_uses_existing_article_without_verification_metadata(self):
        source = {**link('Музей', 'https://museum.example.org/article'), 'checkedAt': '2026-11-07'}
        self.assertEqual(reading_links([question(evidence=[source])], {}),
                         {'q1': [link('Музей', 'https://museum.example.org/article')]})

    def test_omits_unsafe_or_missing_links_and_does_not_offer_pdf_as_reading(self):
        sources = [link(url='javascript:alert(1)'), link(url='https://example.org/paper.pdf'),
                   link(url='https://example.org/')]
        self.assertEqual(reading_links([question(evidence=sources), question(id='q2')], {}), {})

    def test_catalog_rejects_empty_titles_and_unsafe_urls(self):
        for invalid in [link(title=''), link(url='javascript:alert(1)'), link(url='//example.org'),
                        link(url='https://'), {'title': 'Без ссылки'}, 'не объект']:
            with self.subTest(invalid=invalid):
                self.assertTrue(validate_catalog({'questions': {'q1': invalid}}))
        self.assertEqual(validate_catalog({'rows': {'people/thinkers/kongzi': link()}}), [])

    def test_catalog_rejects_unknown_sections_and_non_maps(self):
        for invalid in [[], {'rows': []}, {'question': {}}, {'rows': {'': link()}}]:
            with self.subTest(invalid=invalid):
                self.assertTrue(validate_catalog(invalid))

    def test_published_questions_have_reading_without_changing_bank(self):
        from site_bank import embedded_by, load_settings, site_bank
        bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
        catalog = json.loads((ROOT / 'data/reading.json').read_text('utf-8'))
        self.assertEqual(validate_catalog(catalog), [])
        published = site_bank(bank, load_settings(), embedded_by())
        result = reading_links(published, catalog)
        self.assertEqual(set(result), {record['id'] for record in published})
        # Чтение не подменяет китайские источники проверки ключа русской энциклопедией.
        self.assertNotIn('reading', bank[0])

    def test_catalog_links_do_not_confuse_people_works_and_homonyms(self):
        catalog = json.loads((ROOT / 'data/reading.json').read_text('utf-8'))
        expected = {
            'cinema/works/cin-ru-potemkin': 'Броненосец «Потёмкин» (фильм)',
            'cinema/works/cin-cn-hero': 'Герой (фильм, 2002)',
            'literature/works/lit-w-ru-seagull': 'Чайка (пьеса)',
            'literature/works/lit-w-ru-mother': 'Мать (роман)',
            'nature/waters/wat-heilongjiang': 'Амур',
            'nature/engineering/eng-fast': 'FAST (радиотелескоп)',
            'cuisine/teas/te-qimen': 'Кимун',
            'cuisine/teas/te-longjing': 'Лунцзин (чай)',
        }
        for row, title in expected.items():
            with self.subTest(row=row):
                self.assertEqual(catalog['rows'][row]['title'], title)


if __name__ == '__main__':
    unittest.main()
