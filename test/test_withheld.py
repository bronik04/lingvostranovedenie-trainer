import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from withheld import apply_withheld, load_withheld, reference_errors, validate_withheld


def bank():
    olympiad = [{'id': name, 'questionRu': f'Вопрос {name}', 'occurrences': [{'year': '2026-27'}]}
                for name in ('a', 'b')]
    return [*olympiad, {'id': 'nature-q01', 'questionRu': 'Вопрос досье', 'origin': 'addition'}]


WITHHELD = {'b': {'reason': 'Ответ не подтверждён источниками', 'date': '2026-10-24'}}


class ApplyWithheldTest(unittest.TestCase):
    def test_withheld_record_leaves_the_bank(self):
        self.assertEqual([r['id'] for r in apply_withheld(bank(), WITHHELD)], ['a', 'nature-q01'])

    def test_nothing_withheld_keeps_the_bank(self):
        self.assertEqual(apply_withheld(bank(), {}), bank())


class ValidateWithheldTest(unittest.TestCase):
    def assertRejects(self, withheld, fragment, records=None):
        errors = validate_withheld(withheld, records or bank())
        self.assertTrue(any(fragment in error for error in errors), f'{fragment!r} not in {errors}')
        with self.assertRaises(ValueError):
            apply_withheld(records or bank(), withheld)

    def test_accepts_a_valid_entry(self):
        self.assertEqual(validate_withheld(WITHHELD, bank()), [])

    def test_rejects_unknown_record(self):
        self.assertRejects({'z': WITHHELD['b']}, 'такой записи в банке нет')

    def test_rejects_record_without_olympiad_appearances(self):
        # принятый вопрос досье или дополнение снимают через removed.json, черновик просто не принимают
        self.assertRejects({'nature-q01': WITHHELD['b']}, 'только олимпиадные')

    def test_rejects_entry_that_is_not_an_object(self):
        self.assertRejects({'b': 'ответ не подтверждён'}, 'объектом')
        self.assertRejects(['b'], 'словарём')

    def test_rejects_record_that_absorbed_others(self):
        # влитые записи уже опубликованы: отложить её значит снять с сайта и их
        records = bank()
        records[1]['mergedIds'] = ['old']
        self.assertRejects(WITHHELD, 'влиты', records)

    def test_requires_reason_and_date(self):
        self.assertRejects({'b': {'date': '2026-10-24'}}, 'причина')
        self.assertRejects({'b': {'reason': 'Сомнение'}}, 'дата')
        self.assertRejects({'b': {**WITHHELD['b'], 'keptIn': 'a'}}, 'неизвестные поля')

    def test_layers_pointing_at_a_withheld_record_are_named(self):
        errors = reference_errors(WITHHELD, {'glosses.json': {'a', 'b'}, 'fact-groups.json': {'a'}})
        self.assertEqual(len(errors), 1)
        self.assertIn('glosses.json', errors[0])
        self.assertTrue(errors[0].startswith('b:'))
        self.assertEqual(reference_errors({}, {'glosses.json': {'b'}}), [])

    def test_loader_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'withheld.json'
            path.write_text('{"b": {"reason": "x", "date": "2026-10-24"}, "b": {"reason": "y", "date": "2026-10-24"}}',
                            encoding='utf-8')
            with self.assertRaises(ValueError):
                load_withheld(path)


class WithheldInBankTest(unittest.TestCase):
    def test_withheld_records_are_not_published(self):
        withheld = load_withheld(ROOT / 'data/review/withheld.json')
        published = {r['id'] for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        self.assertFalse(set(withheld) & published)


if __name__ == '__main__':
    unittest.main()
