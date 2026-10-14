import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from dossiers import dossier_records, question_options, validate_dossier

TOPIC = 'Экономика, образование, наука и спорт'


def source(n):
    return {'title': f'Источник {n}', 'url': f'https://www.pbc.gov.cn/page-{n}', 'quote': 'цитата',
            'checkedAt': '2026-10-15', 'authority': 'official'}


def cell(zh, ru=(), gloss=None):
    item = {'zh': zh, 'ru': list(ru)}
    if gloss is not None:
        item['gloss'] = gloss
    return item


def note(row_id, currency, denomination, back, back_ru, flower=None, flower_ru=(),
         series='пятая серия, выпуск 2019 года'):
    row = {'id': row_id, 'currency': cell(currency),
           'denomination': cell(denomination, gloss=f'Купюра {denomination}'),
           'series': series,
           'back': cell(back, back_ru, gloss=f'{back_ru[0]} — на обороте купюры'),
           'sources': [source(1), source(2)], 'olympiad': []}
    if flower:
        row['flower'] = cell(flower, flower_ru, gloss=f'{flower_ru[0].capitalize()} — цветок на купюре')
    return row


def dossier():
    return {'id': 'money', 'title': 'Деньги', 'tables': {'banknotes': {
        'columns': {'currency': 'zh', 'denomination': 'zh', 'series': 'ru', 'back': 'zh', 'flower': 'zh'},
        'required': ['series'], 'datedQuestions': True,
        'rows': [
            note('cny-100', '人民币', '100 元', '人民大会堂', ['Дом народных собраний'], '梅花', ['мэйхуа']),
            note('cny-50', '人民币', '50 元', '布达拉宫', ['Потала'], '菊花', ['хризантема']),
            note('cny-20', '人民币', '20 元', '桂林山水', ['Гуйлинь'], '荷花', ['лотос']),
            note('cny-10', '人民币', '10 元', '长江三峡', ['Три ущелья'], '月季花', ['китайская роза']),
            note('cny-5', '人民币', '5 元', '泰山', ['Тайшань'], '水仙花', ['нарцисс']),
            note('rub-500', '卢布', '500 卢布', '索洛韦茨基修道院', ['Соловецкий монастырь'],
                 series='образца 1997 года'),
        ]}}}


def row(data, row_id):
    return next(r for r in data['tables']['banknotes']['rows'] if r['id'] == row_id)


class ValidateDossierTest(unittest.TestCase):
    def assertRejects(self, mutate, fragment):
        data = dossier()
        mutate(data)
        errors = validate_dossier(data)
        self.assertTrue(any(fragment in error for error in errors), f'{fragment!r} not in {errors}')

    def test_accepts_a_valid_dossier(self):
        self.assertEqual(validate_dossier(dossier()), [])

    def test_rejects_a_dossier_that_is_not_an_object(self):
        self.assertEqual(validate_dossier([]), ['досье должно быть объектом'])

    def test_rejects_each_broken_rule(self):
        table = lambda d: d['tables']['banknotes']
        cases = [
            (lambda d: d.pop('title'), 'нет названия'),
            (lambda d: d.update(id='Деньги'), 'нет id'),
            (lambda d: d.update(tables={}), 'нет таблиц'),
            (lambda d: table(d).update(extra=1), 'неизвестные поля таблицы'),
            (lambda d: table(d)['columns'].update(back='en'), 'колонки'),
            (lambda d: table(d)['columns'].update(sources='zh'), 'заняты служебными полями'),
            (lambda d: table(d).update(required=['colour']), 'required'),
            (lambda d: table(d).update(datedQuestions='да'), 'datedQuestions'),
            (lambda d: row(d, 'cny-50').update(colour=cell('红')), 'необъявленные колонки'),
            (lambda d: row(d, 'cny-50').update(id='cny-100'), 'повторяющийся id строки'),
            (lambda d: row(d, 'cny-50').update(id='CNY 50'), 'нет id строки'),
            (lambda d: row(d, 'cny-50').pop('series'), 'нет обязательной колонки series'),
            (lambda d: row(d, 'cny-50').update(back=cell('Потала')), 'не по-китайски'),
            (lambda d: row(d, 'cny-50').update(back='布达拉宫'), 'должна быть объектом'),
            (lambda d: row(d, 'cny-50')['back'].update(ru='Потала'), 'список русских названий'),
            (lambda d: row(d, 'cny-50')['back'].update(gloss='Д' * 91), 'длиннее 90'),
            (lambda d: row(d, 'cny-50')['back'].update(gloss='две\nстроки'), 'одна непустая строка'),
            (lambda d: row(d, 'cny-50')['back'].update(note='x'), 'неизвестные поля ячейки'),
            (lambda d: row(d, 'cny-50').update(series=''), 'описательная ячейка'),
            (lambda d: row(d, 'cny-50').update(sources=[source(1)]), 'не меньше 2 источников'),
            (lambda d: row(d, 'cny-50')['sources'][0].pop('quote'), 'нет цитаты'),
            (lambda d: row(d, 'cny-50')['sources'][0].update(authority='reference'), 'не помечен официальным'),
            (lambda d: row(d, 'cny-50').update(sources=[source(1), source(1)]), 'источники повторяются'),
            (lambda d: row(d, 'cny-50').update(olympiad='2024-25-shk-29'), 'olympiad'),
        ]
        for mutate, fragment in cases:
            with self.subTest(fragment=fragment):
                self.assertRejects(mutate, fragment)

    def test_cell_without_russian_names_or_gloss_is_valid(self):
        data = dossier()
        row(data, 'cny-50')['back'] = {'zh': '布达拉宫'}
        self.assertEqual(validate_dossier(data), [])



def question(**overrides):
    item = {'id': 'money-q01', 'status': 'accepted', 'topic': TOPIC,
            'fact': {'table': 'banknotes', 'row': 'cny-20', 'ask': 'flower', 'where': {'currency': '人民币'}},
            'questionRu': 'Какой цветок изображён на лицевой стороне купюры 20 юаней выпуска 2019 года?',
            'explanation': 'Первое предложение. Второе предложение. Третье предложение.',
            'exclude': [], 'check': {'verdict': 'accept', 'note': 'ок'}}
    item.update(overrides)
    return item


def ids(options):
    return [option['id'] for option in options]


class QuestionOptionsTest(unittest.TestCase):
    def test_pool_is_the_same_column_of_sibling_rows(self):
        options, answer = question_options(question(), dossier())
        self.assertEqual(answer, 'cny-20')
        self.assertEqual(ids(options), ['cny-20', 'cny-100', 'cny-50', 'cny-10', 'cny-5'])
        self.assertEqual(options[0]['zh'], '荷花')

    def test_where_keeps_only_matching_rows(self):
        fact = {'table': 'banknotes', 'row': 'cny-50', 'ask': 'back'}
        mixed, _ = question_options(question(fact=fact), dossier())
        self.assertIn('rub-500', ids(mixed))
        yuan, _ = question_options(question(fact={**fact, 'where': {'currency': '人民币'}}), dossier())
        self.assertNotIn('rub-500', ids(yuan))

    def test_exclude_drops_a_row(self):
        options, _ = question_options(question(exclude=['cny-5']), dossier())
        self.assertNotIn('cny-5', ids(options))

    def test_repeated_wrong_values_collapse_to_the_first_row(self):
        data = dossier()
        row(data, 'cny-10')['flower'] = cell('梅花', ['мэйхуа'], gloss='Мэйхуа — ещё раз')
        options, _ = question_options(question(), data)
        self.assertEqual(ids(options), ['cny-20', 'cny-100', 'cny-50', 'cny-5'])

    def test_wrong_options_carry_glosses_of_their_cells_and_the_answer_does_not(self):
        options, _ = question_options(question(), dossier())
        self.assertNotIn('gloss', options[0])
        self.assertEqual(options[2], {'id': 'cny-50', 'zh': '菊花', 'gloss': 'Хризантема — цветок на купюре'})

    def test_given_direction_asks_another_column_of_the_same_row(self):
        fact = {'table': 'banknotes', 'row': 'cny-50', 'ask': 'denomination', 'given': 'flower',
                'where': {'currency': '人民币'}}
        options, answer = question_options(question(fact=fact), dossier())
        self.assertEqual((answer, options[0]['zh']), ('cny-50', '50 元'))
        self.assertEqual([o['zh'] for o in options[1:]], ['100 元', '20 元', '10 元', '5 元'])

    def test_explicit_options_put_the_answer_first(self):
        refs = [{'row': r, 'column': 'back'} for r in ('cny-100', 'cny-50', 'cny-20', 'rub-500')]
        fact = {'table': 'banknotes', 'options': refs, 'answer': {'row': 'rub-500', 'column': 'back'}}
        options, answer = question_options(question(fact=fact), dossier())
        self.assertEqual(answer, 'rub-500')
        self.assertEqual(ids(options), ['rub-500', 'cny-100', 'cny-50', 'cny-20'])

    def test_new_row_keeps_the_answer_and_existing_option_ids(self):
        before, answer_before = question_options(question(), dossier())
        data = dossier()
        data['tables']['banknotes']['rows'].append(
            note('cny-1', '人民币', '1 元', '三潭印月', ['Три пруда'], '兰花', ['орхидея']))
        after, answer_after = question_options(question(), data)
        self.assertEqual(answer_after, answer_before)
        self.assertEqual(after[:len(before)], before)
        self.assertEqual(ids(after)[-1], 'cny-1')


class DossierRecordsTest(unittest.TestCase):
    def test_accepted_question_becomes_an_addition_record(self):
        [record] = dossier_records(dossier(), [question()])
        self.assertEqual(record['id'], 'money-q01')
        self.assertEqual(record['origin'], 'addition')
        self.assertEqual(record['dossier'], 'money')
        self.assertEqual(record['topic'], TOPIC)
        self.assertEqual(record['topicSource'], 'authored')
        self.assertIsNone(record['questionZh'])
        self.assertEqual(record['answer'], {'optionId': 'cny-20', 'state': 'verified'})
        self.assertEqual(record['explanation'], {'ru': question()['explanation']})
        self.assertEqual((record['occurrences'], record['parseWarnings']), ([], []))
        self.assertEqual(len(record['options']), 5)

    def test_draft_stays_out_of_the_bank(self):
        self.assertEqual(dossier_records(dossier(), [question(status='draft')]), [])

    def test_evidence_is_the_answer_row_sources_without_quotes(self):
        [record] = dossier_records(dossier(), [question()])
        self.assertEqual(record['evidence'], [
            {key: value for key, value in source(n).items() if key != 'quote'} for n in (1, 2)])

if __name__ == '__main__':
    unittest.main()
