# Один вопрос с меняющимися неверными вариантами — план реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** записи одной группы «один факт» с одинаковым ответом становятся одним вопросом, у которого при каждом показе правильный вариант и три случайных неверных из общего набора; пилот — четыре группы.

**Architecture:** склейка `data/review/merges.json` получает пометку `"distractors": "pool"`: тот же код переносит появления, источники, `mergedIds` и официальные ключи, а варианты влитых записей добавляются к оставшейся как `o5`, `o6`… Раунд (`labelledOptions` в `src/quiz.mjs`) у записи с вариантами сверх четырёх берёт правильный и три случайных неверных. База вопросов показывает все варианты и метку «варианты меняются».

**Tech Stack:** Python 3 (stdlib, unittest), ванильный JS в одном HTML, node:test, playwright-core + системный Chrome для `test/ui.test.mjs`.

**Spec:** `docs/superpowers/specs/2026-10-13-distractor-pools-design.md`

## Global Constraints

- `data/bank.json` и `dist/` руками не править: только `npm run build`.
- `sources/` не редактировать.
- Формулировки, варианты, пояснения меняются только через `data/review/editorial.json` (ключ — итоговый id, обязательна `reason`).
- Вопрос по-русски, варианты по-китайски (проверяет сборка).
- Подпись к варианту: одна строка по-русски, источник, `zh` — копия текста варианта; переносится только принятая автором (существующие подписи копируются как есть).
- JSON-файлы слоёв пишутся `json.dumps(..., ensure_ascii=False, indent=2) + '\n'`; `glosses.json` — ещё и с `sort_keys=True`. Перед записью сверять, что чтение и запись исходного файла дают тот же текст.
- Тесты: `python3 -m unittest discover -s test -t .` и `node --test test/*.test.mjs` (глоб без кавычек). Браузерный тест без Chrome локально пропускается — убедиться, что он реально прошёл (`ℹ skipped 0`).
- Каждое заметное изменение — запись в `CHANGELOG.md`.
- Коммиты заканчиваются строкой `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Ветка `feat/distractor-pools`. Перед слиянием в `master` спросить автора, нужно ли ревью.
- `src/` параллельно переделывает сессия редизайна: правки в `src/` держать минимальными.

## Review Focus

- Прогресс ученика сохранён под несколькими влитыми id одной группы (у «Искусства войны» их три) → после загрузки он один, под оставшимся id, попытки сложены. Тест — Task 2.
- Запись с вариантами сверх четырёх, но без правильного варианта (ответ не проверен или id не найден) → раунд не падает и показывает первые четыре варианта. Тест — Task 2.
- Поиск в базе по неверному варианту, который есть только в общем наборе (阿Q正传) → находит объединённый вопрос. Тест — Task 2.
- Вопрос из общего набора попадает в обычный случайный раунд браузерного теста → помощники теста узнают его по части вариантов и отвечают неверно только показанным вариантом. Правка помощников — Task 2.
- Повтор ошибки в раунде показывает другие неверные варианты → проверка ответа идёт по `optionId`, правильный всегда на экране. Тест — Task 2 (много показов подряд).

---

### Task 1: Склейка с общим набором неверных вариантов

**Files:**
- Modify: `scripts/merges.py`
- Modify: `test/test_merges.py`
- Modify: `CLAUDE.md` (правило склейки)

**Interfaces:**
- Consumes: существующие `apply_merges(bank, merges)`, `validate_merges(merges, bank)`, `normalize_text` из `scripts/normalize.py`.
- Produces: запись `merges.json` может иметь поле `"distractors": "pool"`; у оставшейся записи `options` = её o1–o4 + новые неверные варианты влитых записей с id `o5`, `o6`… (следующий свободный `o<N>`). Сообщения об ошибках (тесты Task 1 ищут эти фрагменты):
  - `distractors может быть только "pool"`
  - `объединение не добавило новых неверных вариантов`
  - `пояснение называет неверный вариант`
  - `годы в вариантах записаны по-разному`

- [ ] **Step 1: Написать падающие тесты**

В `test/test_merges.py` после класса `OfficialKeyTest` добавить:

```python
def pooled(record_id, year, options, answer_text='拉萨', number=5, **overrides):
    """Тот же вопрос с другими неверными вариантами; правильный ответ — answer_text."""
    items = [{'id': f'o{index + 1}', 'zh': text} for index, text in enumerate(options)]
    answer = next(o['id'] for o in items if o['zh'] == answer_text)
    return record(record_id, year, number=number, options=items,
                  answer={'optionId': answer, 'state': 'verified'}, **overrides)


POOL = {'a': {'absorbs': ['b'], 'distractors': 'pool', 'reason': 'Тот же вопрос, другие неверные варианты'}}


def pool_pair():
    return [record('a', '2019-20'), pooled('b', '2022-23', ['成都', '北京', '拉萨', '重庆'])]


class PoolMergeTest(unittest.TestCase):
    def test_new_wrong_options_follow_the_kept_ones(self):
        merged = apply_merges(pool_pair(), POOL)
        self.assertEqual([r['id'] for r in merged], ['a'])
        self.assertEqual([(o['id'], o['zh']) for o in merged[0]['options']],
                         [('o1', '拉萨'), ('o2', '北京'), ('o3', '上海'), ('o4', '香港'),
                          ('o5', '成都'), ('o6', '重庆')])
        self.assertEqual(merged[0]['answer'], {'optionId': 'o1', 'state': 'verified'})
        self.assertEqual(merged[0]['mergedIds'], ['b'])

    def test_options_of_several_absorbed_records_are_added_once_in_absorbs_order(self):
        bank = [*pool_pair(), pooled('c', '2024-25', ['重庆', '拉萨', '西安', '成都'])]
        merges = {'a': {'absorbs': ['b', 'c'], 'distractors': 'pool', 'reason': 'r'}}
        merged = apply_merges(bank, merges)[0]
        self.assertEqual([o['zh'] for o in merged['options']],
                         ['拉萨', '北京', '上海', '香港', '成都', '重庆', '西安'])

    def test_new_option_ids_skip_ids_already_taken(self):
        bank = pool_pair()
        bank[0]['options'][3]['id'] = 'o5'       # у оставшейся записи уже есть o5
        merged = apply_merges(bank, POOL)[0]
        ids = [o['id'] for o in merged['options']]
        self.assertEqual(len(ids), len(set(ids)))

    def test_official_key_of_the_absorbed_record_points_at_the_kept_answer(self):
        bank = pool_pair()
        bank[1]['occurrences'][0]['officialKey'] = 'o3'          # 拉萨 во влитой записи
        merged = apply_merges(bank, POOL)[0]
        keys = {o['year']: o['officialKey'] for o in merged['occurrences']}
        self.assertEqual(keys['2022-23'], 'o1')

    def test_input_records_are_not_mutated(self):
        bank = pool_pair()
        apply_merges(bank, POOL)
        self.assertEqual(len(bank[0]['options']), 4)

    def test_rejects_different_answers(self):
        bank = [record('a', '2019-20'), pooled('b', '2022-23', ['成都', '北京', '拉萨', '重庆'], answer_text='成都')]
        self.assertRejectsPool(bank, 'ответ не совпадает')

    def test_rejects_a_pool_that_adds_nothing(self):
        self.assertRejectsPool(pair(), 'объединение не добавило новых неверных вариантов')

    def test_rejects_an_explanation_naming_a_wrong_option(self):
        bank = pool_pair()
        bank[0]['explanation'] = {'ru': 'Центр района — Лхаса (拉萨), а 成都 — центр Сычуани.'}
        self.assertRejectsPool(bank, 'пояснение называет неверный вариант 成都')

    def test_rejects_years_written_with_and_without_nian(self):
        years = ['2001', '1995', '2015', '1970']
        bank = [pooled('a', '2015-16', years, answer_text='2001', number=1),
                pooled('b', '2024-25', ['2010 年', '2001', '2011 年', '1991 年'], answer_text='2001')]
        self.assertRejectsPool(bank, 'годы в вариантах записаны по-разному')

    def test_accepts_years_written_the_same_way(self):
        bank = [pooled('a', '2015-16', ['2001 年', '1995 年', '2015 年', '1970 年'], answer_text='2001 年', number=1),
                pooled('b', '2024-25', ['2010 年', '2001 年', '2011 年', '1991 年'], answer_text='2001 年')]
        self.assertEqual(validate_merges(POOL, bank), [])

    def test_rejects_an_unknown_distractors_value(self):
        merges = {'a': {'absorbs': ['b'], 'distractors': 'union', 'reason': 'r'}}
        errors = validate_merges(merges, pool_pair())
        self.assertTrue(any('distractors может быть только "pool"' in e for e in errors), errors)

    def test_merge_without_the_flag_still_needs_the_same_options(self):
        merges = {'a': {'absorbs': ['b'], 'reason': 'r'}}
        errors = validate_merges(merges, pool_pair())
        self.assertTrue(any('варианты не совпадают' in e for e in errors), errors)

    def assertRejectsPool(self, bank, fragment):
        errors = validate_merges(POOL, bank)
        self.assertTrue(any(fragment in error for error in errors), f'{fragment!r} not in {errors}')
        with self.assertRaises(ValueError):
            apply_merges(bank, POOL)
```

- [ ] **Step 2: Убедиться, что тесты падают**

Run: `python3 -m unittest test.test_merges -v 2>&1 | tail -20`
Expected: FAIL/ERROR в `PoolMergeTest` (поле `distractors` сейчас «неизвестное», варианты не складываются).

- [ ] **Step 3: Реализовать объединение в `scripts/merges.py`**

В начало модуля (после `from pathlib import Path`) добавить `import re`. В докстринг модуля после первого абзаца добавить абзац:

```
С пометкой `"distractors": "pool"` склеиваются и записи с одинаковым ответом, но
разными неверными вариантами (олимпиада меняла обманки): неверные варианты влитых
записей добавляются к оставшейся как o5, o6…, и раунд каждый раз показывает
правильный и три случайных неверных.
```

Заменить константу и добавить помощников (после `ENTRY_FIELDS`):

```python
ENTRY_FIELDS = {'absorbs', 'reason', 'distractors'}
POOL = 'pool'
YEAR = re.compile(r'^\d{3,4}\s*(年)?$')


def _pooled_options(keep: dict, absorbed: list[dict]) -> list[dict]:
    """Варианты оставшейся записи и новые неверные варианты влитых, в порядке absorbs."""
    options = [dict(option) for option in keep['options']]
    known = {normalize_text(option['zh']) for option in options}
    taken = {option['id'] for option in options}
    number = len(options)
    for other in absorbed:
        for option in other['options']:
            text = normalize_text(option['zh'])
            if text in known:
                continue
            number += 1
            while f'o{number}' in taken:
                number += 1
            known.add(text)
            taken.add(f'o{number}')
            options.append({'id': f'o{number}', 'zh': option['zh']})
    return options


def _pool_errors(keep: dict, absorbed: list[dict]) -> list[str]:
    errors: list[str] = []
    options = _pooled_options(keep, absorbed)
    if len(options) == len(keep['options']):
        errors.append(f'{keep["id"]}: объединение не добавило новых неверных вариантов — '
                      'это обычная склейка, уберите "distractors"')
    explanation = keep.get('explanation', {}).get('ru', '')
    for option in options:
        if option['id'] != keep['answer'].get('optionId') and option['zh'] in explanation:
            errors.append(f'{keep["id"]}: пояснение называет неверный вариант {option["zh"]} — '
                          'на экране его может не оказаться')
    years = [option['zh'] for option in options if YEAR.match(option['zh'].strip())]
    if len({'年' in year for year in years}) > 1:
        errors.append(f'{keep["id"]}: годы в вариантах записаны по-разному (с 年 и без): {years}')
    return errors
```

В `validate_merges` после проверки `unknown` добавить:

```python
        distractors = item.get('distractors')
        if distractors is not None and distractors != POOL:
            errors.append(f'{keep_id}: distractors может быть только "pool"')
```

В том же цикле заменить блок сравнения вариантов

```python
            elif _option_texts(absorbed) != _option_texts(keep):
                errors.append(f'{absorbed_id}: варианты не совпадают с {keep_id}')
            elif _answer_text(absorbed) != _answer_text(keep):
```

на

```python
            elif distractors != POOL and _option_texts(absorbed) != _option_texts(keep):
                errors.append(f'{absorbed_id}: варианты не совпадают с {keep_id}')
            elif _answer_text(absorbed) != _answer_text(keep):
```

и после цикла `for absorbed_id in absorbs:` (внутри цикла по `merges.items()`, на его уровне) добавить:

```python
        if distractors == POOL and all(by_id.get(i) for i in absorbs):
            errors += _pool_errors(keep, [by_id[i] for i in absorbs])
```

В `apply_merges` заменить последнюю строку сборки записи

```python
        result.append({**record, 'occurrences': occurrences, 'evidence': evidence,
                       'mergedIds': sorted(item['absorbs'])})
```

на

```python
        merged = {**record, 'occurrences': occurrences, 'evidence': evidence,
                  'mergedIds': sorted(item['absorbs'])}
        if item.get('distractors') == POOL:
            merged['options'] = _pooled_options(record, absorbed)
        result.append(merged)
```

`_reindexed` менять не нужно: официальный ключ влитой записи указывает на правильный ответ (это проверяется), а он есть среди вариантов оставшейся записи.

- [ ] **Step 4: Убедиться, что тесты проходят**

Run: `python3 -m unittest test.test_merges -v 2>&1 | tail -5`
Expected: `OK`.

- [ ] **Step 5: Переписать правило в `CLAUDE.md`**

В пункте «Склеить дубли…» заменить предложение «Записи с тем же вопросом, но другими вариантами склеивать нельзя — это разные задания; их связывает `data/review/fact-groups.json`.» на:

```
Записи с тем же вопросом и тем же ответом, но другими неверными вариантами
склеиваются только с пометкой `"distractors": "pool"`: варианты складываются в общий
набор, раунд каждый раз показывает правильный и три случайных; пояснение такой записи
не называет неверных вариантов (о них — подписи). Записи с разными ответами на один
вопрос склеивать нельзя — их связывает `data/review/fact-groups.json`.
```

- [ ] **Step 6: Прогнать все тесты и закоммитить**

Run: `python3 -m unittest discover -s test -t . 2>&1 | tail -3`
Expected: `OK` (банк ещё не менялся).

```bash
git add scripts/merges.py test/test_merges.py CLAUDE.md
git commit -m "Склейка с общим набором неверных вариантов

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Раунд берёт четыре варианта из общего набора

**Files:**
- Modify: `src/quiz.mjs` (`labelledOptions`, новая `hasOptionPool`)
- Modify: `test/quiz.test.mjs`
- Modify: `test/ui.test.mjs` (помощники `currentRecord`, `answer`)

**Interfaces:**
- Consumes: запись с `options.length > 4` (Task 1).
- Produces: `export function hasOptionPool(record): boolean` — `true`, если вариантов больше четырёх; `labelledOptions(record, random)` всегда возвращает не больше четырёх `{label, optionId, zh}`.

- [ ] **Step 1: Написать падающие тесты**

В `test/quiz.test.mjs` в импорт из `../src/quiz.mjs` добавить `hasOptionPool, matchesDatabaseSearch, migrateProgress` (сейчас в списке именованных импортов их нет; в файле они вызывались как `quiz.…`). После теста «правильность считается по optionId, а не по букве» добавить:

```js
const POOLED_OPTIONS = ['孙子兵法', '本草纲目', '西游记', '论语', '红楼梦', '水浒传', '阿Q正传']
  .map((zh, index) => ({ id: `o${index + 1}`, zh }));
const pooled = (overrides = {}) => record('pool', {
  options: POOLED_OPTIONS, answer: { optionId: 'o1', state: 'verified' }, ...overrides,
});

function seeded(seed = 1) {
  let value = seed;
  return () => ((value = (value * 16807) % 2147483647) - 1) / 2147483646;
}

test('у вопроса с общим набором на экране четыре варианта, правильный всегда среди них', () => {
  const random = seeded();
  const seen = new Set();
  for (let index = 0; index < 300; index += 1) {
    const shown = labelledOptions(pooled(), random);
    assert.deepEqual(shown.map((option) => option.label), ['A', 'B', 'C', 'D']);
    assert.equal(new Set(shown.map((option) => option.optionId)).size, 4);
    assert.ok(shown.some((option) => option.optionId === 'o1'));
    assert.equal(grade(pooled(), 'o1').correct, true);
    shown.forEach((option) => seen.add(option.optionId));
  }
  assert.equal(seen.size, POOLED_OPTIONS.length, 'каждый неверный вариант хоть раз попадает на экран');
});

test('без правильного варианта вопрос с общим набором показывает первые четыре', () => {
  const shown = labelledOptions(pooled({ answer: { optionId: null, state: 'needs-review' } }), () => 0);
  assert.equal(shown.length, 4);
  assert.deepEqual(shown.map((option) => option.optionId).sort(), ['o1', 'o2', 'o3', 'o4']);
});

test('общий набор отличается от обычных четырёх вариантов', () => {
  assert.equal(hasOptionPool(pooled()), true);
  assert.equal(hasOptionPool(record('a')), false);
});

test('поиск в базе находит вопрос по варианту из общего набора', () => {
  assert.equal(matchesDatabaseSearch(pooled(), '阿Q正传'), true);
});

test('прогресс нескольких влитых записей сходится в одну', () => {
  const bank = [record('kept', { mergedIds: ['gone-1', 'gone-2'] })];
  const item = { attempts: 1, correct: 1, completed: true, lastCorrect: true, box: 2, dueAt: 5 };
  const migrated = migrateProgress(bank, { 'gone-1': item, 'gone-2': { ...item, correct: 0, lastCorrect: false, box: 0, dueAt: 1 } });
  assert.deepEqual(Object.keys(migrated), ['kept']);
  assert.equal(migrated.kept.attempts, 2);
  assert.equal(migrated.kept.lastCorrect, false);
  assert.equal(migrated.kept.box, 0);
});
```

- [ ] **Step 2: Убедиться, что тесты падают**

Run: `node --test test/quiz.test.mjs 2>&1 | grep -E "^not ok|^ℹ (pass|fail)"`
Expected: падают тесты про общий набор (`hasOptionPool` не экспортируется, `labelledOptions` отдаёт 7 вариантов). Тест про прогресс нескольких записей может пройти сразу — `migrateProgress` уже перебирает `mergedIds`; это закрепление поведения.

- [ ] **Step 3: Реализовать в `src/quiz.mjs`**

Заменить функцию `labelledOptions` на:

```js
// Вопрос с общим набором неверных вариантов (склейка с пометкой pool): на экран
// выходят правильный и три случайных неверных, при каждом показе заново.
export function hasOptionPool(record) {
  return record.options.length > LABELS.length;
}

function shownOptions(record, random) {
  const right = record.options.find((option) => option.id === record.answer.optionId);
  if (!hasOptionPool(record)) return record.options;
  if (!right) return record.options.slice(0, LABELS.length);
  const wrong = shuffled(record.options.filter((option) => option !== right), random);
  return [right, ...wrong.slice(0, LABELS.length - 1)];
}

export function labelledOptions(record, random = Math.random) {
  return shuffled(shownOptions(record, random), random).map((option, index) => ({
    label: LABELS[index],
    optionId: option.id,
    zh: option.zh,
  }));
}
```

У записи с четырьмя вариантами `shuffled` вызывается с тем же `random` один раз, как раньше, — существующие тесты меток не меняются.

- [ ] **Step 4: Убедиться, что тесты проходят**

Run: `node --test test/quiz.test.mjs 2>&1 | grep -E "^ℹ (pass|fail)"`
Expected: `ℹ fail 0`.

- [ ] **Step 5: Научить помощников браузерного теста вопросу с общим набором**

В `test/ui.test.mjs` заменить `currentRecord` и `answer` на:

```js
/** Запись банка для вопроса на экране. Сверяются и тексты, и id вариантов: в банке
 * есть записи с одним и тем же текстом вопроса, но разными вариантами. У вопроса с
 * общим набором неверных вариантов на экране только четыре из них, поэтому
 * показанные варианты должны входить в запись, а не совпадать с ней целиком. */
async function currentRecord(page, bank) {
  const question = await page.locator('#questionText').textContent();
  const shown = await page.locator('#options button').evaluateAll((buttons) => buttons
    .map((b) => `${b.dataset.optionId}=${b.querySelector('span:nth-child(2)').textContent}`));
  const matches = bank.filter((r) => r.questionRu === question
    && shown.every((item) => r.options.some((o) => `${o.id}=${o.zh}` === item)));
  assert.equal(matches.length, 1, `вопрос на экране не определить однозначно: ${question}`);
  return matches[0];
}

async function answer(page, record, correct) {
  const shown = await page.locator('#options button')
    .evaluateAll((buttons) => buttons.map((b) => b.dataset.optionId));
  const optionId = correct
    ? record.answer.optionId
    : shown.find((id) => id !== record.answer.optionId);
  await page.locator(`#options button[data-option-id="${optionId}"]`).click();
}
```

- [ ] **Step 6: Собрать страницу, прогнать все тесты и закоммитить**

Run: `npm run build 2>&1 | tail -1 && node --test test/*.test.mjs 2>&1 | grep -E "^ℹ (tests|pass|fail|skipped)"`
Expected: `ℹ fail 0`, `ℹ skipped 0`.

```bash
git add src/quiz.mjs test/quiz.test.mjs test/ui.test.mjs dist/lingvostranovedenie-trainer.html
git commit -m "Раунд берёт правильный и три случайных варианта из общего набора

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Пилот — четыре группы в данных

**Files:**
- Modify: `data/review/editorial.json` (`2015-16-zak-5`, `2015-16-mun-9`, `2022-23-reg-10`)
- Modify: `data/review/glosses.json` (перенос подписей)
- Modify: `data/review/merges.json` (три объединения и одна склейка)
- Modify: `data/review/fact-groups.json` (удалить `art-of-war`, `yuan-founders`, `china-wto-year`)
- Modify: `data/review/similar-questions.md` (пункты 2 и 18)
- Modify: `test/test_merges.py` (проверка на реальных данных)
- Regenerate: `data/bank.json`, `data/review/merge.md`, `dist/lingvostranovedenie-trainer.html` (через `npm run build`)

**Interfaces:**
- Consumes: пометка `"distractors": "pool"` (Task 1), раунд с общим набором (Task 2).
- Produces: в банке три записи с вариантами сверх четырёх (`2017-18-shk-4` — 7 вариантов, `2015-16-zak-5` — 5, `2015-16-mun-9` — 7); `2017-18-mun-2` поглощает `2022-23-reg-10`; 445 записей.

- [ ] **Step 1: Написать падающий тест на реальных данных**

В `test/test_merges.py` в класс `MergesInBankTest` добавить:

```python
    def test_pooled_records_show_every_wrong_option_once(self):
        pools = {k: v for k, v in self.merges.items() if v.get('distractors') == 'pool'}
        self.assertEqual(set(pools), {'2017-18-shk-4', '2015-16-zak-5', '2015-16-mun-9'})
        expected = {'2017-18-shk-4': 7, '2015-16-zak-5': 5, '2015-16-mun-9': 7}
        for keep_id in pools:
            record = self.bank[keep_id]
            texts = [o['zh'] for o in record['options']]
            self.assertEqual(len(texts), expected[keep_id], keep_id)
            self.assertEqual(len(set(texts)), len(texts), keep_id)
            self.assertNotIn('factGroup', record, keep_id)
            wrong = [o['zh'] for o in record['options'] if o['id'] != record['answer']['optionId']]
            for text in wrong:
                self.assertNotIn(text, record['explanation']['ru'], keep_id)

    def test_lao_she_questions_are_one_record_with_beijing_dialect(self):
        record = self.bank['2017-18-mun-2']
        self.assertEqual(record['mergedIds'], ['2022-23-reg-10'])
        answer = next(o['zh'] for o in record['options'] if o['id'] == record['answer']['optionId'])
        self.assertEqual(answer, '北京方言')
        self.assertNotIn('北方方言', [o['zh'] for o in record['options']])
```

Run: `python3 -m unittest test.test_merges 2>&1 | tail -3`
Expected: FAIL (в `merges.json` нет объединений).

- [ ] **Step 2: Правки `editorial.json`**

Выполнить из корня ветки:

```bash
python3 - <<'EOF'
import json
p = 'data/review/editorial.json'
raw = open(p, encoding='utf-8').read()
edits = json.loads(raw)
assert json.dumps(edits, ensure_ascii=False, indent=2) + '\n' == raw
assert '2015-16-zak-5' not in edits and '2015-16-mun-9' not in edits
edits['2015-16-zak-5'] = {
    'reason': 'Объединение с 2016-17-mun-7 в один вопрос с общим набором неверных вариантов: '
              'пояснение не называет неверных вариантов — на экране их может не оказаться, сведения о них в подписях',
    'explanation': 'Династию Юань в 1271 году основал монгол (蒙古族) Хубилай, внук Чингисхана.',
}
edits['2015-16-mun-9'] = {
    'reason': 'Объединение с 2024-25-shk-36 в один вопрос с общим набором неверных вариантов: '
              'годы записаны с 年, как во второй записи; пояснение «Поэтому верен вариант 2001» — тавтология',
    'options': {'o1': '2001 年', 'o2': '1995 年', 'o3': '2015 年', 'o4': '1970 年'},
    'explanation': 'Китай вступил во Всемирную торговую организацию 11 декабря 2001 года.',
}
edit = edits['2022-23-reg-10']
edit['reason'] += ('; решение автора — у вопроса о диалекте Лао Шэ один ответ: 北方方言 заменён на '
                   'более точный 北京方言 (пекинский говор, как в 2017-18-mun-2), запись склеивается с 2017-18-mun-2')
edit['options'] = {'o4': '北京方言'}
open(p, 'w', encoding='utf-8').write(json.dumps(edits, ensure_ascii=False, indent=2) + '\n')
EOF
```

Проверить исходные тексты перед заменой: `2015-16-mun-9` сейчас o1 `2001`, o2 `1995`, o3 `2015`, o4 `1970`; `2022-23-reg-10` o4 сейчас `北方方言`. Если не так — остановиться и сообщить.

- [ ] **Step 3: Перенести подписи влитых записей**

```bash
python3 - <<'EOF'
import json
p = 'data/review/glosses.json'
raw = open(p, encoding='utf-8').read()
glosses = json.loads(raw)
dump = lambda data: json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
assert dump(glosses) == raw
yuan = glosses.pop('2016-17-mun-7')
assert yuan['options']['o4']['zh'] == '维吾尔族'
glosses['2015-16-zak-5']['options']['o5'] = yuan['options']['o4']
wto = glosses.pop('2024-25-shk-36')
assert [wto['options'][k]['zh'] for k in ('o1', 'o3', 'o4')] == ['2010 年', '2011 年', '1991 年']
assert '2015-16-mun-9' not in glosses
glosses['2015-16-mun-9'] = {
    'reviewedAt': wto['reviewedAt'],
    'options': {'o5': wto['options']['o1'], 'o6': wto['options']['o3'], 'o7': wto['options']['o4']},
}
open(p, 'w', encoding='utf-8').write(dump(glosses))
EOF
```

Подписи `2016-17-mun-7` к 汉族 и 满族 не переносятся: у оставшейся записи `2015-16-zak-5` к этим вариантам свои, такие же подписи.

- [ ] **Step 4: Записать объединения и склейку, убрать группы**

```bash
python3 - <<'EOF'
import json
p = 'data/review/merges.json'
raw = open(p, encoding='utf-8').read()
merges = json.loads(raw)
assert json.dumps(merges, ensure_ascii=False, indent=2) + '\n' == raw
merges['2017-18-shk-4'] = {
    'absorbs': ['2018-19-mun-50', '2017-18-zak-2', '2024-25-mun-35'],
    'distractors': 'pool',
    'reason': '«Искусство войны»: олимпиада четыре раза задавала один вопрос с тем же ответом, меняя неверные варианты',
}
merges['2015-16-zak-5'] = {
    'absorbs': ['2016-17-mun-7'],
    'distractors': 'pool',
    'reason': 'Какая национальность основала династию Юань: тот же вопрос и ответ, другие неверные варианты',
}
merges['2015-16-mun-9'] = {
    'absorbs': ['2024-25-shk-36'],
    'distractors': 'pool',
    'reason': 'Год вступления Китая в ВТО: тот же вопрос и ответ, другие неверные варианты',
}
merges['2017-18-mun-2'] = {
    'absorbs': ['2022-23-reg-10'],
    'reason': 'Диалект Лао Шэ: тот же вопрос; после правки ответа второй записи (北方方言 → 北京方言) совпадают варианты и ответ',
}
open(p, 'w', encoding='utf-8').write(json.dumps(merges, ensure_ascii=False, indent=2) + '\n')

p = 'data/review/fact-groups.json'
raw = open(p, encoding='utf-8').read()
groups = json.loads(raw)
assert json.dumps(groups, ensure_ascii=False, indent=2) + '\n' == raw
for name in ('art-of-war', 'yuan-founders', 'china-wto-year'):
    del groups[name]
open(p, 'w', encoding='utf-8').write(json.dumps(groups, ensure_ascii=False, indent=2) + '\n')
EOF
```

- [ ] **Step 5: Пересобрать банк**

Run: `npm run build 2>&1 | tail -4`
Expected: `банк: 445 записей, проверено 445` и `собрано: … проверено 445 из 445`. Если сборка остановилась ошибкой проверки (например, «пояснение называет неверный вариант» у `2017-18-shk-4`) — не обходить проверку, а сообщить: это решение автора.

Проверить вручную:

```bash
python3 -c "
import json
b = {r['id']: r for r in json.load(open('data/bank.json'))}
for i in ('2017-18-shk-4', '2015-16-zak-5', '2015-16-mun-9', '2017-18-mun-2'):
    r = b[i]
    print(i, [(o['id'], o['zh'], bool(o.get('gloss'))) for o in r['options']], '→', r['answer']['optionId'], r['mergedIds'])
"
```

Expected: у `2015-16-zak-5` подписи у o1, o2, o4, o5; у `2015-16-mun-9` — у o5, o6, o7; у `2017-18-shk-4` варианты 本草纲目, 西游记, 孙子兵法, 论语, 红楼梦, 水浒传, 阿Q正传.

- [ ] **Step 6: Отметить решения в `data/review/similar-questions.md`**

В пункте «2. На каком диалекте писал Лао Шэ» строку `Решение: ` заменить на `Решение: склеено, ответ 北京方言 (2026-10-13, пилот общего набора вариантов).` В пункте «18. Национальность основателей Юань / Хубилая» после строки предложения добавить строку: `Записи 2015-16-zak-5 и 2016-17-mun-7 объединены в один вопрос с общим набором вариантов; группы yuan-founders больше нет — 2017-18-reg-10 можно добавить в объединение или оставить отдельным вопросом.`

- [ ] **Step 7: Прогнать все тесты и закоммитить**

Run: `python3 -m unittest discover -s test -t . 2>&1 | tail -3 && node --test test/*.test.mjs 2>&1 | grep -E "^ℹ (tests|pass|fail|skipped)"`
Expected: `OK`; `ℹ fail 0`, `ℹ skipped 0`.

```bash
git add data/review/editorial.json data/review/glosses.json data/review/merges.json data/review/fact-groups.json \
  data/review/similar-questions.md data/review/merge.md data/bank.json dist/lingvostranovedenie-trainer.html test/test_merges.py
git commit -m "Пилот: три вопроса с общим набором вариантов и склейка Лао Шэ

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Метка в базе вопросов и браузерный тест

**Files:**
- Modify: `src/quiz.ui.js` (импорт не нужен: `scripts/build_html.py` встраивает `src/quiz.mjs` в ту же страницу, убирая `export `, поэтому `hasOptionPool` — глобальная функция, как `labelledOptions`)
- Modify: `test/ui.test.mjs`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `hasOptionPool(record)` (Task 2), объединённые записи в банке (Task 3).
- Produces: в карточке базы у записи с общим набором — `<span class="tag">варианты меняются</span>` в `.row-top`.

- [ ] **Step 1: Написать падающий браузерный тест**

В `test/ui.test.mjs` после теста «в раунде нет двух вопросов про один факт» добавить:

```js
test('у вопроса с общим набором в раунде четыре варианта, а в базе — все и метка', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  const pooled = bank.find((r) => r.options.length > 4);
  assert.ok(pooled, 'в банке нет вопросов с общим набором вариантов');
  await page.evaluate((id) => startRoundWith([QUESTION_BANK.find((r) => r.id === id)]), pooled.id);
  const shown = await page.locator('#options button').evaluateAll((buttons) => buttons.map((b) => b.dataset.optionId));
  assert.equal(shown.length, 4);
  assert.ok(shown.includes(pooled.answer.optionId));
  await page.locator(`#options button[data-option-id="${pooled.answer.optionId}"]`).click();
  assert.match(await page.locator('#feedback').textContent(), /Верно/);

  await page.locator('#leaveRound').click();
  await page.locator('#openDatabase').click();
  await page.locator('#databaseSearch').fill(pooled.questionRu);
  const row = page.locator('#databaseList .row', { hasText: pooled.questionRu }).first();
  await row.waitFor();
  assert.match(await row.locator('.row-top').textContent(), /варианты меняются/);
  const options = await row.locator('.row-options').textContent();
  for (const option of pooled.options) assert.ok(options.includes(option.zh), option.zh);
  assert.deepEqual(page.errors, []);
});
```

Run: `node --test test/ui.test.mjs 2>&1 | grep -E "^not ok|^ℹ (pass|fail|skipped)"`
Expected: падает на «варианты меняются» (метки ещё нет); первая половина (4 варианта в раунде) уже проходит благодаря Task 2.

- [ ] **Step 2: Добавить метку в карточку базы**

В `src/quiz.ui.js`, функция `appendDatabaseRows`, в массиве `article.innerHTML` после строки

```js
      origin.isAddition ? `<span class="tag origin">${origin.label}</span>` : '',
```

добавить

```js
      hasOptionPool(record) ? '<span class="tag">варианты меняются</span>' : '',
```

- [ ] **Step 3: Собрать и прогнать все тесты**

Run: `npm run build 2>&1 | tail -1 && python3 -m unittest discover -s test -t . 2>&1 | tail -3 && node --test test/*.test.mjs 2>&1 | grep -E "^ℹ (tests|pass|fail|skipped)"`
Expected: `OK`; `ℹ fail 0`, `ℹ skipped 0`.

- [ ] **Step 4: Запись в `CHANGELOG.md`**

Перед разделом `## Не реализовано (сознательно или пока)` добавить:

```markdown
## 2026-10-13 — Один вопрос с меняющимися неверными вариантами (пилот)

- Спека и план: `docs/superpowers/specs/2026-10-13-distractor-pools-design.md`,
  `docs/superpowers/plans/2026-10-13-distractor-pools.md`.
- Склейка с пометкой `"distractors": "pool"` (`scripts/merges.py`) объединяет записи с
  одинаковым ответом, но разными неверными вариантами: варианты складываются в общий
  набор (o5, o6…), появления, источники, официальные ключи и прогресс учеников
  переносятся, как у обычной склейки. Сборка останавливается, если ответы разные,
  объединение ничего не добавило, пояснение называет неверный вариант или годы
  записаны по-разному. Правило в `CLAUDE.md` обновлено.
- Раунд у такого вопроса каждый раз показывает правильный и три случайных неверных
  (`labelledOptions` в `src/quiz.mjs`); в базе видны все варианты и метка «варианты
  меняются». Режим «Новые» больше не возвращает эти вопросы: это одна запись.
- Пилот: «Искусство войны» (4 записи, 6 неверных вариантов), основатели Юань (4),
  год вступления в ВТО (6; годы приведены к записи с 年). Вопросы о диалекте Лао Шэ
  склеены обычной склейкой после правки ответа 北方方言 → 北京方言 (решение автора).
  Группы `art-of-war`, `yuan-founders`, `china-wto-year` убраны из `fact-groups.json`.
  Банк: 451 → 445 записей.
- Помощники браузерного теста узнают вопрос по части вариантов: у вопроса с общим
  набором на экране четыре из них.
```

- [ ] **Step 5: Закоммитить**

```bash
git add src/quiz.ui.js test/ui.test.mjs dist/lingvostranovedenie-trainer.html CHANGELOG.md
git commit -m "Метка «варианты меняются» в базе вопросов

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Спросить автора про ревью перед слиянием в `master`**

Одной строкой: что в ветке (механизм общего набора вариантов, пилот на четырёх группах, 445 записей) и нужно ли ревью.
