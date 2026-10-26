const STORAGE_KEY = 'lingvo-trainer:v1';
const STUDY_SETTINGS_KEY = 'lingvo-trainer:settings:v1';
const THEME_KEY = 'lingvo-trainer:theme';
const PINYIN_KEY = 'lingvo-trainer:pinyin';
const QUESTION_ZH_KEY = 'lingvo-trainer:question-zh';
// раунд — в sessionStorage: перезагрузка возвращает на тот же вопрос, а новая вкладка его не видит
const ROUND_KEY = 'lingvo-trainer:round:v1';
const STAGE_NAMES = {
  pri: 'пригласительный', shk: 'школьный', mun: 'муниципальный',
  reg: 'региональный', zak: 'заключительный',
};
const STAGE_ORDER = ['pri', 'shk', 'mun', 'reg', 'zak'];
const STATUS_NAMES = {
  verified: 'проверено', unverified: 'не проверено',
  conflict: 'расхождение ключей', 'needs-review': 'нет ответа',
};

// знак-иероглиф темы — на главной, над вопросом и на карточке базы; тема без знака получает 文
const TOPIC_MARKS = {
  'История и государство': '史',
  'География и административное устройство': '地',
  'Культура, традиции и праздники': '节',
  'Литература, язык, искусство и философия': '文',
  'Общество: население, этносы и религии': '民',
  'Экономика, образование, наука и спорт': '经',
  'Россия и межкультурный блок': '俄',
};
const topicMark = (topic) => TOPIC_MARKS[topic] || '文';
// раздел в строке настроек («разделы: география, история») и на карточке базы на телефоне
const TOPIC_SHORT = {
  'География и административное устройство': 'география',
  'История и государство': 'история',
  'Культура, традиции и праздники': 'культура и праздники',
  'Литература, язык, искусство и философия': 'литература и искусство',
  'Общество: население, этносы и религии': 'общество',
  'Россия и межкультурный блок': 'Россия',
  'Экономика, образование, наука и спорт': 'экономика и наука',
};
// подборки — досье банка: знак и короткое имя для строки настроек; название — из досье (DOSSIERS),
// а два названия заменены по решению автора (2026-10-25)
const DOSSIER_TITLES = { sets: 'Четыре великих и другие наборы', people: 'Известные люди' };
const DOSSIER_MARKS = {
  money: '钱', dynasties: '朝', landmarks: '塔', painting: '画', people: '人', 'modern-history': '近',
  cinema: '影', space: '天', cuisine: '食', literature: '书', myths: '神', holidays: '节', nature: '山',
  provinces: '省', crafts: '艺', sets: '四', ethnos: '族', state: '国', 'modern-china': '今',
};
const DOSSIER_SHORT = {
  money: 'деньги', dynasties: 'династии и правители', landmarks: 'достопримечательности',
  painting: 'живопись и каллиграфия', people: 'известные люди', 'modern-history': 'история XIX–XX веков',
  cinema: 'кино и анимация', space: 'космос', cuisine: 'кухня и блюда', literature: 'литература',
  myths: 'мифы и легенды', holidays: 'праздники', nature: 'природа и инженерия', provinces: 'провинции и города',
  crafts: 'ремёсла', sets: 'четыре великих', ethnos: 'этносы и быт', state: 'государство и символы',
  'modern-china': 'современный Китай',
};
const dossierTitle = (id) => DOSSIER_TITLES[id] || DOSSIERS[id] || id;
// «Семь разделов олимпиады…»
const COUNT_WORDS = ['', 'Один', 'Два', 'Три', 'Четыре', 'Пять', 'Шесть', 'Семь', 'Восемь', 'Девять', 'Десять'];
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
const MODE_COPY = {
  all: 'Все доступные вопросы в случайном порядке.',
  new: 'Только вопросы, на которые вы ещё не отвечали.',
  mistakes: 'Вопросы, в которых последний ответ был ошибочным.',
  due: 'Пройденные вопросы, срок повторения которых наступил.',
};
// строка настроек раунда: «Все вопросы, выбор ответа, 10 вопросов, все темы.»
const MODE_SUMMARY = { all: 'Все вопросы', new: 'Новые вопросы', mistakes: 'Ошибки', due: 'Повторение' };
const FORMAT_SUMMARY = { choice: 'выбор ответа', recall: 'вспомни сам', truefalse: 'верно или нет' };
// «Ответы на первые три вопроса…»: до десяти — словом
const NUMBER_WORDS = ['', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять', 'десять'];
const ALL_SIZE = Number.MAX_SAFE_INTEGER;
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
  topics: [], dossiers: [], years: [], stages: [], mode: 'all', onlyVerified: false, origin: 'all',
});

function defaultStudySettings() {
  return { filters: defaultFilters(), size: 10, format: 'choice', topicsBy: 'sections' };
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
  // как выбираются темы раунда: 'sections' — разделами, 'dossiers' — подборками
  topicsBy: savedStudySettings.topicsBy,
  // формат замораживается на старте раунда: настройки во время раунда не видны
  roundFormat: 'choice',
  // фильтры (с режимом) и длина, с которыми начат раунд: «Новый раунд» в итогах повторяет их
  roundSettings: null,
  // раунд дошёл до итогов; начатый и не законченный — плашка «Раунд не закончен» на главной
  finished: false,
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
  $('themeState').textContent = theme === 'dark' ? 'тёмная' : 'светлая';
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
  $('pinyinState').textContent = on ? 'вкл' : 'выкл';
  for (const id of ['pinyinToggle', 'pinyinMenu']) $(id).setAttribute('aria-pressed', String(on));
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

/* ---------- китайский текст вопроса ---------- */

// у части олимпиадных заданий вопрос в бланке дан и по-китайски; по умолчанию он скрыт, чтобы
// русская формулировка читалась без подсказки. Как и пиньинь, показ решает атрибут на <html>, а
// в раунде его можно открыть для одного вопроса кнопкой под формулировкой
function applyQuestionZh(on) {
  document.documentElement.dataset.questionZh = on ? 'on' : 'off';
  $('questionZhLabel').textContent = on ? 'Вопрос 中文: вкл' : 'Вопрос 中文: выкл';
  $('questionZhState').textContent = on ? 'вкл' : 'выкл';
  for (const id of ['questionZhToggle', 'questionZhMenu']) $(id).setAttribute('aria-pressed', String(on));
}

/* ---------- меню «Вид» (телефон) ---------- */

// на телефоне три переключателя шапки заняли бы две строки на каждом экране — они в меню
function setViewMenu(open) {
  $('viewMenu').hidden = !open;
  $('viewToggle').setAttribute('aria-expanded', String(open));
  $('viewToggle').querySelector('.view-arrow').textContent = open ? '▴' : '▾';
}

function initQuestionZh() {
  let on = false;
  try {
    on = localStorage.getItem(QUESTION_ZH_KEY) === 'on';
  } catch { /* приватный режим: по умолчанию скрыт */ }
  applyQuestionZh(on);
}

function toggleQuestionZh() {
  const on = document.documentElement.dataset.questionZh !== 'on';
  applyQuestionZh(on);
  try {
    localStorage.setItem(QUESTION_ZH_KEY, on ? 'on' : 'off');
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
      settings: { filters: state.filters, size: state.size, format: state.format, topicsBy: state.topicsBy },
    }));
  } catch {}
}

/** Снимок раунда: вопросы по id, ход, счёт, повторы ошибок и настройки, с которыми он начат. */
function saveRound() {
  try {
    sessionStorage.setItem(ROUND_KEY, JSON.stringify({
      version: 1,
      round: state.round.map((record) => record.id),
      position: state.position,
      answered: state.answered,
      marks: state.marks,
      correct: state.correct,
      wrongIds: state.wrongIds,
      wrongPicks: state.wrongPicks,
      retryQueue: state.retryQueue.map(({ record, afterPosition }) => ({ id: record.id, afterPosition })),
      retriedIds: [...state.retriedIds],
      format: state.roundFormat,
      recallCounts: state.recallCounts,
      streak: state.streak,
      stepDots: state.stepDots,
      initialRoundLength: state.initialRoundLength,
      settings: state.roundSettings,
      finished: state.finished,
    }));
  } catch { /* без sessionStorage раунд не переживёт перезагрузку, но идёт как обычно */ }
}

function discardRound() {
  state.round = [];
  state.finished = false;
  try {
    sessionStorage.removeItem(ROUND_KEY);
  } catch {}
}

/** После перезагрузки — тот же раунд. Вопрос, на который уже ответили, второй раз не задаётся:
 * ответ сохранён в прогрессе, поэтому раунд продолжается со следующего (или кончается). */
function restoreRound() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(ROUND_KEY) || 'null');
    if (saved?.version !== 1) return;
    const byId = new Map(QUESTION_BANK.map((record) => [record.id, record]));
    const round = saved.round.map((id) => byId.get(id));
    const retryQueue = saved.retryQueue.map(({ id, afterPosition }) => ({ record: byId.get(id), afterPosition }));
    // банк сменился между загрузками или снимок неполный — такой раунд не восстановить
    const filters = saved.settings?.filters;
    if (!round.length || round.some((record) => !record) || retryQueue.some((entry) => !entry.record)
        || !FORMATS.has(saved.format) || !Number.isInteger(saved.position) || saved.position < 0
        || ![saved.marks, saved.wrongIds, saved.retriedIds].every(Array.isArray)
        || !saved.wrongPicks || typeof saved.wrongPicks !== 'object' || !saved.recallCounts
        || ![filters?.topics, filters?.years, filters?.stages].every(Array.isArray)) {
      discardRound();
      return;
    }
    Object.assign(state, {
      round,
      position: saved.position,
      answered: saved.answered,
      marks: saved.marks,
      correct: saved.correct,
      wrongIds: saved.wrongIds,
      wrongPicks: saved.wrongPicks,
      retryQueue,
      retriedIds: new Set(saved.retriedIds),
      roundFormat: saved.format,
      recallCounts: saved.recallCounts,
      streak: saved.streak,
      stepDots: saved.stepDots,
      initialRoundLength: saved.initialRoundLength,
      roundSettings: saved.settings,
      finished: saved.finished,
    });
    if (state.finished) renderResults();
    else if (state.answered && !advance()) completeRound();
    else {
      renderQuestion();
      saveRound();
    }
  } catch {
    // что бы ни случилось со снимком, главная должна открыться
    discardRound();
  }
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
      // плашка незаконченного раунда обещает, что его ответы сохранены, — прогресс заменён
      discardRound();
      if ('chengyu' in parsed) {
        cy.progress = parsed.chengyu;
        cySaveProgress();
        cyDiscardRound();
        cyRenderSetup();
      }
      renderSetup();
    } catch {
      alert('Не удалось загрузить прогресс: файл повреждён или сохранён другой версией тренажёра.');
    }
  };
  reader.readAsText(file);
}

/* ---------- экраны и адреса ---------- */

// у раунда, итогов и базы свои адреса: системное «назад» с них ведёт на главную, а не прочь
// с сайта, а перезагрузка открывает тот же экран. У «Чэнъюй» так же, от начала раздела #chengyu
const VIEW_HASHES = {
  setup: '', quiz: '#round', results: '#results', database: '#database',
  'cy-setup': '#chengyu', 'cy-quiz': '#chengyu/round', 'cy-results': '#chengyu/results',
  'cy-reference': '#chengyu/reference',
};

/** Адрес экрана. С push уход с главной добавляет запись в историю, иначе адрес заменяется.
 * Добавленная запись помечена (mark — fromHome, у «Чэнъюй» fromCyHome): когда с неё вернулись
 * на главную кнопкой, следующий уход снова займёт её — в истории за началом раздела не больше
 * одного экрана этого раздела. Метку каждого раздела читает только он сам: переход шапкой
 * заменяет текущую запись, и раунд другого раздела добавит свою. */
function setAddress(hash, push = false, mark = 'fromHome') {
  const url = `${location.pathname}${location.search}${hash}`;
  try {
    if (push && !history.state?.[mark]) history.pushState({ [mark]: true }, '', url);
    else if (location.hash !== hash) history.replaceState(history.state, '', url);
  } catch { /* без истории адрес просто не меняется */ }
}

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
  // печать уже стоит: вернувшись к отвеченному вопросу, ученик не должен видеть удар снова
  $('feedback').classList.remove('stamp');
  const chengyu = view.startsWith('cy-');
  setAddress(VIEW_HASHES[view]);
  for (const [link, current] of [
    ['navSetup', !chengyu && view !== 'database'],
    ['navDatabase', view === 'database'],
    ['navChengyu', chengyu],
  ]) {
    if (current) $(link).setAttribute('aria-current', 'page');
    else $(link).removeAttribute('aria-current');
  }
  // в шапке — счёт своего раздела: у «Чэнъюй» решённые задания (cyRenderCount в src/chengyu.ui.js)
  if (chengyu) cyRenderCount();
  else renderBankCount();
  $('footerNote').textContent = chengyu ? cyFooterNote() : bankSummary(QUESTION_BANK);
  setViewMenu(false);
  window.scrollTo?.(0, 0);
  updateStartBar();
}

/** Экран по адресу — при загрузке и когда ученик ходит «назад» и «вперёд» в браузере. */
function route() {
  const hash = location.hash;
  // адреса раздела разбирает src/chengyu.ui.js (cyRoute)
  if (/^#chengyu(?:\/|$)/.test(hash)) return;
  if ((hash === '#round' || hash === '#results') && state.round.length) {
    const view = state.finished ? 'results' : 'quiz';
    if (state.view !== view) show(view);
  } else if (hash === '#database') {
    if (state.view !== 'database') {
      show('database');
      renderDatabase();
    }
  } else if (state.view !== 'setup' || hash) {
    // «назад» из раунда оставляет его незаконченным: главная покажет плашку «Раунд не закончен»
    backToSetup();
  }
}

function stageLabel(code) {
  return STAGE_NAMES[code] || code;
}

/** «ВсОШ 2015/16 · региональный этап · задание 9», «ВсОШ 2025/26 · муниципальный этап, Санкт-Петербург · задание 3» */
function occurrenceLabel(occurrence) {
  return `ВсОШ ${occurrence.year.replace('-', '/')} · ${stageLabel(occurrence.stageCode)} этап${
    occurrence.region ? `, ${occurrence.region}` : ''}${
    occurrence.number ? ` · задание ${occurrence.number}` : ''}`;
}

function renderBankCount() {
  // по банку, а не по всем записям прогресса: у снятых вопросов прогресс остаётся в браузере
  const done = QUESTION_BANK.filter((record) => state.progress[record.id]?.completed).length;
  $('bankCount').textContent = `Пройдено ${done} из ${QUESTION_BANK.length}`;
}

/** Строка выбора темы: знак, название, «пройдено N/M» и флажок; отмеченные — в state.filters[key]. */
function topicCheck(value, name, markText, key) {
  const label = document.createElement('label');
  label.className = 'topic-check';
  const mark = document.createElement('span');
  mark.className = 'topic-mark';
  mark.lang = 'zh-Hans';
  mark.setAttribute('aria-hidden', 'true');
  mark.textContent = markText;
  const text = document.createElement('span');
  text.className = 'topic-text';
  const caption = document.createElement('span');
  caption.className = 'topic-name';
  caption.textContent = name;
  const count = document.createElement('span');
  count.className = 'topic-count';
  const progress = document.createElement('span');
  progress.className = 'topic-progress';
  count.append('пройдено ', progress);
  text.append(caption, count);
  const input = document.createElement('input');
  input.type = 'checkbox';
  input.value = value;
  label.append(mark, text, input);
  input.addEventListener('change', (event) => {
    const list = state.filters[key];
    if (event.target.checked) list.push(value);
    else list.splice(list.indexOf(value), 1);
    saveStudySettings();
    renderSetup();
  });
  return label;
}

const bankTopics = () => [...new Set(QUESTION_BANK.map((r) => r.topic))].sort();
const bankDossiers = () => [...new Set(QUESTION_BANK.map((r) => r.dossier).filter(Boolean))]
  .sort((a, b) => dossierTitle(a).localeCompare(dossierTitle(b), 'ru'));

function renderSetup() {
  if (!$('topicControls').children.length) {
    const topics = bankTopics();
    $('topicControls').append(...topics.map((topic) => topicCheck(topic, topic, topicMark(topic), 'topics')));
    $('dossierControls').append(...bankDossiers().map((id) =>
      topicCheck(id, dossierTitle(id), DOSSIER_MARKS[id] || '文', 'dossiers')));

    const years = [...new Set(QUESTION_BANK.flatMap((r) => r.occurrences.map((o) => o.year)))].sort();
    fillSelect($('yearFilter'), 'Все годы', years.map((y) => [y, y]));
    const stages = STAGE_ORDER.filter((code) =>
      QUESTION_BANK.some((r) => r.occurrences.some((o) => o.stageCode === code)));
    fillSelect($('stageFilter'), 'Все этапы', stages.map((code) => [code, stageLabel(code)]));
    fillSelect($('databaseTopic'), 'Все темы', topics.map((t) => [t, t]));
  }
  renderTopicChoice();
  $('yearFilter').value = state.filters.years[0] || '';
  $('stageFilter').value = state.filters.stages[0] || '';
  const size = state.size === ALL_SIZE ? 'all' : String(state.size);
  for (const input of document.querySelectorAll('input[name="roundSize"]')) {
    input.checked = input.value === size;
  }
  $('onlyVerified').checked = state.filters.onlyVerified;
  // на пилюле режима — сколько вопросов он даст при текущих фильтрах
  const modeCounts = {};
  for (const input of document.querySelectorAll('input[name="studyMode"]')) {
    input.checked = input.value === state.filters.mode;
    modeCounts[input.value] = eligible(QUESTION_BANK, { ...state.filters, mode: input.value }, state.progress).length;
    input.nextElementSibling.querySelector('.pill-count').textContent = String(modeCounts[input.value]);
  }
  $('modeHelp').textContent = MODE_COPY[state.filters.mode];
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
  renderHome(modeCounts);
  renderBankCount();
}

/** Верх главной: первый визит, «Следующий раунд» или «Раунд не закончен»; полоса внизу. */
function renderHome(modeCounts) {
  const available = modeCounts[state.filters.mode];
  const unfinished = state.round.length > 0 && !state.finished;
  const fresh = !unfinished && !QUESTION_BANK.some((record) => state.progress[record.id]);
  $('firstHero').hidden = !fresh;
  $('nextRound').hidden = fresh;
  $('nextMain').hidden = unfinished;
  $('resumePanel').hidden = !unfinished;

  const settings = { filters: state.filters, size: state.size };
  const summary = settingsLine(settings, state.format);
  const inRound = Math.min(state.size, available);
  const notice = available
    ? `Подходит вопросов: ${available}, в раунде будет ${inRound}.`
    : state.filters.mode === 'due'
      ? 'Нет вопросов для повторения по текущим фильтрам.'
      : 'Под текущие фильтры не подходит ни один вопрос — снимите часть ограничений.';
  $('nextSummary').textContent = summary;
  $('eligibleNotice').textContent = notice;
  // первый визит: пока настройки не трогали, подпись под кнопкой просто объясняет раунд
  const { filters } = state;
  const plain = filters.mode === 'all' && state.format === 'choice' && !filters.topics.length
    && !filters.dossiers.length && !filters.years.length
    && !filters.stages.length && filters.origin === 'all' && !filters.onlyVerified;
  $('firstCaption').textContent = !plain || !available ? `${summary} ${notice}`
    : `${state.size === ALL_SIZE ? 'Все вопросы базы в случайном порядке'
      : `${state.size} случайных вопросов из всех тем`}. Режим, формат и темы — ниже.`;

  for (const id of ['firstStart', 'startButton', 'barStart']) $(id).disabled = available === 0;
  // на плашке подсказки «не подходит ни один вопрос» нет — кнопка, которая ничего не сделает, не показывается
  $('resumeNew').hidden = available === 0;
  // главная кнопка на экране одна: без подходящих вопросов это «Начать обычный раунд»
  for (const id of ['startButton', 'barStart']) {
    $(id).classList.toggle('ink-btn--primary', available !== 0);
    $(id).classList.toggle('ink-btn--secondary', available === 0);
  }
  $('emptyActions').hidden = available !== 0;
  $('startBarText').textContent = available
    ? `${chosenCount(filters) || 'Все темы'}, ${inRound} из ${available} подходящих`
    : 'Под фильтры не подходит ни один вопрос';

  // быстрые входы: раунд из ошибок или из вопросов, которые пора повторить; пустой не показывается
  for (const [id, mode] of [['quickMistakes', 'mistakes'], ['quickDue', 'due']]) {
    const count = modeCounts[mode];
    $(id).hidden = count === 0;
    $(id).querySelector('.quick-number').textContent = String(count);
    $(id).querySelector('.quick-unit').textContent = pluralRu(count, ['вопрос', 'вопроса', 'вопросов']);
  }
  $('quickStarts').hidden = modeCounts.mistakes === 0 && modeCounts.due === 0;

  if (unfinished) {
    $('resumeProgress').textContent = `Вопрос ${state.position + 1} из ${state.round.length}, верно ${state.correct}.`;
    $('resumeSettings').textContent = ` ${settingsLine(state.roundSettings, state.roundFormat, false)}`;
    renderSteps($('resumeSteps'), $('resumeTrack'), $('resumeFill'));
    const answered = state.position + (state.answered ? 1 : 0);
    $('resumeSaved').hidden = answered === 0;
    $('resumeSaved').textContent = answered === 1 ? 'Ответ на первый вопрос уже сохранён в прогрессе.'
      : `Ответы на первые ${NUMBER_WORDS[answered] || answered} ${pluralRu(answered, ['вопрос', 'вопроса', 'вопросов'])}`
        + ' уже сохранены в прогрессе.';
  }
  updateStartBar();
}

/** Темы словами. В строке настроек — коротко: «разделы: география, история», «подборка: кухня и
 * блюда»; в заголовке раздела — название одной темы или «2 подборки». */
function topicsLabel({ topics, dossiers = [] }, inSentence = false) {
  const sets = dossiers.length > 0;
  const list = sets ? dossiers : topics;
  if (!list.length) return 'все темы';
  if (inSentence) {
    const kind = sets ? (list.length === 1 ? 'подборка' : 'подборки') : list.length === 1 ? 'раздел' : 'разделы';
    const short = (item) => (sets ? DOSSIER_SHORT[item] || dossierTitle(item).toLocaleLowerCase('ru') : TOPIC_SHORT[item] || item);
    return `${kind}: ${list.map(short).join(', ')}`;
  }
  return list.length === 1 ? (sets ? dossierTitle(list[0]) : list[0]) : chosenCount({ topics, dossiers });
}

/** «2 подборки», «3 раздела»; ничего не выбрано — пустая строка. */
function chosenCount({ topics, dossiers = [] }) {
  const sets = dossiers.length > 0;
  const count = sets ? dossiers.length : topics.length;
  return count ? `${count} ${pluralRu(count, sets ? ['подборка', 'подборки', 'подборок'] : ['раздел', 'раздела', 'разделов'])}` : '';
}

/** Фильтры словами: темы, «только с олимпиад», «2015/16», «муниципальный этап»… У раунда из
 * найденного в базе фильтр один — сами найденные вопросы. */
function filterLabels(filters, inSentence = false) {
  if (filters.ids) return ['найденные в базе'];
  const { years, stages, origin, onlyVerified } = filters;
  return [
    topicsLabel(filters, inSentence),
    origin === 'olympiad' ? 'только с олимпиад' : origin === 'addition' ? 'только дополнения' : '',
    years[0] ? years[0].replace('-', '/') : '',
    stages[0] ? `${stageLabel(stages[0])} этап` : '',
    onlyVerified ? 'только проверенные' : '',
  ].filter(Boolean);
}

/** «10 вопросов», «все доступные». */
function sizeLabel(size) {
  return size === ALL_SIZE ? 'все доступные' : `${size} ${pluralRu(size, ['вопрос', 'вопроса', 'вопросов'])}`;
}

/** «Все вопросы, выбор ответа, 10 вопросов, все темы.» — без длины на плашке незаконченного раунда. */
function settingsLine({ filters, size }, format, withSize = true) {
  return `${[MODE_SUMMARY[filters.mode], FORMAT_SUMMARY[format], withSize ? sizeLabel(size) : '',
    ...filterLabels(filters, true)].filter(Boolean).join(', ')}.`;
}

/** «Темы раунда»: разделы или подборки — отметки, «пройдено N/M», подсказка и итог выбора. */
function renderTopicChoice() {
  const bySections = state.topicsBy === 'sections';
  for (const input of document.querySelectorAll('input[name="topicsBy"]')) input.checked = input.value === state.topicsBy;
  $('topicControls').hidden = !bySections;
  $('dossierControls').hidden = bySections;
  const groups = [
    [$('topicControls'), progressByTopic(QUESTION_BANK, state.progress), state.filters.topics],
    [$('dossierControls'), progressByDossier(QUESTION_BANK, state.progress), state.filters.dossiers],
  ];
  for (const [container, counts, picked] of groups) {
    for (const label of container.children) {
      const input = label.querySelector('input');
      input.checked = picked.includes(input.value);
      const { completed, total } = counts[input.value] ?? { completed: 0, total: 0 };
      label.querySelector('.topic-progress').textContent = `${completed}/${total}`;
    }
  }
  const sections = $('topicControls').children.length;
  $('sectionsCount').textContent = String(sections);
  $('dossiersCount').textContent = String($('dossierControls').children.length);
  const questions = (count) => `${count} ${pluralRu(count, ['вопрос', 'вопроса', 'вопросов'])}`;
  const bank = QUESTION_BANK.length;
  $('topicsHelp').textContent = bySections
    ? `${COUNT_WORDS[sections] || sections} ${pluralRu(sections, ['раздел', 'раздела', 'разделов'])} олимпиады: в них все ${questions(bank)}.`
    : `Подборки собраны по темам досье: ${QUESTION_BANK.filter((r) => r.dossier).length} из ${bank} ${ofQuestions(bank)}.`;
  $('topicsHelpMore').textContent = bySections
    ? ' Если не выбрать ни одного, в раунд попадут все.' : ' Отметьте одну или несколько.';
  const [, counts, picked] = groups[bySections ? 0 : 1];
  const chosen = picked.reduce((sum, item) => sum + (counts[item]?.total ?? 0), 0);
  $('topicsFoot').textContent = picked.length
    ? `Выбрано: ${chosenCount(state.filters)}, ${questions(chosen)}.`
    : 'Ничего не выбрано — в раунд попадут вопросы из всех тем.';
}

/** Свёрнутые «Режим», «Формат», «Темы раунда»: в заголовке — что выбрано сейчас. */
function renderFoldValues() {
  // у пилюли режима после названия — число вопросов, в заголовок идёт только название
  const picked = (name) => document.querySelector(`input[name="${name}"]:checked`)?.nextElementSibling?.firstChild?.textContent.trim();
  $('modeValue').textContent = picked('studyMode') || '';
  $('formatValue').textContent = picked('studyFormat') || '';
  $('topicsValue').textContent = filterLabels(state.filters).join(' · ');
}

/** Телефон: кнопка раунда внизу экрана — только пока верхняя «Начать раунд» («Начать первый раунд»)
 * за краем: на экране всегда видна одна главная кнопка. При плашке «Раунд не закончен» полосы нет:
 * её «Начать раунд» молча заменил бы незаконченный раунд вместо «Продолжить». У «Чэнъюй» — своя
 * полоса с теми же правилами. */
function updateStartBar() {
  for (const [view, bar, buttons] of [
    ['setup', 'startBar', ['firstStart', 'startButton']],
    ['cy-setup', 'cyStartBar', ['cyFirstStart', 'cyStartButton']],
  ]) {
    let shown = false;
    if (state.view === view && onPhone()) {
      const top = buttons.map($).find((button) => button.offsetParent);
      const viewport = window.visualViewport;
      const visibleBottom = viewport ? viewport.offsetTop + viewport.height : window.innerHeight;
      const rect = top?.getBoundingClientRect();
      shown = Boolean(rect) && (rect.bottom < 0 || rect.top > visibleBottom - $(bar).offsetHeight);
    }
    $(bar).classList.toggle('is-shown', shown);
  }
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

/** Раунд по текущим настройкам главной; быстрый вход подменяет только режим. Незаконченный
 * раунд новый заменяет без вопроса: его ответы уже сохранены в прогрессе. */
function startRound(mode = state.filters.mode) {
  startRoundFrom({ filters: { ...state.filters, mode }, size: state.size }, state.format);
}

function startRoundFrom(settings, format) {
  const round = buildRound(QUESTION_BANK, settings.filters, state.progress, settings.size);
  if (round.length) startRoundWith(round, format, settings);
}

function startRoundWith(round, format = state.format, settings = { filters: state.filters, size: state.size }) {
  // копия: фильтры главной меняются на месте, а «Новый раунд» должен повторить эти
  state.roundSettings = JSON.parse(JSON.stringify(settings));
  state.finished = false;
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
  // с главной раунд — новая запись в истории («назад» вернёт на главную), из итогов — та же
  setAddress('#round', state.view === 'setup');
  show('quiz');
  renderQuestion();
  saveRound();
}

/** «Продолжить раунд» с плашки: экран раунда остался как был — тот же вопрос, тот же разбор. */
function continueRound() {
  if (!state.round.length || state.finished) return;
  setAddress('#round', true);
  show('quiz');
}

function repeatMistakes() {
  const wrong = wrongQuestions(state.round, state.wrongIds);
  if (wrong.length) startRoundWith(wrong, state.roundFormat, state.roundSettings);
}

function renderQuestion() {
  const record = state.round[state.position];
  if (!record) return finishRound();

  state.answered = false;
  const origin = recordOrigin(record);
  // подпись источника — по фильтрам самого раунда: он мог быть собран не по нынешним настройкам главной
  // («Тренировать найденные», «Продолжить раунд» после смены года); нет подходящего — первое появление
  const first = origin.isAddition ? null
    : matchingOccurrence(record, state.roundSettings?.filters ?? state.filters) ?? record.occurrences[0];
  $('progressLabel').textContent = `Вопрос ${state.position + 1} из ${state.round.length}`;
  renderProgress();
  $('topicMark').textContent = topicMark(record.topic);
  $('topicLabel').textContent = record.topic;
  // у дополнения года и этапа нет — над ним одна метка «Дополнение»
  $('sourceLabel').textContent = first ? occurrenceLabel(first) : '';
  $('sourceLabel').hidden = !first;
  $('originPill').textContent = 'Дополнение';
  $('originPill').hidden = !origin.isAddition;
  $('unverifiedPill').hidden = record.answer.state !== 'unverified';
  $('retryPill').hidden = !isRepeatInRound(state.round, state.position);
  $('questionText').replaceChildren(...questionNodes(record.questionRu));
  $('questionZh').replaceChildren(...[record.questionZh || '', pinyinLine(record.questionZh)].filter(Boolean));
  $('questionZh').hidden = !record.questionZh;
  $('questionZh').classList.remove('revealed');
  $('questionZhReveal').hidden = !record.questionZh;

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

function renderProgress() {
  $('scoreLabel').textContent = `верно ${state.correct}${
    state.roundFormat === 'truefalse' ? ` · серия ${state.streak}` : ''}`;
  renderSteps($('progressSteps'), $('progressTrack'), $('progressFill'));
}

/** Ход раунда — в раунде и на плашке «Раунд не закончен»: кружки ✓/✕ до MAX_STEP_DOTS
 * вопросов, дальше — полоса. */
function renderSteps(steps, track, fill) {
  const dots = state.stepDots;
  steps.hidden = !dots;
  track.hidden = dots;
  if (!dots) {
    const done = state.position + (state.answered ? 1 : 0);
    fill.style.width = `${(done / state.round.length) * 100}%`;
    return;
  }
  steps.replaceChildren(...state.round.map((_, index) => {
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
  saveRound();
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
  showFeedback(record, verdict.correct ? 'good' : 'bad', [
    `<strong>${verdict.correct ? 'Верно' : 'Неверно'}</strong>`,
    verdict.correct
      ? hinted ? '<span>С подсказкой — засчитано как «вспомнил неточно».</span>' : ''
      : `<span>${rightAnswerHtml(record)}</span>`,
  ].join(''));
}

/** После выбора: верный — нефритом, выбранный неверный — киноварью, подписи под неверными, а под
 * верным — его русское название (у вопросов досье). */
function markOptions(record, optionId) {
  const glosses = new Map(optionGlosses(record).map((item) => [item.optionId, item.gloss]));
  if (record.answer.gloss) glosses.set(record.answer.optionId, record.answer.gloss);
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

/** «Правильный ответ: 莫高窟 — Пещеры Могао.» — русское название есть у вопросов досье. */
function rightAnswerHtml(record) {
  const right = record.options.find((option) => option.id === record.answer.optionId);
  const name = answerName(record);
  return `Правильный ответ: <span lang="zh-Hans">${escapeHtml(right.zh)}</span>${name ? ` — ${escapeHtml(name)}` : ''}.`;
}

/** Разбор под вопросом: строка вердикта (её задаёт формат), пояснение, источники. */
function showFeedback(record, kind, verdictHtml) {
  const sources = evidenceList(record.evidence);
  // stamp — удар печати (quiz.css); его снимает show(), чтобы возврат на экран не ставил печать заново
  $('feedback').className = `feedback ${kind} stamp`;
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
  const name = answerName(record);
  showFeedback(record, 'reveal',
    `<strong lang="zh-Hans">${escapeHtml(right.zh)}</strong>${reading}<span>Правильный ответ${
      name ? ` — ${escapeHtml(name)}` : ''}</span>`);
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
  const shown = record.options.find((option) => option.id === statement.optionId);
  const about = statement.isTrue
    ? rightAnswerHtml(record)
    : `${shown.gloss ? `<span lang="zh-Hans">${escapeHtml(shown.zh)}</span> — ${escapeHtml(shown.gloss)}. ` : ''}`
      + rightAnswerHtml(record);
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

/** Следующая позиция раунда, со вставкой отложенного повтора ошибки; false — вопросы кончились. */
function advance() {
  state.position += 1;
  const retryIndex = nextRetryInsertion(state.retryQueue, state.position, state.round.length);
  if (retryIndex !== -1) {
    const [retry] = state.retryQueue.splice(retryIndex, 1);
    state.round.splice(state.position, 0, retry.record);
  }
  return state.position < state.round.length;
}

function nextQuestion() {
  if (!state.answered) return;
  // «Следующий вопрос» сейчас скроется: фокус с него снимаем сразу (см. show)
  $('nextButton').blur();
  if (!advance()) {
    finishRound();
    return;
  }
  renderQuestion();
  saveRound();
  // после разбора страница прокручена вниз — новый вопрос начинается выше
  scrollToTopOnPhone($('quizView'));
}

/** «Закончить раунд» и Esc: после хотя бы одного ответа — итоги по отвеченным вопросам, без
 * ответов — главная (такой раунд не остаётся незаконченным). */
function leaveRound() {
  if (state.correct + state.wrongIds.length > 0) {
    finishRound();
    return;
  }
  discardRound();
  backToSetup();
}

function finishRound() {
  completeRound();
  show('results');
  renderSetup();
}

function completeRound() {
  state.finished = true;
  saveRound();
  renderResults();
}

function renderResults() {
  const wrongCount = state.wrongIds.length;
  // по первым попыткам отвеченных вопросов: после «Закончить раунд» это не весь раунд
  const total = state.correct + wrongCount;
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
  $('resultText').textContent = wrongCount
    ? 'Вопросы с ошибками вернутся в режиме «Ошибки» и при повторении.'
    : 'Весь раунд без ошибок.';
  $('repeatMistakes').hidden = wrongCount === 0;
  $('repeatMistakes').textContent = `Повторить ошибки раунда (${wrongCount})`;
  // «Новый раунд» — тот же режим, формат, длина и фильтры; после раунда «Ошибки» без ошибок
  // подходящих вопросов может не остаться
  const { filters, size } = state.roundSettings;
  const renewable = eligible(QUESTION_BANK, filters, state.progress).length > 0;
  $('newRound').hidden = !renewable;
  $('newRoundNote').hidden = !renewable;
  $('newRoundNote').textContent = `Новый раунд — снова ${size === ALL_SIZE ? 'все доступные вопросы' : sizeLabel(size)}, ${
    [MODE_SUMMARY[filters.mode].toLowerCase(), state.roundFormat === 'choice' ? '' : FORMAT_SUMMARY[state.roundFormat],
      ...filterLabels(filters, true)].filter(Boolean).join(', ')}.`;
  // на экране одна главная кнопка: «Повторить ошибки», без ошибок — «Новый раунд», а если и его
  // нет — «На главную»
  $('newRound').classList.toggle('ink-btn--primary', wrongCount === 0);
  $('newRound').classList.toggle('ink-btn--secondary', wrongCount !== 0);
  const homeIsMain = wrongCount === 0 && !renewable;
  $('backToSetup').classList.toggle('ink-btn--primary', homeIsMain);
  $('backToSetup').classList.toggle('ink-btn--text', !homeIsMain);
  renderMistakes();
}

/** Ошибки раунда: строка — кнопка, под ней разбор (пояснение, подпись выбранного неверного
 * варианта, свёрнутые источники). Раскрыт один разбор, сначала — первый. */
function renderMistakes() {
  const wrong = wrongQuestions(state.round, state.wrongIds);
  $('resultMistakes').hidden = wrong.length === 0;
  $('mistakeList').replaceChildren(...wrong.map((record, index) => {
    const pick = state.wrongPicks[record.id] ?? {};
    const picked = record.options.find((option) => option.id === pick.optionId);
    const right = record.options.find((option) => option.id === record.answer.optionId);
    const gloss = picked && picked !== right ? picked.gloss?.replace(/\.$/, '') : '';
    const sources = evidenceList(record.evidence);
    const item = document.createElement('li');
    item.innerHTML = [
      `<button class="mistake-head" type="button" aria-expanded="false" aria-controls="mistake${index}">`,
      '<span class="ink-seal ink-seal--review ink-seal--md" lang="zh-Hans" aria-hidden="true">复</span>',
      '<span class="mistake-text">',
      `<span class="mistake-question">${escapeHtml(record.questionRu)}</span>`,
      '<span class="mistake-answers">',
      picked ? `Ваш ответ ${pick.said === undefined ? '' : `«${pick.said ? 'верно' : 'неверно'}» для `}`
        + `<span class="picked" lang="zh-Hans">${pick.said !== undefined && pick.isTrue ? '✓' : '✕'} ${escapeHtml(picked.zh)}</span>, верно `
        : 'Верно ',
      `<span class="right" lang="zh-Hans">✓ ${escapeHtml(right.zh)}</span>`,
      answerName(record) ? ` — ${escapeHtml(answerName(record))}` : '',
      '</span></span>',
      '<span class="mistake-arrow" aria-hidden="true">▾</span>',
      '</button>',
      `<div class="mistake-panel" id="mistake${index}" hidden>`,
      `<p class="mistake-why">${record.explanation.ru ? escapeHtml(record.explanation.ru)
        : 'Ответ взят из официального ключа, но ещё не перепроверен по источникам.'}</p>`,
      gloss ? `<p class="mistake-gloss">Ваш ответ <span lang="zh-Hans">${escapeHtml(picked.zh)}</span> — ${escapeHtml(gloss)}.</p>` : '',
      sources ? `<details class="mistake-sources"><summary>Источники (${record.evidence.length})</summary><ul>${sources}</ul></details>` : '',
      '</div>',
    ].join('');
    item.querySelector('.mistake-head').addEventListener('click', (event) => {
      openMistake(event.currentTarget.getAttribute('aria-expanded') === 'true' ? -1 : index);
    });
    return item;
  }));
  openMistake(0);
}

function openMistake(index) {
  for (const [position, item] of [...$('mistakeList').children].entries()) {
    item.querySelector('.mistake-head').setAttribute('aria-expanded', String(position === index));
    item.querySelector('.mistake-panel').hidden = position !== index;
  }
}

/* ---------- база ---------- */

// мой результат по вопросу — по последнему ответу: класс метки, текст на ноутбуке и на телефоне
const MY_RESULTS = {
  wrong: ['bad', '✕ последний ответ — ошибка', '✕ ошибка'],
  right: ['ok', '✓ верно', '✓ верно'],
  new: ['none', 'ещё не отвечали', 'не отвечали'],
};

function myResult(record) {
  const entry = state.progress[record.id];
  return !entry?.completed ? 'new' : entry.lastCorrect === false ? 'wrong' : 'right';
}

/** Текст карточки с подсвеченными словами поиска. */
function marked(text) {
  return searchSegments(text, $('databaseSearch').value)
    .map((segment) => (segment.mark ? `<mark>${escapeHtml(segment.text)}</mark>` : escapeHtml(segment.text))).join('');
}

/** Текст для ноутбука и короткий для телефона — оба в разметке, виден один (wide-only / phone-only). */
const wideOrShort = (wide, short) => (wide === short ? escapeHtml(wide)
  : `<span class="wide-only">${escapeHtml(wide)}</span><span class="phone-only">${escapeHtml(short)}</span>`);

const databaseFiltered = () => Boolean($('databaseSearch').value.trim() || $('databaseTopic').value || $('databaseMine').value);

function filteredDatabaseRows() {
  const topic = $('databaseTopic').value;
  const mine = $('databaseMine').value;
  return QUESTION_BANK.filter((record) =>
    matchesDatabaseSearch(record, $('databaseSearch').value)
    && (!topic || record.topic === topic)
    && (!mine || myResult(record) === mine));
}

function appendDatabaseRows(rows) {
  for (const record of rows) {
    const article = document.createElement('article');
    article.className = 'row';
    const answered = record.options.find((option) => option.id === record.answer.optionId);
    const origin = recordOrigin(record);
    const appearances = record.occurrences.map(occurrenceLabel).join('; ') || (origin.isAddition ? origin.label : '');
    const sources = evidenceList(record.evidence);
    const disputed = record.answer.state === 'needs-review' || record.answer.state === 'conflict';
    const [kind, wide, short] = MY_RESULTS[myResult(record)];
    const shortTopic = TOPIC_SHORT[record.topic] || record.topic;
    const name = answerName(record);
    article.innerHTML = [
      '<div class="row-top">',
      `<span class="topic-line"><span class="topic-mark" lang="zh-Hans" aria-hidden="true">${topicMark(record.topic)}</span>`
        + `${wideOrShort(record.topic, shortTopic[0].toLocaleUpperCase('ru') + shortTopic.slice(1))}</span>`,
      `<span class="my ${kind}">${wideOrShort(wide, short)}</span>`,
      // проверенный ответ — норма; метка только у ответа, который ещё не перепроверен или спорен
      record.answer.state === 'verified' ? ''
        : `<span class="tag${disputed ? ' review' : ''}">${STATUS_NAMES[record.answer.state]}</span>`,
      hasOptionPool(record) ? '<span class="tag">варианты меняются</span>' : '',
      record.parseWarnings?.length ? `<span class="tag warn">${escapeHtml(record.parseWarnings.join('; '))}</span>` : '',
      '</div>',
      `<h3>${marked(record.questionRu)}</h3>`,
      record.questionZh ? `<p class="row-zh-question" lang="zh-Hans">${escapeHtml(record.questionZh)}</p>` : '',
      `<p class="row-options" lang="zh-Hans">${record.options.map((o) => marked(o.zh)).join(' · ')}</p>`,
      appearances ? `<p class="row-meta">${escapeHtml(appearances)}</p>` : '',
      answered || record.explanation.ru ? [
        '<details class="row-reveal"><summary>Показать ответ</summary><div class="row-panel">',
        answered ? `<p class="row-answer"><span>Ответ: <span class="zh" lang="zh-Hans">${escapeHtml(answered.zh)}</span>${
          name ? ` — ${escapeHtml(name)}` : ''}</span></p>` : '',
        record.explanation.ru ? `<p class="row-why">${marked(record.explanation.ru)}</p>` : '',
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

/** Раунд из найденного в базе: только эти вопросы, все сразу; режим и формат — с главной. */
const foundSettings = (rows) => ({
  filters: { ...defaultFilters(), mode: state.filters.mode, ids: rows.map((record) => record.id) },
  size: ALL_SIZE,
});

/** Строка над списком: сколько найдено и мои ответы на них; «Тренировать найденные» — главная
 * кнопка, когда поиск или фильтр что-то отобрали. */
function renderFound(rows) {
  const filtered = databaseFiltered();
  const tally = { wrong: 0, right: 0, new: 0 };
  for (const record of rows) tally[myResult(record)] += 1;
  const questions = pluralRu(rows.length, ['вопрос', 'вопроса', 'вопросов']);
  $('databaseFound').hidden = rows.length === 0;
  $('foundCount').textContent = filtered
    ? `${pluralRu(rows.length, ['Найден', 'Найдено', 'Найдено'])} ${rows.length} ${questions}`
    : `Все ${rows.length} ${questions}`;
  $('foundMine').textContent = `${tally.wrong} с ошибкой, ${tally.right} верно, ${tally.new} ещё не отвечали`;
  const trainable = eligible(QUESTION_BANK, foundSettings(rows).filters, state.progress).length;
  $('trainFound').hidden = !filtered;
  $('trainFound').disabled = trainable === 0;
  $('trainFound').classList.toggle('ink-btn--primary', trainable > 0);
  $('trainFound').classList.toggle('ink-btn--secondary', trainable === 0);
  $('trainFound').textContent = `Тренировать найденные (${trainable})`;
}

function renderDatabase(reset = true) {
  const rows = filteredDatabaseRows();
  if (reset) {
    state.databasePage = 0;
    $('databaseList').innerHTML = '';
    renderFound(rows);
  }
  if (!rows.length) {
    $('databaseList').innerHTML = '<p class="empty">Ничего не найдено.</p>';
    $('databaseMore').hidden = true;
    return;
  }
  appendDatabaseRows(databasePage(rows, state.databasePage, 50));
  state.databasePage += 1;
  const shown = Math.min(state.databasePage * 50, rows.length);
  $('databaseMore').hidden = shown >= rows.length;
  $('databaseMore').textContent = `Показать ещё (${rows.length - shown})`;
}

function openDatabase() {
  setAddress('#database', true);
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
  // открытое меню «Вид» Esc сначала закрывает — и в «Чэнъюй», поэтому до его клавиатуры
  if (event.key === 'Escape' && !$('viewMenu').hidden && onPhone()) {
    event.stopImmediatePropagation();
    setViewMenu(false);
    $('viewToggle').focus();
    return;
  }
  // у раздела «Чэнъюй» своя клавиатура (src/chengyu.ui.js)
  if (state.view.startsWith('cy-')) return;

  if (event.key === 'Escape') {
    if (typing) document.activeElement.blur();
    else if (state.view === 'quiz') leaveRound();
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

  // Enter на главной — главная кнопка её верха: начать раунд или продолжить незаконченный
  if (state.view === 'setup' && event.key === 'Enter' && !onControl) {
    const main = [$('firstStart'), $('startButton'), $('resumeButton')].find((button) => button.offsetParent);
    if (main && !main.disabled) {
      event.preventDefault();
      main.click();
    }
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
$('questionZhToggle').addEventListener('click', toggleQuestionZh);
$('viewToggle').addEventListener('click', () => setViewMenu($('viewMenu').hidden));
$('themeMenu').addEventListener('click', toggleTheme);
$('pinyinMenu').addEventListener('click', togglePinyin);
$('questionZhMenu').addEventListener('click', toggleQuestionZh);
$('questionZhReveal').addEventListener('click', () => {
  $('questionZh').classList.add('revealed');
  $('questionZhReveal').hidden = true;
  // кнопка исчезает — фокус переходит на открытый текст, а не теряется на <body>
  $('questionZh').focus();
});
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
for (const id of ['firstStart', 'startButton', 'barStart', 'resumeNew']) {
  $(id).addEventListener('click', () => startRound());
}
for (const id of ['quickMistakes', 'quickDue']) {
  $(id).addEventListener('click', () => startRound($(id).dataset.mode));
}
$('resumeButton').addEventListener('click', continueRound);
// «Настроить раунд» — к разделам 一–四, раскрыв первый; без записи #settings в адресе
$('settingsLink').addEventListener('click', (event) => {
  event.preventDefault();
  $('modeFold').open = true;
  $('settings').scrollIntoView({ behavior: scrollBehavior(), block: 'start' });
  $('modeFold').querySelector('summary').focus({ preventScroll: true });
});
$('repeatMistakes').addEventListener('click', repeatMistakes);
$('newRound').addEventListener('click', () => startRoundFrom(state.roundSettings, state.roundFormat));
$('nextButton').addEventListener('click', nextQuestion);
$('revealAnswer').addEventListener('click', revealAnswer);
$('showHint').addEventListener('click', showHint);
for (const button of $('recallRate').querySelectorAll('button')) {
  button.addEventListener('click', () => rateRecall(button.dataset.outcome));
}
$('tfTrue').addEventListener('click', () => answerTrueFalse(true));
$('tfFalse').addEventListener('click', () => answerTrueFalse(false));
$('leaveRound').addEventListener('click', leaveRound);
$('closeDatabase').addEventListener('click', backToSetup);
$('backToSetup').addEventListener('click', backToSetup);
$('databaseSearch').addEventListener('input', renderDatabase);
$('databaseTopic').addEventListener('change', renderDatabase);
$('databaseMine').addEventListener('change', renderDatabase);
$('trainFound').addEventListener('click', () => startRoundFrom(foundSettings(filteredDatabaseRows()), state.format));
$('databaseMore').addEventListener('click', () => renderDatabase(false));

for (const input of document.querySelectorAll('input[name="roundSize"]')) {
  input.addEventListener('change', (event) => {
    state.size = event.target.value === 'all' ? ALL_SIZE : Number(event.target.value);
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
for (const input of document.querySelectorAll('input[name="topicsBy"]')) {
  input.addEventListener('change', (event) => {
    // способ выбора один: переключение сбрасывает отметки обоих списков
    state.topicsBy = event.target.value;
    state.filters.topics = [];
    state.filters.dossiers = [];
    saveStudySettings();
    renderSetup();
  });
}
// кнопка стоит в «Темах раунда» и сбрасывает их фильтры; режим — отдельный раздел, его не трогает
$('clearFilters').addEventListener('click', () => {
  state.filters = { ...defaultFilters(), mode: state.filters.mode };
  saveStudySettings();
  renderSetup();
});
$('resetProgress').addEventListener('click', () => {
  if (!confirm('Сбросить прогресс по всем вопросам?')) return;
  state.progress = {};
  saveProgress();
  // плашка незаконченного раунда обещает, что его ответы сохранены, — после сброса это не так
  discardRound();
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
// шапка базы: на телефоне — короче
$('databaseCount').innerHTML = `${QUESTION_BANK.length} ${pluralRu(QUESTION_BANK.length, ['вопрос', 'вопроса', 'вопросов'])} с ответами`
  + '<span class="wide-only">, пояснениями и источниками</span><span class="phone-only"> и пояснениями</span>';

let startBarFrame = 0;
const scheduleStartBar = () => {
  if (!startBarFrame) {
    startBarFrame = requestAnimationFrame(() => {
      startBarFrame = 0;
      updateStartBar();
    });
  }
};
window.addEventListener('scroll', scheduleStartBar, { passive: true });
window.addEventListener('resize', scheduleStartBar);
window.visualViewport?.addEventListener('resize', scheduleStartBar);
window.addEventListener('popstate', route);

initTheme();
initPinyin();
initQuestionZh();
restoreRound();
renderSetup();
route();
