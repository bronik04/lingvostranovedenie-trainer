import hashlib, json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = 8


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / 'sources/manifest.json').read_text('utf-8'))

    def test_manifest_lists_every_source(self):
        on_disk = {p.name for p in (ROOT / 'sources').iterdir() if p.suffix in {'.docx', '.pdf'}}
        self.assertEqual(len(on_disk), EXPECTED)
        self.assertEqual({entry['name'] for entry in self.manifest}, on_disk)

    def test_checksums_match_disk(self):
        for entry in self.manifest:
            data = (ROOT / 'sources' / entry['name']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'], entry['name'])
            self.assertEqual(len(data), entry['bytes'], entry['name'])


if __name__ == '__main__':
    unittest.main()
