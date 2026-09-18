const PLAYABLE = new Set(['verified', 'unverified']);
const LABELS = ['A', 'B', 'C', 'D'];

export function eligible(bank, filters, progress) {
  return bank.filter((record) => {
    if (!PLAYABLE.has(record.answer.state) || !record.answer.optionId) return false;
    if (filters.onlyVerified && record.answer.state !== 'verified') return false;
    if (filters.onlyUnfinished && progress[record.id]?.completed) return false;
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

export function buildRound(bank, filters, progress, size, random = Math.random) {
  const pool = eligible(bank, filters, progress);
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
