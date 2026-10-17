import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from test.test_book_level import HAVE_JIEBA, needs_jieba  # noqa: E402

if HAVE_JIEBA:
    import book  # noqa: E402

GOOD = ROOT / 'book' / 'src' / 'myths' / '09-myth-change-benyue.md'
HSK = ROOT / 'book' / 'hsk'


@needs_jieba
class CheckTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.src = Path(tmp.name)
        (self.src / 'myths').mkdir()
        shutil.copy(GOOD, self.src / 'myths' / GOOD.name)

    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = book.main(['check', '--src', str(self.src), *argv])
        return code, out.getvalue()

    def test_good_lesson_passes(self):
        lines, errors = book.check(self.src, HSK)
        self.assertEqual(errors, 0, lines)
        self.assertTrue(lines[0].startswith('myths/09-myth-change-benyue · '), lines[0])
        self.assertEqual(self.run_main()[0], 0)

    def test_check_reports_errors_and_exit_code(self):
        text = GOOD.read_text(encoding='utf-8')
        tf = text.index('## 判断正误')
        broken = text[tf:].replace(' | 对\n', ' | 是\n', 1)
        text = text[:tf] + broken
        (self.src / 'myths' / GOOD.name).write_text(text, encoding='utf-8')
        lines, errors = book.check(self.src, HSK)
        self.assertEqual(errors, 1, lines)
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn('对/错', out)

    def test_duplicate_id(self):
        shutil.copy(GOOD, self.src / 'myths' / '10-myth-change-benyue.md')
        lines, errors = book.check(self.src, HSK)
        self.assertTrue(any('повтор id' in l for l in lines), lines)
        self.assertGreaterEqual(errors, 1)


if __name__ == '__main__':
    unittest.main()
