import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from taxonomy import TOPICS, assign_topics


def record(**overrides):
    base = {'id': '2015-16-shk-1', 'topic': None, 'topicSource': 'assigned',
            'questionRu': 'Какой город является крупнейшим портовым городом Китая?',
            'questionZh': None, 'options': [{'id': 'o1', 'zh': '上海'}]}
    base.update(overrides)
    return base


class TaxonomyTest(unittest.TestCase):
    def setUp(self):
        self.rules = json.loads((ROOT / 'data/taxonomy.json').read_text('utf-8'))

    def test_seven_topics_and_no_misc(self):
        self.assertEqual(len(TOPICS), 7)
        self.assertNotIn('Разное', TOPICS)
        self.assertEqual(set(self.rules['topics']), set(TOPICS))

    def test_keeps_topic_that_came_from_categories_310(self):
        bank, disputed = assign_topics(
            [record(topic='Культура, традиции и праздники', topicSource='categories-310')], self.rules)
        self.assertEqual(bank[0]['topic'], 'Культура, традиции и праздники')
        self.assertEqual(disputed, [])

    def test_assigns_topic_by_keywords_and_reports_it(self):
        bank, disputed = assign_topics([record()], self.rules)
        self.assertEqual(bank[0]['topic'], 'География и административное устройство')
        self.assertEqual(bank[0]['topicSource'], 'assigned')
        self.assertEqual(len(disputed), 1)

    def test_russia_questions_go_to_the_intercultural_topic(self):
        bank, _ = assign_topics([record(questionRu='Кто считается основателем российского флота?')], self.rules)
        self.assertEqual(bank[0]['topic'], 'Россия и межкультурный блок')

    def test_every_record_ends_with_a_known_topic(self):
        bank, _ = assign_topics([record(questionRu='Вопрос, не попадающий ни в одно правило вообще?')], self.rules)
        self.assertIn(bank[0]['topic'], TOPICS)


if __name__ == '__main__':
    unittest.main()
