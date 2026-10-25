const PLAYABLE = new Set(['verified', 'unverified']);
const LABELS = ['A', 'B', 'C', 'D'];
const STUDY_MODES = new Set(['all', 'new', 'mistakes', 'due']);
// откуда вопросы раунда: все, только с олимпиад или только дополнения к ним
const ORIGINS = new Set(['all', 'olympiad', 'addition']);
const ROUND_SIZES = new Set([5, 10, 20, 50, Number.MAX_SAFE_INTEGER]);
export const FORMATS = new Set(['choice', 'recall', 'truefalse']);
const OUTCOMES = new Set(['correct', 'partial', 'wrong', 'checked']);

// Упрощённый вариант интервального повторения (Leitner-стиль): бокс растёт на
// верном ответе и сгорает до нуля на ошибке. Полноценный SM-2 со шкалой 0–5 не
// нужен: выбор из вариантов даёт только верно/неверно, а самооценка во «Вспомни
// сам» добавляет одну промежуточную ступень — «вспомнил неточно» (applyAnswer).
const REVIEW_INTERVALS_DAYS = [0, 1, 3, 7, 16, 35, 90];
const DAY_MS = 86_400_000;

function mergeProgress(kept, absorbed) {
  if (!kept) return absorbed;
  // отметки времени последнего ответа нет, поэтому при расхождении берём
  // осторожный вариант: повторить раньше и не считать ошибку исправленной
  return {
    attempts: kept.attempts + absorbed.attempts,
    correct: kept.correct + absorbed.correct,
    completed: true,
    lastCorrect: kept.lastCorrect && absorbed.lastCorrect,
    box: Math.min(kept.box, absorbed.box),
    dueAt: Math.min(kept.dueAt, absorbed.dueAt),
  };
}

// Записи, которые вошли в другую при склейке дублей, оставляют в `mergedIds` прежние
// id: прогресс, сохранённый под ними, переезжает на оставшуюся запись.
export function migrateProgress(bank, progress) {
  let migrated = progress;
  for (const record of bank) {
    for (const oldId of record.mergedIds ?? []) {
      if (!(oldId in migrated)) continue;
      const { [oldId]: absorbed, ...rest } = migrated;
      migrated = { ...rest, [record.id]: mergeProgress(rest[record.id], absorbed) };
    }
  }
  return migrated;
}

export function matchingOccurrence(record, filters) {
  return record.occurrences.find((occurrence) =>
    (!filters.years.length || filters.years.includes(occurrence.year))
    && (!filters.stages.length || filters.stages.includes(occurrence.stageCode)));
}

export function isValidProgress(progress) {
  if (!progress || typeof progress !== 'object' || Array.isArray(progress)) return false;
  return Object.values(progress).every((item) =>
    item && typeof item === 'object' && !Array.isArray(item)
    && Number.isInteger(item.attempts) && item.attempts >= 0
    && Number.isInteger(item.correct) && item.correct >= 0 && item.correct <= item.attempts
    && item.completed === true && typeof item.lastCorrect === 'boolean'
    && Number.isInteger(item.box) && item.box >= 0 && item.box < REVIEW_INTERVALS_DAYS.length
    && Number.isFinite(item.dueAt) && item.dueAt >= 0);
}

export function escapeHtml(value) {
  return String(value).replace(/[&<>\x22\x27]/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[character]);
}

export function safeSourceUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' || url.protocol === 'http:' ? url.href : null;
  } catch {
    return null;
  }
}

export function recordOrigin(record) {
  return record.origin === 'addition'
    ? { label: 'Дополнение к олимпиадной базе', isAddition: true }
    : { label: 'Олимпиадная база', isAddition: false };
}

export function matchesDatabaseSearch(record, query) {
  const needle = String(query ?? '').trim().toLocaleLowerCase('ru');
  if (!needle) return true;
  const right = record.options.find((option) => option.id === record.answer.optionId);
  const text = [
    record.questionRu,
    record.topic,
    ...record.options.map((option) => option.zh),
    right?.zh,
    record.explanation?.ru,
    ...record.options.map((option) => option.gloss),
  ].filter(Boolean).join(' ').toLocaleLowerCase('ru');
  return text.includes(needle);
}

export function normaliseStudySettings(value, bank) {
  const defaults = {
    filters: { topics: [], years: [], stages: [], mode: 'all', onlyVerified: false, origin: 'all' },
    size: 10,
    format: 'choice',
  };
  if (!value || typeof value !== 'object' || Array.isArray(value)) return defaults;

  const filters = value.filters;
  if (!filters || typeof filters !== 'object' || Array.isArray(filters)) return defaults;

  const topics = new Set(bank.map((record) => record.topic));
  const years = new Set(bank.flatMap((record) => record.occurrences.map((occurrence) => occurrence.year)));
  const stages = new Set(bank.flatMap((record) => record.occurrences.map((occurrence) => occurrence.stageCode)));
  const availableValues = (selected, available) => Array.isArray(selected)
    ? selected.filter((item) => available.has(item)) : [];

  return {
    filters: {
      topics: availableValues(filters.topics, topics),
      years: availableValues(filters.years, years),
      stages: availableValues(filters.stages, stages),
      mode: STUDY_MODES.has(filters.mode) ? filters.mode : defaults.filters.mode,
      onlyVerified: typeof filters.onlyVerified === 'boolean' ? filters.onlyVerified : false,
      origin: ORIGINS.has(filters.origin) ? filters.origin : defaults.filters.origin,
    },
    size: ROUND_SIZES.has(value.size) ? value.size : defaults.size,
    format: FORMATS.has(value.format) ? value.format : defaults.format,
  };
}

// между ошибкой и её повтором в раунде — столько других карточек
const RETRY_GAP = 5;

export function queueRetry(queue, retriedIds, record, position) {
  if (retriedIds.has(record.id)) return { queue, retriedIds };
  return {
    queue: [...queue, { record, afterPosition: position + RETRY_GAP + 1 }],
    retriedIds: new Set([...retriedIds, record.id]),
  };
}

export function nextRetryInsertion(queue, position, roundLength) {
  const dueIndex = queue.findIndex((entry) => entry.afterPosition <= position);
  if (dueIndex !== -1) return dueIndex;
  return position >= roundLength && queue.length ? 0 : -1;
}

export function isRepeatInRound(round, position) {
  const id = round[position]?.id;
  return round.slice(0, position).some((record) => record.id === id);
}

export function tallyAnswer(tally, recordId, correct) {
  // повтор ошибки в том же раунде нужен, чтобы закрепить ответ, а не чтобы
  // исправить счёт: засчитывается только первая попытка
  if (tally.wrongIds.includes(recordId)) return tally;
  return correct
    ? { ...tally, correct: tally.correct + 1 }
    : { ...tally, wrongIds: [...tally.wrongIds, recordId] };
}

export function roundScore(correct, initialRoundLength) {
  return `${correct} / ${initialRoundLength}`;
}

export function scheduleReview(previous, correct, now = Date.now()) {
  const box = correct ? Math.min((previous?.box ?? 0) + 1, REVIEW_INTERVALS_DAYS.length - 1) : 0;
  return { box, dueAt: now + REVIEW_INTERVALS_DAYS[box] * DAY_MS };
}

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

export function eligible(bank, filters, progress, now = Date.now()) {
  return bank.filter((record) => {
    if (!PLAYABLE.has(record.answer.state) || !record.answer.optionId) return false;
    if (filters.onlyVerified && record.answer.state !== 'verified') return false;
    if (filters.mode === 'new' && progress[record.id]?.completed) return false;
    if (filters.mode === 'mistakes' && progress[record.id]?.lastCorrect !== false) return false;
    if (filters.mode === 'due' && (!progress[record.id]?.completed || progress[record.id].dueAt > now)) return false;
    if (filters.topics.length && !filters.topics.includes(record.topic)) return false;
    const isAddition = record.origin === 'addition';
    if (filters.origin === 'olympiad' && isAddition) return false;
    if (filters.origin === 'addition' && !isAddition) return false;
    if (isAddition && (filters.years.length || filters.stages.length)) return false;
    if (!isAddition && !matchingOccurrence(record, filters)) return false;
    return true;
  });
}

export function progressByTopic(bank, progress) {
  const counts = {};
  for (const record of bank) {
    // вопрос без установленного ответа в раунд не попадает — и в счётчик темы тоже
    if (!PLAYABLE.has(record.answer.state) || !record.answer.optionId) continue;
    const topic = counts[record.topic] ?? { completed: 0, total: 0 };
    topic.total += 1;
    if (progress[record.id]?.completed) topic.completed += 1;
    counts[record.topic] = topic;
  }
  return counts;
}

export function wrongQuestions(round, wrongIds) {
  const wrong = new Set(wrongIds);
  const seen = new Set();
  return round.filter((record) => {
    if (!wrong.has(record.id) || seen.has(record.id)) return false;
    seen.add(record.id);
    return true;
  });
}

export function databasePage(records, page, size) {
  return records.slice(page * size, (page + 1) * size);
}

function shuffled(items, random) {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(random() * (index + 1));
    [copy[index], copy[swap]] = [copy[swap], copy[index]];
  }
  return copy;
}

// Из группы «один факт» и из вопросов об одной строке досье (разные стороны одного
// факта) в раунд берётся одна запись. Это предпочтение, а не запрет: если других
// вопросов не хватает до нужного размера, оставшиеся записи добираются в конец
// раунда, подальше от своих двойников.
function factKeys(record) {
  return [record.factGroup && `g:${record.factGroup}`, record.factRow && `r:${record.factRow}`].filter(Boolean);
}

function onePerFact(ordered, size) {
  const seen = new Set();
  const picked = [];
  const deferred = [];
  for (const record of ordered) {
    if (picked.length === size) break;
    const keys = factKeys(record);
    if (keys.some((key) => seen.has(key))) {
      deferred.push(record);
    } else {
      keys.forEach((key) => seen.add(key));
      picked.push(record);
    }
  }
  return [...picked, ...deferred.slice(0, size - picked.length)];
}

export function buildRound(bank, filters, progress, size, random = Math.random, now = Date.now()) {
  const pool = eligible(bank, filters, progress, now);
  if (filters.mode === 'due') {
    // тут важнее не разнообразие, а то, что самое просроченное идёт первым
    const byDueDate = [...pool].sort((a, b) => (progress[a.id]?.dueAt ?? 0) - (progress[b.id]?.dueAt ?? 0));
    return onePerFact(byDueDate, size);
  }
  return onePerFact(shuffled(pool, random), size);
}

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

export function grade(record, optionId) {
  return { correct: record.answer.optionId === optionId, answerOptionId: record.answer.optionId };
}

export function optionGlosses(record) {
  return record.options
    .filter((option) => option.id !== record.answer.optionId && option.gloss)
    .map((option) => ({ optionId: option.id, zh: option.zh, gloss: option.gloss }));
}

// «Верно или нет»: с вероятностью ½ — правильный вариант, иначе любой неверный,
// у записи с общим набором — из всего набора. Неверный, но верный как отдельное
// утверждение вариант («выше 3000 м» при ответе «выше 4500 м») помечен
// trueFalse: false (data/review/truefalse.json) и здесь не предлагается.
export function trueFalseStatement(record, random = Math.random) {
  const right = record.options.find((option) => option.id === record.answer.optionId);
  if (!right) throw new Error(`у вопроса нет правильного варианта: ${record.id}`);
  const isTrue = random() < 0.5;
  const wrong = record.options.filter((option) => option !== right && option.trueFalse !== false);
  const option = isTrue ? right : wrong[Math.floor(random() * wrong.length)];
  return { optionId: option.id, zh: option.zh, isTrue };
}

// Вопросы, на которые без вариантов не ответить: «Что из перечисленного…»,
// «Какое животное не входит в зодиак?». Правило по формулировке эвристическое:
// промах безвреден — ученик откроет варианты сам, лишний вопрос просто сразу
// покажет четыре варианта. В регулярках нет кавычек и двух косых подряд — их
// не поймёт минификатор сборки.
const LISTED_OPTIONS = /перечисленн|из следующих|из приведённых|из приведенных|из этих|из указанных/i;
const NEGATED_MEMBERSHIP = /(?<![а-яё])не\s+(является|являлся|являются|входит|входят|относится|относятся|был|была|было|были|граничит|принадлежит)(?![а-яё])/i;

export function needsOptions(record) {
  return LISTED_OPTIONS.test(record.questionRu) || NEGATED_MEMBERSHIP.test(record.questionRu);
}

// китайская вставка в русском вопросе: иероглифы, имена с «·» внутри. То же выражение —
// HAN_RUN в scripts/pinyin.py: таблица транскрипций собрана по тем же кускам текста
const HAN = '\\u3400-\\u4dbf\\u4e00-\\u9fff\\uf900-\\ufaff';
const HAN_RUN = new RegExp(`[${HAN}]+(?:[·・][${HAN}]+)*`, 'g');
const HAN_CHAR = new RegExp(`[${HAN}]`);

/** Вставка по иероглифам: слог над каждым знаком. Ruby на всю вставку не переносится и на
 * телефоне выталкивает длинное имя за край экрана, а по знакам строка переносится как обычно.
 * Если слогов не столько, сколько иероглифов, — одна пара на всю вставку. */
export function rubyPairs(text, pinyin) {
  const chars = [...text];
  const syllables = pinyin.split(/[\s·]+/).filter(Boolean);
  if (chars.filter((char) => HAN_CHAR.test(char)).length !== syllables.length) return [{ text, pinyin }];
  let index = 0;
  return chars.map((char) => (HAN_CHAR.test(char) ? { text: char, pinyin: syllables[index++] } : { text: char }));
}

/** Русский вопрос по кускам: у китайских вставок — транскрипция из таблицы (если есть). */
export function pinyinSegments(text, table) {
  const parts = [];
  let last = 0;
  for (const match of text.matchAll(HAN_RUN)) {
    if (match.index > last) parts.push({ text: text.slice(last, match.index) });
    parts.push({ text: match[0], pinyin: table[match[0]] });
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push({ text: text.slice(last) });
  return parts;
}

export function pluralRu(count, forms) {
  if (count % 10 === 1 && count % 100 !== 11) return forms[0];
  if (count % 10 >= 2 && count % 10 <= 4 && !(count % 100 >= 12 && count % 100 <= 14)) return forms[1];
  return forms[2];
}

// «В базе 1270 вопросов: 697 из заданий ВсОШ за 12 сезонов (2015/16—2026/27) и 573 проверенных
// дополнения к ним, 7 тем.» — числа считаются по банку, а не пишутся в разметку
export function bankSummary(bank) {
  const additions = bank.filter((record) => record.origin === 'addition').length;
  const olympiad = bank.length - additions;
  const years = [...new Set(bank.flatMap((record) => record.occurrences.map((o) => o.year)))].sort();
  const first = years[0]?.replace('-', '/');
  const last = years[years.length - 1]?.replace('-', '/');
  const seasons = years.length
    ? ` за ${years.length} ${pluralRu(years.length, ['сезон', 'сезона', 'сезонов'])} (${
      first === last ? first : `${first}—${last}`})`
    : '';
  const topics = new Set(bank.map((record) => record.topic)).size;
  const verified = bank.filter((record) => record.answer.state === 'verified').length;
  const questions = (count) => `${count} ${pluralRu(count, ['вопрос', 'вопроса', 'вопросов'])}`;
  const contents = additions
    ? `${questions(bank.length)}: ${olympiad} из заданий ВсОШ${seasons} и ${additions} ${pluralRu(additions,
      ['проверенное дополнение', 'проверенных дополнения', 'проверенных дополнений'])} к ним`
    : `${questions(olympiad)} из заданий ВсОШ${seasons}`;
  const sources = verified === bank.length
    ? 'У каждого ответа есть пояснение и ссылка на источник.'
    : `У ${verified} ${pluralRu(verified, ['ответа', 'ответов', 'ответов'])} есть пояснение и ссылка `
      + 'на источник; остальные ответы взяты из официального ключа и ждут перепроверки.';
  return `В базе ${contents}, ${topics} ${pluralRu(topics, ['тема', 'темы', 'тем'])}. ${sources}`;
}
