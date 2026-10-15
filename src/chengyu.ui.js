/*
 * Раздел «Чэнъюй». Работает в той же странице, что и основной тренажёр: берёт у него
 * $, show, escapeHtml, pluralRu и state.view (src/quiz.ui.js, src/quiz.mjs), логика —
 * src/chengyu.mjs. Прогресс и настройки хранятся отдельно от основного раздела.
 */

const CY_STORAGE_KEY = 'lingvo-trainer:chengyu:v1';
const CY_SETTINGS_KEY = 'lingvo-trainer:chengyu-settings:v1';

const cy = {
  filters: cyDefaultFilters(),
  size: 10,
  progress: {},
  round: [],
  position: 0,
  answered: false,
  correct: 0,
  marks: [],
  wrongIds: [],
  wrongPicks: {},
};

function cyLoad() {
  try {
    const stored = JSON.parse(localStorage.getItem(CY_STORAGE_KEY) || '{}');
    if (stored.version === 1 && cyIsValidProgress(stored.progress)) cy.progress = stored.progress;
  } catch { /* хранилище недоступно — работаем без сохранения */ }
  try {
    const settings = JSON.parse(localStorage.getItem(CY_SETTINGS_KEY) || '{}');
    cy.filters = cyNormaliseFilters(settings.filters);
    if (settings.size === 'all' || [5, 10, 20].includes(settings.size)) {
      cy.size = settings.size === 'all' ? Number.MAX_SAFE_INTEGER : settings.size;
    }
  } catch { /* настройки по умолчанию */ }
}

function cySaveProgress() {
  try {
    localStorage.setItem(CY_STORAGE_KEY, JSON.stringify({ version: 1, progress: cy.progress }));
  } catch { /* хранилище недоступно */ }
}

function cySaveSettings() {
  try {
    localStorage.setItem(CY_SETTINGS_KEY, JSON.stringify({
      filters: cy.filters, size: cy.size === Number.MAX_SAFE_INTEGER ? 'all' : cy.size,
    }));
  } catch { /* хранилище недоступно */ }
}

/* ---------- начало раздела ---------- */

const CY_MODE_HELP = {
  all: 'Все задания выбранных тем в случайном порядке.',
  new: 'Только задания, которые вы ещё не решали.',
  mistakes: 'Задания, в которых последний ответ был неверным.',
};

function cyRenderStats() {
  const summary = cySummary(CHENGYU_BANK);
  for (const [id, count, forms] of [
    ['cyStatTotal', summary.total, ['задание', 'задания', 'заданий']],
    ['cyStatSeasons', summary.seasons, ['сезон олимпиады', 'сезона олимпиады', 'сезонов олимпиады']],
    ['cyStatGroups', summary.groups, ['тема', 'темы', 'тем']],
  ]) {
    $(id).textContent = String(count);
    $(`${id}Label`).textContent = pluralRu(count, forms);
  }
}

function cyRenderSetup() {
  if (!$('cyGroupControls').children.length) {
    for (const [group, name] of Object.entries(CY_GROUPS)) {
      const label = document.createElement('label');
      label.className = 'topic-check';
      label.innerHTML = `<span class="topic-mark" lang="zh-Hans" aria-hidden="true">${CY_GROUP_MARKS[group]}</span>`
        + `<span class="topic-text"><span class="topic-name">${escapeHtml(name)}</span>`
        + '<span class="topic-count">решено <span class="topic-progress"></span></span></span>';
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.value = group;
      input.addEventListener('change', (event) => {
        const list = cy.filters.groups;
        if (event.target.checked) list.push(group);
        else list.splice(list.indexOf(group), 1);
        cySaveSettings();
        cyRenderSetup();
      });
      label.append(input);
      $('cyGroupControls').append(label);
    }
  }
  for (const label of $('cyGroupControls').children) {
    const input = label.querySelector('input');
    input.checked = cy.filters.groups.includes(input.value);
    const records = CHENGYU_BANK.filter((record) => record.group === input.value);
    const done = records.filter((record) => cy.progress[record.id]).length;
    label.querySelector('.topic-progress').textContent = `${done} из ${records.length}`;
  }
  for (const input of document.querySelectorAll('input[name="cyMode"]')) {
    input.checked = input.value === cy.filters.mode;
  }
  for (const input of document.querySelectorAll('input[name="cySize"]')) {
    input.checked = input.value === (cy.size === Number.MAX_SAFE_INTEGER ? 'all' : String(cy.size));
  }
  $('cyModeHelp').textContent = CY_MODE_HELP[cy.filters.mode];
  const count = cyEligible(CHENGYU_BANK, cy.filters, cy.progress).length;
  const inRound = Math.min(count, cy.size);
  $('cyEligibleNotice').textContent = count
    ? `Доступно ${count} ${pluralRu(count, ['задание', 'задания', 'заданий'])}, в раунде будет ${inRound}.`
    : cy.filters.mode === 'mistakes'
      ? 'Ошибок пока нет: сюда попадает задание, в котором последний ответ был неверным.'
      : 'Под выбранные условия нет заданий. Выберите другие темы или набор.';
  $('cyStartButton').disabled = count === 0;
}

function cyOpenSetup() {
  show('cy-setup');
  cyRenderSetup();
}

/* ---------- раунд ---------- */

function cyStartRoundWith(round) {
  if (!round.length) return;
  Object.assign(cy, {
    round, position: 0, answered: false, correct: 0, marks: [], wrongIds: [], wrongPicks: {},
  });
  show('cy-quiz');
  cyRenderQuestion();
}

function cyStartRound() {
  cyStartRoundWith(cyBuildRound(CHENGYU_BANK, cy.filters, cy.progress, cy.size));
}

function cyRenderProgress() {
  const total = cy.round.length;
  const dots = total <= MAX_STEP_DOTS;
  $('cyProgressSteps').hidden = !dots;
  $('cyProgressTrack').hidden = dots;
  $('cyScoreLabel').textContent = `верно ${cy.correct}`;
  if (!dots) {
    $('cyProgressFill').style.width = `${((cy.position + (cy.answered ? 1 : 0)) / total) * 100}%`;
    return;
  }
  $('cyProgressSteps').replaceChildren(...cy.round.map((_, index) => {
    const step = document.createElement('li');
    const mark = cy.marks[index];
    const current = index === cy.position;
    step.className = ['ink-step', mark === true ? 'ink-step--correct' : '', mark === false ? 'ink-step--wrong' : '',
      current ? 'ink-step--current' : ''].filter(Boolean).join(' ');
    if (mark !== undefined) step.lang = 'zh-Hans';
    step.textContent = mark === true ? '✓' : mark === false ? '✕' : current ? String(index + 1) : '';
    step.setAttribute('aria-label', `${index + 1}${mark === true ? ' — верно' : mark === false ? ' — ошибка' : ''}${
      current ? ', текущий' : ''}`);
    return step;
  }));
}

function cyRenderQuestion() {
  const record = cy.round[cy.position];
  if (!record) return cyFinishRound();
  cy.answered = false;
  $('cyProgressLabel').textContent = `Задание ${cy.position + 1} из ${cy.round.length}`;
  cyRenderProgress();
  $('cyGroupLabel').textContent = CY_GROUPS[record.group];
  const occurrence = cyLatestOccurrence(record);
  $('cySourceLabel').textContent = occurrence ? cyOccurrenceLabel(occurrence) : 'Составленное задание';
  $('cyPrompt').textContent = cyPrompt(record);
  const reverse = record.kind === 'reverse';
  $('cyChengyu').hidden = reverse;
  $('cyPinyin').hidden = reverse;
  $('cyProverb').hidden = !reverse;
  if (reverse) {
    $('cyProverb').textContent = `«${record.prompt}»`;
  } else {
    $('cyChengyu').setAttribute('aria-label', record.chengyu);
    $('cyChengyu').replaceChildren(...[...record.chengyu].map((char) => {
      const cell = document.createElement('span');
      cell.setAttribute('aria-hidden', 'true');
      cell.textContent = char;
      return cell;
    }));
    $('cyPinyin').textContent = record.pinyin;
  }

  $('cyFeedback').className = 'feedback hidden';
  $('cyNextButton').classList.add('hidden');
  $('cyOptions').innerHTML = '';
  for (const option of cyLabelledOptions(record)) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'option';
    button.dataset.optionId = option.optionId;
    const letter = document.createElement('span');
    letter.className = 'letter';
    letter.setAttribute('aria-hidden', 'true');
    letter.textContent = option.label;
    const caption = document.createElement('span');
    caption.className = reverse ? 'option-text' : 'option-text cy-option-ru';
    if (reverse) caption.lang = 'zh-Hans';
    caption.textContent = option.text;
    button.append(letter, caption);
    if (option.gloss) button.dataset.gloss = option.gloss;
    button.addEventListener('click', () => cyAnswer(record, option.optionId));
    $('cyOptions').append(button);
  }
}

function cyFacts(record) {
  const rows = record.kind === 'reverse'
    ? [
      ['Ответ', `<span lang="zh-Hans">${escapeHtml(record.chengyu)}</span> <span lang="zh-Hans" class="muted">${escapeHtml(record.pinyin)}</span> — «${escapeHtml(record.literal)}»`],
      ['Смысл', escapeHtml(record.meaning)],
      ['Ловушка', escapeHtml(record.trap)],
    ]
    : [
      ['Буквально', escapeHtml(record.literal)],
      ['Смысл', escapeHtml(record.meaning)],
      ['Ловушка', escapeHtml(record.trap)],
      record.story ? ['История', escapeHtml(record.story)] : null,
    ];
  return `<dl class="cy-facts">${rows.filter(Boolean).map(([term, text]) =>
    `<dt>${term}</dt><dd>${text}</dd>`).join('')}</dl>`;
}

function cyAnswer(record, optionId) {
  if (cy.answered) return;
  cy.answered = true;
  const verdict = cyGrade(record, optionId);
  cy.progress[record.id] = cyRecordAnswer(cy.progress[record.id], verdict.correct);
  cySaveProgress();
  if (verdict.correct) cy.correct += 1;
  else if (!cy.wrongIds.includes(record.id)) {
    cy.wrongIds.push(record.id);
    cy.wrongPicks[record.id] = optionId;
  }
  cy.marks[cy.position] = verdict.correct;
  cyRenderProgress();

  const odd = record.kind === 'odd';
  for (const button of $('cyOptions').querySelectorAll('button')) {
    button.disabled = true;
    const status = document.createElement('span');
    status.className = 'option-status';
    if (button.dataset.optionId === verdict.answerOptionId) {
      button.classList.add('correct');
      status.textContent = odd ? '✓ Лишний' : '✓ Верно';
      button.append(status);
    } else if (button.dataset.optionId === optionId) {
      button.classList.add('wrong');
      status.textContent = '✕ Ваш ответ';
      button.append(status);
    }
    if (button.dataset.gloss) {
      const note = document.createElement('small');
      note.className = 'option-gloss';
      note.textContent = button.dataset.gloss;
      button.append(note);
    }
  }

  const answerText = cyAnswerText(record);
  const answerHtml = record.kind === 'reverse'
    ? `<span lang="zh-Hans">${escapeHtml(answerText)}</span>` : `«${escapeHtml(answerText)}»`;
  $('cyFeedback').className = `feedback ${verdict.correct ? 'good' : 'bad'}`;
  $('cyFeedback').innerHTML = [
    `<p class="verdict"><strong>${verdict.correct ? 'Верно' : 'Неверно'}</strong>`,
    verdict.correct ? '' : `<span>${odd ? 'Лишний вариант' : 'Правильный ответ'}: ${answerHtml}.</span>`,
    '</p>',
    cyFacts(record),
    record.disputedKey
      ? '<p class="unverified">Ключ олимпиады спорный: он приведён как в официальных ответах, разбор объясняет почему.</p>'
      : '',
  ].join('');

  $('cyNextButton').textContent = cy.position + 1 < cy.round.length ? 'Следующее задание' : 'Итоги раунда';
  $('cyNextButton').classList.remove('hidden');
  requestAnimationFrame(() => {
    const compact = window.matchMedia?.('(max-width: 600px)').matches;
    const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    $('cyFeedback').focus({ preventScroll: true });
    if (compact) $('cyFeedback').scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'nearest' });
  });
}

function cyNextQuestion() {
  if (!cy.answered) return;
  cy.position += 1;
  if (cy.position >= cy.round.length) cyFinishRound();
  else cyRenderQuestion();
}

function cyFinishRound() {
  const total = cy.round.length;
  const wrong = cy.wrongIds.length;
  $('cyFinalScore').innerHTML = `${cy.correct}<span class="score-total"> / ${total}</span>`;
  $('cyResultMeterCorrect').style.flex = String(cy.correct);
  $('cyResultMeterWrong').style.flex = String(wrong);
  $('cyResultCounts').innerHTML = `<span><span class="ok" lang="zh-Hans">✓</span> верно — ${cy.correct}</span>`
    + `<span><span class="bad" lang="zh-Hans">✕</span> с ошибкой — ${wrong}</span>`;
  $('cyRepeatMistakes').hidden = wrong === 0;
  $('cyRepeatMistakes').textContent = `Повторить ошибки раунда (${wrong})`;
  $('cyBackToSetup').classList.toggle('ink-btn--primary', wrong === 0);
  $('cyBackToSetup').classList.toggle('ink-btn--secondary', wrong !== 0);
  const records = cy.round.filter((record) => cy.wrongIds.includes(record.id));
  $('cyResultMistakes').hidden = records.length === 0;
  $('cyMistakeList').replaceChildren(...records.map((record) => {
    const picked = record.options.find((option) => option.id === cy.wrongPicks[record.id]);
    const right = cyAnswerText(record);
    const reverse = record.kind === 'reverse';
    const shown = (text) => (reverse ? `<span lang="zh-Hans">${escapeHtml(text)}</span>` : escapeHtml(text));
    const item = document.createElement('li');
    item.innerHTML = [
      '<span class="ink-seal ink-seal--review ink-seal--md" lang="zh-Hans" aria-hidden="true">复</span>',
      '<div>',
      `<p class="mistake-question">${reverse ? `«${escapeHtml(record.prompt)}»`
        : `<span class="cy-mistake-han" lang="zh-Hans">${escapeHtml(record.chengyu)}</span>`}</p>`,
      '<p class="mistake-answers">',
      picked ? `Ваш ответ <span class="picked">✕ ${shown(picked.text)}</span> · ` : '',
      `верно <span class="right">✓ ${shown(right)}</span>`,
      '</p></div>',
    ].join('');
    return item;
  }));
  show('cy-results');
}

function cyRepeatMistakes() {
  cyStartRoundWith(cy.round.filter((record) => cy.wrongIds.includes(record.id)));
}

/* ---------- справочник ---------- */

function cyOpenReference() {
  show('cy-reference');
  cyRenderReference();
}

function cyRenderReference() {
  const group = $('cyReferenceGroup').value;
  const records = CHENGYU_BANK.filter((record) =>
    cyMatchesSearch(record, $('cyReferenceSearch').value) && (!group || record.group === group));
  $('cyReferenceCount').textContent =
    `Показано ${records.length} из ${CHENGYU_BANK.length} ${pluralRu(CHENGYU_BANK.length, ['задания', 'заданий', 'заданий'])}`;
  if (!records.length) {
    $('cyReferenceList').innerHTML = '<p class="empty">Ничего не найдено.</p>';
    return;
  }
  $('cyReferenceList').replaceChildren(...records.map((record) => {
    const article = document.createElement('article');
    article.className = 'row';
    const reverse = record.kind === 'reverse';
    const answer = cyAnswerText(record);
    const options = record.options.map((option) => {
      const text = reverse ? `<span lang="zh-Hans">${escapeHtml(option.text)}</span>` : escapeHtml(option.text);
      const note = option.gloss ? ` — ${escapeHtml(option.gloss)}` : '';
      return `<li${option.id === record.answer ? ' class="cy-key"' : ''}>${option.id}. ${text}${note}${
        option.id === record.answer ? (record.kind === 'odd' ? ' <span lang="zh-Hans">✓</span> лишний' : ' <span lang="zh-Hans">✓</span>') : ''}</li>`;
    }).join('');
    const appearances = (record.occurrences || []).map(cyOccurrenceLabel).join('; ');
    const done = cy.progress[record.id];
    article.innerHTML = [
      '<div class="row-top">',
      `<span class="row-topic">${escapeHtml(CY_GROUPS[record.group])}</span>`,
      done ? '<span class="tag"><span lang="zh-Hans" aria-hidden="true">●</span> решено</span>' : '',
      record.disputedKey ? '<span class="tag warn">спорный ключ</span>' : '',
      '</div>',
      `<h3 class="cy-row-head"><span class="cy-row-han" lang="zh-Hans">${escapeHtml(record.chengyu)}</span>`,
      `<span class="cy-row-pinyin" lang="zh-Hans">${escapeHtml(record.pinyin)}</span></h3>`,
      `<p class="row-meta">${reverse ? `Обратное задание: «${escapeHtml(record.prompt)}»`
        : record.kind === 'odd' ? 'Найти лишний вариант' : `Аналог: «${escapeHtml(answer)}»`}</p>`,
      appearances ? `<p class="row-meta">${escapeHtml(appearances)}</p>` : '',
      '<details class="row-reveal"><summary>Показать разбор</summary><div class="row-panel">',
      `<p class="row-sources-title">Варианты бланка</p><ol class="cy-options-list">${options}</ol>`,
      cyFacts(record),
      '</div></details>',
    ].join('');
    const reveal = article.querySelector('.row-reveal');
    reveal.addEventListener('toggle', () => {
      reveal.querySelector('summary').textContent = reveal.open ? 'Скрыть разбор' : 'Показать разбор';
    });
    return article;
  }));
}

/* ---------- клавиатура ---------- */

document.addEventListener('keydown', (event) => {
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  if (!state.view.startsWith('cy-')) return;
  const typing = ['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement?.tagName);
  if (event.key === 'Escape') {
    if (typing) document.activeElement.blur();
    else if (state.view !== 'cy-setup') cyOpenSetup();
    return;
  }
  if (typing) return;
  const onControl = Boolean(document.activeElement?.closest?.('a, button, summary'));
  if (state.view === 'cy-reference' && event.key === '/') {
    event.preventDefault();
    $('cyReferenceSearch').focus();
    return;
  }
  if (state.view === 'cy-setup' && event.key === 'Enter' && !onControl && !$('cyStartButton').disabled) {
    event.preventDefault();
    cyStartRound();
    return;
  }
  if (state.view !== 'cy-quiz') return;
  const index = ANSWER_KEYS[event.code];
  if (index !== undefined && !cy.answered) {
    const button = $('cyOptions').querySelectorAll('button')[index];
    if (button) {
      event.preventDefault();
      button.click();
    }
    return;
  }
  if ((event.key === 'Enter' || event.key === ' ') && cy.answered && !onControl) {
    event.preventDefault();
    cyNextQuestion();
  }
});

/* ---------- обвязка ---------- */

$('navChengyu').addEventListener('click', (event) => {
  event.preventDefault();
  cyOpenSetup();
});
$('cyStartButton').addEventListener('click', cyStartRound);
$('cyOpenReference').addEventListener('click', cyOpenReference);
$('cyResultsReference').addEventListener('click', cyOpenReference);
$('cyCloseReference').addEventListener('click', cyOpenSetup);
$('cyBackToSetup').addEventListener('click', cyOpenSetup);
$('cyLeaveRound').addEventListener('click', cyOpenSetup);
$('cyNextButton').addEventListener('click', cyNextQuestion);
$('cyRepeatMistakes').addEventListener('click', cyRepeatMistakes);
$('cyReferenceSearch').addEventListener('input', cyRenderReference);
$('cyReferenceGroup').addEventListener('change', cyRenderReference);
$('cyResetProgress').addEventListener('click', () => {
  if (!confirm('Сбросить прогресс по чэнъюй? Прогресс основного тренажёра останется.')) return;
  cy.progress = {};
  cySaveProgress();
  cyRenderSetup();
});
for (const input of document.querySelectorAll('input[name="cyMode"]')) {
  input.addEventListener('change', (event) => {
    cy.filters.mode = event.target.value;
    cySaveSettings();
    cyRenderSetup();
  });
}
for (const input of document.querySelectorAll('input[name="cySize"]')) {
  input.addEventListener('change', (event) => {
    cy.size = event.target.value === 'all' ? Number.MAX_SAFE_INTEGER : Number(event.target.value);
    cySaveSettings();
    cyRenderSetup();
  });
}
for (const [group, name] of Object.entries(CY_GROUPS)) {
  const option = document.createElement('option');
  option.value = group;
  option.textContent = name;
  $('cyReferenceGroup').append(option);
}

cyLoad();
cyRenderStats();
cyRenderSetup();
// ссылка вида …/#chengyu открывает раздел сразу — и при загрузке, и в открытой странице
if (location.hash === '#chengyu') cyOpenSetup();
window.addEventListener('hashchange', () => {
  if (location.hash === '#chengyu' && !state.view.startsWith('cy-')) cyOpenSetup();
});
