const STORAGE_KEY = 'lingvo-trainer:v1';
const STUDY_SETTINGS_KEY = 'lingvo-trainer:settings:v1';
const THEME_KEY = 'lingvo-trainer:theme';
const PINYIN_KEY = 'lingvo-trainer:pinyin';
const STAGE_NAMES = {
  pri: 'пригласительный', shk: 'школьный', mun: 'муниципальный',
  reg: 'региональный', zak: 'заключительный',
};
const STAGE_ORDER = ['pri', 'shk', 'mun', 'reg', 'zak'];
const STATUS_NAMES = {
  verified: 'проверено', unverified: 'не проверено',
  conflict: 'расхождение ключей', 'needs-review': 'нет ответа',
};

// знак-иероглиф темы на главной; тема без знака получает 文
const TOPIC_MARKS = {
  'История и государство': '史',
  'География и административное устройство': '地',
  'Культура, традиции и праздники': '节',
  'Литература, язык, искусство и философия': '文',
  'Общество: население, этносы и религии': '民',
  'Экономика, образование, наука и спорт': '经',
  'Россия и межкультурный блок': '俄',
};
// до стольких вопросов ход раунда рисуется кружками, длиннее — полосой
const MAX_STEP_DOTS = 14;
// на телефоне под кнопкой «Следующий вопрос» после докрутки остаётся столько воздуха
const BOTTOM_GAP = 24;
const THEME_COLORS = { light: '#faf4e8', dark: '#181512' };
const FORMAT_COPY = {
  choice: 'Вопрос и четыре варианта — как на олимпиаде.',
  recall: 'Сначала вспомните ответ сами, варианты — только как подсказка.',
  truefalse: 'Вопрос и один предложенный ответ: правильный он или нет?',
};
// подсказка клавиш — по стадии вопроса: во «Вспомни сам» цифры то оценивают, то выбирают вариант
const QUIZ_HINTS = {
  choice: '1–4 или A–D — ответить · Enter — дальше · P — пиньинь · Esc — выйти из раунда',
  hint: '1–4 или A–D — ответить · Enter — дальше · P — пиньинь · Esc — выйти из раунда',
  recall: 'Пробел — показать ответ · V — варианты · P — пиньинь · Esc — выйти из раунда',
  rate: '1 — вспомнил сам · 2 — неточно · 3 — не вспомнил · Enter — дальше · P — пиньинь · Esc — выйти из раунда',
  tf: '1 или ← — верно · 2 или → — неверно · Enter — дальше · P — пиньинь · Esc — выйти из раунда',
};

const $ = (id) => document.getElementById(id);

const defaultFilters = () => ({
  topics: [], years: [], stages: [], mode: 'all', onlyVerified: false, origin: 'all',
});

function defaultStudySettings() {
  return { filters: defaultFilters(), size: 10, format: 'choice' };
}

function loadStudySettings() {
  try {
    const stored = JSON.parse(localStorage.getItem(STUDY_SETTINGS_KEY) || '{}');
    if (stored.version !== 1) return defaultStudySettings();
    return normaliseStudySettings(stored.settings, QUESTION_BANK);
  } catch {
    return defaultStudySettings();
  }
}

const savedStudySettings = loadStudySettings();

const state = {
  filters: savedStudySettings.filters,
  size: savedStudySettings.size,
  format: savedStudySettings.format,
  // формат замораживается на старте раунда: настройки во время раунда не видны
  roundFormat: 'choice',
  // стадия вопроса: 'choice' — сетка вариантов; во «Вспомни сам» 'recall' → 'rate' или 'hint';
  // в «Верно или нет» — 'tf'
  stage: 'choice',
  // первые попытки во «Вспомни сам» по самооценке — для строки в итогах
  recallCounts: { correct: 0, partial: 0, wrong: 0 },
  // «Верно или нет»: утверждение текущего вопроса и верные ответы подряд в раунде
  statement: null,
  streak: 0,
  round: [],
  wrongIds: [],
  // ответ ученика на каждую ошибку раунда (первую попытку) — для списка в итогах
  wrongPicks: {},
  // верно/неверно по позициям раунда — для кружков хода
  marks: [],
  position: 0,
  correct: 0,
  initialRoundLength: 0,
  answered: false,
  retryQueue: [],
  retriedIds: new Set(),
  view: 'setup',
  progress: loadProgress(),
  databasePage: 0,
};

/* ---------- тема ---------- */

function systemTheme() {
  return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  $('themeLabel').textContent = theme === 'dark' ? 'Тема: тёмная' : 'Тема: светлая';
  $('themeColorMeta')?.setAttribute('content', THEME_COLORS[theme]);
}

function initTheme() {
  let stored = null;
  try {
    stored = localStorage.getItem(THEME_KEY);
  } catch {
    /* приватный режим: тема следует за системной */
  }
  applyTheme(stored || systemTheme());
  if (!stored && window.matchMedia) {
    // пока выбор не сделан вручную, тема идёт за системной
    window.matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', (event) => applyTheme(event.matches ? 'dark' : 'light'));
  }
}

function toggleTheme() {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  try {
    localStorage.setItem(THEME_KEY, next);
  } catch {
    /* выбор не переживёт перезагрузку, но в этой сессии работает */
  }
}

/* ---------- пиньинь ---------- */

// транскрипция лежит в разметке всегда, а показывает её атрибут на <html>: настройку можно
// переключить посреди вопроса, ничего не перерисовывая
function applyPinyin(on) {
  document.documentElement.dataset.pinyin = on ? 'on' : 'off';
  $('pinyinLabel').textContent = on ? 'Пиньинь: вкл' : 'Пиньинь: выкл';
  $('pinyinToggle').setAttribute('aria-pressed', String(on));
}

function initPinyin() {
  let on = false;
  try {
    on = localStorage.getItem(PINYIN_KEY) === 'on';
  } catch { /* приватный режим: по умолчанию выключено */ }
  applyPinyin(on);
}

function togglePinyin() {
  const on = document.documentElement.dataset.pinyin !== 'on';
  applyPinyin(on);
  try {
    localStorage.setItem(PINYIN_KEY, on ? 'on' : 'off');
  } catch {}
}

/** Строка транскрипции под китайским текстом; null, если её нет в таблице. */
function pinyinLine(text) {
  if (!PINYIN[text]) return null;
  const line = document.createElement('span');
  line.className = 'pinyin';
  line.lang = 'zh-Latn-pinyin';
  line.textContent = PINYIN[text];
  return line;
}

/** Русский вопрос: над каждым иероглифом китайской вставки — его слог (<ruby>). */
function questionNodes(text) {
  return pinyinSegments(text, PINYIN).flatMap((part) => {
    if (!part.pinyin) return [document.createTextNode(part.text)];
    return rubyPairs(part.text, part.pinyin).map((pair) => {
      if (!pair.pinyin) return document.createTextNode(pair.text);
      const ruby = document.createElement('ruby');
      ruby.lang = 'zh-Hans';
      const reading = document.createElement('rt');
      reading.className = 'pinyin';
      reading.lang = 'zh-Latn-pinyin';
      reading.textContent = pair.pinyin;
      ruby.append(pair.text, reading);
      return ruby;
    });
  });
}

/* ---------- прогресс ---------- */

function loadProgress() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    return stored.version === 1 && isValidProgress(stored.progress)
      ? migrateProgress(QUESTION_BANK, stored.progress) : {};
  } catch {
    return {};
  }
}

function saveProgress() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, progress: state.progress }));
  } catch {
    /* приватный режим: прогресс живёт только до перезагрузки */
  }
}

function saveStudySettings() {
  try {
    localStorage.setItem(STUDY_SETTINGS_KEY, JSON.stringify({
      version: 1,
      settings: { filters: state.filters, size: state.size, format: state.format },
    }));
  } catch {}
}

// в файле — прогресс обоих разделов: `chengyu` (cy из src/chengyu.ui.js) прежние версии
// тренажёра просто не читают, поэтому версия формата остаётся первой
function exportProgress() {
  const saved = { version: 1, progress: state.progress, chengyu: cy.progress };
  const blob = new Blob([JSON.stringify(saved, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `lingvo-trainer-progress-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function importProgress(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const parsed = JSON.parse(reader.result);
      if (parsed.version !== 1 || !isValidProgress(parsed.progress)
          || ('chengyu' in parsed && !cyIsValidProgress(parsed.chengyu))) {
        throw new Error('неверный формат файла');
      }
      // в файле из прежней версии нет «Чэнъюй» — тогда прогресс этого раздела не трогаем
      const sections = 'chengyu' in parsed ? 'основного тренажёра и «Чэнъюй»' : 'основного тренажёра';
      if (!confirm(`Загрузить прогресс из файла? Текущий прогресс ${sections} на этом устройстве будет заменён.`)) return;
      state.progress = migrateProgress(QUESTION_BANK, parsed.progress);
      saveProgress();
      if ('chengyu' in parsed) {
        cy.progress = parsed.chengyu;
        cySaveProgress();
        cyRenderSetup();
      }
      renderSetup();
    } catch {
      alert('Не удалось загрузить прогресс: файл повреждён или сохранён другой версией тренажёра.');
    }
  };
  reader.readAsText(file);
}

/* ---------- экраны ---------- */

function show(view) {
  // кнопка, с которой ушли на другой экран, скрывается вместе с ним; пока браузер сам не снял
  // с неё фокус, быстрый пробел или Enter достались бы ей, а не новому экрану
  document.activeElement?.blur?.();
  state.view = view;
  document.body.dataset.view = view;
  for (const [name, id] of Object.entries({
    setup: 'setupView', quiz: 'quizView', results: 'resultsView', database: 'databaseView',
    // раздел «Чэнъюй» (src/chengyu.ui.js)
    'cy-setup': 'cySetupView', 'cy-quiz': 'cyQuizView', 'cy-results': 'cyResultsView',
    'cy-reference': 'cyReferenceView',
  })) {
    $(id).hidden = name !== view;
  }
  const chengyu = view.startsWith('cy-');
  // адрес следует за разделом: перезагрузка открывает тот же раздел, а ссылка #chengyu
  // из другого раздела снова срабатывает (hashchange)
  if (chengyu !== (location.hash === '#chengyu')) {
    try {
      history.replaceState(null, '', `${location.pathname}${location.search}${chengyu ? '#chengyu' : ''}`);
    } catch { /* без истории адрес просто не меняется */ }
  }
  for (const [link, current] of [
    ['navSetup', !chengyu && view !== 'database'],
    ['navDatabase', view === 'database'],
    ['navChengyu', chengyu],
  ]) {
    if (current) $(link).setAttribute('aria-current', 'page');
    else $(link).removeAttribute('aria-current');
  }
  window.scrollTo?.(0, 0);
}

function renderStats() {
  const seasons = new Set(QUESTION_BANK.flatMap((r) => r.occurrences.map((o) => o.year))).size;
  const topics = new Set(QUESTION_BANK.map((r) => r.topic)).size;
  const stats = [
    ['statQuestions', QUESTION_BANK.length, ['вопрос в базе', 'вопроса в базе', 'вопросов в базе']],
    ['statSeasons', seasons, ['сезон олимпиады', 'сезона олимпиады', 'сезонов олимпиады']],
    ['statTopics', topics, ['тема', 'темы', 'тем']],
  ];
  for (const [id, count, forms] of stats) {
    $(id).textContent = String(count);
    $(`${id}Label`).textContent = pluralRu(count, forms);
  }
}

function stageLabel(code) {
  return STAGE_NAMES[code] || code;
}

/** «ВсОШ 2015/16 · региональный этап · задание 9» */
function occurrenceLabel(occurrence) {
  return `ВсОШ ${occurrence.year.replace('-', '/')} · ${stageLabel(occurrence.stageCode)} этап${
    occurrence.number ? ` · задание ${occurrence.number}` : ''}`;
}

function renderBankCount() {
  // по банку, а не по всем записям прогресса: у снятых вопросов прогресс остаётся в браузере
  const done = QUESTION_BANK.filter((record) => state.progress[record.id]?.completed).length;
  $('bankCount').textContent = `Пройдено ${done} из ${QUESTION_BANK.length}`;
}

function renderSetup() {
  const topics = [...new Set(QUESTION_BANK.map((r) => r.topic))].sort();
  if (!$('topicControls').children.length) {
    for (const topic of topics) {
      const label = document.createElement('label');
      label.className = 'topic-check';
      const mark = document.createElement('span');
      mark.className = 'topic-mark';
      mark.lang = 'zh-Hans';
      mark.setAttribute('aria-hidden', 'true');
      mark.textContent = TOPIC_MARKS[topic] || '文';
      const text = document.createElement('span');
      text.className = 'topic-text';
      const caption = document.createElement('span');
      caption.className = 'topic-name';
      caption.textContent = topic;
      const count = document.createElement('span');
      count.className = 'topic-count';
      const progress = document.createElement('span');
      progress.className = 'topic-progress';
      count.append('пройдено ', progress);
      text.append(caption, count);
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.value = topic;
      label.append(mark, text, input);
      input.addEventListener('change', (event) => {
        const list = state.filters.topics;
        if (event.target.checked) list.push(topic);
        else list.splice(list.indexOf(topic), 1);
        saveStudySettings();
        renderSetup();
      });
      $('topicControls').append(label);
    }

    const years = [...new Set(QUESTION_BANK.flatMap((r) => r.occurrences.map((o) => o.year)))].sort();
    fillSelect($('yearFilter'), 'Все годы', years.map((y) => [y, y]));
    const stages = STAGE_ORDER.filter((code) =>
      QUESTION_BANK.some((r) => r.occurrences.some((o) => o.stageCode === code)));
    fillSelect($('stageFilter'), 'Все этапы', stages.map((code) => [code, stageLabel(code)]));
    fillSelect($('databaseTopic'), 'Все темы', topics.map((t) => [t, t]));
  }

  const counts = progressByTopic(QUESTION_BANK, state.progress);
  for (const label of $('topicControls').children) {
    const input = label.querySelector('input');
    input.checked = state.filters.topics.includes(input.value);
    const { completed, total } = counts[input.value];
    label.querySelector('.topic-progress').textContent = `${completed}/${total}`;
  }
  $('yearFilter').value = state.filters.years[0] || '';
  $('stageFilter').value = state.filters.stages[0] || '';
  const size = state.size === Number.MAX_SAFE_INTEGER ? 'all' : String(state.size);
  for (const input of document.querySelectorAll('input[name="roundSize"]')) {
    input.checked = input.value === size;
  }
  $('onlyVerified').checked = state.filters.onlyVerified;
  for (const input of document.querySelectorAll('input[name="studyMode"]')) {
    input.checked = input.value === state.filters.mode;
  }
  const modeCopy = {
    all: 'Все доступные вопросы в случайном порядке.',
    new: 'Только вопросы, на которые вы ещё не отвечали.',
    mistakes: 'Вопросы, в которых последний ответ был ошибочным.',
    due: 'Пройденные вопросы, срок повторения которых наступил.',
  };
  $('modeHelp').textContent = modeCopy[state.filters.mode];
  for (const input of document.querySelectorAll('input[name="studyFormat"]')) {
    input.checked = input.value === state.format;
  }
  $('formatHelp').textContent = FORMAT_COPY[state.format];
  for (const input of document.querySelectorAll('input[name="studyOrigin"]')) {
    input.checked = input.value === state.filters.origin;
  }
  const additions = QUESTION_BANK.filter((record) => record.origin === 'addition').length;
  const olympiad = QUESTION_BANK.length - additions;
  $('originHelp').textContent = {
    all: `Задания олимпиад (${olympiad}) и проверенные дополнения к ним (${additions}).`,
    olympiad: `Только задания, которые были на ВсОШ: ${olympiad}.`,
    addition: `Только проверенные дополнения — на олимпиаде их не было: ${additions}. Год и этап к ним не относятся.`,
  }[state.filters.origin];
  $('verifiedFilterWrap').hidden = !QUESTION_BANK.some((record) => record.answer.state === 'unverified');
  renderFoldValues();

  const pool = eligible(QUESTION_BANK, state.filters, state.progress);
  $('eligibleNotice').textContent = pool.length
    ? state.filters.mode === 'due'
      ? `К повторению готово: ${pool.length}.`
      : `Под фильтры подходит вопросов: ${pool.length}.`
    : state.filters.mode === 'due'
      ? 'Нет вопросов для повторения по текущим фильтрам.'
      : 'Под текущие фильтры не подходит ни один вопрос — снимите часть ограничений.';
  $('startButton').disabled = pool.length === 0;
  // главная кнопка на экране одна: без подходящих вопросов это «Начать обычный раунд»
  $('startButton').classList.toggle('ink-btn--primary', pool.length !== 0);
  $('startButton').classList.toggle('ink-btn--secondary', pool.length === 0);
  $('emptyActions').hidden = pool.length !== 0;
  renderBankCount();
}

/** Свёрнутые «Режим», «Формат», «Темы раунда»: в заголовке — что выбрано сейчас. */
function renderFoldValues() {
  const picked = (name) => document.querySelector(`input[name="${name}"]:checked`)?.nextElementSibling?.textContent;
  $('modeValue').textContent = picked('studyMode') || '';
  $('formatValue').textContent = picked('studyFormat') || '';
  const { topics, years, stages, origin, onlyVerified } = state.filters;
  $('topicsValue').textContent = [
    topics.length === 0 ? 'все темы'
      : topics.length === 1 ? topics[0] : `${topics.length} ${pluralRu(topics.length, ['тема', 'темы', 'тем'])}`,
    origin === 'olympiad' ? 'только с олимпиад' : origin === 'addition' ? 'только дополнения' : '',
    years[0] ? years[0].replace('-', '/') : '',
    stages[0] ? `${stageLabel(stages[0])} этап` : '',
    onlyVerified ? 'только проверенные' : '',
  ].filter(Boolean).join(' · ');
}

function fillSelect(select, allLabel, pairs) {
  select.innerHTML = `<option value="">${allLabel}</option>`;
  for (const [value, label] of pairs) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = label;
    select.append(option);
  }
}

/* ---------- раунд ---------- */

function startRound() {
  const pool = eligible(QUESTION_BANK, state.filters, state.progress);
  if (!pool.length) return;
  startRoundWith(buildRound(QUESTION_BANK, state.filters, state.progress, state.size));
}

function startRoundWith(round, format = state.format) {
  state.roundFormat = format;
  state.recallCounts = { correct: 0, partial: 0, wrong: 0 };
  state.streak = 0;
  state.round = round;
  state.wrongIds = [];
  state.wrongPicks = {};
  state.marks = [];
  // вид хода выбирается по исходной длине: вставленные повторы ошибок удлиняют раунд,
  // и кружки не должны посреди раунда смениться полосой
  state.stepDots = round.length <= MAX_STEP_DOTS;
  state.position = 0;
  state.correct = 0;
  state.initialRoundLength = round.length;
  state.retryQueue = [];
  state.retriedIds = new Set();
  show('quiz');
  renderQuestion();
}

function repeatMistakes() {
  const wrong = wrongQuestions(state.round, state.wrongIds);
  if (wrong.length) startRoundWith(wrong, state.roundFormat);
}

function renderQuestion() {
  const record = state.round[state.position];
  if (!record) return finishRound();

  state.answered = false;
  const origin = recordOrigin(record);
  const first = origin.isAddition ? null : matchingOccurrence(record, state.filters);
  $('progressLabel').textContent = `Вопрос ${state.position + 1} из ${state.round.length}`;
  renderProgress();
  $('topicLabel').textContent = record.topic;
  $('sourceLabel').textContent = origin.isAddition
    ? 'Проверенное дополнение'
    : occurrenceLabel(first);
  $('originPill').textContent = origin.label;
  $('originPill').hidden = !origin.isAddition;
  $('unverifiedPill').hidden = record.answer.state !== 'unverified';
  $('retryPill').hidden = !isRepeatInRound(state.round, state.position);
  $('questionText').replaceChildren(...questionNodes(record.questionRu));
  $('questionZh').replaceChildren(...[record.questionZh || '', pinyinLine(record.questionZh)].filter(Boolean));
  $('questionZh').hidden = !record.questionZh;

  $('feedback').className = 'feedback hidden';
  $('nextButton').classList.add('hidden');
  $('options').innerHTML = '';
  for (const id of ['recallNote', 'recallPrompt', 'recallRate', 'tfPanel']) $(id).classList.add('hidden');
  for (const button of $('recallRate').querySelectorAll('button')) {
    button.disabled = false;
    button.removeAttribute('aria-pressed');
  }
  if (state.roundFormat === 'truefalse') {
    setStage('tf');
    state.statement = trueFalseStatement(record);
    $('tfOption').replaceChildren(...[state.statement.zh, pinyinLine(state.statement.zh)].filter(Boolean));
    for (const button of $('tfPanel').querySelectorAll('button')) {
      button.disabled = false;
      button.removeAttribute('aria-pressed');
    }
    $('tfPanel').classList.remove('hidden');
    return;
  }
  if (state.roundFormat === 'recall' && !needsOptions(record)) {
    setStage('recall');
    $('recallPrompt').classList.remove('hidden');
    return;
  }
  setStage('choice');
  if (state.roundFormat === 'recall') showRecallNote('На этот вопрос без вариантов не ответить — выберите из четырёх.');
  renderOptions(record);
}

function setStage(stage) {
  state.stage = stage;
  $('quizHint').textContent = QUIZ_HINTS[stage];
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
    caption.append(...[option.zh, pinyinLine(option.zh)].filter(Boolean));
    button.append(letter, caption);
    button.addEventListener('click', () => chooseOption(record, option.optionId));
    $('options').append(button);
  }
}

/** Ход раунда: кружки ✓/✕ до MAX_STEP_DOTS вопросов, дальше — полоса. */
function renderProgress() {
  const total = state.round.length;
  const dots = state.stepDots;
  $('progressSteps').hidden = !dots;
  $('progressTrack').hidden = dots;
  $('scoreLabel').textContent = `верно ${state.correct}${
    state.roundFormat === 'truefalse' ? ` · серия ${state.streak}` : ''}`;
  if (!dots) {
    const done = state.position + (state.answered ? 1 : 0);
    $('progressFill').style.width = `${(done / total) * 100}%`;
    return;
  }
  $('progressSteps').replaceChildren(...state.round.map((_, index) => {
    const step = document.createElement('li');
    const mark = state.marks[index];
    const current = index === state.position;
    step.className = ['ink-step', mark === true ? 'ink-step--correct' : '', mark === false ? 'ink-step--wrong' : '',
      current ? 'ink-step--current' : ''].filter(Boolean).join(' ');
    if (mark !== undefined) step.lang = 'zh-Hans';
    step.textContent = mark === true ? '✓' : mark === false ? '✕' : current ? String(index + 1) : '';
    step.setAttribute('aria-label', `${index + 1}${mark === true ? ' — верно' : mark === false ? ' — ошибка' : ''}${
      current ? ', текущий' : ''}`);
    return step;
  }));
}

/** Общее для любого формата: прогресс, счёт раунда, повтор ошибки, ход, кнопка «дальше». */
function commitAnswer(record, outcome, pick = {}) {
  state.answered = true;
  const right = outcome !== 'wrong';
  state.progress[record.id] = applyAnswer(state.progress[record.id], outcome);
  saveProgress();
  if (state.roundFormat === 'recall' && !isRepeatInRound(state.round, state.position)) {
    state.recallCounts[outcome] += 1;
  }
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
    sources ? sourcesBlock(sources, record.evidence.length) : '',
    record.answer.state === 'unverified'
      ? '<p class="unverified">Ответ взят из официального ключа, но ещё не перепроверен по источникам.</p>'
      : '',
  ].join('');
  requestAnimationFrame(() => {
    $('feedback').focus({ preventScroll: true });
    // на телефоне докручиваем до следующего шага под разбором: кнопки «Следующий вопрос»,
    // а во «Вспомни сам» до неё — до самооценки (решение автора: всегда до кнопки)
    revealOnPhone([$('nextButton'), $('recallRate')].find((element) => !element.classList.contains('hidden'))
      || $('feedback'));
  });
}

/** Источники: одна-две ссылки видны сразу, больше — под «Источники (N)», чтобы разбор
 * с кнопкой «Следующий вопрос» помещался на экран телефона. */
function sourcesBlock(items, count) {
  return count > 2
    ? `<details class="feedback-sources"><summary>Источники (${count})</summary><ul>${items}</ul></details>`
    : `<ul>${items}</ul>`;
}

const onPhone = () => Boolean(window.matchMedia?.('(max-width: 600px)').matches);
const scrollBehavior = () => (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth');

/** Телефон: прокрутить вниз ровно настолько, чтобы низ элемента встал над краем экрана.
 * Высота — видимой части (visualViewport): в Safari нижняя панель закрывает низ окна, и
 * scrollIntoView ставил кнопку под неё. Вверх не прокручивает. */
function revealOnPhone(element) {
  if (!onPhone()) return;
  // низ видимой части в координатах окна; при увеличении щипком она сдвинута на offsetTop
  const viewport = window.visualViewport;
  const visibleBottom = viewport ? viewport.offsetTop + viewport.height : window.innerHeight;
  const top = window.scrollY + element.getBoundingClientRect().bottom + BOTTOM_GAP - visibleBottom;
  if (top > window.scrollY + 1) window.scrollTo({ top, behavior: scrollBehavior() });
}

/** Телефон: начало элемента — к верху экрана (новый вопрос после «Следующего вопроса»). */
function scrollToTopOnPhone(element) {
  if (onPhone()) element.scrollIntoView({ behavior: scrollBehavior(), block: 'start' });
}

/* ---------- «Вспомни сам» ---------- */

function showRecallNote(text) {
  $('recallNote').textContent = text;
  $('recallNote').classList.remove('hidden');
}

function revealAnswer() {
  if (state.stage !== 'recall' || state.answered) return;
  const record = state.round[state.position];
  const right = record.options.find((option) => option.id === record.answer.optionId);
  setStage('rate');
  $('recallPrompt').classList.add('hidden');
  const reading = PINYIN[right.zh]
    ? `<span class="pinyin" lang="zh-Latn-pinyin">${escapeHtml(PINYIN[right.zh])}</span>` : '';
  showFeedback(record, 'reveal',
    `<strong lang="zh-Hans">${escapeHtml(right.zh)}</strong>${reading}<span>Правильный ответ</span>`);
  $('recallRate').classList.remove('hidden');
}

function showHint() {
  if (state.stage !== 'recall' || state.answered) return;
  setStage('hint');
  $('recallPrompt').classList.add('hidden');
  showRecallNote('С подсказкой верный ответ засчитается как «вспомнил неточно».');
  renderOptions(state.round[state.position]);
  // кнопка «Не помню» скрылась вместе с фокусом: ставим его на первый вариант
  $('options').querySelector('button')?.focus();
}

function rateRecall(outcome) {
  if (state.stage !== 'rate' || state.answered) return;
  commitAnswer(state.round[state.position], outcome);
  for (const button of $('recallRate').querySelectorAll('button')) {
    button.disabled = true;
    if (button.dataset.outcome === outcome) button.setAttribute('aria-pressed', 'true');
  }
  // нажатая кнопка оценки погасла вместе с фокусом: следующий шаг — «Следующий вопрос»;
  // фокус без своей прокрутки — она поставила бы кнопку под нижнюю панель Safari
  $('nextButton').focus({ preventScroll: true });
  revealOnPhone($('nextButton'));
}

/* ---------- «Верно или нет» ---------- */

function answerTrueFalse(saidTrue) {
  if (state.stage !== 'tf' || state.answered) return;
  const record = state.round[state.position];
  const statement = state.statement;
  const right = statement.isTrue === saidTrue;
  // серия меняется до commitAnswer: тот перерисовывает ход раунда вместе со строкой серии
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

function evidenceList(evidence = []) {
  return evidence.map((source) => {
    const url = safeSourceUrl(source.url);
    const title = escapeHtml(source.title);
    const label = url
      ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${title}</a>`
      : title;
    const checked = source.checkedAt
      ? ` <span class="muted">(проверено ${escapeHtml(source.checkedAt)})</span>` : '';
    return `<li>${label}${checked}</li>`;
  }).join('');
}

function glossList(record) {
  const items = optionGlosses(record);
  if (!items.length) return '';
  return '<p class="row-sources-title">Другие варианты</p><ul class="row-glosses">'
    + items.map(({ zh, gloss }) => `<li><span class="zh" lang="zh-Hans">${escapeHtml(zh)}</span> — ${escapeHtml(gloss)}</li>`).join('')
    + '</ul>';
}

function nextQuestion() {
  if (!state.answered) return;
  // «Следующий вопрос» сейчас скроется: фокус с него снимаем сразу (см. show)
  $('nextButton').blur();
  state.position += 1;
  const retryIndex = nextRetryInsertion(state.retryQueue, state.position, state.round.length);
  if (retryIndex !== -1) {
    const [retry] = state.retryQueue.splice(retryIndex, 1);
    state.round.splice(state.position, 0, retry.record);
  }
  if (state.position >= state.round.length) finishRound();
  else {
    renderQuestion();
    // после разбора страница прокручена вниз — новый вопрос начинается выше
    scrollToTopOnPhone($('quizView'));
  }
}

function finishRound() {
  const total = state.initialRoundLength;
  const wrongCount = state.wrongIds.length;
  // «9 / 10»: делитель тише счёта, но текст тот же, что даёт roundScore
  const [score, outOf] = roundScore(state.correct, total).split(' / ');
  $('finalScore').innerHTML = `${escapeHtml(score)}<span class="score-total"> / ${escapeHtml(outOf)}</span>`;
  $('resultMeterCorrect').style.flex = String(state.correct);
  $('resultMeterWrong').style.flex = String(wrongCount);
  $('resultCounts').innerHTML = `<span><span class="ok" lang="zh-Hans">✓</span> верно — ${state.correct}</span>`
    + `<span><span class="bad" lang="zh-Hans">✕</span> с ошибкой — ${wrongCount}</span>`;
  const recall = state.recallCounts;
  $('resultRecall').hidden = state.roundFormat !== 'recall';
  $('resultRecall').textContent =
    `вспомнил сам — ${recall.correct} · неточно — ${recall.partial} · не вспомнил — ${recall.wrong}`;
  $('repeatMistakes').hidden = wrongCount === 0;
  $('repeatMistakes').textContent = `Повторить ошибки раунда (${wrongCount})`;
  // на экране одна главная кнопка: «Повторить ошибки», а без ошибок — «На главную»
  $('backToSetup').classList.toggle('ink-btn--primary', wrongCount === 0);
  $('backToSetup').classList.toggle('ink-btn--secondary', wrongCount !== 0);
  renderMistakes();
  const share = total ? state.correct / total : 0;
  $('resultText').textContent = share === 1
    ? 'Весь раунд без ошибок.'
    : share >= 0.7
      ? 'Хороший результат: ошибки стоит разобрать в базе вопросов.'
      : 'Есть над чем поработать — загляните в базу, там у каждого ответа есть пояснение.';
  show('results');
  renderSetup();
}

function renderMistakes() {
  const wrong = wrongQuestions(state.round, state.wrongIds);
  $('resultMistakes').hidden = wrong.length === 0;
  $('mistakeList').replaceChildren(...wrong.map((record) => {
    const pick = state.wrongPicks[record.id] ?? {};
    const picked = record.options.find((option) => option.id === pick.optionId);
    const right = record.options.find((option) => option.id === record.answer.optionId);
    const item = document.createElement('li');
    item.innerHTML = [
      '<span class="ink-seal ink-seal--review ink-seal--md" lang="zh-Hans" aria-hidden="true">复</span>',
      '<div>',
      `<p class="mistake-question">${escapeHtml(record.questionRu)}</p>`,
      '<p class="mistake-answers">',
      picked ? `Ваш ответ ${pick.said === undefined ? '' : `«${pick.said ? 'верно' : 'неверно'}» для `}`
        + `<span class="picked" lang="zh-Hans">${pick.said !== undefined && pick.isTrue ? '✓' : '✕'} ${escapeHtml(picked.zh)}</span> · ` : '',
      `верно <span class="right" lang="zh-Hans">✓ ${escapeHtml(right.zh)}</span>`,
      '</p></div>',
    ].join('');
    return item;
  }));
}

/* ---------- база ---------- */

function filteredDatabaseRows() {
  const topic = $('databaseTopic').value;
  const status = $('databaseStatus').value;
  return QUESTION_BANK.filter((record) =>
    matchesDatabaseSearch(record, $('databaseSearch').value)
    && (!topic || record.topic === topic)
    && (!status || record.answer.state === status));

}

function appendDatabaseRows(rows) {
  for (const record of rows) {
    const article = document.createElement('article');
    article.className = 'row';
    const answered = record.options.find((option) => option.id === record.answer.optionId);
    const done = state.progress[record.id]?.completed;
    const origin = recordOrigin(record);
    const appearances = record.occurrences.map(occurrenceLabel).join('; ');
    const sources = evidenceList(record.evidence);
    const verified = record.answer.state === 'verified';
    const disputed = record.answer.state === 'needs-review' || record.answer.state === 'conflict';
    article.innerHTML = [
      '<div class="row-top">',
      `<span class="row-topic">${escapeHtml(record.topic)}</span>`,
      `<span class="tag${verified ? ' done' : ''}${disputed ? ' review' : ''}">${
        verified ? '<span lang="zh-Hans" aria-hidden="true">✓</span> ' : ''}${STATUS_NAMES[record.answer.state]}</span>`,
      done ? '<span class="tag"><span lang="zh-Hans" aria-hidden="true">●</span> пройден</span>' : '',
      origin.isAddition ? `<span class="tag origin">${origin.label}</span>` : '',
      hasOptionPool(record) ? '<span class="tag">варианты меняются</span>' : '',
      record.parseWarnings?.length ? `<span class="tag warn">${escapeHtml(record.parseWarnings.join('; '))}</span>` : '',
      '</div>',
      `<h3>${escapeHtml(record.questionRu)}</h3>`,
      record.questionZh ? `<p class="row-zh-question" lang="zh-Hans">${escapeHtml(record.questionZh)}</p>` : '',
      `<p class="row-options" lang="zh-Hans">${record.options.map((o) => escapeHtml(o.zh)).join(' · ')}</p>`,
      appearances ? `<p class="row-meta">${escapeHtml(appearances)}</p>` : '',
      answered || record.explanation.ru ? [
        '<details class="row-reveal"><summary>Показать ответ</summary><div class="row-panel">',
        answered ? `<p class="row-answer">Ответ: <span class="zh" lang="zh-Hans">${escapeHtml(answered.zh)}</span></p>` : '',
        record.explanation.ru ? `<p class="row-why">${escapeHtml(record.explanation.ru)}</p>` : '',
        glossList(record),
        sources ? `<p class="row-sources-title">Источники</p><ul class="row-sources">${sources}</ul>` : '',
        '</div></details>',
      ].join('') : '',
    ].join('');
    const reveal = article.querySelector('.row-reveal');
    reveal?.addEventListener('toggle', () => {
      reveal.querySelector('summary').textContent = reveal.open ? 'Скрыть ответ' : 'Показать ответ';
    });
    $('databaseList').append(article);
  }
}

// «из 461 вопроса», «из 50 вопросов»: после «из» родительный падеж
const ofQuestions = (count) => pluralRu(count, ['вопроса', 'вопросов', 'вопросов']);

function renderDatabase(reset = true) {
  const rows = filteredDatabaseRows();
  if (reset) {
    state.databasePage = 0;
    $('databaseList').innerHTML = '';
  }
  if (!rows.length) {
    $('databaseCount').textContent = `Показано 0 из ${QUESTION_BANK.length} ${ofQuestions(QUESTION_BANK.length)}`;
    $('databaseList').innerHTML = '<p class="empty">Ничего не найдено.</p>';
    $('databaseMore').hidden = true;
    return;
  }
  appendDatabaseRows(databasePage(rows, state.databasePage, 50));
  state.databasePage += 1;
  const shown = Math.min(state.databasePage * 50, rows.length);
  $('databaseCount').textContent = `Показано ${shown} из ${rows.length} ${ofQuestions(rows.length)}`;
  $('databaseMore').hidden = shown >= rows.length;
  $('databaseMore').textContent = `Показать ещё (${rows.length - shown})`;
}

function openDatabase() {
  show('database');
  renderDatabase();
}

function backToSetup() {
  show('setup');
  renderSetup();
}

/* ---------- клавиатура ---------- */

const ANSWER_KEYS = {
  Digit1: 0, Digit2: 1, Digit3: 2, Digit4: 3,
  Numpad1: 0, Numpad2: 1, Numpad3: 2, Numpad4: 3,
  KeyA: 0, KeyB: 1, KeyC: 2, KeyD: 3,
};
const RATE_KEYS = {
  Digit1: 'correct', Numpad1: 'correct', Digit2: 'partial', Numpad2: 'partial', Digit3: 'wrong', Numpad3: 'wrong',
};
const TRUE_FALSE_KEYS = {
  Digit1: true, Numpad1: true, ArrowLeft: true, Digit2: false, Numpad2: false, ArrowRight: false,
};

document.addEventListener('keydown', (event) => {
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  const typing = ['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement?.tagName);
  // P — пиньинь на любом экране, как кнопка в шапке; код клавиши, а не символ: на русской
  // раскладке это «З»
  if (event.code === 'KeyP' && !typing) {
    event.preventDefault();
    togglePinyin();
    return;
  }
  // у раздела «Чэнъюй» своя клавиатура (src/chengyu.ui.js)
  if (state.view.startsWith('cy-')) return;

  if (event.key === 'Escape') {
    if (typing) document.activeElement.blur();
    else if (state.view !== 'setup') backToSetup();
    return;
  }

  if (typing) return;
  // на кнопке, ссылке или summary Enter и пробел делают своё дело, а не глобальное
  const onControl = Boolean(document.activeElement?.closest?.('a, button, summary'));

  if (state.view === 'database' && event.key === '/') {
    event.preventDefault();
    $('databaseSearch').focus();
    return;
  }

  if (state.view === 'setup' && event.key === 'Enter' && !onControl && !$('startButton').disabled) {
    event.preventDefault();
    startRound();
    return;
  }

  if (state.view !== 'quiz') return;

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
  if (state.stage === 'tf' && !state.answered) {
    const said = TRUE_FALSE_KEYS[event.code];
    if (said !== undefined) {
      event.preventDefault();
      answerTrueFalse(said);
    }
    return;
  }

  // код клавиши, а не символ: на русской раскладке те же клавиши дают Ф, И, С, В
  const index = ANSWER_KEYS[event.code];
  if (index !== undefined && !state.answered) {
    const button = $('options').querySelectorAll('button')[index];
    if (button) {
      event.preventDefault();
      button.click();
    }
    return;
  }

  if ((event.key === 'Enter' || event.key === ' ') && state.answered && !onControl) {
    event.preventDefault();
    nextQuestion();
  }
});

/* ---------- обвязка ---------- */

$('themeToggle').addEventListener('click', toggleTheme);
$('pinyinToggle').addEventListener('click', togglePinyin);
// шапка — ссылки, чтобы работали и без скрипта, но внутри страницы они просто меняют экран
for (const id of ['homeLink', 'navSetup']) {
  $(id).addEventListener('click', (event) => {
    event.preventDefault();
    backToSetup();
  });
}
$('navDatabase').addEventListener('click', (event) => {
  event.preventDefault();
  openDatabase();
});
$('startButton').addEventListener('click', startRound);
$('repeatMistakes').addEventListener('click', repeatMistakes);
$('nextButton').addEventListener('click', nextQuestion);
$('revealAnswer').addEventListener('click', revealAnswer);
$('showHint').addEventListener('click', showHint);
for (const button of $('recallRate').querySelectorAll('button')) {
  button.addEventListener('click', () => rateRecall(button.dataset.outcome));
}
$('tfTrue').addEventListener('click', () => answerTrueFalse(true));
$('tfFalse').addEventListener('click', () => answerTrueFalse(false));
$('leaveRound').addEventListener('click', backToSetup);
$('openDatabase').addEventListener('click', openDatabase);
$('resultsDatabase').addEventListener('click', openDatabase);
$('closeDatabase').addEventListener('click', backToSetup);
$('backToSetup').addEventListener('click', backToSetup);
$('databaseSearch').addEventListener('input', renderDatabase);
$('databaseTopic').addEventListener('change', renderDatabase);
$('databaseStatus').addEventListener('change', renderDatabase);
$('databaseMore').addEventListener('click', () => renderDatabase(false));

for (const input of document.querySelectorAll('input[name="roundSize"]')) {
  input.addEventListener('change', (event) => {
    state.size = event.target.value === 'all' ? Number.MAX_SAFE_INTEGER : Number(event.target.value);
    saveStudySettings();
    renderSetup();
  });
}
$('onlyVerified').addEventListener('change', (event) => {
  state.filters.onlyVerified = event.target.checked;
  saveStudySettings();
  renderSetup();
});
for (const input of document.querySelectorAll('input[name="studyMode"]')) {
  input.addEventListener('change', (event) => {
    state.filters.mode = event.target.value;
    saveStudySettings();
    renderSetup();
  });
}
for (const input of document.querySelectorAll('input[name="studyOrigin"]')) {
  input.addEventListener('change', (event) => {
    state.filters.origin = event.target.value;
    saveStudySettings();
    renderSetup();
  });
}
for (const input of document.querySelectorAll('input[name="studyFormat"]')) {
  input.addEventListener('change', (event) => {
    state.format = event.target.value;
    saveStudySettings();
    renderSetup();
  });
}
$('emptyReset').addEventListener('click', () => {
  state.filters = defaultFilters();
  saveStudySettings();
  renderSetup();
});
$('emptyAll').addEventListener('click', () => {
  state.filters = defaultFilters();
  saveStudySettings();
  startRound();
});
$('yearFilter').addEventListener('change', (event) => {
  state.filters.years = event.target.value ? [event.target.value] : [];
  saveStudySettings();
  renderSetup();
});
$('stageFilter').addEventListener('change', (event) => {
  state.filters.stages = event.target.value ? [event.target.value] : [];
  saveStudySettings();
  renderSetup();
});
$('clearFilters').addEventListener('click', () => {
  state.filters = defaultFilters();
  saveStudySettings();
  renderSetup();
});
$('resetProgress').addEventListener('click', () => {
  if (!confirm('Сбросить прогресс по всем вопросам?')) return;
  state.progress = {};
  saveProgress();
  renderSetup();
});
$('exportProgress').addEventListener('click', exportProgress);
$('importProgress').addEventListener('click', () => $('importProgressFile').click());
$('importProgressFile').addEventListener('change', (event) => {
  const [file] = event.target.files;
  if (file) importProgress(file);
  event.target.value = '';
});

$('footerNote').textContent = bankSummary(QUESTION_BANK);

initTheme();
initPinyin();
renderStats();
renderSetup();
show('setup');
