# Досье «Мифы и легенды» и «Космос» — план реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** встраивание олимпиадных вопросов в досье, ссылки между досье и проверка утечек между ними — и на этом коде два новых досье: «Мифы и легенды» и «Космос».

**Architecture:** вопрос досье с полем `embeds` не создаёт новую запись, а встраивается в существующую: новый модуль `scripts/embeds.py` (слой после `retired.json`) добавляет записи общий набор из таблицы и подписи. `scripts/dossiers.py` учится вопросам `embeds`, ссылкам ячеек `ref`/`from` (`validate_links`) и утечкам по всем досье сразу (`cross_leak_errors`, по окончательным текстам банка). Задачи 1–5 — код на тестовых досье, 6–10 — наполнение агентами.

**Tech Stack:** Python 3 (stdlib, unittest), JSON-слои данных; интерфейс (`src/`) не меняется.

**Spec:** `docs/superpowers/specs/2026-10-15-dossiers-myths-space-design.md` (продолжение `docs/superpowers/specs/2026-10-14-dossier-money-pilot-design.md`)

## Global Constraints

- `data/bank.json` и `dist/` руками не править: только `npm run build`. `sources/` не редактировать.
- Встраивание не меняет у олимпиадной записи id, формулировку, год, этап, исходные варианты и их id; пояснение — только через `editorial.json`.
- Встраивающая запись: поля только `id`, `embeds`, `status`, `fact` (`table`, `row`, `ask`, `where`), `exclude`, `check`.
- Ссылки ячеек — `досье/таблица/строка`; `ref` требует совпадения текста с ячейкой `name` цели, `from` — только существования цели.
- Подписи вопросов досье и встроенных вопросов — из ячеек таблицы; у встроенной записи не может быть подписей в `glosses.json`.
- Пояснение записи с общим набором не называет неверных вариантов.
- id строк — с префиксом таблицы (`fig-`, `story-`, `mis-`); русские названия `ru` — от шести букв или из двух слов.
- Источник строки: не меньше двух независимых, `official`/`academic`, дословная `quote`, `checkedAt`. Книга автора и видеокурс — список тем, не источник; тексты книги не копировать.
- Тесты: `python3 -m unittest discover -s test -t .` и `node --test test/*.test.mjs` (глоб без кавычек).
- Каждое заметное изменение — запись в `CHANGELOG.md` в том же коммите.
- Агенты — с согласия автора на каждый запуск, не больше трёх одновременно, без личных данных в HTTP-запросах.
- Ветка `feat/dossiers-myths-space`; перед слиянием в master — спросить автора о ревью.

## Review Focus

- Встраивается запись, уже собранная склейкой `pool` (вариантов больше четырёх, id `o5`…): её варианты сохраняются, набор из таблицы добавляется после — тест в задаче 3.
- Исходный олимпиадный вариант с лишними пробелами (` 菊花 `) всё равно находит свою ячейку и подпись — тест в задаче 3.
- `embeds` указывает на запись, удалённую через `retired.json` (её id в `mergedIds` оставленной): ошибка называет, куда она ушла — тест в задаче 3.
- Утечка через текст встроенного олимпиадного вопроса в черновике писателя видна в `python3 scripts/dossiers.py`, а не только при сборке — тест в задаче 4 (черновики участвуют).
- У ячейки сразу `ref` и `from` — ошибка формата, а не молчаливый выбор одного — тест в задаче 2.

---

### Task 1: Вопросы-встраивания в проверке досье

**Files:**
- Modify: `scripts/dossiers.py` (`QUESTION_FIELDS`, `validate_questions`, `_content_errors`, `dossier_records`)
- Test: `test/test_dossiers.py`

**Interfaces:**
- Consumes: существующие `validate_questions(questions, dossier, bank=None)`, `_reference_errors`, `_content_errors`, `dossier_records`, тестовые фабрики `dossier()`, `question()`, `row()`, `cell()`.
- Produces: `EMBED_FIELDS`, `EMBED_FACT_FIELDS`; вопрос с `embeds` проходит `validate_questions` без текста, пояснения и темы; `dossier_records` такие вопросы пропускает. Тестовая фабрика `embed(**overrides)`.

- [ ] **Step 1: Создать ветку** (если не создана): `git checkout -b feat/dossiers-myths-space master` — ветка уже есть, проверить `git branch --show-current`.

- [ ] **Step 2: Написать падающие тесты**

В `test/test_dossiers.py` (после `class ValidateQuestionsTest`):

```python
def embed(**overrides):
    item = {'id': 'money-q02', 'embeds': '2024-25-shk-9', 'status': 'accepted',
            'fact': {'table': 'banknotes', 'row': 'cny-20', 'ask': 'flower', 'where': {'currency': '人民币'}},
            'exclude': [], 'check': {'verdict': 'accept', 'note': 'ок'}}
    item.update(overrides)
    return item


class EmbedQuestionTest(unittest.TestCase):
    def errors(self, questions, data=None):
        return validate_questions(questions, data or dossier())

    def assertRejects(self, questions, fragment, data=None):
        errors = self.errors(questions, data)
        self.assertTrue(any(fragment in error for error in errors), f'{fragment!r} not in {errors}')

    def test_embed_is_valid_without_text_explanation_and_topic(self):
        self.assertEqual(self.errors([embed()]), [])

    def test_embed_does_not_carry_its_own_text(self):
        self.assertRejects([embed(questionRu='Какой цветок на купюре 20 юаней 2019 года?')], 'у встраивания нет полей')
        self.assertRejects([embed(topic=TOPIC)], 'у встраивания нет полей')

    def test_embed_asks_a_column_without_given_or_explicit_options(self):
        self.assertRejects([embed(fact={**embed()['fact'], 'given': 'denomination'})], 'встраивание спрашивает колонку')

    def test_embed_needs_a_target(self):
        self.assertRejects([embed(embeds='')], 'embeds — id записи банка')
        self.assertRejects([embed(embeds=['2024-25-shk-9'])], 'embeds — id записи банка')

    def test_same_record_is_embedded_once(self):
        self.assertRejects([embed(), embed(id='money-q03')], 'уже встроена')

    def test_embed_still_checks_twins_and_glosses(self):
        data = dossier()
        row(data, 'cny-50')['flower'] = cell('荷花', ['лотос'], gloss='Лотос — второй')
        self.assertRejects([embed()], 'совпадает с правильным', data)
        data = dossier()
        row(data, 'cny-50')['flower'].pop('gloss')
        self.assertRejects([embed()], 'нет подписи', data)

    def test_embed_with_a_small_table_pool_is_valid(self):
        # исходные олимпиадные варианты сами дают три неверных
        fact = {'table': 'banknotes', 'row': 'rub-500', 'ask': 'back', 'where': {'currency': '卢布'}}
        self.assertEqual(self.errors([embed(fact=fact)]), [])

    def test_embed_is_not_a_new_record(self):
        self.assertEqual(dossier_records(dossier(), [embed()]), [])

    def test_embed_takes_no_part_in_text_leaks_inside_the_dossier(self):
        # текст встроенного вопроса — в банке; утечки с ним ловит cross_leak_errors (задача 4)
        self.assertEqual(self.errors([question(), embed(fact={**embed()['fact'], 'row': 'cny-50'})]), [])
```

- [ ] **Step 3: Запустить и убедиться, что падает**

Run: `python3 -m unittest test.test_dossiers.EmbedQuestionTest -v`
Expected: FAIL — `test_embed_is_valid_without_text_explanation_and_topic` получает ошибки «неизвестные поля вопроса ['embeds']», «тема вне списка», «нет текста вопроса».

- [ ] **Step 4: Реализовать**

В `scripts/dossiers.py`:

```python
QUESTION_FIELDS = {'id', 'status', 'topic', 'fact', 'questionRu', 'explanation', 'exclude', 'check', 'embeds'}
# встраивание олимпиадного вопроса: текст, пояснение и тема — у олимпиадной записи
EMBED_FIELDS = {'id', 'embeds', 'status', 'fact', 'exclude', 'check'}
EMBED_FACT_FIELDS = {'table', 'row', 'ask', 'where'}
```

Новая функция (рядом с `_content_errors`):

```python
def _embed_errors(where: str, question: dict, embedded: set[str]) -> list[str]:
    target = question.get('embeds')
    if not isinstance(target, str) or not target.strip():
        return [f'{where}: embeds — id записи банка']
    errors: list[str] = []
    if target in embedded:
        errors.append(f'{where}: запись {target} уже встроена другим вопросом')
    embedded.add(target)
    extra = sorted(set(question) - EMBED_FIELDS)
    if extra:
        errors.append(f'{where}: у встраивания нет полей {extra} — текст, пояснение и тема у олимпиадной записи')
    fact = question.get('fact')
    if isinstance(fact, dict) and set(fact) - EMBED_FACT_FIELDS:
        errors.append(f'{where}: встраивание спрашивает колонку — без {sorted(set(fact) - EMBED_FACT_FIELDS)}')
    return errors
```

В `_content_errors` — после проверки «нет подписи» и до проверок текста; проверку `MIN_WRONG` пропустить для встраиваний:

```python
    options, _ = question_options(question, dossier)
    embedded = 'embeds' in question
    if not embedded and len(options) - 1 < MIN_WRONG:
        errors.append(f'{where}: в наборе меньше {MIN_WRONG} неверных вариантов')
    unglossed = [option['id'] for option in options[1:] if 'gloss' not in option]
    if unglossed:
        errors.append(f'{where}: у неверных вариантов нет подписи: {unglossed}')
    if embedded:
        return errors
```

(заменяет нынешние строки с `if len(options) - 1 < MIN_WRONG` и `unglossed`; остальной код функции — проверки текста — без изменений).

В `validate_questions`: перед циклом `embedded_targets: set[str] = set()`; блок проверок темы, текста и пояснения обернуть:

```python
        embeds = 'embeds' in question
        text = None
        if embeds:
            errors += _embed_errors(where, question, embedded_targets)
        else:
            if question.get('topic') not in TOPICS:
                errors.append(f'{where}: тема вне списка семи категорий')
            text = question.get('questionRu')
            if not isinstance(text, str) or not text.strip():
                errors.append(f'{where}: нет текста вопроса')
                text = None
            else:
                errors += [f'{where}: {message}' for message in language_errors(text, [])]
                errors += [f'{where}: {message}' for message in completeness_errors(text, None, [])]
            if not isinstance(question.get('explanation'), str) or not question['explanation'].strip():
                errors.append(f'{where}: нет пояснения')
            elif not 3 <= sentence_count(question['explanation']) <= 5:
                errors.append(f'{where}: пояснение должно состоять из 3–5 предложений')
```

и низ цикла:

```python
        broken = _reference_errors(where, question, dossier)
        errors += broken
        if not broken and (embeds or text is not None):
            errors += _content_errors(where, question, dossier)
            if named and not embeds:
                whole.append(question)
```

`_embed_errors` возвращает ошибку раньше остальных, если `embeds` не строка; тогда `_reference_errors` всё равно выполняется — это безопасно.

В `dossier_records`: `if question['status'] != 'accepted' or 'embeds' in question: continue`.

- [ ] **Step 5: Запустить тесты**

Run: `python3 -m unittest test.test_dossiers -v`
Expected: PASS (все прежние и 9 новых).

- [ ] **Step 6: Commit**

```bash
git add scripts/dossiers.py test/test_dossiers.py
git commit -m "Досье: вопросы-встраивания олимпиадных записей в проверке"
```

---

### Task 2: Ссылки между досье — `ref` и `from`

**Files:**
- Modify: `scripts/dossiers.py` (`CELL_FIELDS`, `_cell_errors`, новая `validate_links`)
- Test: `test/test_dossiers.py`

**Interfaces:**
- Consumes: `validate_dossier`, тестовая `source(n)`.
- Produces: `validate_links(dossiers: dict[str, dict]) -> list[str]` — ключ словаря — id досье; тестовые фабрики `myths_dossier()`, `space_dossier()` (задачи 4–5 ими пользуются).

- [ ] **Step 1: Написать падающие тесты**

```python
def plain_row(row_id, **cells):
    return {'id': row_id, **cells, 'sources': [source(1), source(2)], 'olympiad': []}


def myths_dossier():
    figure = lambda row_id, zh, ru: plain_row(row_id, name=cell(zh, [ru], gloss=f'{ru} — персонаж мифа'),
                                              role='персонаж мифа')
    return {'id': 'myths', 'title': 'Мифы и легенды', 'tables': {
        'figures': {'columns': {'name': 'zh', 'role': 'ru'}, 'rows': [
            figure('fig-zhurong', '祝融', 'бог огня Чжужун'),
            figure('fig-change', '嫦娥', 'богиня Чанъэ'),
            figure('fig-xihe', '羲和', 'богиня Сихэ'),
            figure('fig-kuafu', '夸父', 'великан Куафу'),
        ]},
        'stories': {'columns': {'name': 'zh', 'meaning': 'ru'}, 'rows': [
            plain_row('story-niulang-zhinv', name=cell('牛郎织女', ['Пастух и Ткачиха'], gloss='Легенда о Пастухе и Ткачихе'),
                      meaning='народная легенда'),
        ]}}}


def space_dossier():
    mission = lambda row_id, zh, namesake: plain_row(row_id, name=cell(zh, gloss=f'Аппарат {row_id}'), namesake=namesake)
    return {'id': 'space', 'title': 'Космос', 'tables': {
        'missions': {'columns': {'name': 'zh', 'namesake': 'zh'}, 'rows': [
            mission('mis-zhurong', '祝融号', {'zh': '祝融', 'ref': 'myths/figures/fig-zhurong', 'gloss': 'Бог огня Чжужун'}),
            mission('mis-queqiao', '鹊桥', {'zh': '鹊桥', 'from': 'myths/stories/story-niulang-zhinv',
                                           'gloss': 'Сорочий мост из легенды'}),
            mission('mis-wukong', '悟空', {'zh': '悟空', 'gloss': 'Сунь Укун из романа'}),
        ]}}}


class LinksTest(unittest.TestCase):
    def links(self, space=None, myths=None):
        return validate_links({'space': space or space_dossier(), 'myths': myths or myths_dossier()})

    def test_live_links_are_valid(self):
        self.assertEqual(validate_dossier(space_dossier()), [])
        self.assertEqual(self.links(), [])

    def test_ref_to_a_missing_row_is_an_error(self):
        space = space_dossier()
        space['tables']['missions']['rows'][0]['namesake']['ref'] = 'myths/figures/fig-rongzhu'
        self.assertTrue(any('несуществующую строку' in e for e in self.links(space)))

    def test_ref_needs_the_same_name(self):
        myths = myths_dossier()
        myths['tables']['figures']['rows'][0]['name']['zh'] = '祝融氏'
        self.assertTrue(any('другое название' in e for e in self.links(myths=myths)))

    def test_from_only_needs_the_row(self):
        space = space_dossier()
        space['tables']['missions']['rows'][1]['namesake']['from'] = 'myths/stories/story-baishe'
        self.assertTrue(any('несуществующую строку' in e for e in self.links(space)))

    def test_link_format_is_checked_with_the_dossier(self):
        space = space_dossier()
        space['tables']['missions']['rows'][0]['namesake']['ref'] = 'fig-zhurong'
        self.assertTrue(any('досье/таблица/строка' in e for e in validate_dossier(space)))
        space = space_dossier()
        space['tables']['missions']['rows'][0]['namesake']['from'] = 'myths/stories/story-niulang-zhinv'
        self.assertTrue(any('ref или from' in e for e in validate_dossier(space)))
```

Импорт расширить: `validate_links`.

- [ ] **Step 2: Запустить и убедиться, что падает**

Run: `python3 -m unittest test.test_dossiers.LinksTest -v`
Expected: FAIL — `ImportError: cannot import name 'validate_links'`.

- [ ] **Step 3: Реализовать**

`CELL_FIELDS = {'zh', 'ru', 'gloss', 'ref', 'from'}` и:

```python
LINK = re.compile(r'[a-z][a-z0-9-]*/[a-z][a-z0-9_-]*/[a-z0-9][a-z0-9-]*')
LINK_FIELDS = ('ref', 'from')
```

В `_cell_errors` перед `return errors`:

```python
    links = [field for field in LINK_FIELDS if field in cell]
    if len(links) > 1:
        errors.append(f'{where}: у ячейки одна ссылка — ref или from')
    for field in links:
        if not isinstance(cell[field], str) or not LINK.fullmatch(cell[field]):
            errors.append(f'{where}: {field} — «досье/таблица/строка»')
```

Новая функция:

```python
def validate_links(dossiers: dict[str, dict]) -> list[str]:
    """Ссылки ячеек на строки других досье: `ref` — тот же персонаж (текст совпадает), `from` — назван по."""
    errors: list[str] = []
    for dossier_id, dossier in dossiers.items():
        for table_name, table in dossier['tables'].items():
            for row in table['rows']:
                for column, kind in table['columns'].items():
                    cell = row.get(column)
                    if kind != 'zh' or not isinstance(cell, dict):
                        continue
                    for field in LINK_FIELDS:
                        if field not in cell:
                            continue
                        where = f'{dossier_id}/{table_name}/{row["id"]}.{column}'
                        target_dossier, target_table, target_row = cell[field].split('/')
                        rows = {item['id']: item for item in
                                dossiers.get(target_dossier, {}).get('tables', {}).get(target_table, {}).get('rows', [])}
                        target = rows.get(target_row)
                        if target is None:
                            errors.append(f'{where}: {field} ведёт в несуществующую строку {cell[field]}')
                        elif field == 'ref':
                            name = target.get('name', {}).get('zh') if isinstance(target.get('name'), dict) else None
                            if name != cell['zh']:
                                errors.append(f'{where}: ref {cell[field]} — у строки другое название '
                                              f'({name!r} ≠ {cell["zh"]!r})')
    return errors
```

- [ ] **Step 4: Запустить тесты**

Run: `python3 -m unittest test.test_dossiers -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/dossiers.py test/test_dossiers.py
git commit -m "Досье: ссылки ячеек на другие досье (ref, from)"
```

---

### Task 3: Слой встраивания — `scripts/embeds.py`

**Files:**
- Create: `scripts/embeds.py`
- Test: `test/test_dossiers.py` (класс `ApplyEmbedsTest` — фабрики досье уже там)

**Interfaces:**
- Consumes: `question_options(question, dossier) -> (options, answer_id)` из `scripts/dossiers.py`; фабрики `dossier()`, `embed()`.
- Produces: `apply_embeds(bank: list[dict], loaded: list[tuple[dict, list[dict]]], glosses: dict[str, dict]) -> list[dict]` — новый список записей, вход не меняется; при ошибках `ValueError('некорректные встраивания:\n - …')`.

- [ ] **Step 1: Написать падающие тесты**

```python
from embeds import apply_embeds


def olympiad(**overrides):
    item = {'id': '2024-25-shk-9', 'questionRu': 'Какой цветок изображён на купюре 20 юаней?', 'questionZh': None,
            'topic': TOPIC, 'options': [{'id': 'o1', 'zh': '荷花'}, {'id': 'o2', 'zh': '菊花'},
                                        {'id': 'o3', 'zh': '梅花'}, {'id': 'o4', 'zh': '水仙花'}],
            'answer': {'optionId': 'o1', 'state': 'verified'},
            'explanation': {'ru': 'На лицевой стороне купюры 20 юаней — лотос.'},
            'occurrences': [{'year': '2024-25', 'stageCode': 'shk', 'number': 9}], 'evidence': []}
    item.update(overrides)
    return item


class ApplyEmbedsTest(unittest.TestCase):
    def apply(self, bank=None, questions=None, glosses=None):
        return apply_embeds(bank or [olympiad()], [(dossier(), questions or [embed()])], glosses or {})

    def assertRejects(self, fragment, **kwargs):
        with self.assertRaises(ValueError) as caught:
            self.apply(**kwargs)
        self.assertIn(fragment, str(caught.exception))

    def test_embedding_adds_the_table_pool_and_glosses_and_keeps_the_question(self):
        [record] = self.apply()
        self.assertEqual([o['id'] for o in record['options']], ['o1', 'o2', 'o3', 'o4', 'cny-10'])
        self.assertEqual(record['questionRu'], olympiad()['questionRu'])
        self.assertEqual(record['occurrences'], olympiad()['occurrences'])
        self.assertEqual(record['answer'], {'optionId': 'o1', 'state': 'verified'})
        self.assertEqual(record['dossier'], 'money')
        self.assertNotIn('gloss', record['options'][0])
        self.assertEqual(record['options'][1]['gloss'], 'Хризантема — цветок на купюре')
        self.assertEqual(record['options'][4], {'id': 'cny-10', 'zh': '月季花', 'gloss': 'Китайская роза — цветок на купюре'})

    def test_only_accepted_embeds_apply_and_the_input_is_untouched(self):
        bank = [olympiad()]
        [record] = apply_embeds(bank, [(dossier(), [embed(status='draft')])], {})
        self.assertIs(record, bank[0])
        self.apply(bank=bank)
        self.assertEqual(len(bank[0]['options']), 4)

    def test_pooled_record_keeps_its_options_and_order(self):
        options = olympiad()['options'] + [{'id': 'o5', 'zh': '月季花'}]
        [record] = self.apply(bank=[olympiad(options=options)])
        self.assertEqual([o['id'] for o in record['options']], ['o1', 'o2', 'o3', 'o4', 'o5'])

    def test_option_with_stray_spaces_finds_its_cell(self):
        options = [{'id': 'o1', 'zh': '荷花'}, {'id': 'o2', 'zh': ' 菊花 '}, {'id': 'o3', 'zh': '梅花'},
                   {'id': 'o4', 'zh': '水仙花'}]
        [record] = self.apply(bank=[olympiad(options=options)])
        self.assertEqual(record['options'][1]['gloss'], 'Хризантема — цветок на купюре')

    def test_rejects_each_broken_embedding(self):
        self.assertRejects('не совпадает с ячейкой', bank=[olympiad(answer={'optionId': 'o2', 'state': 'verified'})])
        options = olympiad()['options'][:3] + [{'id': 'o4', 'zh': '兰花'}]
        self.assertRejects('нет ячейки с подписью', bank=[olympiad(options=options)])
        self.assertRejects('пояснение', bank=[olympiad(explanation={'ru': 'Не 菊花, а лотос.'})])
        self.assertRejects('glosses.json', glosses={'2024-25-shk-9': {'options': {}}})
        self.assertRejects('вопрос досье', bank=[olympiad(dossier='money')])
        self.assertRejects('влита в 2025-26-mun-1',
                           bank=[olympiad(id='2025-26-mun-1', mergedIds=['2024-25-shk-9'])])
        self.assertRejects('в банке нет записи', bank=[olympiad(id='2025-26-mun-1')])

    def test_record_is_embedded_by_one_dossier_only(self):
        with self.assertRaises(ValueError) as caught:
            apply_embeds([olympiad()], [(dossier(), [embed()]), (dossier(), [embed()])], {})
        self.assertIn('уже встроена', str(caught.exception))
```

- [ ] **Step 2: Запустить и убедиться, что падает**

Run: `python3 -m unittest test.test_dossiers -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'embeds'`.

- [ ] **Step 3: Реализовать `scripts/embeds.py`**

```python
"""Встраивание олимпиадного вопроса в досье.

Вопрос досье с полем `embeds` не создаёт новую запись: олимпиадная запись остаётся собой (id,
формулировка, появления, исходные варианты и их id — на них держится прогресс учеников), но
получает общий набор неверных вариантов из той же колонки таблицы и подписи ко всем неверным
вариантам — из ячеек таблицы. Слой идёт после склеек и удалений (`embeds` — итоговый id) и до
`glosses.json`. Спецификация — docs/superpowers/specs/2026-10-15-dossiers-myths-space-design.md.
"""

from __future__ import annotations

from dossiers import question_options


def _column_glosses(question: dict, dossier: dict) -> dict[str, str]:
    """Подпись каждой ячейки спрашиваемой колонки таблицы — по тексту ячейки."""
    fact = question['fact']
    glosses: dict[str, str] = {}
    for row in dossier['tables'][fact['table']]['rows']:
        cell = row.get(fact['ask'])
        if isinstance(cell, dict) and cell.get('gloss'):
            glosses.setdefault(cell['zh'].strip(), cell['gloss'].strip())
    return glosses


def apply_embeds(bank: list[dict], loaded: list[tuple[dict, list[dict]]],
                 glosses: dict[str, dict]) -> list[dict]:
    by_id = {record['id']: record for record in bank}
    merged_into = {old: record['id'] for record in bank for old in record.get('mergedIds', [])}
    errors: list[str] = []
    embedded_by: dict[str, str] = {}
    updates: dict[str, dict] = {}
    for dossier, questions in loaded:
        for question in questions:
            if 'embeds' not in question or question['status'] != 'accepted':
                continue
            where = f'{dossier["id"]}/{question["id"]}'
            target = question['embeds']
            record = by_id.get(target)
            if record is None:
                hint = f' — влита в {merged_into[target]}' if target in merged_into else ''
                errors.append(f'{where}: в банке нет записи {target}{hint}')
                continue
            if target in embedded_by:
                errors.append(f'{where}: запись {target} уже встроена вопросом {embedded_by[target]}')
                continue
            embedded_by[target] = where
            if 'dossier' in record:
                errors.append(f'{where}: {target} — вопрос досье, его не встраивают')
                continue
            if target in glosses:
                errors.append(f'{where}: у {target} есть подписи в glosses.json — перенесите их в ячейки таблицы')
                continue
            table_options, _ = question_options(question, dossier)
            answer = next(option for option in record['options'] if option['id'] == record['answer']['optionId'])
            if answer['zh'].strip() != table_options[0]['zh']:
                errors.append(f'{where}: ответ {target} ({answer["zh"]}) не совпадает с ячейкой '
                              f'({table_options[0]["zh"]})')
                continue
            cell_glosses = _column_glosses(question, dossier)
            options: list[dict] = []
            for option in record['options']:
                option = {key: value for key, value in option.items() if key != 'gloss'}
                if option['id'] != answer['id']:
                    gloss = cell_glosses.get(option['zh'].strip())
                    if gloss is None:
                        errors.append(f'{where}: для варианта {option["zh"].strip()} нет ячейки с подписью в таблице')
                    else:
                        option['gloss'] = gloss
                options.append(option)
            texts = {option['zh'].strip() for option in options}
            for added in table_options[1:]:
                if added['zh'] not in texts:
                    options.append(added)
                    texts.add(added['zh'])
            explanation = record.get('explanation', {}).get('ru', '')
            named = [option['zh'].strip() for option in options
                     if option['id'] != answer['id'] and option['zh'].strip() in explanation]
            if named:
                errors.append(f'{where}: пояснение {target} называет неверные варианты {named} — '
                              'на экране их может не оказаться; правка в editorial.json')
            updates[target] = {**record, 'options': options, 'dossier': dossier['id']}
    if errors:
        raise ValueError('некорректные встраивания:\n - ' + '\n - '.join(errors))
    return [updates.get(record['id'], record) for record in bank]
```

- [ ] **Step 4: Запустить тесты**

Run: `python3 -m unittest test.test_dossiers -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/embeds.py test/test_dossiers.py
git commit -m "Слой встраивания олимпиадных вопросов в досье"
```

---

### Task 4: Утечки между досье

**Files:**
- Modify: `scripts/dossiers.py` (новая `cross_leak_errors`)
- Test: `test/test_dossiers.py`

**Interfaces:**
- Consumes: `answer_cell`, `_mentions`; фабрики `dossier()`, `question()`, `embed()`, `olympiad()`, `myths_dossier()`.
- Produces: `cross_leak_errors(bank: list[dict], loaded: list[tuple[dict, list[dict]]]) -> list[str]` — по всем вопросам всех досье, включая черновики; текст встроенного вопроса — из банка, текст своего вопроса — из банка, если запись там есть (правки `editorial.json`), иначе из файла вопросов.

- [ ] **Step 1: Написать падающие тесты**

```python
def myths_question(**overrides):
    item = {'id': 'myths-q01', 'status': 'draft', 'topic': 'Культура, традиции и праздники',
            'fact': {'table': 'figures', 'row': 'fig-xihe', 'ask': 'name'},
            'questionRu': 'Какая богиня, по преданию, правила колесницей Солнца, а не цветком 荷花?',
            'explanation': 'Первое предложение. Второе предложение. Третье предложение.', 'exclude': []}
    item.update(overrides)
    return item


class CrossLeakTest(unittest.TestCase):
    def test_answer_of_one_dossier_in_the_text_of_another(self):
        loaded = [(dossier(), [question()]), (myths_dossier(), [myths_question()])]
        errors = cross_leak_errors([], loaded)
        self.assertIn("myths/myths-q01: текст называет ответ вопроса money/money-q01: ['荷花']", errors)

    def test_embedded_question_text_comes_from_the_bank(self):
        record = olympiad(questionRu='Кто из богинь — 羲和 — изображён на купюре 20 юаней?')
        loaded = [(dossier(), [embed()]), (myths_dossier(), [myths_question(questionRu='Какая богиня правила колесницей Солнца?')])]
        errors = cross_leak_errors([record], loaded)
        self.assertTrue(any(e.startswith('money/money-q02: текст называет ответ вопроса myths/myths-q01') for e in errors))

    def test_edited_text_in_the_bank_wins_over_the_file(self):
        edited = {'id': 'myths-q01', 'questionRu': 'Какая богиня правила колесницей Солнца?'}
        loaded = [(dossier(), [question()]), (myths_dossier(), [myths_question(status='accepted')])]
        self.assertEqual(cross_leak_errors([edited], loaded), [])
```

Импорт: `cross_leak_errors`.

- [ ] **Step 2: Запустить и убедиться, что падает**

Run: `python3 -m unittest test.test_dossiers.CrossLeakTest -v`
Expected: FAIL — `ImportError: cannot import name 'cross_leak_errors'`.

- [ ] **Step 3: Реализовать**

```python
def cross_leak_errors(bank: list[dict], loaded: list[tuple[dict, list[dict]]]) -> list[str]:
    """Утечки по всем вопросам всех досье сразу — по окончательным текстам.

    Текст встроенного вопроса есть только в банке; текст своего вопроса берётся из банка, если
    запись уже там (с правками editorial.json), иначе — из файла вопросов (черновик).
    """
    by_id = {record['id']: record for record in bank}
    entries: list[tuple[str, str, dict]] = []
    for dossier, questions in loaded:
        for question in questions:
            if 'embeds' in question:
                record = by_id.get(question['embeds'])
                if record is None:
                    continue
                text = record['questionRu']
            else:
                record = by_id.get(question['id'])
                text = record['questionRu'] if record else question['questionRu']
            entries.append((f'{dossier["id"]}/{question["id"]}', text, answer_cell(question, dossier)[1]))
    errors: list[str] = []
    for label, text, _ in entries:
        for other, _, answer in entries:
            if other != label:
                names = _mentions(text, answer)
                if names:
                    errors.append(f'{label}: текст называет ответ вопроса {other}: {names}')
    return errors
```

- [ ] **Step 4: Запустить тесты**

Run: `python3 -m unittest test.test_dossiers -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/dossiers.py test/test_dossiers.py
git commit -m "Досье: утечки между всеми досье по окончательным текстам"
```

---

### Task 5: Сборка, проверка из командной строки, отчёт, пустые досье, документация

**Files:**
- Modify: `scripts/merge_bank.py:15-25, 374-410`
- Modify: `scripts/dossiers.py` (`dossier_report`, `main`)
- Modify: `test/test_dossiers.py` (`DossierInBankTest`, отчёт)
- Create: `data/dossiers/myths.json`, `data/dossiers/myths-questions.json`, `data/dossiers/space.json`, `data/dossiers/space-questions.json`
- Modify: `CLAUDE.md`, `README.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `apply_embeds`, `validate_links`, `cross_leak_errors`, `load_dossier`, `dossier_paths`, `load_glosses`.
- Produces: `dossier_report(dossier: dict, questions: list[dict], bank: list[dict] | None = None) -> str` — у встраивания: олимпиадный текст, ответ и все неверные варианты записи с подписями (если запись уже встроена в банке), иначе — набор из таблицы и пометка.

- [ ] **Step 1: Написать падающие тесты**

В `DossierReportTest`:

```python
    def test_embed_shows_the_olympiad_question_and_its_options(self):
        [record] = apply_embeds([olympiad()], [(dossier(), [embed()])], {})
        report = dossier_report(dossier(), [embed()], [record])
        self.assertIn('### money-q02 · accepted · проверка: accept · встраивает 2024-25-shk-9', report)
        self.assertIn(olympiad()['questionRu'], report)
        self.assertIn('  - 月季花 — Китайская роза — цветок на купюре', report)

    def test_embed_before_the_build_says_so(self):
        report = dossier_report(dossier(), [embed()])
        self.assertIn('встраивает 2024-25-shk-9; текст и варианты — после сборки', report)
```

В `DossierInBankTest` — заменить `test_accepted_questions_reach_the_bank_and_drafts_do_not` на:

```python
    def test_accepted_questions_reach_the_bank_and_drafts_do_not(self):
        for table_path, questions_path in self.pairs:
            data, questions = load_dossier(table_path, questions_path)
            for item in questions:
                if 'embeds' in item:
                    continue
                if item['status'] != 'accepted':
                    self.assertNotIn(item['id'], self.bank)
                    continue
                record = self.bank[item['id']]
                options, answer_id = question_options(item, data)
                self.assertEqual(record['answer']['optionId'], answer_id, item['id'])
                self.assertEqual([o['id'] for o in record['options']], [o['id'] for o in options], item['id'])
                self.assertTrue(all(o.get('gloss') for o in record['options'] if o['id'] != answer_id), item['id'])

    def test_accepted_embeds_reach_the_bank(self):
        for table_path, questions_path in self.pairs:
            data, questions = load_dossier(table_path, questions_path)
            for item in questions:
                if 'embeds' not in item or item['status'] != 'accepted':
                    continue
                record = self.bank[item['embeds']]
                answer = next(o for o in record['options'] if o['id'] == record['answer']['optionId'])
                self.assertEqual(record.get('dossier'), data['id'], item['id'])
                self.assertEqual(answer['zh'].strip(), question_options(item, data)[0][0]['zh'], item['id'])
                self.assertTrue(all(o.get('gloss') for o in record['options'] if o is not answer), item['id'])

    def test_links_between_dossiers_are_alive(self):
        loaded = {}
        for table_path, questions_path in self.pairs:
            data, _ = load_dossier(table_path, questions_path)
            loaded[data['id']] = data
        self.assertEqual(validate_links(loaded), [])

    def test_all_dossiers_are_part_of_the_build(self):
        names = {table.name for table, _ in self.pairs}
        self.assertEqual(names, {'money.json', 'myths.json', 'space.json'})
```

(прежний `test_money_dossier_is_part_of_the_build` удалить — его заменяет последний тест).

- [ ] **Step 2: Запустить и убедиться, что падает**

Run: `python3 -m unittest test.test_dossiers -v`
Expected: FAIL — отчёт: `dossier_report() takes 2 positional arguments but 3 were given`; `test_all_dossiers_are_part_of_the_build`: нет myths.json, space.json.

- [ ] **Step 3: Отчёт со встраиваниями**

В `dossier_report` — сигнатура `dossier_report(dossier, questions, bank=None)`, перед циклом по вопросам `by_id = {record['id']: record for record in bank or []}`; тело цикла:

```python
    for question in questions:
        check = question.get('check') or {}
        header = f'### {question["id"]} · {question["status"]} · проверка: {check.get("verdict", "нет")}'
        if 'embeds' in question:
            record = by_id.get(question['embeds'])
            header += f' · встраивает {question["embeds"]}'
            if record is not None and record.get('dossier') == dossier['id']:
                answer = next(o for o in record['options'] if o['id'] == record['answer']['optionId'])
                wrong = [o for o in record['options'] if o is not answer]
                text, topic = record['questionRu'], record.get('topic', '')
                explanation = record.get('explanation', {}).get('ru', '')
            else:
                options, _ = question_options(question, dossier)
                answer, wrong = options[0], options[1:]
                text = f'(встраивает {question["embeds"]}; текст и варианты — после сборки)'
                topic, explanation = '—', '—'
        else:
            options, _ = question_options(question, dossier)
            answer, wrong = options[0], options[1:]
            text, topic, explanation = question['questionRu'], question['topic'], question['explanation'].strip()
        lines += [header, '', text, '',
                  f'- Ответ: {answer["zh"].strip()}',
                  # подписи принимает автор — значит, он их видит здесь
                  '- Неверные:', *(f'  - {option["zh"].strip()} — {option.get("gloss", "без подписи")}'
                                   for option in wrong),
                  f'- Тема: {topic}',
                  f'- Пояснение: {explanation}']
        if check.get('note'):
            lines.append(f'- Замечание проверки: {check["note"]}')
        lines.append('')
```

- [ ] **Step 4: Сборка банка**

`scripts/merge_bank.py` — импорты:

```python
from dossiers import (cross_leak_errors, dossier_paths, dossier_records, dossier_report, load_dossier,
                      validate_links)
from embeds import apply_embeds
```

Блок досье после `load_authored`:

```python
    # досье — сразу после дополнений: правки, склейки и подписи дальше работают и для них
    loaded: list[tuple[dict, list[dict]]] = []
    for table_path, questions_path in dossier_paths(ROOT / 'data/dossiers'):
        dossier, questions = load_dossier(table_path, questions_path, bank)
        bank.extend(dossier_records(dossier, questions))
        loaded.append((dossier, questions))
    errors = validate_links({dossier['id']: dossier for dossier, _ in loaded})
    if errors:
        raise ValueError('некорректные ссылки между досье:\n - ' + '\n - '.join(errors))
```

После `apply_retired` (до `apply_fact_groups`):

```python
    # встраивание олимпиадных вопросов в досье — по итоговым id, до подписей glosses.json
    glosses = load_glosses(ROOT / 'data/review/glosses.json')
    bank = apply_embeds(bank, loaded, glosses)
```

После проверки `validate_authored` (до `apply_glosses`):

```python
    # утечки между досье — по окончательным текстам, с правками и встраиваниями
    errors = cross_leak_errors(bank, loaded)
    if errors:
        raise ValueError('утечки между вопросами досье:\n - ' + '\n - '.join(errors))
```

`apply_glosses(bank, load_glosses(...))` → `apply_glosses(bank, glosses)`. Отчёты — после `_write_report(report, bank)`:

```python
    for dossier, questions in loaded:
        (ROOT / f'data/review/dossier-{dossier["id"]}.md').write_text(
            dossier_report(dossier, questions, bank), encoding='utf-8')
```

(прежний словарь `dossier_reports` удалить).

- [ ] **Step 5: Проверка из командной строки**

`main()` в `scripts/dossiers.py`:

```python
def main() -> None:
    """Проверка всех досье без сборки банка: её запускают агенты, пока пишут досье."""
    root = Path(__file__).resolve().parents[1]
    bank_path = root / 'data/bank.json'
    bank = json.loads(bank_path.read_text('utf-8')) if bank_path.exists() else []
    loaded = [load_dossier(table_path, questions_path, bank)
              for table_path, questions_path in dossier_paths(root / 'data/dossiers')]
    errors = validate_links({data['id']: data for data, _ in loaded}) + cross_leak_errors(bank, loaded)
    if errors:
        raise SystemExit('ошибки досье:\n - ' + '\n - '.join(errors))
    for data, questions in loaded:
        accepted = sum(1 for question in questions if question['status'] == 'accepted')
        rows = sum(len(table['rows']) for table in data['tables'].values())
        print(f'{data["id"]}: строк {rows}, вопросов {len(questions)}, принято {accepted} — ошибок нет')
```

- [ ] **Step 6: Пустые досье**

`data/dossiers/myths.json`:

```json
{
  "id": "myths",
  "title": "Мифы и легенды",
  "tables": {
    "figures": {
      "columns": {
        "name": "zh",
        "role": "ru"
      },
      "rows": []
    },
    "stories": {
      "columns": {
        "name": "zh",
        "kind": "zh",
        "hero": "zh",
        "meaning": "ru"
      },
      "rows": []
    }
  }
}
```

`data/dossiers/space.json`:

```json
{
  "id": "space",
  "title": "Космос",
  "tables": {
    "missions": {
      "columns": {
        "name": "zh",
        "program": "zh",
        "year": "zh",
        "namesake": "zh",
        "achievement": "ru"
      },
      "rows": []
    }
  }
}
```

`data/dossiers/myths-questions.json` и `data/dossiers/space-questions.json`: `[]`.

- [ ] **Step 7: Собрать и прогнать всё**

Run: `npm run build && python3 scripts/dossiers.py && python3 -m unittest discover -s test -t . && node --test test/*.test.mjs`
Expected: банк 440 записей (не изменился), три строки «… — ошибок нет» (money 37/36/36, myths 0, space 0), все тесты зелёные; появились `data/review/dossier-myths.md`, `dossier-space.md`; `git diff data/bank.json` пусто.

- [ ] **Step 8: Документация**

`CLAUDE.md` — дописать к пункту о досье:

```markdown
  Олимпиадный вопрос можно встроить в досье: вопрос досье с полем `embeds` (итоговый id записи)
  не создаёт новую запись, а добавляет олимпиадной общий набор из колонки таблицы и подписи из
  ячеек (`scripts/embeds.py`, слой после `retired.json`); id, формулировка и исходные варианты
  записи не меняются, у неё не может быть подписей в `glosses.json`, пояснение не называет
  неверных вариантов. Ячейка может ссылаться на строку другого досье: `ref` — тот же персонаж
  (текст совпадает с ячейкой `name`), `from` — назван по; утечки ищутся по всем досье сразу.
```

`README.md` — в порядке слоёв после `retired.json` добавить «→ встраивание олимпиадных вопросов в досье (`embeds`)».

`CHANGELOG.md` — перед `## Не реализовано (сознательно или пока)`:

```markdown
## 2026-10-15 — Встраивание олимпиадных вопросов в досье, ссылки и утечки между досье

- `scripts/embeds.py`: вопрос досье с `embeds` встраивается в олимпиадную запись — та сохраняет
  id, формулировку и варианты, но получает общий набор из таблицы и подписи из ячеек; сборка
  останавливается, если ответ не совпал с ячейкой, у варианта нет строки, пояснение называет
  неверный вариант или у записи есть подписи в `glosses.json`.
- Ссылки ячеек на другие досье (`ref` — тот же персонаж, `from` — назван по) и утечки по всем
  досье сразу — по окончательным текстам банка; `python3 scripts/dossiers.py` проверяет и то, и
  другое.
- Заведены пустые досье «Мифы и легенды» (`figures`, `stories`) и «Космос» (`missions`).
```

- [ ] **Step 9: Commit**

```bash
git add scripts test data/dossiers data/review/dossier-*.md CLAUDE.md README.md CHANGELOG.md
git commit -m "Встраивание и ссылки досье в сборке; пустые досье «Мифы и легенды» и «Космос»"
```

После задачи 5 — ревью кода одним агентом (с согласия автора), до наполнения досье.

---

### Task 6: Этап 1 — два сборщика

**Files:**
- Modify: `data/dossiers/myths.json`, `data/dossiers/space.json`

- [ ] **Step 1: Список встраиваемых вопросов для сборщика «Мифов и легенд».** Скрипт в scratchpad печатает из `data/bank.json` записи с ответами-мифами (поиск по 盘古, 女娲, 夸父, 嫦娥, 神农, 伏羲, 黄帝, 大禹, 共工, 后羿 в вариантах): id, текст, все варианты, ответ. Ожидаемо: `2017-18-reg-3`, `2020-21-reg-q588b1b`, `2020-21-zak-q2c2d90`, `2021-22-reg-qdc153d`, `2022-23-reg-7`, `2022-23-shk-q92d9cf`, `2023-24-reg-5`, `2024-25-pri-37`, `2024-25-zak-q082614`, `2025-26-reg-7`, `addition-b1-12`, `2024-25-zak-qa37e63` (мостик: станции названы в честь 嫦娥; встраивается в `figures`, см. спецификацию); для «Космоса» — `2020-21-zak-q244298` (神舟五号), `addition-b1-17` (嫦娥四号). Сохранить в `scratchpad/myths/embed-targets.json`.

- [ ] **Step 2: Скрипт проверки строк** `scratchpad/myths/check_rows.py <досье> <таблица> <файл>` — как `check_rows.py` пилота, но с выбором досье (`myths`/`space`) и с `validate_links` по всем трём досье (для `space`).

- [ ] **Step 3: Спросить автора о запуске двух сборщиков.**

- [ ] **Step 4: Сборщики.** Общее в задании — как в пилоте (формат строки и ячейки, два официальных/академических источника с дословной цитатой, `ru` — от шести букв или из двух слов, `gloss` у каждой ячейки-варианта, `olympiad`, без личных данных в запросах, проект не менять) плюс:
  - **«Мифы и легенды»:** строки `figures` для ВСЕХ вариантов встраиваемых вопросов (`embed-targets.json`) — текст `name` дословно как в олимпиадном варианте; персонажи-тёзки аппаратов (玉兔, 后羿, 吴刚, 羲和, 望舒, 夸父, 祝融, 精卫); герои легенд (牛郎, 织女, 王母娘娘, 梁山伯, 祝英台, 孟姜女, 白娘子, 花木兰). `stories`: мифы (盘古开天, 女娲造人, 女娲补天, 后羿射日, 夸父逐日, 精卫填海, 嫦娥奔月, 大禹治水, 仓颉造字) и легенды (牛郎织女, 梁山伯与祝英台, 孟姜女哭长城, 白蛇传, 木兰从军) — названия как в олимпиадных вариантах; `kind` — `神话` или `民间传说`; `hero` — имя как в `figures`. Темы книги автора и видеокурса (спецификация, «Источники тем») — проверить, что покрыты. id: `fig-…`, `story-…`.
  - **«Космос»:** `missions` — 嫦娥一号–六号, 玉兔/玉兔二号, 鹊桥, 天问一号, 祝融号, 天宫, 神舟五号, 悟空, 羲和号, 夸父一号, 北斗, недавняя лунная программа (梦舟/揽月/望宇 — названия и даты по официальным сообщениям; 嫦娥七号 — только если запущен); `namesake` с `ref` на `myths/figures/fig-…` (тот же персонаж) или `from` (鹊桥 → `myths/stories/story-niulang-zhinv`); у 悟空, 天问, 北斗 — без ссылки. Строки должны покрыть варианты встраиваемых вопросов «Космоса» (神舟五号 и его варианты 神舟十一号, 天宫一号, 嫦娥一号; 嫦娥三号–六号). id: `mis-…`.

- [ ] **Step 5: Свести в проект** (скрипт в scratchpad), проверить, закоммитить:

Run: `python3 scripts/dossiers.py && npm run build && python3 -m unittest discover -s test -t .`
Expected: ошибок нет, банк 440.

```bash
git add data/dossiers data/review/dossier-*.md
git commit -m "Досье «Мифы и легенды» и «Космос»: таблицы фактов (черновик до сверки)"
```

---

### Task 7: Этап 2 — сверка

- [ ] **Step 1: Спросить автора о запуске сверщика** (обе таблицы).
- [ ] **Step 2: Сверщик** — задание как в пилоте (каждый источник заново, цитата дословна, факты и даты, подписи, ложные срабатывания `ru`, `olympiad`) плюс: ссылки `ref`/`from` указывают на того самого персонажа; названия `name` дословно совпадают с олимпиадными вариантами встраиваемых вопросов; даты недавней лунной программы — по официальным сообщениям. Результат `verify.json` (ok / fix / remove).
- [ ] **Step 3: Применить исправления, проверить, закоммитить** (`CHANGELOG.md` — строка о сверке).

Run: `python3 scripts/dossiers.py && npm run build && python3 -m unittest discover -s test -t .`
Expected: ошибок нет.

---

### Task 8: Этап 3 — писатель

- [ ] **Step 1: Скрипт проверки черновика** `scratchpad/myths/check_questions.py <досье> <файл вопросов> [<отчёт>]` — `validate_questions` для одного досье + `validate_links` + `cross_leak_errors` по всем досье (файлы остальных — из проекта), отчёт `dossier_report(…, bank)`.
- [ ] **Step 2: Спросить автора о запуске писателя.**
- [ ] **Step 3: Писатель** — задание как в пилоте плюс:
  - встраивания: для каждой записи из `embed-targets.json` — вопрос `embeds` (`fact` с `table`/`row`/`ask`, при нужде `where`/`exclude`); если пояснение записи называет неверный вариант — предложить новое пояснение (3–5 предложений, только о правильном ответе) в отдельный файл `editorial-proposals.json` `{id: {"reason": …, "explanation": …}}`;
  - новые вопросы: «Мифы и легенды» ≈ 15, «Космос» ≈ 12, из них мостики (`namesake`) ≈ 4–5; не повторять встраиваемые;
  - всё — `status: "draft"`, без `check`; проверка — `check_questions.py`.
- [ ] **Step 4: Положить вопросы и правки пояснений в проект** (`editorial.json` — с `reason` «пояснение называло неверные варианты: вопрос встроен в досье с общим набором»), проверить, закоммитить.

Run: `python3 scripts/dossiers.py && npm run build && python3 -m unittest discover -s test -t .`
Expected: ошибок нет; черновики в банк не попали (банк 440).

---

### Task 9: Этап 4 — проверяющий

- [ ] **Step 1: Спросить автора о запуске проверяющего** (и о передаче его правок писателю на согласование).
- [ ] **Step 2: Проверяющий** — задание как в пилоте; для встраиваний: олимпиадный вопрос с расширенным набором — нет ли среди добавленных вариантов второго верного ответа (это главное), подписи исходных вариантов верны, новое пояснение верно. Вердикты — `check.json`.
- [ ] **Step 3: Согласование с писателем** (`writer-response.json`), применить согласованное, разногласия — в список для автора; проверить, закоммитить.

Run: `python3 scripts/dossiers.py && npm run build && python3 -m unittest discover -s test -t .`
Expected: ошибок нет.

---

### Task 10: Этап 5 — решение автора, слияние

- [ ] **Step 1: Показать автору отчёты** `data/review/dossier-myths.md`, `dossier-space.md`: новые вопросы (вопрос → ответ) и встраивания (олимпиадный вопрос → ответ, сколько вариантов добавлено), спорное.
- [ ] **Step 2: Применить решение:** принятые — `status: "accepted"`; отклонённые — удалить, причина — в `CHANGELOG.md`.
- [ ] **Step 3: Собрать и прогнать всё**

Run: `npm run build && python3 scripts/dossiers.py && python3 -m unittest discover -s test -t . && node --test test/*.test.mjs`
Expected: банк = 440 + новые принятые (встраивания число записей не меняют); все тесты зелёные, браузерный не пропущен; `test_accepted_embeds_reach_the_bank` проверил каждое встраивание.

- [ ] **Step 4: Итог** — `CHANGELOG.md` и абзац в `docs/ideas/2026-10-13-question-bank-ideas.md`; коммит; вопрос автору о ревью; после ответа — ревью, исправления, fast-forward master, `git push origin master`.
