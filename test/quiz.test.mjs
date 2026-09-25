import assert from 'node:assert/strict';
import test from 'node:test';
import * as quiz from '../src/quiz.mjs';
import {
  buildRound, eligible, escapeHtml, grade, isValidProgress, labelledOptions,
  matchingOccurrence, recordOrigin, safeSourceUrl, scheduleReview,
} from '../src/quiz.mjs';

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

test('происхождение отличает дополнение от олимпиадного вопроса', () => {
  assert.deepEqual(recordOrigin(record('olympiad')), { label: 'Олимпиадная база', isAddition: false });
  assert.deepEqual(recordOrigin(record('addition', { origin: 'addition' })), {
    label: 'Дополнение к олимпиадной базе', isAddition: true,
  });
});

const NO_FILTERS = {
  topics: [], years: [], stages: [], mode: 'all', onlyVerified: false,
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
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, mode: 'new' }, progress).map((r) => r.id), ['b']);
});

test('«работа над ошибками» отбирает только вопросы, где в прошлый раз ошиблись', () => {
  const bank = [record('a'), record('b'), record('c')];
  const progress = {
    a: { completed: true, lastCorrect: false },
    b: { completed: true, lastCorrect: true },
  };
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, mode: 'mistakes' }, progress).map((r) => r.id), ['a']);
});

test('режимы взаимоисключающие и продолжают учитывать тему', () => {
  const bank = [
    record('new'), record('wrong'), record('due'),
    record('other', { topic: 'История и государство' }),
  ];
  const now = 1000;
  const progress = {
    wrong: { completed: true, lastCorrect: false, dueAt: 900 },
    due: { completed: true, lastCorrect: true, dueAt: 900 },
  };
  const inTopic = { ...NO_FILTERS, topics: ['География и административное устройство'] };
  const ids = (mode) => eligible(bank, { ...inTopic, mode }, progress, now).map((item) => item.id);
  assert.deepEqual(ids('all'), ['new', 'wrong', 'due']);
  assert.deepEqual(ids('new'), ['new']);
  assert.deepEqual(ids('mistakes'), ['wrong']);
  assert.deepEqual(ids('due'), ['wrong', 'due']);
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

test('«пора повторить» берёт только пройденные вопросы с наступившим сроком', () => {
  const bank = [record('a'), record('b'), record('c')];
  const now = 1_000_000_000_000;
  const progress = {
    a: { completed: true, dueAt: now - 1000 },
    b: { completed: true, dueAt: now + 999_999_999 },
  };
  assert.deepEqual(
    eligible(bank, { ...NO_FILTERS, mode: 'due' }, progress, now).map((r) => r.id),
    ['a'],
  );
  assert.deepEqual(eligible(bank, { ...NO_FILTERS, mode: 'due' }, {}, now), []);
});

test('счётчики тем считают уникальные пройденные вопросы в каждой теме', () => {
  const bank = [record('a'), record('b'), record('c', { topic: 'История и государство' })];
  const counts = quiz.progressByTopic(bank, {
    a: { completed: true }, c: { completed: true }, extra: { completed: true },
  });
  assert.deepEqual(counts, {
    'География и административное устройство': { completed: 1, total: 2 },
    'История и государство': { completed: 1, total: 1 },
  });
});

test('повтор ошибок берёт вопросы только завершённого раунда и сохраняет порядок', () => {
  const round = [record('a'), record('b'), record('c')];
  assert.deepEqual(quiz.wrongQuestions(round, ['c', 'outside', 'a', 'a']).map((item) => item.id), ['a', 'c']);
});

test('повтор ошибок не дублирует вопрос, возвращённый внутри раунда', () => {
  const round = [record('a'), record('b'), record('a')];
  assert.deepEqual(quiz.wrongQuestions(round, ['a']).map((item) => item.id), ['a']);
});

test('страница базы возвращает ровно свой диапазон и последнюю короткую страницу', () => {
  const items = ['a', 'b', 'c', 'd', 'e'];
  assert.deepEqual(quiz.databasePage(items, 0, 2), ['a', 'b']);
  assert.deepEqual(quiz.databasePage(items, 1, 2), ['c', 'd']);
  assert.deepEqual(quiz.databasePage(items, 2, 2), ['e']);
  assert.deepEqual(quiz.databasePage(items, 3, 2), []);
});

test('раунд «пора повторить» сортирует по просрочке, а не перемешивает', () => {
  const bank = [record('a'), record('b'), record('c')];
  const now = 1000;
  const progress = {
    a: { completed: true, dueAt: 500 },
    b: { completed: true, dueAt: 100 },
    c: { completed: true, dueAt: 900 },
  };
  const round = buildRound(bank, { ...NO_FILTERS, mode: 'due' }, progress, 10, () => 0.5, now);
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

test('дополнение входит в обычный раунд, но не подменяет олимпийский фильтр', () => {
  const addition = record('addition', { origin: 'addition', occurrences: [] });
  assert.deepEqual(eligible([addition], NO_FILTERS, {}).map((item) => item.id), ['addition']);
  assert.deepEqual(
    eligible([addition], { ...NO_FILTERS, years: ['2015-16'] }, {}).map((item) => item.id),
    [],
  );
  assert.deepEqual(
    eligible([addition], { ...NO_FILTERS, stages: ['shk'] }, {}).map((item) => item.id),
    [],
  );
});

test('год и этап должны относиться к одному появлению вопроса', () => {
  const item = record('a', { occurrences: [
    { year: '2015-16', stageCode: 'reg' },
    { year: '2016-17', stageCode: 'mun' },
  ] });
  assert.deepEqual(eligible([item], { ...NO_FILTERS, years: ['2015-16'], stages: ['mun'] }, {}), []);
  assert.equal(matchingOccurrence(item, { ...NO_FILTERS, years: ['2016-17'], stages: ['mun'] })?.year, '2016-17');
});

test('прогресс с повреждённой записью отклоняется до сохранения', () => {
  assert.equal(isValidProgress({ a: null }), false);
  assert.equal(isValidProgress({ a: { attempts: 1, correct: 1, completed: true,
    lastCorrect: true, box: 1, dueAt: 1_000 } }), true);
});

test('поля источников не могут превратиться в HTML или исполняемую ссылку', () => {
  assert.equal(escapeHtml('<img src=x onerror="alert(1)">'), '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;');
  assert.equal(safeSourceUrl('javascript:alert(1)'), null);
  assert.equal(safeSourceUrl('https://example.org/source'), 'https://example.org/source');
});

test('раунд не повторяет вопрос и не превышает подходящее множество', () => {
  const bank = [record('a'), record('b'), record('c')];
  const round = buildRound(bank, NO_FILTERS, {}, 10, () => 0.5);
  assert.equal(round.length, 3);
  assert.equal(new Set(round.map((r) => r.id)).size, 3);
});

test('поиск базы проверяет вопрос, тему, варианты, ответ и пояснение', () => {
  const item = record('a', { explanation: { ru: 'Династия Ся была первой' } });
  assert.equal(quiz.matchesDatabaseSearch(item, 'крупнейшим портовым'), true);
  assert.equal(quiz.matchesDatabaseSearch(item, 'география'), true);
  assert.equal(quiz.matchesDatabaseSearch(item, '上海'), true);
  assert.equal(quiz.matchesDatabaseSearch(item, 'династия ся'), true);
  assert.equal(quiz.matchesDatabaseSearch(item, 'нет такого текста'), false);
  assert.equal(quiz.matchesDatabaseSearch(item, ''), true);
});

test('поиск базы находит и подписи к неверным вариантам', () => {
  const item = record('a', { options: [
    { id: 'o1', zh: '广州', gloss: 'Гуанчжоу, центр провинции Гуандун' },
    { id: 'o2', zh: '上海' }, { id: 'o3', zh: '北京' }, { id: 'o4', zh: '西安' },
  ] });
  assert.equal(quiz.matchesDatabaseSearch(item, 'центр провинции гуандун'), true);
});

test('настройки отбрасывают повреждённые и устаревшие значения', () => {
  const bank = [record('a')];
  assert.deepEqual(quiz.normaliseStudySettings({
    filters: {
      topics: ['нет темы'], years: ['2015-16'], stages: ['shk'], mode: 'due', onlyVerified: true,
    },
    size: 20,
  }, bank), {
    filters: {
      topics: [], years: ['2015-16'], stages: ['shk'], mode: 'due', onlyVerified: true,
    },
    size: 20,
  });
  assert.deepEqual(quiz.normaliseStudySettings({
    filters: { topics: 'не массив', years: [], stages: [], mode: 'не режим', onlyVerified: 'да' },
    size: 99,
  }, bank), {
    filters: { topics: [], years: [], stages: [], mode: 'all', onlyVerified: false },
    size: 10,
  });
});

test('ошибка возвращается после трёх следующих вопросов', () => {
  const queue = [{ record: record('a'), afterPosition: 4 }];
  assert.equal(quiz.nextRetryInsertion(queue, 3, 10), -1);
  assert.equal(quiz.nextRetryInsertion(queue, 4, 10), 0);
});

test('ошибка в конце раунда возвращается до итогов', () => {
  const queue = [{ record: record('a'), afterPosition: 8 }];
  assert.equal(quiz.nextRetryInsertion(queue, 5, 5), 0);
});

test('повтор не добавляется второй раз', () => {
  const first = quiz.queueRetry([], new Set(), record('a'), 0);
  const second = quiz.queueRetry(first.queue, first.retriedIds, record('a'), 5);
  assert.equal(second.queue.length, 1);
  assert.equal(second.queue[0].afterPosition, 4);
});

test('итог раунда не увеличивает число выбранных вопросов из-за повторов', () => {
  assert.equal(quiz.roundScore(10, 10), '10 / 10');
});

test('склонение по числу', () => {
  const forms = ['вопрос', 'вопроса', 'вопросов'];
  const cases = { 1: 'вопрос', 3: 'вопроса', 5: 'вопросов', 11: 'вопросов', 14: 'вопросов', 21: 'вопрос', 421: 'вопрос', 462: 'вопроса' };
  for (const [count, expected] of Object.entries(cases)) {
    assert.equal(quiz.pluralRu(Number(count), forms), expected, count);
  }
});

test('подвал считает вопросы, дополнения и годы по банку', () => {
  const bank = [
    record('a', { occurrences: [{ year: '2015-16', stageCode: 'shk' }] }),
    record('b', { occurrences: [{ year: '2025-26', stageCode: 'reg' }] }),
    record('c', { origin: 'addition', occurrences: [] }),
  ];
  assert.equal(quiz.bankSummary(bank),
    'В базе 2 вопроса из материалов ВсОШ 2015/16 — 2025/26 и 1 проверенное дополнение к ним. '
    + 'У каждого ответа есть пояснение и ссылка на источник.');
});

test('подвал не говорит о непроверенных ответах, когда их нет, и называет их, когда есть', () => {
  const verified = [record('a'), record('b')];
  assert.doesNotMatch(quiz.bankSummary(verified), /остальные|перепроверки/);
  const mixed = [record('a'), record('b', { answer: { optionId: 'o2', state: 'unverified' } })];
  assert.match(quiz.bankSummary(mixed), /^В базе 2 вопроса из материалов ВсОШ 2015\/16\. У 1 ответа есть пояснение/);
  assert.match(quiz.bankSummary(mixed), /остальные ответы взяты из официального ключа/);
});

test('повтор ошибки в том же раунде не меняет счёт', () => {
  let tally = { correct: 0, wrongIds: [] };
  tally = quiz.tallyAnswer(tally, 'a', true);
  tally = quiz.tallyAnswer(tally, 'b', false);
  assert.deepEqual(tally, { correct: 1, wrongIds: ['b'] });
  // повтор ошибки: и верный, и неверный ответ оставляют счёт и список ошибок как были
  assert.deepEqual(quiz.tallyAnswer(tally, 'b', true), tally);
  assert.deepEqual(quiz.tallyAnswer(tally, 'b', false), tally);
});

test('подписи берутся только у неверных вариантов, где они есть', () => {
  const withGlosses = record('g', {
    options: [
      { id: 'o1', zh: '广州', gloss: 'Гуанчжоу, центр провинции Гуандун' },
      { id: 'o2', zh: '上海', gloss: 'не должна показываться: это ответ' },
      { id: 'o3', zh: '北京' },
      { id: 'o4', zh: '西安', gloss: 'Сиань, древняя столица' },
    ],
  });
  assert.deepEqual(quiz.optionGlosses(withGlosses), [
    { optionId: 'o1', zh: '广州', gloss: 'Гуанчжоу, центр провинции Гуандун' },
    { optionId: 'o4', zh: '西安', gloss: 'Сиань, древняя столица' },
  ]);
  assert.deepEqual(quiz.optionGlosses(record('plain')), []);
});
