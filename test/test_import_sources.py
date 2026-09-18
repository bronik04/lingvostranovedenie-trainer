import json, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ImportSourcesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, 'scripts/import_sources.py'], cwd=ROOT, check=True)
        cls.index = json.loads((ROOT / 'data/raw/index.json').read_text('utf-8'))

    def test_every_source_produced_a_file(self):
        manifest = json.loads((ROOT / 'sources/manifest.json').read_text('utf-8'))
        self.assertEqual(len(self.index), len(manifest))
        for entry in self.index:
            self.assertTrue((ROOT / 'data/raw' / f"{entry['slug']}.json").exists(), entry['slug'])

    def test_bank423_contributed_all_records(self):
        bank = next(e for e in self.index if e['slug'] == 'bank423')
        self.assertEqual(bank['records'], 423)

    def test_records_follow_the_raw_contract(self):
        records = json.loads((ROOT / 'data/raw/bank423.json').read_text('utf-8'))
        required = {'sourceFile', 'year', 'stage', 'stageCode', 'grades', 'number',
                    'questionRu', 'questionZh', 'options', 'officialKeyIndex', 'topic', 'parseWarnings'}
        for record in records:
            self.assertEqual(set(record), required)

    def test_import_is_deterministic(self):
        before = (ROOT / 'data/raw/bank423.json').read_bytes()
        subprocess.run([sys.executable, 'scripts/import_sources.py'], cwd=ROOT, check=True)
        self.assertEqual(before, (ROOT / 'data/raw/bank423.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
