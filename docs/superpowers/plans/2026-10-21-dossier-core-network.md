# Ядро досье и сеть связей — план работ

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Дать сборке инструменты для работы «ядро темы с разных сторон»: раунд разводит
вопросы об одной строке, проверка утечек их пропускает, в досье размечаются ядро и стороны,
сборка пишет отчёт о пробелах и граф для Obsidian. Затем — предложение каркаса провинций.

**Architecture:** У записи банка из досье (и у встроенной олимпиадной) появляется поле
`factRow` — `досье/таблица/строка` ответа. Раунд (`onePerFact`) берёт не больше одной записи и
по `factGroup`, и по `factRow`. Ядро — флаг строки `core`, стороны — список колонок таблицы
`sides`. Новый скрипт `scripts/network.py` после сборки пишет `data/review/network.md` и папку
заметок `data/review/graph/`.

**Tech Stack:** Python 3 (stdlib, `unittest`), Node 22 (`node --test`), JSON-данные.

**Spec:** `docs/superpowers/specs/2026-10-20-dossier-core-network-design.md`

## Global Constraints

- Тесты: `python3 -m unittest discover -s test -t .` и `node --test test/*.test.mjs` (паттерн без кавычек).
- `data/bank.json` — только сборкой (`npm run build`), руками никогда; `sources/` не трогать.
- id вопросов и вариантов не меняются; снятые id — в `data/review/removed.json`, повторно не выдаются.
- Правки готовых вопросов — только `data/review/editorial.json` (ключ — итоговый id, `reason`).
- Отчёт сборки `data/review/dossier-<id>.md` перезаписывается; ручные отчёты — `dossier-<id>-<что>.md`.
- Каждое заметное изменение — запись в `CHANGELOG.md` в том же коммите.
- Агенты — только с согласия автора на каждый запуск, не больше трёх одновременно; писатели и
  проверяющие — Opus, сборщики — Sonnet, механика — Haiku.
- Работа идёт в ветке `feat/dossier-core-network`; перед слиянием в `master` спросить автора,
  нужно ли ревью (правило автора).
- Тексты отчётов и сообщений об ошибках — по-русски, в стиле соседнего кода.

## Review Focus

1. Запись с `factGroup` и `factRow` сразу — раунд разводит по любому из двух ключей (тест в задаче 2).
2. Встроенная запись, пересобранная из `bank.json` (`original_record`), не тащит старый `factRow` (тест в задаче 1).
3. Досье без разметки ядра — отчёт не падает и пишет «каркас не утверждён» с базовыми цифрами (тест в задаче 5).
4. Ссылка ядра на строку вне ядра или в досье без каркаса — ссылка в заметке есть, отчёт её называет, ничего не падает (тест в задаче 5).
5. Строка перестала быть ядром — её заметка исчезает из `data/review/graph/` при следующей сборке (тест в задаче 5).

---

### Task 1: `factRow` у записей досье и встроенных записей

**Files:**
- Modify: `scripts/dossiers.py` (`_answer_place`, `dossier_records`, `original_record`, `embed_record`)
- Test: `test/test_dossiers.py`

**Interfaces:**
- Produces: `fact_place(question: dict, dossier: dict) -> tuple[str, str]` в `scripts/dossiers.py` —
  (`'<досье>/<таблица>/<строка ответа>'`, колонка ответа: `fact['answer']['column']` при `options`,
  иначе `fact['ask']`). `_answer_place` использует её для первых двух элементов.
- Produces: поле записи банка `factRow: str` (значение — первый элемент `fact_place`).

- [ ] **Step 1: Написать падающие тесты**

```python
# DossierRecordsTest
def test_record_carries_its_answer_row(self):
    [record] = dossier_records(dossier(), [question()])
    self.assertEqual(record['factRow'], 'money/banknotes/cny-20')

def test_explicit_options_question_takes_the_answer_row(self):
    # вопрос с fact.options: строка — из fact.answer, колонка — answer.column
    ...  # вопрос с options по четырём строкам, answer {'row': 'cny-50', 'column': 'back'}
    self.assertEqual(fact_place(q, dossier()), ('money/banknotes/cny-50', 'back'))

# ApplyEmbedsTest
def test_embedded_record_gets_the_row_of_its_question(self):
    [record] = [r for r in apply_embeds([olympiad()], [(dossier(), [embed()])], {}) if r['id'] == olympiad()['id']]
    self.assertEqual(record['factRow'], 'money/banknotes/<строка из embed()>')

def test_original_record_drops_fact_row(self):
    built = {**olympiad(), 'dossier': 'money', 'factRow': 'money/banknotes/cny-20'}
    self.assertNotIn('factRow', original_record(built))
```

- [ ] **Step 2: Запустить — тесты падают**

Run: `python3 -m unittest test.test_dossiers -v 2>&1 | tail -20`
Expected: FAIL — `KeyError: 'factRow'` / `ImportError: fact_place`.

- [ ] **Step 3: Реализовать**

`fact_place` в `scripts/dossiers.py`; `dossier_records` и `embed_record` кладут `'factRow'`;
`original_record` убирает ключи `{'dossier', 'factRow'}`. Докстринг `original_record` дополнить.

- [ ] **Step 4: Запустить — тесты проходят, весь Python-набор зелёный**

Run: `python3 -m unittest discover -s test -t .`
Expected: OK (тесты на реальном банке могут требовать пересборки — см. шаг 5).

- [ ] **Step 5: Пересобрать банк и проверить поле**

Run: `npm run build && python3 -c "import json;b=json.load(open('data/bank.json'));print(sum('factRow' in r for r in b))"`
Expected: число ≥ 743 (все принятые вопросы досье плюс встроенные олимпиадные).

- [ ] **Step 6: Commit** (с записью в `CHANGELOG.md`: «записи досье помнят строку ответа — `factRow`»)

```bash
git add scripts/dossiers.py test/test_dossiers.py data/ CHANGELOG.md
git commit -m "Записи досье помнят строку ответа (factRow)"
```

---

### Task 2: раунд разводит вопросы об одной строке

**Files:**
- Modify: `src/quiz.mjs:243-260` (`onePerFact` и комментарий над ним)
- Test: `test/quiz.test.mjs`

**Interfaces:**
- Consumes: поле `factRow` (задача 1).

- [ ] **Step 1: Написать падающие тесты** (рядом с тестами «один факт»)

```js
test('раунд берёт из вопросов об одной строке досье одну запись', () => {
  const bank = [record('a', { factRow: 'p/t/r1' }), record('b', { factRow: 'p/t/r1' }), record('c'), record('d')];
  for (const random of [() => 0, () => 0.5, () => 0.99]) {
    const round = buildRound(bank, NO_FILTERS, {}, 3, random);
    assert.equal(round.filter((r) => r.factRow === 'p/t/r1').length, 1);
  }
});

test('в раунде никакие две записи не делят ни строку досье, ни группу фактов', () => {
  // a и b — одна строка, b и c — одна группа; a и c вместе допустимы: общего факта у них нет
  const bank = [record('a', { factRow: 'p/t/r1' }), record('b', { factRow: 'p/t/r1', factGroup: 'g' }),
                record('c', { factGroup: 'g' }), record('d'), record('e')];
  const keys = (r) => [r.factRow && `r:${r.factRow}`, r.factGroup && `g:${r.factGroup}`].filter(Boolean);
  for (const random of [() => 0, () => 0.5, () => 0.99]) {
    const round = buildRound(bank, NO_FILTERS, {}, 3, random);
    const all = round.flatMap(keys);
    assert.equal(new Set(all).size, all.length, round.map((r) => r.id).join());
  }
});
```

- [ ] **Step 2: Запустить — падают**

Run: `node --test test/quiz.test.mjs`
Expected: FAIL в двух новых тестах.

- [ ] **Step 3: Реализовать** — `onePerFact` собирает ключи записи как
`['g:' + factGroup, 'r:' + factRow]` (только заданные); запись откладывается, если любой ключ
уже виден; у выбранной все ключи добавляются в `seen`. Комментарий над функцией дополнить
строкой досье.

- [ ] **Step 4: Запустить — проходят все JS-тесты**

Run: `node --test test/*.test.mjs`
Expected: все pass (ui.test пропускается без Chrome).

- [ ] **Step 5: Commit** (запись в `CHANGELOG.md`: «раунд не ставит рядом вопросы об одной строке досье — решение автора 21.10»)

```bash
git add src/quiz.mjs test/quiz.test.mjs CHANGELOG.md
git commit -m "Раунд разводит вопросы об одной строке досье"
```

---

### Task 3: вопросы об одной строке — не утечка

**Files:**
- Modify: `scripts/dossiers.py` (`validate_questions` — цикл утечек; `cross_leak_errors`; докстринги)
- Test: `test/test_dossiers.py`

**Interfaces:**
- Consumes: `_answer_place` (первый элемент — строка ответа).
- Produces: `_same_row(place: tuple, other_place: tuple) -> bool` — `place[0] == other_place[0]`.

- [ ] **Step 1: Переписать тест и добавить новые**

`test_rejects_a_leak_between_questions` сейчас ждёт утечку между двумя вопросами о строке
`cny-20` — по решению 21.10 это разные стороны одной строки. Переименовать в
`test_two_sides_of_one_row_are_not_a_leak` и ждать `[]`. Добавить:

```python
def test_rejects_a_leak_between_rows(self):
    # текст вопроса о cny-50 называет ответ вопроса о cny-20 (荷花) — утечка остаётся
    other = question(id='money-q02', fact={'table': 'banknotes', 'row': 'cny-50', 'ask': 'flower',
                                           'where': {'currency': '人民币'}},
                     questionRu='Какой цветок на купюре 50 юаней 2019 года, а не 荷花?')
    self.assertRejects([question(), other], 'money-q02: текст называет ответ вопроса money-q01')

# CrossLeakTest
def test_sides_of_one_row_across_files_are_not_a_leak(self):
    # встроенный олимпиадный вопрос и свой вопрос досье об одной строке
    ...  # embed() и question() с одной строкой ответа, текст олимпиадной записи называет ответ вопроса
    self.assertEqual(cross_leak_errors([record], loaded), [])
```

- [ ] **Step 2: Запустить — новые тесты падают**

Run: `python3 -m unittest test.test_dossiers -v 2>&1 | tail -20`
Expected: FAIL в `test_two_sides_of_one_row_are_not_a_leak` и кросс-тесте.

- [ ] **Step 3: Реализовать** — в обоих циклах пропускать пару при `_same_row(place, other_place)`
рядом с `_bridged` и `_same_group`. В докстринге `cross_leak_errors` — «решение автора
2026-10-21: стороны одной строки — не утечка, раунд разводит их по `factRow`».

- [ ] **Step 4: Запустить весь набор и проверку досье**

Run: `python3 -m unittest discover -s test -t . && python3 scripts/dossiers.py`
Expected: OK; проверка досье без ошибок.

- [ ] **Step 5: Commit** (запись в `CHANGELOG.md`; строка в `CLAUDE.md` о мостике — дополнить «стороны одной строки — не утечка»)

```bash
git add scripts/dossiers.py test/test_dossiers.py CHANGELOG.md CLAUDE.md
git commit -m "Стороны одной строки досье — не утечка"
```

---

### Task 4: разметка ядра и сторон в таблицах досье

**Files:**
- Modify: `scripts/dossiers.py` (`ROW_SERVICE_FIELDS`, `TABLE_FIELDS`, `_row_errors`, `validate_dossier`, `dossier_report`)
- Test: `test/test_dossiers.py` (`ValidateDossierTest`)

**Interfaces:**
- Produces: строка таблицы — необязательное `core: bool`; таблица — необязательное
  `sides: list[str]` (колонки этой таблицы вида `zh`, без повторов). Отсутствие — «каркас не
  утверждён».

- [ ] **Step 1: Написать падающие тесты**

```python
def test_core_and_sides_are_accepted(self):
    data = dossier(); data['tables']['banknotes']['sides'] = ['flower', 'back']
    row(data, 'cny-20')['core'] = True
    self.assertEqual(validate_dossier(data), [])

def test_rejects_bad_core_and_sides(self):
    for mutate, message in [
        (lambda d: row(d, 'cny-20').__setitem__('core', 'yes'), 'core — true или false'),
        (lambda d: d['tables']['banknotes'].__setitem__('sides', 'flower'), 'sides — список колонок zh'),
        (lambda d: d['tables']['banknotes'].__setitem__('sides', ['series']), 'sides — список колонок zh'),
        (lambda d: d['tables']['banknotes'].__setitem__('sides', ['nope']), 'sides — список колонок zh'),
        (lambda d: d['tables']['banknotes'].__setitem__('sides', ['flower', 'flower']), 'sides: колонки повторяются'),
    ]:
        ...  # копия dossier(), mutate, assert message in errors

def test_report_marks_core_rows(self):
    data = dossier(); row(data, 'cny-20')['core'] = True
    self.assertIn('| cny-20 ★ |', dossier_report(data, []))
```

(`series` в фикстуре — колонка `ru`, поэтому стороной быть не может.)

- [ ] **Step 2: Запустить — падают**

Run: `python3 -m unittest test.test_dossiers.ValidateDossierTest -v 2>&1 | tail -15`
Expected: FAIL.

- [ ] **Step 3: Реализовать** — `'core'` в `ROW_SERVICE_FIELDS`, `'sides'` в `TABLE_FIELDS`, проверки
с текстами из теста; в отчёте досье id строки ядра помечается ` ★`, а под заголовком таблицы с
`sides` — строка `Стороны: …`.

- [ ] **Step 4: Запустить весь набор**

Run: `python3 -m unittest discover -s test -t .`
Expected: OK.

- [ ] **Step 5: Commit** (запись в `CHANGELOG.md`)

```bash
git add scripts/dossiers.py test/test_dossiers.py CHANGELOG.md
git commit -m "Разметка ядра (core) и сторон (sides) в таблицах досье"
```

---

### Task 5: отчёт о пробелах и граф для Obsidian

**Files:**
- Create: `scripts/network.py`
- Create: `test/test_network.py`
- Modify: `package.json` (`build`: `python3 scripts/network.py` после `coverage_map.py`)
- Generated: `data/review/network.md`, `data/review/graph/*.md`

**Interfaces:**
- Consumes: `fact_place` (задача 1), `core`/`sides` (задача 4), `dossier_paths`, `load_removed` из `scripts/dossiers.py`; `strict_json.loads_unique`.
- Produces:
  - `network_report(loaded: list[tuple[dict, list[dict]]], bank: list[dict]) -> str`
  - `graph_notes(loaded: list[tuple[dict, list[dict]]], bank: list[dict]) -> dict[str, str]` — имя файла → текст
  - `write_graph(directory: Path, notes: dict[str, str]) -> None` — стирает `*.md` в папке и пишет заново
  - `main()` — читает `data/bank.json` и пары досье, пишет оба результата.

Счёт по вопросу досье: принятый вопрос (свой или `embeds`) — это пара `fact_place`. Вопросы
со статусом `draft` не считаются.

**Содержание `network.md`** (шапка: «Файл пишет сборка (`scripts/network.py`)»):

1. **Олимпиада по годам** — таблица: категория (7 тем) × учебный год, в ячейке — число
   появлений олимпиадных записей (`occurrences`); итог по строке. Ниже — то же по этапам.
2. **По досье**, для каждого:
   - без строк `core`: «каркас не утверждён» и базовые цифры — строк, принятых вопросов, строк
     с вопросом, строк с двумя и более сторонами, встроено олимпиадных;
   - с ядром — по каждой таблице, где есть `core`: матрица «строка ядра × сторона из `sides`»,
     в ячейке — число вопросов, пустая сторона — `—`; колонка «олимпиада» (`да`, если у строки
     непустой `olympiad`, иначе `прогноз`); список принятых вопросов о строках вне ядра (это
     кандидаты на перебор).
3. **Связи**: строки ядра без ссылок наружу и без ссылок на себя (`ref`/`from`) — «изолированные
   узлы»; ссылки из ядра на строку вне ядра или в досье без каркаса — «ведёт в тему без каркаса».

**Заметки графа** (только строки ядра и по заметке на досье):
- `<досье>.md` — `# <title>`, ссылки `[[<досье>.<строка>]]` на строки ядра.
- `<досье>.<строка>.md` — `# <zh имени> — <первое ru>`, `Тема: [[<досье>]]`, ссылки
  `[[<целевое досье>.<целевая строка>]]` из `ref`/`from` ячеек, вопросы по сторонам
  (`- <сторона>: <id> — <questionRu>`), олимпиадные id из `olympiad`.
- Ссылка на строку без заметки остаётся ссылкой: в Obsidian это «призрачный» узел — так видно
  тему без каркаса.

- [ ] **Step 1: Написать падающие тесты** в `test/test_network.py` на маленьких фикстурах
(две таблицы, одно досье с ядром, одно без):

```python
def test_dossier_without_core_says_so_with_baseline_numbers(self):
    report = network_report([(plain_dossier(), plain_questions())], bank=[])
    self.assertIn('каркас не утверждён', report)
    self.assertIn('строк с двумя и более сторонами: 1', report)

def test_core_matrix_counts_questions_per_side_and_marks_empty(self):
    report = network_report([(core_dossier(), core_questions())], bank=[])
    self.assertIn('| prov-sichuan | 2 | 1 | — | да |', report)   # abbr, capital, named, олимпиада
    self.assertIn('| prov-hainan | — | — | — | прогноз |', report)

def test_questions_outside_core_are_listed(self):
    self.assertIn('provinces-q09', network_report([(core_dossier(), core_questions())], bank=[]))

def test_link_to_a_topic_without_core_is_named_and_kept_in_notes(self):
    loaded = [(core_dossier(), core_questions()), (plain_dossier(), plain_questions())]
    self.assertIn('ведёт в тему без каркаса', network_report(loaded, bank=[]))
    notes = graph_notes(loaded, bank=[])
    self.assertIn('[[cuisine.sichuan-cuisine]]', notes['provinces.prov-sichuan.md'])
    self.assertNotIn('cuisine.sichuan-cuisine.md', notes)

def test_olympiad_by_year_counts_occurrences_per_category(self):
    bank = [olympiad_record('2019-20', 'школьный', 'География и административное устройство')] * 2
    # колонки — только годы, которые есть в банке, по порядку, и «Всего»
    report = network_report([], bank)
    self.assertIn('| Категория | 2019-20 | Всего |', report)
    self.assertIn('| География и административное устройство | 2 | 2 |', report)

def test_write_graph_removes_stale_notes(self):
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / 'old.md').write_text('x', 'utf-8')
        write_graph(Path(tmp), {'new.md': 'y'})
        self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ['new.md'])
```

- [ ] **Step 2: Запустить — падают**

Run: `python3 -m unittest test.test_network -v`
Expected: FAIL — `ModuleNotFoundError: network`.

- [ ] **Step 3: Реализовать `scripts/network.py`** по разделу выше; `write_graph` удаляет только
`*.md` (не трогает `.obsidian/`, если автор откроет папку как хранилище).

- [ ] **Step 4: Запустить тесты и сборку**

Run: `python3 -m unittest discover -s test -t . && npm run build && head -40 data/review/network.md && ls data/review/graph | head`
Expected: OK; в отчёте все 15 досье помечены «каркас не утверждён» (ядра ещё нет), папка `graph/`
содержит только 15 заметок досье.

- [ ] **Step 5: Commit** (запись в `CHANGELOG.md`: что пишет отчёт, где граф, как открыть в Obsidian — «Open folder as vault» на `data/review/graph`)

```bash
git add scripts/network.py test/test_network.py package.json data/review/network.md data/review/graph CHANGELOG.md
git commit -m "Отчёт о пробелах и граф ядра досье для Obsidian"
```

---

### Task 6: правила проекта под ядро

**Files:**
- Modify: `CLAUDE.md` (абзацы о досье)
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Заменить в `CLAUDE.md`** абзац «Новое досье и дособор готового — с запасом…»
и фразу «~70 % вопросов о Китае и 30 % о России» на правила из раздела спецификации «Что
меняется в правилах проекта»: каркас утверждает автор до сборки и вопросов; ядро — каркас плюс
2–4 самых известных примера на элемент (`core`), стороны — `sides`; каждый элемент ядра — с
нескольких сторон; порции — не больше 20–30 вопросов, автор смотрит каждый; доля 70/30 — по
банку в целом, Россия — своими темами; отчёт `data/review/network.md` и граф `data/review/graph/`.
Карта покрытия `coverage.md` остаётся рядом как счёт по ключевым словам; упоминание цели «1000»
в правилах убрать. Остальные правила досье не трогать.

- [ ] **Step 2: Проверить, что ничего не сломано**

Run: `python3 -m unittest discover -s test -t . && node --test test/*.test.mjs`
Expected: все зелёные.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md CHANGELOG.md
git commit -m "Правила досье: ядро темы вместо запаса (решение автора 20–21.10)"
```

Перед слиянием ветки в `master` — спросить автора, нужно ли ревью (одной строкой: что в ветке).

---

### Task 7: предложение каркаса провинций

Содержательная задача, без кода. Исполнитель — один агент-писатель (Opus) по согласию автора
или ведущий сессии сам.

**Files:**
- Create: `data/review/dossier-provinces-skeleton.md` (ручной отчёт — не `dossier-provinces.md`)

**Входные данные:** `data/dossiers/provinces.json` (34 единицы провинциального уровня, 49
городов: 25 китайских, 24 российских), `data/dossiers/provinces-questions.json` (86 принятых),
олимпиадные записи банка (`occurrences`: год, этап), книги Готлиба (глава
«Административно-территориальное деление Китая») и Волковой (раздел 1) из
`Яндекс.Диск/Китайский язык/02-Навыки/Страноведение/04-Книги и энциклопедии/Исправленные_md/`,
`data/review/network.md` из задачи 5.

- [ ] **Step 1: Собрать олимпиадные задания темы** — все олимпиадные записи о провинциях,
сокращениях, центрах, городах Китая: id, год, этап, что спрошено, встроено ли.
- [ ] **Step 2: Написать документ** с разделами: каркас (34 единицы — закрытый набор, по типам);
предлагаемые стороны (имеющиеся `abbr`, `capital`, `kind`, `named` и новые кандидаты — с
пометкой «нужен сбор»); примеры — какие китайские города входят в ядро и почему; связи с другими
темами (кухни, чаи, достопримечательности — как будущие ссылки); для каждого элемента —
олимпиадные задания и упоминание в книгах; кандидаты в прогноз; что из нынешних таблиц в ядро
не входит. Российские города не трогаются (решение 21.10).
- [ ] **Step 3: Отдать автору** — ссылка на документ и вопрос об утверждении. Дальше без
утверждённого каркаса ничего не делается.

После утверждения шаги 3–8 спецификации для провинций (разметка `core`/`sides`, перебор 86
вопросов, новые вопросы, проверка, порции автору) — отдельный короткий план: он зависит от
решений автора по каркасу.
