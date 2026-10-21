import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from network import graph_notes, network_report, write_graph
from taxonomy import TOPICS

GEO = TOPICS[0]


def cell(zh, ru=(), **links):
    return {'zh': zh, 'ru': list(ru), **links}


def province(row_id, name, abbr, capital, core=None, olympiad=(), **extra):
    row = {'id': row_id, 'name': cell(name), 'abbr': cell(abbr), 'capital': cell(capital), 'named': cell(name + '名'),
           'sources': [], 'olympiad': list(olympiad), **extra}
    if core is not None:
        row['core'] = core
    return row


def core_dossier():
    return {'id': 'provinces', 'title': 'Провинции', 'tables': {'provinces': {
        'columns': {'name': 'zh', 'abbr': 'zh', 'capital': 'zh', 'named': 'zh'},
        'sides': ['abbr', 'capital', 'named'],
        'rows': [
            # ссылка на кухню — в досье, где каркаса ещё нет
            {**province('prov-sichuan', '四川', '川', '成都', core=True, olympiad=['2019-20-shk-1']),
             'abbr': cell('川', ref='cuisine/cuisines/sichuan-cuisine')},
            province('prov-hainan', '海南', '琼', '海口', core=True),
            province('prov-guizhou', '贵州', '黔', '贵阳'),
        ]}}}


def q(qid, row, ask, status='accepted', **extra):
    return {'id': qid, 'status': status, 'topic': GEO, 'questionRu': f'Вопрос {qid}?',
            'fact': {'table': 'provinces', 'row': row, 'ask': ask}, **extra}


def core_questions():
    # q04 — вопрос «какая провинция…» без given: его сторона «name» не в sides, он идёт в «другие»
    return [q('provinces-q01', 'prov-sichuan', 'abbr'), q('provinces-q02', 'prov-sichuan', 'abbr'),
            q('provinces-q04', 'prov-sichuan', 'name'),
            q('provinces-q03', 'prov-sichuan', 'capital'), q('provinces-q09', 'prov-guizhou', 'abbr'),
            q('provinces-q10', 'prov-hainan', 'abbr', status='draft')]


def plain_dossier():
    return {'id': 'cuisine', 'title': 'Кухня', 'tables': {'cuisines': {
        'columns': {'name': 'zh', 'taste': 'zh', 'region': 'zh'},
        'rows': [{'id': 'sichuan-cuisine', 'name': cell('川菜'), 'taste': cell('麻辣'), 'region': cell('四川'),
                  'sources': [], 'olympiad': []},
                 {'id': 'canton-cuisine', 'name': cell('粤菜'), 'taste': cell('清淡'), 'region': cell('广东'),
                  'sources': [], 'olympiad': []}]}}}


def plain_questions():
    fact = lambda row, ask: {'table': 'cuisines', 'row': row, 'ask': ask}
    return [{'id': 'cuisine-q01', 'status': 'accepted', 'topic': GEO, 'questionRu': 'Вопрос?', 'fact': fact('sichuan-cuisine', 'taste')},
            {'id': 'cuisine-q02', 'status': 'accepted', 'topic': GEO, 'questionRu': 'Вопрос?', 'fact': fact('sichuan-cuisine', 'region')},
            {'id': 'cuisine-q03', 'status': 'accepted', 'topic': GEO, 'questionRu': 'Вопрос?', 'fact': fact('canton-cuisine', 'taste')}]


def olympiad_record(year, stage, topic, record_id='x'):
    return {'id': record_id, 'topic': topic, 'questionRu': 'Вопрос?', 'occurrences': [{'year': year, 'stage': stage}]}


class NetworkReportTest(unittest.TestCase):
    def test_dossier_without_core_says_so_with_baseline_numbers(self):
        report = network_report([(plain_dossier(), plain_questions())], bank=[])
        self.assertIn('каркас не утверждён', report)
        self.assertIn('- строк: 2', report)
        self.assertIn('- принятых вопросов: 3', report)
        self.assertIn('- строк с вопросом: 2', report)
        self.assertIn('- строк, спрошенных с двух и более сторон (разные колонки ответа): 1', report)

    def test_core_matrix_counts_questions_per_side_and_marks_empty(self):
        report = network_report([(core_dossier(), core_questions())], bank=[])
        self.assertIn('| строка | abbr | capital | named | другие | олимпиада |', report)
        self.assertIn('| prov-sichuan | 2 | 1 | — | 1 | да |', report)
        # черновик не считается: у Хайнаня пусто
        self.assertIn('| prov-hainan | — | — | — | — | прогноз |', report)

    def test_russian_rows_are_left_to_the_russian_topic(self):
        data = core_dossier()
        data['tables']['provinces']['columns']['country'] = 'zh'
        data['tables']['provinces']['rows'].append(province('city-ru-tula', '图拉', '图', '图拉', country=cell('俄罗斯')))
        report = network_report([(data, core_questions() + [q('provinces-q20', 'city-ru-tula', 'abbr')])], bank=[])
        self.assertNotIn('provinces-q20 —', report)
        self.assertIn('Российские строки (разбирает российская тема): вопросов 1', report)

    def test_questions_outside_core_are_listed(self):
        report = network_report([(core_dossier(), core_questions())], bank=[])
        self.assertIn('provinces-q09', report)
        self.assertNotIn('provinces-q01 —', report)

    def test_link_to_a_topic_without_core_is_named_and_kept_in_notes(self):
        loaded = [(core_dossier(), core_questions()), (plain_dossier(), plain_questions())]
        report = network_report(loaded, bank=[])
        self.assertIn('ведёт в тему без каркаса', report)
        self.assertIn('provinces/provinces/prov-sichuan → cuisine/cuisines/sichuan-cuisine', report)
        notes = graph_notes(loaded, bank=[])
        self.assertIn('[[cuisine.sichuan-cuisine]]', notes['provinces.prov-sichuan.md'])
        self.assertNotIn('cuisine.sichuan-cuisine.md', notes)

    def test_core_row_without_links_is_isolated(self):
        report = network_report([(core_dossier(), core_questions())], bank=[])
        self.assertIn('изолированные узлы', report)
        self.assertIn('- provinces/provinces/prov-hainan', report)
        self.assertNotIn('- provinces/provinces/prov-sichuan\n', report)

    def test_olympiad_by_year_counts_occurrences_per_category(self):
        bank = [olympiad_record('2019-20', 'школьный', GEO, 'a'), olympiad_record('2019-20', 'школьный', GEO, 'b')]
        report = network_report([], bank)
        self.assertIn('| Категория | 2019-20 | Всего |', report)
        self.assertIn(f'| {GEO} | 2 | 2 |', report)
        self.assertIn('| Категория | школьный | Всего |', report)


class GraphNotesTest(unittest.TestCase):
    def test_notes_cover_dossiers_and_core_rows_only(self):
        loaded = [(core_dossier(), core_questions()), (plain_dossier(), plain_questions())]
        notes = graph_notes(loaded, bank=[])
        self.assertEqual(sorted(notes), ['cuisine.md', 'provinces.md', 'provinces.prov-hainan.md',
                                         'provinces.prov-sichuan.md'])
        self.assertIn('[[provinces.prov-sichuan]]', notes['provinces.md'])
        self.assertIn('Каркас не утверждён', notes['cuisine.md'])

    def test_row_note_lists_questions_by_side_and_olympiad(self):
        note = graph_notes([(core_dossier(), core_questions())], bank=[])['provinces.prov-sichuan.md']
        self.assertIn('# 四川', note)
        self.assertIn('Тема: [[provinces]]', note)
        self.assertIn('- abbr: provinces-q01 — Вопрос provinces-q01?', note)
        self.assertIn('2019-20-shk-1', note)

    def test_bank_text_wins_over_the_file(self):
        bank = [{'id': 'provinces-q01', 'questionRu': 'Исправленный текст?'}]
        note = graph_notes([(core_dossier(), core_questions())], bank)['provinces.prov-sichuan.md']
        self.assertIn('provinces-q01 — Исправленный текст?', note)

    def test_core_row_in_a_table_without_zh_columns_is_titled_by_id(self):
        data = core_dossier()
        data['tables']['notes'] = {'columns': {'about': 'ru'}, 'rows': [{'id': 'note-1', 'about': 'текст', 'core': True,
                                                                          'sources': [], 'olympiad': []}]}
        self.assertIn('# note-1', graph_notes([(data, [])], bank=[])['provinces.note-1.md'])

    def test_report_warns_that_the_graph_folder_is_rewritten(self):
        self.assertIn('свои заметки в эту папку не кладите', network_report([], bank=[]))

    def test_write_graph_removes_stale_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'old.md').write_text('x', 'utf-8')
            (Path(tmp) / '.obsidian').mkdir()
            write_graph(Path(tmp), {'new.md': 'y'})
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ['.obsidian', 'new.md'])
            self.assertEqual((Path(tmp) / 'new.md').read_text('utf-8'), 'y')


if __name__ == '__main__':
    unittest.main()
