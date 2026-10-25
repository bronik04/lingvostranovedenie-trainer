import assert from 'node:assert/strict';
import test from 'node:test';
import * as quiz from '../src/quiz.mjs';
import {
  buildRound, eligible, escapeHtml, grade, hasOptionPool, isValidProgress, labelledOptions,
  matchesDatabaseSearch, matchingOccurrence, migrateProgress, recordOrigin, safeSourceUrl, scheduleReview,
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

const POOLED_OPTIONS = ['孙子兵法', '本草纲目', '西游记', '论语', '红楼梦', '水浒传', '阿Q正传']
  .map((zh, index) => ({ id: `o${index + 1}`, zh }));
const pooled = (overrides = {}) => record('pool', {
  options: POOLED_OPTIONS, answer: { optionId: 'o1', state: 'verified' }, ...overrides,
});

function seeded(seed = 1) {
  let value = seed;
  return () => ((value = (value * 16807) % 2147483647) - 1) / 2147483646;
}

test('у вопроса с общим набором на экране четыре варианта, правильный всегда среди них', () => {
  const random = seeded();
  const seen = new Set();
  for (let index = 0; index < 300; index += 1) {
    const shown = labelledOptions(pooled(), random);
    assert.deepEqual(shown.map((option) => option.label), ['A', 'B', 'C', 'D']);
    assert.equal(new Set(shown.map((option) => option.optionId)).size, 4);
    assert.ok(shown.some((option) => option.optionId === 'o1'));
    assert.equal(grade(pooled(), 'o1').correct, true);
    shown.forEach((option) => seen.add(option.optionId));
  }
  assert.equal(seen.size, POOLED_OPTIONS.length, 'каждый неверный вариант хоть раз попадает на экран');
});

test('без правильного варианта вопрос с общим набором показывает первые четыре', () => {
  const shown = labelledOptions(pooled({ answer: { optionId: null, state: 'needs-review' } }), () => 0);
  assert.equal(shown.length, 4);
  assert.deepEqual(shown.map((option) => option.optionId).sort(), ['o1', 'o2', 'o3', 'o4']);
});

test('общий набор отличается от обычных четырёх вариантов', () => {
  assert.equal(hasOptionPool(pooled()), true);
  assert.equal(hasOptionPool(record('a')), false);
});

test('поиск в базе находит вопрос по варианту из общего набора', () => {
  assert.equal(matchesDatabaseSearch(pooled(), '阿Q正传'), true);
});

test('прогресс нескольких влитых записей сходится в одну', () => {
  const bank = [record('kept', { mergedIds: ['gone-1', 'gone-2'] })];
  const item = { attempts: 1, correct: 1, completed: true, lastCorrect: true, box: 2, dueAt: 5 };
  const migrated = migrateProgress(bank, { 'gone-1': item, 'gone-2': { ...item, correct: 0, lastCorrect: false, box: 0, dueAt: 1 } });
  assert.deepEqual(Object.keys(migrated), ['kept']);
  assert.equal(migrated.kept.attempts, 2);
  assert.equal(migrated.kept.lastCorrect, false);
  assert.equal(migrated.kept.box, 0);
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

test('счётчик темы не считает вопрос без установленного ответа: в раунд он не попадёт', () => {
  const bank = [record('a'), record('b', { answer: { optionId: null, state: 'needs-review' } })];
  assert.deepEqual(quiz.progressByTopic(bank, {}), {
    'География и административное устройство': { completed: 0, total: 1 },
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

test('поиск базы — с начала слова: «чай» находит «чая» и «чаем», но не «величайший» и «случай»', () => {
  const item = (questionRu) => record('a', { questionRu, explanation: { ru: '' } });
  for (const text of ['Какой чай не является китайским?', 'К какому виду чая относится пуэр?',
    'Каким чаем славится Чжэцзян?', 'Кто открыл первый чайный дом?']) {
    assert.equal(quiz.matchesDatabaseSearch(item(text), 'чай'), true, text);
  }
  for (const text of ['Кто величайший поэт Тан?', 'В каком случае дарят часы?', 'Сколько длится час?']) {
    assert.equal(quiz.matchesDatabaseSearch(item(text), 'чай'), false, text);
  }
  // окончание запроса тоже отбрасывается, «ё» — как «е»
  assert.equal(quiz.matchesDatabaseSearch(item('Какой чай не является китайским?'), 'чаем'), true);
  assert.equal(quiz.matchesDatabaseSearch(item('Чем знаменит Пекин?'), 'пекине'), true);
  assert.equal(quiz.matchesDatabaseSearch(item('Как зовут ёжика?'), 'ежик'), true);
  // несколько слов — каждое где-то в тексте
  assert.equal(quiz.matchesDatabaseSearch(item('Каким чаем славится Чжэцзян?'), 'чжэцзян чай'), true);
  assert.equal(quiz.matchesDatabaseSearch(item('Каким чаем славится Чжэцзян?'), 'чай фуцзянь'), false);
  // имена и понятия в русской записи не теряют гласную: «мао» не находит «мая», «дао» — «дай»
  assert.equal(quiz.matchesDatabaseSearch(item('Что произошло 4 мая 1919 года?'), 'мао'), false);
  assert.equal(quiz.matchesDatabaseSearch(item('Кто такой Мао Цзэдун?'), 'мао'), true);
  assert.equal(quiz.matchesDatabaseSearch(item('Дай ответ'), 'дао'), false);
  // китайский — куском текста
  assert.equal(quiz.matchesDatabaseSearch(record('a', { options: [{ id: 'o1', zh: '龙井茶' }] }), '井茶'), true);
});

test('найденное слово подсвечивается целиком, китайское — куском', () => {
  assert.deepEqual(quiz.searchSegments('Величайший случай: каким чаем славится?', 'чай'), [
    { text: 'Величайший случай: каким ' }, { text: 'чаем', mark: true }, { text: ' славится?' },
  ]);
  assert.deepEqual(quiz.searchSegments('红茶 · 龙井茶', '龙井'), [
    { text: '红茶 · ' }, { text: '龙井', mark: true }, { text: '茶' },
  ]);
  assert.deepEqual(quiz.searchSegments('Без поиска', ''), [{ text: 'Без поиска' }]);
});

test('русское название верного ответа — из подписи ячейки досье, до первого тире', () => {
  assert.equal(quiz.answerName(record('a', { answer: { optionId: 'o2', state: 'verified', gloss: 'Пещеры Могао' } })), 'Пещеры Могао');
  assert.equal(quiz.answerName(record('a', { answer: { optionId: 'o2', state: 'verified', gloss: 'Чжан Имоу — кинорежиссёр' } })),
    'Чжан Имоу');
  assert.equal(quiz.answerName(record('a')), '');
  // запятая перед тире в подписи ячейки к названию не прилипает
  assert.equal(quiz.answerName(record('a', { answer: { optionId: 'o2', state: 'verified',
    gloss: 'Солёно-свежий вкус, подчёркивающий вкус продуктов, — шаньдунская кухня' } })),
  'Солёно-свежий вкус, подчёркивающий вкус продуктов');
  // поиск находит вопрос и по названию ответа
  assert.equal(quiz.matchesDatabaseSearch(record('a', { answer: { optionId: 'o2', state: 'verified', gloss: 'Пещеры Могао' } }), 'могао'), true);
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
      topics: [], dossiers: [], years: ['2015-16'], stages: ['shk'], mode: 'due', onlyVerified: true, origin: 'all',
    },
    size: 20,
    format: 'choice',
    topicsBy: 'sections',
  });
  assert.deepEqual(quiz.normaliseStudySettings({
    filters: { topics: 'не массив', years: [], stages: [], mode: 'не режим', onlyVerified: 'да', origin: 'всё' },
    size: 99,
  }, bank), {
    filters: { topics: [], dossiers: [], years: [], stages: [], mode: 'all', onlyVerified: false, origin: 'all' },
    size: 10,
    format: 'choice',
    topicsBy: 'sections',
  });
});

test('подборки: досье банка, сохраняются вместе с настройками, способ выбора тем один', () => {
  const bank = [
    record('a', { dossier: 'cuisine' }),
    record('b', { dossier: 'holidays', topic: 'Культура, традиции и праздники' }),
    record('c'),
  ];
  const settings = (value) => quiz.normaliseStudySettings({ filters: { ...NO_FILTERS, ...value.filters }, size: 10, ...value }, bank);
  const bySets = settings({ topicsBy: 'dossiers', filters: { dossiers: ['cuisine', 'нет такого'], topics: ['География и административное устройство'] } });
  assert.equal(bySets.topicsBy, 'dossiers');
  assert.deepEqual(bySets.filters.dossiers, ['cuisine']);
  // разделы и подборки сразу не отмечаются: остаётся выбор того способа, который включён
  assert.deepEqual(bySets.filters.topics, []);
  const bySections = settings({ filters: { dossiers: ['cuisine'], topics: ['География и административное устройство'] } });
  assert.equal(bySections.topicsBy, 'sections');
  assert.deepEqual(bySections.filters.dossiers, []);
  assert.equal(settings({ topicsBy: 'всё' }).topicsBy, 'sections');
  const ids = (filters) => quiz.eligible(bank, { ...NO_FILTERS, ...filters }, {}).map((item) => item.id);
  assert.deepEqual(ids({ dossiers: ['cuisine', 'holidays'] }), ['a', 'b']);
  // старые настройки без поля — все вопросы
  assert.deepEqual(ids({ dossiers: undefined }), ['a', 'b', 'c']);
  assert.deepEqual(quiz.progressByDossier(bank, { a: { completed: true } }),
    { cuisine: { completed: 1, total: 1 }, holidays: { completed: 0, total: 1 } });
});

test('раунд из найденного в базе: только эти вопросы', () => {
  const bank = [record('a'), record('b'), record('c')];
  assert.deepEqual(quiz.eligible(bank, { ...NO_FILTERS, ids: ['c', 'a'] }, {}).map((item) => item.id), ['a', 'c']);
  assert.deepEqual(quiz.eligible(bank, { ...NO_FILTERS, ids: [] }, {}), []);
});

test('ошибка возвращается после пяти следующих карточек', () => {
  // ошибка на позиции 2: между ней и повтором карточки 3–7, повтор встаёт на позицию 8
  const { queue } = quiz.queueRetry([], new Set(), record('a'), 2);
  assert.equal(quiz.nextRetryInsertion(queue, 7, 20), -1);
  assert.equal(quiz.nextRetryInsertion(queue, 8, 20), 0);
});

test('повтор ошибки в раунде узнаётся по тому, что вопрос уже был раньше', () => {
  const round = [record('a'), record('b'), record('c'), record('b')];
  assert.deepEqual(round.map((_, index) => quiz.isRepeatInRound(round, index)), [false, false, false, true]);
});

test('ошибка в конце раунда возвращается до итогов', () => {
  const queue = [{ record: record('a'), afterPosition: 8 }];
  assert.equal(quiz.nextRetryInsertion(queue, 5, 5), 0);
});

test('повтор не добавляется второй раз', () => {
  const first = quiz.queueRetry([], new Set(), record('a'), 0);
  const second = quiz.queueRetry(first.queue, first.retriedIds, record('a'), 5);
  assert.equal(second.queue.length, 1);
  assert.equal(second.queue[0].afterPosition, 6);
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

test('подвал считает вопросы, дополнения, сезоны и темы по банку', () => {
  const bank = [
    record('a', { occurrences: [{ year: '2015-16', stageCode: 'shk' }, { year: '2016-17', stageCode: 'mun' }] }),
    record('b', { topic: 'История и государство', occurrences: [{ year: '2025-26', stageCode: 'reg' }] }),
    record('c', { origin: 'addition', occurrences: [] }),
  ];
  assert.equal(quiz.bankSummary(bank),
    'В базе 3 вопроса: 2 из заданий ВсОШ за 3 сезона (2015/16—2025/26) и 1 проверенное дополнение к ним, 2 темы. '
    + 'У каждого ответа есть пояснение и ссылка на источник.');
});

test('подвал не говорит о непроверенных ответах, когда их нет, и называет их, когда есть', () => {
  const verified = [record('a'), record('b')];
  assert.doesNotMatch(quiz.bankSummary(verified), /остальные|перепроверки/);
  const mixed = [record('a'), record('b', { answer: { optionId: 'o2', state: 'unverified' } })];
  assert.match(quiz.bankSummary(mixed), /^В базе 2 вопроса из заданий ВсОШ за 1 сезон \(2015\/16\), 1 тема\. У 1 ответа есть пояснение/);
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

const progressItem = (overrides = {}) => ({
  attempts: 2, correct: 1, completed: true, lastCorrect: true, box: 2, dueAt: 5_000, ...overrides,
});

test('раунд берёт из группы «один факт» одну запись', () => {
  const bank = [
    record('a', { factGroup: 'g' }), record('b', { factGroup: 'g' }),
    record('c'), record('d'),
  ];
  for (const random of [() => 0, () => 0.5, () => 0.99]) {
    const round = buildRound(bank, NO_FILTERS, {}, 3, random);
    assert.equal(round.length, 3);
    assert.equal(round.filter((r) => r.factGroup === 'g').length, 1, round.map((r) => r.id).join());
  }
});

test('раунд берёт из вопросов об одной строке досье одну запись', () => {
  const bank = [record('a', { factRow: 'p/t/r1' }), record('b', { factRow: 'p/t/r1' }), record('c'), record('d')];
  for (const random of [() => 0, () => 0.5, () => 0.99]) {
    const round = buildRound(bank, NO_FILTERS, {}, 3, random);
    assert.equal(round.filter((r) => r.factRow === 'p/t/r1').length, 1, round.map((r) => r.id).join());
  }
});

test('запись, привязанная к нескольким строкам досье, не встаёт рядом с вопросом ни об одной из них', () => {
  const bank = [record('a', { factRow: ['p/t/r1', 'p/t/r2'] }), record('b', { factRow: 'p/t/r1' }),
    record('c', { factRow: 'p/t/r2' }), record('d'), record('e')];
  for (const random of [() => 0, () => 0.5, () => 0.99]) {
    const ids = buildRound(bank, NO_FILTERS, {}, 3, random).map((r) => r.id);
    assert.ok(!(ids.includes('a') && (ids.includes('b') || ids.includes('c'))), ids.join());
  }
});

test('в раунде никакие две записи не делят ни строку досье, ни группу фактов', () => {
  // a и b — одна строка, b и c — одна группа; a и c вместе допустимы: общего факта у них нет
  const bank = [record('a', { factRow: 'p/t/r1' }), record('b', { factRow: 'p/t/r1', factGroup: 'g' }),
    record('c', { factGroup: 'g' }), record('d'), record('e')];
  const keys = (r) => [r.factRow && `r:${r.factRow}`, r.factGroup && `g:${r.factGroup}`].filter(Boolean);
  for (const random of [() => 0, () => 0.5, () => 0.99]) {
    const round = buildRound(bank, NO_FILTERS, {}, 3, random);
    const all = round.flatMap(keys);
    assert.equal(new Set(all).size, all.length, round.map((r) => r.id).join());
  }
});

test('двойник не пропадает, если других вопросов не хватает: он идёт в конец раунда', () => {
  const bank = [record('a', { factGroup: 'g' }), record('b', { factGroup: 'g' }), record('c')];
  // random = 0.99 оставляет порядок [a, b, c]: без отбора двойники стояли бы подряд в начале
  const round = buildRound(bank, NO_FILTERS, {}, 10, () => 0.99);
  assert.deepEqual(round.map((r) => r.id), ['a', 'c', 'b']);
});

test('«пора повторить» берёт из группы самую просроченную запись, вторая ждёт следующего раунда', () => {
  const bank = [record('a', { factGroup: 'g' }), record('b', { factGroup: 'g' }), record('c')];
  const progress = {
    a: progressItem({ dueAt: 100 }), b: progressItem({ dueAt: 200 }), c: progressItem({ dueAt: 300 }),
  };
  // без отбора по группам получилось бы [a, b]
  const round = buildRound(bank, { ...NO_FILTERS, mode: 'due' }, progress, 2, () => 0.5, 1_000);
  assert.deepEqual(round.map((r) => r.id), ['a', 'c']);
});

test('записи без группы раунд не трогает', () => {
  const bank = [record('a'), record('b'), record('c')];
  assert.equal(buildRound(bank, NO_FILTERS, {}, 3, () => 0.5).length, 3);
});

test('прогресс с влитой записи переезжает на оставшуюся', () => {
  const bank = [record('kept', { mergedIds: ['gone'] }), record('other')];
  const progress = { gone: progressItem(), other: progressItem({ box: 0 }) };
  const migrated = quiz.migrateProgress(bank, progress);
  assert.deepEqual(migrated, { kept: progressItem(), other: progressItem({ box: 0 }) });
  assert.equal(quiz.isValidProgress(migrated), true);
});

test('если ученик отвечал на обе записи, попытки складываются, а срок берётся осторожный', () => {
  const bank = [record('kept', { mergedIds: ['gone'] })];
  const migrated = quiz.migrateProgress(bank, {
    kept: progressItem({ attempts: 3, correct: 3, box: 3, dueAt: 9_000, lastCorrect: true }),
    gone: progressItem({ attempts: 2, correct: 0, box: 0, dueAt: 100, lastCorrect: false }),
  });
  assert.deepEqual(migrated.kept, {
    attempts: 5, correct: 3, completed: true, lastCorrect: false, box: 0, dueAt: 100,
  });
  assert.equal('gone' in migrated, false);
  assert.equal(quiz.isValidProgress(migrated), true);
});

test('осторожный вариант выбирается независимо от того, на какой записи «хуже»', () => {
  const bank = [record('kept', { mergedIds: ['gone'] })];
  const migrated = quiz.migrateProgress(bank, {
    kept: progressItem({ attempts: 2, correct: 0, box: 0, dueAt: 100, lastCorrect: false }),
    gone: progressItem({ attempts: 3, correct: 3, box: 3, dueAt: 9_000, lastCorrect: true }),
  });
  assert.deepEqual(migrated.kept, {
    attempts: 5, correct: 3, completed: true, lastCorrect: false, box: 0, dueAt: 100,
  });
  assert.equal(quiz.isValidProgress(migrated), true);
});

test('перенос прогресса не меняет исходный объект и повторный вызов ничего не портит', () => {
  const bank = [record('kept', { mergedIds: ['gone'] })];
  const progress = { gone: progressItem() };
  const once = quiz.migrateProgress(bank, progress);
  assert.deepEqual(Object.keys(progress), ['gone']);
  assert.deepEqual(quiz.migrateProgress(bank, once), once);
});

test('без влитых записей прогресс остаётся тем же объектом', () => {
  const progress = { a: progressItem() };
  assert.equal(quiz.migrateProgress([record('a')], progress), progress);
});

test('формат раунда хранится в настройках; неизвестный и отсутствующий — «выбор ответа»', () => {
  const bank = [record('a')];
  const filters = { topics: [], years: [], stages: [], mode: 'all', onlyVerified: false };
  assert.equal(quiz.normaliseStudySettings({ filters, size: 10, format: 'recall' }, bank).format, 'recall');
  assert.equal(quiz.normaliseStudySettings({ filters, size: 10, format: 'truefalse' }, bank).format, 'truefalse');
  assert.equal(quiz.normaliseStudySettings({ filters, size: 10 }, bank).format, 'choice');
  assert.equal(quiz.normaliseStudySettings({ filters, size: 10, format: 'blitz' }, bank).format, 'choice');
  assert.equal(quiz.normaliseStudySettings(null, bank).format, 'choice');
});

const NOW = 1_000_000_000_000;
const DAY = 86_400_000;

test('исход correct двигает коробку, wrong сбрасывает — как прежний ответ из четырёх', () => {
  const first = quiz.applyAnswer(undefined, 'correct', NOW);
  assert.deepEqual(first, { attempts: 1, correct: 1, completed: true, lastCorrect: true, box: 1, dueAt: NOW + DAY });
  assert.deepEqual(quiz.applyAnswer(first, 'wrong', NOW),
    { attempts: 2, correct: 1, completed: true, lastCorrect: false, box: 0, dueAt: NOW });
});

test('«вспомнил неточно» не поднимает коробку, но и не оставляет вопрос на сегодня', () => {
  assert.deepEqual(quiz.applyAnswer(undefined, 'partial', NOW),
    { attempts: 1, correct: 1, completed: true, lastCorrect: true, box: 1, dueAt: NOW + DAY });
  const learned = { attempts: 5, correct: 5, completed: true, lastCorrect: true, box: 4, dueAt: 0 };
  assert.deepEqual(quiz.applyAnswer(learned, 'partial', NOW),
    { attempts: 6, correct: 6, completed: true, lastCorrect: true, box: 4, dueAt: NOW + 16 * DAY });
  const afterMistake = { attempts: 2, correct: 1, completed: true, lastCorrect: false, box: 0, dueAt: 0 };
  assert.equal(quiz.applyAnswer(afterMistake, 'partial', NOW).box, 1);
});

test('верно в «Верно или нет» не сдвигает повторение и не выводит вопрос из «Ошибок»', () => {
  const mistake = { attempts: 1, correct: 0, completed: true, lastCorrect: false, box: 0, dueAt: 123 };
  assert.deepEqual(quiz.applyAnswer(mistake, 'checked', NOW),
    { attempts: 2, correct: 1, completed: true, lastCorrect: false, box: 0, dueAt: 123 });
  const learned = { attempts: 3, correct: 3, completed: true, lastCorrect: true, box: 3, dueAt: 999 };
  assert.deepEqual(quiz.applyAnswer(learned, 'checked', NOW),
    { attempts: 4, correct: 4, completed: true, lastCorrect: true, box: 3, dueAt: 999 });
  // новый вопрос считается пройденным и сразу ждёт настоящего повторения
  assert.deepEqual(quiz.applyAnswer(undefined, 'checked', NOW),
    { attempts: 1, correct: 1, completed: true, lastCorrect: true, box: 0, dueAt: NOW });
  assert.deepEqual(quiz.applyAnswer({ attempts: 0, correct: 0 }, 'checked', NOW),
    { attempts: 1, correct: 1, completed: true, lastCorrect: true, box: 0, dueAt: NOW });
});

test('любой исход даёт запись, которую принимает проверка прогресса', () => {
  const progress = Object.fromEntries(['correct', 'partial', 'wrong', 'checked']
    .map((outcome) => [outcome, quiz.applyAnswer(undefined, outcome, NOW)]));
  assert.equal(isValidProgress(progress), true);
});

test('неизвестный исход — ошибка программы, а не тихая порча прогресса', () => {
  assert.throws(() => quiz.applyAnswer(undefined, 'maybe', NOW), /исход/);
});

const sequence = (...values) => {
  let index = 0;
  return () => values[index++];
};

test('«верно или нет»: при random < ½ предлагается правильный вариант', () => {
  assert.deepEqual(quiz.trueFalseStatement(record('a'), sequence(0.1)),
    { optionId: 'o2', zh: '上海', isTrue: true });
});

test('«верно или нет»: иначе предлагается неверный вариант, и выпасть может любой', () => {
  const picked = [0, 0.34, 0.67, 0.99].map((x) => quiz.trueFalseStatement(record('a'), sequence(0.5, x)));
  assert.ok(picked.every((statement) => statement.isTrue === false && statement.optionId !== 'o2'));
  assert.deepEqual(new Set(picked.map((statement) => statement.optionId)), new Set(['o1', 'o3', 'o4']));
});

test('«верно или нет»: у записи с общим набором неверный берётся из всего набора', () => {
  const pooled = record('a', {
    options: [
      { id: 'o1', zh: '广州' }, { id: 'o2', zh: '上海' }, { id: 'o3', zh: '北京' },
      { id: 'o4', zh: '西安' }, { id: 'o5', zh: '天津' }, { id: 'o6', zh: '重庆' },
    ],
  });
  assert.deepEqual(quiz.trueFalseStatement(pooled, sequence(0.5, 0.99)),
    { optionId: 'o6', zh: '重庆', isTrue: false });
});

test('вопросы, на которые без вариантов не ответить, узнаются по формулировке', () => {
  const needs = (questionRu) => quiz.needsOptions(record('a', { questionRu }));
  assert.equal(needs('Что из перечисленного является специальным административным районом Китая?'), true);
  assert.equal(needs('Какой из нижеперечисленных городов Китая называют 泉城?'), true);
  assert.equal(needs('Какое животное не входит в китайский двенадцатилетний зодиак?'), true);
  assert.equal(needs('Какой город не относится к шести древним столицам Китая?'), true);
  assert.equal(needs('С какой страной не граничит КНР?'), true);
});

test('«не» в формулировке ещё не значит, что без вариантов не ответить', () => {
  const needs = (questionRu) => quiz.needsOptions(record('a', { questionRu }));
  assert.equal(needs('Как называлась самая ранняя династия Китая?'), false);
  assert.equal(needs('Обычай в день праздника Ханьши («праздник холодной пищи»), предшествующего Цинмину, '
    + 'не разводить огонь и есть только холодную пищу, по преданию установил Цзинь Вэнь-гун в память '
    + 'о своём верном спутнике. О ком идёт речь?'), false);
  assert.equal(needs('Какой денежный подарок делают не только на Праздник весны, но и на рождение ребёнка, '
    + 'новоселье и день рождения?'), false);
  assert.equal(needs('Какой праздник неразрывно связан с луной?'), false);
});

test('«верно или нет»: исключённый вариант не предлагается никогда', () => {
  const plateau = record('a', {
    options: [
      { id: 'o1', zh: '3000 米以上', trueFalse: false }, { id: 'o2', zh: '4500 米以上' },
      { id: 'o3', zh: '1500 米以上', trueFalse: false }, { id: 'o4', zh: '6000 米以上' },
    ],
  });
  const offered = [0, 0.34, 0.5, 0.67, 0.99].map((x) => quiz.trueFalseStatement(plateau, sequence(0.5, x)).optionId);
  assert.deepEqual(new Set(offered), new Set(['o4']));
  // правильный вариант исключением не затрагивается
  assert.equal(quiz.trueFalseStatement(plateau, sequence(0.1)).optionId, 'o2');
});

test('пиньинь: китайские вставки русского вопроса получают транскрипцию по таблице', () => {
  const table = { 双皮奶: 'shuāng pí nǎi', '亚历山大·涅夫斯基': 'yà lì shān dà·niè fū sī jī' };
  assert.deepEqual(quiz.pinyinSegments('Как выглядит десерт 双皮奶?', table), [
    { text: 'Как выглядит десерт ' }, { text: '双皮奶', pinyin: 'shuāng pí nǎi' }, { text: '?' },
  ]);
  // имя с «·» — одна вставка, как в scripts/pinyin.py
  assert.deepEqual(quiz.pinyinSegments('Кто такой 亚历山大·涅夫斯基', table), [
    { text: 'Кто такой ' }, { text: '亚历山大·涅夫斯基', pinyin: 'yà lì shān dà·niè fū sī jī' },
  ]);
  // нет записи в таблице — кусок остаётся без транскрипции; текст без иероглифов — один кусок
  assert.deepEqual(quiz.pinyinSegments('Что такое 糖葫芦', {}), [
    { text: 'Что такое ' }, { text: '糖葫芦', pinyin: undefined },
  ]);
  assert.deepEqual(quiz.pinyinSegments('Столица России?', table), [{ text: 'Столица России?' }]);
});

test('фильтр происхождения: только олимпиадные или только дополнения', () => {
  const bank = [record('olympiad'), record('addition', { origin: 'addition', occurrences: [] })];
  const ids = (origin) => quiz.eligible(bank, { ...NO_FILTERS, origin }, {}).map((item) => item.id);
  assert.deepEqual(ids('all'), ['olympiad', 'addition']);
  assert.deepEqual(ids('olympiad'), ['olympiad']);
  assert.deepEqual(ids('addition'), ['addition']);
  // старые сохранённые настройки без поля — как «все»
  assert.deepEqual(ids(undefined), ['olympiad', 'addition']);
  const kept = quiz.normaliseStudySettings({ filters: { ...NO_FILTERS, origin: 'addition' }, size: 10 }, bank);
  assert.equal(kept.filters.origin, 'addition');
});

test('пиньинь по иероглифам: слог над каждым знаком, «·» без слога, несовпадение — одной парой', () => {
  assert.deepEqual(quiz.rubyPairs('双皮奶', 'shuāng pí nǎi'), [
    { text: '双', pinyin: 'shuāng' }, { text: '皮', pinyin: 'pí' }, { text: '奶', pinyin: 'nǎi' },
  ]);
  assert.deepEqual(quiz.rubyPairs('伊万·希施金', 'yī wàn·xī shī jīn'), [
    { text: '伊', pinyin: 'yī' }, { text: '万', pinyin: 'wàn' }, { text: '·' },
    { text: '希', pinyin: 'xī' }, { text: '施', pinyin: 'shī' }, { text: '金', pinyin: 'jīn' },
  ]);
  assert.deepEqual(quiz.rubyPairs('坎儿井', 'kǎnr jǐng'), [{ text: '坎儿井', pinyin: 'kǎnr jǐng' }]);
});
