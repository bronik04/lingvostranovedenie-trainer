const STORAGE_KEY = 'lingvo-trainer:v1';
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
  filters: { topics: [], years: [], stages: [], onlyUnfinished: false, onlyVerified: false },
  size: 10,
  round: [],
  position: 0,
  correct: 0,
  progress: loadProgress(),
};

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

function show(screen) {
  for (const id of ['start', 'round', 'database']) $(id).hidden = id !== screen;
}

function chips(container, values, isOn, onPick) {
  container.innerHTML = '';
  for (const { value, label } of values) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = isOn(value) ? 'chip chip-on' : 'chip';
    button.textContent = label;
    button.addEventListener('click', () => { onPick(value); renderStart(); });
    container.append(button);
  }
}

function toggle(key) {
  return (value) => {
    const list = state.filters[key];
    const index = list.indexOf(value);
    if (index === -1) list.push(value); else list.splice(index, 1);
  };
}

function renderStart() {
  const topics = [...new Set(QUESTION_BANK.map((record) => record.topic))].sort();
  const years = [...new Set(QUESTION_BANK.flatMap((r) => r.occurrences.map((o) => o.year)))].sort();
  const stages = STAGE_ORDER.filter((code) =>
    QUESTION_BANK.some((r) => r.occurrences.some((o) => o.stageCode === code)));

  chips($('topicChips'), topics.map((value) => ({ value, label: value })),
    (value) => state.filters.topics.includes(value), toggle('topics'));
  chips($('yearChips'), years.map((value) => ({ value, label: value })),
    (value) => state.filters.years.includes(value), toggle('years'));
  chips($('stageChips'), stages.map((value) => ({ value, label: STAGE_NAMES[value] || value })),
    (value) => state.filters.stages.includes(value), toggle('stages'));
  chips($('sizes'), [5, 10, 20, 50, Number.MAX_SAFE_INTEGER].map((value) => ({
    value, label: value === Number.MAX_SAFE_INTEGER ? 'все' : String(value),
  })), (value) => state.size === value, (value) => { state.size = value; });

  const pool = eligible(QUESTION_BANK, state.filters, state.progress);
  $('eligibleCount').textContent = pool.length
    ? `Подходит вопросов: ${pool.length}`
    : 'Под текущие фильтры не подходит ни один вопрос — снимите часть ограничений.';
  $('startRound').disabled = pool.length === 0;

  const verified = QUESTION_BANK.filter((r) => r.answer.state === 'verified').length;
  const done = Object.values(state.progress).filter((item) => item.completed).length;
  $('stats').textContent =
    `Вопросов ${QUESTION_BANK.length} · проверено ${verified} · пройдено ${done}`;
}

function startRound() {
  state.round = buildRound(QUESTION_BANK, state.filters, state.progress, state.size);
  state.position = 0;
  state.correct = 0;
  show('round');
  renderQuestion();
}

function renderQuestion() {
  const record = state.round[state.position];
  if (!record) {
    $('roundMeta').textContent = state.round.length
      ? `Раунд окончен: ${state.correct} из ${state.round.length}`
      : 'Раунд пуст.';
    $('questionText').textContent = '';
    $('optionList').innerHTML = '';
    $('feedback').hidden = true;
    return;
  }
  const first = record.occurrences[0];
  $('roundMeta').textContent = [
    record.topic,
    `${first.year}, ${first.stage}`,
    `${state.position + 1} из ${state.round.length}`,
    `верных ${state.correct}`,
  ].join(' · ');
  $('questionText').textContent = record.questionRu;
  $('feedback').hidden = true;
  $('optionList').innerHTML = '';
  for (const option of labelledOptions(record)) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'option';
    button.dataset.optionId = option.optionId;
    button.innerHTML = `<span class="label">${option.label}</span>${option.zh}`;
    button.addEventListener('click', () => answer(record, option.optionId));
    $('optionList').append(button);
  }
}

function answer(record, optionId) {
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

  for (const button of $('optionList').querySelectorAll('button')) {
    button.disabled = true;
    if (button.dataset.optionId === verdict.answerOptionId) button.classList.add('right');
    else if (button.dataset.optionId === optionId) button.classList.add('wrong');
  }

  const right = record.options.find((option) => option.id === verdict.answerOptionId);
  $('verdict').className = verdict.correct ? 'verdict right' : 'verdict wrong';
  $('verdict').textContent = verdict.correct ? 'Верно' : `Неверно. Правильный ответ: ${right.zh}`;
  $('explanation').textContent = record.explanation.ru;
  $('evidence').innerHTML = '';
  for (const source of record.evidence) {
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = source.url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = `${source.title}${source.checkedAt ? ` (проверено ${source.checkedAt})` : ''}`;
    item.append(link);
    $('evidence').append(item);
  }
  $('unverifiedNote').hidden = record.answer.state !== 'unverified';
  $('feedback').hidden = false;
  $('nextQuestion').textContent =
    state.position + 1 < state.round.length ? 'Дальше' : 'Завершить раунд';
}

function renderDatabase() {
  const needle = $('search').value.trim().toLocaleLowerCase('ru');
  const status = $('statusFilter').value;
  const rows = QUESTION_BANK.filter((record) =>
    (!needle || record.questionRu.toLocaleLowerCase('ru').includes(needle))
    && (!status || record.answer.state === status));

  $('databaseCount').textContent = `Показано ${rows.length} из ${QUESTION_BANK.length}`;
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
      .map((o) => `${o.year} ${o.stage}${o.number ? ` №${o.number}` : ''}`).join(' · ');
    article.innerHTML = [
      `<h3>${record.questionRu}</h3>`,
      `<p class="meta"><span class="tag">${record.topic}</span>`,
      `<span class="tag">${STATUS_NAMES[record.answer.state]}</span>`,
      done ? '<span class="tag">пройден</span>' : '',
      record.parseWarnings?.length ? `<span class="tag warn">${record.parseWarnings.join('; ')}</span>` : '',
      `<br>${appearances}</p>`,
      `<p class="zh">${record.options.map((o) => o.zh).join(' · ')}</p>`,
      answered ? `<p class="answer">Ответ: ${answered.zh}</p>` : '',
      record.explanation.ru ? `<p>${record.explanation.ru}</p>` : '',
      record.questionZh ? `<p class="zh">${record.questionZh}</p>` : '',
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

$('startRound').addEventListener('click', startRound);
$('nextQuestion').addEventListener('click', () => {
  state.position += 1;
  if (state.position >= state.round.length) {
    show('start');
    renderStart();
    return;
  }
  renderQuestion();
});
$('leaveRound').addEventListener('click', () => { show('start'); renderStart(); });
$('onlyUnfinished').addEventListener('change', (event) => {
  state.filters.onlyUnfinished = event.target.checked;
  renderStart();
});
$('onlyVerified').addEventListener('change', (event) => {
  state.filters.onlyVerified = event.target.checked;
  renderStart();
});
$('openDatabase').addEventListener('click', () => { show('database'); renderDatabase(); });
$('backToStart').addEventListener('click', () => { show('start'); renderStart(); });
$('search').addEventListener('input', renderDatabase);
$('statusFilter').addEventListener('change', renderDatabase);
$('resetProgress').addEventListener('click', () => {
  if (!confirm('Сбросить прогресс по всем вопросам?')) return;
  state.progress = {};
  saveProgress();
  renderStart();
});

renderStart();
show('start');
