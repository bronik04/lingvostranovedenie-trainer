# Форматы «Вспомни сам» и «Верно или нет» — план реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** в «Тренировке» появляется настройка «Формат» с двумя новыми форматами вопроса — «Вспомни сам» (ответ сначала вспоминается без вариантов, потом самооценка) и «Верно или нет» (один предложенный ответ, две кнопки).

**Architecture:** вся логика без DOM — в `src/quiz.mjs` (формат в настройках, исход ответа → запись прогресса, утверждение «верно или нет», распознавание вопросов, которым нужны варианты), с юнит-тестами в `test/quiz.test.mjs`. `src/quiz.ui.js` получает формат раунда и стадию вопроса; общий путь ответа (`commitAnswer`) один для всех форматов. Разметка — в `src/template.html`, стили — в `src/quiz.css` на токенах «Туши и киновари». Браузерные сценарии — в `test/ui.test.mjs` по собранному `dist/`.

**Tech Stack:** ванильный JS (ES-модуль для движка, классический скрипт для интерфейса), `node:test`, Playwright (`playwright-core`) с установленным Chrome, Python-сборка `scripts/build_html.py`.

**Spec:** `docs/superpowers/specs/2026-10-15-recall-and-true-false-design.md`

## Global Constraints

- `data/`, `sources/` не меняются. `dist/` руками не править — только сборкой (`python3 scripts/build_html.py` во время задач, `npm run build` в финальной проверке); пересобранный `dist/lingvostranovedenie-trainer.html` коммитится вместе с изменениями `src/`.
- Запись прогресса не меняет формы: поля `attempts`, `correct`, `completed`, `lastCorrect`, `box`, `dueAt`; `isValidProgress` не меняется. Ключи `localStorage` прежние (`lingvo-trainer:v1`, `lingvo-trainer:settings:v1`), версия — 1.
- Настройки: `{ filters, size, format }`, `format` ∈ `choice` | `recall` | `truefalse`, по умолчанию `choice`.
- Исходы: `correct`, `partial`, `wrong`, `checked` — значения по таблице спецификации.
- Тексты интерфейса — по-русски, варианты — по-китайски с `lang="zh-Hans"`.
- Цвета и размеры — только токены системы (`src/ink/`): `var(--…)`, никаких hex.
- Сборщик (`scripts/minify.py`) вырезает `//` и `/* */` без учёта регулярных выражений: в литералах регулярок в `src/*.js`/`*.mjs` не должно быть кавычек, `//` и `/*`.
- `build_html.py` убирает `export ` из движка: функции `quiz.mjs` в браузере — глобальные (`needsOptions`, `QUESTION_BANK` доступны из `page.evaluate`), как и `const state` из `quiz.ui.js`.
- Тесты: `python3 -m unittest discover -s test -t .` и `node --test test/*.test.mjs` (глоб без кавычек). `test/ui.test.mjs` без Chrome локально пропускается — перед ним пересобрать `dist/`.
- Каждое заметное изменение — строка в `CHANGELOG.md` в том же коммите (раздел «2026-10-15 — Форматы „Вспомни сам“ и „Верно или нет“», перед «Не реализовано»).
- Сообщения коммитов — по-русски, с последней строкой `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Ветка `feat/recall-true-false`; перед слиянием в `master` — спросить автора о ревью.

## Review Focus

1. Ученик уходит из раунда посреди стадии (ответ открыт, оценки нет) и начинает раунд в другом формате — на экране не должно остаться панелей прошлого формата. Тест в задаче 4.
2. Пробел/Enter, когда фокус на кнопке «Показать ответ» или «Не помню»: кнопка срабатывает один раз, без второго глобального действия; цифры 1–3 до открытия ответа ничего не оценивают. Тест в задаче 4.
3. Регулярные выражения `needsOptions` переживают минификацию — в собранном `dist/` вопрос «из перечисленного» сразу показывает варианты. Тест в задаче 4.
4. «Повторить ошибки раунда» и повтор ошибки внутри раунда остаются в том же формате. Тест в задаче 5.
5. Телефон 360 px: новые экраны без горизонтальной прокрутки (длинный вариант в карточке «Предложенный ответ», кнопки самооценки). Тесты в задачах 4 и 5.

---

### Задача 1: формат в настройках и исходы ответа

**Files:**
- Modify: `src/quiz.mjs` (константы в начале файла, `normaliseStudySettings`, новая `applyAnswer` после `scheduleReview`)
- Test: `test/quiz.test.mjs`

**Interfaces:**
- Produces: `FORMATS: Set<'choice'|'recall'|'truefalse'>`; `normaliseStudySettings(value, bank) → { filters, size, format }`; `applyAnswer(previous: ProgressEntry | undefined, outcome: 'correct'|'partial'|'wrong'|'checked', now = Date.now()) → ProgressEntry` (бросает `Error` на неизвестный исход).

- [ ] **Шаг 1: тесты.** В `test/quiz.test.mjs` в существующем тесте «настройки отбрасывают повреждённые и устаревшие значения» добавить `format: 'choice'` в оба ожидаемых объекта (после `size`):

```js
    size: 20,
    format: 'choice',
  });
```

```js
    size: 10,
    format: 'choice',
  });
```

И добавить в конец файла:

```js
test('формат раунда хранится в настройках; неизвестный и отсутствующий — «выбор ответа»', () => {
  const bank = [record('a')];
  const filters = { topics: [], years: [], stages: [], mode: 'all', onlyVerified: false };
  assert.equal(quiz.normaliseStudySettings({ filters, size: 10, format: 'recall' }, bank).format, 'recall');
  assert.equal(quiz.normaliseStudySettings({ filters, size: 10, format: 'truefalse' }, bank).format, 'truefalse');
  assert.equal(quiz.normaliseStudySettings({ filters, size: 10 }, bank).format, 'choice');
  assert.equal(quiz.normaliseStudySettings({ filters, size: 10, format: 'blitz' }, bank).format, 'choice');
  assert.equal(quiz.normaliseStudySettings(null, bank).format, 'choice');
});

const NOW = 1_000_000_000_000;
const DAY = 86_400_000;

test('исход correct двигает коробку, wrong сбрасывает — как прежний ответ из четырёх', () => {
  const first = quiz.applyAnswer(undefined, 'correct', NOW);
  assert.deepEqual(first, { attempts: 1, correct: 1, completed: true, lastCorrect: true, box: 1, dueAt: NOW + DAY });
  assert.deepEqual(quiz.applyAnswer(first, 'wrong', NOW),
    { attempts: 2, correct: 1, completed: true, lastCorrect: false, box: 0, dueAt: NOW });
});

test('«вспомнил неточно» не поднимает коробку, но и не оставляет вопрос на сегодня', () => {
  assert.deepEqual(quiz.applyAnswer(undefined, 'partial', NOW),
    { attempts: 1, correct: 1, completed: true, lastCorrect: true, box: 1, dueAt: NOW + DAY });
  const learned = { attempts: 5, correct: 5, completed: true, lastCorrect: true, box: 4, dueAt: 0 };
  assert.deepEqual(quiz.applyAnswer(learned, 'partial', NOW),
    { attempts: 6, correct: 6, completed: true, lastCorrect: true, box: 4, dueAt: NOW + 16 * DAY });
  const afterMistake = { attempts: 2, correct: 1, completed: true, lastCorrect: false, box: 0, dueAt: 0 };
  assert.equal(quiz.applyAnswer(afterMistake, 'partial', NOW).box, 1);
});

test('верно в «Верно или нет» не сдвигает повторение и не выводит вопрос из «Ошибок»', () => {
  const mistake = { attempts: 1, correct: 0, completed: true, lastCorrect: false, box: 0, dueAt: 123 };
  assert.deepEqual(quiz.applyAnswer(mistake, 'checked', NOW),
    { attempts: 2, correct: 1, completed: true, lastCorrect: false, box: 0, dueAt: 123 });
  const learned = { attempts: 3, correct: 3, completed: true, lastCorrect: true, box: 3, dueAt: 999 };
  assert.deepEqual(quiz.applyAnswer(learned, 'checked', NOW),
    { attempts: 4, correct: 4, completed: true, lastCorrect: true, box: 3, dueAt: 999 });
  // новый вопрос считается пройденным и сразу ждёт настоящего повторения
  assert.deepEqual(quiz.applyAnswer(undefined, 'checked', NOW),
    { attempts: 1, correct: 1, completed: true, lastCorrect: true, box: 0, dueAt: NOW });
  assert.deepEqual(quiz.applyAnswer({ attempts: 0, correct: 0 }, 'checked', NOW),
    { attempts: 1, correct: 1, completed: true, lastCorrect: true, box: 0, dueAt: NOW });
});

test('любой исход даёт запись, которую принимает проверка прогресса', () => {
  const progress = Object.fromEntries(['correct', 'partial', 'wrong', 'checked']
    .map((outcome) => [outcome, quiz.applyAnswer(undefined, outcome, NOW)]));
  assert.equal(isValidProgress(progress), true);
});

test('неизвестный исход — ошибка программы, а не тихая порча прогресса', () => {
  assert.throws(() => quiz.applyAnswer(undefined, 'maybe', NOW), /исход/);
});
```

- [ ] **Шаг 2: убедиться, что тесты падают.**

Run: `node --test test/quiz.test.mjs`
Expected: FAIL — `quiz.applyAnswer is not a function`, у настроек нет `format`.

- [ ] **Шаг 3: реализация в `src/quiz.mjs`.** После `const ROUND_SIZES = …` добавить:

```js
export const FORMATS = new Set(['choice', 'recall', 'truefalse']);
const OUTCOMES = new Set(['correct', 'partial', 'wrong', 'checked']);
```

Заменить комментарий над `REVIEW_INTERVALS_DAYS` на:

```js
// Упрощённый вариант интервального повторения (Leitner-стиль): бокс растёт на
// верном ответе и сгорает до нуля на ошибке. Полноценный SM-2 со шкалой 0–5 не
// нужен: выбор из вариантов даёт только верно/неверно, а самооценка во «Вспомни
// сам» добавляет одну промежуточную ступень — «вспомнил неточно» (applyAnswer).
```

В `normaliseStudySettings`: в `defaults` после `size: 10,` добавить `format: 'choice',`; в возвращаемом объекте после `size: …,` добавить:

```js
    format: FORMATS.has(value.format) ? value.format : defaults.format,
```

После функции `scheduleReview` добавить:

```js
// Исход ответа → новая запись прогресса. correct — знал; partial — вспомнил неточно
// или верно после подсказки: коробка не растёт (но не ниже первой); wrong — ошибка;
// checked — верно в «Верно или нет»: угадать можно в половине случаев, поэтому
// коробка, срок и lastCorrect не меняются, а новый вопрос сразу ждёт повторения.
export function applyAnswer(previous, outcome, now = Date.now()) {
  if (!OUTCOMES.has(outcome)) throw new Error(`неизвестный исход ответа: ${outcome}`);
  const entry = {
    attempts: (previous?.attempts ?? 0) + 1,
    correct: (previous?.correct ?? 0) + (outcome === 'wrong' ? 0 : 1),
    completed: true,
  };
  if (outcome === 'checked') {
    return previous?.completed
      ? { ...entry, lastCorrect: previous.lastCorrect, box: previous.box, dueAt: previous.dueAt }
      : { ...entry, lastCorrect: true, box: 0, dueAt: now };
  }
  if (outcome === 'partial') {
    const box = Math.max(previous?.box ?? 0, 1);
    return { ...entry, lastCorrect: true, box, dueAt: now + REVIEW_INTERVALS_DAYS[box] * DAY_MS };
  }
  return { ...entry, lastCorrect: outcome === 'correct', ...scheduleReview(previous, outcome === 'correct', now) };
}
```

- [ ] **Шаг 4: тесты проходят.**

Run: `node --test test/quiz.test.mjs`
Expected: PASS, все тесты, включая прежние.

- [ ] **Шаг 5: коммит.**

```bash
git add src/quiz.mjs test/quiz.test.mjs
git commit -m "Движок: формат раунда в настройках и исходы ответа

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Задача 2: утверждение «верно или нет» и вопросы, которым нужны варианты

**Files:**
- Modify: `src/quiz.mjs` (после `optionGlosses`)
- Test: `test/quiz.test.mjs`

**Interfaces:**
- Consumes: `hasOptionPool` не нужен — функция берёт неверные из всех `record.options`.
- Produces: `trueFalseStatement(record, random = Math.random) → { optionId: string, zh: string, isTrue: boolean }` (первый вызов `random()` решает правду, второй — какой неверный); `needsOptions(record) → boolean`.

- [ ] **Шаг 1: тесты** — в конец `test/quiz.test.mjs`:

```js
const sequence = (...values) => {
  let index = 0;
  return () => values[index++];
};

test('«верно или нет»: при random < ½ предлагается правильный вариант', () => {
  assert.deepEqual(quiz.trueFalseStatement(record('a'), sequence(0.1)),
    { optionId: 'o2', zh: '上海', isTrue: true });
});

test('«верно или нет»: иначе предлагается неверный вариант, и выпасть может любой', () => {
  const picked = [0, 0.34, 0.67, 0.99].map((x) => quiz.trueFalseStatement(record('a'), sequence(0.5, x)));
  assert.ok(picked.every((statement) => statement.isTrue === false && statement.optionId !== 'o2'));
  assert.deepEqual(new Set(picked.map((statement) => statement.optionId)), new Set(['o1', 'o3', 'o4']));
});

test('«верно или нет»: у записи с общим набором неверный берётся из всего набора', () => {
  const pooled = record('a', {
    options: [
      { id: 'o1', zh: '广州' }, { id: 'o2', zh: '上海' }, { id: 'o3', zh: '北京' },
      { id: 'o4', zh: '西安' }, { id: 'o5', zh: '天津' }, { id: 'o6', zh: '重庆' },
    ],
  });
  assert.deepEqual(quiz.trueFalseStatement(pooled, sequence(0.5, 0.99)),
    { optionId: 'o6', zh: '重庆', isTrue: false });
});

test('вопросы, на которые без вариантов не ответить, узнаются по формулировке', () => {
  const needs = (questionRu) => quiz.needsOptions(record('a', { questionRu }));
  assert.equal(needs('Что из перечисленного является специальным административным районом Китая?'), true);
  assert.equal(needs('Какой из нижеперечисленных городов Китая называют 泉城?'), true);
  assert.equal(needs('Какое животное не входит в китайский двенадцатилетний зодиак?'), true);
  assert.equal(needs('Какой город не относится к шести древним столицам Китая?'), true);
  assert.equal(needs('С какой страной не граничит КНР?'), true);
});

test('«не» в формулировке ещё не значит, что без вариантов не ответить', () => {
  const needs = (questionRu) => quiz.needsOptions(record('a', { questionRu }));
  assert.equal(needs('Как называлась самая ранняя династия Китая?'), false);
  assert.equal(needs('Обычай в день праздника Ханьши («праздник холодной пищи»), предшествующего Цинмину, '
    + 'не разводить огонь и есть только холодную пищу, по преданию установил Цзинь Вэнь-гун в память '
    + 'о своём верном спутнике. О ком идёт речь?'), false);
  assert.equal(needs('Какой денежный подарок делают не только на Праздник весны, но и на рождение ребёнка, '
    + 'новоселье и день рождения?'), false);
  assert.equal(needs('Какой праздник неразрывно связан с луной?'), false);
});
```

- [ ] **Шаг 2: тесты падают.**

Run: `node --test test/quiz.test.mjs`
Expected: FAIL — `quiz.trueFalseStatement is not a function`.

- [ ] **Шаг 3: реализация** — в `src/quiz.mjs` после `optionGlosses`:

```js
// «Верно или нет»: с вероятностью ½ — правильный вариант, иначе любой неверный,
// у записи с общим набором — из всего набора.
export function trueFalseStatement(record, random = Math.random) {
  const right = record.options.find((option) => option.id === record.answer.optionId);
  if (!right) throw new Error(`у вопроса нет правильного варианта: ${record.id}`);
  const isTrue = random() < 0.5;
  const wrong = record.options.filter((option) => option !== right);
  const option = isTrue ? right : wrong[Math.floor(random() * wrong.length)];
  return { optionId: option.id, zh: option.zh, isTrue };
}

// Вопросы, на которые без вариантов не ответить: «Что из перечисленного…»,
// «Какое животное не входит в зодиак?». Правило по формулировке эвристическое:
// промах безвреден — ученик откроет варианты сам, лишний вопрос просто сразу
// покажет четыре варианта. В регулярках нет кавычек и // — их не поймёт минификатор.
const LISTED_OPTIONS = /перечисленн|из следующих|из приведённых|из приведенных|из этих|из указанных/i;
const NEGATED_MEMBERSHIP = /(?<![а-яё])не\s+(является|являлся|являются|входит|входят|относится|относятся|был|была|было|были|граничит|принадлежит)(?![а-яё])/i;

export function needsOptions(record) {
  return LISTED_OPTIONS.test(record.questionRu) || NEGATED_MEMBERSHIP.test(record.questionRu);
}
```

- [ ] **Шаг 4: тесты проходят, и правило на банке даёт 32 вопроса, как в спецификации.**

Run: `node --test test/quiz.test.mjs`
Expected: PASS.

Run: `node -e "import('./src/quiz.mjs').then(({ needsOptions }) => { const bank = JSON.parse(require('fs').readFileSync('data/bank.json', 'utf8')); console.log(bank.filter(needsOptions).length); })"`
Expected: `32` (если банк вырос — число может быть больше; меньше 32 — регулярка сломана).

- [ ] **Шаг 5: коммит.**

```bash
git add src/quiz.mjs test/quiz.test.mjs
git commit -m "Движок: утверждение «верно или нет» и вопросы, которым нужны варианты

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Задача 3: настройка «Формат» и общий путь ответа в интерфейсе

Формат выбирается и запоминается; раунд пока везде идёт выбором из четырёх, но ответ уже проходит через `applyAnswer` и `commitAnswer`, на которые опираются задачи 4 и 5.

**Files:**
- Modify: `src/template.html` (главная — раздел «Формат» и номера глав; экран вопроса — `id="quizHint"`)
- Modify: `src/quiz.ui.js`
- Modify: `CHANGELOG.md`
- Rebuild: `dist/lingvostranovedenie-trainer.html`
- Test: `test/ui.test.mjs`

**Interfaces:**
- Consumes: `normaliseStudySettings(...).format`, `applyAnswer` (задача 1).
- Produces (в `quiz.ui.js`): `state.format`, `state.roundFormat`, `state.stage` (`'choice'` пока единственная стадия); `startRoundWith(round, format = state.format)`; `renderOptions(record)`; `chooseOption(record, optionId)`; `commitAnswer(record, outcome, pick = {})`; `markOptions(record, optionId)`; `showFeedback(record, kind, verdictHtml)`; `QUIZ_HINTS`; `state.wrongPicks[id]` — объект `{ optionId?, said?, isTrue? }` вместо строки. В разметке: `input[name="studyFormat"]`, `#formatHelp`, `#quizHint`.

- [ ] **Шаг 1: браузерный тест** — в `test/ui.test.mjs` перед блоком `/* ---------- раздел «Чэнъюй» ---------- */`:

```js
async function pickFormat(page, label) {
  await page.locator('#setupView .mode-option', { hasText: label }).click();
}

test('формат выбирается, объясняется и переживает перезагрузку', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  assert.equal(await page.locator('input[name="studyFormat"]:checked').getAttribute('value'), 'choice');
  await pickFormat(page, 'Верно или нет');
  assert.match(await page.locator('#formatHelp').textContent(), /один предложенный ответ/);
  await page.reload();
  assert.equal(await page.locator('input[name="studyFormat"]:checked').getAttribute('value'), 'truefalse');
  // «Сбросить фильтры» не трогает формат: это не фильтр
  await page.locator('#clearFilters').click();
  assert.equal(await page.locator('input[name="studyFormat"]:checked').getAttribute('value'), 'truefalse');
  assert.deepEqual(page.errors, []);
});
```

- [ ] **Шаг 2: тест падает.**

Run: `python3 scripts/build_html.py && node --test test/ui.test.mjs`
Expected: FAIL — нет `input[name="studyFormat"]` (остальные тесты проходят).

- [ ] **Шаг 3: разметка.** В `src/template.html` сразу после секции «Режим» (после её `</section>`) вставить:

```html
    <section class="chapter">
      <span class="chapter-mark" lang="zh-Hans" aria-hidden="true">二</span>
      <fieldset class="chapter-body mode-picker">
        <legend class="ink-title-2">Формат</legend>
        <div class="ink-pills mode-options">
          <label class="mode-option"><input type="radio" name="studyFormat" value="choice" checked><span class="ink-pill">Выбор ответа</span></label>
          <label class="mode-option"><input type="radio" name="studyFormat" value="recall"><span class="ink-pill">Вспомни сам</span></label>
          <label class="mode-option"><input type="radio" name="studyFormat" value="truefalse"><span class="ink-pill">Верно или нет</span></label>
        </div>
        <p class="ink-caption mode-help" id="formatHelp"></p>
      </fieldset>
    </section>
```

В секции `#settingsPanel` знак главы `二` → `三`; в секции «Длина раунда» `三` → `四`. Подсказку под экраном вопроса

```html
    <p class="ink-caption hint">1–4 или A–D — ответить · Enter — дальше · Esc — выйти из раунда</p>
```

заменить на

```html
    <p class="ink-caption hint" id="quizHint">1–4 или A–D — ответить · Enter — дальше · Esc — выйти из раунда</p>
```

- [ ] **Шаг 4: настройки в `src/quiz.ui.js`.**

После `const THEME_COLORS = …` добавить:

```js
const FORMAT_COPY = {
  choice: 'Вопрос и четыре варианта — как на олимпиаде.',
  recall: 'Сначала вспомните ответ сами, варианты — только как подсказка.',
  truefalse: 'Вопрос и один предложенный ответ: правильный он или нет?',
};
const QUIZ_HINTS = {
  choice: '1–4 или A–D — ответить · Enter — дальше · Esc — выйти из раунда',
  recall: 'Пробел — показать ответ · V — варианты · 1 / 2 / 3 — оценка · Esc — выйти из раунда',
  truefalse: '1 или ← — верно · 2 или → — неверно · Enter — дальше · Esc — выйти из раунда',
};
```

`defaultStudySettings` → `return { filters: defaultFilters(), size: 10, format: 'choice' };`

В `state` после `size: savedStudySettings.size,`:

```js
  format: savedStudySettings.format,
  // формат замораживается на старте раунда: настройки во время раунда не видны
  roundFormat: 'choice',
  // стадия текущего вопроса: 'choice' — сетка вариантов (задачи 4–5 добавят свои)
  stage: 'choice',
```

В `saveStudySettings` объект настроек: `settings: { filters: state.filters, size: state.size, format: state.format },`.

В `renderSetup` сразу после строки `$('modeHelp').textContent = modeCopy[state.filters.mode];`:

```js
  for (const input of document.querySelectorAll('input[name="studyFormat"]')) {
    input.checked = input.value === state.format;
  }
  $('formatHelp').textContent = FORMAT_COPY[state.format];
```

В обвязке после цикла по `input[name="studyMode"]`:

```js
for (const input of document.querySelectorAll('input[name="studyFormat"]')) {
  input.addEventListener('change', (event) => {
    state.format = event.target.value;
    saveStudySettings();
    renderSetup();
  });
}
```

- [ ] **Шаг 5: общий путь ответа в `src/quiz.ui.js`.**

`startRoundWith(round)` → `startRoundWith(round, format = state.format)`, первой строкой тела: `state.roundFormat = format;`. В `repeatMistakes`: `if (wrong.length) startRoundWith(wrong, state.roundFormat);`.

В `renderQuestion` заменить всё от `$('feedback').className = 'feedback hidden';` до конца функции на:

```js
  $('feedback').className = 'feedback hidden';
  $('nextButton').classList.add('hidden');
  $('options').innerHTML = '';
  $('quizHint').textContent = QUIZ_HINTS[state.roundFormat];
  state.stage = 'choice';
  renderOptions(record);
}

function renderOptions(record) {
  $('options').innerHTML = '';
  for (const option of labelledOptions(record)) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'option';
    button.dataset.optionId = option.optionId;
    const letter = document.createElement('span');
    letter.className = 'letter';
    letter.setAttribute('aria-hidden', 'true');
    letter.textContent = option.label;
    const caption = document.createElement('span');
    caption.className = 'option-text';
    caption.lang = 'zh-Hans';
    caption.textContent = option.zh;
    button.append(letter, caption);
    button.addEventListener('click', () => chooseOption(record, option.optionId));
    $('options').append(button);
  }
}
```

Функцию `answer(record, optionId)` целиком заменить на четыре:

```js
/** Общее для любого формата: прогресс, счёт раунда, повтор ошибки, ход, кнопка «дальше». */
function commitAnswer(record, outcome, pick = {}) {
  state.answered = true;
  const right = outcome !== 'wrong';
  state.progress[record.id] = applyAnswer(state.progress[record.id], outcome);
  saveProgress();
  ({ correct: state.correct, wrongIds: state.wrongIds } =
    tallyAnswer({ correct: state.correct, wrongIds: state.wrongIds }, record.id, right));
  if (!right) {
    if (!(record.id in state.wrongPicks)) state.wrongPicks[record.id] = pick;
    const retry = queueRetry(state.retryQueue, state.retriedIds, record, state.position);
    state.retryQueue = retry.queue;
    state.retriedIds = retry.retriedIds;
  }
  state.marks[state.position] = right;
  renderProgress();
  $('nextButton').textContent =
    state.position + 1 < state.round.length ? 'Следующий вопрос' : 'Итоги раунда';
  $('nextButton').classList.remove('hidden');
}

function chooseOption(record, optionId) {
  if (state.answered) return;
  const verdict = grade(record, optionId);
  commitAnswer(record, verdict.correct ? 'correct' : 'wrong', { optionId });
  markOptions(record, optionId);
  const right = record.options.find((option) => option.id === verdict.answerOptionId);
  showFeedback(record, verdict.correct ? 'good' : 'bad', [
    `<strong>${verdict.correct ? 'Верно' : 'Неверно'}</strong>`,
    verdict.correct ? '' : `<span>Правильный ответ: <span lang="zh-Hans">${escapeHtml(right.zh)}</span>.</span>`,
  ].join(''));
}

/** После выбора: верный — нефритом, выбранный неверный — киноварью, подписи под неверными. */
function markOptions(record, optionId) {
  const glosses = new Map(optionGlosses(record).map((item) => [item.optionId, item.gloss]));
  for (const button of $('options').querySelectorAll('button')) {
    button.disabled = true;
    if (button.dataset.optionId === record.answer.optionId) {
      button.classList.add('correct');
      const status = document.createElement('span');
      status.className = 'option-status';
      status.textContent = '✓ Верно';
      button.append(status);
    } else if (button.dataset.optionId === optionId) {
      button.classList.add('wrong');
      const status = document.createElement('span');
      status.className = 'option-status';
      status.textContent = '✕ Ваш ответ';
      button.append(status);
    }
    if (glosses.has(button.dataset.optionId)) {
      const note = document.createElement('small');
      note.className = 'option-gloss';
      note.textContent = glosses.get(button.dataset.optionId);
      button.append(note);
    }
  }
}

/** Разбор под вопросом: строка вердикта (её задаёт формат), пояснение, источники. */
function showFeedback(record, kind, verdictHtml) {
  const sources = evidenceList(record.evidence);
  $('feedback').className = `feedback ${kind}`;
  $('feedback').innerHTML = [
    `<p class="verdict">${verdictHtml}</p>`,
    record.explanation.ru ? `<p class="why">${escapeHtml(record.explanation.ru)}</p>` : '',
    sources ? `<ul>${sources}</ul>` : '',
    record.answer.state === 'unverified'
      ? '<p class="unverified">Ответ взят из официального ключа, но ещё не перепроверен по источникам.</p>'
      : '',
  ].join('');
  requestAnimationFrame(() => {
    const compact = window.matchMedia?.('(max-width: 600px)').matches;
    const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    $('feedback').focus({ preventScroll: true });
    if (compact) $('feedback').scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'nearest' });
  });
}
```

В `renderMistakes` строку `const picked = record.options.find((option) => option.id === state.wrongPicks[record.id]);` заменить на:

```js
    const pick = state.wrongPicks[record.id] ?? {};
    const picked = record.options.find((option) => option.id === pick.optionId);
```

- [ ] **Шаг 6: запись в `CHANGELOG.md`** — перед строкой `## Не реализовано (сознательно или пока)`:

```markdown
## 2026-10-15 — Форматы «Вспомни сам» и «Верно или нет»

Спецификация — `docs/superpowers/specs/2026-10-15-recall-and-true-false-design.md`.

- На главной — раздел «Формат» (выбор ответа, «Вспомни сам», «Верно или нет»), независимый от
  «Режима»; запоминается вместе с настройками, «Сбросить фильтры» его не трогает. Запись прогресса
  после ответа считает `applyAnswer` в движке; форма записи прежняя.

```

- [ ] **Шаг 7: сборка и все тесты.**

Run: `python3 scripts/build_html.py && node --test test/*.test.mjs && python3 -m unittest discover -s test -t .`
Expected: PASS, включая новый тест формата и все прежние сценарии раунда (верный/неверный ответ, повтор ошибки, клавиатура, «Ошибки», подписи, телефон).

- [ ] **Шаг 8: коммит.**

```bash
git add src/template.html src/quiz.ui.js test/ui.test.mjs CHANGELOG.md dist/lingvostranovedenie-trainer.html
git commit -m "Настройка «Формат» и общий путь ответа в интерфейсе

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Задача 4: формат «Вспомни сам»

**Files:**
- Modify: `src/template.html` (экран вопроса, итоги)
- Modify: `src/quiz.ui.js`
- Modify: `src/quiz.css`
- Modify: `CHANGELOG.md`
- Rebuild: `dist/lingvostranovedenie-trainer.html`
- Test: `test/ui.test.mjs`

**Interfaces:**
- Consumes: `needsOptions` (задача 2); `commitAnswer`, `chooseOption`, `renderOptions`, `showFeedback`, `state.roundFormat`, `state.stage` (задача 3).
- Produces: стадии `'recall'` → `'rate'` | `'hint'`; `state.recallCounts = { correct, partial, wrong }`; функции `revealAnswer()`, `showHint()`, `rateRecall(outcome)`, `showRecallNote(text)`; разметка `#recallNote`, `#recallPrompt`, `#revealAnswer`, `#showHint`, `#recallRate` (кнопки с `data-outcome`), `#resultRecall`; класс разбора `feedback reveal`. Задача 5 добавляет `'tfPanel'` в список скрываемых панелей `renderQuestion`.

- [ ] **Шаг 1: браузерные тесты** — в `test/ui.test.mjs` после теста «формат выбирается…»:

```js
/** Убирает из банка страницы вопросы, которым нужны варианты (или, наоборот, все остальные),
 * чтобы стадия первого вопроса во «Вспомни сам» не зависела от случая. */
async function keepRecallQuestions(page, needs) {
  await page.evaluate((keepNeeds) => {
    for (let index = QUESTION_BANK.length - 1; index >= 0; index -= 1) {
      if (needsOptions(QUESTION_BANK[index]) !== keepNeeds) QUESTION_BANK.splice(index, 1);
    }
  }, needs);
}

test('вспомни сам: ответ открывается пробелом, «не вспомнил» отправляет вопрос в «Ошибки»', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, false);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  assert.equal(await page.locator('#recallPrompt').isVisible(), true);
  assert.equal(await page.locator('#options button').count(), 0);
  // до открытия ответа оценка ничего не делает
  await page.keyboard.press('Digit3');
  assert.equal(await page.locator('#nextButton').isVisible(), false);
  await page.keyboard.press('Space');
  assert.equal(await page.locator('#feedback.reveal').isVisible(), true);
  assert.equal(await page.locator('#recallRate').isVisible(), true);
  assert.equal(await page.locator('#recallPrompt').isVisible(), false);
  await page.keyboard.press('Digit3');
  await page.locator('#nextButton:not(.hidden)').waitFor();
  assert.equal(await page.locator('#progressSteps li').first().getAttribute('class'), 'ink-step ink-step--wrong ink-step--current');
  await page.locator('#leaveRound').click();
  await page.locator('#setupView .mode-option', { hasText: 'Ошибки' }).click();
  assert.equal(await page.locator('#eligibleNotice').textContent(), 'Под фильтры подходит вопросов: 1.');
  assert.deepEqual(page.errors, []);
});

test('вспомни сам: кнопка «Показать ответ» с клавиатуры срабатывает один раз', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, false);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  await page.locator('#revealAnswer').focus();
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('#recallRate').isVisible(), true);
  // ответ открыт, оценки ещё нет: Enter не должен ни оценить, ни перелистнуть вопрос
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('#nextButton').isVisible(), false);
  assert.match(await page.locator('#progressLabel').textContent(), /^Вопрос 1 из/);
  assert.deepEqual(page.errors, []);
});

test('вспомни сам: подсказка показывает варианты, верный ответ засчитан как «неточно»', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, false);
  const bank = await bankOf(page);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  await page.locator('#showHint').click();
  assert.equal(await page.locator('#options button').count(), 4);
  assert.match(await page.locator('#recallNote').textContent(), /«вспомнил неточно»/);
  const record = await currentRecord(page, bank);
  await answer(page, record, true);
  const progress = await page.evaluate(() => JSON.parse(localStorage.getItem('lingvo-trainer:v1')).progress);
  assert.equal(progress[record.id].box, 1);
  assert.equal(progress[record.id].lastCorrect, true);
  assert.deepEqual(page.errors, []);
});

test('вспомни сам: вопрос «из перечисленного» сразу показывает варианты', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, true);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  assert.equal(await page.locator('#options button').count(), 4);
  assert.equal(await page.locator('#recallPrompt').isVisible(), false);
  assert.match(await page.locator('#recallNote').textContent(), /без вариантов не ответить/);
  assert.deepEqual(page.errors, []);
});

test('вспомни сам: в итогах — разбивка по самооценке', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, false);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  for (let question = 0; question < 5; question += 1) {
    await page.keyboard.press('Space');
    await page.keyboard.press(question === 0 ? 'Digit2' : 'Digit1');
    await page.keyboard.press('Enter');
  }
  await page.locator('#resultsView').waitFor();
  assert.equal(await page.locator('#finalScore').textContent(), '5 / 5');
  assert.equal(await page.locator('#resultRecall').textContent(), 'вспомнил сам — 4 · неточно — 1 · не вспомнил — 0');
  assert.deepEqual(page.errors, []);
});

test('уход из раунда посреди стадии не оставляет панелей в раунде другого формата', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, false);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  await page.keyboard.press('Space');
  await page.keyboard.press('Escape');
  await pickFormat(page, 'Выбор ответа');
  await startRound(page, 5);
  assert.equal(await page.locator('#options button').count(), 4);
  for (const id of ['#recallPrompt', '#recallRate', '#recallNote', '#feedback']) {
    assert.equal(await page.locator(id).isVisible(), false, id);
  }
  assert.deepEqual(page.errors, []);
});

test('телефон: «Вспомни сам» без горизонтальной прокрутки', LIMIT, async (t) => {
  const page = await openPage(t, { width: 360, height: 780 });
  if (!page) return;
  await keepRecallQuestions(page, false);
  const overflow = () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  assert.equal(await overflow(), 0, 'стадия «вспомнить»');
  await page.locator('#revealAnswer').click();
  assert.equal(await overflow(), 0, 'ответ и самооценка');
  assert.deepEqual(page.errors, []);
});
```

- [ ] **Шаг 2: тесты падают.**

Run: `python3 scripts/build_html.py && node --test test/ui.test.mjs`
Expected: FAIL — нет `#recallPrompt`.

- [ ] **Шаг 3: разметка.** В `src/template.html` на экране вопроса заменить строку `<div class="options" id="options" …></div>` и строку `#feedback` на:

```html
    <p class="ink-caption recall-note hidden" id="recallNote"></p>
    <div class="options" id="options" role="group" aria-label="Варианты ответа"></div>
    <div class="recall-prompt hidden" id="recallPrompt">
      <p>Вспомните ответ, произнесите или запишите его, потом откройте.</p>
      <div class="actions">
        <button class="ink-btn ink-btn--primary" id="revealAnswer" type="button">Показать ответ</button>
        <button class="ink-btn ink-btn--secondary" id="showHint" type="button">Не помню — показать варианты</button>
      </div>
    </div>
    <div class="feedback hidden" id="feedback" role="status" tabindex="-1"></div>
    <div class="recall-rate hidden" id="recallRate" role="group" aria-labelledby="recallRateTitle">
      <p class="recall-rate-title" id="recallRateTitle">Как получилось?</p>
      <div class="actions">
        <button class="ink-btn ink-btn--secondary" type="button" data-outcome="correct">Вспомнил сам</button>
        <button class="ink-btn ink-btn--secondary" type="button" data-outcome="partial">Вспомнил неточно</button>
        <button class="ink-btn ink-btn--secondary" type="button" data-outcome="wrong">Не вспомнил</button>
      </div>
    </div>
```

В итогах после `<p class="ink-caption result-counts" id="resultCounts"></p>`:

```html
      <p class="ink-caption result-recall" id="resultRecall" hidden></p>
```

- [ ] **Шаг 4: логика в `src/quiz.ui.js`.**

В `state` после `stage: 'choice',`:

```js
  // первые попытки во «Вспомни сам» по самооценке — для строки в итогах
  recallCounts: { correct: 0, partial: 0, wrong: 0 },
```

Комментарий у `stage` заменить на `// стадия вопроса: 'choice' — сетка вариантов; во «Вспомни сам» 'recall' → 'rate' или 'hint'`.

В `startRoundWith` после `state.roundFormat = format;`: `state.recallCounts = { correct: 0, partial: 0, wrong: 0 };`.

В `renderQuestion` строки

```js
  $('quizHint').textContent = QUIZ_HINTS[state.roundFormat];
  state.stage = 'choice';
  renderOptions(record);
```

заменить на

```js
  $('quizHint').textContent = QUIZ_HINTS[state.roundFormat];
  for (const id of ['recallNote', 'recallPrompt', 'recallRate']) $(id).classList.add('hidden');
  for (const button of $('recallRate').querySelectorAll('button')) {
    button.disabled = false;
    button.removeAttribute('aria-pressed');
  }
  if (state.roundFormat === 'recall' && !needsOptions(record)) {
    state.stage = 'recall';
    $('recallPrompt').classList.remove('hidden');
    return;
  }
  state.stage = 'choice';
  if (state.roundFormat === 'recall') showRecallNote('На этот вопрос без вариантов не ответить — выберите из четырёх.');
  renderOptions(record);
```

В `commitAnswer` после `saveProgress();`:

```js
  if (state.roundFormat === 'recall' && !isRepeatInRound(state.round, state.position)) {
    state.recallCounts[outcome] += 1;
  }
```

В `chooseOption` строки `commitAnswer(...)` и `showFeedback(...)` заменить так, чтобы подсказка давала `partial`:

```js
  const hinted = state.stage === 'hint';
  const outcome = !verdict.correct ? 'wrong' : hinted ? 'partial' : 'correct';
  commitAnswer(record, outcome, { optionId });
  markOptions(record, optionId);
  const right = record.options.find((option) => option.id === verdict.answerOptionId);
  showFeedback(record, verdict.correct ? 'good' : 'bad', [
    `<strong>${verdict.correct ? 'Верно' : 'Неверно'}</strong>`,
    verdict.correct
      ? hinted ? '<span>С подсказкой — засчитано как «вспомнил неточно».</span>' : ''
      : `<span>Правильный ответ: <span lang="zh-Hans">${escapeHtml(right.zh)}</span>.</span>`,
  ].join(''));
```

После `showFeedback` добавить:

```js
/* ---------- «Вспомни сам» ---------- */

function showRecallNote(text) {
  $('recallNote').textContent = text;
  $('recallNote').classList.remove('hidden');
}

function revealAnswer() {
  if (state.stage !== 'recall' || state.answered) return;
  const record = state.round[state.position];
  const right = record.options.find((option) => option.id === record.answer.optionId);
  state.stage = 'rate';
  $('recallPrompt').classList.add('hidden');
  showFeedback(record, 'reveal',
    `<strong lang="zh-Hans">${escapeHtml(right.zh)}</strong><span>Правильный ответ</span>`);
  $('recallRate').classList.remove('hidden');
}

function showHint() {
  if (state.stage !== 'recall' || state.answered) return;
  state.stage = 'hint';
  $('recallPrompt').classList.add('hidden');
  showRecallNote('С подсказкой верный ответ засчитается как «вспомнил неточно».');
  renderOptions(state.round[state.position]);
}

function rateRecall(outcome) {
  if (state.stage !== 'rate' || state.answered) return;
  commitAnswer(state.round[state.position], outcome);
  for (const button of $('recallRate').querySelectorAll('button')) {
    button.disabled = true;
    if (button.dataset.outcome === outcome) button.setAttribute('aria-pressed', 'true');
  }
}
```

В `finishRound` после строки `$('resultCounts').innerHTML = …;`:

```js
  const recall = state.recallCounts;
  $('resultRecall').hidden = state.roundFormat !== 'recall';
  $('resultRecall').textContent =
    `вспомнил сам — ${recall.correct} · неточно — ${recall.partial} · не вспомнил — ${recall.wrong}`;
```

Клавиатура: после `const ANSWER_KEYS = {…};` добавить

```js
const RATE_KEYS = {
  Digit1: 'correct', Numpad1: 'correct', Digit2: 'partial', Numpad2: 'partial', Digit3: 'wrong', Numpad3: 'wrong',
};
```

и в обработчике `keydown` сразу после `if (state.view !== 'quiz') return;`:

```js
  if (state.stage === 'recall') {
    if ((event.key === 'Enter' || event.key === ' ') && !onControl) {
      event.preventDefault();
      revealAnswer();
    } else if (event.code === 'KeyV') {
      event.preventDefault();
      showHint();
    }
    return;
  }
  if (state.stage === 'rate' && !state.answered) {
    const outcome = RATE_KEYS[event.code];
    if (outcome) {
      event.preventDefault();
      rateRecall(outcome);
    }
    return;
  }
```

Обвязка — после `$('nextButton').addEventListener(...)`:

```js
$('revealAnswer').addEventListener('click', revealAnswer);
$('showHint').addEventListener('click', showHint);
for (const button of $('recallRate').querySelectorAll('button')) {
  button.addEventListener('click', () => rateRecall(button.dataset.outcome));
}
```

- [ ] **Шаг 5: стили** — в `src/quiz.css` перед `/* ---------- итог раунда ---------- */`:

```css
/* ---------- «Вспомни сам» и «Верно или нет» ---------- */

.recall-note { margin: 0 0 var(--s-3); }
.recall-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--s-4);
  padding: var(--s-6) var(--s-5);
  border: var(--border-hair) dashed var(--line-on-ground-strong);
  border-radius: var(--radius-sm);
  text-align: center;
}
.recall-prompt p, .recall-rate p { margin: 0; }
.recall-prompt .actions { justify-content: center; }
.recall-rate { display: flex; flex-direction: column; gap: var(--s-3); margin-top: var(--s-5); }
.recall-rate-title { font-weight: var(--t-weight-semibold); }
/* выбранная оценка — залита тушью, как выбранная пилюля; остальные гаснут как disabled */
.recall-rate .ink-btn[aria-pressed='true'] {
  border-style: solid;
  border-color: var(--text-on-ground);
  background: var(--text-on-ground);
  color: var(--surface-ground);
}
/* ответ, открытый во «Вспомни сам», — печать 答 вместо 对/错 */
.feedback.reveal .verdict::before {
  content: '答';
  content: '答' / '';
  border: var(--border-hair) solid var(--line-on-ground-strong);
  color: var(--text-on-ground);
}
.feedback.reveal .verdict strong { font-family: var(--font-han); }
.result-recall { margin: 0; }
```

И в `@media (max-width: 600px)` добавить строку:

```css
  .recall-prompt .ink-btn, .recall-rate .ink-btn { flex: 1 1 100%; }
```

- [ ] **Шаг 6: `CHANGELOG.md`** — в раздел задачи 3 добавить пункт:

```markdown
- «Вспомни сам»: сначала только вопрос; «Показать ответ» (пробел) открывает ответ с пояснением и
  самооценку 1 / 2 / 3 — «вспомнил сам» двигает повторение, «неточно» держит коробку (не ниже
  первой), «не вспомнил» — ошибка. «Не помню — показать варианты» (V): верный ответ с подсказкой
  засчитывается как «неточно». 32 вопроса «из перечисленного…» и с «не входит/не относится…»
  (`needsOptions`) сразу идут с вариантами. В итогах — разбивка по самооценке.
```

- [ ] **Шаг 7: сборка и все тесты.**

Run: `python3 scripts/build_html.py && node --test test/*.test.mjs && python3 -m unittest discover -s test -t .`
Expected: PASS.

- [ ] **Шаг 8: глазами.** Запустить превью `dist/` (`.claude/launch.json`, сервер `dist`), пройти «Вспомни сам» в светлой и тёмной теме: пунктирная рамка, печать 答, выбранная оценка залита, на 360 px кнопки во всю ширину. Поправить, если что-то выбивается из «Туши и киновари».

- [ ] **Шаг 9: коммит.**

```bash
git add src/template.html src/quiz.ui.js src/quiz.css test/ui.test.mjs CHANGELOG.md dist/lingvostranovedenie-trainer.html
git commit -m "Формат «Вспомни сам»

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Задача 5: формат «Верно или нет»

**Files:**
- Modify: `src/template.html` (экран вопроса)
- Modify: `src/quiz.ui.js`
- Modify: `src/quiz.css`
- Modify: `CHANGELOG.md`
- Rebuild: `dist/lingvostranovedenie-trainer.html`
- Test: `test/ui.test.mjs`

**Interfaces:**
- Consumes: `trueFalseStatement` (задача 2); `commitAnswer(record, outcome, pick)`, `showFeedback`, `state.stage`, список скрываемых панелей в `renderQuestion` (задачи 3–4).
- Produces: стадия `'tf'`; `state.statement`, `state.streak`; `answerTrueFalse(saidTrue: boolean)`; разметка `#tfPanel`, `#tfOption`, `#tfTrue`, `#tfFalse`; `state.wrongPicks[id] = { optionId, said, isTrue }`.

- [ ] **Шаг 1: браузерные тесты** — в `test/ui.test.mjs` после тестов «Вспомни сам»:

```js
const currentStatement = (page) => page.evaluate(() => ({
  id: state.round[state.position].id, isTrue: state.statement.isTrue, zh: state.statement.zh,
}));

test('верно или нет: ошибка объясняется, возвращается в раунде и повторяется в том же формате', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  await pickFormat(page, 'Верно или нет');
  await startRound(page, 5);
  let questions = 0;
  let wrongId = null;
  while (await page.locator('#quizView').isVisible()) {
    questions += 1;
    assert.ok(questions <= 6, 'раунд не заканчивается');
    assert.equal(await page.locator('#tfPanel').isVisible(), true);
    assert.equal(await page.locator('#options button').count(), 0);
    const statement = await currentStatement(page);
    assert.equal(await page.locator('#tfOption').textContent(), statement.zh);
    const mistake = questions === 1;
    // ← — «верно», → — «неверно»; ошибаемся только на первом вопросе
    const sayTrue = mistake ? !statement.isTrue : statement.isTrue;
    await page.keyboard.press(sayTrue ? 'ArrowLeft' : 'ArrowRight');
    await page.locator('#nextButton:not(.hidden)').waitFor();
    if (mistake) {
      wrongId = statement.id;
      const right = bank.find((r) => r.id === statement.id).options
        .find((o) => o.id === bank.find((r) => r.id === statement.id).answer.optionId);
      assert.equal(await page.locator('#feedback.bad').isVisible(), true);
      assert.ok((await page.locator('#feedback').textContent()).includes(right.zh), 'нет правильного ответа');
      assert.match(await page.locator('#scoreLabel').textContent(), /серия 0/);
    }
    if (questions === 6) assert.equal(statement.id, wrongId, 'шестым должен вернуться ошибочный вопрос');
    await page.keyboard.press('Enter');
  }
  assert.equal(await page.locator('#finalScore').textContent(), '4 / 5');
  assert.match(await page.locator('#mistakeList li').first().textContent(), /«(не)?верно» для/);
  await page.locator('#repeatMistakes').click();
  assert.equal(await page.locator('#tfPanel').isVisible(), true, 'повтор ошибок — в том же формате');
  assert.deepEqual(page.errors, []);
});

test('верно или нет: угаданное «верно» не выводит вопрос из «Ошибок»', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  const target = bank.find((r) => r.answer.state === 'verified');
  await page.evaluate((id) => localStorage.setItem('lingvo-trainer:v1', JSON.stringify({
    version: 1,
    progress: { [id]: { attempts: 1, correct: 0, completed: true, lastCorrect: false, box: 0, dueAt: 0 } },
  })), target.id);
  await page.reload();
  await page.locator('#setupView .mode-option', { hasText: 'Ошибки' }).click();
  await pickFormat(page, 'Верно или нет');
  await startRound(page, 5);
  const statement = await currentStatement(page);
  assert.equal(statement.id, target.id);
  await page.locator(statement.isTrue ? '#tfTrue' : '#tfFalse').click();
  assert.equal(await page.locator('#feedback.good').isVisible(), true);
  await page.locator('#leaveRound').click();
  assert.equal(await page.locator('#eligibleNotice').textContent(), 'Под фильтры подходит вопросов: 1.');
  assert.deepEqual(page.errors, []);
});

test('телефон: «Верно или нет» с длинным вариантом без горизонтальной прокрутки', LIMIT, async (t) => {
  const page = await openPage(t, { width: 360, height: 780 });
  if (!page) return;
  await page.evaluate(() => {
    for (const r of QUESTION_BANK) for (const o of r.options) o.zh = `${o.zh}中华人民共和国全国人民代表大会常务委员会`;
  });
  const overflow = () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  await pickFormat(page, 'Верно или нет');
  await startRound(page, 5);
  assert.equal(await overflow(), 0, 'карточка с предложенным ответом');
  await page.locator('#tfTrue').click();
  assert.equal(await overflow(), 0, 'разбор ответа');
  assert.deepEqual(page.errors, []);
});
```

- [ ] **Шаг 2: тесты падают.**

Run: `python3 scripts/build_html.py && node --test test/ui.test.mjs`
Expected: FAIL — нет `#tfPanel`.

- [ ] **Шаг 3: разметка.** В `src/template.html` сразу после блока `#recallPrompt` (перед `#feedback`):

```html
    <div class="truefalse hidden" id="tfPanel">
      <div class="tf-card">
        <p class="ink-caption">Предложенный ответ</p>
        <p class="tf-option" id="tfOption" lang="zh-Hans"></p>
      </div>
      <div class="tf-buttons" role="group" aria-label="Правильный ли это ответ">
        <button class="ink-btn ink-btn--secondary" id="tfTrue" type="button">Верно</button>
        <button class="ink-btn ink-btn--secondary" id="tfFalse" type="button">Неверно</button>
      </div>
    </div>
```

- [ ] **Шаг 4: логика в `src/quiz.ui.js`.**

В `state` после `recallCounts: …,`:

```js
  // «Верно или нет»: утверждение текущего вопроса и верные ответы подряд в раунде
  statement: null,
  streak: 0,
```

В `startRoundWith` после сброса `recallCounts`: `state.streak = 0;`.

В `renderQuestion` список панелей — `['recallNote', 'recallPrompt', 'recallRate', 'tfPanel']`; после цикла по кнопкам `#recallRate` и перед `if (state.roundFormat === 'recall' …)`:

```js
  if (state.roundFormat === 'truefalse') {
    state.stage = 'tf';
    state.statement = trueFalseStatement(record);
    $('tfOption').textContent = state.statement.zh;
    for (const button of $('tfPanel').querySelectorAll('button')) {
      button.disabled = false;
      button.removeAttribute('aria-pressed');
    }
    $('tfPanel').classList.remove('hidden');
    return;
  }
```

Комментарий у `stage` дополнить: `; в «Верно или нет» — 'tf'`.

В `renderProgress` строку счёта заменить на:

```js
  $('scoreLabel').textContent = `верно ${state.correct}${
    state.roundFormat === 'truefalse' ? ` · серия ${state.streak}` : ''}`;
```

После функций «Вспомни сам» добавить:

```js
/* ---------- «Верно или нет» ---------- */

function answerTrueFalse(saidTrue) {
  if (state.stage !== 'tf' || state.answered) return;
  const record = state.round[state.position];
  const statement = state.statement;
  const right = statement.isTrue === saidTrue;
  state.streak = right ? state.streak + 1 : 0;
  commitAnswer(record, right ? 'checked' : 'wrong',
    { optionId: statement.optionId, said: saidTrue, isTrue: statement.isTrue });
  for (const button of $('tfPanel').querySelectorAll('button')) {
    button.disabled = true;
    if (button.id === (saidTrue ? 'tfTrue' : 'tfFalse')) button.setAttribute('aria-pressed', 'true');
  }
  const answerOption = record.options.find((option) => option.id === record.answer.optionId);
  const shown = record.options.find((option) => option.id === statement.optionId);
  const about = statement.isTrue
    ? `<span lang="zh-Hans">${escapeHtml(shown.zh)}</span> — правильный ответ.`
    : `${shown.gloss ? `<span lang="zh-Hans">${escapeHtml(shown.zh)}</span> — ${escapeHtml(shown.gloss)}. ` : ''}`
      + `Правильный ответ: <span lang="zh-Hans">${escapeHtml(answerOption.zh)}</span>.`;
  showFeedback(record, right ? 'good' : 'bad', `<strong>${right ? 'Правильно' : 'Ошибка'}</strong><span>${about}</span>`);
}
```

`state.streak` меняется до `commitAnswer`, потому что `commitAnswer` вызывает `renderProgress`, а та выводит серию.

В `renderMistakes` строку с `picked ? \`Ваш ответ …` заменить на:

```js
      picked ? `Ваш ответ ${pick.said === undefined ? '' : `«${pick.said ? 'верно' : 'неверно'}» для `}`
        + `<span class="picked" lang="zh-Hans">${pick.said !== undefined && pick.isTrue ? '✓' : '✕'} ${escapeHtml(picked.zh)}</span> · ` : '',
```

Клавиатура: после `RATE_KEYS`:

```js
const TRUE_FALSE_KEYS = {
  Digit1: true, Numpad1: true, ArrowLeft: true, Digit2: false, Numpad2: false, ArrowRight: false,
};
```

В обработчике после ветки `state.stage === 'rate'`:

```js
  if (state.stage === 'tf' && !state.answered) {
    const said = TRUE_FALSE_KEYS[event.code];
    if (said !== undefined) {
      event.preventDefault();
      answerTrueFalse(said);
    }
    return;
  }
```

Обвязка — после обработчиков «Вспомни сам»:

```js
$('tfTrue').addEventListener('click', () => answerTrueFalse(true));
$('tfFalse').addEventListener('click', () => answerTrueFalse(false));
```

- [ ] **Шаг 5: стили** — в `src/quiz.css` в конец раздела «„Вспомни сам“ и „Верно или нет“»:

```css
.tf-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--s-2);
  padding: var(--s-6) var(--s-5);
  border: var(--border-hair) solid var(--line-on-ground-strong);
  border-radius: var(--radius-sm);
  background: var(--surface-raised);
}
.tf-card p { margin: 0; }
.tf-option {
  font-family: var(--font-han);
  font-size: 44px;
  font-weight: var(--t-weight-bold);
  line-height: 1.2;
  text-align: center;
  overflow-wrap: anywhere;
}
.tf-buttons { display: grid; grid-template-columns: 1fr 1fr; gap: var(--s-3); margin-top: var(--s-3); }
.tf-buttons .ink-btn { min-height: 64px; }
.tf-buttons .ink-btn[aria-pressed='true'] {
  border-style: solid;
  border-color: var(--text-on-ground);
  background: var(--text-on-ground);
  color: var(--surface-ground);
}
```

(Правило `aria-pressed` для `.recall-rate` из задачи 4 можно объединить с этим одним селектором через запятую.) В `@media (max-width: 600px)`: `.tf-option { font-size: 34px; }`.

- [ ] **Шаг 6: `CHANGELOG.md`** — пункт в тот же раздел:

```markdown
- «Верно или нет»: вопрос и один предложенный ответ (правильный с вероятностью ½, неверный — из всех
  вариантов, у записи с общим набором — из набора), кнопки и ← / →. Ошибка — как обычная (в «Ошибки»,
  повтор в раунде); верный ответ отмечает вопрос пройденным, но не сдвигает повторение и не выводит
  из «Ошибок». После ответа — подпись к предложенному варианту, правильный ответ, пояснение; над
  ходом раунда — серия верных подряд.
```

- [ ] **Шаг 7: сборка и все тесты.**

Run: `python3 scripts/build_html.py && node --test test/*.test.mjs && python3 -m unittest discover -s test -t .`
Expected: PASS.

- [ ] **Шаг 8: глазами** — превью `dist/`, обе темы, 360 px: карточка «Предложенный ответ», две кнопки, выбранная залита, разбор с подписью.

- [ ] **Шаг 9: коммит.**

```bash
git add src/template.html src/quiz.ui.js src/quiz.css test/ui.test.mjs CHANGELOG.md dist/lingvostranovedenie-trainer.html
git commit -m "Формат «Верно или нет»

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Задача 6: полная проверка ветки

**Files:** без новых правок, кроме найденных проверкой.

- [ ] **Шаг 1: полная сборка из первоисточников, как в CI.**

Run: `npm run build && git status --short`
Expected: сборка без нарушений; в `git status` нет изменений в `data/` и `dist/` (всё уже собрано и закоммичено), кроме неотслеживаемого `.claude/`.

- [ ] **Шаг 2: все тесты.**

Run: `python3 -m unittest discover -s test -t . && node --test test/*.test.mjs`
Expected: PASS, браузерные тесты не пропущены (Chrome установлен).

- [ ] **Шаг 3: сверка со спецификацией** — пройтись по разделам `docs/superpowers/specs/2026-10-15-recall-and-true-false-design.md` и отметить каждое требование в работающем `dist/`: таблица исходов, «нужны варианты», итоги, клавиатура обоих форматов, «Чэнъюй» не изменился. Расхождения — чинить в этой ветке отдельным коммитом с записью в `CHANGELOG.md`.

- [ ] **Шаг 4: перед слиянием** — спросить автора, нужно ли ревью ветки (правило из `~/.claude/CLAUDE.md`), одной строкой назвав, что в ветке.
