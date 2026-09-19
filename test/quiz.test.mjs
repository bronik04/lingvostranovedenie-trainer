import assert from 'node:assert/strict';
import test from 'node:test';
import { buildRound, eligible, grade, labelledOptions, scheduleReview } from '../src/quiz.mjs';

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
  onlyDue: false,
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

test('интервальное повторение: правильный ответ откладывает следующий показ дальше, неправильный — сбрасывает', () => {
  const now = 1_000_000_000_000;
  const DAY = 86_400_000;

  const afterFirstCorrect = scheduleReview(undefined, true, now);
  assert.equal(afterFirstCorrect.box, 1);
  assert.equal(afterFirstCorrect.dueAt, now + DAY);

  const afterSecondCorrect = scheduleReview(afterFirstCorrect, true, now);
  assert.equal(afterSecondCorrect.box, 2);
  assert.equal(afterSecondCorrect.dueAt, now + 3 * DAY);
  assert.ok(afterSecondCorrect.dueAt > afterFirstCorrect.dueAt, 'интервал растёт');

  const afterWrong = scheduleReview(afterSecondCorrect, false, now);
  assert.equal(afterWrong.box, 0);
  assert.equal(afterWrong.dueAt, now, 'ошибка — показать почти сразу, а не через 90 дней');
});

test('интервальное повторение: box не растёт бесконечно', () => {
  let state;
  for (let i = 0; i < 20; i += 1) state = scheduleReview(state, true, 0);
  const plateau = state.box;
  state = scheduleReview(state, true, 0);
  assert.equal(state.box, plateau, 'дальше уже некуда — упёрлись в потолок интервалов');
});

test('«пора повторить» пропускает вопросы, чей срок ещё не наступил, но включает никогда не отвеченные', () => {
  const bank = [record('a'), record('b'), record('c')];
  const now = 1_000_000_000_000;
  const progress = {
    a: { dueAt: now - 1000 },
    b: { dueAt: now + 999_999_999 },
  };
  assert.deepEqual(
    eligible(bank, { ...NO_FILTERS, onlyDue: true }, progress, now).map((r) => r.id),
    ['a', 'c'],
  );
});

test('раунд «пора повторить» сортирует по просрочке, а не перемешивает', () => {
  const bank = [record('a'), record('b'), record('c')];
  const now = 1000;
  const progress = { a: { dueAt: 500 }, b: { dueAt: 100 }, c: { dueAt: 900 } };
  const round = buildRound(bank, { ...NO_FILTERS, onlyDue: true }, progress, 10, () => 0.5, now);
  assert.deepEqual(round.map((r) => r.id), ['b', 'a', 'c']);
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
