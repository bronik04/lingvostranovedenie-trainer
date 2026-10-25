import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from fact_rows import apply_fact_rows, attached_rows


def dossier(rows):
    return {'id': 'money', 'title': 'Деньги', 'tables': {'banknotes': {
        'columns': {}, 'rows': [{'id': row_id, 'olympiad': ids} for row_id, ids in rows.items()]}}}


def bank():
    return [{'id': 'a'}, {'id': 'b', 'mergedIds': ['b-old']}, {'id': 'c'},
            {'id': 'emb', 'dossier': 'money', 'factRow': 'money/banknotes/cny-20'}]


class FactRowsTest(unittest.TestCase):
    def test_one_row_is_a_string_several_rows_a_sorted_list(self):
        loaded = [(dossier({'cny-50': ['a', 'c'], 'cny-20': ['c']}), [])]
        by_id = {record['id']: record for record in apply_fact_rows(bank(), loaded)}
        self.assertEqual(by_id['a']['factRow'], 'money/banknotes/cny-50')
        self.assertEqual(by_id['c']['factRow'], ['money/banknotes/cny-20', 'money/banknotes/cny-50'])
        self.assertNotIn('factRow', by_id['b'])

    def test_absorbed_id_points_to_the_final_record(self):
        loaded = [(dossier({'cny-50': ['b-old']}), [])]
        self.assertEqual(attached_rows(bank(), loaded), {'b': ['money/banknotes/cny-50']})

    def test_embedded_record_keeps_its_row_and_unknown_ids_are_skipped(self):
        loaded = [(dossier({'cny-50': ['emb', 'gone']}), [])]
        built = apply_fact_rows(bank(), loaded)
        self.assertEqual(built, bank())

    def test_input_records_are_not_mutated(self):
        original = bank()
        apply_fact_rows(original, [(dossier({'cny-50': ['a']}), [])])
        self.assertNotIn('factRow', original[0])


if __name__ == '__main__':
    unittest.main()
