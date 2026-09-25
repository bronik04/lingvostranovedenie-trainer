import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from glosses import apply_glosses, validate_glosses


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

    def test_keeps_untouched_records(self):
        other = record(id='other')
        result = apply_glosses([record(), other], {'2015-16-zak-4': entry({'o2': gloss()})})
        self.assertIs(result[1], other)

    def test_rejects_invalid_glosses(self):
        bank = [record()]
        bad = [
            {'missing': entry({'o2': gloss()})},
            {'2015-16-zak-4': entry({'o9': gloss()})},
            {'2015-16-zak-4': entry({'o1': gloss(zh='秦朝', ru='Династия Цинь')})},
            {'2015-16-zak-4': entry({'o2': gloss(zh='汉代')})},
            {'2015-16-zak-4': entry({'o2': gloss(ru='Han dynasty')})},
            {'2015-16-zak-4': entry({'o2': gloss(ru='Династия ' + 'Хань ' * 20)})},
            {'2015-16-zak-4': entry({'o2': gloss(ru='Династия Хань — — 206')})},
            {'2015-16-zak-4': entry({'o2': gloss(ru='Династия  Хань')})},
            {'2015-16-zak-4': entry({'o2': gloss(source={'title': 'x', 'url': 'javascript:alert(1)'})})},
            {'2015-16-zak-4': entry({'o2': gloss(source={'title': ' ', 'url': 'https://example.org'})})},
            {'2015-16-zak-4': {'options': {'o2': gloss()}}},
            {'2015-16-zak-4': entry({})},
            [],
        ]
        for glosses in bad:
            self.assertTrue(validate_glosses(glosses, bank), glosses)
        self.assertEqual(validate_glosses({'2015-16-zak-4': entry({'o2': gloss()})}, bank), [])

    def test_changed_option_text_stops_the_build(self):
        with self.assertRaises(ValueError):
            apply_glosses([record()], {'2015-16-zak-4': entry({'o2': gloss(zh='汉代')})})


class GlossesInBankTest(unittest.TestCase):
    """Каждая подпись из data/review/glosses.json должна дойти до data/bank.json."""

    def test_every_gloss_reaches_the_bank(self):
        glosses = json.loads((ROOT / 'data/review/glosses.json').read_text('utf-8'))
        bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        for record_id, item in glosses.items():
            options = {o['id']: o for o in bank[record_id]['options']}
            for option_id, value in item['options'].items():
                self.assertEqual(options[option_id].get('gloss'), value['ru'], f'{record_id}/{option_id}')


if __name__ == '__main__':
    unittest.main()
