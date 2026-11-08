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
                    '2025-26-mun-chel-2', '2021-22-mun-tat-57']:
            self.assertIn(rid, shown)
        # 2026-11-08: автор разрешил все принятые встраивания, включая прежде скрытое о мяо.
        self.assertIn('2019-20-mun-lip-4', shown)
        self.assertIn('2019-20-mun-lip-4', load_settings()['showRegionalIds'])
        for rid in ['2025-26-mun-nnov-1', '2020-21-shk-mosobl-52']:
            self.assertNotIn(rid, shown)
        for rid in load_settings().get('hiddenQuestions', {}):
            self.assertNotIn(rid, shown, 'окончательные снятия сильнее разрешения встраиваний')

    def test_draft_embed_does_not_open_a_record(self):
        import tempfile, json as j
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / 'sets-questions.json').write_text(j.dumps([
                {'id': 'sets-q90', 'embeds': 'b', 'status': 'draft'},
                {'id': 'sets-q91', 'embeds': 'e', 'status': 'accepted'}]), 'utf-8')
            self.assertEqual(embedded_by(Path(folder)), {'e': 'sets'})

    def test_switch_on_shows_everything(self):
        bank = [record('b', self.regional)]
        self.assertIs(site_bank(bank, {'showRegional': True}), bank)
        self.assertIs(site_bank(bank, {}), bank)

    def test_repository_settings(self):
        settings = load_settings()
        self.assertIsInstance(settings.get('showRegional'), bool)
        self.assertTrue(settings.get('reason'))

    def test_editorial_hiding_wins_over_regional_switch_and_exceptions(self):
        bank = [record('a', self.old), record('b', self.regional), record('c', self.old)]
        for show_regional in [True, False]:
            with self.subTest(showRegional=show_regional):
                settings = {'showRegional': show_regional, 'showRegionalIds': ['b'],
                            'showEmbeddedIn': ['sets'], 'hiddenQuestions': {
                                'a': {'reason': 'решение автора', 'date': '2026-11-03'},
                                'b': {'reason': 'решение автора', 'date': '2026-11-03'}}}
                self.assertEqual([r['id'] for r in site_bank(bank, settings, {'b': 'sets'})], ['c'])
                self.assertEqual([r['id'] for r in bank], ['a', 'b', 'c'])

    def test_unknown_hidden_id_is_not_silently_ignored(self):
        with self.assertRaisesRegex(ValueError, 'missing'):
            site_bank([record('a', self.old)], {'hiddenQuestions': {
                'missing': {'reason': 'решение автора', 'date': '2026-11-03'}}})

    def test_hiding_requires_a_reason_and_date(self):
        for entry in [{}, {'reason': 'решение автора'}, {'date': '2026-11-03'}]:
            with self.subTest(entry=entry), self.assertRaisesRegex(ValueError, 'a'):
                site_bank([record('a', self.old)], {'hiddenQuestions': {'a': entry}})


if __name__ == '__main__':
    unittest.main()
