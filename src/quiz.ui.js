const STORAGE_KEY = 'lingvo-trainer:v1';
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

const state = {
  filters: { topics: [], years: [], stages: [], onlyUnfinished: false, onlyVerified: false, onlyMistakes: false },
  size: 10,
  round: [],
  position: 0,
  correct: 0,
  answered: false,
  view: 'setup',
  progress: loadProgress(),
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
    return stored.version === 1 && stored.progress ? stored.progress : {};
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
      if (parsed.version !== 1 || typeof parsed.progress !== 'object' || !parsed.progress) {
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
  const verified = QUESTION_BANK.filter((r) => r.answer.state === 'verified').length;
  const done = Object.values(state.progress).filter((item) => item.completed).length;
  $('bankCount').textContent = `${QUESTION_BANK.length} вопросов · проверено ${verified} · пройдено ${done}`;
}

function renderSetup() {
  const topics = [...new Set(QUESTION_BANK.map((r) => r.topic))].sort();
  if (!$('topicControls').children.length) {
    for (const topic of topics) {
      const label = document.createElement('label');
      label.className = 'topic-check';
      label.innerHTML = `<input type="checkbox" value="${topic}"><span>${topic}</span>`;
      label.querySelector('input').addEventListener('change', (event) => {
        const list = state.filters.topics;
        if (event.target.checked) list.push(topic);
        else list.splice(list.indexOf(topic), 1);
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

  const pool = eligible(QUESTION_BANK, state.filters, state.progress);
  $('eligibleNotice').textContent = pool.length
    ? `Под фильтры подходит вопросов: ${pool.length}.`
    : 'Под текущие фильтры не подходит ни один вопрос — снимите часть ограничений.';
  $('startButton').disabled = pool.length === 0;
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
  state.round = buildRound(QUESTION_BANK, state.filters, state.progress, state.size);
  state.position = 0;
  state.correct = 0;
  show('quiz');
  renderQuestion();
}

function renderQuestion() {
  const record = state.round[state.position];
  if (!record) return finishRound();

  state.answered = false;
  const first = record.occurrences[0];
  $('progressLabel').textContent = `Вопрос ${state.position + 1} из ${state.round.length}`;
  $('scoreLabel').textContent = `Счёт: ${state.correct}`;
  $('progressFill').style.width = `${(state.position / state.round.length) * 100}%`;
  $('topicLabel').textContent = record.topic;
  $('sourceLabel').textContent = `${first.year}, ${stageLabel(first.stageCode)}${first.number ? ` · №${first.number}` : ''}`;
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
    button.innerHTML = `<span class="letter">${option.label}</span><span>${option.zh}</span>`;
    button.addEventListener('click', () => answer(record, option.optionId));
    $('options').append(button);
  }
}

function answer(record, optionId) {
  if (state.answered) return;
  state.answered = true;

  const verdict = grade(record, optionId);
  const previous = state.progress[record.id] || { attempts: 0, correct: 0 };
  state.progress[record.id] = {
    attempts: previous.attempts + 1,
    correct: previous.correct + (verdict.correct ? 1 : 0),
    completed: true,
    lastCorrect: verdict.correct,
  };
  saveProgress();
  if (verdict.correct) state.correct += 1;
  $('scoreLabel').textContent = `Счёт: ${state.correct}`;

  for (const button of $('options').querySelectorAll('button')) {
    button.disabled = true;
    if (button.dataset.optionId === verdict.answerOptionId) button.classList.add('correct');
    else if (button.dataset.optionId === optionId) button.classList.add('wrong');
  }

  const right = record.options.find((option) => option.id === verdict.answerOptionId);
  const sources = record.evidence.map((source) =>
    `<li><a href="${source.url}" target="_blank" rel="noopener noreferrer">${source.title}</a>` +
    `${source.checkedAt ? ` <span class="muted">(проверено ${source.checkedAt})</span>` : ''}</li>`).join('');

  $('feedback').className = `feedback ${verdict.correct ? 'good' : 'bad'}`;
  $('feedback').innerHTML = [
    `<p><strong>${verdict.correct ? 'Верно' : 'Неверно'}</strong>`,
    verdict.correct ? '' : `Правильный ответ: ${right.zh}.`,
    '</p>',
    record.explanation.ru ? `<p class="why">${record.explanation.ru}</p>` : '',
    sources ? `<ul>${sources}</ul>` : '',
    record.answer.state === 'unverified'
      ? '<p class="unverified">Ответ взят из официального ключа, но ещё не перепроверен по источникам.</p>'
      : '',
  ].join('');

  $('nextButton').textContent =
    state.position + 1 < state.round.length ? 'Следующий вопрос' : 'Итоги раунда';
  $('nextButton').classList.remove('hidden');
  $('nextButton').focus();
}

function nextQuestion() {
  if (!state.answered) return;
  state.position += 1;
  if (state.position >= state.round.length) finishRound();
  else renderQuestion();
}

function finishRound() {
  const total = state.round.length;
  $('finalScore').textContent = `${state.correct} / ${total}`;
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

function renderDatabase() {
  const needle = $('databaseSearch').value.trim().toLocaleLowerCase('ru');
  const topic = $('databaseTopic').value;
  const status = $('databaseStatus').value;
  const rows = QUESTION_BANK.filter((record) =>
    (!needle || record.questionRu.toLocaleLowerCase('ru').includes(needle))
    && (!topic || record.topic === topic)
    && (!status || record.answer.state === status));

  $('databaseCount').textContent = `Показано ${rows.length} из ${QUESTION_BANK.length} вопросов`;
  $('databaseList').innerHTML = '';
  if (!rows.length) {
    $('databaseList').innerHTML = '<p class="empty">Ничего не найдено.</p>';
    return;
  }

  for (const record of rows.slice(0, 300)) {
    const article = document.createElement('article');
    article.className = 'row';
    const answered = record.options.find((option) => option.id === record.answer.optionId);
    const done = state.progress[record.id]?.completed;
    const appearances = record.occurrences
      .map((o) => `${o.year} ${stageLabel(o.stageCode)}${o.number ? ` №${o.number}` : ''}`).join(' · ');
    article.innerHTML = [
      '<div class="row-top">',
      `<span class="tag">${record.topic}</span>`,
      `<span class="tag${record.answer.state === 'verified' ? ' done' : ''}${
        record.answer.state === 'needs-review' || record.answer.state === 'conflict' ? ' review' : ''
      }">${STATUS_NAMES[record.answer.state]}</span>`,
      done ? '<span class="tag done">пройден</span>' : '',
      record.parseWarnings?.length ? `<span class="tag warn">${record.parseWarnings.join('; ')}</span>` : '',
      '</div>',
      `<h3>${record.questionRu}</h3>`,
      `<div class="row-options">${record.options.map((o) => o.zh).join(' · ')}</div>`,
      answered ? `<p class="row-answer">Ответ: ${answered.zh}</p>` : '',
      record.explanation.ru ? `<p class="row-why">${record.explanation.ru}</p>` : '',
      record.questionZh ? `<p class="row-zh">${record.questionZh}</p>` : '',
      `<p class="row-zh">${appearances}</p>`,
    ].join('');
    $('databaseList').append(article);
  }
  if (rows.length > 300) {
    const more = document.createElement('p');
    more.className = 'empty';
    more.textContent = `Показаны первые 300. Уточните поиск, чтобы увидеть остальные ${rows.length - 300}.`;
    $('databaseList').append(more);
  }
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
$('nextButton').addEventListener('click', nextQuestion);
$('leaveRound').addEventListener('click', backToSetup);
$('openDatabase').addEventListener('click', openDatabase);
$('resultsDatabase').addEventListener('click', openDatabase);
$('closeDatabase').addEventListener('click', backToSetup);
$('backToSetup').addEventListener('click', backToSetup);
$('databaseSearch').addEventListener('input', renderDatabase);
$('databaseTopic').addEventListener('change', renderDatabase);
$('databaseStatus').addEventListener('change', renderDatabase);

$('roundSize').addEventListener('change', (event) => {
  state.size = event.target.value === 'all' ? Number.MAX_SAFE_INTEGER : Number(event.target.value);
  renderSetup();
});
$('onlyUncompleted').addEventListener('change', (event) => {
  state.filters.onlyUnfinished = event.target.checked;
  renderSetup();
});
$('onlyVerified').addEventListener('change', (event) => {
  state.filters.onlyVerified = event.target.checked;
  renderSetup();
});
$('onlyMistakes').addEventListener('change', (event) => {
  state.filters.onlyMistakes = event.target.checked;
  renderSetup();
});
$('yearFilter').addEventListener('change', (event) => {
  state.filters.years = event.target.value ? [event.target.value] : [];
  renderSetup();
});
$('stageFilter').addEventListener('change', (event) => {
  state.filters.stages = event.target.value ? [event.target.value] : [];
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

const verifiedCount = QUESTION_BANK.filter((r) => r.answer.state === 'verified').length;
$('footerNote').textContent =
  `${QUESTION_BANK.length} вопросов, собранных из материалов ВсОШ 2015/16 — 2025/26. ` +
  `У ${verifiedCount} ответов есть пояснение и ссылка на источник; у остальных ответ взят из ` +
  'официального ключа и ждёт перепроверки.';

initTheme();
renderSetup();
show('setup');
