import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coverage_map import coverage_report, theme_matches, topic_shares, validate_themes
from taxonomy import TOPICS

GEO, HIST = TOPICS[0], TOPICS[3]


def record(id='2015-16-shk-1', topic=GEO, questionRu='Какая провинция Китая самая большая?', options=None,
           occurrences=True, **extra):
    return {'id': id, 'topic': topic, 'questionRu': questionRu, 'questionZh': None,
            'options': options or [{'id': 'o1', 'zh': '新疆'}, {'id': 'o2', 'zh': '西藏'}],
            'occurrences': [{'year': '2015-16'}] if occurrences else [], **extra}


def theme(id='geo-provinces', topic=GEO, title='Провинции', match=None, sources=None):
    return {'id': id, 'topic': topic, 'title': title,
            'match': ['провинци', '省'] if match is None else match,
            'sources': ['олимпиада'] if sources is None else sources}


class ValidateThemesTest(unittest.TestCase):
    def test_good_themes_pass(self):
        self.assertEqual(validate_themes([theme(), theme(id='hist-dynasties', topic=HIST, match=['династи'])]), [])

    def test_unknown_topic_duplicate_id_and_empty_match_are_errors(self):
        errors = validate_themes([theme(topic='Разное'), theme(), theme(id='x', match=[])])
        self.assertTrue(any('Разное' in e for e in errors))
        self.assertTrue(any('geo-provinces' in e and 'повтор' in e for e in errors))
        self.assertTrue(any(e.startswith('x:') and 'match' in e for e in errors))

    def test_theme_needs_a_source(self):
        self.assertTrue(any('sources' in e for e in validate_themes([theme(sources=[])])))


class ThemeMatchesTest(unittest.TestCase):
    def test_question_text_and_options_are_searched_ignoring_case(self):
        bank = [record(), record(id='b', questionRu='Где течёт Хуанхэ?', options=[{'id': 'o1', 'zh': '山东省'}]),
                record(id='c', questionRu='Кто написал «Сон в красном тереме»?', options=[{'id': 'o1', 'zh': '曹雪芹'}])]
        self.assertEqual(theme_matches(bank, [theme(match=['ПРОВИНЦИ', '省'])]), {'geo-provinces': ['2015-16-shk-1', 'b']})

    def test_yo_and_ye_are_the_same_letter(self):
        bank = [record(questionRu='Сколько ступеней учёных степеней в КНР?'),
                record(id='b', questionRu='Сколько ступеней ученых степеней в КНР?')]
        self.assertEqual(theme_matches(bank, [theme(match=['учёных степеней'])]), {'geo-provinces': ['2015-16-shk-1', 'b']})

    def test_options_added_by_a_dossier_are_not_searched(self):
        embedded = record(questionRu='Какой праздник отмечают 10 сентября?', dossier='holidays',
                          options=[{'id': 'o1', 'zh': '教师节'}, {'id': 'hol-x', 'zh': '湖南省'}])
        self.assertEqual(theme_matches([embedded], [theme()]), {'geo-provinces': []})


class TopicSharesTest(unittest.TestCase):
    def test_olympiad_share_counts_only_records_from_olympiad_papers(self):
        bank = [record(), record(id='b'), record(id='c', topic=HIST),
                record(id='addition-1', topic=HIST, occurrences=False)]
        shares = topic_shares(bank)
        self.assertAlmostEqual(shares[GEO]['olympiad'], 2 / 3)
        self.assertEqual(shares[HIST]['bank'], 2)
        self.assertEqual(shares[TOPICS[1]]['bank'], 0)


class CoverageReportTest(unittest.TestCase):
    def setUp(self):
        self.bank = [record(), record(id='b', topic=HIST, questionRu='Как называлась первая династия?',
                                      options=[{'id': 'o1', 'zh': '夏'}])]
        self.themes = [theme(), theme(id='hist-wars', topic=HIST, title='Сражения', match=['сражени'])]

    def test_report_shows_target_gap_per_topic(self):
        report = coverage_report(self.bank, self.themes, target=1000)
        self.assertIn('Цель — 1000', report)
        # география — половина олимпиады, в банке 1 из 2: к 1000 нужно ещё 499
        self.assertRegex(report, rf'\| {GEO} \| 50 % \| 1 \| 500 \| 499 \|')

    def test_report_lists_empty_themes_and_records_outside_every_theme(self):
        report = coverage_report(self.bank, self.themes, target=1000)
        self.assertIn('Сражения', report.split('## Пустые темы')[1].split('##')[0])
        self.assertIn('`b`', report.split('## Вопросы вне тем')[1])


class CoverageDataTest(unittest.TestCase):
    def test_real_theme_list_is_valid_and_every_topic_has_themes(self):
        data = json.loads((ROOT / 'data/coverage.json').read_text('utf-8'))
        self.assertEqual(validate_themes(data['themes']), [])
        self.assertEqual({t['topic'] for t in data['themes']}, set(TOPICS))


if __name__ == '__main__':
    unittest.main()
