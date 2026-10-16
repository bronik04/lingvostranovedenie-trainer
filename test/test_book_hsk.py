import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import book_hsk  # noqa: E402


def write_deck(folder, name, lines):
    (Path(folder) / name).write_text('﻿' + '\n'.join(lines) + '\n', encoding='utf-8')


class ImportAnkiTest(unittest.TestCase):
    def test_import_takes_lowest_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_deck(tmp, 'HSK1.txt', ['爱\tài\tлюбить\t\tHSK1'])
            write_deck(tmp, 'HSK4F.txt', ['爱\tài\tлюбить\t\tHSK4', '阿姨\tàyí\tтётя\t\tHSK4'])
            self.assertEqual(book_hsk.import_anki(Path(tmp)), [('爱', 'ài', 1), ('阿姨', 'àyí', 4)])

    def test_variants_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_deck(tmp, 'HSK2.txt', ['是|是不是\tshì\tбыть\t\tHSK2'])
            words = [w for w, _, _ in book_hsk.import_anki(Path(tmp))]
            self.assertEqual(sorted(words), ['是', '是不是'])

    def test_write_tsv_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'hsk20.tsv'
            book_hsk.write_tsv([('爱', 'ài', 1)], path)
            self.assertEqual(path.read_text(encoding='utf-8'), '爱\tài\t1\n')


if __name__ == '__main__':
    unittest.main()
