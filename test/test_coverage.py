import contextlib, io, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from coverage_map import coverage_report, theme_matches, topic_shares, validate_coverage, validate_themes
import coverage_map
from taxonomy import TOPICS

GEO, HIST = TOPICS[0], TOPICS[3]


def record(id='2015-16-shk-1', topic=GEO, questionRu='Какая провинция Китая самая большая?', options=None,
           occurrences=True, **extra):
    return {'id': id, 'topic': topic, 'questionRu': questionRu, 'questionZh': None,
            'options': options or [{'id': 'o1', 'zh': '新疆'}, {'id': 'o2', 'zh': '西藏'}],
            'answer': {'optionId': (options or [{'id': 'o1'}])[0]['id'], 'state': 'verified'},
            'occurrences': occurrences if isinstance(occurrences, list) else
                           [{'year': '2015-16'}] if occurrences else [], **extra}


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
        self.assertTrue(any('sources' in e for e in validate_themes([theme(sources=[1])])))

    def test_broken_coverage_file_gives_a_message(self):
        self.assertTrue(validate_coverage({}))
        self.assertTrue(validate_coverage([]))
        self.assertEqual(validate_coverage({'themes': [theme()]}), [])


class ThemeMatchesTest(unittest.TestCase):
    def test_question_text_and_the_answer_are_searched_ignoring_case(self):
        bank = [record(), record(id='b', questionRu='Где течёт Хуанхэ?', options=[{'id': 'o1', 'zh': '山东省'}]),
                record(id='c', questionRu='Кто написал «Сон в красном тереме»?', options=[{'id': 'o1', 'zh': '曹雪芹'}])]
        self.assertEqual(theme_matches(bank, [theme(match=['ПРОВИНЦИ', '省'])]), {'geo-provinces': ['2015-16-shk-1', 'b']})

    def test_wrong_options_are_not_searched(self):
        # неверный вариант — соседний факт: 曹雪芹 среди вариантов вопроса о «Речных заводях» не делает его вопросом о «Сне»
        question = record(questionRu='Кто автор «Речных заводей»?',
                          options=[{'id': 'o1', 'zh': '施耐庵'}, {'id': 'o2', 'zh': '曹雪芹'}])
        self.assertEqual(theme_matches([question], [theme(match=['曹雪芹'])]), {'geo-provinces': []})

    def test_russian_words_match_from_the_start_of_a_word(self):
        bank = [record(questionRu='Какие сады Сучжоу внесены в список?'), record(id='b', questionRu='День посадки деревьев')]
        self.assertEqual(theme_matches(bank, [theme(match=['сад'])]), {'geo-provinces': ['2015-16-shk-1']})

    def test_yo_and_ye_are_the_same_letter(self):
        bank = [record(questionRu='Сколько ступеней учёных степеней в КНР?'),
                record(id='b', questionRu='Сколько ступеней ученых степеней в КНР?')]
        self.assertEqual(theme_matches(bank, [theme(match=['учёных степеней'])]), {'geo-provinces': ['2015-16-shk-1', 'b']})

    def test_answer_of_a_dossier_question_is_searched(self):
        # у вопроса досье id вариантов — id строк таблицы; ответ ищется, соседние строки — нет
        dossier_question = record(questionRu='Какой праздник отмечают 10 сентября?', dossier='holidays',
                                  options=[{'id': 'hol-teacher', 'zh': '教师节'}, {'id': 'hol-x', 'zh': '湖南省'}])
        self.assertEqual(theme_matches([dossier_question], [theme(match=['教师节'])]), {'geo-provinces': ['2015-16-shk-1']})
        self.assertEqual(theme_matches([dossier_question], [theme()]), {'geo-provinces': []})


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

    def test_report_shows_actual_category_counts_and_shares_without_quotas(self):
        report = coverage_report(self.bank, self.themes)
        self.assertIn('На сайте доступны 2 вопроса', report)
        self.assertRegex(report, rf'\| {GEO} \| 50 % \| 1 \| 50 % \|')
        self.assertNotIn('Цель —', report)
        self.assertNotIn('Нужно к цели', report)

    def test_report_lists_empty_themes_and_records_outside_every_theme(self):
        report = coverage_report(self.bank, self.themes)
        self.assertIn('Сражения', report.split('## Пустые темы')[1].split('##')[0])
        self.assertIn('`b`', report.split('## Вопросы вне тем')[1])

    def test_report_separates_sparse_themes_from_empty_themes(self):
        report = coverage_report(self.bank, self.themes)
        self.assertIn('## Темы с 1–2 вопросами', report)
        sparse = report.split('## Темы с 1–2 вопросами')[1].split('##')[0]
        self.assertIn('Провинции', sparse)
        self.assertNotIn('Сражения', sparse)


class CoverageMainTest(unittest.TestCase):
    def report(self, bank, settings, dossier_questions=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / 'data'
            (data / 'review').mkdir(parents=True)
            (data / 'dossiers').mkdir()
            for name, value in {
                'bank.json': bank,
                'site.json': settings,
                'coverage.json': {'themes': [theme()]},
                'dossiers/test-questions.json': dossier_questions or [],
            }.items():
                (data / name).write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
            with patch.object(coverage_map, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                coverage_map.main()
            return (data / 'review/coverage.md').read_text('utf-8')

    def test_main_uses_site_visibility_for_counts_matches_and_outside_questions(self):
        regional = [{'year': '2025-26', 'regionCode': 'test'}]
        bank = [
            record(id='public'),
            record(id='regional', topic=HIST, questionRu='СКРЫТАЯ региональная запись',
                   options=[{'id': 'o1', 'zh': '甲'}], occurrences=regional),
            record(id='by-id', topic=HIST, questionRu='Открытый вопрос вне тем',
                   options=[{'id': 'o1', 'zh': '夏'}], occurrences=regional),
            record(id='by-embed', occurrences=regional),
            record(id='draft', questionRu='СКРЫТОЕ черновое встраивание', occurrences=regional),
            record(id='editor-hidden', questionRu='СКРЫТО редактором', occurrences=regional),
            record(id='mixed', occurrences=[{'year': '2024-25'}, *regional]),
        ]
        settings = {'showRegional': False, 'showEmbeddedIn': ['test'],
                    'showRegionalIds': ['by-id', 'editor-hidden'],
                    'hiddenQuestions': {'editor-hidden': {'reason': 'снято автором', 'date': '2026-11-07'}}}
        dossier_questions = [{'embeds': 'by-embed', 'status': 'accepted'},
                             {'embeds': 'draft', 'status': 'draft'},
                             {'embeds': 'editor-hidden', 'status': 'accepted'}]
        report = self.report(bank, settings, dossier_questions)
        self.assertIn('На сайте доступны 4 вопроса', report)
        self.assertRegex(report, rf'\| {GEO} \| 75 % \| 3 \| 75 % \|')
        self.assertIn('| Провинции | 3 |', report)
        self.assertIn('`by-id`', report.split('## Вопросы вне тем')[1])
        self.assertNotIn('СКРЫТ', report)

    def test_main_honors_enabled_regional_setting(self):
        regional = record(id='regional', occurrences=[{'year': '2025-26', 'regionCode': 'test'}])
        report = self.report([regional], {'showRegional': True})
        self.assertIn('На сайте доступен 1 вопрос', report)
        self.assertIn('| Провинции — мало | 1 |', report)

    def test_empty_site_has_zero_shares_and_an_empty_theme(self):
        report = self.report([], {'showRegional': False})
        self.assertIn('На сайте доступны 0 вопросов', report)
        self.assertRegex(report, rf'\| {GEO} \| 0 % \| 0 \| 0 % \|')
        self.assertIn('Провинции', report.split('## Пустые темы')[1].split('##')[0])


class CoverageDataTest(unittest.TestCase):
    def test_real_theme_list_is_valid_and_every_topic_has_themes(self):
        data = json.loads((ROOT / 'data/coverage.json').read_text('utf-8'))
        self.assertEqual(validate_themes(data['themes']), [])
        self.assertEqual({t['topic'] for t in data['themes']}, set(TOPICS))


if __name__ == '__main__':
    unittest.main()
