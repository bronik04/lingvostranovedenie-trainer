import shutil
import sys
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from book_lesson import Gloss, Item, Lesson, load_blocks  # noqa: E402
from test.test_book_level import HAVE_JIEBA, needs_jieba  # noqa: E402

if HAVE_JIEBA:
    import book  # noqa: E402
    import book_render  # noqa: E402
    from book_level import Annotated, Block, Run  # noqa: E402

BLOCKS = load_blocks()
MYTHS = BLOCKS[0]
GOOD = ROOT / 'book' / 'src' / 'myths' / '09-myth-change-benyue.md'
NS = {'opf': 'http://www.idpf.org/2007/opf'}


def annotated(lesson_id='myth-x', title='《盘古》“开天”……', runs=None, status='draft'):
    lesson = Lesson(lesson_id, 'myths', title, f'img/{lesson_id}.png', status, '',
                    gloss=[Gloss('盘古', 'Pángǔ', 'Паньгу & <бог>')],
                    tf=[Item('盘古是神。', '对')], qa=[Item('盘古是谁？', '神。')], note='Примечание & <ссылка>')
    runs = runs or [Run('天 & 地 <分开>。')]
    return Annotated(lesson, [Block('p', runs=runs)])


@needs_jieba
class LessonXhtmlTest(unittest.TestCase):
    def test_lesson_xhtml_is_wellformed(self):
        xhtml = book_render.lesson_xhtml(annotated(), MYTHS, ROOT / 'book', draft_mark=True)
        root = ET.fromstring(xhtml)
        text = ''.join(root.itertext())
        for piece in ('《盘古》“开天”……', '天 & 地 <分开>。', 'Паньгу & <бог>', 'Примечание & <ссылка>', 'черновик'):
            self.assertIn(piece, text)

    def test_ruby_rendered(self):
        xhtml = book_render.lesson_xhtml(annotated(runs=[Run('温暖', 'wēnnuǎn'), Run('。')]), MYTHS, ROOT / 'book', False)
        self.assertIn('<ruby>温暖<rt>wēnnuǎn</rt></ruby>', xhtml)
        self.assertNotIn('черновик', xhtml)

    def test_true_false_items_are_numbered_like_key(self):
        xhtml = book_render.lesson_xhtml(annotated(), MYTHS, ROOT / 'book', False)
        self.assertIn('1) ☐ 盘古是神。', xhtml)

    def test_missing_image_gives_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            xhtml = book_render.lesson_xhtml(annotated(), MYTHS, root, False)
            self.assertIn('img-placeholder', xhtml)
            self.assertIn('img/myth-x.png', xhtml)
            (root / 'img').mkdir()
            (root / 'img' / 'myth-x.png').write_bytes(b'\x89PNG')
            xhtml = book_render.lesson_xhtml(annotated(), MYTHS, root, False, img_base='../')
            self.assertIn('<img src="../img/myth-x.png"', xhtml)
            self.assertNotIn('img-placeholder', xhtml)

    def test_key_lists_answers(self):
        key = book_render.key_xhtml([annotated()])
        ET.fromstring(key)
        self.assertIn('1) 对', key)
        self.assertIn('神。', key)


@needs_jieba
class EpubTest(unittest.TestCase):
    def test_epub_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'book.epub'
            book_render.write_epub([annotated('myth-a'), annotated('myth-b')], BLOCKS, out, ROOT / 'book', drafts=True)
            with zipfile.ZipFile(out) as z:
                first = z.infolist()[0]
                self.assertEqual(first.filename, 'mimetype')
                self.assertEqual(first.compress_type, zipfile.ZIP_STORED)
                self.assertEqual(z.read('mimetype'), b'application/epub+zip')
                opf = ET.fromstring(z.read('OEBPS/content.opf'))
                spine = [i.get('idref') for i in opf.find('opf:spine', NS)]
                self.assertIn('lesson-myth-a', spine)
                self.assertIn('lesson-myth-b', spine)
                for name in z.namelist():
                    if name.endswith(('.xhtml', '.opf', '.xml')):
                        with self.subTest(name=name):
                            ET.fromstring(z.read(name))


@needs_jieba
class BuildTest(unittest.TestCase):
    def test_build_skips_drafts(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out = Path(tmp) / 'src', Path(tmp) / 'out'
            (src / 'myths').mkdir(parents=True)
            shutil.copy(GOOD, src / 'myths' / GOOD.name)
            self.assertEqual(book.build(src, out, drafts=False, pdf=False), [])
            self.assertEqual(book.build(src, out, drafts=True, pdf=False), ['myth-change-benyue'])
            with zipfile.ZipFile(out / f'{book.TITLE}.epub') as z:
                self.assertIn('черновик', z.read('OEBPS/lesson-myth-change-benyue.xhtml').decode())

    @unittest.skipUnless(HAVE_JIEBA and book_render.chrome_path() if HAVE_JIEBA else False, 'нет Google Chrome')
    def test_pdf_smoke(self):
        with tempfile.TemporaryDirectory() as tmp:
            html = Path(tmp) / 'a.html'
            html.write_text('<!doctype html><html><body><p>盘古</p></body></html>', encoding='utf-8')
            pdf = Path(tmp) / 'a.pdf'
            book_render.write_pdf(html, pdf)
            self.assertTrue(pdf.read_bytes().startswith(b'%PDF'))


if __name__ == '__main__':
    unittest.main()
