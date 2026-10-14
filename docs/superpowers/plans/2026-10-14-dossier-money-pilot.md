# Досье «Деньги» (пилот) — план реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** досье — таблица проверенных фактов, из ячеек которой собираются вопросы с общим набором неверных вариантов; пилот — досье «Деньги» от пустой таблицы до принятых автором вопросов в банке.

**Architecture:** новый модуль `scripts/dossiers.py` проверяет таблицы (`data/dossiers/<id>.json`) и вопросы (`data/dossiers/<id>-questions.json`), строит из принятых вопросов записи банка (`origin: "addition"`, `dossier: "<id>"`: правильный вариант — ячейка, неверные — та же колонка соседних строк, подписи — из ячеек) и пишет отчёт для автора. `scripts/merge_bank.py` добавляет эти записи сразу после дополнений из `data/authored/`. Задачи 1–5 — код на маленьком тестовом досье, задачи 6–10 — наполнение настоящего досье агентами.

**Tech Stack:** Python 3 (stdlib, unittest), JSON-слои данных; интерфейс (`src/`) не меняется.

**Spec:** `docs/superpowers/specs/2026-10-14-dossier-money-pilot-design.md`

## Global Constraints

- `data/bank.json` и `dist/` руками не править: только `npm run build`. `sources/` не редактировать.
- Вопрос по-русски, варианты по-китайски (проверяет сборка, `scripts/normalize.py`).
- Источник строки досье: не меньше двух независимых, каждый `authority` — `official` или `academic`, с дословной `quote`, `title`, `url` (http/https) и `checkedAt`. Википедия в `sources` не попадает.
- Подпись ячейки: одна строка по-русски, не длиннее 90 знаков (`MAX_LENGTH` из `scripts/glosses.py`).
- В банк идут только вопросы со `status: "accepted"` и вердиктом проверки `check.verdict == "accept"`.
- id вопроса — `<id досье>-qNN`, от текста не зависит; id варианта — id строки таблицы.
- Пояснение вопроса досье говорит только о правильном ответе; 3–5 предложений (правило дополнений).
- JSON-файлы данных пишутся `json.dumps(..., ensure_ascii=False, indent=2) + '\n'`.
- Тесты: `python3 -m unittest discover -s test -t .` и `node --test test/*.test.mjs` (глоб без кавычек).
- Каждое заметное изменение — запись в `CHANGELOG.md` в том же коммите.
- Агенты — только с согласия автора на каждый запуск, одновременно не больше трёх; в их HTTP-запросах никаких личных данных (имён, почты), только обезличенный User-Agent.
- Работа в ветке `feat/dossier-money` от `feat/dossier-money-spec`; перед слиянием в master — спросить автора, нужно ли ревью.

## Review Focus

- Таблица растёт (новая строка) после того, как вопрос принят: правильный вариант и id прежних вариантов не меняются, новая строка просто добавляется в набор — тест в задаче 2.
- Черновик со сломанной ссылкой: сборка останавливается сразу, а не когда вопрос примут, — тест в задаче 3.
- Русское название ответа в тексте с другой заглавной буквой («Лотос» при `ru: ["лотос"]`) — всё равно подсказка — тест в задаче 3.
- Правка `editorial.json` по вопросу досье адресует вариант по id строки (`cny-50`) и работает, как у любой записи — тест в задаче 4.
- Ссылка `olympiad` на олимпиадный вопрос, влитый склейкой в другой (`mergedIds`), считается живой — тест в задаче 4.

---

### Task 1: Проверка таблиц досье

**Files:**
- Create: `scripts/dossiers.py`
- Create: `test/test_dossiers.py`

**Interfaces:**
- Consumes: `evidence_errors(evidence) -> list[str]` из `scripts/authored.py`; `MAX_LENGTH` из `scripts/glosses.py`; `CYRILLIC` из `scripts/normalize.py`.
- Produces: `validate_dossier(dossier: object) -> list[str]`; константы `KINDS`, `ROW_SERVICE_FIELDS`; тестовые фабрики `dossier()`, `note(...)`, `cell(...)`, `source(n)` в `test/test_dossiers.py` (ими пользуются задачи 2–5).

- [ ] **Step 1: Создать ветку**

```bash
git checkout -b feat/dossier-money feat/dossier-money-spec
```

- [ ] **Step 2: Написать падающий тест**

`test/test_dossiers.py`:

```python
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from dossiers import validate_dossier

TOPIC = 'Экономика, образование, наука и спорт'


def source(n):
    return {'title': f'Источник {n}', 'url': f'https://www.pbc.gov.cn/page-{n}', 'quote': 'цитата',
            'checkedAt': '2026-10-15', 'authority': 'official'}


def cell(zh, ru=(), gloss=None):
    item = {'zh': zh, 'ru': list(ru)}
    if gloss is not None:
        item['gloss'] = gloss
    return item


def note(row_id, currency, denomination, back, back_ru, flower=None, flower_ru=(),
         series='пятая серия, выпуск 2019 года'):
    row = {'id': row_id, 'currency': cell(currency),
           'denomination': cell(denomination, gloss=f'Купюра {denomination}'),
           'series': series,
           'back': cell(back, back_ru, gloss=f'{back_ru[0]} — на обороте купюры'),
           'sources': [source(1), source(2)], 'olympiad': []}
    if flower:
        row['flower'] = cell(flower, flower_ru, gloss=f'{flower_ru[0].capitalize()} — цветок на купюре')
    return row


def dossier():
    return {'id': 'money', 'title': 'Деньги', 'tables': {'banknotes': {
        'columns': {'currency': 'zh', 'denomination': 'zh', 'series': 'ru', 'back': 'zh', 'flower': 'zh'},
        'required': ['series'], 'datedQuestions': True,
        'rows': [
            note('cny-100', '人民币', '100 元', '人民大会堂', ['Дом народных собраний'], '梅花', ['мэйхуа']),
            note('cny-50', '人民币', '50 元', '布达拉宫', ['Потала'], '菊花', ['хризантема']),
            note('cny-20', '人民币', '20 元', '桂林山水', ['Гуйлинь'], '荷花', ['лотос']),
            note('cny-10', '人民币', '10 元', '长江三峡', ['Три ущелья'], '月季花', ['китайская роза']),
            note('cny-5', '人民币', '5 元', '泰山', ['Тайшань'], '水仙花', ['нарцисс']),
            note('rub-500', '卢布', '500 卢布', '索洛韦茨基修道院', ['Соловецкий монастырь'],
                 series='образца 1997 года'),
        ]}}}


def row(data, row_id):
    return next(r for r in data['tables']['banknotes']['rows'] if r['id'] == row_id)


class ValidateDossierTest(unittest.TestCase):
    def assertRejects(self, mutate, fragment):
        data = dossier()
        mutate(data)
        errors = validate_dossier(data)
        self.assertTrue(any(fragment in error for error in errors), f'{fragment!r} not in {errors}')

    def test_accepts_a_valid_dossier(self):
        self.assertEqual(validate_dossier(dossier()), [])

    def test_rejects_a_dossier_that_is_not_an_object(self):
        self.assertEqual(validate_dossier([]), ['досье должно быть объектом'])

    def test_rejects_each_broken_rule(self):
        table = lambda d: d['tables']['banknotes']
        cases = [
            (lambda d: d.pop('title'), 'нет названия'),
            (lambda d: d.update(id='Деньги'), 'нет id'),
            (lambda d: d.update(tables={}), 'нет таблиц'),
            (lambda d: table(d).update(extra=1), 'неизвестные поля таблицы'),
            (lambda d: table(d)['columns'].update(back='en'), 'колонки'),
            (lambda d: table(d)['columns'].update(sources='zh'), 'заняты служебными полями'),
            (lambda d: table(d).update(required=['colour']), 'required'),
            (lambda d: table(d).update(datedQuestions='да'), 'datedQuestions'),
            (lambda d: row(d, 'cny-50').update(colour=cell('红')), 'необъявленные колонки'),
            (lambda d: row(d, 'cny-50').update(id='cny-100'), 'повторяющийся id строки'),
            (lambda d: row(d, 'cny-50').update(id='CNY 50'), 'нет id строки'),
            (lambda d: row(d, 'cny-50').pop('series'), 'нет обязательной колонки series'),
            (lambda d: row(d, 'cny-50').update(back=cell('Потала')), 'не по-китайски'),
            (lambda d: row(d, 'cny-50').update(back='布达拉宫'), 'должна быть объектом'),
            (lambda d: row(d, 'cny-50')['back'].update(ru='Потала'), 'список русских названий'),
            (lambda d: row(d, 'cny-50')['back'].update(gloss='Д' * 91), 'длиннее 90'),
            (lambda d: row(d, 'cny-50')['back'].update(gloss='две\nстроки'), 'одна непустая строка'),
            (lambda d: row(d, 'cny-50')['back'].update(note='x'), 'неизвестные поля ячейки'),
            (lambda d: row(d, 'cny-50').update(series=''), 'описательная ячейка'),
            (lambda d: row(d, 'cny-50').update(sources=[source(1)]), 'не меньше 2 источников'),
            (lambda d: row(d, 'cny-50')['sources'][0].pop('quote'), 'нет цитаты'),
            (lambda d: row(d, 'cny-50')['sources'][0].update(authority='reference'), 'не помечен официальным'),
            (lambda d: row(d, 'cny-50').update(sources=[source(1), source(1)]), 'источники повторяются'),
            (lambda d: row(d, 'cny-50').update(olympiad='2024-25-shk-29'), 'olympiad'),
        ]
        for mutate, fragment in cases:
            with self.subTest(fragment=fragment):
                self.assertRejects(mutate, fragment)

    def test_cell_without_russian_names_or_gloss_is_valid(self):
        data = dossier()
        row(data, 'cny-50')['back'] = {'zh': '布达拉宫'}
        self.assertEqual(validate_dossier(data), [])


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 3: Запустить и убедиться, что падает**

Run: `python3 -m unittest test.test_dossiers -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dossiers'`.

- [ ] **Step 4: Написать проверку таблиц**

`scripts/dossiers.py`:

```python
"""Досье: таблица проверенных фактов по одной теме и вопросы, которые ссылаются на её ячейки.

Спецификация — docs/superpowers/specs/2026-10-14-dossier-money-pilot-design.md.
Вопрос не пишет варианты сам: правильный — ячейка таблицы, неверные — та же колонка в
соседних строках (общий набор), подписи к ним — из ячеек. В банк идут только вопросы,
принятые автором (`status: "accepted"`).
"""

from __future__ import annotations

import re

from authored import evidence_errors
from glosses import MAX_LENGTH
from normalize import CYRILLIC

KINDS = {'zh', 'ru'}
TABLE_FIELDS = {'columns', 'rows', 'required', 'datedQuestions'}
ROW_SERVICE_FIELDS = {'id', 'sources', 'olympiad'}
CELL_FIELDS = {'zh', 'ru', 'gloss'}
MIN_SOURCES = 2
SLUG = re.compile(r'[a-z0-9][a-z0-9-]*')


def _cell_errors(where: str, cell: object) -> list[str]:
    if not isinstance(cell, dict):
        return [f'{where}: ячейка-вариант должна быть объектом']
    errors: list[str] = []
    unknown = set(cell) - CELL_FIELDS
    if unknown:
        errors.append(f'{where}: неизвестные поля ячейки {sorted(unknown)}')
    zh = cell.get('zh')
    if not isinstance(zh, str) or not zh.strip():
        errors.append(f'{where}: пустой текст варианта')
    elif CYRILLIC.search(zh):
        errors.append(f'{where}: текст варианта не по-китайски: {zh!r}')
    names = cell.get('ru', [])
    if not isinstance(names, list) or not all(isinstance(name, str) and name.strip() for name in names):
        errors.append(f'{where}: ru — список русских названий')
    gloss = cell.get('gloss')
    if gloss is not None:
        if not isinstance(gloss, str) or not gloss.strip() or '\n' in gloss:
            errors.append(f'{where}: подпись — одна непустая строка')
        elif len(gloss) > MAX_LENGTH:
            errors.append(f'{where}: подпись длиннее {MAX_LENGTH} символов')
    return errors


def _source_errors(where: str, sources: object) -> list[str]:
    if not isinstance(sources, list) or len(sources) < MIN_SOURCES:
        return [f'{where}: нужно не меньше {MIN_SOURCES} источников']
    errors = [f'{where}: {message}' for message in evidence_errors(sources)]
    for index, item in enumerate(sources, start=1):
        if isinstance(item, dict) and (not isinstance(item.get('quote'), str) or not item['quote'].strip()):
            errors.append(f'{where}: у источника {index} нет цитаты')
    urls = [item.get('url') for item in sources if isinstance(item, dict)]
    if len(set(urls)) != len(urls):
        errors.append(f'{where}: источники повторяются')
    return errors


def _row_errors(name: str, index: int, row: object, table: dict, seen_rows: set[str]) -> list[str]:
    if not isinstance(row, dict):
        return [f'{name}: строка {index} должна быть объектом']
    columns = table['columns']
    row_id = row.get('id')
    where = f'{name}/{row_id}' if isinstance(row_id, str) else f'{name}/строка {index}'
    errors: list[str] = []
    if not isinstance(row_id, str) or not SLUG.fullmatch(row_id):
        errors.append(f'{where}: нет id строки (латиница, цифры, дефис)')
    elif row_id in seen_rows:
        errors.append(f'{where}: повторяющийся id строки')
    else:
        seen_rows.add(row_id)
    unknown = set(row) - set(columns) - ROW_SERVICE_FIELDS
    if unknown:
        errors.append(f'{where}: необъявленные колонки {sorted(unknown)}')
    for column in table.get('required', []):
        if column not in row:
            errors.append(f'{where}: нет обязательной колонки {column}')
    for column, kind in columns.items():
        if column not in row:
            continue
        if kind == 'zh':
            errors += _cell_errors(f'{where}.{column}', row[column])
        elif not isinstance(row[column], str) or not row[column].strip():
            errors.append(f'{where}.{column}: описательная ячейка — непустая строка')
    errors += _source_errors(where, row.get('sources'))
    olympiad = row.get('olympiad', [])
    if not isinstance(olympiad, list) or not all(isinstance(item, str) for item in olympiad):
        errors.append(f'{where}: olympiad — список id олимпиадных вопросов')
    return errors


def validate_dossier(dossier: object) -> list[str]:
    if not isinstance(dossier, dict):
        return ['досье должно быть объектом']
    errors: list[str] = []
    if not isinstance(dossier.get('id'), str) or not re.fullmatch(r'[a-z][a-z0-9-]*', dossier['id']):
        errors.append('у досье нет id (латиница, цифры, дефис)')
    if not isinstance(dossier.get('title'), str) or not dossier['title'].strip():
        errors.append('у досье нет названия')
    tables = dossier.get('tables')
    if not isinstance(tables, dict) or not tables:
        return errors + ['в досье нет таблиц']
    # id строки — id варианта в банке, поэтому он уникален во всём досье, а не только в таблице
    seen_rows: set[str] = set()
    for name, table in tables.items():
        if not isinstance(table, dict):
            errors.append(f'{name}: таблица должна быть объектом')
            continue
        unknown = set(table) - TABLE_FIELDS
        if unknown:
            errors.append(f'{name}: неизвестные поля таблицы {sorted(unknown)}')
        columns = table.get('columns')
        if not isinstance(columns, dict) or not columns or any(kind not in KINDS for kind in columns.values()):
            errors.append(f'{name}: колонки — словарь имя → zh или ru')
            continue
        reserved = set(columns) & ROW_SERVICE_FIELDS
        if reserved:
            errors.append(f'{name}: имена колонок заняты служебными полями {sorted(reserved)}')
        required = table.get('required', [])
        if not isinstance(required, list) or any(column not in columns for column in required):
            errors.append(f'{name}: required называет необъявленную колонку')
            table = {**table, 'required': []}
        if not isinstance(table.get('datedQuestions', False), bool):
            errors.append(f'{name}: datedQuestions — true или false')
        rows = table.get('rows')
        if not isinstance(rows, list):
            errors.append(f'{name}: rows должен быть списком')
            continue
        for index, row in enumerate(rows, start=1):
            errors += _row_errors(name, index, row, table, seen_rows)
    return errors
```

- [ ] **Step 5: Запустить тесты**

Run: `python3 -m unittest test.test_dossiers -v`
Expected: PASS (3 теста). Если `from glosses import MAX_LENGTH` даёт циклический импорт — проверить верх `scripts/glosses.py`; он не должен импортировать `dossiers`.

- [ ] **Step 6: Commit**

```bash
git add scripts/dossiers.py test/test_dossiers.py
git commit -m "Досье: проверка таблиц фактов"
```

---

### Task 2: Варианты и записи банка из вопроса досье

**Files:**
- Modify: `scripts/dossiers.py`
- Modify: `test/test_dossiers.py`

**Interfaces:**
- Consumes: `dossier()`, `row()`, `cell()` из тестов задачи 1; проверенное досье.
- Produces:
  - `answer_cell(question: dict, dossier: dict) -> tuple[str, dict]` — id строки и ячейка правильного ответа;
  - `question_options(question: dict, dossier: dict) -> tuple[list[dict], str]` — варианты (правильный первым, неверные в порядке таблицы, повторы текста сведены к первой строке, у неверных `gloss` их ячеек) и id правильного;
  - `dossier_records(dossier: dict, questions: list[dict]) -> list[dict]` — записи банка для `accepted`.
  Обе функции считают ссылки вопроса уже проверенными (задача 3).

- [ ] **Step 1: Написать падающие тесты**

Добавить в `test/test_dossiers.py` (импорт расширить: `from dossiers import dossier_records, question_options, validate_dossier`):

```python
def question(**overrides):
    item = {'id': 'money-q01', 'status': 'accepted', 'topic': TOPIC,
            'fact': {'table': 'banknotes', 'row': 'cny-20', 'ask': 'flower', 'where': {'currency': '人民币'}},
            'questionRu': 'Какой цветок изображён на лицевой стороне купюры 20 юаней выпуска 2019 года?',
            'explanation': 'Первое предложение. Второе предложение. Третье предложение.',
            'exclude': [], 'check': {'verdict': 'accept', 'note': 'ок'}}
    item.update(overrides)
    return item


def ids(options):
    return [option['id'] for option in options]


class QuestionOptionsTest(unittest.TestCase):
    def test_pool_is_the_same_column_of_sibling_rows(self):
        options, answer = question_options(question(), dossier())
        self.assertEqual(answer, 'cny-20')
        self.assertEqual(ids(options), ['cny-20', 'cny-100', 'cny-50', 'cny-10', 'cny-5'])
        self.assertEqual(options[0]['zh'], '荷花')

    def test_where_keeps_only_matching_rows(self):
        fact = {'table': 'banknotes', 'row': 'cny-50', 'ask': 'back'}
        mixed, _ = question_options(question(fact=fact), dossier())
        self.assertIn('rub-500', ids(mixed))
        yuan, _ = question_options(question(fact={**fact, 'where': {'currency': '人民币'}}), dossier())
        self.assertNotIn('rub-500', ids(yuan))

    def test_exclude_drops_a_row(self):
        options, _ = question_options(question(exclude=['cny-5']), dossier())
        self.assertNotIn('cny-5', ids(options))

    def test_repeated_wrong_values_collapse_to_the_first_row(self):
        data = dossier()
        row(data, 'cny-10')['flower'] = cell('梅花', ['мэйхуа'], gloss='Мэйхуа — ещё раз')
        options, _ = question_options(question(), data)
        self.assertEqual(ids(options), ['cny-20', 'cny-100', 'cny-50', 'cny-5'])

    def test_wrong_options_carry_glosses_of_their_cells_and_the_answer_does_not(self):
        options, _ = question_options(question(), dossier())
        self.assertNotIn('gloss', options[0])
        self.assertEqual(options[2], {'id': 'cny-50', 'zh': '菊花', 'gloss': 'Хризантема — цветок на купюре'})

    def test_given_direction_asks_another_column_of_the_same_row(self):
        fact = {'table': 'banknotes', 'row': 'cny-50', 'ask': 'denomination', 'given': 'flower',
                'where': {'currency': '人民币'}}
        options, answer = question_options(question(fact=fact), dossier())
        self.assertEqual((answer, options[0]['zh']), ('cny-50', '50 元'))
        self.assertEqual([o['zh'] for o in options[1:]], ['100 元', '20 元', '10 元', '5 元'])

    def test_explicit_options_put_the_answer_first(self):
        refs = [{'row': r, 'column': 'back'} for r in ('cny-100', 'cny-50', 'cny-20', 'rub-500')]
        fact = {'table': 'banknotes', 'options': refs, 'answer': {'row': 'rub-500', 'column': 'back'}}
        options, answer = question_options(question(fact=fact), dossier())
        self.assertEqual(answer, 'rub-500')
        self.assertEqual(ids(options), ['rub-500', 'cny-100', 'cny-50', 'cny-20'])

    def test_new_row_keeps_the_answer_and_existing_option_ids(self):
        before, answer_before = question_options(question(), dossier())
        data = dossier()
        data['tables']['banknotes']['rows'].append(
            note('cny-1', '人民币', '1 元', '三潭印月', ['Три пруда'], '兰花', ['орхидея']))
        after, answer_after = question_options(question(), data)
        self.assertEqual(answer_after, answer_before)
        self.assertEqual(after[:len(before)], before)
        self.assertEqual(ids(after)[-1], 'cny-1')


class DossierRecordsTest(unittest.TestCase):
    def test_accepted_question_becomes_an_addition_record(self):
        [record] = dossier_records(dossier(), [question()])
        self.assertEqual(record['id'], 'money-q01')
        self.assertEqual(record['origin'], 'addition')
        self.assertEqual(record['dossier'], 'money')
        self.assertEqual(record['topic'], TOPIC)
        self.assertEqual(record['topicSource'], 'authored')
        self.assertIsNone(record['questionZh'])
        self.assertEqual(record['answer'], {'optionId': 'cny-20', 'state': 'verified'})
        self.assertEqual(record['explanation'], {'ru': question()['explanation']})
        self.assertEqual((record['occurrences'], record['parseWarnings']), ([], []))
        self.assertEqual(len(record['options']), 5)

    def test_draft_stays_out_of_the_bank(self):
        self.assertEqual(dossier_records(dossier(), [question(status='draft')]), [])

    def test_evidence_is_the_answer_row_sources_without_quotes(self):
        [record] = dossier_records(dossier(), [question()])
        self.assertEqual(record['evidence'], [
            {key: value for key, value in source(n).items() if key != 'quote'} for n in (1, 2)])
```

- [ ] **Step 2: Запустить и убедиться, что падает**

Run: `python3 -m unittest test.test_dossiers -v`
Expected: FAIL — `ImportError: cannot import name 'dossier_records'`.

- [ ] **Step 3: Написать построение вариантов и записей**

Добавить в `scripts/dossiers.py`:

```python
EVIDENCE_FIELDS = ('title', 'url', 'checkedAt', 'authority')


def _rows(dossier: dict, table: str) -> dict[str, dict]:
    return {row['id']: row for row in dossier['tables'][table]['rows']}


def answer_cell(question: dict, dossier: dict) -> tuple[str, dict]:
    fact = question['fact']
    rows = _rows(dossier, fact['table'])
    if 'options' in fact:
        ref = fact['answer']
        return ref['row'], rows[ref['row']][ref['column']]
    return fact['row'], rows[fact['row']][fact['ask']]


def _candidates(question: dict, dossier: dict) -> list[tuple[str, dict]]:
    """Все неверные варианты по порядку таблицы, ещё без сведения повторов."""
    fact = question['fact']
    rows = _rows(dossier, fact['table'])
    if 'options' in fact:
        return [(ref['row'], rows[ref['row']][ref['column']])
                for ref in fact['options'] if ref != fact['answer']]
    excluded = set(question.get('exclude', []))
    where = fact.get('where', {})
    return [(row_id, row[fact['ask']]) for row_id, row in rows.items()
            if row_id != fact['row'] and row_id not in excluded and fact['ask'] in row
            and all(column in row and row[column]['zh'] == value for column, value in where.items())]


def question_options(question: dict, dossier: dict) -> tuple[list[dict], str]:
    answer_id, answer = answer_cell(question, dossier)
    options = [{'id': answer_id, 'zh': answer['zh'].strip()}]
    seen = {options[0]['zh']}
    for row_id, cell in _candidates(question, dossier):
        text = cell['zh'].strip()
        if text in seen:
            continue
        seen.add(text)
        option = {'id': row_id, 'zh': text}
        if cell.get('gloss'):
            option['gloss'] = cell['gloss'].strip()
        options.append(option)
    return options, answer_id


def dossier_records(dossier: dict, questions: list[dict]) -> list[dict]:
    rows = {row['id']: row for table in dossier['tables'].values() for row in table['rows']}
    records = []
    for question in questions:
        if question['status'] != 'accepted':
            continue
        options, answer_id = question_options(question, dossier)
        records.append({
            'id': question['id'],
            'origin': 'addition',
            'dossier': dossier['id'],
            'topic': question['topic'],
            'topicSource': 'authored',
            'questionRu': question['questionRu'],
            'questionZh': None,
            'options': options,
            'answer': {'optionId': answer_id, 'state': 'verified'},
            'explanation': {'ru': question['explanation'].strip()},
            'evidence': [{key: item[key] for key in EVIDENCE_FIELDS} for item in rows[answer_id]['sources']],
            'occurrences': [],
            'parseWarnings': [],
        })
    return records
```

- [ ] **Step 4: Запустить тесты**

Run: `python3 -m unittest test.test_dossiers -v`
Expected: PASS (все тесты задач 1–2).

- [ ] **Step 5: Commit**

```bash
git add scripts/dossiers.py test/test_dossiers.py
git commit -m "Досье: варианты из колонки и записи банка"
```

---

### Task 3: Проверка вопросов досье

**Files:**
- Modify: `scripts/dossiers.py`
- Modify: `test/test_dossiers.py`

**Interfaces:**
- Consumes: `answer_cell`, `_candidates`, `question_options` (задача 2); `TOPICS` из `scripts/taxonomy.py`; `loads_unique(text, what)` из `scripts/strict_json.py`; `sentence_count(text) -> int` из `scripts/authored.py`.
- Produces:
  - `validate_questions(questions: object, dossier: dict) -> list[str]` — досье уже проверено;
  - `load_dossier(dossier_path: Path, questions_path: Path) -> tuple[dict, list[dict]]` — читает, проверяет оба файла, при ошибках `ValueError` с именем файла.

- [ ] **Step 1: Написать падающие тесты**

Добавить в `test/test_dossiers.py` (импорт: `load_dossier, validate_questions`; `import tempfile`):

```python
class ValidateQuestionsTest(unittest.TestCase):
    def errors(self, questions, data=None):
        return validate_questions(questions, data or dossier())

    def assertRejects(self, questions, fragment, data=None):
        errors = self.errors(questions, data)
        self.assertTrue(any(fragment in error for error in errors), f'{fragment!r} not in {errors}')

    def test_accepts_a_valid_question(self):
        self.assertEqual(self.errors([question()]), [])

    def test_draft_without_check_is_valid(self):
        draft = question(status='draft')
        draft.pop('check')
        self.assertEqual(self.errors([draft]), [])

    def test_rejects_broken_references(self):
        fact = question()['fact']
        cases = [
            ({**fact, 'table': 'coins'}, 'нет таблицы'),
            ({**fact, 'row': 'cny-3'}, "нет строки 'cny-3'"),
            ({**fact, 'ask': 'series'}, 'не может быть вариантом'),
            ({**fact, 'row': 'rub-500', 'where': {'currency': '卢布'}}, 'нет ячейки flower'),
            ({**fact, 'where': {'series': 'x'}}, 'where'),
            ({**fact, 'where': {'currency': '卢布'}}, 'не проходит where'),
            ({**fact, 'answer': {'row': 'cny-20', 'column': 'flower'}}, 'answer бывает только'),
            ({**fact, 'given': 'flower'}, 'given совпадает с ask'),
            ({**fact, 'colour': 1}, 'неизвестные поля fact'),
        ]
        for broken, fragment in cases:
            with self.subTest(fragment=fragment):
                self.assertRejects([question(fact=broken)], fragment)

    def test_draft_with_broken_reference_still_stops_the_build(self):
        broken = question(status='draft', fact={**question()['fact'], 'row': 'cny-3'})
        self.assertRejects([broken], "нет строки 'cny-3'")

    def test_rejects_bad_exclude(self):
        self.assertRejects([question(exclude=['cny-3'])], 'exclude')
        self.assertRejects([question(exclude=['cny-20'])], 'exclude убирает строку ответа')

    def test_rejects_a_pool_that_is_too_small(self):
        fact = {'table': 'banknotes', 'row': 'rub-500', 'ask': 'back', 'where': {'currency': '卢布'}}
        self.assertRejects([question(fact=fact, questionRu='Что изображено на обороте купюры 500 рублей образца 1997 года?')],
                           'меньше 3 неверных')

    def test_rejects_a_twin_of_the_right_answer(self):
        data = dossier()
        row(data, 'cny-50')['flower'] = cell('荷花', ['лотос'], gloss='Лотос — второй')
        self.assertRejects([question()], 'совпадает с правильным', data)

    def test_rejects_a_wrong_option_without_gloss(self):
        data = dossier()
        row(data, 'cny-50')['flower'].pop('gloss')
        self.assertRejects([question()], 'нет подписи', data)

    def test_rejects_a_question_that_names_its_own_answer(self):
        self.assertRejects([question(questionRu='Какой цветок, 荷花, изображён на купюре 20 юаней 2019 года?')],
                           'называет свой ответ')
        # русское название ловится без учёта регистра
        self.assertRejects([question(questionRu='Лотос ли изображён на купюре 20 юаней выпуска 2019 года?')],
                           'называет свой ответ')

    def test_given_value_must_be_named_in_the_question(self):
        fact = {'table': 'banknotes', 'row': 'cny-50', 'ask': 'denomination', 'given': 'flower',
                'where': {'currency': '人民币'}}
        named = question(fact=fact, questionRu='На купюре какого номинала выпуска 2019 года изображён цветок 菊花?')
        self.assertEqual(self.errors([named]), [])
        self.assertRejects([question(fact=fact, questionRu='На купюре какого номинала 2019 года изображён этот цветок?')],
                           'не называет значение given')

    def test_dated_table_needs_a_year_or_series_in_the_question(self):
        self.assertRejects([question(questionRu='Какой цветок изображён на лицевой стороне купюры 20 юаней?')],
                           'год или серию')
        series = question(questionRu='Какой цветок изображён на купюре 20 юаней пятой серии?')
        self.assertEqual(self.errors([series]), [])

    def test_rejects_a_leak_between_questions(self):
        reverse = question(id='money-q02', fact={'table': 'banknotes', 'row': 'cny-20', 'ask': 'denomination',
                                                 'given': 'flower', 'where': {'currency': '人民币'}},
                           questionRu='На купюре какого номинала выпуска 2019 года изображён цветок 荷花?')
        self.assertRejects([question(), reverse], 'money-q02: текст называет ответ вопроса money-q01')

    def test_rejects_bad_status_check_id_topic_and_fields(self):
        cases = [
            ([question(status='done')], 'status'),
            ([{k: v for k, v in question().items() if k != 'check'}], 'вердикта проверки accept'),
            ([question(check={'verdict': 'fix', 'note': 'неточно'})], 'вердикта проверки accept'),
            ([question(check={'verdict': 'maybe', 'note': ''})], 'verdict'),
            ([question(id='q1')], 'id'),
            ([question(), question()], 'повторяющийся id'),
            ([question(topic='Деньги')], 'тема'),
            ([question(colour=1)], 'неизвестные поля вопроса'),
            ([question(explanation=' ')], 'нет пояснения'),
            ([question(explanation='Одно предложение.')], '3–5 предложений'),
            ('не список', 'списком'),
        ]
        for questions, fragment in cases:
            with self.subTest(fragment=fragment):
                self.assertRejects(questions, fragment)

    def test_rejects_broken_explicit_options(self):
        refs = [{'row': r, 'column': 'back'} for r in ('cny-100', 'cny-50', 'cny-20', 'rub-500')]
        answer = {'row': 'rub-500', 'column': 'back'}
        text = 'Что изображено на обороте купюры 500 рублей образца 1997 года?'
        explicit = lambda **fact: question(fact={'table': 'banknotes', 'options': refs, 'answer': answer, **fact},
                                           questionRu=text)
        self.assertEqual(self.errors([explicit()]), [])
        self.assertRejects([explicit(options=refs[:3])], 'не меньше четырёх')
        self.assertRejects([explicit(options=refs[:3] + [{'row': 'cny-100', 'column': 'flower'}])],
                           'не больше одного варианта')
        self.assertRejects([explicit(answer={'row': 'cny-5', 'column': 'back'})], 'answer — не один из вариантов')
        self.assertRejects([explicit(row='cny-20')], 'не использует')


class LoadDossierTest(unittest.TestCase):
    def write(self, directory, name, text):
        path = Path(directory) / name
        path.write_text(text, encoding='utf-8')
        return path

    def test_loads_a_valid_dossier(self):
        with tempfile.TemporaryDirectory() as directory:
            table = self.write(directory, 'money.json', json.dumps(dossier(), ensure_ascii=False))
            questions = self.write(directory, 'money-questions.json', json.dumps([question()], ensure_ascii=False))
            data, loaded = load_dossier(table, questions)
            self.assertEqual((data['id'], [q['id'] for q in loaded]), ('money', ['money-q01']))

    def test_errors_name_the_file(self):
        with tempfile.TemporaryDirectory() as directory:
            broken = dossier()
            broken.pop('title')
            table = self.write(directory, 'money.json', json.dumps(broken, ensure_ascii=False))
            questions = self.write(directory, 'money-questions.json', '[]')
            with self.assertRaisesRegex(ValueError, 'money.json'):
                load_dossier(table, questions)
            table = self.write(directory, 'money.json', json.dumps(dossier(), ensure_ascii=False))
            questions = self.write(directory, 'money-questions.json', '"x"')
            with self.assertRaisesRegex(ValueError, 'money-questions.json'):
                load_dossier(table, questions)

    def test_repeated_key_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            table = self.write(directory, 'money.json', '{"id": "money", "id": "cash"}')
            questions = self.write(directory, 'money-questions.json', '[]')
            with self.assertRaisesRegex(ValueError, 'повторяются ключи'):
                load_dossier(table, questions)
```

- [ ] **Step 2: Запустить и убедиться, что падает**

Run: `python3 -m unittest test.test_dossiers -v`
Expected: FAIL — `ImportError: cannot import name 'load_dossier'`.

- [ ] **Step 3: Написать проверку вопросов**

Добавить в `scripts/dossiers.py` (в импорты: `from pathlib import Path`, `from strict_json import loads_unique`, `from taxonomy import TOPICS`; импорт из `authored` расширить до `from authored import evidence_errors, sentence_count`):

```python
QUESTION_FIELDS = {'id', 'status', 'topic', 'fact', 'questionRu', 'explanation', 'exclude', 'check'}
FACT_FIELDS = {'table', 'row', 'ask', 'given', 'where', 'options', 'answer'}
STATUSES = {'draft', 'accepted'}
VERDICTS = {'accept', 'fix', 'drop'}
MIN_WRONG = 3
MIN_EXPLICIT = 4
DATED = re.compile(r'\d{4}|сери', re.IGNORECASE)


def _mentions(text: str, cell: dict) -> list[str]:
    lowered = text.lower()
    return [name for name in [cell['zh'], *cell.get('ru', [])] if name.strip() and name.lower() in lowered]


def _reference_errors(where: str, question: dict, dossier: dict) -> list[str]:
    fact = question.get('fact')
    if not isinstance(fact, dict):
        return [f'{where}: нет fact']
    errors: list[str] = []
    unknown = set(fact) - FACT_FIELDS
    if unknown:
        errors.append(f'{where}: неизвестные поля fact {sorted(unknown)}')
    table = dossier['tables'].get(fact.get('table'))
    if table is None:
        return errors + [f'{where}: нет таблицы {fact.get("table")!r}']
    columns = table['columns']
    rows = {row['id']: row for row in table['rows']}

    def cell_ref(label: str, row_id: object, column: object) -> list[str]:
        if row_id not in rows:
            return [f'{where}: {label} — нет строки {row_id!r}']
        if columns.get(column) != 'zh':
            return [f'{where}: {label} — колонка {column!r} не может быть вариантом']
        if column not in rows[row_id]:
            return [f'{where}: {label} — у строки {row_id} нет ячейки {column}']
        return []

    if 'options' in fact:
        extra = ({'row', 'ask', 'given', 'where'} & set(fact)) | ({'exclude'} if question.get('exclude') else set())
        if extra:
            errors.append(f'{where}: вопрос с явными вариантами не использует {sorted(extra)}')
        refs = fact['options']
        if (not isinstance(refs, list) or len(refs) < MIN_EXPLICIT
                or not all(isinstance(ref, dict) and set(ref) == {'row', 'column'} for ref in refs)):
            return errors + [f'{where}: options — не меньше четырёх ссылок {{row, column}}']
        for index, ref in enumerate(refs, start=1):
            errors += cell_ref(f'вариант {index}', ref['row'], ref['column'])
        if len({ref['row'] for ref in refs}) != len(refs):
            errors.append(f'{where}: одна строка — не больше одного варианта')
        if fact.get('answer') not in refs:
            errors.append(f'{where}: answer — не один из вариантов')
        return errors

    errors += cell_ref('ask', fact.get('row'), fact.get('ask'))
    if 'answer' in fact:
        errors.append(f'{where}: answer бывает только у вопроса с явными вариантами')
    if 'given' in fact:
        if fact['given'] == fact.get('ask'):
            errors.append(f'{where}: given совпадает с ask')
        else:
            errors += cell_ref('given', fact.get('row'), fact['given'])
    condition = fact.get('where', {})
    if not isinstance(condition, dict) or any(columns.get(column) != 'zh' for column in condition):
        errors.append(f'{where}: where — равенство по колонкам рода zh')
    elif fact.get('row') in rows:
        answer_row = rows[fact['row']]
        if not all(column in answer_row and answer_row[column]['zh'] == value for column, value in condition.items()):
            errors.append(f'{where}: строка ответа не проходит where')
    exclude = question.get('exclude', [])
    if not isinstance(exclude, list) or any(row_id not in rows for row_id in exclude):
        errors.append(f'{where}: exclude называет строку не из этой таблицы')
    elif fact.get('row') in exclude:
        errors.append(f'{where}: exclude убирает строку ответа')
    return errors


def _content_errors(where: str, question: dict, dossier: dict) -> list[str]:
    """Проверки, которым нужны целые ссылки: набор вариантов и текст вопроса."""
    errors: list[str] = []
    fact = question['fact']
    _, answer = answer_cell(question, dossier)
    twins = [row_id for row_id, cell in _candidates(question, dossier) if cell['zh'].strip() == answer['zh'].strip()]
    if twins:
        errors.append(f'{where}: неверный вариант совпадает с правильным: {twins}')
    options, _ = question_options(question, dossier)
    if len(options) - 1 < MIN_WRONG:
        errors.append(f'{where}: в наборе меньше {MIN_WRONG} неверных вариантов')
    unglossed = [option['id'] for option in options[1:] if 'gloss' not in option]
    if unglossed:
        errors.append(f'{where}: у неверных вариантов нет подписи: {unglossed}')
    text = question['questionRu']
    hints = _mentions(text, answer)
    if hints:
        errors.append(f'{where}: вопрос называет свой ответ: {hints}')
    if 'given' in fact:
        given = _rows(dossier, fact['table'])[fact['row']][fact['given']]
        if given['zh'] not in text:
            errors.append(f'{where}: вопрос не называет значение given {given["zh"]!r}')
    if dossier['tables'][fact['table']].get('datedQuestions') and not DATED.search(text):
        errors.append(f'{where}: вопрос не называет год или серию')
    return errors


def validate_questions(questions: object, dossier: dict) -> list[str]:
    if not isinstance(questions, list):
        return ['вопросы досье должны быть списком']
    errors: list[str] = []
    seen: set[str] = set()
    whole: list[dict] = []
    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            errors.append(f'вопрос {index} должен быть объектом')
            continue
        question_id = question.get('id')
        where = question_id if isinstance(question_id, str) else f'вопрос {index}'
        if not isinstance(question_id, str) or not re.fullmatch(rf'{re.escape(dossier["id"])}-q\d+', question_id):
            errors.append(f'{where}: id — «{dossier["id"]}-qNN»')
        elif question_id in seen:
            errors.append(f'{where}: повторяющийся id')
        seen.add(question_id)
        unknown = set(question) - QUESTION_FIELDS
        if unknown:
            errors.append(f'{where}: неизвестные поля вопроса {sorted(unknown)}')
        if question.get('status') not in STATUSES:
            errors.append(f'{where}: status — draft или accepted')
        if question.get('topic') not in TOPICS:
            errors.append(f'{where}: тема вне списка семи категорий')
        if not isinstance(question.get('questionRu'), str) or not question['questionRu'].strip():
            errors.append(f'{where}: нет текста вопроса')
        if not isinstance(question.get('explanation'), str) or not question['explanation'].strip():
            errors.append(f'{where}: нет пояснения')
        elif not 3 <= sentence_count(question['explanation']) <= 5:
            # то же правило, что у дополнений: сборка банка проверит его снова
            errors.append(f'{where}: пояснение должно состоять из 3–5 предложений')
        check = question.get('check')
        if check is not None and (not isinstance(check, dict) or check.get('verdict') not in VERDICTS
                                  or not isinstance(check.get('note', ''), str)):
            errors.append(f'{where}: check — {{verdict: accept | fix | drop, note}}')
        if question.get('status') == 'accepted' and (not isinstance(check, dict) or check.get('verdict') != 'accept'):
            errors.append(f'{where}: принятый вопрос без вердикта проверки accept')
        broken = _reference_errors(where, question, dossier)
        errors += broken
        if not broken and isinstance(question.get('questionRu'), str):
            errors += _content_errors(where, question, dossier)
            whole.append(question)
    # утечки: ответ одного вопроса не должен стоять в тексте другого
    answers = {question['id']: answer_cell(question, dossier)[1] for question in whole}
    for question in whole:
        for other_id, answer in answers.items():
            if other_id == question['id']:
                continue
            names = _mentions(question['questionRu'], answer)
            if names:
                errors.append(f'{question["id"]}: текст называет ответ вопроса {other_id}: {names}')
    return errors


def load_dossier(dossier_path: Path, questions_path: Path) -> tuple[dict, list[dict]]:
    dossier = loads_unique(dossier_path.read_text('utf-8'), 'досье')
    errors = validate_dossier(dossier)
    if errors:
        raise ValueError(f'некорректное досье {dossier_path.name}:\n - ' + '\n - '.join(errors))
    questions = loads_unique(questions_path.read_text('utf-8'), 'вопросах досье')
    errors = validate_questions(questions, dossier)
    if errors:
        raise ValueError(f'некорректные вопросы {questions_path.name}:\n - ' + '\n - '.join(errors))
    return dossier, questions
```

- [ ] **Step 4: Запустить тесты**

Run: `python3 -m unittest test.test_dossiers -v`
Expected: PASS. Если тест утечки ловит и обратное направление (`money-q01 … money-q02`), проверить: ответ `money-q02` — `20 元` без русских названий, в тексте `money-q01` его нет; падение значит, что `_mentions` сравнивает не те тексты.

- [ ] **Step 5: Commit**

```bash
git add scripts/dossiers.py test/test_dossiers.py
git commit -m "Досье: проверка вопросов, подсказок и утечек"
```

---

### Task 4: Досье в сборке банка

**Files:**
- Modify: `scripts/authored.py:76-84` (правило «ровно четыре варианта»)
- Modify: `scripts/dossiers.py` (`dossier_paths`, `main`)
- Modify: `scripts/merge_bank.py:15-21, 373-374`
- Modify: `test/test_authored.py`, `test/test_dossiers.py`, `test/test_glosses.py:115-123`
- Create: `data/dossiers/money.json`, `data/dossiers/money-questions.json`
- Modify: `CLAUDE.md`, `README.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `load_dossier`, `dossier_records`, `question_options` (задачи 2–3).
- Produces: `dossier_paths(directory: Path) -> list[tuple[Path, Path]]` — пары (таблица, вопросы) по файлам `*-questions.json`; `python3 scripts/dossiers.py` — проверка всех досье без записи файлов (ей пользуются агенты в задачах 6–9).

- [ ] **Step 1: Написать падающие тесты**

В `test/test_authored.py` добавить в класс с тестами `validate_authored` (рядом с проверкой четырёх вариантов):

```python
    def test_dossier_record_may_carry_a_pool_of_options(self):
        record = addition(dossier='money', options=[
            {'id': 'cny-100', 'zh': '北京'}, {'id': 'cny-50', 'zh': '上海'}, {'id': 'cny-20', 'zh': '广州'},
            {'id': 'cny-10', 'zh': '西安'}, {'id': 'cny-5', 'zh': '成都'}],
            answer={'optionId': 'cny-100', 'state': 'verified'})
        self.assertEqual(validate_authored([record], [olympiad_record()]), [])

    def test_dossier_record_still_needs_four_options_with_unique_ids(self):
        three = addition(dossier='money', options=addition()['options'][:3])
        self.assertTrue(any('не меньше четырёх' in e for e in validate_authored([three], [olympiad_record()])))
        twins = addition(dossier='money', options=[*addition()['options'], {'id': 'o1', 'zh': '成都'}])
        self.assertTrue(any('уникальные id' in e for e in validate_authored([twins], [olympiad_record()])))
```

В `test/test_dossiers.py` добавить (импорт: `dossier_paths`; `from editorial import apply_editorial, validate_editorial`):

```python
class DossierPathsTest(unittest.TestCase):
    def test_pairs_each_questions_file_with_its_table(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            for name in ('money.json', 'money-questions.json', 'notes.md'):
                (base / name).write_text('[]', encoding='utf-8')
            self.assertEqual(dossier_paths(base), [(base / 'money.json', base / 'money-questions.json')])

    def test_questions_without_a_table_are_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'money-questions.json').write_text('[]', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'money.json'):
                dossier_paths(Path(directory))


class EditorialOnDossierRecordTest(unittest.TestCase):
    def test_option_is_addressed_by_its_row_id(self):
        [record] = dossier_records(dossier(), [question()])
        edits = {'money-q01': {'reason': 'опечатка', 'options': {'cny-50': '菊'}}}
        self.assertEqual(validate_editorial(edits, [record]), [])
        [edited] = apply_editorial([record], edits)
        self.assertEqual(next(o['zh'] for o in edited['options'] if o['id'] == 'cny-50'), '菊')


class DossierInBankTest(unittest.TestCase):
    """Каждый принятый вопрос досье доходит до data/bank.json, черновики — нет."""

    def setUp(self):
        self.bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        self.pairs = dossier_paths(ROOT / 'data/dossiers')

    def test_money_dossier_is_part_of_the_build(self):
        self.assertIn((ROOT / 'data/dossiers/money.json', ROOT / 'data/dossiers/money-questions.json'), self.pairs)

    def test_accepted_questions_reach_the_bank_and_drafts_do_not(self):
        for table_path, questions_path in self.pairs:
            data, questions = load_dossier(table_path, questions_path)
            for item in questions:
                if item['status'] != 'accepted':
                    self.assertNotIn(item['id'], self.bank)
                    continue
                record = self.bank[item['id']]
                options, answer_id = question_options(item, data)
                self.assertEqual(record['answer']['optionId'], answer_id, item['id'])
                self.assertEqual([o['id'] for o in record['options']], [o['id'] for o in options], item['id'])
                self.assertTrue(all(o.get('gloss') for o in record['options'] if o['id'] != answer_id), item['id'])

    def test_olympiad_links_point_to_bank_questions(self):
        # олимпиадный вопрос мог быть влит склейкой в другой — его id тогда в mergedIds
        known = set(self.bank) | {i for r in self.bank.values() for i in r.get('mergedIds', [])}
        for table_path, questions_path in self.pairs:
            data, _ = load_dossier(table_path, questions_path)
            for table in data['tables'].values():
                for item in table['rows']:
                    for olympiad_id in item.get('olympiad', []):
                        self.assertIn(olympiad_id, known, item['id'])
```

- [ ] **Step 2: Запустить и убедиться, что падают**

Run: `python3 -m unittest test.test_authored test.test_dossiers -v`
Expected: FAIL — `ImportError: cannot import name 'dossier_paths'` и тесты `test_authored` о пятом варианте («нужно ровно четыре варианта»).

- [ ] **Step 3: Ослабить правило четырёх вариантов для записей досье**

В `scripts/authored.py` заменить блок проверки вариантов (сейчас строки 76–84):

```python
        options = record.get('options')
        # у вопроса досье неверные варианты — общий набор из таблицы, их может быть больше трёх
        pooled = 'dossier' in record
        if not isinstance(options, list) or (len(options) < 4 if pooled else len(options) != 4):
            errors.append(f'{where}: нужно не меньше четырёх вариантов' if pooled
                          else f'{where}: нужно ровно четыре варианта')
            option_ids: set[str] = set()
            option_texts: list[str] = []
        else:
            option_ids = {option.get('id') for option in options if isinstance(option, dict)}
            option_texts = [option.get('zh', '') if isinstance(option, dict) else '' for option in options]
            if len(option_ids) != len(options) or any(not isinstance(option_id, str) or not option_id
                                                      for option_id in option_ids):
                errors.append(f'{where}: варианты должны иметь уникальные id')
```

(дальше — без изменений: `language_errors`, `completeness_errors`).

- [ ] **Step 4: Добавить `dossier_paths` и проверку из командной строки**

В конец `scripts/dossiers.py`:

```python
QUESTIONS_SUFFIX = '-questions.json'


def dossier_paths(directory: Path) -> list[tuple[Path, Path]]:
    pairs = []
    for questions_path in sorted(directory.glob(f'*{QUESTIONS_SUFFIX}')):
        table_path = questions_path.with_name(questions_path.name.removesuffix(QUESTIONS_SUFFIX) + '.json')
        if not table_path.exists():
            raise ValueError(f'{questions_path.name}: нет таблицы досье {table_path.name}')
        pairs.append((table_path, questions_path))
    return pairs


def main() -> None:
    """Проверка всех досье без сборки банка: её запускают агенты, пока пишут досье."""
    root = Path(__file__).resolve().parents[1]
    for table_path, questions_path in dossier_paths(root / 'data/dossiers'):
        data, questions = load_dossier(table_path, questions_path)
        accepted = sum(1 for question in questions if question['status'] == 'accepted')
        rows = sum(len(table['rows']) for table in data['tables'].values())
        print(f'{data["id"]}: строк {rows}, вопросов {len(questions)}, принято {accepted} — ошибок нет')


if __name__ == '__main__':
    main()
```

- [ ] **Step 5: Создать файлы досье «Деньги» без строк**

`data/dossiers/money.json`:

```json
{
  "id": "money",
  "title": "Деньги",
  "tables": {
    "banknotes": {
      "columns": {
        "currency": "zh",
        "denomination": "zh",
        "series": "ru",
        "front": "zh",
        "back": "zh",
        "flower": "zh",
        "city": "zh"
      },
      "required": ["series"],
      "datedQuestions": true,
      "rows": []
    },
    "history": {
      "columns": {
        "name": "zh",
        "era": "zh",
        "meaning": "ru"
      },
      "rows": []
    },
    "customs": {
      "columns": {
        "name": "zh",
        "occasion": "zh",
        "meaning": "ru"
      },
      "rows": []
    }
  }
}
```

`data/dossiers/money-questions.json`:

```json
[]
```

- [ ] **Step 6: Подключить досье к сборке**

В `scripts/merge_bank.py` добавить импорт рядом с остальными:

```python
from dossiers import dossier_paths, dossier_records, load_dossier
```

и сразу после строки `bank.extend(load_authored(ROOT / 'data/authored/questions.json', bank))`:

```python
    # досье — сразу после дополнений: правки, склейки и подписи дальше работают и для них
    for table_path, questions_path in dossier_paths(ROOT / 'data/dossiers'):
        dossier, questions = load_dossier(table_path, questions_path)
        bank.extend(dossier_records(dossier, questions))
```

- [ ] **Step 7: Подписи досье — не из glosses.json**

В `test/test_glosses.py`, `test_every_gloss_reaches_the_bank`, заменить построение `actual`:

```python
        # в обе стороны: и каждая подпись дошла, и лишних подписей в банке нет;
        # у вопросов досье подписи из ячеек таблицы (data/dossiers/), а не из glosses.json
        actual = {(record['id'], option['id']): option['gloss']
                  for record in bank.values() if 'dossier' not in record
                  for option in record['options'] if 'gloss' in option}
```

- [ ] **Step 8: Собрать и прогнать все тесты**

Run: `npm run build && python3 scripts/dossiers.py && python3 -m unittest discover -s test -t . && node --test test/*.test.mjs`
Expected: сборка проходит (404 записи, банк не изменился: в досье ни одного вопроса), `money: строк 0, вопросов 0, принято 0 — ошибок нет`, все тесты зелёные. `git diff --stat data/bank.json dist/` — пусто.

- [ ] **Step 9: Документация**

`CLAUDE.md` — после пункта о `glosses.json` добавить:

```markdown
- Досье — таблица проверенных фактов (`data/dossiers/<id>.json`) и вопросы по её ячейкам
  (`data/dossiers/<id>-questions.json`), спецификация —
  `docs/superpowers/specs/2026-10-14-dossier-money-pilot-design.md`. Варианты вопроса досье не
  пишутся руками: правильный — ячейка, неверные — та же колонка соседних строк (общий набор),
  подписи — из ячеек таблицы, а не из `glosses.json`. У строки — не меньше двух официальных или
  академических источников с цитатой. В банк идут только вопросы со `status: "accepted"`,
  принятые автором после проверки отдельным агентом. id вопроса (`<id досье>-qNN`) и id
  варианта (id строки) не менять: на них держится прогресс учеников. Проверка без сборки:
  `python3 scripts/dossiers.py`.
```

`README.md` — в описании порядка слоёв сборки добавить шаг «досье (`data/dossiers/`, только принятые вопросы)» сразу после дополнений `data/authored/`. Найти место: `grep -n "authored" README.md`.

`CHANGELOG.md` — перед `## Не реализовано (сознательно или пока)`:

```markdown
## 2026-10-15 — Досье в сборке банка (код пилота)

- `scripts/dossiers.py`: проверка таблиц досье и вопросов по их ячейкам, сборка записей банка
  (варианты — колонка соседних строк, подписи — из ячеек), поиск подсказок и утечек между
  вопросами; `python3 scripts/dossiers.py` проверяет досье без сборки.
- Записи досье — дополнения (`origin: "addition"`, `dossier`), идут в банк сразу после
  `data/authored/`; проверка дополнений пропускает у них варианты сверх четырёх.
- Досье «Деньги» заведено пустым: три таблицы (банкноты, история денег, обычаи), вопросов нет.
```

- [ ] **Step 10: Commit**

```bash
git add scripts/authored.py scripts/dossiers.py scripts/merge_bank.py data/dossiers test CLAUDE.md README.md CHANGELOG.md
git commit -m "Досье в сборке банка: пустое досье «Деньги», правило вариантов для записей досье"
```

---

### Task 5: Отчёт досье для автора

**Files:**
- Modify: `scripts/dossiers.py`, `scripts/merge_bank.py`
- Modify: `test/test_dossiers.py`
- Create (сборкой): `data/review/dossier-money.md`

**Interfaces:**
- Consumes: `question_options`, `answer_cell` (задача 2); `dossier_paths`, `load_dossier` (задачи 3–4).
- Produces: `dossier_report(dossier: dict, questions: list[dict]) -> str` — markdown; сборка пишет его в `data/review/dossier-<id>.md`.

- [ ] **Step 1: Написать падающий тест**

Добавить в `test/test_dossiers.py` (импорт `dossier_report`):

```python
class DossierReportTest(unittest.TestCase):
    def test_report_lists_tables_and_every_question(self):
        draft = question(id='money-q02', status='draft', check={'verdict': 'fix', 'note': 'неточно'},
                         fact={'table': 'banknotes', 'row': 'cny-50', 'ask': 'back', 'where': {'currency': '人民币'}},
                         questionRu='Что изображено на обороте купюры 50 юаней выпуска 2019 года?')
        report = dossier_report(dossier(), [question(), draft])
        self.assertTrue(report.startswith('# Досье «Деньги»\n'))
        self.assertIn('## Таблица `banknotes` — строк: 6', report)
        self.assertIn('| cny-50 | 人民币 | 50 元 | пятая серия, выпуск 2019 года | 布达拉宫 | 菊花 |  |', report)
        self.assertIn('## Вопросы — принято 1 из 2', report)
        self.assertIn('### money-q02 · draft · проверка: fix', report)
        self.assertIn('- Ответ: 布达拉宫', report)
        self.assertIn('- Неверные: 人民大会堂, 桂林山水, 长江三峡, 泰山', report)
        self.assertIn('- Замечание проверки: неточно', report)
        self.assertTrue(report.endswith('\n') and not report.endswith('\n\n'))

    def test_question_without_check_says_so(self):
        draft = question(status='draft')
        draft.pop('check')
        self.assertIn('### money-q01 · draft · проверка: нет', dossier_report(dossier(), [draft]))
```

- [ ] **Step 2: Запустить и убедиться, что падает**

Run: `python3 -m unittest test.test_dossiers.DossierReportTest -v`
Expected: FAIL — `ImportError: cannot import name 'dossier_report'`.

- [ ] **Step 3: Написать отчёт**

Добавить в `scripts/dossiers.py` (перед `QUESTIONS_SUFFIX`):

```python
def _report_cell(value: object) -> str:
    if value is None:
        return ''
    text = value['zh'] if isinstance(value, dict) else str(value)
    return text.replace('|', '\\|')


def dossier_report(dossier: dict, questions: list[dict]) -> str:
    lines = [f'# Досье «{dossier["title"]}»', '',
             f'Файл пишет сборка (`scripts/dossiers.py`). Править — `data/dossiers/{dossier["id"]}.json` '
             f'и `data/dossiers/{dossier["id"]}-questions.json`.', '']
    for name, table in dossier['tables'].items():
        columns = list(table['columns'])
        lines += [f'## Таблица `{name}` — строк: {len(table["rows"])}', '']
        if table['rows']:
            lines.append('| id | ' + ' | '.join(columns) + ' | olympiad |')
            lines.append('|' + '---|' * (len(columns) + 2))
            for row in table['rows']:
                cells = ' | '.join(_report_cell(row.get(column)) for column in columns)
                lines.append(f'| {row["id"]} | {cells} | {", ".join(row.get("olympiad", []))} |')
            lines.append('')
    accepted = sum(1 for question in questions if question['status'] == 'accepted')
    lines += [f'## Вопросы — принято {accepted} из {len(questions)}', '']
    for question in questions:
        options, _ = question_options(question, dossier)
        check = question.get('check') or {}
        lines += [f'### {question["id"]} · {question["status"]} · проверка: {check.get("verdict", "нет")}', '',
                  question['questionRu'], '',
                  f'- Ответ: {options[0]["zh"]}',
                  '- Неверные: ' + ', '.join(option['zh'] for option in options[1:]),
                  f'- Тема: {question["topic"]}',
                  f'- Пояснение: {question["explanation"].strip()}']
        if check.get('note'):
            lines.append(f'- Замечание проверки: {check["note"]}')
        lines.append('')
    return '\n'.join(lines).rstrip('\n') + '\n'
```

- [ ] **Step 4: Сборка пишет отчёт**

В `scripts/merge_bank.py` импорт расширить: `from dossiers import dossier_paths, dossier_records, dossier_report, load_dossier`. Цикл досье из задачи 4 заменить на:

```python
    # досье — сразу после дополнений: правки, склейки и подписи дальше работают и для них
    dossier_reports: dict[str, str] = {}
    for table_path, questions_path in dossier_paths(ROOT / 'data/dossiers'):
        dossier, questions = load_dossier(table_path, questions_path)
        bank.extend(dossier_records(dossier, questions))
        dossier_reports[dossier['id']] = dossier_report(dossier, questions)
```

и после вызова `_write_report(report, bank)` (отчёты пишутся только вместе с банком):

```python
    for dossier_id, text in dossier_reports.items():
        (ROOT / f'data/review/dossier-{dossier_id}.md').write_text(text, encoding='utf-8')
```

- [ ] **Step 5: Собрать и прогнать тесты**

Run: `npm run build && python3 -m unittest discover -s test -t .`
Expected: PASS; появился `data/review/dossier-money.md` с тремя таблицами `— строк: 0` и `## Вопросы — принято 0 из 0`.

- [ ] **Step 6: Commit**

В `CHANGELOG.md` дописать к записи задачи 4 строку: «- Сборка пишет отчёт досье для автора `data/review/dossier-<id>.md`: таблицы и все вопросы с ответом, набором, статусом и вердиктом проверки.»

```bash
git add scripts/dossiers.py scripts/merge_bank.py test/test_dossiers.py data/review/dossier-money.md CHANGELOG.md
git commit -m "Досье: отчёт для автора"
```

После задачи 5 — ревью кода отдельным агентом (с согласия автора) до наполнения досье: дальше на этот код опираются агенты.

---

### Task 6: Этап 1 — факты (три агента-сборщика)

**Files:**
- Modify: `data/dossiers/money.json` (строки трёх таблиц)
- Рабочие файлы агентов — в scratchpad сессии, не в проекте.

**Interfaces:**
- Consumes: формат таблиц (задача 1), `python3 scripts/dossiers.py` (задача 4), банк для поля `olympiad`.
- Produces: `money.json` со строками: банкноты ≈ 20, история ≈ 10, обычаи ≈ 8.

- [ ] **Step 1: Спросить автора о запуске трёх агентов-сборщиков** (одновременно три — предел).

- [ ] **Step 2: Запустить сборщиков** — каждому его таблицу. Общее в задании каждого:
  - формат строки и ячейки — раздел «Формат данных» спецификации; писать в свой файл в scratchpad (`money-<table>.json` — список строк);
  - источники: не меньше двух независимых, `official` или `academic`, дословная `quote` (на языке страницы), `checkedAt` — дата проверки; Википедия только для ориентира, в `sources` её нет;
  - `ru` у ячейки — русские названия, по которым ответ узнаётся в тексте вопроса (Потала, лотос); у номиналов `ru` не заполнять: «20 юаней» в тексте вопроса — тема, а не подсказка;
  - `gloss` — у каждой ячейки рода `zh`, которая может стать вариантом: русское название и один факт о ней в её колонке («Хризантема — цветок на лицевой стороне купюры 50 юаней»), ≤ 90 знаков, без «почему не подходит»;
  - `olympiad` — найти в `data/bank.json` олимпиадные вопросы о том же факте (по ключевым словам), вписать их id;
  - в HTTP-запросах никаких личных данных, только обезличенный User-Agent; проект не менять.
  - **Банкноты:** юань пятой серии — 1, 5, 10, 20, 50, 100 юаней в действующих выпусках (2015–2020), колонки `front`, `back`, `flower` (точное место цветка на купюре — по Народному банку Китая); рубль — серия 1997 года (5–5000 в последней модификации), 200 и 2000 рублей 2017 года, обновлённые 100 (2022), 1000 и 5000 (2023) — `back`, `front`, `city`; у каждой строки `series`. Источники — pbc.gov.cn, cbr.ru.
  - **История:** 贝币, 刀币, 布币, 蚁鼻钱, 秦半两, 五铢钱, 开元通宝, 交子, 元宝, 银元 — `name`, `era` (по-китайски: 商, 战国, 秦, 汉, 唐, 北宋, 明清…), `meaning`. Источники — Национальный музей Китая, 中国钱币博物馆, Народный банк Китая, академические издания.
  - **Обычаи:** 红包, 压岁钱, 财神, 招财进宝, 摇钱树, 金元宝 (новогодний символ), 铜钱 как оберег, 发 и 8 — `name`, `occasion`, `meaning`; легенды — с пометкой «по преданию» в `meaning`. Источники — gov.cn, Министерство культуры и туризма, 中国非物质文化遗产网, музеи.

- [ ] **Step 3: Свести файлы агентов в `data/dossiers/money.json`** (скрипт в scratchpad: строки в порядке номиналов/эпох, `json.dumps(..., ensure_ascii=False, indent=2) + '\n'`) и проверить:

Run: `python3 scripts/dossiers.py`
Expected: `money: строк ≈38, вопросов 0, принято 0 — ошибок нет`. Ошибки формата исправить в своде (не трогая факты) или вернуть агенту.

- [ ] **Step 4: Commit**

```bash
git add data/dossiers/money.json
git commit -m "Досье «Деньги»: таблицы фактов (черновик до сверки)"
```

---

### Task 7: Этап 2 — сверка фактов

**Files:**
- Modify: `data/dossiers/money.json`

- [ ] **Step 1: Спросить автора о запуске одного агента-сверщика.**

- [ ] **Step 2: Запустить сверщика** (таблиц не собирал). Задание: заново открыть каждый источник каждой строки, найти `quote` дословно; проверить каждый факт ячеек, серию и год, действует ли купюра; проверить подписи (верны, ≤ 90, не делают вариант вторым верным ответом в вопросе по колонке); вердикт на строку — `ok` / `fix` (с исправленной строкой) / `remove`, файл `verify.json` в scratchpad. Личных данных в запросах нет.

- [ ] **Step 3: Применить исправления** в `money.json`, затем:

Run: `python3 scripts/dossiers.py && npm run build && python3 -m unittest discover -s test -t .`
Expected: ошибок нет, тесты зелёные (в том числе `test_olympiad_links_point_to_bank_questions`).

- [ ] **Step 4: Commit** — в `CHANGELOG.md` строка о сверке (сколько строк исправлено, главное).

```bash
git add data/dossiers/money.json data/review/dossier-money.md CHANGELOG.md
git commit -m "Досье «Деньги»: таблицы сверены"
```

---

### Task 8: Этап 3 — вопросы (агент-писатель)

**Files:**
- Modify: `data/dossiers/money-questions.json`

- [ ] **Step 1: Спросить автора о запуске агента-писателя.**

- [ ] **Step 2: Запустить писателя.** Задание: по сверенной таблице написать 30–40 вопросов со `status: "draft"` в формате спецификации («Вопросы»), без `check`. Правила:
  - вопрос по-русски, ответ однозначен среди всего набора (если в колонке есть второй верный — `exclude` или `where`);
  - текст не называет ответ (ни по-китайски, ни по-русски) и не подсказывает его;
  - колонки — с разных сторон (`given`), но одну ячейку в обе стороны не спрашивать; обратный вопрос — по другой строке;
  - не повторять факты из `olympiad` в том же направлении;
  - у банкнот — год или серия в тексте; у легенд — «по преданию»;
  - пояснение — 3–5 предложений только о правильном ответе;
  - тема — одна из семи (`scripts/taxonomy.py`);
  - после записи запускать `python3 scripts/dossiers.py` и чинить, пока ошибок нет.
  Писатель меняет только `money-questions.json` (в scratchpad-копии; свожу я).

- [ ] **Step 3: Положить вопросы в проект и проверить**

Run: `python3 scripts/dossiers.py && npm run build`
Expected: ошибок нет; в банке по-прежнему 404 записи (черновики не идут в банк); `data/review/dossier-money.md` со всеми вопросами.

- [ ] **Step 4: Commit**

```bash
git add data/dossiers/money-questions.json data/review/dossier-money.md
git commit -m "Досье «Деньги»: черновики вопросов"
```

---

### Task 9: Этап 4 — проверка вопросов (агент-проверяющий)

**Files:**
- Modify: `data/dossiers/money-questions.json`

- [ ] **Step 1: Спросить автора о запуске агента-проверяющего** (и повторного запуска писателя на правки).

- [ ] **Step 2: Запустить проверяющего** (вопросов не писал). Задание: каждый вопрос глазами ученика — по отчёту `data/review/dossier-money.md` и таблице: нет ли в наборе второго верного ответа; не выдаёт ли формулировка ответ; верно ли пояснение по источникам строки; хорош ли русский язык; не повторяет ли олимпиаду. Вердикт — `check: {verdict: accept | fix | drop, note}` в scratchpad-копии файла вопросов.

- [ ] **Step 3: Правки.** Вопросы `fix` — писателю (одна правка), затем проверяющему повторно. Не сошлись после одной правки — вопрос в список для автора с обеими позициями. `drop` — удалить вопрос, причину записать в список для автора.

- [ ] **Step 4: Проверить и закоммитить**

Run: `python3 scripts/dossiers.py && npm run build`
Expected: ошибок нет.

```bash
git add data/dossiers/money-questions.json data/review/dossier-money.md
git commit -m "Досье «Деньги»: вопросы проверены"
```

---

### Task 10: Этап 5 — решение автора, слияние

**Files:**
- Modify: `data/dossiers/money-questions.json`, `CHANGELOG.md`, `docs/ideas/2026-10-13-question-bank-ideas.md`

- [ ] **Step 1: Показать автору отчёт** `data/review/dossier-money.md`, список спорных и снятых вопросов. Ждать ответа по списку («всё да, кроме 7 и 12»).

- [ ] **Step 2: Применить решение.** Принятые — `status: "accepted"` (у спорных, решённых автором, `check: {verdict: "accept", note: "решение автора: …"}`); отклонённые — удалить, причина — в `CHANGELOG.md`.

- [ ] **Step 3: Собрать и прогнать всё**

Run: `npm run build && python3 -m unittest discover -s test -t . && node --test test/*.test.mjs`
Expected: банк = 404 + число принятых; все тесты зелёные (браузерный — не пропущен); `test_accepted_questions_reach_the_bank_and_drafts_do_not` проверил каждый принятый вопрос.

- [ ] **Step 4: Итог пилота.** `CHANGELOG.md` — запись: сколько строк и вопросов, сколько принято, что пришлось чинить в процессе. В `docs/ideas/2026-10-13-question-bank-ideas.md` — абзац «Итог пилота» (что сработало, что поправить до второго досье).

- [ ] **Step 5: Commit, ревью, слияние**

```bash
git add data/dossiers data/review/dossier-money.md data/bank.json dist CHANGELOG.md docs/ideas
git commit -m "Досье «Деньги»: принятые автором вопросы в банке"
```

Спросить автора, нужно ли ревью перед слиянием в master (одной строкой — что в ветке). После ответа: ревью отдельным агентом, исправления, повторный прогон проверок, fast-forward master, `git push origin master`. Перед слиянием удалить в основной папке проекта незакоммиченную копию `docs/ideas/2026-10-13-question-bank-ideas.md` (иначе git не обновит рабочую папку).
