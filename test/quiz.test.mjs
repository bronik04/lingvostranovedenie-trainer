import assert from 'node:assert/strict';
import test from 'node:test';
import { buildRound, eligible, grade, labelledOptions } from '../src/quiz.mjs';

const record = (id, overrides = {}) => ({
  id,
  topic: 'География и административное устройство',
  questionRu: 'Какой город является крупнейшим портовым городом Китая?',
  options: [
    { id: 'o1', zh: '广州' }, { id: 'o2', zh: '上海' },
    { id: 'o3', zh: '北京' }, { id: 'o4', zh: '西安' },
  ],
  occurrences: [{ year: '2015-16', stage: 'школьный', stageCode: 'shk', number: 56 }],
  answer: { optionId: 'o2', state: 'verified' },
  ...overrides,
});

const NO_FILTERS = {
  topics: [], years: [], stages: [], onlyUnfinished: false, onlyVerified: false, onlyMistakes: false,
};

test('метки идут A–D по видимому порядку при любом перемешивании', () => {
  const reversed = labelledOptions(record('a'), () => 0.99);
  assert.deepEqual(reversed.map((option) => option.label), ['A', 'B', 'C', 'D']);
  assert.equal(new Set(reversed.map((option) => option.optionId)).size, 4);
});

test('правильность считается по optionId, а не по букве', () => {
  const shuffled = labelledOptions(record('a'), () => 0.99);
  const correct = shuffled.find((option) => option.optionId === 'o2');
  assert.equal(grade(record('a'), correct.optionId).correct, true);
  assert.equal(grade(record('a'), 'o1').correct, false);
});

test('conflict и needs-review в раунд не попадают', () => {
  const bank = [
    record('a'),
    record('b', { answer: { optionId: null, state: 'conflict' } }),
    record('c', { answer: { optionId: null, state: 'needs-review' } }),
    record('d', { answer: { optionId: 'o1', state: 'unverified' } }),
  ];
  assert.deepEqual(eligible(bank, NO_FILTERS, {}).map((r) => r.id), ['a', 'd']);
});

test('«только проверенные» отсекает unverified', () => {
  const bank = [record('a'), record('d', { answer: { optionId: 'o1', state: 'unverified' } })];
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, onlyVerified: true }, {}).map((r) => r.id), ['a']);
});

test('«только непройденные» уважает прогресс', () => {
  const bank = [record('a'), record('b')];
  const progress = { a: { completed: true } };
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, onlyUnfinished: true }, progress).map((r) => r.id), ['b']);
});

test('«работа над ошибками» отбирает только вопросы, где в прошлый раз ошиблись', () => {
  const bank = [record('a'), record('b'), record('c')];
  const progress = {
    a: { completed: true, lastCorrect: false },
    b: { completed: true, lastCorrect: true },
  };
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, onlyMistakes: true }, progress).map((r) => r.id), ['a']);
});

test('фильтры по теме, году и этапу складываются', () => {
  const bank = [
    record('a'),
    record('b', { topic: 'Россия и межкультурный блок' }),
    record('c', { occurrences: [{ year: '2024-25', stage: 'региональный', stageCode: 'reg', number: 4 }] }),
  ];
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, topics: ['Россия и межкультурный блок'] }, {}).map((r) => r.id), ['b']);
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, years: ['2024-25'] }, {}).map((r) => r.id), ['c']);
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, stages: ['reg'] }, {}).map((r) => r.id), ['c']);
});

test('раунд не повторяет вопрос и не превышает подходящее множество', () => {
  const bank = [record('a'), record('b'), record('c')];
  const round = buildRound(bank, NO_FILTERS, {}, 10, () => 0.5);
  assert.equal(round.length, 3);
  assert.equal(new Set(round.map((r) => r.id)).size, 3);
});
