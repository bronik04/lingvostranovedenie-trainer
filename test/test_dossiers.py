import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from dossiers import cross_leak_errors, dossier_paths, dossier_records, dossier_report, load_dossier, question_options, validate_dossier, validate_links, validate_questions
from editorial import apply_editorial, validate_editorial
from embeds import apply_embeds

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
           'denomination': cell(denomination, gloss=f'Купюра номиналом {denomination.split()[0]}'),
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
            (lambda d: row(d, 'cny-50')['back'].update(gloss='две\nстроки'), 'не в одну строку'),
            (lambda d: row(d, 'cny-50')['back'].update(gloss=''), 'одна непустая строка'),
            (lambda d: row(d, 'cny-50')['back'].update(gloss='Potala Palace on the back'), 'не по-русски'),
            (lambda d: row(d, 'cny-50')['back'].update(gloss='布达拉宫 — дворец в Лхасе'), 'повторяет сам вариант'),
            (lambda d: row(d, 'cny-50')['back'].update(gloss='Потала  в Лхасе'), 'лишние пробелы'),
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


class ValidateQuestionsTest(unittest.TestCase):
    def errors(self, questions, data=None):
        return validate_questions(questions, data or dossier())

    def assertRejects(self, questions, fragment, data=None):
        errors = self.errors(questions, data)
        self.assertTrue(any(fragment in error for error in errors), f'{fragment!r} not in {errors}')

    def test_accepts_a_valid_question(self):
        self.assertEqual(self.errors([question()]), [])

    def test_draft_without_check_is_valid(self):
        draft = question(status='draft')
        draft.pop('check')
        self.assertEqual(self.errors([draft]), [])

    def test_rejects_broken_references(self):
        fact = question()['fact']
        cases = [
            ({**fact, 'table': 'coins'}, 'нет таблицы'),
            ({**fact, 'row': 'cny-3'}, "нет строки 'cny-3'"),
            ({**fact, 'ask': 'series'}, 'не может быть вариантом'),
            ({**fact, 'row': 'rub-500', 'where': {'currency': '卢布'}}, 'нет ячейки flower'),
            ({**fact, 'where': {'series': 'x'}}, 'where'),
            ({**fact, 'where': {'currency': '卢布'}}, 'не проходит where'),
            ({**fact, 'answer': {'row': 'cny-20', 'column': 'flower'}}, 'answer бывает только'),
            ({**fact, 'given': 'flower'}, 'given совпадает с ask'),
            ({**fact, 'colour': 1}, 'неизвестные поля fact'),
        ]
        for broken, fragment in cases:
            with self.subTest(fragment=fragment):
                self.assertRejects([question(fact=broken)], fragment)

    def test_draft_with_broken_reference_still_stops_the_build(self):
        broken = question(status='draft', fact={**question()['fact'], 'row': 'cny-3'})
        self.assertRejects([broken], "нет строки 'cny-3'")

    def test_rejects_bad_exclude(self):
        self.assertRejects([question(exclude=['cny-3'])], 'exclude')
        self.assertRejects([question(exclude=['cny-20'])], 'exclude убирает строку ответа')

    def test_rejects_a_pool_that_is_too_small(self):
        fact = {'table': 'banknotes', 'row': 'rub-500', 'ask': 'back', 'where': {'currency': '卢布'}}
        self.assertRejects([question(fact=fact, questionRu='Что изображено на обороте купюры 500 рублей образца 1997 года?')],
                           'меньше 3 неверных')

    def test_rejects_a_twin_of_the_right_answer(self):
        data = dossier()
        row(data, 'cny-50')['flower'] = cell('荷花', ['лотос'], gloss='Лотос — второй')
        self.assertRejects([question()], 'совпадает с правильным', data)

    def test_rejects_a_wrong_option_without_gloss(self):
        data = dossier()
        row(data, 'cny-50')['flower'].pop('gloss')
        self.assertRejects([question()], 'нет подписи', data)

    def test_rejects_a_question_that_names_its_own_answer(self):
        self.assertRejects([question(questionRu='Какой цветок, 荷花, изображён на купюре 20 юаней 2019 года?')],
                           'называет свой ответ')
        # русское название ловится без учёта регистра
        self.assertRejects([question(questionRu='Лотос ли изображён на купюре 20 юаней выпуска 2019 года?')],
                           'называет свой ответ')

    def test_given_value_must_be_named_in_the_question(self):
        fact = {'table': 'banknotes', 'row': 'cny-50', 'ask': 'denomination', 'given': 'flower',
                'where': {'currency': '人民币'}}
        named = question(fact=fact, questionRu='На купюре какого номинала выпуска 2019 года изображён цветок 菊花?')
        self.assertEqual(self.errors([named]), [])
        self.assertRejects([question(fact=fact, questionRu='На купюре какого номинала 2019 года изображён этот цветок?')],
                           'не называет значение given')

    def test_dated_table_needs_a_year_or_series_in_the_question(self):
        self.assertRejects([question(questionRu='Какой цветок изображён на лицевой стороне купюры 20 юаней?')],
                           'год или серию')
        series = question(questionRu='Какой цветок изображён на купюре 20 юаней пятой серии?')
        self.assertEqual(self.errors([series]), [])

    def test_rejects_a_leak_between_questions(self):
        reverse = question(id='money-q02', fact={'table': 'banknotes', 'row': 'cny-20', 'ask': 'denomination',
                                                 'given': 'flower', 'where': {'currency': '人民币'}},
                           questionRu='На купюре какого номинала выпуска 2019 года изображён цветок 荷花?')
        self.assertRejects([question(), reverse], 'money-q02: текст называет ответ вопроса money-q01')

    def test_rejects_bad_status_check_id_topic_and_fields(self):
        cases = [
            ([question(status='done')], 'status'),
            ([{k: v for k, v in question().items() if k != 'check'}], 'вердикта проверки accept'),
            ([question(check={'verdict': 'fix', 'note': 'неточно'})], 'вердикта проверки accept'),
            ([question(check={'verdict': 'maybe', 'note': ''})], 'verdict'),
            ([question(id='q1')], 'id'),
            ([question(), question()], 'повторяющийся id'),
            ([question(topic='Деньги')], 'тема'),
            ([question(colour=1)], 'неизвестные поля вопроса'),
            ([question(explanation=' ')], 'нет пояснения'),
            ([question(explanation='Одно предложение.')], '3–5 предложений'),
            ('не список', 'списком'),
        ]
        for questions, fragment in cases:
            with self.subTest(fragment=fragment):
                self.assertRejects(questions, fragment)

    def test_rejects_broken_explicit_options(self):
        refs = [{'row': r, 'column': 'back'} for r in ('cny-100', 'cny-50', 'cny-20', 'rub-500')]
        answer = {'row': 'rub-500', 'column': 'back'}
        text = 'Что изображено на обороте купюры 500 рублей образца 1997 года?'
        explicit = lambda **fact: question(fact={'table': 'banknotes', 'options': refs, 'answer': answer, **fact},
                                           questionRu=text)
        self.assertEqual(self.errors([explicit()]), [])
        self.assertRejects([explicit(options=refs[:3])], 'не меньше четырёх')
        self.assertRejects([explicit(options=refs[:3] + [{'row': 'cny-100', 'column': 'flower'}])],
                           'не больше одного варианта')
        self.assertRejects([explicit(answer={'row': 'cny-5', 'column': 'back'})], 'answer — не один из вариантов')
        self.assertRejects([explicit(row='cny-20')], 'не использует')



def embed(**overrides):
    item = {'id': 'money-q02', 'embeds': '2024-25-shk-9', 'status': 'accepted',
            'fact': {'table': 'banknotes', 'row': 'cny-20', 'ask': 'flower', 'where': {'currency': '人民币'}},
            'exclude': [], 'check': {'verdict': 'accept', 'note': 'ок'}}
    item.update(overrides)
    return item


class EmbedQuestionTest(unittest.TestCase):
    def errors(self, questions, data=None):
        return validate_questions(questions, data or dossier())

    def assertRejects(self, questions, fragment, data=None):
        errors = self.errors(questions, data)
        self.assertTrue(any(fragment in error for error in errors), f'{fragment!r} not in {errors}')

    def test_embed_is_valid_without_text_explanation_and_topic(self):
        self.assertEqual(self.errors([embed()]), [])

    def test_embed_does_not_carry_its_own_text(self):
        self.assertRejects([embed(questionRu='Какой цветок на купюре 20 юаней 2019 года?')], 'у встраивания нет полей')
        self.assertRejects([embed(topic=TOPIC)], 'у встраивания нет полей')

    def test_embed_asks_a_column_without_given_or_explicit_options(self):
        self.assertRejects([embed(fact={**embed()['fact'], 'given': 'denomination'})], 'встраивание спрашивает колонку')

    def test_embed_needs_a_target(self):
        self.assertRejects([embed(embeds='')], 'embeds — id записи банка')
        self.assertRejects([embed(embeds=['2024-25-shk-9'])], 'embeds — id записи банка')

    def test_same_record_is_embedded_once(self):
        self.assertRejects([embed(), embed(id='money-q03')], 'уже встроена')

    def test_embed_still_checks_twins_and_glosses(self):
        data = dossier()
        row(data, 'cny-50')['flower'] = cell('荷花', ['лотос'], gloss='Лотос — второй')
        self.assertRejects([embed()], 'совпадает с правильным', data)
        data = dossier()
        row(data, 'cny-50')['flower'].pop('gloss')
        self.assertRejects([embed()], 'нет подписи', data)

    def test_embed_with_a_small_table_pool_is_valid(self):
        # исходные олимпиадные варианты сами дают три неверных
        fact = {'table': 'banknotes', 'row': 'rub-500', 'ask': 'back', 'where': {'currency': '卢布'}}
        self.assertEqual(self.errors([embed(fact=fact)]), [])

    def test_embed_is_not_a_new_record(self):
        self.assertEqual(dossier_records(dossier(), [embed()]), [])

    def test_embed_takes_no_part_in_text_leaks_inside_the_dossier(self):
        # текст встроенного вопроса — в банке; утечки с ним ловит cross_leak_errors (задача 4)
        self.assertEqual(self.errors([question(), embed(fact={**embed()['fact'], 'row': 'cny-50'})]), [])


def plain_row(row_id, **cells):
    return {'id': row_id, **cells, 'sources': [source(1), source(2)], 'olympiad': []}


def myths_dossier():
    figure = lambda row_id, zh, ru: plain_row(row_id, name=cell(zh, [ru], gloss=f'{ru} — персонаж мифа'),
                                              role='персонаж мифа')
    return {'id': 'myths', 'title': 'Мифы и легенды', 'tables': {
        'figures': {'columns': {'name': 'zh', 'role': 'ru'}, 'rows': [
            figure('fig-zhurong', '祝融', 'бог огня Чжужун'),
            figure('fig-change', '嫦娥', 'богиня Чанъэ'),
            figure('fig-xihe', '羲和', 'богиня Сихэ'),
            figure('fig-kuafu', '夸父', 'великан Куафу'),
        ]},
        'stories': {'columns': {'name': 'zh', 'meaning': 'ru'}, 'rows': [
            plain_row('story-niulang-zhinv', name=cell('牛郎织女', ['Пастух и Ткачиха'], gloss='Легенда о Пастухе и Ткачихе'),
                      meaning='народная легенда'),
        ]}}}


def space_dossier():
    mission = lambda row_id, zh, namesake: plain_row(row_id, name=cell(zh, gloss=f'Аппарат {row_id}'), namesake=namesake)
    return {'id': 'space', 'title': 'Космос', 'tables': {
        'missions': {'columns': {'name': 'zh', 'namesake': 'zh'}, 'rows': [
            mission('mis-zhurong', '祝融号', {'zh': '祝融', 'ref': 'myths/figures/fig-zhurong', 'gloss': 'Бог огня Чжужун'}),
            mission('mis-queqiao', '鹊桥', {'zh': '鹊桥', 'from': 'myths/stories/story-niulang-zhinv',
                                           'gloss': 'Сорочий мост из легенды'}),
            mission('mis-wukong', '悟空', {'zh': '悟空', 'gloss': 'Сунь Укун из романа'}),
        ]}}}


class LinksTest(unittest.TestCase):
    def links(self, space=None, myths=None):
        return validate_links({'space': space or space_dossier(), 'myths': myths or myths_dossier()})

    def test_live_links_are_valid(self):
        self.assertEqual(validate_dossier(space_dossier()), [])
        self.assertEqual(self.links(), [])

    def test_ref_to_a_missing_row_is_an_error(self):
        space = space_dossier()
        space['tables']['missions']['rows'][0]['namesake']['ref'] = 'myths/figures/fig-rongzhu'
        self.assertTrue(any('несуществующую строку' in e for e in self.links(space)))

    def test_ref_needs_the_same_name(self):
        myths = myths_dossier()
        myths['tables']['figures']['rows'][0]['name']['zh'] = '祝融氏'
        self.assertTrue(any('другое название' in e for e in self.links(myths=myths)))

    def test_from_only_needs_the_row(self):
        space = space_dossier()
        space['tables']['missions']['rows'][1]['namesake']['from'] = 'myths/stories/story-baishe'
        self.assertTrue(any('несуществующую строку' in e for e in self.links(space)))

    def test_link_format_is_checked_with_the_dossier(self):
        space = space_dossier()
        space['tables']['missions']['rows'][0]['namesake']['ref'] = 'fig-zhurong'
        self.assertTrue(any('досье/таблица/строка' in e for e in validate_dossier(space)))
        space = space_dossier()
        space['tables']['missions']['rows'][0]['namesake']['from'] = 'myths/stories/story-niulang-zhinv'
        self.assertTrue(any('ref или from' in e for e in validate_dossier(space)))


def olympiad(**overrides):
    item = {'id': '2024-25-shk-9', 'questionRu': 'Какой цветок изображён на купюре 20 юаней?', 'questionZh': None,
            'topic': TOPIC, 'options': [{'id': 'o1', 'zh': '荷花'}, {'id': 'o2', 'zh': '菊花'},
                                        {'id': 'o3', 'zh': '梅花'}, {'id': 'o4', 'zh': '水仙花'}],
            'answer': {'optionId': 'o1', 'state': 'verified'},
            'explanation': {'ru': 'На лицевой стороне купюры 20 юаней — лотос.'},
            'occurrences': [{'year': '2024-25', 'stageCode': 'shk', 'number': 9}], 'evidence': []}
    item.update(overrides)
    return item


class ApplyEmbedsTest(unittest.TestCase):
    def apply(self, bank=None, questions=None, glosses=None):
        return apply_embeds(bank or [olympiad()], [(dossier(), questions or [embed()])], glosses or {})

    def assertRejects(self, fragment, **kwargs):
        with self.assertRaises(ValueError) as caught:
            self.apply(**kwargs)
        self.assertIn(fragment, str(caught.exception))

    def test_embedding_adds_the_table_pool_and_glosses_and_keeps_the_question(self):
        [record] = self.apply()
        self.assertEqual([o['id'] for o in record['options']], ['o1', 'o2', 'o3', 'o4', 'cny-10'])
        self.assertEqual(record['questionRu'], olympiad()['questionRu'])
        self.assertEqual(record['occurrences'], olympiad()['occurrences'])
        self.assertEqual(record['answer'], {'optionId': 'o1', 'state': 'verified'})
        self.assertEqual(record['dossier'], 'money')
        self.assertNotIn('gloss', record['options'][0])
        self.assertEqual(record['options'][1]['gloss'], 'Хризантема — цветок на купюре')
        self.assertEqual(record['options'][4], {'id': 'cny-10', 'zh': '月季花', 'gloss': 'Китайская роза — цветок на купюре'})

    def test_only_accepted_embeds_apply_and_the_input_is_untouched(self):
        bank = [olympiad()]
        [record] = apply_embeds(bank, [(dossier(), [embed(status='draft')])], {})
        self.assertIs(record, bank[0])
        self.apply(bank=bank)
        self.assertEqual(len(bank[0]['options']), 4)

    def test_pooled_record_keeps_its_options_and_order(self):
        options = olympiad()['options'] + [{'id': 'o5', 'zh': '月季花'}]
        [record] = self.apply(bank=[olympiad(options=options)])
        self.assertEqual([o['id'] for o in record['options']], ['o1', 'o2', 'o3', 'o4', 'o5'])

    def test_option_with_stray_spaces_finds_its_cell(self):
        options = [{'id': 'o1', 'zh': '荷花'}, {'id': 'o2', 'zh': ' 菊花 '}, {'id': 'o3', 'zh': '梅花'},
                   {'id': 'o4', 'zh': '水仙花'}]
        [record] = self.apply(bank=[olympiad(options=options)])
        self.assertEqual(record['options'][1]['gloss'], 'Хризантема — цветок на купюре')

    def test_rejects_each_broken_embedding(self):
        self.assertRejects('не совпадает с ячейкой', bank=[olympiad(answer={'optionId': 'o2', 'state': 'verified'})])
        options = olympiad()['options'][:3] + [{'id': 'o4', 'zh': '兰花'}]
        self.assertRejects('нет ячейки с подписью', bank=[olympiad(options=options)])
        self.assertRejects('пояснение', bank=[olympiad(explanation={'ru': 'Не 菊花, а лотос.'})])
        self.assertRejects('glosses.json', glosses={'2024-25-shk-9': {'options': {}}})
        self.assertRejects('вопрос досье', bank=[olympiad(dossier='money')])
        self.assertRejects('влита в 2025-26-mun-1',
                           bank=[olympiad(id='2025-26-mun-1', mergedIds=['2024-25-shk-9'])])
        self.assertRejects('в банке нет записи', bank=[olympiad(id='2025-26-mun-1')])

    def test_record_is_embedded_by_one_dossier_only(self):
        with self.assertRaises(ValueError) as caught:
            apply_embeds([olympiad()], [(dossier(), [embed()]), (dossier(), [embed()])], {})
        self.assertIn('уже встроена', str(caught.exception))


def myths_question(**overrides):
    item = {'id': 'myths-q01', 'status': 'draft', 'topic': 'Культура, традиции и праздники',
            'fact': {'table': 'figures', 'row': 'fig-xihe', 'ask': 'name'},
            'questionRu': 'Какая богиня, по преданию, правила колесницей Солнца, а не цветком 荷花?',
            'explanation': 'Первое предложение. Второе предложение. Третье предложение.', 'exclude': []}
    item.update(overrides)
    return item


class CrossLeakTest(unittest.TestCase):
    def test_answer_of_one_dossier_in_the_text_of_another(self):
        loaded = [(dossier(), [question()]), (myths_dossier(), [myths_question()])]
        errors = cross_leak_errors([], loaded)
        self.assertIn("myths/myths-q01: текст называет ответ вопроса money/money-q01: ['荷花']", errors)

    def test_embedded_question_text_comes_from_the_bank(self):
        record = olympiad(questionRu='Кто из богинь — 羲和 — изображён на купюре 20 юаней?')
        loaded = [(dossier(), [embed()]), (myths_dossier(), [myths_question(questionRu='Какая богиня правила колесницей Солнца?')])]
        errors = cross_leak_errors([record], loaded)
        self.assertTrue(any(e.startswith('money/money-q02: текст называет ответ вопроса myths/myths-q01') for e in errors))

    def test_edited_text_in_the_bank_wins_over_the_file(self):
        edited = {'id': 'myths-q01', 'questionRu': 'Какая богиня правила колесницей Солнца?'}
        loaded = [(dossier(), [question()]), (myths_dossier(), [myths_question(status='accepted')])]
        self.assertEqual(cross_leak_errors([edited], loaded), [])

class LoadDossierTest(unittest.TestCase):
    def write(self, directory, name, text):
        path = Path(directory) / name
        path.write_text(text, encoding='utf-8')
        return path

    def test_loads_a_valid_dossier(self):
        with tempfile.TemporaryDirectory() as directory:
            table = self.write(directory, 'money.json', json.dumps(dossier(), ensure_ascii=False))
            questions = self.write(directory, 'money-questions.json', json.dumps([question()], ensure_ascii=False))
            data, loaded = load_dossier(table, questions)
            self.assertEqual((data['id'], [q['id'] for q in loaded]), ('money', ['money-q01']))

    def test_errors_name_the_file(self):
        with tempfile.TemporaryDirectory() as directory:
            broken = dossier()
            broken.pop('title')
            table = self.write(directory, 'money.json', json.dumps(broken, ensure_ascii=False))
            questions = self.write(directory, 'money-questions.json', '[]')
            with self.assertRaisesRegex(ValueError, 'money.json'):
                load_dossier(table, questions)
            table = self.write(directory, 'money.json', json.dumps(dossier(), ensure_ascii=False))
            questions = self.write(directory, 'money-questions.json', '"x"')
            with self.assertRaisesRegex(ValueError, 'money-questions.json'):
                load_dossier(table, questions)

    def test_repeated_key_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            table = self.write(directory, 'money.json', '{"id": "money", "id": "cash"}')
            questions = self.write(directory, 'money-questions.json', '[]')
            with self.assertRaisesRegex(ValueError, 'повторяются ключи'):
                load_dossier(table, questions)


class DossierPathsTest(unittest.TestCase):
    def test_pairs_each_questions_file_with_its_table(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            for name in ('money.json', 'money-questions.json', 'notes.md'):
                (base / name).write_text('[]', encoding='utf-8')
            self.assertEqual(dossier_paths(base), [(base / 'money.json', base / 'money-questions.json')])

    def test_questions_without_a_table_are_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'money-questions.json').write_text('[]', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'money.json'):
                dossier_paths(Path(directory))


class EditorialOnDossierRecordTest(unittest.TestCase):
    def test_option_is_addressed_by_its_row_id(self):
        [record] = dossier_records(dossier(), [question()])
        edits = {'money-q01': {'reason': 'опечатка', 'options': {'cny-50': '菊'}}}
        self.assertEqual(validate_editorial(edits, [record]), [])
        [edited] = apply_editorial([record], edits)
        self.assertEqual(next(o['zh'] for o in edited['options'] if o['id'] == 'cny-50'), '菊')


class DossierInBankTest(unittest.TestCase):
    """Каждый принятый вопрос досье доходит до data/bank.json, черновики — нет."""

    def setUp(self):
        self.bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        self.pairs = dossier_paths(ROOT / 'data/dossiers')

    def test_money_dossier_is_part_of_the_build(self):
        self.assertIn((ROOT / 'data/dossiers/money.json', ROOT / 'data/dossiers/money-questions.json'), self.pairs)

    def test_accepted_questions_reach_the_bank_and_drafts_do_not(self):
        for table_path, questions_path in self.pairs:
            data, questions = load_dossier(table_path, questions_path)
            for item in questions:
                if item['status'] != 'accepted':
                    self.assertNotIn(item['id'], self.bank)
                    continue
                record = self.bank[item['id']]
                options, answer_id = question_options(item, data)
                self.assertEqual(record['answer']['optionId'], answer_id, item['id'])
                self.assertEqual([o['id'] for o in record['options']], [o['id'] for o in options], item['id'])
                self.assertTrue(all(o.get('gloss') for o in record['options'] if o['id'] != answer_id), item['id'])

    def test_olympiad_links_point_to_bank_questions(self):
        # олимпиадный вопрос мог быть влит склейкой в другой — его id тогда в mergedIds
        known = set(self.bank) | {i for r in self.bank.values() for i in r.get('mergedIds', [])}
        for table_path, questions_path in self.pairs:
            data, _ = load_dossier(table_path, questions_path)
            for table in data['tables'].values():
                for item in table['rows']:
                    for olympiad_id in item.get('olympiad', []):
                        self.assertIn(olympiad_id, known, item['id'])


class DossierReportTest(unittest.TestCase):
    def test_report_lists_tables_and_every_question(self):
        draft = question(id='money-q02', status='draft', check={'verdict': 'fix', 'note': 'неточно'},
                         fact={'table': 'banknotes', 'row': 'cny-50', 'ask': 'back', 'where': {'currency': '人民币'}},
                         questionRu='Что изображено на обороте купюры 50 юаней выпуска 2019 года?')
        report = dossier_report(dossier(), [question(), draft])
        self.assertTrue(report.startswith('# Досье «Деньги»\n'))
        self.assertIn('## Таблица `banknotes` — строк: 6', report)
        self.assertIn('| cny-50 | 人民币 | 50 元 | пятая серия, выпуск 2019 года | 布达拉宫 (Потала) | 菊花 (хризантема) |  |', report)
        self.assertIn('## Вопросы — принято 1 из 2', report)
        self.assertIn('### money-q02 · draft · проверка: fix', report)
        self.assertIn('- Ответ: 布达拉宫', report)
        # подписи принимает автор — значит, он их видит в отчёте
        self.assertIn('- Неверные:\n  - 人民大会堂 — Дом народных собраний — на обороте купюры\n'
                      '  - 桂林山水 — Гуйлинь — на обороте купюры\n', report)
        self.assertIn('- Замечание проверки: неточно', report)
        self.assertTrue(report.endswith('\n') and not report.endswith('\n\n'))

    def test_question_without_check_says_so(self):
        draft = question(status='draft')
        draft.pop('check')
        self.assertIn('### money-q01 · draft · проверка: нет', dossier_report(dossier(), [draft]))

class ReviewFindingsTest(unittest.TestCase):
    """Замечания ревью ветки 2026-10-14: проверка досье не пропускает то, что потом остановит сборку."""

    def errors(self, questions, data=None, bank=None):
        return validate_questions(questions, data or dossier(), bank)

    def assertRejects(self, questions, fragment, data=None, bank=None):
        errors = self.errors(questions, data, bank)
        self.assertTrue(any(fragment in error for error in errors), f'{fragment!r} not in {errors}')

    def test_four_digit_denomination_is_not_a_year(self):
        for text in ('Какой цветок изображён на лицевой стороне купюры 2000 юаней?',
                     'Какой цветок изображён на купюре в 1000 рублей?'):
            with self.subTest(text=text):
                self.assertRejects([question(questionRu=text)], 'год или серию')
        self.assertEqual(self.errors([question(questionRu='Какой цветок изображён на купюре 20 юаней образца 2019 года?')]), [])

    def test_inflected_answer_is_still_a_hint(self):
        data = dossier()
        hint = question(fact={'table': 'banknotes', 'row': 'cny-50', 'ask': 'flower', 'where': {'currency': '人民币'}},
                        questionRu='Хризантемой ли украшена купюра 50 юаней выпуска 2019 года?')
        self.assertRejects([hint], 'называет свой ответ', data)

    def test_inflected_multiword_answer_is_still_a_leak(self):
        back = question(fact={'table': 'banknotes', 'row': 'cny-100', 'ask': 'back', 'where': {'currency': '人民币'}},
                        questionRu='Что изображено на обороте купюры 100 юаней выпуска 2015 года?')
        other = question(id='money-q02', questionRu='Какой цветок соседствует с изображением Дома народных собраний на купюре 2019 года?')
        self.assertRejects([back, other], 'money-q02: текст называет ответ вопроса money-q01')

    def test_question_text_rules_of_the_build_apply_to_drafts(self):
        cases = [
            ('какой цветок изображён на купюре 20 юаней выпуска 2019 года?', 'заглавной'),
            ('Какой цветок изображён на купюре 20 юаней выпуска 2019 года', 'без знака препинания'),
            ('Which flower is on the 20 yuan note of 2019?', 'не по-русски'),
        ]
        for text, fragment in cases:
            with self.subTest(fragment=fragment):
                self.assertRejects([question(status='draft', questionRu=text)], fragment)

    def test_repeated_or_truncated_wording_is_caught_before_acceptance(self):
        first = question(status='draft')
        same = question(id='money-q02', status='draft', fact={**question()['fact'], 'row': 'cny-50'})
        self.assertRejects([first, same], 'повторяет формулировку money-q01')
        longer = question(id='money-q02', status='draft', fact={**question()['fact'], 'row': 'cny-50'},
                          questionRu=question()['questionRu'][:-1] + ' пятой серии?')
        self.assertRejects([first, longer], 'обрезком')
        bank = [{'id': '2024-25-shk-1', 'questionRu': question()['questionRu']}]
        self.assertRejects([first], 'уже есть в базе', bank=bank)

    def test_question_without_id_is_reported_not_crashed(self):
        nameless = question()
        nameless.pop('id')
        self.assertRejects([nameless], 'вопрос 1: id')

    def test_malformed_values_are_reported_not_crashed(self):
        fact = question()['fact']
        broken_questions = [
            question(fact={**fact, 'row': ['cny-20']}),
            question(fact={**fact, 'table': ['banknotes']}),
            question(fact={**fact, 'ask': ['flower']}),
            question(exclude=[{'row': 'cny-5'}]),
            question(status=['accepted']),
            question(check={'verdict': ['accept']}),
            question(id=['money-q01']),
            question(fact={'table': 'banknotes', 'options': [{'row': ['cny-1'], 'column': 'back'}] * 4,
                           'answer': {'row': ['cny-1'], 'column': 'back'}}),
        ]
        for broken in broken_questions:
            with self.subTest(question=broken):
                self.assertTrue(self.errors([broken]))
        broken_dossiers = [
            lambda d: d['tables']['banknotes']['columns'].update(back=['zh']),
            lambda d: d['tables']['banknotes'].update(required=[{'series': 1}]),
            lambda d: row(d, 'cny-50')['sources'][0].update(url=['https://x']),
        ]
        for mutate in broken_dossiers:
            data = dossier()
            mutate(data)
            with self.subTest(mutate=mutate):
                self.assertTrue(validate_dossier(data))

if __name__ == '__main__':
    unittest.main()
