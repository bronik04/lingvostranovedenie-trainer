// Логика раздела «Чэнъюй» (src/chengyu.mjs): отбор заданий, раунд, буквы вариантов, оценка.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import {
  cyBuildRound, cyEligible, cyGrade, cyIsValidProgress, cyLabelledOptions, cyLatestOccurrence,
  cyMatchesSearch, cyNormaliseFilters, cyOccurrenceLabel, cyPrompt, cyRecordAnswer, cySummary,
} from '../src/chengyu.mjs';

const OLYMPIAD = JSON.parse(readFileSync(new URL('../data/chengyu/olympiad.json', import.meta.url), 'utf8'));

const record = (id, group, extra = {}) => ({
  id, kind: 'analog', chengyu: id.slice(3), pinyin: 'pīn yīn', group, answer: 'B',
  options: [{ id: 'A', text: 'один' }, { id: 'B', text: 'два' }, { id: 'C', text: 'три' }, { id: 'D', text: 'четыре' }],
  literal: 'буквально', meaning: 'смысл', trap: 'ловушка', ...extra,
});
const BANK = [record('cy-一二三四', 'work'), record('cy-五六七八', 'char'), record('cy-九十百千', 'work')];
const seeded = (seed = 1) => () => {
  seed = (seed * 16807) % 2147483647;
  return (seed - 1) / 2147483646;
};

test('наборы: все, новые и ошибки', () => {
  const progress = {
    'cy-一二三四': { attempts: 1, correct: 1, lastCorrect: true },
    'cy-五六七八': { attempts: 2, correct: 1, lastCorrect: false },
  };
  const ids = (mode, groups = []) => cyEligible(BANK, { mode, groups }, progress).map((r) => r.id);
  assert.deepEqual(ids('all'), ['cy-一二三四', 'cy-五六七八', 'cy-九十百千']);
  assert.deepEqual(ids('new'), ['cy-九十百千']);
  assert.deepEqual(ids('mistakes'), ['cy-五六七八']);
  assert.deepEqual(ids('all', ['work']), ['cy-一二三四', 'cy-九十百千']);
});

test('раунд не длиннее выбранного и без повторов', () => {
  const round = cyBuildRound(BANK, { mode: 'all', groups: [] }, {}, 2, seeded(3));
  assert.equal(round.length, 2);
  assert.equal(new Set(round.map((r) => r.id)).size, 2);
  assert.equal(cyBuildRound(BANK, { mode: 'all', groups: [] }, {}, 99).length, 3);
});

test('буквы — по видимому порядку, id варианта — буква бланка', () => {
  const shown = cyLabelledOptions(BANK[0], seeded(7));
  assert.deepEqual(shown.map((o) => o.label), ['A', 'B', 'C', 'D']);
  assert.deepEqual(shown.map((o) => o.optionId).sort(), ['A', 'B', 'C', 'D']);
  for (const option of shown) {
    assert.equal(option.text, BANK[0].options.find((o) => o.id === option.optionId).text);
  }
});

test('оценка и запись прогресса', () => {
  assert.deepEqual(cyGrade(BANK[0], 'B'), { correct: true, answerOptionId: 'B' });
  assert.equal(cyGrade(BANK[0], 'A').correct, false);
  const first = cyRecordAnswer(undefined, false);
  assert.deepEqual(first, { attempts: 1, correct: 0, lastCorrect: false });
  assert.deepEqual(cyRecordAnswer(first, true), { attempts: 2, correct: 1, lastCorrect: true });
  assert.equal(cyIsValidProgress({ x: first }), true);
  assert.equal(cyIsValidProgress({ x: { attempts: 1 } }), false);
  assert.equal(cyIsValidProgress([]), false);
});

test('настройки из хранилища: мусор заменяется значениями по умолчанию', () => {
  assert.deepEqual(cyNormaliseFilters({ mode: 'всё', groups: ['work', 'нет такой', 'work'] }),
    { mode: 'all', groups: ['work'] });
  assert.deepEqual(cyNormaliseFilters(null), { mode: 'all', groups: [] });
});

test('поиск: иероглифы, пиньинь без тонов, русские слова, ё как е', () => {
  const sample = record('cy-一二三四', 'work', { pinyin: 'bēi gōng', meaning: 'страх, выдуманный самим' });
  assert.equal(cyMatchesSearch(sample, '二三'), true);
  assert.equal(cyMatchesSearch(sample, 'bei gong'), true);
  assert.equal(cyMatchesSearch(sample, 'ЧЕТЫРЕ'), true);
  assert.equal(cyMatchesSearch(sample, 'выдуманныи'), false);
  assert.equal(cyMatchesSearch(sample, 'самим'), true);
});

test('подпись появления на олимпиаде и самое свежее появление', () => {
  const repeated = OLYMPIAD.find((r) => r.occurrences.length > 1);
  const latest = cyLatestOccurrence(repeated);
  assert.ok(repeated.occurrences.every((o) => o.year <= latest.year));
  assert.equal(cyOccurrenceLabel({ year: '2022-23', stageCode: 'zak', number: 10 }),
    'ВсОШ 2022/23 · заключительный этап · задание 10');
  assert.equal(cyLatestOccurrence({}), null);
});

test('настоящие данные: формулировки задания и сводка', () => {
  const kinds = new Set(OLYMPIAD.map((r) => r.kind));
  assert.deepEqual([...kinds].sort(), ['analog', 'odd', 'reverse']);
  for (const item of OLYMPIAD) assert.ok(cyPrompt(item));
  const summary = cySummary(OLYMPIAD);
  assert.equal(summary.total, 35);
  assert.equal(summary.groups, 8);
  assert.equal(summary.seasons, 8);
});
