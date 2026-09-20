const PLAYABLE = new Set(['verified', 'unverified']);
const LABELS = ['A', 'B', 'C', 'D'];
const STUDY_MODES = new Set(['all', 'new', 'mistakes', 'due']);
const ROUND_SIZES = new Set([5, 10, 20, 50, Number.MAX_SAFE_INTEGER]);

// Упрощённый вариант интервального повторения (Leitner-стиль): бокс растёт на
// верном ответе и сгорает до нуля на ошибке. Полноценный SM-2 просит оценку
// «насколько легко вспомнилось» по шкале 0–5 — у нас есть только бинарный
// верно/неверно от клика по варианту, так что более тонкая шкала не даст
// дополнительного сигнала.
const REVIEW_INTERVALS_DAYS = [0, 1, 3, 7, 16, 35, 90];
const DAY_MS = 86_400_000;

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
  ].filter(Boolean).join(' ').toLocaleLowerCase('ru');
  return text.includes(needle);
}

export function normaliseStudySettings(value, bank) {
  const defaults = {
    filters: { topics: [], years: [], stages: [], mode: 'all', onlyVerified: false },
    size: 10,
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
    },
    size: ROUND_SIZES.has(value.size) ? value.size : defaults.size,
  };
}

export function queueRetry(queue, retriedIds, record, position) {
  if (retriedIds.has(record.id)) return { queue, retriedIds };
  return {
    queue: [...queue, { record, afterPosition: position + 4 }],
    retriedIds: new Set([...retriedIds, record.id]),
  };
}

export function nextRetryInsertion(queue, position, roundLength) {
  const dueIndex = queue.findIndex((entry) => entry.afterPosition <= position);
  if (dueIndex !== -1) return dueIndex;
  return position >= roundLength && queue.length ? 0 : -1;
}

export function scheduleReview(previous, correct, now = Date.now()) {
  const box = correct ? Math.min((previous?.box ?? 0) + 1, REVIEW_INTERVALS_DAYS.length - 1) : 0;
  return { box, dueAt: now + REVIEW_INTERVALS_DAYS[box] * DAY_MS };
}

export function eligible(bank, filters, progress, now = Date.now()) {
  return bank.filter((record) => {
    if (!PLAYABLE.has(record.answer.state) || !record.answer.optionId) return false;
    if (filters.onlyVerified && record.answer.state !== 'verified') return false;
    if (filters.mode === 'new' && progress[record.id]?.completed) return false;
    if (filters.mode === 'mistakes' && progress[record.id]?.lastCorrect !== false) return false;
    if (filters.mode === 'due' && (!progress[record.id]?.completed || progress[record.id].dueAt > now)) return false;
    if (filters.topics.length && !filters.topics.includes(record.topic)) return false;
    if (!matchingOccurrence(record, filters)) return false;
    return true;
  });
}

export function progressByTopic(bank, progress) {
  const counts = {};
  for (const record of bank) {
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

export function buildRound(bank, filters, progress, size, random = Math.random, now = Date.now()) {
  const pool = eligible(bank, filters, progress, now);
  if (filters.mode === 'due') {
    // тут важнее не разнообразие, а то, что самое просроченное идёт первым
    const byDueDate = [...pool].sort((a, b) => (progress[a.id]?.dueAt ?? 0) - (progress[b.id]?.dueAt ?? 0));
    return byDueDate.slice(0, Math.min(size, byDueDate.length));
  }
  return shuffled(pool, random).slice(0, Math.min(size, pool.length));
}

export function labelledOptions(record, random = Math.random) {
  return shuffled(record.options, random).map((option, index) => ({
    label: LABELS[index],
    optionId: option.id,
    zh: option.zh,
  }));
}

export function grade(record, optionId) {
  return { correct: record.answer.optionId === optionId, answerOptionId: record.answer.optionId };
}
