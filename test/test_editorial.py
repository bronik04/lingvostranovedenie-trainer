import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from editorial import apply_editorial, validate_editorial


def record(**overrides):
    item = {
        'id': '2015-16-mun-1',
        'topic': 'История и государство',
        'topicSource': 'assigned',
        'questionRu': 'Как называлась самая ранняя династия Китая?',
        'questionZh': None,
        'options': [
            {'id': 'o1', 'zh': '夏'},
            {'id': 'o2', 'zh': '明'},
            {'id': 'o3', 'zh': '清'},
            {'id': 'o4', 'zh': '隋'},
        ],
        'answer': {'optionId': 'o1', 'state': 'verified'},
        'explanation': {'ru': 'Первой династией считается Ся.'},
    }
    item.update(overrides)
    return item


class EditorialTest(unittest.TestCase):
    def test_applies_question_option_explanation_and_topic(self):
        edits = {'2015-16-mun-1': {
            'reason': 'опечатка',
            'questionRu': 'Какая династия считается первой в истории Китая?',
            'options': {'o4': '秦'},
            'explanation': 'Первой династией считается Ся (夏).',
            'topic': 'Культура, традиции и праздники',
        }}
        [result] = apply_editorial([record()], edits)
        self.assertEqual(result['questionRu'], 'Какая династия считается первой в истории Китая?')
        self.assertEqual([o['zh'] for o in result['options']], ['夏', '明', '清', '秦'])
        self.assertEqual(result['explanation']['ru'], 'Первой династией считается Ся (夏).')
        self.assertEqual(result['topic'], 'Культура, традиции и праздники')
        self.assertEqual(result['topicSource'], 'editorial')
        self.assertEqual(result['answer'], {'optionId': 'o1', 'state': 'verified'})
        self.assertEqual(result['editorial'], {'reason': 'опечатка'})

    def test_keeps_id_and_untouched_records(self):
        other = record(id='other')
        edits = {'2015-16-mun-1': {'reason': 'x', 'options': {'o2': '元'}}}
        result = apply_editorial([record(), other], edits)
        self.assertEqual([r['id'] for r in result], ['2015-16-mun-1', 'other'])
        self.assertIs(result[1], other)

    def test_rejects_invalid_edits(self):
        bank = [record()]
        self.assertTrue(validate_editorial({'missing': {'reason': 'x', 'options': {'o1': '夏'}}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x'}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'options': {'o2': '元'}}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'options': {'o9': '元'}}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'options': {'o2': 'Мин'}}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'options': {'o2': '夏'}}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'questionRu': '朝代？'}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'topic': 'Нет такой'}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'explanation': ' '}}, bank))
        self.assertTrue(validate_editorial({'2015-16-mun-1': {'reason': 'x', 'surprise': 1}}, bank))


if __name__ == '__main__':
    unittest.main()
