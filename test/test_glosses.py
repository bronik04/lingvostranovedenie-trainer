import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from glosses import apply_glosses, load_glosses, validate_glosses


def record(**overrides):
    item = {
        'id': '2015-16-zak-4',
        'questionRu': 'Как называлась первая единая централизованная феодальная династия в истории Китая?',
        'options': [{'id': 'o1', 'zh': '秦朝'}, {'id': 'o2', 'zh': '汉朝'},
                    {'id': 'o3', 'zh': '明朝'}, {'id': 'o4', 'zh': '夏朝'}],
        'answer': {'optionId': 'o1', 'state': 'verified'},
    }
    item.update(overrides)
    return item


def gloss(zh='汉朝', ru='Династия Хань, 206 г. до н. э. — 220 г.', **overrides):
    item = {'zh': zh, 'ru': ru, 'source': {'title': '汉朝 — 百科', 'url': 'https://example.org/han'}}
    item.update(overrides)
    return item


def entry(options):
    return {'reviewedAt': '2026-09-25', 'options': options}


class GlossesTest(unittest.TestCase):
    def test_puts_gloss_into_the_option(self):
        [result] = apply_glosses([record()], {'2015-16-zak-4': entry({'o2': gloss()})})
        self.assertEqual(result['options'][1], {'id': 'o2', 'zh': '汉朝',
                                                'gloss': 'Династия Хань, 206 г. до н. э. — 220 г.'})
        self.assertNotIn('gloss', result['options'][0])

    def test_keeps_untouched_records(self):
        other = record(id='other')
        result = apply_glosses([record(), other], {'2015-16-zak-4': entry({'o2': gloss()})})
        self.assertIs(result[1], other)

    def assertRejected(self, glosses, message, bank=None):
        errors = validate_glosses(glosses, bank or [record()])
        self.assertTrue(any(message in error for error in errors), f'{message!r} не найдено в {errors}')

    def test_accepts_a_valid_gloss(self):
        self.assertEqual(validate_glosses({'2015-16-zak-4': entry({'o2': gloss()})}, [record()]), [])

    def test_rejects_each_broken_rule(self):
        cases = [
            ({'missing': entry({'o2': gloss()})}, 'такой записи в банке нет'),
            ({'2015-16-zak-4': entry({'o9': gloss()})}, 'такого варианта нет'),
            ({'2015-16-zak-4': entry({'o1': gloss(zh='秦朝', ru='Династия Цинь')})}, 'у правильного варианта'),
            ({'2015-16-zak-4': entry({'o2': gloss(zh='汉代')})}, 'вариант изменился'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='Han dynasty')})}, 'не по-русски'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='   ')})}, 'не по-русски'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='Д' * 91)})}, 'длиннее 90'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='Династия Хань — — 206')})}, 'двойное тире'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='Династия  Хань')})}, 'лишние пробелы'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru=' Династия Хань')})}, 'лишние пробелы'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='Династия Хань\n206 г.')})}, 'не в одну строку'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='汉朝 — династия Хань')})}, 'повторяет сам вариант'),
            ({'2015-16-zak-4': entry({'o2': gloss(source={'title': 'x', 'url': 'javascript:alert(1)'})})}, 'нет источника'),
            ({'2015-16-zak-4': entry({'o2': gloss(source={'title': ' ', 'url': 'https://example.org'})})}, 'нет источника'),
            ({'2015-16-zak-4': entry({'o2': gloss(source={'title': 'x', 'url': 42})})}, 'нет источника'),
            ({'2015-16-zak-4': entry({'o2': {'zh': '汉朝', 'ru': 'Династия Хань'}})}, 'нет источника'),
            ({'2015-16-zak-4': entry({'o2': gloss(quote='цитата из черновика')})}, 'неизвестные поля'),
            ({'2015-16-zak-4': entry({'o2': 'Династия Хань'})}, 'должна быть объектом'),
            ({'2015-16-zak-4': {'options': {'o2': gloss()}}}, 'нет даты проверки'),
            ({'2015-16-zak-4': {**entry({'o2': gloss()}), 'skip': 'x'}}, 'неизвестные поля'),
            ({'2015-16-zak-4': entry({})}, 'нет ни одной подписи'),
            ({'2015-16-zak-4': 'Династия Хань'}, 'должна быть объектом'),
            ([], 'словарём'),
        ]
        for glosses, message in cases:
            with self.subTest(message=message):
                self.assertRejected(glosses, message)

    def test_rejects_gloss_for_question_without_verified_answer(self):
        unverified = record(answer={'optionId': None, 'state': 'needs-review'})
        self.assertRejected({'2015-16-zak-4': entry({'o2': gloss()})}, 'без проверенного ответа', [unverified])

    def test_duplicate_keys_in_file_are_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'glosses.json'
            path.write_text('{"2015-16-zak-4": {"reviewedAt": "x", "options": {"o2": {}, "o2": {}}}}', 'utf-8')
            with self.assertRaises(ValueError):
                load_glosses(path)

    def test_changed_option_text_stops_the_build(self):
        with self.assertRaises(ValueError):
            apply_glosses([record()], {'2015-16-zak-4': entry({'o2': gloss(zh='汉代')})})


class GlossesInBankTest(unittest.TestCase):
    """Каждая подпись из data/review/glosses.json должна дойти до data/bank.json."""

    def test_every_gloss_reaches_the_bank(self):
        glosses = json.loads((ROOT / 'data/review/glosses.json').read_text('utf-8'))
        bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        expected = {(record_id, option_id): value['ru']
                    for record_id, item in glosses.items() for option_id, value in item['options'].items()}
        # в обе стороны: и каждая подпись дошла, и лишних подписей в банке нет
        actual = {(record['id'], option['id']): option['gloss']
                  for record in bank.values() for option in record['options'] if 'gloss' in option}
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
