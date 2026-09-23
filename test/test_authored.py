import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from authored import sentence_count, validate_authored


TOPIC = 'География и административное устройство'


def olympiad_record(**overrides):
    item = {
        'id': 'olympiad-1',
        'questionRu': 'Какой город является столицей Китая?',
    }
    item.update(overrides)
    return item


def addition(**overrides):
    item = {
        'id': 'addition-001',
        'origin': 'addition',
        'topic': TOPIC,
        'questionRu': 'Какой город является административным центром Китая?',
        'questionZh': None,
        'options': [
            {'id': 'o1', 'zh': '北京'},
            {'id': 'o2', 'zh': '上海'},
            {'id': 'o3', 'zh': '广州'},
            {'id': 'o4', 'zh': '西安'},
        ],
        'answer': {'optionId': 'o1', 'state': 'verified'},
        'explanation': {'ru': 'Пекин является столицей Китая. Здесь расположены центральные органы власти. Поэтому верен вариант 北京.'},
        'evidence': [{
            'title': 'Государственный портал КНР',
            'url': 'https://www.gov.cn/example',
            'checkedAt': '2026-09-21',
            'authority': 'official',
        }, {
            'title': 'Энциклопедия',
            'url': 'https://www.zgbk.com/example',
            'checkedAt': '2026-09-21',
            'authority': 'academic',
        }],
    }
    item.update(overrides)
    return item


class AuthoredQuestionTest(unittest.TestCase):
    def test_accepts_complete_addition(self):
        self.assertEqual(validate_authored([addition()], [olympiad_record()]), [])

    def test_rejects_unsafe_or_missing_evidence(self):
        self.assertTrue(validate_authored([addition(evidence=[])], []))
        bad_evidence = [{
            'title': 'x', 'url': 'javascript:alert(1)', 'checkedAt': '2026-09-21',
            'authority': 'official',
        }]
        self.assertTrue(validate_authored([addition(evidence=bad_evidence)], []))

    def test_requires_two_official_or_academic_sources(self):
        one = addition()['evidence'][:1]
        self.assertTrue(validate_authored([addition(evidence=one)], []))
        blog = [*addition()['evidence'][:1], {**addition()['evidence'][1], 'authority': 'blog'}]
        self.assertTrue(validate_authored([addition(evidence=blog)], []))

    def test_rejects_duplicate_and_invalid_reverse_link(self):
        base = [olympiad_record()]
        self.assertTrue(validate_authored([addition(questionRu=base[0]['questionRu'])], base))
        self.assertTrue(validate_authored([addition(derivedFrom='missing')], base))
        self.assertTrue(validate_authored([
            addition(derivedFrom='olympiad-1', questionRu=base[0]['questionRu']),
        ], base))

    def test_rejects_bad_options_and_sentence_count(self):
        self.assertTrue(validate_authored([addition(options=addition()['options'][:3])], []))
        self.assertTrue(validate_authored([addition(explanation={'ru': 'Одно предложение.'})], []))
        self.assertTrue(validate_authored([
            addition(explanation={'ru': 'Раз. Два. Три. Четыре. Пять. Шесть.'}),
        ], []))

    def test_sentence_count_ignores_abbreviations_and_initials(self):
        self.assertEqual(sentence_count(
            'Договор подписали 16 мая 1858 г. в Айгуне. Н. Н. Муравьёв получил титул. '
            'Это было ок. 1860 г., т. е. позже. 汴京 — столица Северной Сун.'), 4)
        self.assertEqual(sentence_count('Раз. Два. Три.'), 3)
        self.assertEqual(sentence_count('Это высший орган КНР. Оно важно. Верен ответ 全国人大.'), 3)


if __name__ == '__main__':
    unittest.main()
