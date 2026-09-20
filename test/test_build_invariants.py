import sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_html import serialize_bank, validate


def record(**overrides):
    base = {
        'id': '2015-16-shk-56', 'topic': 'География и административное устройство',
        'questionRu': 'Какой город является крупнейшим портовым городом Китая?',
        'questionZh': '中国最大的港口城市是哪一个？',
        'options': [{'id': 'o1', 'zh': '广州'}, {'id': 'o2', 'zh': '上海'},
                    {'id': 'o3', 'zh': '北京'}, {'id': 'o4', 'zh': '西安'}],
        'occurrences': [{'year': '2015-16', 'stage': 'школьный', 'stageCode': 'shk', 'number': 56}],
        'answer': {'optionId': 'o2', 'state': 'verified'},
        'explanation': {'ru': 'Шанхай (上海) — крупнейший порт мира по контейнерообороту.'},
        'evidence': [{'title': 'Порт Шанхая', 'url': 'https://example.org', 'checkedAt': '2026-09-18'}],
        'wave': 1,
    }
    base.update(overrides)
    return base


class ValidateTest(unittest.TestCase):
    def test_serialized_bank_cannot_close_its_script_tag(self):
        payload = record(explanation={'ru': '</script><script>alert(1)</script>'})
        result = serialize_bank([payload])
        self.assertNotIn('</script>', result.lower())
        self.assertIn('\\u003c/script>', result)

    def test_accepts_a_healthy_bank(self):
        self.assertEqual(validate([record()]), [])

    def test_rejects_chinese_question(self):
        self.assertTrue(validate([record(questionRu='中国最大的港口城市是哪一个？')]))

    def test_allows_chinese_terms_inside_a_russian_question(self):
        """«Какой из городов называют 泉城?» — законный вопрос олимпиады."""
        self.assertEqual(validate([record(questionRu='Какой из нижеперечисленных городов Китая называют 泉城?')]), [])

    def test_rejects_cyrillic_option(self):
        broken = record(options=[{'id': 'o1', 'zh': 'Шанхай'}], answer={'optionId': 'o1', 'state': 'verified'})
        self.assertTrue(validate([broken]))

    def test_rejects_truncated_question(self):
        self.assertTrue(validate([record(questionRu='дминистративный центр провинции Цзянсу')]))

    def test_rejects_answer_pointing_nowhere(self):
        self.assertTrue(validate([record(answer={'optionId': 'o9', 'state': 'verified'})]))

    def test_rejects_verified_without_explanation_or_evidence(self):
        self.assertTrue(validate([record(explanation={'ru': ''})]))
        self.assertTrue(validate([record(evidence=[])]))

    def test_rejects_duplicate_ids(self):
        self.assertTrue(validate([record(), record()]))

    def test_rejects_unknown_topic(self):
        self.assertTrue(validate([record(topic='Разное')]))


if __name__ == '__main__':
    unittest.main()
