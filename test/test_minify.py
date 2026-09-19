import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from minify import minify_css, minify_js


class MinifyCssTest(unittest.TestCase):
    def test_strips_block_comments(self):
        self.assertEqual(minify_css('/* заметка */ .a { color: red; }'), '.a{color:red}')

    def test_collapses_whitespace_between_rules(self):
        css = '.a {\n  color:  red;\n  gap:   4px;\n}\n\n.b { color: blue; }'
        self.assertEqual(minify_css(css), '.a{color:red;gap:4px}.b{color:blue}')

    def test_drops_trailing_semicolon_before_closing_brace(self):
        self.assertEqual(minify_css('.a { color: red; }'), '.a{color:red}')

    def test_real_stylesheet_still_contains_expected_rules_after_minifying(self):
        css = (ROOT / 'src/quiz.css').read_text('utf-8')
        minified = minify_css(css)
        self.assertNotIn('/*', minified)
        self.assertIn(':root{', minified)
        self.assertIn('.option.correct', minified)
        self.assertLess(len(minified), len(css))


class MinifyJsTest(unittest.TestCase):
    def test_strips_line_comments(self):
        self.assertEqual(minify_js('const a = 1; // заметка\nconst b = 2;'),
                          'const a = 1; \nconst b = 2;')

    def test_strips_block_comments(self):
        self.assertEqual(minify_js('/* заметка */\nconst a = 1;'), '\nconst a = 1;')

    def test_does_not_touch_a_double_slash_inside_a_string(self):
        js = "const url = 'https://example.org';"
        self.assertEqual(minify_js(js), js)

    def test_does_not_touch_a_comment_like_sequence_inside_a_template_literal(self):
        js = 'const t = `текст /* не комментарий */ и // тоже нет`;'
        self.assertEqual(minify_js(js), js)

    def test_respects_escaped_quotes_inside_strings(self):
        js = r'''const s = 'it\'s // not a comment';'''
        self.assertEqual(minify_js(js), js)

    def test_real_engine_files_still_parse_after_minifying(self):
        for path in ('src/quiz.mjs', 'src/quiz.ui.js'):
            source = (ROOT / path).read_text('utf-8')
            minified = minify_js(source)
            self.assertNotIn('//', minified.replace('https://', '').replace('http://', ''))
            self.assertLessEqual(len(minified), len(source))
        ui_source = (ROOT / 'src/quiz.ui.js').read_text('utf-8')
        self.assertLess(len(minify_js(ui_source)), len(ui_source))


if __name__ == '__main__':
    unittest.main()
