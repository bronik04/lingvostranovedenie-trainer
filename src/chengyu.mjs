/*
 * Раздел «Чэнъюй»: чистые функции раунда. Сборка встраивает файл в страницу без `export`,
 * поэтому имена с приставкой cy — чтобы не столкнуться с функциями quiz.mjs.
 */

export const CY_GROUPS = {
  work: 'Труд и старание',
  char: 'Характер и чувства',
  speech: 'Слово и речь',
  fable: 'Притчи и истории',
  luck: 'Удача и беда',
  measure: 'Сколько, как быстро, насколько похоже',
  mind: 'Знание и понимание',
  people: 'Люди вместе',
};

/** Знак темы — иероглиф, как у тем основного раздела. */
export const CY_GROUP_MARKS = {
  work: '勤', char: '性', speech: '言', fable: '寓',
  luck: '福', measure: '数', mind: '知', people: '众',
};

const CY_STAGES = {
  pri: 'пригласительный', shk: 'школьный', mun: 'муниципальный',
  reg: 'региональный', zak: 'заключительный',
};

// формулировки по умолчанию — для составленных заданий; у олимпиадных берётся
// формулировка бланка (instruction самого свежего появления)
const CY_PROMPTS = {
  analog: 'Подберите аналог фразеологизму в русском языке',
  reverse: 'Подберите аналог фразеологизму в китайском языке',
  odd: 'Укажите русский фразеологизм, не передающий значение приведенного китайского фразеологизма',
};

export function cyPrompt(record) {
  return cyLatestOccurrence(record)?.instruction || CY_PROMPTS[record.kind];
}

/** «ВсОШ 2022/23 · заключительный этап · задание 10» */
export function cyOccurrenceLabel(occurrence) {
  return `ВсОШ ${occurrence.year.replace('-', '/')} · ${CY_STAGES[occurrence.stageCode] || occurrence.stageCode} этап · задание ${occurrence.number}`;
}

/** Самое свежее появление задания на олимпиаде. */
export function cyLatestOccurrence(record) {
  const order = ['pri', 'shk', 'mun', 'reg', 'zak'];
  return [...(record.occurrences || [])].sort((a, b) =>
    b.year.localeCompare(a.year) || order.indexOf(b.stageCode) - order.indexOf(a.stageCode))[0] || null;
}

export function cyDefaultFilters() {
  return { mode: 'all', groups: [] };
}

/** Настройки из хранилища: неизвестные значения заменяются значениями по умолчанию. */
export function cyNormaliseFilters(value) {
  const filters = cyDefaultFilters();
  if (value && ['all', 'new', 'mistakes'].includes(value.mode)) filters.mode = value.mode;
  if (value && Array.isArray(value.groups)) {
    filters.groups = [...new Set(value.groups.filter((group) => group in CY_GROUPS))];
  }
  return filters;
}

export function cyIsValidProgress(progress) {
  return Boolean(progress) && typeof progress === 'object' && !Array.isArray(progress)
    && Object.values(progress).every((item) => item && typeof item === 'object'
      && Number.isInteger(item.attempts) && Number.isInteger(item.correct)
      && typeof item.lastCorrect === 'boolean');
}

export function cyEligible(bank, filters, progress) {
  return bank.filter((record) => {
    if (filters.groups.length && !filters.groups.includes(record.group)) return false;
    const item = progress[record.id];
    if (filters.mode === 'new') return !item;
    if (filters.mode === 'mistakes') return Boolean(item) && item.lastCorrect === false;
    return true;
  });
}

function cyShuffle(list, random) {
  const copy = [...list];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export function cyBuildRound(bank, filters, progress, size, random = Math.random) {
  return cyShuffle(cyEligible(bank, filters, progress), random).slice(0, size);
}

/** Варианты в случайном порядке; буквы A–D — по видимому порядку, а не по бланку. */
export function cyLabelledOptions(record, random = Math.random) {
  return cyShuffle(record.options, random).map((option, index) => ({
    optionId: option.id, label: 'ABCD'[index], text: option.text, gloss: option.gloss || '',
  }));
}

export function cyGrade(record, optionId) {
  return { correct: optionId === record.answer, answerOptionId: record.answer };
}

export function cyAnswerText(record) {
  return record.options.find((option) => option.id === record.answer).text;
}

export function cyRecordAnswer(previous, correct) {
  const item = previous || { attempts: 0, correct: 0 };
  return { attempts: item.attempts + 1, correct: item.correct + (correct ? 1 : 0), lastCorrect: correct };
}

/** Тоны снимаются только с латиницы (пиньинь): «й» не должна превращаться в «и». */
function cyNorm(value) {
  return String(value).normalize('NFD').replace(/([a-z])[̀-ͯ]+/gi, '$1').normalize('NFC')
    .toLowerCase().replace(/ё/g, 'е');
}

/** Поиск справочника: иероглифы, пиньинь без тонов, русские слова вариантов и разбора. */
export function cyMatchesSearch(record, query) {
  const needle = cyNorm(query.trim());
  if (!needle) return true;
  const haystack = [record.chengyu, record.pinyin, record.prompt || '', record.literal, record.meaning,
    record.trap, ...record.options.map((option) => option.text)].join(' ');
  return cyNorm(haystack).includes(needle);
}

export function cySummary(bank) {
  const seasons = new Set(bank.flatMap((record) => (record.occurrences || []).map((o) => o.year)));
  return {
    total: bank.length,
    olympiad: bank.filter((record) => record.occurrences?.length).length,
    seasons: seasons.size,
    groups: new Set(bank.map((r) => r.group)).size,
  };
}
