import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from wave import apply_results, select_wave


def record(record_id, state, option_id='o2', official='o2', topic='География и административное устройство'):
    return {
        'id': record_id, 'topic': topic,
        'questionRu': 'Какой город является крупнейшим портовым городом Китая?',
        'options': [{'id': 'o1', 'zh': '广州'}, {'id': 'o2', 'zh': '上海'}],
        'occurrences': [{'year': '2015-16', 'stage': 'школьный', 'stageCode': 'shk',
                         'number': 56, 'officialKey': official}],
        'answer': {'optionId': option_id, 'state': state},
        'explanation': {'ru': ''}, 'evidence': [], 'wave': 0,
    }


GOOD = {
    'explanation': 'Шанхай (上海) — крупнейший порт мира по контейнерообороту; 广州 уступает ему.',
    'evidence': [{'title': 'Порт Шанхая', 'url': 'https://example.org'}],
    'note': '',
}


class SelectWaveTest(unittest.TestCase):
    def test_unanswered_and_conflicting_go_first(self):
        bank = [record('a', 'unverified'), record('b', 'needs-review', None, None),
                record('c', 'conflict', None, None)]
        self.assertEqual([r['id'] for r in select_wave(bank, 2)], ['b', 'c'])

    def test_already_verified_are_not_offered_again(self):
        bank = [record('a', 'verified'), record('b', 'unverified')]
        self.assertEqual([r['id'] for r in select_wave(bank, 5)], ['b'])


class ApplyResultsTest(unittest.TestCase):
    def test_verified_record_gets_explanation_evidence_and_wave(self):
        bank = [record('a', 'unverified')]
        bank, mismatches = apply_results(bank, [{'id': 'a', 'optionId': 'o2', **GOOD}], wave=1)
        self.assertEqual(bank[0]['answer']['state'], 'verified')
        self.assertEqual(bank[0]['wave'], 1)
        self.assertTrue(bank[0]['evidence'][0]['checkedAt'])
        self.assertEqual(mismatches, [])

    def test_result_against_the_official_key_becomes_conflict(self):
        bank = [record('a', 'unverified')]
        bank, mismatches = apply_results(bank, [{
            'id': 'a', 'optionId': 'o1',
            'explanation': 'Источники называют другой город.',
            'evidence': [{'title': 'Источник', 'url': 'https://example.org'}],
            'note': 'расходится с ключом',
        }], wave=1)
        self.assertEqual(bank[0]['answer']['state'], 'conflict')
        self.assertEqual(len(mismatches), 1)

    def test_explicit_override_of_the_official_key_is_accepted_and_not_a_mismatch(self):
        """Автор проекта сам проверил факт и осознанно принимает решение, что
        официальный ключ ошибочен — это не то же самое, что молчаливое расхождение."""
        bank = [record('a', 'unverified')]
        bank, mismatches = apply_results(bank, [{
            'id': 'a', 'optionId': 'o1', 'overrideOfficialKey': True,
            'explanation': 'Источники расходятся с ключом, решение принято владельцем проекта.',
            'evidence': [{'title': 'Источник', 'url': 'https://example.org'}],
            'note': '',
        }], wave=1)
        self.assertEqual(bank[0]['answer'], {'optionId': 'o1', 'state': 'verified'})
        self.assertEqual(mismatches, [])

    def test_question_without_official_key_is_simply_verified(self):
        bank = [record('a', 'needs-review', None, None)]
        bank, mismatches = apply_results(bank, [{'id': 'a', 'optionId': 'o1', **GOOD}], wave=1)
        self.assertEqual(bank[0]['answer'], {'optionId': 'o1', 'state': 'verified'})
        self.assertEqual(mismatches, [])

    def test_result_without_evidence_is_rejected(self):
        bank = [record('a', 'unverified')]
        with self.assertRaises(ValueError):
            apply_results(bank, [{'id': 'a', 'optionId': 'o2', 'explanation': 'Потому что.',
                                  'evidence': [], 'note': ''}], wave=1)

    def test_result_without_explanation_is_rejected(self):
        bank = [record('a', 'unverified')]
        with self.assertRaises(ValueError):
            apply_results(bank, [{'id': 'a', 'optionId': 'o2', 'explanation': '   ',
                                  'evidence': [{'title': 'x', 'url': 'https://example.org'}], 'note': ''}], wave=1)

    def test_result_pointing_at_an_unknown_option_is_rejected(self):
        bank = [record('a', 'unverified')]
        with self.assertRaises(ValueError):
            apply_results(bank, [{'id': 'a', 'optionId': 'o9', **GOOD}], wave=1)


if __name__ == '__main__':
    unittest.main()
