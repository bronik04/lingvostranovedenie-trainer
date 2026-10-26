/*
 * Раздел «Чэнъюй». Работает в той же странице, что и основной тренажёр: берёт у него
 * $, show, escapeHtml, pluralRu и state.view (src/quiz.ui.js, src/quiz.mjs), логика —
 * src/chengyu.mjs. Прогресс и настройки хранятся отдельно от основного раздела; в файл
 * прогресса (exportProgress/importProgress в src/quiz.ui.js) cy.progress идёт вместе с ним.
 * Счёт в шапке на экранах раздела пишет cyRenderCount, подвал — cyFooterNote; их зовёт show из
 * quiz.ui.js. У раунда, итогов и справочника свои адреса (#chengyu/round, #chengyu/results,
 * #chengyu/reference): «назад» с них ведёт к началу раздела, раунд переживает перезагрузку.
 */

const CY_STORAGE_KEY = 'lingvo-trainer:chengyu:v1';
const CY_SETTINGS_KEY = 'lingvo-trainer:chengyu-settings:v1';
// раунд — в sessionStorage, как у основного раздела: перезагрузка возвращает на то же задание
const CY_ROUND_KEY = 'lingvo-trainer:chengyu-round:v1';
const CY_HASH = /^#chengyu(?:\/|$)/;

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
  finished: false,
  // настройки, с которыми начат раунд: для плашки «Раунд не закончен» и «Нового раунда»
  roundSettings: null,
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

/** Снимок раунда: задания по id, ход, счёт и настройки, с которыми он начат. */
function cySaveRound() {
  try {
    sessionStorage.setItem(CY_ROUND_KEY, JSON.stringify({
      version: 1,
      round: cy.round.map((record) => record.id),
      position: cy.position,
      answered: cy.answered,
      correct: cy.correct,
      marks: cy.marks,
      wrongIds: cy.wrongIds,
      wrongPicks: cy.wrongPicks,
      settings: { filters: cy.roundSettings.filters, size: cy.roundSettings.size === Number.MAX_SAFE_INTEGER ? 'all' : cy.roundSettings.size },
      finished: cy.finished,
    }));
  } catch { /* без sessionStorage раунд не переживёт перезагрузку, но идёт как обычно */ }
}

function cyDiscardRound() {
  cy.round = [];
  cy.finished = false;
  try {
    sessionStorage.removeItem(CY_ROUND_KEY);
  } catch {}
}

/** После перезагрузки — тот же раунд. Задание, на которое уже ответили, второй раз не задаётся:
 * ответ сохранён в прогрессе, поэтому раунд продолжается со следующего (или кончается). */
function cyRestoreRound() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(CY_ROUND_KEY) || 'null');
    if (saved?.version !== 1) return;
    const byId = new Map(CHENGYU_BANK.map((record) => [record.id, record]));
    const round = saved.round.map((id) => byId.get(id));
    const size = saved.settings?.size;
    // задания сменились между загрузками или снимок неполный — такой раунд не восстановить
    if (!round.length || round.some((record) => !record) || !Number.isInteger(saved.position)
        || saved.position < 0 || saved.position > round.length
        || ![saved.marks, saved.wrongIds].every(Array.isArray) || !saved.wrongPicks
        || typeof saved.wrongPicks !== 'object' || !Array.isArray(saved.settings?.filters?.groups)
        || !(size === 'all' || Number.isInteger(size))) {
      cyDiscardRound();
      return;
    }
    Object.assign(cy, {
      round,
      position: saved.position,
      answered: Boolean(saved.answered),
      correct: saved.correct,
      marks: saved.marks,
      wrongIds: saved.wrongIds,
      wrongPicks: saved.wrongPicks,
      roundSettings: {
        filters: cyNormaliseFilters(saved.settings.filters),
        size: size === 'all' ? Number.MAX_SAFE_INTEGER : size,
      },
      finished: Boolean(saved.finished),
    });
    if (cy.finished) cyRenderResults();
    else if (cy.answered || cy.position >= round.length) {
      cy.position += cy.answered ? 1 : 0;
      if (cy.position >= round.length) cyCompleteRound();
      else {
        cyRenderQuestion();
        cySaveRound();
      }
    } else {
      cyRenderQuestion();
      cySaveRound();
    }
  } catch {
    // что бы ни случилось со снимком, раздел должен открыться
    cyDiscardRound();
  }
}

/* ---------- начало раздела ---------- */

const CY_MODE_HELP = {
  all: 'Все задания выбранных тем в случайном порядке.',
  new: 'Только задания, которые вы ещё не решали.',
  mistakes: 'Задания, в которых последний ответ был неверным.',
};

const CY_MODE_SUMMARY = { all: 'Все задания', new: 'Новые задания', mistakes: 'Ошибки' };
const CY_TASKS = ['задание', 'задания', 'заданий'];

/** Подвал на экранах раздела: числа, которые раньше стояли рядом под заголовком. */
function cyFooterNote() {
  const { total, olympiad, seasons, groups } = cySummary(CHENGYU_BANK);
  const authored = total - olympiad;
  return `В разделе ${total} ${pluralRu(total, CY_TASKS)}: ${olympiad} из вариантов ВсОШ за ${seasons} ${
    pluralRu(seasons, ['сезон', 'сезона', 'сезонов'])} и ${authored} ${pluralRu(authored, ['составленное', 'составленных', 'составленных'])}`
    + ` по той же схеме и сверенных со словарями, ${groups} ${pluralRu(groups, ['тема', 'темы', 'тем'])}.`;
}

/** «10 заданий», «все доступные». */
function cySizeLabel(size) {
  return size === Number.MAX_SAFE_INTEGER ? 'все доступные' : `${size} ${pluralRu(size, CY_TASKS)}`;
}

/** «все темы», «тема «Притчи и истории»», «3 темы». */
function cyGroupsLabel(groups) {
  if (!groups.length) return 'все темы';
  return groups.length === 1 ? `тема «${CY_GROUPS[groups[0]]}»` : `${groups.length} ${pluralRu(groups.length, ['тема', 'темы', 'тем'])}`;
}

/** «Все задания, 10 заданий, все темы.» — без длины на плашке незаконченного раунда. */
function cySettingsLine({ filters, size }, withSize = true) {
  return `${[CY_MODE_SUMMARY[filters.mode], withSize ? cySizeLabel(size) : '', cyGroupsLabel(filters.groups)]
    .filter(Boolean).join(', ')}.`;
}

/** Шапка в разделе: решённые задания «Чэнъюй», а не прогресс основного банка. */
function cyRenderCount() {
  const solved = CHENGYU_BANK.filter((record) => cy.progress[record.id]).length;
  $('bankCount').textContent = `Решено ${solved} из ${CHENGYU_BANK.length}`;
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
  // на пилюле набора — сколько заданий он даст при выбранных темах
  const modeCounts = {};
  for (const input of document.querySelectorAll('input[name="cyMode"]')) {
    input.checked = input.value === cy.filters.mode;
    modeCounts[input.value] = cyEligible(CHENGYU_BANK, { ...cy.filters, mode: input.value }, cy.progress).length;
    input.nextElementSibling.querySelector('.pill-count').textContent = String(modeCounts[input.value]);
  }
  for (const input of document.querySelectorAll('input[name="cySize"]')) {
    input.checked = input.value === (cy.size === Number.MAX_SAFE_INTEGER ? 'all' : String(cy.size));
  }
  $('cyModeHelp').textContent = CY_MODE_HELP[cy.filters.mode];
  cyRenderHome(modeCounts);
}

/** Верх раздела: первый визит, «Следующий раунд» или «Раунд не закончен»; полоса внизу. */
function cyRenderHome(modeCounts) {
  const available = modeCounts[cy.filters.mode];
  const unfinished = cy.round.length > 0 && !cy.finished;
  const fresh = !unfinished && !CHENGYU_BANK.some((record) => cy.progress[record.id]);
  $('cyFirstHero').hidden = !fresh;
  $('cyNextRound').hidden = fresh;
  $('cyNextMain').hidden = unfinished;
  $('cyResumePanel').hidden = !unfinished;

  const { groups } = cy.filters;
  const summary = cySettingsLine({ filters: cy.filters, size: cy.size });
  const inRound = Math.min(cy.size, available);
  const notice = available
    ? `Подходит заданий: ${available}, в раунде будет ${inRound}.`
    : cy.filters.mode === 'mistakes'
      ? 'Ошибок пока нет: сюда попадает задание, в котором последний ответ был неверным.'
      : 'Под выбранные условия нет заданий. Выберите другие темы или набор.';
  $('cyNextSummary').textContent = summary;
  $('cyEligibleNotice').textContent = notice;
  // первый визит: пока настройки не трогали, подпись под кнопкой просто объясняет раунд
  const plain = cy.filters.mode === 'all' && !groups.length;
  $('cyFirstCaption').textContent = !plain || !available ? `${summary} ${notice}`
    : `${cy.size === Number.MAX_SAFE_INTEGER ? 'Все задания раздела в случайном порядке'
      : `${cy.size} случайных заданий из всех тем`}. Набор, темы и длина — ниже.`;
  for (const id of ['cyFirstStart', 'cyStartButton', 'cyBarStart']) $(id).disabled = available === 0;
  $('cyResumeNew').hidden = available === 0;
  // главная кнопка на экране одна: без подходящих заданий это «Начать обычный раунд»
  for (const id of ['cyStartButton', 'cyBarStart']) {
    $(id).classList.toggle('ink-btn--primary', available !== 0);
    $(id).classList.toggle('ink-btn--secondary', available === 0);
  }
  $('cyEmptyActions').hidden = available !== 0;
  $('cyStartBarText').textContent = available
    ? `${groups.length ? `${groups.length} ${pluralRu(groups.length, ['тема', 'темы', 'тем'])}` : 'Все темы'}, ${inRound} из ${available} подходящих`
    : 'Под условия не подходит ни одно задание';

  // быстрые входы: раунд из ошибок (пустой не показывается) и справочник
  const mistakes = modeCounts.mistakes;
  $('cyQuickMistakes').hidden = mistakes === 0;
  $('cyQuickMistakes').querySelector('.quick-number').textContent = String(mistakes);
  $('cyQuickMistakes').querySelector('.quick-unit').textContent = pluralRu(mistakes, CY_TASKS);
  $('cyQuickReference').querySelector('.quick-number').textContent = String(CHENGYU_BANK.length);

  if (unfinished) {
    $('cyResumeProgress').textContent = `Задание ${cy.position + 1} из ${cy.round.length}, верно ${cy.correct}.`;
    $('cyResumeSettings').textContent = ` ${cySettingsLine(cy.roundSettings, false)}`;
    cyRenderSteps($('cyResumeSteps'), $('cyResumeTrack'), $('cyResumeFill'));
    const answered = cy.position + (cy.answered ? 1 : 0);
    $('cyResumeSaved').hidden = answered === 0;
    $('cyResumeSaved').textContent = answered === 1 ? 'Ответ на первое задание уже сохранён в прогрессе.'
      : `Ответы на первые ${NUMBER_WORDS[answered] || answered} ${pluralRu(answered, CY_TASKS)} уже сохранены в прогрессе.`;
  }
  updateStartBar();
}

function cyOpenSetup() {
  show('cy-setup');
  cyRenderSetup();
}

/* ---------- раунд ---------- */

/** Раунд по настройкам раздела; быстрый вход «Ошибки» подменяет только набор. Незаконченный
 * раунд новый заменяет без вопроса: его ответы уже сохранены в прогрессе. */
function cyStartRound(mode = cy.filters.mode) {
  cyStartRoundFrom({ filters: { ...cy.filters, mode }, size: cy.size });
}

function cyStartRoundFrom(settings) {
  cyStartRoundWith(cyBuildRound(CHENGYU_BANK, settings.filters, cy.progress, settings.size), settings);
}

function cyStartRoundWith(round, settings = { filters: cy.filters, size: cy.size }) {
  if (!round.length) return;
  Object.assign(cy, {
    round, position: 0, answered: false, correct: 0, marks: [], wrongIds: [], wrongPicks: {}, finished: false,
    // копия: настройки раздела меняются на месте, а «Новый раунд» должен повторить эти
    roundSettings: JSON.parse(JSON.stringify(settings)),
  });
  // с начала раздела раунд — новая запись в истории («назад» вернёт к началу), из итогов — та же
  setAddress('#chengyu/round', state.view === 'cy-setup', 'fromCyHome');
  show('cy-quiz');
  cyRenderQuestion();
  cySaveRound();
}

/** «Продолжить раунд» с плашки: экран раунда остался как был — то же задание, тот же разбор. */
function cyContinueRound() {
  if (!cy.round.length || cy.finished) return;
  setAddress('#chengyu/round', true, 'fromCyHome');
  show('cy-quiz');
}

function cyRenderProgress() {
  $('cyScoreLabel').textContent = `верно ${cy.correct}`;
  cyRenderSteps($('cyProgressSteps'), $('cyProgressTrack'), $('cyProgressFill'));
}

/** Ход раунда — в раунде и на плашке «Раунд не закончен»: кружки ✓/✕, в длинном раунде — полоса. */
function cyRenderSteps(steps, track, fill) {
  const dots = cy.round.length <= MAX_STEP_DOTS;
  steps.hidden = !dots;
  track.hidden = dots;
  if (!dots) {
    fill.style.width = `${((cy.position + (cy.answered ? 1 : 0)) / cy.round.length) * 100}%`;
    return;
  }
  steps.replaceChildren(...cy.round.map((_, index) => {
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
  $('cyGroupMark').textContent = CY_GROUP_MARKS[record.group];
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
  cyRenderCount();
  if (verdict.correct) cy.correct += 1;
  else if (!cy.wrongIds.includes(record.id)) {
    cy.wrongIds.push(record.id);
    cy.wrongPicks[record.id] = optionId;
  }
  cy.marks[cy.position] = verdict.correct;
  cySaveRound();
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
  if (cy.position >= cy.round.length) {
    cyFinishRound();
    return;
  }
  cyRenderQuestion();
  cySaveRound();
  // после разбора страница прокручена вниз — новое задание начинается выше
  scrollToTopOnPhone($('cyQuizView'));
}

/** «Закончить раунд» и Esc: после хотя бы одного ответа — итоги по отвеченным заданиям, без
 * ответов — начало раздела (такой раунд не остаётся незаконченным). */
function cyLeaveRound() {
  if (cy.correct + cy.wrongIds.length > 0) {
    cyFinishRound();
    return;
  }
  cyDiscardRound();
  cyOpenSetup();
}

function cyFinishRound() {
  cyCompleteRound();
  show('cy-results');
}

function cyCompleteRound() {
  cy.finished = true;
  cySaveRound();
  cyRenderResults();
}

function cyRenderResults() {
  const wrong = cy.wrongIds.length;
  // по отвеченным заданиям: после «Закончить раунд» это не весь раунд
  const total = cy.correct + wrong;
  $('cyFinalScore').innerHTML = `${cy.correct}<span class="score-total"> / ${total}</span>`;
  $('cyResultMeterCorrect').style.flex = String(cy.correct);
  $('cyResultMeterWrong').style.flex = String(wrong);
  $('cyResultCounts').innerHTML = `<span><span class="ok" lang="zh-Hans">✓</span> верно — ${cy.correct}</span>`
    + `<span><span class="bad" lang="zh-Hans">✕</span> с ошибкой — ${wrong}</span>`;
  $('cyResultText').textContent = wrong
    ? 'Задания с ошибками вернутся в наборе «Ошибки».'
    : 'Весь раунд без ошибок.';
  $('cyRepeatMistakes').hidden = wrong === 0;
  $('cyRepeatMistakes').textContent = `Повторить ошибки раунда (${wrong})`;
  // «Новый раунд» — тот же набор, длина и темы; после раунда «Ошибки» без ошибок подходящих
  // заданий может не остаться
  const { filters, size } = cy.roundSettings;
  const renewable = cyEligible(CHENGYU_BANK, filters, cy.progress).length > 0;
  $('cyNewRound').hidden = !renewable;
  $('cyNewRoundNote').hidden = !renewable;
  $('cyNewRoundNote').textContent = `Новый раунд — снова ${size === Number.MAX_SAFE_INTEGER ? 'все доступные задания' : cySizeLabel(size)}, ${
    CY_MODE_SUMMARY[filters.mode].toLowerCase()}, ${cyGroupsLabel(filters.groups)}.`;
  // на экране одна главная кнопка: «Повторить ошибки», без ошибок — «Новый раунд», а если и его
  // нет — «К разделу»
  $('cyNewRound').classList.toggle('ink-btn--primary', wrong === 0);
  $('cyNewRound').classList.toggle('ink-btn--secondary', wrong !== 0);
  const homeIsMain = wrong === 0 && !renewable;
  $('cyBackToSetup').classList.toggle('ink-btn--primary', homeIsMain);
  $('cyBackToSetup').classList.toggle('ink-btn--text', !homeIsMain);
  cyRenderMistakes();
}

/** Ошибки раунда: строка — кнопка, под ней разбор (буквально, смысл, ловушка) и подпись выбранного
 * варианта. Раскрыт один разбор, сначала — первый. */
function cyRenderMistakes() {
  const records = cy.round.filter((record) => cy.wrongIds.includes(record.id));
  $('cyResultMistakes').hidden = records.length === 0;
  $('cyMistakeList').replaceChildren(...records.map((record, index) => {
    const picked = record.options.find((option) => option.id === cy.wrongPicks[record.id]);
    const right = cyAnswerText(record);
    const reverse = record.kind === 'reverse';
    const shown = (text) => (reverse ? `<span lang="zh-Hans">${escapeHtml(text)}</span>` : escapeHtml(text));
    const gloss = picked?.gloss?.replace(/\.$/, '');
    const item = document.createElement('li');
    item.innerHTML = [
      `<button class="mistake-head" type="button" aria-expanded="false" aria-controls="cyMistake${index}">`,
      '<span class="ink-seal ink-seal--review ink-seal--md" lang="zh-Hans" aria-hidden="true">复</span>',
      '<span class="mistake-text">',
      `<span class="mistake-question">${reverse ? `«${escapeHtml(record.prompt)}»`
        : `<span class="cy-mistake-han" lang="zh-Hans">${escapeHtml(record.chengyu)}</span>`}</span>`,
      '<span class="mistake-answers">',
      picked ? `Ваш ответ <span class="picked">✕ ${shown(picked.text)}</span>, верно ` : 'Верно ',
      `<span class="right">✓ ${shown(right)}</span>`,
      '</span></span>',
      '<span class="mistake-arrow" aria-hidden="true">▾</span>',
      '</button>',
      `<div class="mistake-panel" id="cyMistake${index}" hidden>`,
      cyFacts(record),
      gloss ? `<p class="mistake-gloss">Ваш ответ ${shown(picked.text)} — ${escapeHtml(gloss)}.</p>` : '',
      '</div>',
    ].join('');
    item.querySelector('.mistake-head').addEventListener('click', (event) => {
      cyOpenMistake(event.currentTarget.getAttribute('aria-expanded') === 'true' ? -1 : index);
    });
    return item;
  }));
  cyOpenMistake(0);
}

function cyOpenMistake(index) {
  for (const [position, item] of [...$('cyMistakeList').children].entries()) {
    item.querySelector('.mistake-head').setAttribute('aria-expanded', String(position === index));
    item.querySelector('.mistake-panel').hidden = position !== index;
  }
}

function cyRepeatMistakes() {
  cyStartRoundWith(cy.round.filter((record) => cy.wrongIds.includes(record.id)), cy.roundSettings);
}

/* ---------- справочник ---------- */

function cyOpenReference() {
  setAddress('#chengyu/reference', true, 'fromCyHome');
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
      record.origin === 'authored' ? '<span class="tag origin">составлено, сверено со словарями</span>' : '',
      '</div>',
      `<h3 class="cy-row-head"><span class="cy-row-han" lang="zh-Hans">${escapeHtml(record.chengyu)}</span>`,
      `<span class="cy-row-pinyin" lang="zh-Hans">${escapeHtml(record.pinyin)}</span></h3>`,
      `<p class="row-meta">${reverse ? `Обратное задание: «${escapeHtml(record.prompt)}»`
        : record.kind === 'odd' ? 'Найти лишний вариант' : 'Подобрать русский аналог'}</p>`,
      appearances ? `<p class="row-meta">${escapeHtml(appearances)}</p>` : '',
      '<details class="row-reveal"><summary>Показать разбор</summary><div class="row-panel">',
      `<p class="row-answer">${record.kind === 'odd' ? 'Лишний' : 'Ответ'}: ${reverse
        ? `<span class="zh" lang="zh-Hans">${escapeHtml(answer)}</span>` : `«${escapeHtml(answer)}»`}</p>`,
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
    else if (state.view === 'cy-quiz') cyLeaveRound();
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
  // Enter в начале раздела — главная кнопка его верха: начать раунд или продолжить незаконченный
  if (state.view === 'cy-setup' && event.key === 'Enter' && !onControl) {
    const main = [$('cyFirstStart'), $('cyStartButton'), $('cyResumeButton')].find((button) => button.offsetParent);
    if (main && !main.disabled) {
      event.preventDefault();
      main.click();
    }
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
for (const id of ['cyFirstStart', 'cyStartButton', 'cyBarStart', 'cyResumeNew']) {
  $(id).addEventListener('click', () => cyStartRound());
}
$('cyQuickMistakes').addEventListener('click', () => cyStartRound('mistakes'));
// подходящих заданий нет: обычный раунд — все задания всех тем
$('cyEmptyAll').addEventListener('click', () => {
  cy.filters = cyDefaultFilters();
  cySaveSettings();
  cyStartRound();
});
$('cyResumeButton').addEventListener('click', cyContinueRound);
// «Настроить раунд» — к «Набору», без записи в адресе
$('cySettingsLink').addEventListener('click', (event) => {
  event.preventDefault();
  $('cySettings').scrollIntoView({ behavior: scrollBehavior(), block: 'start' });
  document.querySelector('input[name="cyMode"]:checked')?.focus({ preventScroll: true });
});
for (const id of ['cyFirstReference', 'cyQuickReference', 'cyResultsReference']) {
  $(id).addEventListener('click', cyOpenReference);
}
$('cyCloseReference').addEventListener('click', cyOpenSetup);
$('cyBackToSetup').addEventListener('click', cyOpenSetup);
$('cyLeaveRound').addEventListener('click', cyLeaveRound);
$('cyNextButton').addEventListener('click', cyNextQuestion);
$('cyRepeatMistakes').addEventListener('click', cyRepeatMistakes);
$('cyNewRound').addEventListener('click', () => cyStartRoundFrom(cy.roundSettings));
$('cyReferenceSearch').addEventListener('input', cyRenderReference);
$('cyReferenceGroup').addEventListener('change', cyRenderReference);
$('cyResetProgress').addEventListener('click', () => {
  if (!confirm('Сбросить прогресс по чэнъюй? Прогресс основного тренажёра останется.')) return;
  cy.progress = {};
  cySaveProgress();
  // плашка незаконченного раунда обещает, что его ответы сохранены, — после сброса это не так
  cyDiscardRound();
  cyRenderSetup();
  cyRenderCount();
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

/** Экран раздела по адресу — при загрузке и когда ученик ходит «назад» и «вперёд». Адреса вне
 * раздела разбирает route в quiz.ui.js. */
function cyRoute() {
  const hash = location.hash;
  if ((hash === '#chengyu/round' || hash === '#chengyu/results') && cy.round.length) {
    const view = cy.finished ? 'cy-results' : 'cy-quiz';
    if (state.view !== view) show(view);
  } else if (hash === '#chengyu/reference') {
    if (state.view !== 'cy-reference') {
      show('cy-reference');
      cyRenderReference();
    }
  } else if (state.view !== 'cy-setup' || hash !== '#chengyu') {
    // «назад» из раунда оставляет его незаконченным: начало раздела покажет плашку «Раунд не закончен»
    cyOpenSetup();
  }
}

cyLoad();
cyRestoreRound();
cyRenderSetup();
// ссылка вида …/#chengyu открывает раздел сразу — и при загрузке, и в открытой странице
if (CY_HASH.test(location.hash)) cyRoute();
window.addEventListener('popstate', () => {
  if (CY_HASH.test(location.hash)) cyRoute();
});
