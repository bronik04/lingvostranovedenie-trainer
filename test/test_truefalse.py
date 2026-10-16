import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from truefalse import apply_truefalse, load_truefalse, validate_truefalse


def record(**overrides):
    item = {
        'id': '2018-19-reg-2',
        'questionRu': 'Какова средняя высота Цинхай-Тибетского нагорья, называемого «крышей мира»?',
        'options': [{'id': 'o1', 'zh': '3000 米以上'}, {'id': 'o2', 'zh': '4500 米以上'},
                    {'id': 'o3', 'zh': '1500 米以上'}, {'id': 'o4', 'zh': '6000 米以上'}],
        'answer': {'optionId': 'o2', 'state': 'verified'},
    }
    item.update(overrides)
    return item


def entry(exclude=None, reason='«выше 3000 м» верно как утверждение: средняя высота 4000–5000 м'):
    return {'exclude': {'o1': '3000 米以上'} if exclude is None else exclude, 'reason': reason}


class TrueFalseTest(unittest.TestCase):
    def test_marks_excluded_options(self):
        [result] = apply_truefalse([record()], {'2018-19-reg-2': entry({'o1': '3000 米以上', 'o3': '1500 米以上'})})
        self.assertEqual(result['options'][0], {'id': 'o1', 'zh': '3000 米以上', 'trueFalse': False})
        self.assertEqual(result['options'][2], {'id': 'o3', 'zh': '1500 米以上', 'trueFalse': False})
        self.assertNotIn('trueFalse', result['options'][1])
        self.assertNotIn('trueFalse', result['options'][3])

    def test_keeps_untouched_records(self):
        other = record(id='other')
        result = apply_truefalse([record(), other], {'2018-19-reg-2': entry()})
        self.assertIs(result[1], other)

    def test_accepts_a_valid_entry(self):
        self.assertEqual(validate_truefalse({'2018-19-reg-2': entry()}, [record()]), [])

    def assertRejected(self, layer, message, bank=None):
        errors = validate_truefalse(layer, bank or [record()])
        self.assertTrue(any(message in error for error in errors), f'{message!r} не найдено в {errors}')

    def test_rejects_each_broken_rule(self):
        cases = [
            ({'missing': entry()}, 'такой записи в банке нет'),
            ({'2018-19-reg-2': entry({'o9': '3000 米以上'})}, 'такого варианта нет'),
            ({'2018-19-reg-2': entry({'o2': '4500 米以上'})}, 'правильный ответ'),
            ({'2018-19-reg-2': entry({'o1': '3000米以上'})}, 'вариант изменился'),
            ({'2018-19-reg-2': entry({})}, 'не исключено ни одного варианта'),
            ({'2018-19-reg-2': entry({'o1': '3000 米以上', 'o3': '1500 米以上', 'o4': '6000 米以上'})},
             'не осталось ни одного неверного варианта'),
            ({'2018-19-reg-2': entry(reason='  ')}, 'нет причины'),
            ({'2018-19-reg-2': {**entry(), 'note': 'x'}}, 'неизвестные поля'),
            ({'2018-19-reg-2': 'o1'}, 'должна быть объектом'),
        ]
        for layer, message in cases:
            with self.subTest(message=message):
                self.assertRejected(layer, message)

    def test_rejects_a_layer_that_is_not_a_dict(self):
        self.assertRejected([], 'словарём')

    def test_apply_stops_on_errors(self):
        with self.assertRaises(ValueError):
            apply_truefalse([record()], {'2018-19-reg-2': entry({'o2': '4500 米以上'})})

    def test_load_missing_file_is_empty(self):
        self.assertEqual(load_truefalse(ROOT / 'нет такого файла.json'), {})

    def test_load_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'truefalse.json'
            path.write_text('{"a": {}, "a": {}}', 'utf-8')
            with self.assertRaises(ValueError):
                load_truefalse(path)

    def test_real_layer_matches_the_bank(self):
        bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
        layer = load_truefalse(ROOT / 'data/review/truefalse.json')
        self.assertIn('2018-19-reg-2', layer)
        self.assertEqual(validate_truefalse(layer, bank), [])
        [entry_record] = [r for r in bank if r['id'] == '2018-19-reg-2']
        self.assertEqual({o['id'] for o in entry_record['options'] if o.get('trueFalse') is False}, {'o1', 'o3'})


if __name__ == '__main__':
    unittest.main()
