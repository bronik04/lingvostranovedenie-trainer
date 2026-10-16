import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import book_lesson  # noqa: E402

BLOCKS = book_lesson.load_blocks()
WORDS = ['盘古', '天地', '宇宙', '鸡蛋', '斧子', '清气', '浊气', '上升',
         '下降', '头发', '眼睛', '太阳', '月亮', '星星', '江河']
FILLER = '天很高，地很大。' * 115  # 690 иероглифов + слова «生词» — около 720


def lesson_text(status='draft', block='myths', body=None, gloss=None, tf=None, qa=None, sources=None):
    body = body if body is not None else '{盘古|Pángǔ}' + ''.join(WORDS[1:]) + '。\n\n' + FILLER
    gloss = gloss if gloss is not None else [f'- {w} | pīnyīn | перевод' for w in WORDS]
    tf = tf if tf is not None else ['- 盘古是神。 | 对', '- 盘古睡了一年。 | 错', '- 天在上面。 | 对', '- 地在上面。 | 错']
    qa = qa if qa is not None else ['- 盘古是谁？ | 神。', '- 天是怎么来的？ | 清气上升。', '- 地是怎么来的？ | 浊气下降。']
    sources = sources if sources is not None else [
        '- official | 盘古神话 — 中国非物质文化遗产网 | https://www.ihchina.cn/x | 内容涉及开天辟地 | 2026-10-15']
    return '\n'.join([
        '---', 'id: myth-test', f'block: {block}', 'title: 测试', 'image: img/myth-test.png', f'status: {status}', '---', '',
        body, '', '## 生词', '', *gloss, '', '## 判断正误', '', *tf, '', '## 回答问题', '', *qa, '',
        '## 来源', '', *sources, '', '## 注', '', 'Примечание.', ''])


class LessonCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, text, name='01-myth-test.md'):
        path = Path(self.tmp.name) / name
        path.write_text(text, encoding='utf-8')
        return path

    def errors(self, text, name='01-myth-test.md'):
        return book_lesson.validate_lesson(book_lesson.parse_lesson(self.write(text, name)), BLOCKS)


class ParseTest(LessonCase):
    def test_parses_sample(self):
        lesson = book_lesson.parse_lesson(self.write(lesson_text()))
        self.assertEqual(lesson.id, 'myth-test')
        self.assertEqual(lesson.block, 'myths')
        self.assertEqual(len(lesson.tf), 4)
        self.assertEqual(lesson.tf[1].answer, '错')
        self.assertEqual(lesson.sources[0].kind, 'official')
        self.assertEqual(lesson.gloss[0], book_lesson.Gloss('盘古', 'pīnyīn', 'перевод'))
        self.assertEqual(lesson.note, 'Примечание.')

    def test_missing_front_matter_raises(self):
        with self.assertRaises(book_lesson.LessonError):
            book_lesson.parse_lesson(self.write('просто текст'))

    def test_source_line_needs_five_fields(self):
        with self.assertRaises(book_lesson.LessonError):
            book_lesson.parse_lesson(self.write(lesson_text(sources=['- official | только название'])))


class ValidateTest(LessonCase):
    def test_good_lesson_has_no_errors(self):
        self.assertEqual(self.errors(lesson_text()), [])

    def assertOneError(self, text, needle, name='01-myth-test.md'):
        errors = self.errors(text, name)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(needle, errors[0])

    def test_errors(self):
        good_tf = ['- 盘古是神。 | 对', '- 盘古睡了一年。 | 错', '- 天在上面。 | 对', '- 地在上面。 | 错']
        cases = [
            (lesson_text(block='gods'), 'блок'),
            (lesson_text(status='done'), 'status'),
            (lesson_text(tf=good_tf[:3] + ['- 地在上面。 | 是']), '对/错'),
            (lesson_text(tf=good_tf + good_tf[:2]), '判断正误'),
            (lesson_text(qa=['- 盘古是谁？ | 神。', '- 天呢？ | 上面。']), '回答问题'),
            (lesson_text(gloss=[f'- {w} | p | п' for w in WORDS[:9]]), '生词'),
            (lesson_text(body=''.join(WORDS) + '。' + '天很高。' * 40), 'длина'),
            (lesson_text(status='accepted', sources=['- retelling | 百度百科 | https://baike.baidu.com/x | 引文 | 2026-10-15']), 'источник'),
            (lesson_text(sources=['- official | 名 | https://a.cn/x | 引文 | 16.10.2026']), 'дата'),
            (lesson_text(sources=['- blog | 名 | https://a.cn/x | 引文 | 2026-10-16']), 'kind'),
            (lesson_text(sources=['- official | 名 | a.cn/x | 引文 | 2026-10-16']), 'ссылка'),
            (lesson_text(gloss=[f'- {w} | p | п' for w in WORDS] + ['- 斧头 | fǔtóu | топор']), 'нет в тексте'),
        ]
        for text, needle in cases:
            with self.subTest(needle=needle):
                self.assertOneError(text, needle)

    def test_file_name_must_match_id(self):
        self.assertOneError(lesson_text(), 'id', name='01-other.md')

    def test_gloss_word_inside_longer_word_is_used(self):
        body = '{蟠桃园|pántáoyuán}' + ''.join(WORDS) + '。\n\n' + FILLER
        gloss = [f'- {w} | p | п' for w in WORDS[1:]] + ['- 蟠桃 | pántáo | персик бессмертия']
        self.assertEqual(self.errors(lesson_text(body=body, gloss=gloss)), [])

    def test_gloss_pattern_with_ellipsis_skipped(self):
        gloss = [f'- {w} | p | п' for w in WORDS] + ['- 拜……为师 | bài…wéi shī | стать учеником']
        self.assertEqual(self.errors(lesson_text(gloss=gloss)), [])


class TextTest(LessonCase):
    def test_count_han_excludes_quote_and_marks(self):
        body = '{盘古|Pángǔ}在1万8千年里。\n\n> 原文：天地混沌如鸡子\n\n**例句**\n\n1. 他很高。'
        lesson = book_lesson.parse_lesson(self.write(lesson_text(body=body)))
        self.assertEqual(book_lesson.body_text(lesson).count('原文'), 0)
        self.assertEqual(book_lesson.count_han(book_lesson.body_text(lesson)), len('盘古在万千年里') + len('他很高'))


class LoadTest(unittest.TestCase):
    def test_unknown_folder_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            (src / 'folktales').mkdir()
            (src / 'folktales' / '01-myth-test.md').write_text(lesson_text(), encoding='utf-8')
            with self.assertRaises(book_lesson.LessonError):
                book_lesson.load_lessons(src)

    def test_block_must_match_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            (src / 'chengyu').mkdir()
            (src / 'chengyu' / '01-myth-test.md').write_text(lesson_text(block='myths'), encoding='utf-8')
            with self.assertRaises(book_lesson.LessonError):
                book_lesson.load_lessons(src)

    def test_load_lessons_in_block_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            for block, name in [('chengyu', '01-myth-test.md'), ('myths', '02-myth-test.md')]:
                (src / block).mkdir()
                (src / block / name).write_text(lesson_text(block=block), encoding='utf-8')
            self.assertEqual([l.block for l in book_lesson.load_lessons(src)], ['myths', 'chengyu'])


if __name__ == '__main__':
    unittest.main()
