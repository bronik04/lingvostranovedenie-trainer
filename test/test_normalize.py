import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from normalize import (completeness_errors, fragment_pairs, language_errors,
                       normalize_text, option_key)

WHOLE = 'Административный центр провинции Цзянсу, одна из четырех древних столиц Китая.'


class NormalizeTest(unittest.TestCase):
    def test_normalize_strips_labels_spaces_and_tail_punctuation(self):
        self.assertEqual(normalize_text('A) 接近 20 亿'), '接近20亿')
        self.assertEqual(normalize_text('B. 上海'), '上海')
        self.assertEqual(normalize_text('中国最大的港口城市是哪一个？'), '中国最大的港口城市是哪一个')

    def test_option_key_ignores_order_and_labels(self):
        self.assertEqual(option_key(['A) 广州', 'B) 上海']), option_key(['上海', '广州']))


class LanguageTest(unittest.TestCase):
    def test_accepts_russian_question_with_chinese_options(self):
        self.assertEqual(language_errors(WHOLE, ['西安', '北京', '洛阳', '南京']), [])

    def test_accepts_numeric_and_latin_options_from_originals(self):
        self.assertEqual(language_errors(WHOLE, ['5%', '22%', 'HSK', '阿Q正传']), [])

    def test_rejects_chinese_question(self):
        self.assertTrue(language_errors('中国最大的港口城市是哪一个？', ['上海']))

    def test_rejects_cyrillic_option(self):
        self.assertTrue(language_errors(WHOLE, ['Шанхай', '北京']))


class CompletenessTest(unittest.TestCase):
    def test_accepts_whole_question(self):
        self.assertEqual(completeness_errors(WHOLE, '江苏省的行政中心是哪里？', ['西安', '南京']), [])

    def test_rejects_question_cut_at_the_head(self):
        self.assertTrue(completeness_errors('дминистративный центр провинции Цзянсу.', None, ['西安']))

    def test_rejects_question_cut_at_the_tail(self):
        self.assertTrue(completeness_errors(
            'Река Хуанхэ отделяет эту провинцию от провинции Шэньси. В этой провинции',
            None, ['山西', '河北']))

    def test_rejects_leading_space(self):
        self.assertTrue(completeness_errors(' какой провинции расположены три из пяти СЭЗ?', None, ['广东']))

    def test_rejects_too_short_question(self):
        self.assertTrue(completeness_errors('Столица Китая?', None, ['北京']))

    def test_rejects_empty_option(self):
        self.assertTrue(completeness_errors(WHOLE, None, ['西安', '  ']))


class FragmentTest(unittest.TestCase):
    def test_reports_question_that_is_a_prefix_of_another(self):
        pairs = fragment_pairs([
            ('2023-24-shk-138', 'Административный центр провинции Цзянсу, одна из четырех древних столиц'),
            ('2023-24-mun-138', WHOLE),
            ('2015-16-shk-1', 'Какова общая численность населения Китая в настоящее время?'),
        ])
        self.assertEqual(pairs, [('2023-24-shk-138', '2023-24-mun-138')])


if __name__ == '__main__':
    unittest.main()
