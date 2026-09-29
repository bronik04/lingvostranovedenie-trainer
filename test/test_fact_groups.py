import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from fact_groups import apply_fact_groups, load_fact_groups, validate_fact_groups


def bank():
    return [{'id': name, 'questionRu': f'Вопрос {name}'} for name in ('a', 'b', 'c', 'd')]


class FactGroupsTest(unittest.TestCase):
    def test_marks_members_and_leaves_others_alone(self):
        result = apply_fact_groups(bank(), {'pair-ab': ['a', 'b']})
        by_id = {r['id']: r for r in result}
        self.assertEqual(by_id['a']['factGroup'], 'pair-ab')
        self.assertEqual(by_id['b']['factGroup'], 'pair-ab')
        self.assertNotIn('factGroup', by_id['c'])
        self.assertEqual([r['id'] for r in result], ['a', 'b', 'c', 'd'])

    def test_input_records_are_not_mutated(self):
        original = bank()
        apply_fact_groups(original, {'pair-ab': ['a', 'b']})
        self.assertNotIn('factGroup', original[0])

    def test_accepts_a_valid_file(self):
        self.assertEqual(validate_fact_groups({'g1': ['a', 'b'], 'g2': ['c', 'd']}, bank()), [])

    def test_rejects_each_broken_rule(self):
        cases = [
            ({'g': ['a']}, 'хотя бы две разные записи'),
            ({'g': ['a', 'a']}, 'id повторяются'),
            ({'g': ['a', 'zzz']}, 'записи zzz в банке нет'),
            ({'g1': ['a', 'b'], 'g2': ['b', 'c']}, 'состоит в двух группах'),
            ({'Bad Id': ['a', 'b']}, 'латиница, цифры и дефисы'),
            ({'g': 'a'}, 'должна быть списком'),
            ({'g': ['a', 2]}, 'должна быть списком'),
            (['a', 'b'], 'должны быть словарём'),
        ]
        for groups, fragment in cases:
            errors = validate_fact_groups(groups, bank())
            self.assertTrue(any(fragment in e for e in errors), f'{groups}: {errors}')
            with self.assertRaises(ValueError):
                apply_fact_groups(bank(), groups)

    def test_loads_a_file_and_treats_missing_as_empty(self):
        self.assertEqual(load_fact_groups(Path('/nonexistent/groups.json')), {})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'groups.json'
            path.write_text(json.dumps({'g': ['a', 'b']}), encoding='utf-8')
            self.assertEqual(load_fact_groups(path), {'g': ['a', 'b']})
            path.write_text('[]', encoding='utf-8')
            with self.assertRaises(ValueError):
                load_fact_groups(path)

    def test_repeated_group_id_in_the_file_is_an_error_not_a_silent_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'groups.json'
            path.write_text('{"g": ["a", "b"], "g": ["c", "d"]}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'в группах повторяются ключи'):
                load_fact_groups(path)


class FactGroupsInBankTest(unittest.TestCase):
    def test_every_group_reaches_the_bank_and_nothing_else_is_marked(self):
        groups = load_fact_groups(ROOT / 'data/review/fact-groups.json')
        bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        expected = {record_id: group for group, ids in groups.items() for record_id in ids}
        for record_id, group in expected.items():
            self.assertEqual(bank[record_id].get('factGroup'), group, record_id)
        marked = {i for i, r in bank.items() if 'factGroup' in r}
        self.assertEqual(marked, set(expected))


if __name__ == '__main__':
    unittest.main()
