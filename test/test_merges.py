import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from merges import apply_merges, load_merges, validate_merges


def record(record_id, year, stage='mun', number=1, **overrides):
    item = {
        'id': record_id,
        'questionRu': 'Какой город является центром Тибетского автономного района?',
        'options': [{'id': 'o1', 'zh': '拉萨'}, {'id': 'o2', 'zh': '北京'},
                    {'id': 'o3', 'zh': '上海'}, {'id': 'o4', 'zh': '香港'}],
        'answer': {'optionId': 'o1', 'state': 'verified'},
        'occurrences': [{'year': year, 'stage': 'муниципальный', 'stageCode': stage, 'number': number,
                         'grades': '9-11', 'officialKey': None, 'sourceFiles': ['a.docx']}],
        'evidence': [{'title': 'A', 'url': f'https://example.org/{record_id}', 'checkedAt': '2026-09-18'}],
    }
    item.update(overrides)
    return item


def shuffled(item):
    """Тот же вопрос, но варианты лежат в другом порядке и под другими id."""
    order = [3, 0, 2, 1]
    options = [{'id': f'o{index + 1}', 'zh': item['options'][position]['zh']}
               for index, position in enumerate(order)]
    answer = next(o['id'] for o in options if o['zh'] == '拉萨')
    return {**item, 'options': options, 'answer': {'optionId': answer, 'state': 'verified'}}


MERGE = {'a': {'absorbs': ['b'], 'reason': 'Тот же вопрос с теми же вариантами'}}


def pair():
    return [record('a', '2019-20'), shuffled(record('b', '2022-23', number=5))]


class ApplyMergesTest(unittest.TestCase):
    def test_absorbed_record_disappears_and_its_appearances_move_to_the_kept_one(self):
        bank = apply_merges(pair(), MERGE)
        self.assertEqual([r['id'] for r in bank], ['a'])
        self.assertEqual([(o['year'], o['number']) for o in bank[0]['occurrences']],
                         [('2019-20', 1), ('2022-23', 5)])
        self.assertEqual(bank[0]['mergedIds'], ['b'])

    def test_kept_record_keeps_its_own_wording_and_options(self):
        original = pair()
        merged = apply_merges(original, MERGE)[0]
        self.assertEqual(merged['questionRu'], original[0]['questionRu'])
        self.assertEqual(merged['options'], original[0]['options'])
        self.assertEqual(merged['answer'], original[0]['answer'])

    def test_appearances_are_ordered_by_year_stage_then_number(self):
        bank = [record('a', '2022-23', stage='reg', number=2),
                shuffled(record('b', '2022-23', stage='shk', number=9)),
                shuffled(record('c', '2019-20', stage='zak', number=1))]
        merged = apply_merges(bank, {'a': {'absorbs': ['b', 'c'], 'reason': 'дубли'}})[0]
        self.assertEqual([(o['year'], o['stageCode']) for o in merged['occurrences']],
                         [('2019-20', 'zak'), ('2022-23', 'shk'), ('2022-23', 'reg')])
        self.assertEqual(merged['mergedIds'], ['b', 'c'])

    def test_evidence_of_both_records_is_kept_without_repeating_a_link(self):
        bank = pair()
        bank[1]['evidence'].append({'title': 'A', 'url': 'https://example.org/a', 'checkedAt': '2026-09-19'})
        merged = apply_merges(bank, MERGE)[0]
        self.assertEqual([e['url'] for e in merged['evidence']],
                         ['https://example.org/a', 'https://example.org/b'])

    def test_records_outside_the_merge_are_untouched(self):
        other = record('z', '2015-16', questionRu='Другой вопрос?')
        bank = apply_merges([*pair(), other], MERGE)
        self.assertIn(other, bank)
        self.assertNotIn('mergedIds', other)

    def test_input_records_are_not_mutated(self):
        original = pair()
        apply_merges(original, MERGE)
        self.assertEqual(len(original[0]['occurrences']), 1)
        self.assertNotIn('mergedIds', original[0])


class OfficialKeyTest(unittest.TestCase):
    """Официальный ключ хранится как id варианта, а у влитой записи id другие."""

    def keyed_pair(self, key_text='拉萨'):
        bank = pair()
        absorbed = bank[1]
        absorbed['occurrences'][0]['officialKey'] = next(o['id'] for o in absorbed['options'] if o['zh'] == key_text)
        return bank

    def test_key_of_the_absorbed_appearance_points_to_the_same_text_in_the_kept_record(self):
        bank = self.keyed_pair()
        absorbed_key = bank[1]['occurrences'][0]['officialKey']
        self.assertNotEqual(absorbed_key, 'o1')            # id действительно разъехались
        merged = apply_merges(bank, MERGE)[0]
        keys = {o['year']: o['officialKey'] for o in merged['occurrences']}
        self.assertEqual(keys['2022-23'], 'o1')            # 拉萨 в оставшейся записи
        self.assertEqual(keys['2019-20'], None)

    def test_key_of_the_kept_appearance_is_left_alone(self):
        bank = pair()
        bank[0]['occurrences'][0]['officialKey'] = 'o1'
        merged = apply_merges(bank, MERGE)[0]
        self.assertEqual(merged['occurrences'][0]['officialKey'], 'o1')

    def test_absorbed_record_is_not_mutated_by_reindexing(self):
        bank = self.keyed_pair()
        before = bank[1]['occurrences'][0]['officialKey']
        apply_merges(bank, MERGE)
        self.assertEqual(bank[1]['occurrences'][0]['officialKey'], before)

    def test_key_pointing_at_another_answer_is_a_conflict_not_a_duplicate(self):
        bank = self.keyed_pair(key_text='北京')
        errors = validate_merges(MERGE, bank)
        self.assertTrue(any('расходится с ответом' in e for e in errors), errors)
        with self.assertRaises(ValueError):
            apply_merges(bank, MERGE)

    def test_same_year_stage_and_number_cannot_be_glued(self):
        bank = [record('a', '2019-20', number=3), shuffled(record('b', '2019-20', number=3))]
        errors = validate_merges(MERGE, bank)
        self.assertTrue(any('уже есть у a' in e for e in errors), errors)

    def test_appearances_without_a_number_are_allowed_to_share_year_and_stage(self):
        bank = [record('a', '2019-20', number=None), shuffled(record('b', '2019-20', number=None))]
        self.assertEqual(validate_merges(MERGE, bank), [])


class ValidateMergesTest(unittest.TestCase):
    def errors(self, merges, bank=None):
        return validate_merges(merges, bank if bank is not None else pair())

    def assertRejects(self, merges, fragment, bank=None):
        errors = self.errors(merges, bank)
        self.assertTrue(any(fragment in error for error in errors), f'{fragment!r} not in {errors}')
        with self.assertRaises(ValueError):
            apply_merges(bank if bank is not None else pair(), merges)

    def test_accepts_a_valid_merge(self):
        self.assertEqual(self.errors(MERGE), [])

    def test_rejects_each_broken_rule(self):
        self.assertRejects({'x': {'absorbs': ['b'], 'reason': 'r'}}, 'x: такой записи в банке нет')
        self.assertRejects({'a': {'absorbs': ['x'], 'reason': 'r'}}, 'x: такой записи в банке нет')
        self.assertRejects({'a': {'absorbs': ['a'], 'reason': 'r'}}, 'влита сама в себя')
        self.assertRejects({'a': {'absorbs': ['b']}}, 'не указана причина')
        self.assertRejects({'a': {'absorbs': ['b'], 'reason': '  '}}, 'не указана причина')
        self.assertRejects({'a': {'absorbs': [], 'reason': 'r'}}, 'absorbs должен быть непустым')
        self.assertRejects({'a': {'absorbs': ['b', 'b'], 'reason': 'r'}}, 'id повторяются')
        self.assertRejects({'a': {'absorbs': ['b'], 'reason': 'r', 'extra': 1}}, 'неизвестные поля')
        self.assertRejects({'a': 'b'}, 'склейка должна быть объектом')
        self.assertRejects(['a'], 'должны быть словарём', bank=pair())

    def test_rejects_different_options_or_answer(self):
        bank = pair()
        bank[1]['options'][0] = {'id': 'o1', 'zh': '成都'}
        self.assertRejects(MERGE, 'варианты не совпадают', bank=bank)
        bank = pair()
        bank[1]['answer'] = {'optionId': 'o1', 'state': 'verified'}   # o1 теперь 香港
        self.assertRejects(MERGE, 'ответ не совпадает', bank=bank)

    def test_rejects_unverified_answer_on_either_side(self):
        bank = pair()
        bank[1]['answer'] = {'optionId': None, 'state': 'needs-review'}
        self.assertRejects(MERGE, 'b: ответ не проверен', bank=bank)
        bank = pair()
        bank[0]['answer'] = {'optionId': 'o1', 'state': 'unverified'}
        self.assertRejects(MERGE, 'a: ответ не проверен', bank=bank)

    def test_rejects_additions_which_have_no_appearances(self):
        bank = pair()
        bank[1] = {**bank[1], 'occurrences': [], 'origin': 'addition'}
        self.assertRejects(MERGE, 'склеивать можно только олимпиадные', bank=bank)

    def test_rejects_chains_and_double_absorption(self):
        bank = [*pair(), shuffled(record('c', '2024-25'))]
        self.assertRejects({'a': {'absorbs': ['b'], 'reason': 'r'},
                            'b': {'absorbs': ['c'], 'reason': 'r'}}, 'влитая запись сама принимает', bank=bank)
        self.assertRejects({'a': {'absorbs': ['c'], 'reason': 'r'},
                            'b': {'absorbs': ['c'], 'reason': 'r'}}, 'влита дважды', bank=bank)


class LoadMergesTest(unittest.TestCase):
    def test_missing_file_means_no_merges(self):
        self.assertEqual(load_merges(Path('/nonexistent/merges.json')), {})

    def test_repeated_key_in_the_file_is_an_error_not_a_silent_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'merges.json'
            path.write_text('{"a": {"absorbs": ["b"], "reason": "r"}, "a": {"absorbs": ["c"], "reason": "r"}}',
                            encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'в склейках повторяются ключи'):
                load_merges(path)

    def test_reads_a_file_and_rejects_a_non_object(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'merges.json'
            path.write_text(json.dumps(MERGE), encoding='utf-8')
            self.assertEqual(load_merges(path), MERGE)
            path.write_text('[]', encoding='utf-8')
            with self.assertRaises(ValueError):
                load_merges(path)


class MergesInBankTest(unittest.TestCase):
    """Каждая склейка из data/review/merges.json должна дойти до data/bank.json."""

    @classmethod
    def setUpClass(cls):
        cls.merges = load_merges(ROOT / 'data/review/merges.json')
        cls.bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}

    def test_absorbed_records_are_gone_and_kept_ones_remember_them(self):
        for keep_id, item in self.merges.items():
            self.assertIn(keep_id, self.bank)
            self.assertEqual(self.bank[keep_id]['mergedIds'], sorted(item['absorbs']), keep_id)
            for absorbed_id in item['absorbs']:
                self.assertNotIn(absorbed_id, self.bank, absorbed_id)

    def test_kept_record_carries_appearances_of_every_merged_one_without_repeats(self):
        for keep_id, item in self.merges.items():
            spots = [(o['year'], o['stageCode'], o['number']) for o in self.bank[keep_id]['occurrences']]
            self.assertGreaterEqual(len(spots), 1 + len(item['absorbs']), keep_id)
            self.assertEqual(len(spots), len(set(spots)), keep_id)

    def test_official_keys_of_merged_records_point_at_the_answer(self):
        for keep_id in self.merges:
            record = self.bank[keep_id]
            for occurrence in record['occurrences']:
                self.assertIn(occurrence['officialKey'], (None, record['answer']['optionId']),
                              f"{keep_id} {occurrence['year']} {occurrence['stageCode']}")

    def test_merged_ids_never_collide_with_live_ids(self):
        merged = {i for r in self.bank.values() for i in r.get('mergedIds', [])}
        self.assertFalse(merged & set(self.bank))
        self.assertEqual(len(merged), sum(len(r.get('mergedIds', [])) for r in self.bank.values()))


if __name__ == '__main__':
    unittest.main()
