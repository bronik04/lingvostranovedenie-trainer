# Досье «Праздники»: план

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** досье «Праздники» (`data/dossiers/holidays.json`) с проверенными таблицами, около 15
новыми вопросами и встраиванием 13 олимпиадных вопросов о праздниках — до приёмки автором и
слияния в master.

**Architecture:** новый код не нужен. Система досье (таблицы, вопросы, встраивание, ссылки,
утечки между досье) готова и покрыта тестами. Работа — пустое досье в сборке (одна правка теста) и
пять содержательных этапов с агентами: сборщики → сверщик → писатель → проверяющий → автор.

**Tech Stack:** Python 3 (`scripts/dossiers.py`, `scripts/embeds.py`, `scripts/merge_bank.py`),
JSON-данные, Node (сборка `npm run build`, тесты `node --test`).

**Spec:** `docs/superpowers/specs/2026-10-15-dossier-holidays-design.md` (общие правила —
`docs/superpowers/specs/2026-10-14-dossier-money-pilot-design.md`,
`docs/superpowers/specs/2026-10-15-dossiers-myths-space-design.md`).

## Global Constraints

- Вопрос по-русски, варианты по-китайски. Правки готовых записей — только через `data/review/editorial.json` с `reason`.
- id вопросов (`holidays-qNN`), id строк и id исходных вариантов олимпиады не меняются после принятия.
- У строки — не меньше двух официальных или академических источников с дословной цитатой; Википедия — не источник.
- `country` — 中国, 俄罗斯 или 国际 (без `ru`); доля вопросов — около 70 % Китай, 30 % Россия.
- id строк с префиксом таблицы: `hol-`, `cus-`, `fig-`.
- `ru` — названия от шести букв или из двух слов («праздник Циси», «Праздник фонарей»).
- Даты китайскими цифрами: лунные без 日 и без 农历 (五月初五, 八月十五), солнечные с 日 (四月五日).
- Подвижные даты (Пасха, Масленица) — без ячейки `date`, о дате не спрашивают.
- Каждый запуск агентов — с согласия автора: сколько и зачем; одновременно не больше трёх (больше — только по прямому разрешению автора).
- В HTTP-запросах агентов — никаких личных данных, только обезличенный User-Agent.
- Каждое заметное изменение — запись в `CHANGELOG.md` в том же коммите.
- Слияние: вопрос автору о ревью; master обновлять через `git push origin feat/dossier-holidays:master` и `git fetch origin master:master`, не трогая основную копию репозитория (там может стоять ветка другой сессии).

## Review Focus

Автоматика сборки этого не ловит; каждую строку проверяет проверяющий (Task 5) и ревью перед слиянием:

1. Подсказка формой в наборе названий: почти все названия кончаются на 节, а 七夕, 除夕, 小年, 那达慕, 三月三 — нет. Ответ без 节 среди вариантов с 节 (или наоборот) угадывается без знания.
2. Подсказка формой в датах: лунная дата (初, 正月, 腊月, без 日) среди солнечных (с 日) или наоборот.
3. Настоящая утечка с «Деньгами» и «Мифами», которую ссылка `ref` скрыла от проверки: оба вопроса могут попасть в один раунд — нужна группа в `fact-groups.json` (урок «Космоса», Ян Ливэй).
4. Российский вопрос с `where country=俄罗斯`, у которого меньше трёх неверных вариантов, или с китайскими вариантами, по которым ответ находится отсевом «всё китайское» (урок «Мифов», сказки).
5. Факты, которые устаревают или зависят от года (выходной с 2008 года, ЮНЕСКО 2009/2024, новые профессиональные праздники): в тексте вопроса или пояснения — с годом.

---

### Task 1: Пустое досье «Праздники» в сборке

**Files:**
- Create: `data/dossiers/holidays.json`, `data/dossiers/holidays-questions.json`
- Modify: `test/test_dossiers.py` (тест `test_all_dossiers_are_part_of_the_build`, около строки 772)
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `dossier_paths(directory)` и `check_dossiers(...)` из `scripts/dossiers.py` — находят все пары `<id>.json` + `<id>-questions.json`.
- Produces: таблицы `holidays`, `customs`, `figures` с колонками ниже — их заполняют Task 2–3.

- [ ] **Step 1: Тест ждёт новое досье**

В `test/test_dossiers.py`:

```python
    def test_all_dossiers_are_part_of_the_build(self):
        names = {table.name for table, _ in self.pairs}
        self.assertEqual(names, {'money.json', 'myths.json', 'space.json', 'holidays.json'})
```

- [ ] **Step 2: Тест падает**

Run: `python3 -m unittest test.test_dossiers -k test_all_dossiers_are_part_of_the_build`
Expected: FAIL — в наборе нет `holidays.json`.

- [ ] **Step 3: Пустое досье**

`data/dossiers/holidays.json`:

```json
{
  "id": "holidays",
  "title": "Праздники",
  "tables": {
    "holidays": {
      "columns": {
        "name": "zh",
        "country": "zh",
        "kind": "zh",
        "date": "zh",
        "people": "zh",
        "legend": "zh",
        "origin": "ru"
      },
      "rows": []
    },
    "customs": {
      "columns": {
        "name": "zh",
        "kind": "zh",
        "holiday": "zh",
        "meaning": "ru"
      },
      "rows": []
    },
    "figures": {
      "columns": {
        "name": "zh",
        "holiday": "zh",
        "role": "ru"
      },
      "rows": []
    }
  }
}
```

`data/dossiers/holidays-questions.json`:

```json
[]
```

- [ ] **Step 4: Тесты и проверки зелёные**

Run: `python3 -m unittest discover -s test -t . && python3 scripts/dossiers.py && npm run build`
Expected: OK; `holidays: строк 0, вопросов 0, принято 0`; `ошибок нет`; банк 469.

- [ ] **Step 5: Коммит**

`CHANGELOG.md` — в раздел «Спецификация досье «Праздники»» строка: «Пустое досье `holidays` (таблицы `holidays`, `customs`, `figures`) в сборке».

```bash
git add data/dossiers/holidays.json data/dossiers/holidays-questions.json test/test_dossiers.py CHANGELOG.md
git commit -m "Досье «Праздники»: пустые таблицы в сборке"
```

---

### Task 2: Этап 1 — сборщики

**Files:**
- Create (рабочая папка `<scratchpad>/holidays/`, не в проекте): `brief-common.md`, `check_rows.py`, `drafts/*.json`, `embed-targets.json`
- Modify: `data/dossiers/holidays.json`, `CHANGELOG.md`

- [ ] **Step 1: `embed-targets.json`** — 13 записей из таблицы «Встраивание» спецификации: id, `questionRu`, варианты, ответ, пояснение, будущая таблица и колонка. Собрать скриптом из `data/bank.json`:

```bash
python3 - <<'EOF'
import json
bank = {r['id']: r for r in json.load(open('data/bank.json'))}
targets = {
  '2015-16-mun-8': 'holidays.name', '2015-16-reg-7': 'holidays.name', '2015-16-zak-10': 'holidays.date',
  '2016-17-shk-5': 'holidays.name', '2017-18-mun-1': 'holidays.name', '2017-18-mun-7': 'holidays.name',
  '2017-18-mun-9': 'customs.name', '2019-20-mun-q81216d': 'customs.name', '2021-22-shk-qfce22f': 'holidays.name',
  '2022-23-zak-5': 'holidays.name', '2023-24-shk-30': 'holidays.name', 'addition-b1-10': 'figures.name',
  'addition-b1-15': 'holidays.people'}
out = {}
for i, place in targets.items():
    r = bank[i]
    out[i] = {'place': place, 'questionRu': r['questionRu'],
              'answer': next(o['zh'] for o in r['options'] if o['id'] == r['answer']['optionId']),
              'options': [o['zh'] for o in r['options']], 'explanation': r['explanation']['ru']}
open('<scratchpad>/holidays/embed-targets.json', 'w').write(json.dumps(out, ensure_ascii=False, indent=1))
EOF
```

- [ ] **Step 2: `check_rows.py`** — копия `<scratchpad>/myths/check_rows.py`, где словарь частей таблиц — для `holidays` (`drafts/holidays-china-trad.json`, `holidays-china-modern.json`, `holidays-russia.json`), `customs` и `figures` (`drafts/customs-figures.json`). Проверка: на пустом черновике `[]` выводит «ошибок нет».
- [ ] **Step 3: Общее задание** `brief-common.md` — по образцу `<scratchpad>/myths/brief-common.md`. Добавить: формат дат (Global Constraints); названия вариантов олимпиады — дословно (`embed-targets.json`); строки для всех исходных вариантов встраиваемых вопросов (без ячейки вариант не получит подпись и вопрос не встроится); 国际 для 劳动节, 妇女节, 儿童节; `ref` в «Мифы», «Космос», «Деньги» (текст `name` совпадает с ячейкой цели); российских строк — не меньше пяти на колонку.
- [ ] **Step 4: Спросить автора о запуске** — 4 сборщика (решение автора по «Мифам»: по части на агента), или по очереди не больше трёх:
  1. Китай, традиционные и народности (`holidays`);
  2. Китай, современные и международные (`holidays`);
  3. Россия (`holidays` и российские `customs`);
  4. `customs` (китайские) и `figures`.
- [ ] **Step 5: Свести черновики в `holidays.json`, проверить**

Run: `python3 scripts/dossiers.py && npm run build && python3 -m unittest discover -s test -t .`
Expected: ошибок нет; банк 469 (вопросов ещё нет).

Кроме того, по таблице «Встраивание» убедиться: у каждого из 13 вопросов есть ячейки всех исходных вариантов. Вопросы, у которых их нет, перечислить в CHANGELOG и отчёте автору.

- [ ] **Step 6: Коммит** — «Досье «Праздники»: таблицы фактов (черновик до сверки)», строка в `CHANGELOG.md`: сколько строк по таблицам, сколько российских, какие варианты не подтвердились.

---

### Task 3: Этап 2 — сверка

- [ ] **Step 1: Спросить автора о запуске сверщика** (1 агент; при большом объёме — 2, по таблицам).
- [ ] **Step 2: Сверщик** — как в «Мифах» (`<scratchpad>/myths/verify-*.json`):
  - каждый источник заново, цитата дословна;
  - факты и даты, формат дат;
  - подписи: ≤ 90 знаков, одна строка, не делают вариант вторым верным ответом;
  - ложные срабатывания `ru`;
  - `olympiad`;
  - `ref` ведёт на ту самую строку.

  Результат — `verify.json` (ok / fix / remove), формат `{table, row, verdict, checked, problems, fix}`; `fix` — новые значения полей, `null` убирает ячейку.
- [ ] **Step 3: Применить** — тем же скриптом, что в «Мифах»: поле = значение, `null` удаляет, `remove` убирает строку. Убедиться, что ни одна строка не осталась без вердикта.

Run: `python3 scripts/dossiers.py && npm run build && python3 -m unittest discover -s test -t .`
Expected: ошибок нет.

- [ ] **Step 4: Коммит** с записью в `CHANGELOG.md` — «Сверка таблиц «Праздников»»: итог ok / fix / remove и главное по правкам.

---

### Task 4: Этап 3 — писатель

- [ ] **Step 1: Скрипт проверки черновика** — копия `<scratchpad>/myths/check_questions.py` (подставляет черновики из папки, `check_dossiers` по всем досье, `--report`). Проверка: пустой черновик даёт «ошибок нет».
- [ ] **Step 2: Спросить автора о запуске писателя** (1 агент или 2 — Китай и Россия).
- [ ] **Step 3: Писатель** — задание по образцу `<scratchpad>/myths/brief-writer.md`, плюс:
  - 13 встраиваний: `fact` с `where`/`exclude`, чтобы ни один добавленный вариант не стал вторым верным ответом. 2022-23-zak-5 — набор только из традиционных праздников через `exclude`;
  - около 15 новых вопросов, около 9 о России;
  - стороны из раздела «Вопросы» спецификации; зеркальные пары — двумя вопросами;
  - не спрашивать подвижные даты;
  - Review Focus, пункты 1 и 2, — проверить у каждого вопроса;
  - предложения пояснений — в `holidays-editorial.json`.
- [ ] **Step 4: Положить в проект**
  - Вопросы — в `data/dossiers/holidays-questions.json` (`draft`).
  - Пояснения — в `editorial.json`.
  - Правка варианта 2015-16-zak-10 в `editorial.json`: `"2015-16-zak-10": {"reason": "Лунная дата записана как солнечная; приведено к записи лунных дат досье", "options": {"o3": "八月十五"}}` (формат — как у 2015-16-shk-58; id варианта не меняется).

Run: `npm run build && python3 scripts/dossiers.py && python3 -m unittest discover -s test -t .`
Expected: ошибок нет; банк 469 (черновики в банк не идут).

- [ ] **Step 5: Коммит** с записью в `CHANGELOG.md`.

---

### Task 5: Этап 4 — проверяющий

- [ ] **Step 1: Спросить автора о запуске проверяющего** и о передаче его правок писателю на согласование.
- [ ] **Step 2: Проверяющий** — задание по образцу `<scratchpad>/myths/brief-checker.md`; все пять пунктов Review Focus — обязательные. Вердикты — `holidays-check.json`, правки — на копии вопросов.
- [ ] **Step 3: Согласование** — писатель отвечает `holidays-writer-response.json`.
  - Принятое — перенести.
  - Перед переносом сверить скриптом: копия проверяющего = исходный файл + `proposed`. У принятых вопросов копия не изменилась.
  - Правки таблицы, о которых сказал проверяющий, внести самому.
  - Разногласия — в список для автора.

Run: `npm run build && python3 scripts/dossiers.py && python3 -m unittest discover -s test -t . && node --test test/*.test.mjs`
Expected: ошибок нет, все тесты зелёные.

- [ ] **Step 4: Коммит** с записью в `CHANGELOG.md`.

---

### Task 6: Этап 5 — решение автора, слияние

- [ ] **Step 1: Список на приёмку** — вопрос → ответ; у встраиваний — сколько вариантов добавлено. Отчёт: `data/review/dossier-holidays.md`.
- [ ] **Step 2: Применить решение автора**
  - Принятые: `status: "accepted"`, `check: {"verdict": "accept", "note": "…"}`; у исправленных `note` начинается с «Исправлено по проверке, писатель согласен.».
  - Отклонённые — удалить, причину записать в `CHANGELOG.md`.
- [ ] **Step 3: Собрать и прогнать всё**

Run: `npm run build && python3 scripts/dossiers.py && python3 -m unittest discover -s test -t . && node --test test/*.test.mjs`
Expected:
- банк = 469 + новые принятые (встраивания записей не добавляют);
- все тесты зелёные, браузерный тест не пропущен;
- `DossierInBank` проверил встраивания.

- [ ] **Step 4: Итог и коммит** — запись в `CHANGELOG.md`, абзац «Итог досье «Праздники»» в `docs/ideas/2026-10-13-question-bank-ideas.md`, в «Источниках тем» отметить праздники курса.
- [ ] **Step 5: Слияние**
  1. Спросить автора о ревью и одной строкой сказать, что в ветке.
  2. Если ревью нужно — ревью и исправления.
  3. Если master ушёл вперёд — `sync_with_base_branch`, свести конфликты, пересобрать `dist`, прогнать всё.
  4. Отправить:

```bash
git push origin feat/dossier-holidays:master
git fetch origin master:master
```
