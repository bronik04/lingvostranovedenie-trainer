# Подписи к неверным вариантам — план реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** под неверными вариантами после ответа показывать короткую подпись «что это такое», начиная с пилота на теме «История и государство».

**Architecture:** новый слой `data/review/glosses.json` + `scripts/glosses.py` накладывается в `merge_bank.py` последним, после правок; подпись попадает в банк как `options[i].gloss`. Интерфейс берёт подписи чистой функцией `optionGlosses` из `src/quiz.mjs`. Содержимое пилота пишется и сверяется вне репозитория, проходит проверку автора на странице проверки и только потом попадает в `glosses.json`.

**Tech Stack:** Python 3 (stdlib, unittest), ванильный JS в одном HTML, node:test, playwright-core + системный Chrome для `test/ui.test.mjs`.

## Global Constraints

- Спецификация: `docs/superpowers/specs/2026-09-25-distractor-glosses-design.md`.
- Подпись: одна строка по-русски, не длиннее 90 символов, без «— —» и двойных пробелов; только у неверных вариантов; необязательна.
- У подписи обязателен источник `{title, url}` с HTTP(S)-ссылкой; в интерфейсе не показывается.
- `zh` в подписи — копия текущего текста варианта; расхождение останавливает сборку.
- `data/bank.json` руками не править; каждое заметное изменение — запись в `CHANGELOG.md`.
- Тесты: `python3 -m unittest discover -s test -t .` и `node --test test/*.test.mjs` (глоб без кавычек).
- Перед слиянием в `master` — ревью ветки отдельным агентом (правило автора), найденное чинится в той же ветке.
- В проект попадают только подписи, принятые автором.

---

### Task 1: Слой подписей в данных

**Files:**
- Create: `scripts/glosses.py`
- Create: `data/review/glosses.json` (содержимое `{}`)
- Create: `test/test_glosses.py`
- Modify: `scripts/merge_bank.py` (импорт и вызов после `apply_editorial` и проверки дополнений)
- Modify: `CLAUDE.md` (правило про подписи), `CHANGELOG.md`

**Interfaces:**
- Produces: `load_glosses(path: Path) -> dict[str, dict]`, `validate_glosses(glosses: object, bank: list[dict]) -> list[str]`, `apply_glosses(bank: list[dict], glosses: dict) -> list[dict]`; в банке у варианта появляется необязательное поле `gloss: str`.

- [ ] **Step 1: Написать падающие тесты** — `test/test_glosses.py`:

```python
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from glosses import apply_glosses, validate_glosses


def record(**overrides):
    item = {
        'id': '2015-16-zak-4',
        'questionRu': 'Как называлась первая единая централизованная феодальная династия в истории Китая?',
        'options': [{'id': 'o1', 'zh': '秦朝'}, {'id': 'o2', 'zh': '汉朝'},
                    {'id': 'o3', 'zh': '明朝'}, {'id': 'o4', 'zh': '夏朝'}],
        'answer': {'optionId': 'o1', 'state': 'verified'},
    }
    item.update(overrides)
    return item


def gloss(zh='汉朝', ru='Династия Хань, 206 г. до н. э. — 220 г.', **overrides):
    item = {'zh': zh, 'ru': ru, 'source': {'title': '汉朝 — 百科', 'url': 'https://example.org/han'}}
    item.update(overrides)
    return item


def entry(options):
    return {'reviewedAt': '2026-09-25', 'options': options}


class GlossesTest(unittest.TestCase):
    def test_puts_gloss_into_the_option(self):
        [result] = apply_glosses([record()], {'2015-16-zak-4': entry({'o2': gloss()})})
        self.assertEqual(result['options'][1], {'id': 'o2', 'zh': '汉朝',
                                                'gloss': 'Династия Хань, 206 г. до н. э. — 220 г.'})
        self.assertNotIn('gloss', result['options'][0])

    def test_keeps_untouched_records(self):
        other = record(id='other')
        result = apply_glosses([record(), other], {'2015-16-zak-4': entry({'o2': gloss()})})
        self.assertIs(result[1], other)

    def test_rejects_invalid_glosses(self):
        bank = [record()]
        bad = [
            {'missing': entry({'o2': gloss()})},
            {'2015-16-zak-4': entry({'o9': gloss()})},
            {'2015-16-zak-4': entry({'o1': gloss(zh='秦朝', ru='Династия Цинь')})},
            {'2015-16-zak-4': entry({'o2': gloss(zh='汉代')})},
            {'2015-16-zak-4': entry({'o2': gloss(ru='Han dynasty')})},
            {'2015-16-zak-4': entry({'o2': gloss(ru='Династия ' + 'Хань ' * 20)})},
            {'2015-16-zak-4': entry({'o2': gloss(ru='Династия Хань — — 206')})},
            {'2015-16-zak-4': entry({'o2': gloss(ru='Династия  Хань')})},
            {'2015-16-zak-4': entry({'o2': gloss(source={'title': 'x', 'url': 'javascript:alert(1)'})})},
            {'2015-16-zak-4': entry({'o2': gloss(source={'title': ' ', 'url': 'https://example.org'})})},
            {'2015-16-zak-4': {'options': {'o2': gloss()}}},
            {'2015-16-zak-4': entry({})},
            [],
        ]
        for glosses in bad:
            self.assertTrue(validate_glosses(glosses, bank), glosses)
        self.assertEqual(validate_glosses({'2015-16-zak-4': entry({'o2': gloss()})}, bank), [])

    def test_changed_option_text_stops_the_build(self):
        with self.assertRaises(ValueError):
            apply_glosses([record()], {'2015-16-zak-4': entry({'o2': gloss(zh='汉代')})})


class GlossesInBankTest(unittest.TestCase):
    """Каждая подпись из data/review/glosses.json должна дойти до data/bank.json."""

    def test_every_gloss_reaches_the_bank(self):
        glosses = json.loads((ROOT / 'data/review/glosses.json').read_text('utf-8'))
        bank = {r['id']: r for r in json.loads((ROOT / 'data/bank.json').read_text('utf-8'))}
        for record_id, item in glosses.items():
            options = {o['id']: o for o in bank[record_id]['options']}
            for option_id, value in item['options'].items():
                self.assertEqual(options[option_id].get('gloss'), value['ru'], f'{record_id}/{option_id}')


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Убедиться, что тесты падают**

Run: `python3 -m unittest test.test_glosses -v`
Expected: `ModuleNotFoundError: No module named 'glosses'`

- [ ] **Step 3: Реализовать `scripts/glosses.py`**

```python
"""Подписи к неверным вариантам поверх собранного банка.

Подпись — одна строка по-русски о том, что такое неверный вариант: название и
один опознавательный факт. Она хранится вместе с копией текста варианта: если
вариант потом исправят через editorial.json, подпись перестанет совпадать, и
сборка остановится, чтобы подпись перепроверили, а не показали к другому тексту.
Источник подписи хранится для аудита и в интерфейс не попадает.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

MAX_LENGTH = 90
CYRILLIC = re.compile(r'[А-Яа-яЁё]')


def _source_ok(source: object) -> bool:
    if not isinstance(source, dict):
        return False
    url = urlparse(source.get('url') or '')
    title = source.get('title')
    return url.scheme in {'http', 'https'} and bool(url.netloc) and isinstance(title, str) and bool(title.strip())


def validate_glosses(glosses: object, bank: list[dict]) -> list[str]:
    if not isinstance(glosses, dict):
        return ['подписи должны быть словарём id → запись']
    errors: list[str] = []
    by_id = {record['id']: record for record in bank}
    for record_id, item in glosses.items():
        record = by_id.get(record_id)
        if record is None:
            errors.append(f'{record_id}: такой записи в банке нет')
            continue
        if not isinstance(item, dict):
            errors.append(f'{record_id}: запись подписей должна быть объектом')
            continue
        if not isinstance(item.get('reviewedAt'), str) or not item['reviewedAt'].strip():
            errors.append(f'{record_id}: нет даты проверки')
        options = item.get('options')
        if not isinstance(options, dict) or not options:
            errors.append(f'{record_id}: нет ни одной подписи')
            continue
        current = {option['id']: option['zh'] for option in record['options']}
        for option_id, gloss in options.items():
            where = f'{record_id}/{option_id}'
            if option_id not in current:
                errors.append(f'{where}: такого варианта нет')
                continue
            if option_id == record['answer']['optionId']:
                errors.append(f'{where}: подпись у правильного варианта')
            if not isinstance(gloss, dict):
                errors.append(f'{where}: подпись должна быть объектом')
                continue
            if gloss.get('zh') != current[option_id]:
                errors.append(f'{where}: вариант изменился ({gloss.get("zh")!r} → {current[option_id]!r}), '
                              'подпись нужно перепроверить')
            text = gloss.get('ru')
            if not isinstance(text, str) or not CYRILLIC.search(text):
                errors.append(f'{where}: подпись не по-русски')
            else:
                if len(text) > MAX_LENGTH:
                    errors.append(f'{where}: подпись длиннее {MAX_LENGTH} символов')
                if '— —' in text or '  ' in text or text != text.strip():
                    errors.append(f'{where}: двойное тире или лишние пробелы')
            if not _source_ok(gloss.get('source')):
                errors.append(f'{where}: нет источника с HTTP(S)-ссылкой и названием')
    return errors


def apply_glosses(bank: list[dict], glosses: dict[str, dict]) -> list[dict]:
    errors = validate_glosses(glosses, bank)
    if errors:
        raise ValueError('некорректные подписи к вариантам:\n - ' + '\n - '.join(errors))
    updated = []
    for record in bank:
        item = glosses.get(record['id'])
        if item is None:
            updated.append(record)
            continue
        updated.append({**record, 'options': [
            {**option, 'gloss': item['options'][option['id']]['ru']} if option['id'] in item['options'] else option
            for option in record['options']]})
    return updated


def load_glosses(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    glosses = json.loads(path.read_text('utf-8'))
    if not isinstance(glosses, dict):
        raise ValueError('подписи должны быть словарём id → запись')
    return glosses
```

Создать `data/review/glosses.json` с содержимым `{}` и переводом строки.

- [ ] **Step 4: Подключить слой в `scripts/merge_bank.py`**

Импорт рядом с остальными: `from glosses import apply_glosses, load_glosses`. После блока проверки дополнений (`validate_authored` … `raise ValueError`) и до `bank.sort(...)`:

```python
    # подписи к неверным вариантам — самым последним слоем: они сверяются с
    # текстом варианта уже после всех правок
    bank = apply_glosses(bank, load_glosses(ROOT / 'data/review/glosses.json'))
```

- [ ] **Step 5: Пересобрать банк и прогнать тесты**

Run: `python3 scripts/merge_bank.py && python3 scripts/taxonomy.py && python3 scripts/build_html.py && python3 -m unittest discover -s test -t . && node --test test/*.test.mjs`
Expected: банк 461 запись, `git diff data/bank.json` пуст (подписей ещё нет), все тесты OK.

- [ ] **Step 6: Документация**

В `CLAUDE.md` после правила про `editorial.json`:

```markdown
- Подписи к неверным вариантам — только в `data/review/glosses.json` и только принятые
  автором: одна строка по-русски, источник, копия текста варианта. Изменился вариант —
  сборка остановится, подпись нужно перепроверить.
```

В `CHANGELOG.md` — новый раздел `## 2026-09-25 — Подписи к неверным вариантам` с пунктом о слое данных.

- [ ] **Step 7: Commit**

```bash
git add scripts/glosses.py data/review/glosses.json test/test_glosses.py scripts/merge_bank.py CLAUDE.md CHANGELOG.md
git commit -m "Слой подписей к неверным вариантам"
```

---

### Task 2: Показ подписей в раунде и в базе

**Files:**
- Modify: `src/quiz.mjs` (новая `optionGlosses`)
- Modify: `src/quiz.ui.js` (`answer`, `appendDatabaseRows`)
- Modify: `src/quiz.css` (`.option-gloss`, `.row-glosses`)
- Test: `test/quiz.test.mjs`, `test/ui.test.mjs`
- Modify: `CHANGELOG.md`, `dist/lingvostranovedenie-trainer.html` (пересборка)

**Interfaces:**
- Consumes: поле `options[i].gloss` из Task 1.
- Produces: `optionGlosses(record) -> Array<{optionId: string, zh: string, gloss: string}>` — подписанные неверные варианты в исходном порядке.

- [ ] **Step 1: Падающий модульный тест** — в конец `test/quiz.test.mjs`:

```js
test('подписи берутся только у неверных вариантов, где они есть', () => {
  const withGlosses = record('g', {
    options: [
      { id: 'o1', zh: '广州', gloss: 'Гуанчжоу, центр провинции Гуандун' },
      { id: 'o2', zh: '上海', gloss: 'не должна показываться: это ответ' },
      { id: 'o3', zh: '北京' },
      { id: 'o4', zh: '西安', gloss: 'Сиань, древняя столица' },
    ],
  });
  assert.deepEqual(quiz.optionGlosses(withGlosses), [
    { optionId: 'o1', zh: '广州', gloss: 'Гуанчжоу, центр провинции Гуандун' },
    { optionId: 'o4', zh: '西安', gloss: 'Сиань, древняя столица' },
  ]);
  assert.deepEqual(quiz.optionGlosses(record('plain')), []);
});
```

Run: `node --test test/quiz.test.mjs` — Expected: FAIL, `quiz.optionGlosses is not a function`.

- [ ] **Step 2: Реализовать `optionGlosses`** — в `src/quiz.mjs` после `grade`:

```js
export function optionGlosses(record) {
  return record.options
    .filter((option) => option.id !== record.answer.optionId && option.gloss)
    .map((option) => ({ optionId: option.id, zh: option.zh, gloss: option.gloss }));
}
```

Run: `node --test test/quiz.test.mjs` — Expected: PASS.

- [ ] **Step 3: Падающий браузерный тест** — в `test/ui.test.mjs` перед тестом «тема…»:

```js
test('подписи появляются под неверными вариантами после ответа и в базе', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  // glosses.json в пилоте ещё пуст: подпись подкладывается в банк прямо на странице
  const record = await page.evaluate(() => {
    const target = QUESTION_BANK.find((r) => r.id === '2015-16-mun-1');
    const wrong = target.options.find((o) => o.id !== target.answer.optionId);
    wrong.gloss = 'Тестовая подпись к неверному варианту';
    startRoundWith([target]);
    return target;
  });
  assert.equal(await page.locator('.option-gloss').count(), 0, 'подпись видна до ответа');
  await page.locator(`#options button[data-option-id="${record.answer.optionId}"]`).click();
  const glossed = page.locator('.option-gloss');
  assert.equal(await glossed.count(), 1);
  assert.equal(await glossed.textContent(), 'Тестовая подпись к неверному варианту');
  const wrongId = record.options.find((o) => o.id !== record.answer.optionId).id;
  assert.equal(await page.locator(`#options button[data-option-id="${wrongId}"] .option-gloss`).count(), 1);

  await page.locator('#leaveRound').click();
  await page.locator('#openDatabase').click();
  await page.locator('#databaseSearch').fill(record.questionRu);
  const row = page.locator('#databaseList article').first();
  await row.locator('summary').click();
  assert.equal(await row.locator('.row-glosses li').isVisible(), true);
  assert.match(await row.locator('.row-glosses li').textContent(), /Тестовая подпись к неверному варианту/);
  assert.deepEqual(page.errors, []);
});
```

И в тесте «телефон…» перед `await startRound(page, 5);` подложить длинную подпись всем записям, чтобы проверить перенос:

```js
  await page.evaluate(() => {
    for (const r of QUESTION_BANK) {
      for (const o of r.options) if (o.id !== r.answer.optionId) o.gloss = 'Длинная подпись для проверки переноса на узком экране телефона';
    }
  });
```

Run: `python3 scripts/build_html.py && node --test test/ui.test.mjs` — Expected: новый тест FAIL (`.option-gloss` не появляется).

- [ ] **Step 4: Показ в раунде** — в `src/quiz.ui.js`, в `answer()` сразу после цикла, который ставит `✓ Верно` / `✕ Ваш ответ`:

```js
  for (const { optionId, gloss } of optionGlosses(record)) {
    const button = $('options').querySelector(`button[data-option-id="${optionId}"]`);
    const note = document.createElement('small');
    note.className = 'option-gloss';
    note.textContent = gloss;
    button.append(note);
  }
```

- [ ] **Step 5: Показ в базе** — в `appendDatabaseRows`, в массиве внутри `<details class="row-reveal">` после строки с `row-why`:

```js
        glossList(record),
```

и функция рядом с `evidenceList`:

```js
function glossList(record) {
  const items = optionGlosses(record);
  if (!items.length) return '';
  return '<p class="row-sources-title">Другие варианты</p><ul class="row-glosses">'
    + items.map(({ zh, gloss }) => `<li><span class="zh">${escapeHtml(zh)}</span> — ${escapeHtml(gloss)}</li>`).join('')
    + '</ul>';
}
```

- [ ] **Step 6: Стили** — в `src/quiz.css` после `.option.wrong .option-status`:

```css
.option-gloss { grid-column: 2 / -1; grid-row: 2; margin-top: -6px; color: var(--muted); font-size: .84rem; line-height: 1.35; }
.row-glosses { margin: 5px 0 0; padding-left: 18px; font-size: .88rem; }
```

и в медиазапросе телефона (рядом с `.option-status { grid-column: 2; }`):

```css
  .option-gloss { grid-column: 2; grid-row: auto; margin-top: 0; }
```

- [ ] **Step 7: Пересобрать и прогнать всё**

Run: `python3 scripts/build_html.py && python3 -m unittest discover -s test -t . && node --test test/*.test.mjs`
Expected: всё зелёное, включая оба изменённых браузерных теста.

- [ ] **Step 8: Скриншот для себя** — в браузерной вкладке открыть раунд с подложенной подписью (как в тесте) на ширине 1280 и 360 и убедиться глазами, что строка стоит под китайским текстом и не налезает на «✕ Ваш ответ».

- [ ] **Step 9: CHANGELOG и commit**

Пункт в разделе `2026-09-25`: показ подписей в раунде и в базе, пока без данных.

```bash
git add src/quiz.mjs src/quiz.ui.js src/quiz.css test/quiz.test.mjs test/ui.test.mjs CHANGELOG.md dist/lingvostranovedenie-trainer.html
git commit -m "Показывать подписи к неверным вариантам"
```

---

### Task 3: Ревью кода и слияние

- [ ] **Step 1:** отдельный агент-ревьюер читает `git diff master...feat/distractor-glosses` (ошибки, правила `CLAUDE.md`, документация, соседний код, тесты, которые проверяют не то). Ничего не меняет.
- [ ] **Step 2:** найденное исправить в той же ветке, прогнать оба набора тестов, запись в `CHANGELOG.md`.
- [ ] **Step 3:** `git checkout master && git merge --ff-only feat/distractor-glosses`.

---

### Task 4: Черновик подписей пилота

Вне репозитория, в `<scratchpad>/glosses/draft-*.json`, по одному файлу на часть темы.

- [ ] **Step 1:** выгрузить 74 записи темы «История и государство» из `data/bank.json` (id, `questionRu`, варианты, ответ, пояснение) в `<scratchpad>/glosses/input.json` и разбить на 3 части по ~25.
- [ ] **Step 2:** три агента параллельно пишут подписи по своей части. Для каждого неверного варианта — либо `{"zh", "ru", "source": {"title", "url"}, "quote"}`, где `quote` — дословная короткая цитата со страницы источника, подтверждающая факт, либо `{"zh", "skip": "причина"}`. Правила подписи — из спецификации; источники — энциклопедии (中国大百科全书, БРЭ, Baike, Википедия) и официальные сайты; ссылку агент открывает сам.
- [ ] **Step 3:** скрипт-проверка формата черновиков: те же правила, что `validate_glosses` (переиспользовать функцию на собранном из черновиков словаре), плюс непустая `quote` у каждой подписи.

### Task 5: Независимая сверка

- [ ] **Step 1:** отдельный агент (не писавший черновик) для каждой подписи открывает источник, ищет цитату, проверяет, что подпись следует из цитаты и относится именно к этому варианту (омонимы: 高祖, 太宗 и т. п.). Вердикт по каждой: `ok` / `fix: …` / `drop: …`.
- [ ] **Step 2:** применить вердикты: `fix` — поправить и перепроверить источник, `drop` — перевести вариант в `skip`.

### Task 6: Страница проверки

- [ ] **Step 1:** прочитать страницу (`Artifact` read), добавить вид карточки `gloss`: вопрос, варианты с отмеченным ответом, под неверными — подпись, источник-ссылка и цитата; для пропущенных — причина пропуска серым. Вкладка «Подписи к вариантам». Кнопки «Принять / Нужна правка / Отклонить» — `LABELS.gloss = LABELS.question`. Перед правкой загрузить `artifact-design`; при публикации `capabilities` не передавать (остаётся `db`).
- [ ] **Step 2:** записать 74 карточки в `items` одной-двумя пачками (`ArtifactData` batch, по 50): `id: gloss-<recordId>`, `kind: "gloss"`, `cat`: тема, `order`.
- [ ] **Step 3:** открыть страницу и проверить, что вкладка показывает карточки и решения сохраняются.
- [ ] **Step 4:** сообщить автору ссылку и что ждёт решения.

### Task 7: Принятые подписи в проект (после решения автора)

- [ ] **Step 1:** прочитать `decisions` (`gloss-*`). `yes` — взять как есть; `edit` — поправить по комментарию; `no` — не брать.
- [ ] **Step 2:** записать в `data/review/glosses.json` (`reviewedAt` — дата решения, без `quote`), пересобрать банк, тесты, `CHANGELOG.md`.
- [ ] **Step 3:** ревью ветки агентом, исправления, слияние.
