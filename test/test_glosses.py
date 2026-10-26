import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from glosses import apply_glosses, load_glosses, validate_glosses


def record(**overrides):
    item = {
        'id': '2015-16-zak-4',
        'questionRu': 'Как называлась первая единая централизованная феодальная династия в истории Китая?',
        'options': [{'id': 'o1', 'zh': '秦朝'}, {'id': 'o2', 'zh': '汉朝'},
                    {'id': 'o3', 'zh': '明朝'}, {'id': 'o4', 'zh': '夏朝'}],
        'answer': {'optionId': 'o1', 'state': 'verified'},
    }
    item.update(overrides)
    return item


def gloss(zh='汉朝', ru='Династия Хань, 206 г. до н. э. — 220 г.', **overrides):
    item = {'zh': zh, 'ru': ru, 'source': {'title': '汉朝 — 百科', 'url': 'https://example.org/han'}}
    item.update(overrides)
    return item


def entry(options):
    return {'reviewedAt': '2026-09-25', 'options': options}


class GlossesTest(unittest.TestCase):
    def test_puts_gloss_into_the_option(self):
        [result] = apply_glosses([record()], {'2015-16-zak-4': entry({'o2': gloss()})})
        self.assertEqual(result['options'][1], {'id': 'o2', 'zh': '汉朝',
                                                'gloss': 'Династия Хань, 206 г. до н. э. — 220 г.'})
        self.assertNotIn('gloss', result['options'][0])

    def test_puts_answer_name_into_the_answer(self):
        # решение автора 2026-10-26: у вопросов вне досье название верного ответа — подпись
        # к варианту-ответу в glosses.json; сборка кладёт её в answer.gloss, как ячейку досье
        name = gloss(zh='秦朝', ru='Династия Цинь — первая единая империя, 221–207 гг. до н. э.')
        [result] = apply_glosses([record()], {'2015-16-zak-4': entry({'o1': name, 'o2': gloss()})})
        self.assertEqual(result['answer'], {'optionId': 'o1', 'state': 'verified',
                                            'gloss': 'Династия Цинь — первая единая империя, 221–207 гг. до н. э.'})
        self.assertEqual(result['options'][0], {'id': 'o1', 'zh': '秦朝'})
        self.assertEqual(result['options'][1]['gloss'], 'Династия Хань, 206 г. до н. э. — 220 г.')

    def test_answer_name_alone_is_enough(self):
        name = gloss(zh='秦朝', ru='Династия Цинь — первая единая империя')
        [result] = apply_glosses([record()], {'2015-16-zak-4': entry({'o1': name})})
        self.assertEqual(result['answer']['gloss'], 'Династия Цинь — первая единая империя')
        self.assertTrue(all('gloss' not in option for option in result['options']))

    def test_dossier_record_takes_answer_name_from_its_cell(self):
        dossier = record(dossier='history', answer={'optionId': 'o1', 'state': 'verified', 'gloss': 'Династия Цинь'})
        name = gloss(zh='秦朝', ru='Династия Цинь — первая единая империя')
        self.assertRejected({'2015-16-zak-4': entry({'o1': name})}, 'берётся из ячейки досье', [dossier])

    def test_changed_answer_text_stops_the_build(self):
        name = gloss(zh='秦', ru='Династия Цинь — первая единая империя')
        with self.assertRaisesRegex(ValueError, 'вариант изменился'):
            apply_glosses([record()], {'2015-16-zak-4': entry({'o1': name})})

    def test_keeps_untouched_records(self):
        other = record(id='other')
        result = apply_glosses([record(), other], {'2015-16-zak-4': entry({'o2': gloss()})})
        self.assertIs(result[1], other)

    def assertRejected(self, glosses, message, bank=None):
        errors = validate_glosses(glosses, bank or [record()])
        self.assertTrue(any(message in error for error in errors), f'{message!r} не найдено в {errors}')

    def test_accepts_a_valid_gloss(self):
        self.assertEqual(validate_glosses({'2015-16-zak-4': entry({'o2': gloss()})}, [record()]), [])

    def test_rejects_each_broken_rule(self):
        cases = [
            ({'missing': entry({'o2': gloss()})}, 'такой записи в банке нет'),
            ({'2015-16-zak-4': entry({'o9': gloss()})}, 'такого варианта нет'),
            ({'2015-16-zak-4': entry({'o1': gloss(zh='秦朝', ru='Династия Цинь')})}, 'название верного ответа — «Название — факт»'),
            ({'2015-16-zak-4': entry({'o1': gloss(zh='秦朝', ru=' — первая единая империя')})}, 'название верного ответа — «Название — факт»'),
            ({'2015-16-zak-4': entry({'o2': gloss(zh='汉代')})}, 'вариант изменился'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='Han dynasty')})}, 'не по-русски'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='   ')})}, 'не по-русски'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='Д' * 91)})}, 'длиннее 90'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='Династия Хань — — 206')})}, 'двойное тире'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='Династия  Хань')})}, 'лишние пробелы'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru=' Династия Хань')})}, 'лишние пробелы'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='Династия Хань\n206 г.')})}, 'не в одну строку'),
            ({'2015-16-zak-4': entry({'o2': gloss(ru='汉朝 — династия Хань')})}, 'повторяет сам вариант'),
            ({'2015-16-zak-4': entry({'o2': gloss(source={'title': 'x', 'url': 'javascript:alert(1)'})})}, 'нет источника'),
            ({'2015-16-zak-4': entry({'o2': gloss(source={'title': ' ', 'url': 'https://example.org'})})}, 'нет источника'),
            ({'2015-16-zak-4': entry({'o2': gloss(source={'title': 'x', 'url': 42})})}, 'нет источника'),
            ({'2015-16-zak-4': entry({'o2': {'zh': '汉朝', 'ru': 'Династия Хань'}})}, 'нет источника'),
            ({'2015-16-zak-4': entry({'o2': gloss(quote='цитата из черновика')})}, 'неизвестные поля'),
            ({'2015-16-zak-4': entry({'o2': 'Династия Хань'})}, 'должна быть объектом'),
            ({'2015-16-zak-4': {'options': {'o2': gloss()}}}, 'нет даты проверки'),
            ({'2015-16-zak-4': {**entry({'o2': gloss()}), 'skip': 'x'}}, 'неизвестные поля'),
            ({'2015-16-zak-4': entry({})}, 'нет ни одной подписи'),
            ({'2015-16-zak-4': 'Династия Хань'}, 'должна быть объектом'),
            ([], 'словарём'),
        ]
        for glosses, message in cases:
            with self.subTest(message=message):
                self.assertRejected(glosses, message)

    def test_year_option_may_start_its_gloss_with_the_year(self):
        years = record(options=[{'id': 'o1', 'zh': '1912'}, {'id': 'o2', 'zh': '1911'},
                                {'id': 'o3', 'zh': '1910'}, {'id': 'o4', 'zh': '1915'}])
        glosses = {'2015-16-zak-4': entry({'o2': gloss(zh='1911', ru='1911 — Учанское восстание')})}
        self.assertEqual(validate_glosses(glosses, [years]), [])

    def test_year_option_with_hieroglyphs_is_not_repeated(self):
        years = record(options=[{'id': 'o1', 'zh': '1912 年'}, {'id': 'o2', 'zh': '1911 年'},
                                {'id': 'o3', 'zh': '1910 年'}, {'id': 'o4', 'zh': '1915 年'}])
        glosses = {'2015-16-zak-4': entry({'o2': gloss(zh='1911 年', ru='1911 年 — Учанское восстание')})}
        self.assertRejected(glosses, 'повторяет сам вариант', [years])

    def test_rejects_gloss_for_question_without_verified_answer(self):
        unverified = record(answer={'optionId': None, 'state': 'needs-review'})
        self.assertRejected({'2015-16-zak-4': entry({'o2': gloss()})}, 'без проверенного ответа', [unverified])

    def test_duplicate_keys_in_file_are_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'glosses.json'
            path.write_text('{"2015-16-zak-4": {"reviewedAt": "x", "options": {"o2": {}, "o2": {}}}}', 'utf-8')
            with self.assertRaises(ValueError):
                load_glosses(path)

    def test_changed_option_text_stops_the_build(self):
        with self.assertRaises(ValueError):
            apply_glosses([record()], {'2015-16-zak-4': entry({'o2': gloss(zh='汉代')})})


class GlossesInBankTest(unittest.TestCase):
    """Каждая подпись из data/review/glosses.json должна дойти до data/bank.json."""

    def test_every_gloss_reaches_the_bank(self):
        glosses = json.loads((ROOT / 'data/review/glosses.json').read_text('utf-8'))
        bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        expected = {(record_id, option_id): value['ru']
                    for record_id, item in glosses.items() for option_id, value in item['options'].items()}
        # в обе стороны: и каждая подпись дошла, и лишних подписей в банке нет;
        # у вопросов досье подписи из ячеек таблицы (data/dossiers/), а не из glosses.json;
        # подпись к варианту-ответу — название верного ответа, оно у ответа, а не у варианта
        actual = {(record['id'], option['id']): option['gloss']
                  for record in bank.values() if 'dossier' not in record
                  for option in record['options'] if 'gloss' in option}
        actual |= {(record['id'], record['answer']['optionId']): record['answer']['gloss']
                   for record in bank.values() if 'dossier' not in record and 'gloss' in record['answer']}
        self.assertEqual(actual, expected)

    def test_wrong_options_of_pooled_questions_are_glossed(self):
        # у вопроса с общим набором пояснение не говорит о неверных вариантах — о них
        # рассказывают подписи; без подписи остаются только варианты, о которых нечего
        # сказать правдиво (выдуманный термин, промежуток лет без события)
        unglossed_on_purpose = {
            ('2017-18-reg-1', '经贸合作带'), ('2017-18-reg-1', '陆海丝绸之路'),
            ('2022-23-shk-q3c7e59', '1901-1905 年'), ('2022-23-shk-q3c7e59', '1917-1918 年'),
            ('2022-23-shk-q3c7e59', '1917-1921 年'),
            # раздел Б (2026-10-14): числа лет и год без связи с темой вопроса
            ('2016-17-shk-8', '十'), ('2016-17-shk-8', '十一'), ('2016-17-shk-8', '八'),
            ('2018-19-zak-7', '1800'),
            # годы основания Москвы (2018-19-shk-8, склейка 2026-10-25): с Москвой эти годы ничем не связаны
            ('2018-19-shk-8', '1201'), ('2018-19-shk-8', '1247'), ('2018-19-shk-8', '1148'),
            ('2018-19-shk-8', '1838'), ('2018-19-shk-8', '953'),
        }
        merges = json.loads((ROOT / 'data/review/merges.json').read_text('utf-8'))
        bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        missing = {(keep_id, option['zh'])
                   for keep_id, item in merges.items()
                   if item.get('distractors') == 'pool'
                   for option in bank[keep_id]['options']
                   if option['id'] != bank[keep_id]['answer']['optionId'] and not option.get('gloss')}
        self.assertEqual(missing, unglossed_on_purpose)

    def test_same_option_of_pooled_questions_is_glossed_alike(self):
        # где вопросу не нужна своя формулировка, у варианта одна подпись (правило пилота)
        bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
        for zh in ('天津', '李白', '深圳', '珠海', '汕头'):
            texts = {o['gloss'] for r in bank for o in r['options'] if o['zh'] == zh and o.get('gloss')}
            self.assertEqual(len(texts), 1, (zh, texts))

    def test_blue_in_the_traditional_culture_question_is_the_temple_of_heaven_tile(self):
        # решение автора 2026-10-13: в вопросе о цвете в традиционной культуре синий
        # подписан по традиционной культуре, а не как цвет партии Гоминьдан
        bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        blue = next(o['gloss'] for o in bank['2015-16-mun-5']['options'] if o['zh'] == '蓝色')
        self.assertEqual(blue, 'Синяя черепица — на кровлях Храма Неба, символ неба')

    def test_first_special_economic_zones_are_named_in_the_largest_zone_question(self):
        # решение автора 2026-10-13: в вопросе о крупнейшей СЭЗ подписи говорят, что Сямэнь,
        # Чжухай и Шаньтоу — одни из четырёх первых СЭЗ
        bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        for zh in ('深圳', '厦门', '珠海', '汕头'):
            gloss = next(o['gloss'] for o in bank['2016-17-zak-1']['options'] if o['zh'] == zh)
            # все четыре получили статус одновременно, в 1980 году: ни одна не «первая»
            self.assertIn('одна из четырёх первых особых экономических зон', gloss, zh)

    def test_special_economic_zone_questions_gloss_every_wrong_option(self):
        # решение автора 2026-10-13: в вопросах «какой город (не) является СЭЗ» подписаны все
        # неверные варианты; города-СЭЗ подписаны как СЭЗ, остальные — уже принятыми подписями
        bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        for record_id in ('2023-24-shk-32', '2025-26-shk-29'):
            record = bank[record_id]
            wrong = [o for o in record['options'] if o['id'] != record['answer']['optionId']]
            self.assertTrue(all(o.get('gloss') for o in wrong), record_id)
        for option in bank['2023-24-shk-32']['options']:
            if option['zh'] in ('深圳', '汕头', '珠海'):
                self.assertIn('особ', option['gloss'], option['zh'])


if __name__ == '__main__':
    unittest.main()
