import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from dossiers import validate_dossier

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


if __name__ == '__main__':
    unittest.main()
