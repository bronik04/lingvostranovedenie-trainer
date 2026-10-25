import json, re, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from parsers.regions import records, task_id
import regions
from regions import load, validate


def variant(*tasks):
    return {'id': '2025-26-mun-spb', 'year': '2025-26', 'stage': 'муниципальный', 'stageCode': 'mun',
            'region': 'Санкт-Петербург', 'regionCode': 'spb', 'grades': '9-11',
            'origin': [{'file': '01-Варианты/2025-26/2-Муниципальный/Санкт-Петербург/9-11_Задания.pdf',
                        'sha256': '0' * 64}],
            'tasks': list(tasks)}


def task(number=3, options=('上海', '北京', '杭州', '广州'), key=2, **extra):
    return {'number': number, 'questionRu': 'В каком городе в 2016 году проходил саммит G20?',
            'questionZh': None, 'options': list(options), 'officialKeyIndex': key, **extra}


class RegionsParserTest(unittest.TestCase):
    def test_only_tasks_marked_add_reach_the_bank(self):
        v = variant(task(3), task(4))
        decisions = {'2025-26-mun-spb-3': {'status': 'add'},
                     '2025-26-mun-spb-4': {'status': 'narrow', 'reason': 'узко'}}
        result = records([v], decisions)
        self.assertEqual([r['number'] for r in result], [3])
        self.assertEqual(result[0]['regionCode'], 'spb')
        self.assertEqual(result[0]['region'], 'Санкт-Петербург')

    def test_transcribed_task_carries_a_warning(self):
        result = records([variant(task(transcribed=True))], {'2025-26-mun-spb-3': {'status': 'add'}})
        self.assertEqual(result[0]['parseWarnings'], ['расшифровано по картинке страницы'])

    def test_task_id_includes_the_region(self):
        self.assertEqual(task_id(variant(), task(7)), '2025-26-mun-spb-7')


class RegionsValidationTest(unittest.TestCase):
    def test_every_task_needs_a_decision(self):
        self.assertIn('2025-26-mun-spb-3: нет решения', validate([variant(task())], {}))

    def test_repeat_must_point_to_a_task_that_goes_to_the_bank(self):
        v = variant(task(3), task(4))
        errors = validate([v], {'2025-26-mun-spb-3': {'status': 'narrow', 'reason': 'узко'},
                                '2025-26-mun-spb-4': {'status': 'repeat', 'sameAs': '2025-26-mun-spb-3'}})
        self.assertTrue(any('повтор задания' in e for e in errors))

    def test_in_bank_must_name_an_existing_record(self):
        errors = validate([variant(task())], {'2025-26-mun-spb-3': {'status': 'in-bank', 'bankId': 'нет'}},
                          bank=[{'id': '2016-17-mun-1', 'occurrences': []}])
        self.assertIn("2025-26-mun-spb-3: в банке нет записи 'нет'", errors)

    def test_task_going_to_the_bank_needs_chinese_options(self):
        errors = validate([variant(task(options=('Пекин', 'Шанхай', 'Ханчжоу')))],
                          {'2025-26-mun-spb-3': {'status': 'add'}})
        self.assertIn('2025-26-mun-spb-3: варианты должны быть по-китайски', errors)

    def test_withheld_statuses_need_a_reason(self):
        errors = validate([variant(task())], {'2025-26-mun-spb-3': {'status': 'doubtful'}})
        self.assertIn('2025-26-mun-spb-3: не указана причина', errors)

    def test_regional_task_must_not_join_an_old_record(self):
        record = {'id': '2017-18-mun-6', 'occurrences': [{'year': '2017-18', 'stageCode': 'mun'},
                                                         {'year': '2018-19', 'stageCode': 'mun', 'regionCode': 'tyum'}]}
        errors = validate([variant(task())], {'2025-26-mun-spb-3': {'status': 'add'}}, bank=[record])
        self.assertTrue(any('влилось в запись банка' in e for e in errors))

    def test_decision_that_is_not_an_object_is_an_error(self):
        errors = validate([variant(task())], {'2025-26-mun-spb-3': 'add'})
        self.assertIn('2025-26-mun-spb-3: решение должно быть объектом', errors)

    def test_repository_decisions_are_valid(self):
        variants, decisions = load()
        bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
        self.assertEqual(validate(variants, decisions, bank), [])

    def test_page_lists_only_withheld_tasks(self):
        import tempfile
        v = variant(*(task(n) for n in range(1, 11)))
        v['tasks'][9]['questionRu'] = 'Что значит </script><!--<script> в задании?'
        decisions = {'2025-26-mun-spb-1': {'status': 'add'},
                     '2025-26-mun-spb-2': {'status': 'narrow', 'reason': 'узко'},
                     '2025-26-mun-spb-3': {'status': 'doubtful', 'reason': 'ключ не подтверждён'},
                     '2025-26-mun-spb-4': {'status': 'in-bank', 'bankId': '2016-17-mun-1'},
                     '2025-26-mun-spb-5': {'status': 'repeat', 'sameAs': '2025-26-mun-spb-1'},
                     '2025-26-mun-spb-6': {'status': 'ru-options', 'reason': 'варианты по-русски'},
                     '2025-26-mun-spb-7': {'status': 'format', 'reason': 'не выбор ответа'},
                     '2025-26-mun-spb-8': {'status': 'add'},
                     '2025-26-mun-spb-9': {'status': 'in-bank', 'bankId': '2016-17-mun-1'},
                     '2025-26-mun-spb-10': {'status': 'narrow', 'reason': 'узко'}}
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'page.html'
            original, regions.PAGE = regions.PAGE, target
            try:
                regions.write_page([v], decisions)
            finally:
                regions.PAGE = original
            page = target.read_text('utf-8')
        rows = json.loads(re.search(r'const DATA = (.*?);\n', page).group(1))
        # в банке, повторы и уже добавленные — не на странице; номера по порядку чисел
        self.assertEqual([row['id'].rsplit('-', 1)[1] for row in rows], ['2', '3', '6', '7', '10'])
        self.assertEqual({row['s'] for row in rows}, set(regions.PAGE_STATUSES))
        self.assertIn('всего 5: узких 2, сомнительных 1, с вариантами по-русски 1, не того формата 1', page)
        self.assertNotIn('</script><!--', page.split('const DATA')[1].split('\n')[0])

    def test_every_added_task_is_in_the_bank(self):
        variants, decisions = load()
        bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
        spots = {(o['year'], o['stageCode'], o.get('regionCode'), o['number'])
                 for r in bank for o in r.get('occurrences', [])}
        for v in variants:
            for t in v['tasks']:
                if decisions[task_id(v, t)]['status'] == 'add':
                    self.assertIn((v['year'], v['stageCode'], v['regionCode'], t['number']), spots, task_id(v, t))


if __name__ == '__main__':
    unittest.main()
