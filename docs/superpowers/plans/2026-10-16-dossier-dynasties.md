# Досье «Династии и правители»: план

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** досье «Династии и правители» (`data/dossiers/dynasties.json`) с проверенными таблицами,
около 15 новыми вопросами и встраиванием до 20 олимпиадных вопросов. Итог — приёмка автором и
слияние в master.

**Architecture:** новый код не нужен: система досье готова. Работа — пустое досье в сборке (одна
правка теста) и пять содержательных этапов с агентами: сборщики → сверщики → писатели →
проверяющие → автор. Те же скрипты рабочей папки, что у «Праздников» (`check_rows.py`,
`check_questions.py`), с новым досье.

**Tech Stack:** Python 3 (`scripts/dossiers.py`, `scripts/embeds.py`, `scripts/merge_bank.py`),
JSON, Node (`npm run build`, `node --test`).

**Spec:** `docs/superpowers/specs/2026-10-16-dossier-dynasties-design.md` (общие правила — спецификации
досье «Деньги», «Мифы и Космос», «Праздники» в `docs/superpowers/specs/`).

## Global Constraints

- Вопрос по-русски, варианты по-китайски; правки готовых записей — только через `data/review/editorial.json` с `reason`.
- id вопросов (`dynasties-qNN`), строк и исходных вариантов олимпиады не меняются после принятия; текст варианта меняется только через `editorial.json` (`options`).
- У строки — не меньше двух официальных или академических источников с дословной цитатой; Википедия — не источник.
- `country` — 中国 или 俄罗斯 (без `ru`); доля вопросов — около 70 % Китай, 30 % Россия.
- id строк с префиксом таблицы: `dyn-`, `rul-` (`rul-ru-` у российских).
- Колонки названия династии: `name` (秦), `chao` (秦朝), `dai` (秦代); вопрос берёт набор из колонки своей формы.
- Одно написание имени русского правителя — по китайским официальным источникам; олимпиадные варианты с другим приводятся к нему в `editorial.json`, `reason`: «одно написание имени для досье; так пишут китайские официальные источники».
- `ru` — названия от шести букв или из двух слов («династия Цинь», «император Канси»).
- Каждый запуск агентов — с согласия автора (число агентов назначает автор).
- В HTTP-запросах агентов — никаких личных данных, только обезличенный User-Agent.
- Каждое заметное изменение — запись в `CHANGELOG.md` в том же коммите.
- Слияние: вопрос автору о ревью; master — `git push origin feat/dossier-dynasties:master` и `git fetch origin master:master`, основную копию репозитория не трогать; если master ушёл вперёд — сначала `sync_with_base_branch`.

## Review Focus

Автоматика сборки этого не ловит; каждую строку проверяет проверяющий (Task 5) и ревью перед слиянием:

1. Второй верный ответ по традиционным датировкам и спорной периодизации: «самая ранняя династия» (夏 и легендарные правители), «первая централизованная» (秦 и 西周), «последняя феодальная» (清 и 中华民国 не династия), Вёсны и Осени (东周 и 周).
2. Подсказка формой: ответ один выделяется видом — 皇帝 в имени (崇祯皇帝), точка «·» в транслитерации, 大帝, число 二世 среди имён без числа; одиночный иероглиф среди двусложных названий.
3. Настоящая подсказка из вопросов банка вне досье: «терракотовая армия императора Цинь Шихуана» (2016-17-shk-4), «основан Петром I» (2020-21-pri-q4e8b0e), «по приказу Петра I» (2025-26-zak-q387588, 2018-19-zak-7) — группа в `fact-groups.json` при принятии, если подсказка в тексте.
4. Правка написания имени (伊凡 / 伊万) в `editorial.json` меняет текст варианта у нескольких записей: подписи в `glosses.json` с копией старого `zh` остановят сборку — их нужно править вместе.
5. Российский вопрос, где ответ находится отсевом (единственная женщина, единственный «大帝», единственный князь среди императоров), — урок «Мифов» и «Праздников».

---

### Task 1: Пустое досье в сборке

**Files:**
- Create: `data/dossiers/dynasties.json`, `data/dossiers/dynasties-questions.json`
- Modify: `test/test_dossiers.py` (тест `test_all_dossiers_are_part_of_the_build`)
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `dossier_paths(directory)` и `check_dossiers(...)` из `scripts/dossiers.py`.
- Produces: таблицы `dynasties`, `rulers` с колонками ниже — их заполняют Task 2–3.

- [ ] **Step 1: Тест ждёт новое досье**

```python
    def test_all_dossiers_are_part_of_the_build(self):
        names = {table.name for table, _ in self.pairs}
        self.assertEqual(names, {'money.json', 'myths.json', 'space.json', 'holidays.json', 'dynasties.json'})
```

- [ ] **Step 2: Тест падает**

Run: `python3 -m unittest test.test_dossiers -k test_all_dossiers_are_part_of_the_build`
Expected: FAIL — в наборе нет `dynasties.json`.

- [ ] **Step 3: Пустое досье**

`data/dossiers/dynasties.json`:

```json
{
  "id": "dynasties",
  "title": "Династии и правители",
  "tables": {
    "dynasties": {
      "columns": {
        "name": "zh",
        "chao": "zh",
        "dai": "zh",
        "country": "zh",
        "founder": "zh",
        "capital": "zh",
        "people": "zh",
        "about": "ru"
      },
      "rows": []
    },
    "rulers": {
      "columns": {
        "name": "zh",
        "country": "zh",
        "dynasty": "zh",
        "role": "ru"
      },
      "rows": []
    }
  }
}
```

`data/dossiers/dynasties-questions.json`: `[]`

- [ ] **Step 4: Тесты и проверки зелёные**

Run: `python3 -m unittest discover -s test -t . && python3 scripts/dossiers.py && npm run build`
Expected: OK; `dynasties: строк 0, вопросов 0, принято 0`; `ошибок нет`; банк 488.

- [ ] **Step 5: Коммит** — строка в `CHANGELOG.md` (раздел спецификации): «Пустое досье `dynasties` (таблицы `dynasties`, `rulers`) в сборке».

```bash
git add data/dossiers/dynasties.json data/dossiers/dynasties-questions.json data/review/dossier-dynasties.md test/test_dossiers.py CHANGELOG.md
git commit -m "Досье «Династии и правители»: пустые таблицы в сборке"
```

---

### Task 2: Этап 1 — сборщики

**Files:**
- Create (рабочая папка `<scratchpad>/dynasties/`): `embed-targets.json`, `check_rows.py`, `brief-common.md`, `drafts/*.json`
- Modify: `data/dossiers/dynasties.json`, `CHANGELOG.md`

- [ ] **Step 1: `embed-targets.json`** — 20 записей из таблицы «Встраивание» спецификации, тем же скриптом, что у «Праздников» (`<scratchpad>/holidays/embed-targets.json`), со словарём:

```python
targets = {
  '2015-16-mun-1': 'dynasties.name', '2015-16-mun-6': 'dynasties.dai', '2015-16-shk-61': 'dynasties.chao',
  '2015-16-zak-4': 'dynasties.chao', '2017-18-mun-3': 'dynasties.dai', '2018-19-zak-10': 'dynasties.chao',
  '2020-21-reg-q55effb': 'dynasties.name', 'addition-b1-06': 'dynasties.capital',
  '2015-16-shk-59': 'rulers.name', '2019-20-mun-qe6c5d3': 'rulers.name', '2022-23-shk-qa664f6': 'rulers.name',
  'addition-b1-07': 'rulers.name', '2019-20-reg-1': 'rulers.name', '2020-21-pri-q59b606': 'rulers.name',
  '2020-21-zak-qdf339a': 'rulers.name', '2022-23-shk-qde2687': 'rulers.name', '2023-24-mun-35': 'rulers.name',
  '2025-26-mun-4': 'rulers.name', '2025-26-reg-9': 'rulers.name', 'addition-b2-16': 'rulers.name'}
```

- [ ] **Step 2: `check_rows.py`** — копия `<scratchpad>/holidays/check_rows.py` для досье `dynasties`. Части таблиц:
  - `dynasties` — `drafts/dynasties.json`;
  - `rulers` — `drafts/rulers-china.json` и `drafts/rulers-russia.json`.

  Список «встраивание — пока нет ячеек» сравнивает варианты с ячейками. Варианты, которые писатель приведёт к одному написанию, должны совпасть хотя бы по выбранной форме: сборщик называет её в отчёте. Проверка: пустой черновик `[]` даёт «ошибок нет».
- [ ] **Step 3: `brief-common.md`** — по образцу `<scratchpad>/holidays/brief-common.md`, плюс:
  - три колонки названия;
  - одно написание имени и отчёт о расхождениях с олимпиадой;
  - строки для неверных вариантов-«чужаков» (陈毅);
  - `ref` founder → `rulers`, dynasty → `dynasties`;
  - годы «до н. э.», традиционные датировки с оговоркой.
- [ ] **Step 4: Спросить автора о запуске** — предложить 3 сборщиков:
  1. `dynasties` (Китай и две российские династии);
  2. `rulers`, Китай;
  3. `rulers`, Россия.
- [ ] **Step 5: Свести черновики, проверить**

Run: `python3 scripts/dossiers.py && npm run build && python3 -m unittest discover -s test -t .`
Expected: ошибок нет; банк 488. Встраиваемые вопросы, у которых нет ячеек для вариантов, — перечислить в `CHANGELOG.md` и в отчёте автору.

- [ ] **Step 6: Коммит** — «Досье «Династии и правители»: таблицы фактов (черновик до сверки)».

---

### Task 3: Этап 2 — сверка

- [ ] **Step 1: Спросить автора о запуске** — 2 сверщика: `dynasties` и `rulers`.
- [ ] **Step 2: Сверщики** — задание по образцу `<scratchpad>/holidays/brief-verify.md`, плюс:
  - даты династий и правлений;
  - форма названия: есть ли `chao` / `dai` в источниках;
  - выбранное написание имени — по китайским официальным источникам;
  - подписи не делают вариант вторым верным ответом в 20 встраиваниях (Review Focus 1).

  Результат — `verify-dynasties.json`, `verify-rulers.json`.
- [ ] **Step 3: Применить** тем же скриптом, что в «Праздниках»: поле = значение, `null` удаляет, `remove` убирает строку, у каждой строки есть вердикт.

Run: `python3 scripts/dossiers.py && npm run build && python3 -m unittest discover -s test -t .`
Expected: ошибок нет.

- [ ] **Step 4: Коммит** с записью в `CHANGELOG.md`.

---

### Task 4: Этап 3 — писатели

- [ ] **Step 1: Скрипт проверки черновика** — копия `<scratchpad>/holidays/check_questions.py` для `dynasties`:
  - склеивает `dynasties-china.json` и `dynasties-russia.json` или берёт `dynasties-questions.json`;
  - подставляет `explanation` и `options` из `dynasties-editorial.json` в записи банка.

  Проверка: пустой черновик даёт «ошибок нет».
- [ ] **Step 2: Спросить автора о запуске** — 2 писателя:
  - Китай со встраиваниями о Китае;
  - Россия со встраиваниями о России.
- [ ] **Step 3: Писатели** — задание по образцу `<scratchpad>/holidays/brief-writer.md`, плюс:
  - 20 встраиваний (`where country`, однородная колонка);
  - около 15 новых (в основном о Китае, «что раньше» — явными `options`);
  - мост 康熙 ↔ 彼得大帝;
  - правки написания имён и пояснений — в `dynasties-editorial.json`;
  - Review Focus 1, 2, 5 — проверить у каждого вопроса.
- [ ] **Step 4: Положить в проект**
  - Вопросы — `draft`.
  - `editorial.json` — пояснения и `options`.
  - Если правка написания затрагивает подписи `glosses.json` (Review Focus 4) — поправить и их.

Run: `npm run build && python3 scripts/dossiers.py && python3 -m unittest discover -s test -t .`
Expected: ошибок нет; банк 488.

- [ ] **Step 5: Коммит** с записью в `CHANGELOG.md`.

---

### Task 5: Этап 4 — проверяющие

- [ ] **Step 1: Спросить автора о запуске** — число по объёму, около 4: встраивания Китай, встраивания Россия, новые Китай, новые Россия.
- [ ] **Step 2: Проверяющие** — задание по образцу `<scratchpad>/holidays/brief-checker.md`; все пять пунктов Review Focus обязательны. Вердикты — в `check-<N>/dynasties-check.json`.
- [ ] **Step 3: Согласование с писателями**
  - Свести скриптом. Копия проверяющего = исходный файл + `proposed`.
  - Правки таблицы внести самому.
  - Группы фактов отметить для Task 6: группа ссылается на записи банка.

Run: `npm run build && python3 scripts/dossiers.py && python3 -m unittest discover -s test -t . && node --test test/*.test.mjs`
Expected: ошибок нет, все тесты зелёные.

- [ ] **Step 4: Коммит** с записью в `CHANGELOG.md`.

---

### Task 6: Этап 5 — решение автора, слияние

- [ ] **Step 1: Список на приёмку** — вопрос → ответ, у встраиваний — сколько вариантов добавлено. Отчёт: `data/review/dossier-dynasties.md`.
- [ ] **Step 2: Применить решение автора**
  - Принятые: `status: "accepted"`, `check: {"verdict": "accept", "note": …}`.
  - Группы фактов — в `data/review/fact-groups.json`. У записи с общим набором вариантов (`merges.json` с `distractors: pool`) группы не бывает.
  - Подписи `glosses.json` встроенных записей — убрать.
  - Отклонённые — удалить, причину записать в CHANGELOG.
- [ ] **Step 3: Собрать и прогнать всё**

Run: `npm run build && python3 scripts/dossiers.py && python3 -m unittest discover -s test -t . && node --test test/*.test.mjs`
Expected:
- банк = 488 + новые принятые;
- все тесты зелёные, браузерный не пропущен.

- [ ] **Step 4: Итог** — `CHANGELOG.md` и абзац «Итог досье «Династии и правители»» в `docs/ideas/2026-10-13-question-bank-ideas.md`; коммит.
- [ ] **Step 5: Слияние**
  1. Спросить автора о ревью и одной строкой сказать, что в ветке.
  2. Если ревью нужно — ревью и исправления.
  3. Если master ушёл вперёд — `sync_with_base_branch`, свести конфликты, пересобрать, прогнать всё.
  4. Отправить:

```bash
git push origin feat/dossier-dynasties:master
git fetch origin master:master
```
