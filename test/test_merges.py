import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from dossiers import original_record  # noqa: E402
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


def pooled(record_id, year, options, answer_text='拉萨', number=5, **overrides):
    """Тот же вопрос с другими неверными вариантами; правильный ответ — answer_text."""
    items = [{'id': f'o{index + 1}', 'zh': text} for index, text in enumerate(options)]
    answer = next(o['id'] for o in items if o['zh'] == answer_text)
    return record(record_id, year, number=number, options=items,
                  answer={'optionId': answer, 'state': 'verified'}, **overrides)


POOL = {'a': {'absorbs': ['b'], 'distractors': 'pool', 'reason': 'Тот же вопрос, другие неверные варианты'}}


def pool_pair():
    return [record('a', '2019-20'), pooled('b', '2022-23', ['成都', '北京', '拉萨', '重庆'])]


class PoolMergeTest(unittest.TestCase):
    def test_new_wrong_options_follow_the_kept_ones(self):
        merged = apply_merges(pool_pair(), POOL)
        self.assertEqual([r['id'] for r in merged], ['a'])
        self.assertEqual([(o['id'], o['zh']) for o in merged[0]['options']],
                         [('o1', '拉萨'), ('o2', '北京'), ('o3', '上海'), ('o4', '香港'),
                          ('o5', '成都'), ('o6', '重庆')])
        self.assertEqual(merged[0]['answer'], {'optionId': 'o1', 'state': 'verified'})
        self.assertEqual(merged[0]['mergedIds'], ['b'])

    def test_options_of_several_absorbed_records_are_added_once_in_absorbs_order(self):
        bank = [*pool_pair(), pooled('c', '2024-25', ['重庆', '拉萨', '西安', '成都'])]
        merges = {'a': {'absorbs': ['b', 'c'], 'distractors': 'pool', 'reason': 'r'}}
        merged = apply_merges(bank, merges)[0]
        self.assertEqual([o['zh'] for o in merged['options']],
                         ['拉萨', '北京', '上海', '香港', '成都', '重庆', '西安'])

    def test_new_option_ids_skip_ids_already_taken(self):
        bank = pool_pair()
        bank[0]['options'][3]['id'] = 'o5'       # у оставшейся записи уже есть o5
        merged = apply_merges(bank, POOL)[0]
        ids = [o['id'] for o in merged['options']]
        self.assertEqual(len(ids), len(set(ids)))

    def test_official_key_of_the_absorbed_record_points_at_the_kept_answer(self):
        bank = pool_pair()
        bank[1]['occurrences'][0]['officialKey'] = 'o3'          # 拉萨 во влитой записи
        merged = apply_merges(bank, POOL)[0]
        keys = {o['year']: o['officialKey'] for o in merged['occurrences']}
        self.assertEqual(keys['2022-23'], 'o1')

    def test_input_records_are_not_mutated(self):
        bank = pool_pair()
        apply_merges(bank, POOL)
        self.assertEqual(len(bank[0]['options']), 4)

    def test_rejects_different_answers(self):
        bank = [record('a', '2019-20'), pooled('b', '2022-23', ['成都', '北京', '拉萨', '重庆'], answer_text='成都')]
        self.assertRejectsPool(bank, 'ответ не совпадает')

    def test_rejects_a_pool_that_adds_nothing(self):
        self.assertRejectsPool(pair(), 'объединение не добавило новых неверных вариантов')

    def test_rejects_an_explanation_naming_a_wrong_option(self):
        bank = pool_pair()
        bank[0]['explanation'] = {'ru': 'Центр района — Лхаса (拉萨), а 成都 — центр Сычуани.'}
        self.assertRejectsPool(bank, 'пояснение называет неверный вариант 成都')

    def test_rejects_years_written_with_and_without_nian(self):
        years = ['2001', '1995', '2015', '1970']
        bank = [pooled('a', '2015-16', years, answer_text='2001', number=1),
                pooled('b', '2024-25', ['2010 年', '2001', '2011 年', '1991 年'], answer_text='2001')]
        self.assertRejectsPool(bank, 'годы в вариантах записаны по-разному')

    def test_accepts_years_written_the_same_way(self):
        bank = [pooled('a', '2015-16', ['2001 年', '1995 年', '2015 年', '1970 年'], answer_text='2001 年', number=1),
                pooled('b', '2024-25', ['2010 年', '2001 年', '2011 年', '1991 年'], answer_text='2001 年')]
        self.assertEqual(validate_merges(POOL, bank), [])

    def test_rejects_an_unknown_distractors_value(self):
        merges = {'a': {'absorbs': ['b'], 'distractors': 'union', 'reason': 'r'}}
        errors = validate_merges(merges, pool_pair())
        self.assertTrue(any('distractors может быть только "pool"' in e for e in errors), errors)

    def test_merge_without_the_flag_still_needs_the_same_options(self):
        merges = {'a': {'absorbs': ['b'], 'reason': 'r'}}
        errors = validate_merges(merges, pool_pair())
        self.assertTrue(any('варианты не совпадают' in e for e in errors), errors)

    def assertRejectsPool(self, bank, fragment):
        errors = validate_merges(POOL, bank)
        self.assertTrue(any(fragment in error for error in errors), f'{fragment!r} not in {errors}')
        with self.assertRaises(ValueError):
            apply_merges(bank, POOL)


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

    def test_pooled_records_show_every_wrong_option_once(self):
        pools = {k: v for k, v in self.merges.items() if v.get('distractors') == 'pool'}
        expected = {
            '2023-24-zak-2': 7, '2017-18-shk-4': 7, '2015-16-zak-5': 6, '2015-16-mun-9': 7,
            '2015-16-zak-7': 5, '2020-21-reg-q094875': 5, '2016-17-reg-5': 5, '2016-17-shk-1': 5,
            '2017-18-reg-1': 5, '2021-22-mun-q833ea2': 6, '2021-22-mun-qd67aaa': 5, '2018-19-shk-6': 5,
            '2022-23-shk-q623963': 5, '2015-16-mun-10': 5, '2017-18-zak-10': 6, '2022-23-shk-q3c7e59': 6,
            '2023-24-shk-29': 6, '2018-19-reg-3': 6, '2017-18-zak-1': 6, '2019-20-mun-qe6c5d3': 5,
            '2016-17-mun-10': 6, '2023-24-shk-30': 6, '2016-17-reg-6': 5, '2016-17-zak-1': 5,
            '2015-16-mun-5': 5, '2018-19-reg-8': 7, '2016-17-reg-4': 6, '2015-16-reg-4': 6,
            '2016-17-mun-4': 6, '2016-17-reg-8': 6, '2019-20-mun-q727051': 6, '2018-19-zak-7': 7,
            '2018-19-reg-6': 7, '2022-23-reg-2': 6, '2015-16-zak-8': 5, '2016-17-shk-8': 5,
            '2015-16-reg-1': 7, '2018-19-mun-55': 6, '2018-19-mun-53': 5, '2016-17-shk-10': 5,
        }
        self.assertEqual(set(pools), set(expected))
        for keep_id in pools:
            record = self.bank[keep_id]
            texts = [o['zh'] for o in record['options']]
            # встроенная в досье запись получает ещё и варианты из таблицы — считаем свои
            self.assertEqual(len(original_record(record)['options']), expected[keep_id], keep_id)
            self.assertEqual(len(set(texts)), len(texts), keep_id)
            # группа у склеенной записи — только ради взаимной подсказки с вопросом о другом факте
            # (решение автора 2026-10-22, порция 3 провинций); дубль одного факта в группе ловит следующий тест
            if 'factGroup' in record:
                self.assertIn(record['factGroup'], {'province-names-river-lake', 'beijing-tianjin-municipality'}, keep_id)
            wrong = [o['zh'] for o in record['options'] if o['id'] != record['answer']['optionId']]
            for text in wrong:
                self.assertNotIn(text, record['explanation']['ru'], keep_id)

    def test_no_fact_group_left_where_one_question_with_a_pool_would_do(self):
        # группа «один факт» нужна только записям с разными ответами (романы, метро);
        # записи с одним ответом склеиваются в один вопрос с общим набором вариантов
        groups = json.loads((ROOT / 'data/review/fact-groups.json').read_text('utf-8'))
        for name, ids in groups.items():
            answers = {next(o['zh'] for o in self.bank[i]['options'] if o['id'] == self.bank[i]['answer']['optionId'])
                       for i in ids}
            self.assertGreater(len(answers), 1, name)

    def test_merged_wording_keeps_the_precise_edition(self):
        # формулировка, при которой неверный вариант можно защитить, заменена точной
        # редакцией влитой записи: Шэньчжэнь крупнее по экономике, Гуанчжоу был базой до 1927 г.
        self.assertIn('по площади', self.bank['2016-17-zak-1']['questionRu'])
        self.assertIn('перенесена', self.bank['2016-17-mun-10']['questionRu'])

    def test_merged_record_takes_the_fuller_wording_of_the_absorbed_one(self):
        # решение автора 2026-10-13: у склеенной записи — полная формулировка влитой
        fuller = {
            '2017-18-shk-4': 'знаменитый древнекитайский трактат',
            '2022-23-shk-q623963': 'крупнейшая в Китае библиотека',
            '2023-24-shk-29': 'польских интервентов',
            '2016-17-reg-6': 'антиимпериалистическое движение',
            '2018-19-reg-3': 'в 1999 году были включены',
            '2017-18-zak-1': 'огромному вкладу в дело революции',
            '2017-18-mun-2': 'свои произведения',
            '2015-16-mun-9': '(ВТО)',
            '2018-19-shk-6': 'провинции Китая',
            '2015-16-mun-10': 'наибольшую площадь',
            '2015-16-mun-5': 'традиционной культуре',
        }
        for keep_id, fragment in fuller.items():
            self.assertIn(fragment, self.bank[keep_id]['questionRu'], keep_id)
        self.assertEqual(self.bank['2021-22-mun-q833ea2']['topic'], 'История и государство')
        self.assertIn('29 декабря 1911', self.bank['2017-18-zak-1']['explanation']['ru'])
        self.assertIn('Чунцин', self.bank['2016-17-mun-10']['explanation']['ru'])
        # в 1932 г. правительство «переносило столицу» (迁都) в Лоян, а 洛阳 — неверный вариант:
        # пояснение обязано сказать, что официальной столицей оставался Нанкин
        self.assertIn('официальной столицей', self.bank['2016-17-mun-10']['explanation']['ru'])
        for keep_id in ('2016-17-reg-2', '2017-18-reg-1'):
            self.assertNotIn('Поэтому', self.bank[keep_id]['explanation']['ru'], keep_id)
        # китайский текст — исходный текст олимпиады того года: правки его не трогают
        edits = json.loads((ROOT / 'data/review/editorial.json').read_text('utf-8'))
        for keep_id in fuller:
            self.assertNotIn('questionZh', edits.get(keep_id, {}), keep_id)

    def test_fuller_wording_does_not_hint_at_the_answer(self):
        # Си Цзиньпин стал председателем КНР в марте 2013 года: «председатель КНР Си
        # Цзиньпин выдвинул» отсекает 2000, 2001, 2010 и 2011 — вопрос остаётся с «Китай»
        self.assertNotIn('Си Цзиньпин', self.bank['2021-22-mun-q833ea2']['questionRu'])

    def test_unified_spellings_do_not_reappear_side_by_side(self):
        # разные записи одного и того же (刘邦 и 汉高祖, 新年 и 新年节, 蓝 и 蓝色)
        # выровнены правкой до склейки, иначе на экране стояли бы два одинаковых варианта
        for keep_id in ('2019-20-mun-qe6c5d3', '2023-24-shk-30', '2015-16-mun-5', '2016-17-reg-2'):
            texts = [o['zh'] for o in self.bank[keep_id]['options']]
            for left, right in (('刘邦', '汉高祖'), ('新年', '新年节'), ('蓝', '蓝色'), ('白', '白色'),
                                ('黑', '黑色'), ('全国政治协商会议', '全国政治协商会议（政协）')):
                self.assertFalse(left in texts and right in texts, (keep_id, left, right))

    def test_lao_she_questions_are_one_record_with_beijing_dialect(self):
        record = self.bank['2017-18-mun-2']
        self.assertEqual(record['mergedIds'], ['2022-23-reg-10'])
        answer = next(o['zh'] for o in record['options'] if o['id'] == record['answer']['optionId'])
        self.assertEqual(answer, '北京方言')
        self.assertNotIn('北方方言', [o['zh'] for o in record['options']])
        # в ключе 2022-23 ответ записан как 北方方言: ученик должен узнать, что это тот же говор
        self.assertIn('北方方言', record['explanation']['ru'])


if __name__ == '__main__':
    unittest.main()
