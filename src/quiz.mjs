const PLAYABLE = new Set(['verified', 'unverified']);
const LABELS = ['A', 'B', 'C', 'D'];

// Упрощённый вариант интервального повторения (Leitner-стиль): бокс растёт на
// верном ответе и сгорает до нуля на ошибке. Полноценный SM-2 просит оценку
// «насколько легко вспомнилось» по шкале 0–5 — у нас есть только бинарный
// верно/неверно от клика по варианту, так что более тонкая шкала не даст
// дополнительного сигнала.
const REVIEW_INTERVALS_DAYS = [0, 1, 3, 7, 16, 35, 90];
const DAY_MS = 86_400_000;

export function scheduleReview(previous, correct, now = Date.now()) {
  const box = correct ? Math.min((previous?.box ?? 0) + 1, REVIEW_INTERVALS_DAYS.length - 1) : 0;
  return { box, dueAt: now + REVIEW_INTERVALS_DAYS[box] * DAY_MS };
}

export function eligible(bank, filters, progress, now = Date.now()) {
  return bank.filter((record) => {
    if (!PLAYABLE.has(record.answer.state) || !record.answer.optionId) return false;
    if (filters.onlyVerified && record.answer.state !== 'verified') return false;
    if (filters.onlyUnfinished && progress[record.id]?.completed) return false;
    if (filters.onlyMistakes && progress[record.id]?.lastCorrect !== false) return false;
    if (filters.onlyDue && (progress[record.id]?.dueAt ?? 0) > now) return false;
    if (filters.topics.length && !filters.topics.includes(record.topic)) return false;
    if (filters.years.length && !record.occurrences.some((o) => filters.years.includes(o.year))) return false;
    if (filters.stages.length && !record.occurrences.some((o) => filters.stages.includes(o.stageCode))) return false;
    return true;
  });
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
  if (filters.onlyDue) {
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
