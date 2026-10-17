import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from dossiers import REPORT_MARK, check_dossiers, cross_leak_errors, dossier_paths, embed_record, original_record, dossier_records, dossier_report, is_build_report, load_dossier, question_options, validate_dossier, validate_links, validate_questions, write_dossier_reports
from editorial import apply_editorial, validate_editorial
from embeds import apply_embeds, embed_errors

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
            (lambda d: row(d, 'cny-50').update(id='o5'), 'зарезервирован'),
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
        self.assertRejects('вопрос досье', bank=[olympiad(id='money-q01')],
                           questions=[question(), embed(embeds='money-q01')])
        self.assertRejects('влита в 2025-26-mun-1',
                           bank=[olympiad(id='2025-26-mun-1', mergedIds=['2024-25-shk-9'])])
        self.assertRejects('в банке нет записи', bank=[olympiad(id='2025-26-mun-1')])

    def test_pool_is_added_after_the_options_of_a_pooled_record(self):
        options = olympiad()['options'] + [{'id': 'o5', 'zh': '牡丹'}]
        data = dossier()
        row(data, 'rub-500')['flower'] = cell('牡丹', ['пион'], gloss='Пион — цветок')
        [record] = apply_embeds([olympiad(options=options)], [(data, [embed()])], {})
        self.assertEqual([o['id'] for o in record['options']], ['o1', 'o2', 'o3', 'o4', 'o5', 'cny-10'])
        self.assertEqual(record['options'][4]['gloss'], 'Пион — цветок')

    def test_original_option_takes_the_gloss_of_its_own_pool(self):
        # строка рубля с тем же цветком стоит раньше юаней: подпись берётся из набора вопроса (where)
        data = dossier()
        data['tables']['banknotes']['rows'].insert(0, note('rub-50', '卢布', '50 卢布', '圣彼得堡', ['Петербург'],
                                                          '菊花', ['хризантема рублёвая'], series='образца 1997 года'))
        row(data, 'rub-50')['flower']['gloss'] = 'Хризантема рублёвая'
        [record] = apply_embeds([olympiad()], [(data, [embed()])], {})
        self.assertEqual(record['options'][1]['gloss'], 'Хризантема — цветок на купюре')

    def test_ambiguous_gloss_outside_the_pool_is_an_error(self):
        data = dossier()
        data['tables']['banknotes']['rows'].insert(0, note('rub-50', '卢布', '50 卢布', '圣彼得堡', ['Петербург'],
                                                          '菊花', ['хризантема рублёвая'], series='образца 1997 года'))
        row(data, 'rub-50')['flower']['gloss'] = 'Хризантема рублёвая'
        with self.assertRaises(ValueError) as caught:
            apply_embeds([olympiad()], [(data, [embed(exclude=['cny-50'])])], {})
        self.assertIn('несколько подписей', str(caught.exception))

    def test_unverified_answer_is_not_embedded(self):
        self.assertRejects('не проверен', bank=[olympiad(answer={'optionId': None, 'state': 'needs-review'})])

    def test_explanation_may_contain_the_answer_that_contains_a_wrong_option(self):
        data = dossier()
        row(data, 'cny-20')['flower'] = cell('荷花王', ['царский лотос'], gloss='Царский лотос')
        row(data, 'cny-50')['flower'] = cell('荷花', ['лотос'], gloss='Лотос — цветок')
        # неверный 荷花 — часть ответа 荷花王; пояснение называет ответ, а не неверный вариант
        options = [{'id': 'o1', 'zh': '荷花王'}, {'id': 'o2', 'zh': '荷花'}] + olympiad()['options'][2:]
        record = olympiad(options=options, explanation={'ru': 'Это 荷花王 — царский лотос.'})
        [embedded] = apply_embeds([record], [(data, [embed()])], {})
        self.assertEqual(embedded['dossier'], 'money')

    def test_row_id_that_collides_with_an_option_id_is_an_error(self):
        data = dossier()
        row(data, 'cny-10')['id'] = 'o5'
        options = olympiad()['options'] + [{'id': 'o5', 'zh': '牡丹'}]
        with self.assertRaises(ValueError) as caught:
            apply_embeds([olympiad(options=options)], [(data, [embed()])], {})
        self.assertIn('совпадает с id варианта', str(caught.exception))

    def test_embedding_a_built_record_again_gives_the_same_result(self):
        # bank.json после сборки: у записи уже есть добавленные варианты и подписи
        [built] = self.apply()
        preview, problems = embed_record(original_record(built), embed(), dossier())
        self.assertEqual((preview, problems), (built, []))

    def test_drafts_are_checked_on_request(self):
        draft = embed(status='draft')
        bad = [olympiad(answer={'optionId': 'o2', 'state': 'verified'})]
        self.assertEqual(embed_errors(bad, [(dossier(), [draft])], {}), [])
        self.assertTrue(any('не совпадает' in e for e in embed_errors(bad, [(dossier(), [draft])], {}, drafts=True)))

    def test_draft_embed_may_keep_glosses_until_it_is_accepted(self):
        # пока вопрос — черновик, банк живёт с подписями glosses.json; ячейки заменяют их при принятии
        glosses = {'2024-25-shk-9': {'options': {}}}
        draft = embed(status='draft')
        self.assertEqual(embed_errors([olympiad()], [(dossier(), [draft])], glosses, drafts=True), [])
        accepted = embed()
        self.assertTrue(any('glosses.json' in e for e in embed_errors([olympiad()], [(dossier(), [accepted])], glosses, drafts=True)))

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


class LocalLeakBridgeTest(unittest.TestCase):
    def fixture(self):
        pairs = [('sakha', '萨哈族', 'саха', '萨哈共和国', 'Якутия', 'olonkho', '奥隆霍', 'олонхо'),
                 ('tuva', '图瓦人', 'тувинцы', '图瓦共和国', 'Тыва', 'khoomei', '图瓦呼麦', 'хоомей'),
                 ('kalmyk', '卡尔梅克人', 'калмыки', '卡尔梅克共和国', 'Калмыкия',
                  'jangar', '卡尔梅克《江格尔》', 'Джангар'),
                 ('buryat', '布里亚特人', 'буряты', '布里亚特共和国', 'Бурятия', 'geser', '格斯尔', 'Гэсэр')]
        people, traditions = [], []
        for pid, pzh, pru, rzh, rru, tid, tzh, tru in pairs:
            people.append(plain_row(pid, name=cell(pzh, [pru], gloss=pru.capitalize()),
                                    region=cell(rzh, [rru], gloss=rru),
                                    heritage=cell(tzh, [tru], gloss=tru.capitalize())))
            traditions.append(plain_row(tid, name=cell(tzh, [tru], gloss=tru.capitalize()),
                                        people=cell(pzh, [pru], gloss=pru.capitalize())))
        data = {'id': 'ethnos', 'title': 'Этносы', 'tables': {
            'peoples': {'columns': {'name': 'zh', 'region': 'zh', 'heritage': 'zh'}, 'rows': people},
            'heritage': {'columns': {'name': 'zh', 'people': 'zh'}, 'rows': traditions}}}
        questions = [
            question(id='ethnos-q01', status='draft',
                     fact={'table': 'peoples', 'row': 'sakha', 'ask': 'name'},
                     questionRu='Какой народ сохраняет традицию олонхо?'),
            question(id='ethnos-q02', status='draft',
                     fact={'table': 'heritage', 'row': 'olonkho', 'ask': 'name'},
                     questionRu='Как называется героический эпос народа саха?')]
        return data, questions

    @staticmethod
    def leaks(errors, label, other):
        return [error for error in errors if error.startswith(f'{label}: текст называет ответ вопроса {other}:')]

    def test_a_question_may_name_the_row_its_row_links_to(self):
        # у саха ячейка наследия ссылается на олонхо: вопрос о саха может назвать олонхо
        for field in ('ref', 'from'):
            with self.subTest(field=field):
                data, questions = self.fixture()
                data['tables']['peoples']['rows'][0]['heritage'][field] = 'ethnos/heritage/olonkho'
                self.assertEqual(validate_links({'ethnos': data}), [])
                errors = validate_questions(questions, data)
                self.assertEqual(self.leaks(errors, 'ethnos-q01', 'ethnos-q02'), [], errors)

    def test_a_link_does_not_let_the_target_name_the_linking_row(self):
        # ссылка только у саха: вопрос об олонхо, назвавший саха, выдаёт ответ «какой народ…»
        data, questions = self.fixture()
        data['tables']['peoples']['rows'][0]['heritage']['ref'] = 'ethnos/heritage/olonkho'
        errors = validate_questions(questions, data)
        self.assertEqual(self.leaks(errors, 'ethnos-q02', 'ethnos-q01'), [
            "ethnos-q02: текст называет ответ вопроса ethnos-q01: ['саха']"])

    def test_questions_of_one_fact_group_are_not_leaks(self):
        # группа фактов — решение автора «это один факт»: так он закрывает такую пару
        data, questions = self.fixture()
        data['tables']['peoples']['rows'][0]['heritage']['ref'] = 'ethnos/heritage/olonkho'
        groups = {'sakha-olonkho': ['ethnos-q01', 'ethnos-q02']}
        self.assertEqual(validate_questions(questions, data, groups=groups), [])
        other = {'sakha-other': ['ethnos-q01', 'ethnos-q09'], 'olonkho-other': ['ethnos-q02', 'ethnos-q08']}
        self.assertEqual(len(self.leaks(validate_questions(questions, data, groups=other), 'ethnos-q02', 'ethnos-q01')), 1)

    def test_explicit_options_answer_column_decides_the_bridge(self):
        # колонка ответа вопроса с явными вариантами — из fact.answer, а не из ask
        data, _ = self.fixture()
        data['tables']['peoples']['rows'][0]['heritage']['ref'] = 'ethnos/heritage/olonkho'
        about_sakha = question(id='ethnos-q01', status='draft',
                               fact={'table': 'peoples', 'row': 'sakha', 'ask': 'region'},
                               questionRu='Где живёт большинство народа саха, хранящего олонхо?')
        rows = ('olonkho', 'khoomei', 'jangar', 'geser')
        for column, leaks in (('name', []), ('people', ["ethnos-q01: текст называет ответ вопроса ethnos-q02: ['саха']"])):
            with self.subTest(column=column):
                explicit = question(id='ethnos-q02', status='draft', fact={
                    'table': 'heritage', 'options': [{'row': r, 'column': column} for r in rows],
                    'answer': {'row': 'olonkho', 'column': column}},
                    questionRu='Какая традиция — героический эпос, исполняемый речитативом и пением?')
                errors = validate_questions([about_sakha, explicit], data)
                self.assertEqual(self.leaks(errors, 'ethnos-q01', 'ethnos-q02'), leaks, errors)

    def test_links_both_ways_let_both_questions_name_each_other(self):
        data, questions = self.fixture()
        data['tables']['peoples']['rows'][0]['heritage']['ref'] = 'ethnos/heritage/olonkho'
        data['tables']['heritage']['rows'][0]['people']['ref'] = 'ethnos/peoples/sakha'
        self.assertEqual(validate_links({'ethnos': data}), [])
        self.assertEqual(validate_questions(questions, data), [])

    def test_a_question_may_name_the_linking_cell_that_points_to_its_row(self):
        # вопрос «какой эпос у народа Якутии» отвечает связующей ячейкой, она называет строку олонхо
        data, _ = self.fixture()
        data['tables']['peoples']['rows'][0]['heritage']['ref'] = 'ethnos/heritage/olonkho'
        questions = [
            question(id='ethnos-q01', status='draft',
                     fact={'table': 'peoples', 'row': 'sakha', 'ask': 'heritage'},
                     questionRu='Какую эпическую традицию сохраняет народ Якутии?'),
            question(id='ethnos-q02', status='draft',
                     fact={'table': 'heritage', 'row': 'olonkho', 'ask': 'people'},
                     questionRu='Какой народ сохраняет олонхо?')]
        self.assertEqual(validate_questions(questions, data), [])

    def test_a_link_does_not_exempt_other_columns_of_the_linked_row(self):
        # связь саха ↔ олонхо не разрешает вопросу об олонхо называть регион саха
        data, _ = self.fixture()
        data['tables']['peoples']['rows'][0]['heritage']['ref'] = 'ethnos/heritage/olonkho'
        data['tables']['heritage']['rows'][0]['people']['ref'] = 'ethnos/peoples/sakha'
        questions = [
            question(id='ethnos-q01', status='draft',
                     fact={'table': 'peoples', 'row': 'sakha', 'ask': 'region'},
                     questionRu='Где живёт большинство народа саха?'),
            question(id='ethnos-q02', status='draft',
                     fact={'table': 'heritage', 'row': 'olonkho', 'ask': 'name'},
                     questionRu='Как называется эпос, который сохраняют в Якутии?')]
        errors = validate_questions(questions, data)
        self.assertEqual(self.leaks(errors, 'ethnos-q02', 'ethnos-q01'), [
            "ethnos-q02: текст называет ответ вопроса ethnos-q01: ['Якутия']"])

    def test_a_link_on_another_row_does_not_hide_a_leak(self):
        data, questions = self.fixture()
        data['tables']['peoples']['rows'][1]['heritage']['from'] = 'ethnos/heritage/olonkho'
        errors = validate_questions(questions, data)
        self.assertTrue(any('текст называет ответ вопроса' in error for error in errors), errors)

    def test_a_bridge_does_not_hide_a_leak_to_an_unlinked_row(self):
        # у вопроса есть связь, но текст называет ответ вопроса о другой, несвязанной строке
        data, questions = self.fixture()
        data['tables']['peoples']['rows'][0]['heritage']['ref'] = 'ethnos/heritage/olonkho'
        questions[0]['questionRu'] = 'Какой народ сохраняет олонхо, а не хоомей?'
        questions.append(question(id='ethnos-q03', status='draft',
                                  fact={'table': 'heritage', 'row': 'khoomei', 'ask': 'name'},
                                  questionRu='Как называется горловое пение тувинцев?'))
        errors = validate_questions(questions, data)
        self.assertTrue(any('ethnos-q03' in error for error in errors), errors)

    def test_a_bridge_does_not_allow_naming_its_own_answer(self):
        data, questions = self.fixture()
        data['tables']['peoples']['rows'][0]['heritage']['ref'] = 'ethnos/heritage/olonkho'
        questions[0]['questionRu'] = 'Какой народ, саха, сохраняет традицию олонхо?'
        errors = validate_questions(questions, data)
        self.assertTrue(any('называет свой ответ' in error for error in errors), errors)


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

class CrossLeakChineseTextTest(unittest.TestCase):
    def test_chinese_text_of_an_embedded_question_counts(self):
        record = olympiad(questionZh='哪位女神驾驶太阳车？羲和')
        loaded = [(dossier(), [embed()]), (myths_dossier(), [myths_question(questionRu='Какая богиня правила колесницей Солнца?')])]
        self.assertTrue(any(e.startswith('money/money-q02') for e in cross_leak_errors([record], loaded)))


def launches():
    mission = lambda row_id, zh, year, namesake: plain_row(row_id, name=cell(zh, gloss=f'Аппарат {zh}'),
                                                           year=cell(year, gloss=f'{year} — запуск'), namesake=namesake)
    return {'id': 'space', 'title': 'Космос', 'tables': {'missions': {
        'columns': {'name': 'zh', 'year': 'zh', 'namesake': 'zh'}, 'rows': [
            mission('mis-change4', '嫦娥四号', '2018 年', {'zh': '嫦娥', 'ref': 'myths/figures/fig-change', 'gloss': 'Богиня Луны'}),
            mission('mis-zhurong', '祝融号', '2020 年', {'zh': '祝融', 'ref': 'myths/figures/fig-zhurong', 'gloss': 'Бог огня'}),
        ]}}}


def change_question():
    return myths_question(fact={'table': 'figures', 'row': 'fig-change', 'ask': 'name'},
                          questionRu='Какая богиня, по преданию, улетела на Луну?')


class CrossLeakBridgeTest(unittest.TestCase):
    def test_naming_a_craft_after_its_myth_is_not_a_leak(self):
        year = {'id': 'space-q01', 'status': 'draft', 'fact': {'table': 'missions', 'row': 'mis-change4', 'ask': 'year'},
                'questionRu': 'В каком году запущен лунный аппарат 嫦娥四号?'}
        errors = cross_leak_errors([], [(myths_dossier(), [change_question()]), (launches(), [year])])
        self.assertEqual(errors, [])

    def test_naming_the_myth_in_a_question_about_another_craft_is_still_a_leak(self):
        year = {'id': 'space-q02', 'status': 'draft', 'fact': {'table': 'missions', 'row': 'mis-zhurong', 'ask': 'year'},
                'questionRu': 'В каком году запущен марсоход 祝融号 — младший брат станций 嫦娥?'}
        errors = cross_leak_errors([], [(myths_dossier(), [change_question()]), (launches(), [year])])
        self.assertTrue(any(e.startswith('space/space-q02: текст называет ответ вопроса myths/myths-q01') for e in errors))

    def test_a_myth_question_may_not_name_another_column_of_the_craft(self):
        # аппарат назван по Чанъэ, но вопрос о мифе, назвавший сам аппарат, выдаёт ответ вопроса о нём
        craft = {'id': 'space-q03', 'status': 'draft', 'fact': {'table': 'missions', 'row': 'mis-change4', 'ask': 'name'},
                 'questionRu': 'Какой аппарат в 2018 году отправился к обратной стороне Луны?'}
        myth = myths_question(fact={'table': 'figures', 'row': 'fig-change', 'ask': 'name'},
                              questionRu='Какая богиня улетела на Луну и дала имя аппарату 嫦娥四号?')
        errors = cross_leak_errors([], [(myths_dossier(), [myth]), (launches(), [craft])])
        self.assertTrue(any(e.startswith('myths/myths-q01: текст называет ответ вопроса space/space-q03')
                            for e in errors), errors)
        grouped = cross_leak_errors([], [(myths_dossier(), [myth]), (launches(), [craft])],
                                    groups={'change-craft': ['myths-q01', 'space-q03']})
        self.assertEqual(grouped, [])

    def test_an_embedded_question_joins_a_fact_group_by_its_record_id(self):
        record = olympiad(questionRu='Кто из богинь — 羲和 — изображён на купюре 20 юаней?')
        loaded = [(dossier(), [embed()]), (myths_dossier(), [myths_question(questionRu='Какая богиня правила колесницей Солнца?')])]
        self.assertEqual(cross_leak_errors([record], loaded, groups={'xihe': ['2024-25-shk-9', 'myths-q01']}), [])

    def test_single_character_answer_of_another_dossier_is_not_searched(self):
        era = question(id='money-q05', fact={'table': 'banknotes', 'row': 'cny-20', 'ask': 'flower'})
        data = dossier()
        row(data, 'cny-20')['flower'] = cell('唐', gloss='Эпоха Тан')
        monk = myths_question(questionRu='Кто сопровождал монаха 唐僧 в романе — по преданию?')
        self.assertEqual(cross_leak_errors([], [(data, [era]), (myths_dossier(), [monk])]), [])


class CheckDossiersTest(unittest.TestCase):
    def write(self, directory, name, data):
        (Path(directory) / name).write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

    def test_one_broken_dossier_does_not_hide_the_others(self):
        with tempfile.TemporaryDirectory() as directory:
            broken = myths_dossier()
            broken.pop('title')
            self.write(directory, 'myths.json', broken)
            self.write(directory, 'myths-questions.json', [])
            self.write(directory, 'money.json', dossier())
            self.write(directory, 'money-questions.json', [question(questionRu='Какой цветок, 荷花, на купюре 2019 года?')])
            errors, loaded = check_dossiers(Path(directory), [], {})
        self.assertTrue(any('myths.json' in e for e in errors))
        self.assertTrue(any('называет свой ответ' in e for e in errors))
        self.assertEqual(loaded, [])

    def test_draft_embeds_are_checked_against_the_bank(self):
        with tempfile.TemporaryDirectory() as directory:
            self.write(directory, 'money.json', dossier())
            self.write(directory, 'money-questions.json', [embed(status='draft')])
            errors, loaded = check_dossiers(Path(directory), [olympiad(answer={'optionId': 'o2', 'state': 'verified'})], {})
        self.assertTrue(any('не совпадает' in e for e in errors))
        self.assertEqual([d['id'] for d, _ in loaded], ['money'])

    def test_wording_of_an_embedded_record_counts_as_taken(self):
        [built] = apply_embeds([olympiad()], [(dossier(), [embed()])], {})
        twin = question(id='money-q04', status='draft', questionRu=built['questionRu'])
        with tempfile.TemporaryDirectory() as directory:
            self.write(directory, 'money.json', dossier())
            self.write(directory, 'money-questions.json', [embed(), twin])
            errors, _ = check_dossiers(Path(directory), [built], {})
        self.assertTrue(any('уже есть в базе' in e for e in errors), errors)


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

    def test_accepted_questions_reach_the_bank_and_drafts_do_not(self):
        for table_path, questions_path in self.pairs:
            data, questions = load_dossier(table_path, questions_path)
            for item in questions:
                if 'embeds' in item:
                    continue
                if item['status'] != 'accepted':
                    self.assertNotIn(item['id'], self.bank)
                    continue
                record = self.bank[item['id']]
                options, answer_id = question_options(item, data)
                self.assertEqual(record['answer']['optionId'], answer_id, item['id'])
                self.assertEqual([o['id'] for o in record['options']], [o['id'] for o in options], item['id'])
                self.assertTrue(all(o.get('gloss') for o in record['options'] if o['id'] != answer_id), item['id'])

    def test_accepted_embeds_reach_the_bank(self):
        for table_path, questions_path in self.pairs:
            data, questions = load_dossier(table_path, questions_path)
            for item in questions:
                if 'embeds' not in item or item['status'] != 'accepted':
                    continue
                record = self.bank[item['embeds']]
                answer = next(o for o in record['options'] if o['id'] == record['answer']['optionId'])
                self.assertEqual(record.get('dossier'), data['id'], item['id'])
                self.assertEqual(answer['zh'].strip(), question_options(item, data)[0][0]['zh'], item['id'])
                self.assertTrue(all(o.get('gloss') for o in record['options'] if o is not answer), item['id'])
                # исходные варианты на месте, набор из таблицы добавлен: сборка повторяема
                self.assertEqual(embed_record(original_record(record), item, data), (record, []), item['id'])

    def test_links_between_dossiers_are_alive(self):
        loaded = {}
        for table_path, questions_path in self.pairs:
            data, _ = load_dossier(table_path, questions_path)
            loaded[data['id']] = data
        self.assertEqual(validate_links(loaded), [])

    def test_all_dossiers_are_part_of_the_build(self):
        names = {table.name for table, _ in self.pairs}
        self.assertEqual(names, {'money.json', 'myths.json', 'space.json', 'holidays.json', 'dynasties.json',
                                 'ethnos.json', 'provinces.json', 'landmarks.json', 'literature.json',
                                 'painting.json'})

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
        self.assertTrue(report.startswith(REPORT_MARK + '\n# Досье «Деньги»\n'))
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

    def test_embed_shows_the_olympiad_question_and_its_options(self):
        [record] = apply_embeds([olympiad()], [(dossier(), [embed()])], {})
        report = dossier_report(dossier(), [embed()], [record])
        self.assertIn('### money-q02 · accepted · проверка: accept · встраивает 2024-25-shk-9', report)
        self.assertIn(olympiad()['questionRu'], report)
        self.assertIn('  - 月季花 — Китайская роза — цветок на купюре', report)

    def test_draft_embed_shows_the_olympiad_question_and_the_preview(self):
        report = dossier_report(dossier(), [embed(status='draft')], [olympiad()])
        self.assertIn(olympiad()['questionRu'], report)
        self.assertIn('  - 菊花 — Хризантема — цветок на купюре', report)
        self.assertIn('  - 月季花 — Китайская роза — цветок на купюре', report)

    def test_embed_problems_are_shown_in_the_report(self):
        report = dossier_report(dossier(), [embed(status='draft')],
                                [olympiad(explanation={'ru': 'Не 菊花, а лотос.'})])
        self.assertIn('- Ошибка встраивания: пояснение 2024-25-shk-9 называет неверные варианты', report)

    def test_embed_of_a_missing_record_says_so(self):
        report = dossier_report(dossier(), [embed()])
        self.assertIn('встраивает 2024-25-shk-9; такой записи нет в банке', report)

    def test_report_shows_links(self):
        report = dossier_report(space_dossier(), [])
        self.assertIn('祝融 → myths/figures/fig-zhurong', report)

    def test_question_without_check_says_so(self):
        draft = question(status='draft')
        draft.pop('check')
        self.assertIn('### money-q01 · draft · проверка: нет', dossier_report(dossier(), [draft]))


class WriteDossierReportsTest(unittest.TestCase):
    """17.10.2026 слияние молча затёрло ручной отчёт «Этносов» отчётом сборки под тем же именем."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.dir = Path(directory.name)
        self.path = self.dir / 'dossier-money.md'

    def test_build_report_is_overwritten(self):
        self.path.write_text(dossier_report(dossier(), []), encoding='utf-8')
        fresh = dossier_report(dossier(), [question()])
        write_dossier_reports({self.path: fresh})
        self.assertEqual(self.path.read_text('utf-8'), fresh)

    def test_missing_report_is_written(self):
        write_dossier_reports({self.path: dossier_report(dossier(), [])})
        self.assertTrue(is_build_report(self.path.read_text('utf-8')))

    def test_report_written_before_the_mark_is_overwritten(self):
        self.path.write_text('# Досье «Деньги»\n\nФайл пишет сборка (`scripts/dossiers.py`). Править — '
                             '`data/dossiers/money.json`.\n', encoding='utf-8')
        write_dossier_reports({self.path: dossier_report(dossier(), [])})
        self.assertTrue(self.path.read_text('utf-8').startswith(REPORT_MARK))

    def test_manual_report_stops_the_build_and_nothing_is_written(self):
        manual = '# Досье «Деньги»: таблицы\n\nЭтап: сбор и сверка фактов.\n'
        self.path.write_text(manual, encoding='utf-8')
        other = self.dir / 'dossier-space.md'
        with self.assertRaises(ValueError) as caught:
            write_dossier_reports({other: dossier_report(space_dossier(), []),
                                   self.path: dossier_report(dossier(), [])})
        self.assertIn('dossier-money.md написан не сборкой', str(caught.exception))
        self.assertIn('переименуйте ручной отчёт в dossier-money-<что>.md', str(caught.exception))
        self.assertEqual(self.path.read_text('utf-8'), manual)
        self.assertFalse(other.exists())

    def test_mark_must_open_the_file(self):
        # метка в середине ручного отчёта (скопированный кусок) его не делает отчётом сборки
        self.assertFalse(is_build_report('# Заметки\n\n' + REPORT_MARK + '\n'))

    def test_build_report_with_bom_is_overwritten(self):
        self.path.write_text('\ufeff' + dossier_report(dossier(), []), encoding='utf-8')
        write_dossier_reports({self.path: dossier_report(dossier(), [])})
        self.assertTrue(self.path.read_text('utf-8').startswith(REPORT_MARK))

    def test_check_without_build_finds_a_manual_report(self):
        # то, что остановит сборку, видно уже в `python3 scripts/dossiers.py`
        dossiers = self.dir / 'dossiers'
        dossiers.mkdir()
        (dossiers / 'money.json').write_text(json.dumps(dossier(), ensure_ascii=False), encoding='utf-8')
        (dossiers / 'money-questions.json').write_text('[]', encoding='utf-8')
        self.assertEqual(check_dossiers(dossiers, [], {}, reports=self.dir)[0], [])
        self.path.write_text('# Досье «Деньги»: таблицы\n', encoding='utf-8')
        errors, _ = check_dossiers(dossiers, [], {}, reports=self.dir)
        self.assertEqual(len(errors), 1)
        self.assertIn('dossier-money.md написан не сборкой', errors[0])

    def test_reports_on_disk_are_build_reports(self):
        for table_path, _ in dossier_paths(ROOT / 'data/dossiers'):
            # сборка называет отчёт по id досье, а не по имени файла
            dossier_id = json.loads(table_path.read_text('utf-8'))['id']
            path = ROOT / f'data/review/dossier-{dossier_id}.md'
            self.assertTrue(path.read_text('utf-8').startswith(REPORT_MARK + '\n'), path.name)


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
