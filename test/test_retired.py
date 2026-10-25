import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from retired import apply_retired, load_retired, validate_retired


def bank():
    return [{'id': name, 'questionRu': f'Вопрос {name}'} for name in ('a', 'b', 'c')]


RETIRED = {'b': {'keptIn': 'a', 'reason': 'Тот же факт, другой ответ: оставлен вопрос a'}}


class ApplyRetiredTest(unittest.TestCase):
    def test_retired_record_leaves_the_bank_and_its_id_moves_to_the_kept_one(self):
        result = apply_retired(bank(), RETIRED)
        self.assertEqual([r['id'] for r in result], ['a', 'c'])
        self.assertEqual(result[0]['mergedIds'], ['b'])
        self.assertNotIn('mergedIds', result[1])

    def test_kept_record_keeps_ids_it_already_absorbed(self):
        records = bank()
        records[0]['mergedIds'] = ['z']
        result = apply_retired(records, RETIRED)
        self.assertEqual(result[0]['mergedIds'], ['b', 'z'])

    def test_ids_absorbed_by_the_retired_record_move_along(self):
        # иначе прогресс, перенесённый на удалённую запись раньше, потерялся бы
        records = bank()
        records[1]['mergedIds'] = ['y']
        result = apply_retired(records, RETIRED)
        self.assertEqual(result[0]['mergedIds'], ['b', 'y'])

    def test_kept_record_keeps_its_own_question(self):
        result = apply_retired(bank(), RETIRED)
        self.assertEqual(result[0]['questionRu'], 'Вопрос a')

    def test_input_records_are_not_mutated(self):
        original = bank()
        apply_retired(original, RETIRED)
        self.assertEqual(len(original), 3)
        self.assertNotIn('mergedIds', original[0])


class ValidateRetiredTest(unittest.TestCase):
    def assertRejects(self, retired, fragment):
        errors = validate_retired(retired, bank())
        self.assertTrue(any(fragment in error for error in errors), f'{fragment!r} not in {errors}')
        with self.assertRaises(ValueError):
            apply_retired(bank(), retired)

    def test_accepts_a_valid_entry(self):
        self.assertEqual(validate_retired(RETIRED, bank()), [])

    def test_rejects_each_broken_rule(self):
        self.assertRejects({'x': {'keptIn': 'a', 'reason': 'r'}}, 'x: такой записи в банке нет')
        self.assertRejects({'b': {'keptIn': 'x', 'reason': 'r'}}, 'x: такой записи в банке нет')
        self.assertRejects({'b': {'keptIn': 'b', 'reason': 'r'}}, 'оставлена сама вместо себя')
        self.assertRejects({'b': {'keptIn': 'a'}}, 'не указана причина')
        self.assertRejects({'b': {'keptIn': 'a', 'reason': '  '}}, 'не указана причина')
        self.assertRejects({'b': {'keptIn': 'a', 'reason': 'r', 'extra': 1}}, 'неизвестные поля')
        self.assertRejects({'b': 'a'}, 'должна быть объектом')
        self.assertRejects({'b': {'keptIn': 'c', 'reason': 'r'}, 'c': {'keptIn': 'a', 'reason': 'r'}},
                           'c: оставленная запись сама удалена')
        self.assertRejects(['b'], 'должны быть словарём')


class LoadRetiredTest(unittest.TestCase):
    def test_missing_file_means_nothing_is_retired(self):
        self.assertEqual(load_retired(Path('/nonexistent/retired.json')), {})

    def test_repeated_key_in_the_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'retired.json'
            path.write_text('{"b": {"keptIn": "a", "reason": "r"}, "b": {"keptIn": "c", "reason": "r"}}',
                            encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'повторяются ключи'):
                load_retired(path)


class RetiredInBankTest(unittest.TestCase):
    """Каждое удаление из data/review/retired.json должно дойти до data/bank.json."""

    def test_retired_records_are_gone_and_their_progress_has_a_home(self):
        retired = load_retired(ROOT / 'data/review/retired.json')
        bank_by_id = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        self.assertEqual(retired.keys(), {
            '2017-18-zak-8', '2016-17-mun-9',
            # дубли региональных вопросов (решение автора 2026-10-25, data/review/regions-dossier-check.md)
            '2022-23-mun-amur-1', '2025-26-mun-vlad-3', '2021-22-mun-lenobl-7', '2023-24-mun-udm-4',
            '2022-23-mun-spb-2', '2025-26-mun-kgd-55', '2025-26-shk-mosobl-17'})
        for record_id, item in retired.items():
            self.assertNotIn(record_id, bank_by_id)
            self.assertIn(record_id, bank_by_id[item['keptIn']]['mergedIds'])


if __name__ == '__main__':
    unittest.main()
