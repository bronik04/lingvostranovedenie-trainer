import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from explanations import apply_revisions, validate_revisions


def record(**overrides):
    item = {
        'id': '2015-16-mun-2',
        'topic': 'Общество: население, этносы и религии',
        'questionRu': 'В какой части Китая проживает больше населения?',
        'options': [{'id': 'o1', 'zh': '东部'}, {'id': 'o2', 'zh': '西部'}],
        'occurrences': [{'year': '2015-16'}],
        'answer': {'optionId': 'o1', 'state': 'verified'},
        'explanation': {'ru': 'Старое пояснение.'},
        'evidence': [{'title': 'Старый источник', 'url': 'https://example.org', 'checkedAt': '2026-09-18'}],
    }
    item.update(overrides)
    return item


def revision(text='Факт верен. Контекст помогает его запомнить. Поэтому выбран этот вариант.', **overrides):
    item = {
        'explanation': text,
        'evidence': [{
            'title': 'Официальный источник',
            'url': 'https://www.gov.cn/example',
            'checkedAt': '2026-09-21',
            'authority': 'official',
        }],
        'reviewedAt': '2026-09-21',
    }
    item.update(overrides)
    return item


class ExplanationRevisionTest(unittest.TestCase):
    def test_applies_reviewed_explanation_without_changing_question_data(self):
        original = record()
        updated = apply_revisions([original], {'2015-16-mun-2': revision()})[0]
        self.assertEqual(updated['explanationRevision'], 2)
        self.assertEqual(updated['explanationReviewedAt'], '2026-09-21')
        self.assertEqual(updated['answer'], original['answer'])
        self.assertEqual(updated['questionRu'], original['questionRu'])
        self.assertEqual(updated['occurrences'], original['occurrences'])

    def test_rejects_unknown_id_short_text_and_unsafe_link(self):
        self.assertTrue(validate_revisions({'missing': revision()}, [record()]))
        self.assertTrue(validate_revisions({'2015-16-mun-2': revision('Коротко.')}, [record()]))
        self.assertTrue(validate_revisions({'2015-16-mun-2': revision(evidence=[{
            'title': 'x', 'url': 'ftp://example.org', 'checkedAt': '2026-09-21', 'authority': 'official',
        }])}, [record()]))


if __name__ == '__main__':
    unittest.main()
