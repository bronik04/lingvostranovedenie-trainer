import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from book_lesson import Gloss, Lesson, load_lessons  # noqa: E402

# Как test/ui.test.mjs: без jieba локально тесты пропускаются, в CI — обязательны.
HAVE_JIEBA = importlib.util.find_spec('jieba') is not None
needs_jieba = unittest.skipUnless(HAVE_JIEBA or os.environ.get('CI'),
                                  'нет jieba — запускайте .venv/bin/python3 -m unittest')
if HAVE_JIEBA or os.environ.get('CI'):
    import book_level  # noqa: E402
    from book_level import Run, Vocab  # noqa: E402


def lesson(body, gloss=()):
    return Lesson('t', 'myths', '题', 'img/t.png', 'draft', body, gloss=list(gloss))


def vocab(**words):
    """vocab(温暖=(5, 'wēnnuǎn'), 很=1) — уровень и, при желании, пиньинь."""
    level, pinyin = {}, {}
    for w, v in words.items():
        lv, py = v if isinstance(v, tuple) else (v, '')
        level[w], pinyin[w] = lv, py
    return Vocab(level, pinyin)


def pinyin_runs(a):
    return [r for b in a.blocks for r in (b.runs or []) if r.pinyin]


@needs_jieba
class AnnotateTest(unittest.TestCase):
    def test_hsk5_word_gets_pinyin_once(self):
        a = book_level.annotate(lesson('温暖，温暖。'), vocab(温暖=(5, 'wēnnuǎn')))
        self.assertEqual(pinyin_runs(a), [Run('温暖', 'wēnnuǎn')])
        self.assertEqual(''.join(r.text for r in a.blocks[0].runs), '温暖，温暖。')
        self.assertIn('温暖', a.hsk5)
        self.assertEqual(a.errors, [])

    def test_unknown_word_is_error(self):
        a = book_level.annotate(lesson('他心术不正。'), vocab(他=1, 不=1, 正=2))
        self.assertEqual(len(a.errors), 1, a.errors)
        self.assertIn('心术不正', a.errors[0])

    def test_inline_mark_after_plain_is_error(self):
        a = book_level.annotate(lesson('逢蒙来了。{逢蒙|Féng Méng}走了。'), vocab(来=1, 了=1, 走=1))
        self.assertEqual(len(a.errors), 1, a.errors)
        self.assertIn('первое появление', a.errors[0])

    def test_polyphone_needs_mark(self):
        v = vocab(很=1, 重=(5, 'zhòng'))
        a = book_level.annotate(lesson('很重。'), v)
        self.assertEqual(len(a.errors), 1, a.errors)
        self.assertIn('многозначный', a.errors[0])
        self.assertEqual(book_level.annotate(lesson('很{重|zhòng}。'), v).errors, [])

    def test_decomposable_compound_is_known(self):
        a = book_level.annotate(lesson('打不过。'), vocab(打=1, 不=1, 过=1))
        self.assertEqual(a.errors, [])
        self.assertEqual(pinyin_runs(a), [])

    def test_char_from_shown_word_is_known(self):
        a = book_level.annotate(lesson('{射箭|shè jiàn}，射下了。'), vocab(下=1, 了=1))
        self.assertEqual(a.errors, [])

    def test_gloss_word_gets_gloss_pinyin(self):
        a = book_level.annotate(lesson('后羿很高。后羿很高。', [Gloss('后羿', 'Hòu Yì', 'Хоу И')]), vocab(很=1, 高=1))
        self.assertEqual(a.errors, [])
        self.assertEqual(pinyin_runs(a), [Run('后羿', 'Hòu Yì')])

    def test_inline_mark_gets_pinyin_once(self):
        a = book_level.annotate(lesson('{逢蒙|Féng Méng}来了，{逢蒙|Féng Méng}走了。'), vocab(来=1, 了=1, 走=1))
        self.assertEqual(a.errors, [])
        self.assertEqual(pinyin_runs(a), [Run('逢蒙', 'Féng Méng')])

    def test_quote_is_not_checked(self):
        a = book_level.annotate(lesson('> 原文：宋人有耕者'), vocab())
        self.assertEqual(a.blocks[0].kind, 'quote')
        self.assertEqual(a.blocks[0].text, '原文：宋人有耕者')
        self.assertEqual(a.errors, [])

    def test_body_structure(self):
        body = '### 小标题\n\n段落。\n\n**例句**\n\n1. 例一。\n2. 例二。'
        a = book_level.annotate(lesson(body), vocab())
        self.assertEqual([b.kind for b in a.blocks], ['h3', 'p', 'label', 'examples'])
        self.assertEqual(len(a.blocks[3].items), 2)
        self.assertEqual(''.join(r.text for r in a.blocks[3].items[1]), '例二。')

    def test_lessons_do_not_leak_words(self):
        v = vocab(来=1, 了=1)
        book_level.annotate(lesson('{逢蒙|Féng Méng}来了。'), v)
        self.assertTrue(book_level.annotate(lesson('逢蒙来了。'), v).errors)


class LoadVocabTest(unittest.TestCase):
    @needs_jieba
    def test_reads_hsk_and_extra(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'hsk20.tsv').write_text('爱\tài\t1\n温暖\twēnnuǎn\t5\n', encoding='utf-8')
            Path(tmp, 'extra.tsv').write_text('# слово\tпиньинь\tуровень\tпричина\n们\tmen\t1\tиз 我们\n', encoding='utf-8')
            v = book_level.load_vocab(Path(tmp))
            self.assertEqual((v.level['爱'], v.level['温暖'], v.level['们']), (1, 5, 1))
            self.assertEqual(v.pinyin['温暖'], 'wēnnuǎn')


SRC = ROOT / 'book' / 'src'


@needs_jieba
class LessonsPassTest(unittest.TestCase):
    def test_lessons_pass(self):
        v = book_level.load_vocab()
        lessons = load_lessons(SRC)
        self.assertTrue(lessons, 'в book/src нет уроков')
        for item in lessons:
            with self.subTest(lesson=item.id):
                self.assertEqual(book_level.annotate(item, v).errors, [])


if __name__ == '__main__':
    unittest.main()
