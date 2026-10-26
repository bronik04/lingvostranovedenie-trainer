import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from site_bank import embedded_by, load_settings, site_bank


def record(rid, *occurrences):
    return {'id': rid, 'occurrences': list(occurrences)}


class SiteBankTest(unittest.TestCase):
    old = {'year': '2016-17', 'stageCode': 'mun', 'number': 1}
    regional = {'year': '2025-26', 'stageCode': 'mun', 'number': 3, 'region': 'Санкт-Петербург', 'regionCode': 'spb'}
    # подпись региона без кода (Цифриум, Московская область) — основной источник, а не региональный вариант
    labelled = {'year': '2026-27', 'stageCode': 'mun', 'number': 2, 'region': 'Московская область'}

    def test_hidden_regional_records_and_occurrences(self):
        bank = [record('a', self.old), record('b', self.regional), record('c', self.old, self.regional),
                record('d', self.labelled), {'id': 'addition-b1-01', 'occurrences': []}]
        shown = site_bank(bank, {'showRegional': False})
        self.assertEqual([r['id'] for r in shown], ['a', 'c', 'd', 'addition-b1-01'])
        self.assertEqual(shown[1]['occurrences'], [self.old])
        self.assertEqual(bank[2]['occurrences'], [self.old, self.regional], 'исходный банк не меняется')

    def test_exceptions_keep_embedded_and_listed_records(self):
        bank = [record('b', self.regional), record('e', self.regional), record('f', self.regional)]
        settings = {'showRegional': False, 'showEmbeddedIn': ['sets'], 'showRegionalIds': ['f']}
        shown = site_bank(bank, settings, {'b': 'sets', 'e': 'provinces'})
        self.assertEqual([r['id'] for r in shown], ['b', 'f'])
        self.assertEqual(shown[0]['occurrences'], [self.regional], 'оставленная запись — с региональным появлением')

    def test_repository_exceptions(self):
        # решение автора 2026-10-26: встроенные темами «Четыре великих», «Государство», «Современный Китай» и два
        # вопроса «Литературы», бывшие на сайте до сверки, не скрываются
        bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
        shown = {r['id'] for r in site_bank(bank, load_settings(), embedded_by())}
        for rid in ['2024-25-mun-mosobl-5', '2018-19-mun-spb-9', '2023-24-mun-komi-2', '2024-25-mun-udm-8',
                    '2025-26-mun-chel-2']:
            self.assertIn(rid, shown)
        for rid in ['2025-26-mun-nnov-1', '2021-22-mun-tat-57', '2019-20-mun-lip-4']:
            self.assertNotIn(rid, shown)

    def test_switch_on_shows_everything(self):
        bank = [record('b', self.regional)]
        self.assertIs(site_bank(bank, {'showRegional': True}), bank)
        self.assertIs(site_bank(bank, {}), bank)

    def test_repository_settings(self):
        settings = load_settings()
        self.assertIsInstance(settings.get('showRegional'), bool)
        self.assertTrue(settings.get('reason'))


if __name__ == '__main__':
    unittest.main()
