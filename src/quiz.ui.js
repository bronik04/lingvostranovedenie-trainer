const STORAGE_KEY = 'lingvo-trainer:v1';
const STUDY_SETTINGS_KEY = 'lingvo-trainer:settings:v1';
const THEME_KEY = 'lingvo-trainer:theme';
const STAGE_NAMES = {
  pri: 'пригласительный', shk: 'школьный', mun: 'муниципальный',
  reg: 'региональный', zak: 'заключительный',
};
const STAGE_ORDER = ['pri', 'shk', 'mun', 'reg', 'zak'];
const STATUS_NAMES = {
  verified: 'проверено', unverified: 'не проверено',
  conflict: 'расхождение ключей', 'needs-review': 'нет ответа',
};

const $ = (id) => document.getElementById(id);

const defaultFilters = () => ({
  topics: [], years: [], stages: [], mode: 'all', onlyVerified: false,
});

function defaultStudySettings() {
  return { filters: defaultFilters(), size: 10 };
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
  round: [],
  wrongIds: [],
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
  $('themeIcon').textContent = theme === 'dark' ? '☾' : '☀';
  $('themeLabel').textContent = theme === 'dark' ? 'Тёмная' : 'Светлая';
  $('themeColorMeta')?.setAttribute('content', theme === 'dark' ? '#6f9bff' : '#245eea');
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

/* ---------- прогресс ---------- */

function loadProgress() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    return stored.version === 1 && isValidProgress(stored.progress) ? stored.progress : {};
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
      settings: { filters: state.filters, size: state.size },
    }));
  } catch {}
}

function exportProgress() {
  const blob = new Blob([JSON.stringify({ version: 1, progress: state.progress }, null, 2)],
    { type: 'application/json' });
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
      if (parsed.version !== 1 || !isValidProgress(parsed.progress)) {
        throw new Error('неверный формат файла');
      }
      state.progress = parsed.progress;
      saveProgress();
      renderSetup();
    } catch {
      alert('Не удалось загрузить прогресс: файл повреждён или сохранён другой версией тренажёра.');
    }
  };
  reader.readAsText(file);
}

/* ---------- экраны ---------- */

function show(view) {
  state.view = view;
  for (const [name, id] of Object.entries({
    setup: 'setupView', quiz: 'quizView', results: 'resultsView', database: 'databaseView',
  })) {
    $(id).hidden = name !== view;
  }
}

function stageLabel(code) {
  return STAGE_NAMES[code] || code;
}

function renderBankCount() {
  const done = Object.values(state.progress).filter((item) => item.completed).length;
  $('bankCount').textContent = `Пройдено ${done} из ${QUESTION_BANK.length}`;
}

function renderSetup() {
  const topics = [...new Set(QUESTION_BANK.map((r) => r.topic))].sort();
  if (!$('topicControls').children.length) {
    for (const topic of topics) {
      const label = document.createElement('label');
      label.className = 'topic-check';
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.value = topic;
      const caption = document.createElement('span');
      caption.textContent = topic;
      const count = document.createElement('small');
      count.className = 'topic-progress';
      label.append(input, caption, count);
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
  $('roundSize').value = state.size === Number.MAX_SAFE_INTEGER ? 'all' : String(state.size);
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
  $('verifiedFilterWrap').hidden = !QUESTION_BANK.some((record) => record.answer.state === 'unverified');

  const pool = eligible(QUESTION_BANK, state.filters, state.progress);
  $('eligibleNotice').textContent = pool.length
    ? state.filters.mode === 'due'
      ? `К повторению готово: ${pool.length}.`
      : `Под фильтры подходит вопросов: ${pool.length}.`
    : state.filters.mode === 'due'
      ? 'Нет вопросов для повторения по текущим фильтрам.'
      : 'Под текущие фильтры не подходит ни один вопрос — снимите часть ограничений.';
  $('startButton').disabled = pool.length === 0;
  $('emptyActions').hidden = pool.length !== 0;
  renderBankCount();
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

function startRoundWith(round) {
  state.round = round;
  state.wrongIds = [];
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
  if (wrong.length) startRoundWith(wrong);
}

function renderQuestion() {
  const record = state.round[state.position];
  if (!record) return finishRound();

  state.answered = false;
  const origin = recordOrigin(record);
  const first = origin.isAddition ? null : matchingOccurrence(record, state.filters);
  $('progressLabel').textContent = `Вопрос ${state.position + 1} из ${state.round.length}`;
  $('scoreLabel').textContent = `Счёт: ${state.correct}`;
  $('progressFill').style.width = `${(state.position / state.round.length) * 100}%`;
  $('topicLabel').textContent = record.topic;
  $('sourceLabel').textContent = origin.isAddition
    ? 'Проверенное дополнение'
    : `${first.year}, ${stageLabel(first.stageCode)}${first.number ? ` · №${first.number}` : ''}`;
  $('originPill').textContent = origin.label;
  $('originPill').hidden = !origin.isAddition;
  $('unverifiedPill').hidden = record.answer.state !== 'unverified';
  $('questionText').textContent = record.questionRu;

  $('feedback').className = 'feedback hidden';
  $('nextButton').classList.add('hidden');
  $('options').innerHTML = '';
  for (const option of labelledOptions(record)) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'option';
    button.dataset.optionId = option.optionId;
    const letter = document.createElement('span');
    letter.className = 'letter';
    letter.textContent = option.label;
    const caption = document.createElement('span');
    caption.textContent = option.zh;
    button.append(letter, caption);
    button.addEventListener('click', () => answer(record, option.optionId));
    $('options').append(button);
  }
}

function answer(record, optionId) {
  if (state.answered) return;
  state.answered = true;

  const verdict = grade(record, optionId);
  const previous = state.progress[record.id] || { attempts: 0, correct: 0 };
  const review = scheduleReview(previous, verdict.correct);
  state.progress[record.id] = {
    attempts: previous.attempts + 1,
    correct: previous.correct + (verdict.correct ? 1 : 0),
    completed: true,
    lastCorrect: verdict.correct,
    box: review.box,
    dueAt: review.dueAt,
  };
  saveProgress();
  ({ correct: state.correct, wrongIds: state.wrongIds } =
    tallyAnswer({ correct: state.correct, wrongIds: state.wrongIds }, record.id, verdict.correct));
  if (!verdict.correct) {
    const retry = queueRetry(state.retryQueue, state.retriedIds, record, state.position);
    state.retryQueue = retry.queue;
    state.retriedIds = retry.retriedIds;
  }
  $('scoreLabel').textContent = `Счёт: ${state.correct}`;

  for (const button of $('options').querySelectorAll('button')) {
    button.disabled = true;
    if (button.dataset.optionId === verdict.answerOptionId) {
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
  }

  const right = record.options.find((option) => option.id === verdict.answerOptionId);
  const sources = evidenceList(record.evidence);

  $('feedback').className = `feedback ${verdict.correct ? 'good' : 'bad'}`;
  $('feedback').innerHTML = [
    `<p><strong>${verdict.correct ? 'Верно' : 'Неверно'}</strong>`,
    verdict.correct ? '' : `Правильный ответ: ${escapeHtml(right.zh)}.`,
    '</p>',
    record.explanation.ru ? `<p class="why">${escapeHtml(record.explanation.ru)}</p>` : '',
    sources ? `<ul>${sources}</ul>` : '',
    record.answer.state === 'unverified'
      ? '<p class="unverified">Ответ взят из официального ключа, но ещё не перепроверен по источникам.</p>'
      : '',
  ].join('');

  $('nextButton').textContent =
    state.position + 1 < state.round.length ? 'Следующий вопрос' : 'Итоги раунда';
  $('nextButton').classList.remove('hidden');
  requestAnimationFrame(() => {
    const compact = window.matchMedia?.('(max-width: 600px)').matches;
    const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    $('feedback').focus({ preventScroll: true });
    if (compact) $('feedback').scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'nearest' });
  });
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

function nextQuestion() {
  if (!state.answered) return;
  state.position += 1;
  const retryIndex = nextRetryInsertion(state.retryQueue, state.position, state.round.length);
  if (retryIndex !== -1) {
    const [retry] = state.retryQueue.splice(retryIndex, 1);
    state.round.splice(state.position, 0, retry.record);
  }
  if (state.position >= state.round.length) finishRound();
  else renderQuestion();
}

function finishRound() {
  const total = state.initialRoundLength;
  const wrongCount = state.wrongIds.length;
  $('finalScore').textContent = roundScore(state.correct, total);
  $('repeatMistakes').hidden = wrongCount === 0;
  $('repeatMistakes').textContent = `Повторить ошибки раунда (${wrongCount})`;
  const share = total ? state.correct / total : 0;
  $('resultText').textContent = share === 1
    ? 'Весь раунд без ошибок.'
    : share >= 0.7
      ? 'Хороший результат: ошибки стоит разобрать в базе вопросов.'
      : 'Есть над чем поработать — загляните в базу, там у каждого ответа есть пояснение.';
  show('results');
  renderSetup();
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
    const appearances = record.occurrences
      .map((o) => `${o.year} ${stageLabel(o.stageCode)}${o.number ? ` №${o.number}` : ''}`).join(' · ');
    const sources = evidenceList(record.evidence);
    article.innerHTML = [
      '<div class="row-top">',
      `<span class="tag">${escapeHtml(record.topic)}</span>`,
      origin.isAddition ? `<span class="tag origin">${origin.label}</span>` : '',
      `<span class="tag${record.answer.state === 'verified' ? ' done' : ''}${
        record.answer.state === 'needs-review' || record.answer.state === 'conflict' ? ' review' : ''
      }">${STATUS_NAMES[record.answer.state]}</span>`,
      done ? '<span class="tag done">пройден</span>' : '',
      record.parseWarnings?.length ? `<span class="tag warn">${escapeHtml(record.parseWarnings.join('; '))}</span>` : '',
      '</div>',
      `<h3>${escapeHtml(record.questionRu)}</h3>`,
      `<div class="row-options">${record.options.map((o) => escapeHtml(o.zh)).join(' · ')}</div>`,
      answered || record.explanation.ru ? [
        '<details class="row-reveal"><summary>Показать ответ</summary>',
        answered ? `<p class="row-answer">Ответ: ${escapeHtml(answered.zh)}</p>` : '',
        record.explanation.ru ? `<p class="row-why">${escapeHtml(record.explanation.ru)}</p>` : '',
        sources ? `<p class="row-sources-title">Источники</p><ul class="row-sources">${sources}</ul>` : '',
        '</details>',
      ].join('') : '',
      record.questionZh ? `<p class="row-zh">${escapeHtml(record.questionZh)}</p>` : '',
      appearances ? `<p class="row-zh">${escapeHtml(appearances)}</p>` : '',
    ].join('');
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

document.addEventListener('keydown', (event) => {
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  const typing = ['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement?.tagName);

  if (event.key === 'Escape') {
    if (typing) document.activeElement.blur();
    else if (state.view !== 'setup') backToSetup();
    return;
  }

  if (typing) return;

  if (state.view === 'database' && event.key === '/') {
    event.preventDefault();
    $('databaseSearch').focus();
    return;
  }

  if (state.view === 'setup' && event.key === 'Enter' && !$('startButton').disabled) {
    event.preventDefault();
    startRound();
    return;
  }

  if (state.view !== 'quiz') return;

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

  if ((event.key === 'Enter' || event.key === ' ') && state.answered) {
    event.preventDefault();
    nextQuestion();
  }
});

/* ---------- обвязка ---------- */

$('themeToggle').addEventListener('click', toggleTheme);
$('startButton').addEventListener('click', startRound);
$('repeatMistakes').addEventListener('click', repeatMistakes);
$('nextButton').addEventListener('click', nextQuestion);
$('leaveRound').addEventListener('click', backToSetup);
$('openDatabase').addEventListener('click', openDatabase);
$('resultsDatabase').addEventListener('click', openDatabase);
$('closeDatabase').addEventListener('click', backToSetup);
$('backToSetup').addEventListener('click', backToSetup);
$('databaseSearch').addEventListener('input', renderDatabase);
$('databaseTopic').addEventListener('change', renderDatabase);
$('databaseStatus').addEventListener('change', renderDatabase);
$('databaseMore').addEventListener('click', () => renderDatabase(false));

$('roundSize').addEventListener('change', (event) => {
  state.size = event.target.value === 'all' ? Number.MAX_SAFE_INTEGER : Number(event.target.value);
  saveStudySettings();
  renderSetup();
});
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
renderSetup();
show('setup');
