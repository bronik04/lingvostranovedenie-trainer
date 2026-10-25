// Смоук-тест интерфейса в настоящем браузере: собранный dist/ открывается в
// Chrome без окна, и по нему проходит ученик — раунд, ответы, итоги, база,
// фильтры, телефон. Логику раунда покрывает quiz.test.mjs; здесь проверяется,
// что её правильно подключает quiz.ui.js и что страница вообще работает.
//
// Нужны Google Chrome и `npm ci` (playwright-core без своего браузера). Локально
// без них тест пропускается, в CI (переменная CI) — падает.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { after, before, test } from 'node:test';
import { eligible } from '../src/quiz.mjs';

const HTML = new URL('../dist/lingvostranovedenie-trainer.html', import.meta.url);

let browser;
let server;
let baseUrl;
let skipReason = null;
// у node:test нет таймаута по умолчанию: зависший тест держал бы CI часами
const LIMIT = { timeout: 60_000 };
const ALL = { topics: [], years: [], stages: [], mode: 'all', onlyVerified: false };

before(async () => {
  try {
    const { chromium } = await import('playwright-core');
    browser = await chromium.launch({ channel: 'chrome', headless: true });
  } catch (error) {
    if (process.env.CI) throw error;
    skipReason = `нет Chrome или playwright-core (npm ci): ${error.message.split('\n')[0]}`;
    return;
  }
  const html = readFileSync(HTML);
  server = createServer((request, response) => {
    if (request.url === '/' || request.url.startsWith('/?')) {
      response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      response.end(html);
    } else {
      response.writeHead(404).end();
    }
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  baseUrl = `http://127.0.0.1:${server.address().port}/`;
});

after(async () => {
  await browser?.close();
  await new Promise((resolve) => (server ? server.close(resolve) : resolve()));
});

/** Свежая вкладка с пустым localStorage; ошибки страницы копятся в errors. Режим, формат и
 * темы на главной свёрнуты; тесты раскрывают их при каждой загрузке, а `folded` оставляет
 * как есть — для проверки самого сворачивания. */
async function openPage(t, viewport = { width: 1280, height: 900 }, { folded = false } = {}) {
  if (skipReason) {
    t.skip(skipReason);
    return null;
  }
  const context = await browser.newContext({ viewport });
  t.after(() => context.close());
  if (!folded) {
    await context.addInitScript(() => document.addEventListener('DOMContentLoaded', () => {
      for (const fold of document.querySelectorAll('.chapter-fold')) fold.open = true;
    }));
  }
  const page = await context.newPage();
  page.errors = [];
  page.on('pageerror', (error) => page.errors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') page.errors.push(message.text());
  });
  await page.goto(baseUrl);
  return page;
}

const bankOf = (page) => page.evaluate(() => QUESTION_BANK);

/** Запись банка для вопроса на экране. Сверяются и тексты, и id вариантов: в банке
 * есть записи с одним и тем же текстом вопроса, но разными вариантами. У вопроса с
 * общим набором неверных вариантов на экране только четыре из них, поэтому
 * показанные варианты должны входить в запись, а не совпадать с ней целиком. */
async function currentRecord(page, bank) {
  // innerText, а не textContent: скрытая транскрипция (настройка «Пиньинь» выключена) не текст вопроса
  const question = await page.locator('#questionText').innerText();
  const shown = await page.locator('#options button').evaluateAll((buttons) => buttons
    .map((b) => `${b.dataset.optionId}=${b.querySelector('span:nth-child(2)').innerText}`));
  const matches = bank.filter((r) => r.questionRu === question
    && shown.every((item) => r.options.some((o) => `${o.id}=${o.zh}` === item)));
  assert.equal(matches.length, 1, `вопрос на экране не определить однозначно: ${question}`);
  return matches[0];
}

async function answer(page, record, correct) {
  const shown = await page.locator('#options button')
    .evaluateAll((buttons) => buttons.map((b) => b.dataset.optionId));
  const optionId = correct
    ? record.answer.optionId
    : shown.find((id) => id !== record.answer.optionId);
  await page.locator(`#options button[data-option-id="${optionId}"]`).click();
  return optionId;
}

async function startRound(page, size) {
  await page.locator(`input[name="roundSize"][value="${size}"]`).check();
  await page.locator('#startButton').click();
  await page.locator('#quizView').waitFor();
}

test('главная открывается без ошибок и считает банк', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  assert.ok(bank.length > 400);
  assert.equal(await page.locator('#bankCount').textContent(), `Пройдено 0 из ${bank.length}`);
  assert.match(await page.locator('#footerNote').textContent(), /^В базе \d+ вопрос/);
  assert.equal(await page.locator('#startButton').isEnabled(), true);
  const description = await page.locator('meta[name="description"]').getAttribute('content');
  assert.ok(description.startsWith(`${bank.length} `), description);
  assert.deepEqual(page.errors, []);
});

test('раунд: верный и неверный ответ, повтор ошибки и честный итог', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  await startRound(page, 10);
  assert.equal(await page.locator('#progressLabel').textContent(), 'Вопрос 1 из 10');

  let wrongId = null;
  let wrongPick = null;
  let questions = 0;
  while (await page.locator('#quizView').isVisible()) {
    const record = await currentRecord(page, bank);
    questions += 1;
    assert.ok(questions <= 11, 'раунд не заканчивается');
    // ошибка на втором вопросе возвращается после пяти других карточек — восьмой
    const isRepeat = questions === 8;
    if (isRepeat) assert.equal(record.id, wrongId, 'восьмым должен вернуться ошибочный вопрос');
    assert.equal(await page.locator('#retryPill').isVisible(), isRepeat, `плашка «повтор ошибки» на вопросе ${questions}`);
    // ошибаемся ровно один раз — на втором вопросе; повтор этой ошибки отвечаем верно
    const correct = questions !== 2;
    const picked = await answer(page, record, correct);
    if (!correct) {
      wrongId = record.id;
      wrongPick = record.options.find((o) => o.id === picked).zh;
    }
    // ход раунда — кружки до конца раунда, хотя повтор ошибки удлиняет его до 11
    assert.equal(await page.locator('#progressSteps').isVisible(), true, `кружки хода на вопросе ${questions}`);
    assert.equal(await page.locator('#progressSteps li.ink-step--wrong').count(), questions >= 2 ? 1 : 0);
    assert.equal(await page.locator('#progressSteps li.ink-step--correct').count(), questions - (questions >= 2 ? 1 : 0));
    const feedback = page.locator('#feedback');
    assert.match(await feedback.getAttribute('class'), correct ? /\bgood\b/ : /\bbad\b/);
    assert.match(await feedback.textContent(), correct ? /^Верно/ : /^Неверно.*Правильный ответ/);
    await page.locator('#nextButton').click();
  }

  assert.equal(questions, 11, 'ошибочный вопрос должен вернуться в раунд один раз');
  await page.locator('#resultsView').waitFor();
  // повтор ошибки закрепляет ответ, но не исправляет счёт: из десяти вопросов верно девять
  assert.equal(await page.locator('#finalScore').textContent(), '9 / 10');
  assert.doesNotMatch(await page.locator('#resultText').textContent(), /без ошибок/);
  assert.equal(await page.locator('#repeatMistakes').textContent(), 'Повторить ошибки раунда (1)');
  // в итогах — ошибка с ответом ученика и верным ответом, и одна главная кнопка
  const wrongRecord = bank.find((r) => r.id === wrongId);
  const mistakes = page.locator('#mistakeList li');
  assert.equal(await mistakes.count(), 1);
  const mistake = await mistakes.first().textContent();
  assert.ok(mistake.includes(wrongRecord.questionRu), mistake);
  assert.ok(mistake.includes(`✕ ${wrongPick}`), mistake);
  const right = wrongRecord.options.find((o) => o.id === wrongRecord.answer.optionId).zh;
  assert.ok(mistake.includes(`✓ ${right}`), mistake);
  assert.equal(await page.locator('#resultsView .ink-btn--primary:visible').count(), 1);

  await page.locator('#repeatMistakes').click();
  assert.equal(await page.locator('#progressLabel').textContent(), 'Вопрос 1 из 1');
  assert.equal((await currentRecord(page, bank)).id, wrongId);
  assert.deepEqual(page.errors, []);
});

test('клавиатура: цифра отвечает, Enter ведёт дальше, Esc выходит', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await page.keyboard.press('Enter');
  await page.locator('#quizView').waitFor();
  await page.keyboard.press('Digit1');
  await page.locator('#nextButton:not(.hidden)').waitFor();
  assert.equal(await page.locator('#options button:not(:disabled)').count(), 0);
  await page.keyboard.press('Enter');
  assert.match(await page.locator('#progressLabel').textContent(), /^Вопрос 2 из/);
  await page.keyboard.press('Escape');
  await page.locator('#setupView').waitFor();
  assert.deepEqual(page.errors, []);
});

test('прогресс переживает перезагрузку, а режим «Ошибки» находит ошибку', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  await startRound(page, 5);
  await answer(page, await currentRecord(page, bank), false);
  await page.locator('#leaveRound').click();
  await page.reload();
  assert.equal(await page.locator('#bankCount').textContent(), `Пройдено 1 из ${bank.length}`);
  await page.locator('#setupView .mode-option', { hasText: 'Ошибки' }).click();
  assert.equal(await page.locator('#eligibleNotice').textContent(), 'Под фильтры подходит вопросов: 1.');
  assert.deepEqual(page.errors, []);
});

test('фильтр по теме считает вопросы темы', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  const topic = 'История и государство';
  const expected = eligible(bank, { ...ALL, topics: [topic] }, {}).length;
  await page.locator('#topicControls label', { hasText: topic }).locator('input').check();
  assert.equal(await page.locator('#eligibleNotice').textContent(), `Под фильтры подходит вопросов: ${expected}.`);
  assert.equal(await page.locator('#topicControls label', { hasText: topic }).locator('.topic-progress').textContent(),
    `0/${expected}`);
  await page.locator('#clearFilters').click();
  assert.equal(await page.locator('#eligibleNotice').textContent(),
    `Под фильтры подходит вопросов: ${eligible(bank, ALL, {}).length}.`);
  assert.deepEqual(page.errors, []);
});

test('база: поиск по-китайски и раскрытие ответа', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await page.locator('#openDatabase').click();
  await page.locator('#databaseView').waitFor();
  await page.locator('#databaseSearch').fill('颐和园');
  assert.match(await page.locator('#databaseCount').textContent(), /^Показано [1-9]\d* из [1-9]\d* вопрос/);
  const first = page.locator('#databaseList article').first();
  assert.equal(await first.locator('.row-answer').isVisible(), false, 'ответ виден до нажатия');
  await first.locator('summary').click();
  // textContent читает и закрытый <details>, поэтому проверяется именно видимость
  assert.equal(await first.locator('.row-answer').isVisible(), true, 'ответ не раскрылся');
  assert.match(await first.locator('.row-answer').textContent(), /^Ответ: /);
  assert.equal(await first.locator('.row-sources a').first().isVisible(), true, 'не видно ссылки на источник');
  await page.locator('#databaseSearch').fill('такого текста точно нет в базе');
  assert.equal(await page.locator('#databaseList .empty').textContent(), 'Ничего не найдено.');
  assert.deepEqual(page.errors, []);
});

test('подписи появляются под неверными вариантами после ответа и в базе', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  // тест не зависит от glosses.json: настоящие подписи вопроса снимаются, а тестовые
  // подкладываются прямо на странице — одному неверному варианту и, для проверки,
  // правильному (её показывать нельзя). Вопрос — с постоянными четырьмя вариантами: у записи
  // с общим набором (досье, склейка pool) раунд берёт три случайных неверных, и подписанного
  // варианта на экране может не оказаться
  const { record, wrongId } = await page.evaluate(() => {
    const target = QUESTION_BANK.find((r) => r.options.length === 4
      && QUESTION_BANK.filter((other) => other.questionRu === r.questionRu).length === 1);
    if (!target) return { record: null, wrongId: null };
    target.options.forEach((o) => { delete o.gloss; });
    const wrong = target.options.find((o) => o.id !== target.answer.optionId);
    wrong.gloss = 'Тестовая подпись к неверному варианту';
    target.options.find((o) => o.id === target.answer.optionId).gloss = 'Подпись правильного — не показывать';
    startRoundWith([target]);
    return { record: target, wrongId: wrong.id };
  });
  assert.ok(record, 'в банке нет вопроса с постоянными четырьмя вариантами');
  assert.equal(await page.locator('.option-gloss').count(), 0, 'подпись видна до ответа');
  // неверный ответ именно на подписанный вариант: на кнопке будут и пометка, и подпись
  await page.locator(`#options button[data-option-id="${wrongId}"]`).click();
  assert.equal(await page.locator('.option-gloss').count(), 1, 'подписей должно быть ровно одна');
  const button = page.locator(`#options button[data-option-id="${wrongId}"]`);
  assert.equal(await button.locator('.option-gloss').textContent(), 'Тестовая подпись к неверному варианту');
  assert.equal(await button.locator('.option-status').textContent(), '✕ Ваш ответ');
  // подпись стоит под китайским текстом варианта и по его левому краю
  const caption = await button.locator('span:nth-child(2)').boundingBox();
  const note = await button.locator('.option-gloss').boundingBox();
  assert.ok(note.y >= caption.y + caption.height - 1, 'подпись не под текстом варианта');
  assert.ok(Math.abs(note.x - caption.x) <= 1, 'подпись не выровнена по тексту варианта');

  await page.locator('#leaveRound').click();
  await page.locator('#openDatabase').click();
  await page.locator('#databaseSearch').fill(record.questionRu);
  assert.equal(await page.locator('#databaseList article').count(), 1, 'поиск должен найти одну запись');
  const row = page.locator('#databaseList article').first();
  await row.locator('summary').click();
  const items = row.locator('.row-glosses li');
  assert.equal(await items.count(), 1);
  assert.equal(await items.first().isVisible(), true);
  assert.match(await items.first().textContent(), /Тестовая подпись к неверному варианту/);
  assert.doesNotMatch(await row.textContent(), /Подпись правильного/);
  assert.deepEqual(page.errors, []);
});

test('настоящие подписи из банка стоят под всеми неверными вариантами', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  // вся цепочка на реальных данных: data/bank.json → dist → интерфейс; ответ верный,
  // поэтому подписи должны быть под каждым неверным вариантом, а не только под выбранным
  const bank = JSON.parse(readFileSync(new URL('../data/bank.json', import.meta.url), 'utf8'));
  const record = bank.find((r) => r.options.filter((o) => o.gloss).length === 3);
  assert.ok(record, 'в банке нет вопроса с подписями у всех трёх неверных вариантов');
  await page.evaluate((id) => startRoundWith([QUESTION_BANK.find((r) => r.id === id)]), record.id);
  await page.locator(`#options button[data-option-id="${record.answer.optionId}"]`).click();
  for (const option of record.options) {
    const note = page.locator(`#options button[data-option-id="${option.id}"] .option-gloss`);
    assert.equal(await note.count(), option.gloss ? 1 : 0, `${record.id}/${option.id}: число подписей`);
    if (option.gloss) assert.equal(await note.textContent(), option.gloss, `${record.id}/${option.id}`);
  }
  assert.deepEqual(page.errors, []);
});

const OLD_PROGRESS = { attempts: 2, correct: 1, completed: true, lastCorrect: false, box: 0, dueAt: 1 };

test('прогресс склеенного дубля переезжает на оставшуюся запись при загрузке и при импорте', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  const kept = bank.find((r) => r.mergedIds?.length);
  assert.ok(kept, 'в банке нет склеенных записей');
  const oldId = kept.mergedIds[0];
  const stored = JSON.stringify({ version: 1, progress: { [oldId]: OLD_PROGRESS } });

  await page.evaluate((value) => localStorage.setItem('lingvo-trainer:v1', value), stored);
  await page.reload();
  assert.equal(await page.locator('#bankCount').textContent(), `Пройдено 1 из ${bank.length}`);
  assert.deepEqual(await page.evaluate(() => Object.keys(state.progress)), [kept.id]);
  await page.locator('#setupView .mode-option', { hasText: 'Ошибки' }).click();
  assert.equal(await page.locator('#eligibleNotice').textContent(), 'Под фильтры подходит вопросов: 1.');

  await page.evaluate(() => localStorage.clear());
  await page.reload();
  assert.equal(await page.locator('#bankCount').textContent(), `Пройдено 0 из ${bank.length}`);
  page.once('dialog', (dialog) => dialog.accept());
  await page.locator('#importProgressFile').setInputFiles({
    name: 'progress.json', mimeType: 'application/json', buffer: Buffer.from(stored),
  });
  await page.waitForFunction((id) => state.progress[id], kept.id);
  assert.deepEqual(await page.evaluate(() => Object.keys(state.progress)), [kept.id]);
  assert.equal(await page.locator('#bankCount').textContent(), `Пройдено 1 из ${bank.length}`);
  assert.deepEqual(page.errors, []);
});

test('файл прогресса несёт и «Чэнъюй»; загрузка — только после подтверждения', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const [record] = await bankOf(page);
  const [cyRecord] = await page.evaluate(() => CHENGYU_BANK);
  const cyProgress = { [cyRecord.id]: { attempts: 1, correct: 0, lastCorrect: false } };
  await page.evaluate(([id, cyValue]) => {
    localStorage.setItem('lingvo-trainer:v1', JSON.stringify({ version: 1, progress: { [id]: {
      attempts: 2, correct: 1, completed: true, lastCorrect: false, box: 0, dueAt: 1 } } }));
    localStorage.setItem('lingvo-trainer:chengyu:v1', JSON.stringify({ version: 1, progress: cyValue }));
  }, [record.id, cyProgress]);
  await page.reload();

  // сохранение: перехватываем Blob, который уходит в ссылку на скачивание
  const saved = await page.evaluate(async () => {
    let blob = null;
    URL.createObjectURL = (value) => { blob = value; return 'blob:test'; };
    HTMLAnchorElement.prototype.click = () => {};
    document.getElementById('exportProgress').click();
    return JSON.parse(await blob.text());
  });
  assert.deepEqual(Object.keys(saved.progress), [record.id]);
  assert.deepEqual(saved.chengyu, cyProgress);

  const upload = (value) => page.locator('#importProgressFile').setInputFiles({
    name: 'progress.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(value)),
  });
  // отказ в подтверждении ничего не меняет
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  const asked = page.waitForEvent('dialog');
  await upload(saved);
  const dialog = await asked;
  assert.match(dialog.message(), /основного тренажёра и «Чэнъюй».*будет заменён/);
  await dialog.dismiss();
  assert.deepEqual(await page.evaluate(() => [state.progress, cy.progress]), [{}, {}]);

  // согласие загружает оба раздела
  page.once('dialog', (dialog) => dialog.accept());
  await upload(saved);
  await page.waitForFunction((id) => state.progress[id], record.id);
  assert.deepEqual(await page.evaluate(() => cy.progress), cyProgress);
  const storedCy = await page.evaluate(() => JSON.parse(localStorage.getItem('lingvo-trainer:chengyu:v1')));
  assert.deepEqual(storedCy.progress, cyProgress);

  // файл прежней версии без «Чэнъюй» прогресс этого раздела не стирает
  page.once('dialog', (dialog) => dialog.accept());
  await upload({ version: 1, progress: {} });
  await page.waitForFunction(() => Object.keys(state.progress).length === 0);
  assert.deepEqual(await page.evaluate(() => cy.progress), cyProgress);
  assert.deepEqual(page.errors, []);
});

test('в раунде нет двух вопросов про один факт', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  // все прежние группы с одним ответом стали одним вопросом с общим набором вариантов;
  // механизм остаётся для пар с разными ответами и проверяется на 20 парах,
  // помеченных прямо на странице
  const grouped = await page.evaluate(() => {
    const picked = QUESTION_BANK.filter((r) => r.answer.state === 'verified').slice(0, 40);
    picked.forEach((r, index) => { r.factGroup = `test-${index % 20}`; });
    return picked.length;
  });
  assert.equal(grouped, 40);
  // сотня раундов по 50 вопросов: без отбора хотя бы в одном оказались бы «двойники»
  const worst = await page.evaluate(() => {
    let repeats = 0;
    for (let index = 0; index < 100; index += 1) {
      const groups = buildRound(QUESTION_BANK, state.filters, {}, 50).map((r) => r.factGroup).filter(Boolean);
      repeats += groups.length - new Set(groups).size;
    }
    return repeats;
  });
  assert.equal(worst, 0);
  await startRound(page, 50);
  const shown = await page.evaluate(() => state.round.map((r) => r.factGroup).filter(Boolean));
  assert.equal(shown.length, new Set(shown).size);
  assert.deepEqual(page.errors, []);
});

test('у вопроса с общим набором в раунде четыре варианта, а в базе — все и метка', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  const pooled = bank.find((r) => r.options.length > 4);
  assert.ok(pooled, 'в банке нет вопросов с общим набором вариантов');
  await page.evaluate((id) => startRoundWith([QUESTION_BANK.find((r) => r.id === id)]), pooled.id);
  const shown = await page.locator('#options button').evaluateAll((buttons) => buttons.map((b) => b.dataset.optionId));
  assert.equal(shown.length, 4);
  assert.ok(shown.includes(pooled.answer.optionId));
  await page.locator(`#options button[data-option-id="${pooled.answer.optionId}"]`).click();
  assert.match(await page.locator('#feedback').textContent(), /Верно/);

  await page.locator('#leaveRound').click();
  await page.locator('#openDatabase').click();
  await page.locator('#databaseSearch').fill(pooled.questionRu);
  const row = page.locator('#databaseList .row', { hasText: pooled.questionRu }).first();
  await row.waitFor();
  assert.match(await row.locator('.row-top').textContent(), /варианты меняются/);
  const options = await row.locator('.row-options').textContent();
  for (const option of pooled.options) assert.ok(options.includes(option.zh), option.zh);
  assert.deepEqual(page.errors, []);
});

test('тема переключается и запоминается', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const before = await page.locator('html').getAttribute('data-theme');
  await page.locator('#themeToggle').click();
  const after = await page.locator('html').getAttribute('data-theme');
  assert.notEqual(after, before);
  await page.reload();
  assert.equal(await page.locator('html').getAttribute('data-theme'), after);
});

test('телефон: ни на одном экране нет горизонтальной прокрутки', LIMIT, async (t) => {
  const page = await openPage(t, { width: 360, height: 780 });
  if (!page) return;
  const bank = await bankOf(page);
  const overflow = () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.equal(await overflow(), 0, 'главная');
  await page.evaluate(() => {
    for (const r of QUESTION_BANK) {
      for (const o of r.options) if (o.id !== r.answer.optionId) o.gloss = 'Длинная подпись для проверки переноса на узком экране телефона';
    }
  });
  await startRound(page, 5);
  await answer(page, await currentRecord(page, bank), false);
  assert.equal(await overflow(), 0, 'вопрос с разбором ответа');
  await page.locator('#leaveRound').click();
  await page.locator('#openDatabase').click();
  const first = page.locator('#databaseList article').first();
  await first.locator('summary').click();
  assert.equal(await first.locator('.row-answer').isVisible(), true, 'ответ в базе не раскрылся');
  assert.equal(await overflow(), 0, 'база с раскрытым ответом');
  assert.deepEqual(page.errors, []);
});

async function pickFormat(page, label) {
  await page.locator('#setupView .mode-option', { hasText: label }).click();
}

test('формат выбирается, объясняется и переживает перезагрузку', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  assert.equal(await page.locator('input[name="studyFormat"]:checked').getAttribute('value'), 'choice');
  await pickFormat(page, 'Верно или нет');
  assert.match(await page.locator('#formatHelp').textContent(), /один предложенный ответ/);
  await page.reload();
  assert.equal(await page.locator('input[name="studyFormat"]:checked').getAttribute('value'), 'truefalse');
  // «Сбросить фильтры» не трогает формат: это не фильтр
  await page.locator('#clearFilters').click();
  assert.equal(await page.locator('input[name="studyFormat"]:checked').getAttribute('value'), 'truefalse');
  assert.deepEqual(page.errors, []);
});

/** Убирает из банка страницы вопросы, которым нужны варианты (или, наоборот, все остальные),
 * чтобы стадия первого вопроса во «Вспомни сам» не зависела от случая. */
async function keepRecallQuestions(page, needs) {
  await page.evaluate((keepNeeds) => {
    for (let index = QUESTION_BANK.length - 1; index >= 0; index -= 1) {
      if (needsOptions(QUESTION_BANK[index]) !== keepNeeds) QUESTION_BANK.splice(index, 1);
    }
  }, needs);
}

test('вспомни сам: ответ открывается пробелом, «не вспомнил» отправляет вопрос в «Ошибки»', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, false);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  assert.equal(await page.locator('#recallPrompt').isVisible(), true);
  assert.equal(await page.locator('#options button').count(), 0);
  // до открытия ответа оценка ничего не делает
  await page.keyboard.press('Digit3');
  assert.equal(await page.locator('#nextButton').isVisible(), false);
  await page.keyboard.press('Space');
  assert.equal(await page.locator('#feedback.reveal').isVisible(), true);
  assert.equal(await page.locator('#recallRate').isVisible(), true);
  assert.equal(await page.locator('#recallPrompt').isVisible(), false);
  await page.keyboard.press('Digit3');
  await page.locator('#nextButton:not(.hidden)').waitFor();
  assert.equal(await page.locator('#progressSteps li').first().getAttribute('class'), 'ink-step ink-step--wrong ink-step--current');
  await page.locator('#leaveRound').click();
  await page.locator('#setupView .mode-option', { hasText: 'Ошибки' }).click();
  assert.equal(await page.locator('#eligibleNotice').textContent(), 'Под фильтры подходит вопросов: 1.');
  assert.deepEqual(page.errors, []);
});

test('вспомни сам: кнопка «Показать ответ» с клавиатуры срабатывает один раз', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, false);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  await page.locator('#revealAnswer').focus();
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('#recallRate').isVisible(), true);
  // ответ открыт, оценки ещё нет: Enter не должен ни оценить, ни перелистнуть вопрос
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('#nextButton').isVisible(), false);
  assert.match(await page.locator('#progressLabel').textContent(), /^Вопрос 1 из/);
  assert.deepEqual(page.errors, []);
});

test('вспомни сам: подсказка показывает варианты, верный ответ засчитан как «неточно»', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  // все вопросы уже в третьей коробке: «неточно» оставит третью, «вспомнил сам» дал бы четвёртую
  await page.evaluate(() => localStorage.setItem('lingvo-trainer:v1', JSON.stringify({
    version: 1,
    progress: Object.fromEntries(QUESTION_BANK.map((r) => [r.id,
      { attempts: 3, correct: 3, completed: true, lastCorrect: true, box: 3, dueAt: 0 }])),
  })));
  await page.reload();
  await keepRecallQuestions(page, false);
  const bank = await bankOf(page);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  await page.locator('#showHint').click();
  assert.equal(await page.locator('#options button').count(), 4);
  assert.match(await page.locator('#recallNote').textContent(), /«вспомнил неточно»/);
  const record = await currentRecord(page, bank);
  await answer(page, record, true);
  const progress = await page.evaluate(() => JSON.parse(localStorage.getItem('lingvo-trainer:v1')).progress);
  assert.equal(progress[record.id].box, 3, 'с подсказкой коробка не растёт');
  assert.equal(progress[record.id].lastCorrect, true);
  assert.deepEqual(page.errors, []);
});

test('вспомни сам: подсказка клавиш следует за стадией вопроса', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, false);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  const hint = () => page.locator('#quizHint').textContent();
  assert.match(await hint(), /Пробел — показать ответ/);
  assert.doesNotMatch(await hint(), /оценка|вспомнил/, 'до открытия ответа оценивать нечего');
  await page.keyboard.press('Space');
  assert.match(await hint(), /1 — вспомнил сам/);
  assert.match(await hint(), /Enter — дальше/);
  await page.keyboard.press('Digit1');
  await page.keyboard.press('Enter');
  await page.keyboard.press('KeyV');
  assert.match(await hint(), /1–4 или A–D — ответить/, 'с подсказкой цифры выбирают вариант');
  assert.deepEqual(page.errors, []);
});

test('вспомни сам: вопрос «из перечисленного» подсказывает клавиши выбора, а не оценки', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, true);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  assert.match(await page.locator('#quizHint').textContent(), /1–4 или A–D — ответить/);
  assert.deepEqual(page.errors, []);
});

test('вспомни сам: фокус не теряется ни после подсказки, ни после оценки', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, false);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  await page.locator('#showHint').click();
  assert.equal(await page.evaluate(() => document.activeElement === document.querySelector('#options button')), true,
    'после «Не помню» фокус — на первом варианте');
  await page.keyboard.press('Escape');
  await startRound(page, 5);
  await page.keyboard.press('Space');
  await page.locator('#recallRate button[data-outcome="correct"]').click();
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'nextButton', 'после оценки фокус — на «Следующий вопрос»');
  assert.deepEqual(page.errors, []);
});

test('вспомни сам: вопрос «из перечисленного» сразу показывает варианты', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, true);
  const bank = await bankOf(page);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  // в региональных бланках бывает и три варианта: на экране столько, сколько у вопроса, но не больше четырёх
  const record = await currentRecord(page, bank);
  assert.equal(await page.locator('#options button').count(), Math.min(4, record.options.length));
  assert.equal(await page.locator('#recallPrompt').isVisible(), false);
  assert.match(await page.locator('#recallNote').textContent(), /без вариантов не ответить/);
  assert.deepEqual(page.errors, []);
});

test('вспомни сам: в итогах — разбивка по самооценке', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, false);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  for (let question = 0; question < 5; question += 1) {
    await page.keyboard.press('Space');
    await page.keyboard.press(question === 0 ? 'Digit2' : 'Digit1');
    await page.keyboard.press('Enter');
  }
  await page.locator('#resultsView').waitFor();
  assert.equal(await page.locator('#finalScore').textContent(), '5 / 5');
  assert.equal(await page.locator('#resultRecall').textContent(), 'вспомнил сам — 4 · неточно — 1 · не вспомнил — 0');
  assert.deepEqual(page.errors, []);
});

test('уход из раунда посреди стадии не оставляет панелей в раунде другого формата', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await keepRecallQuestions(page, false);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  await page.keyboard.press('Space');
  await page.keyboard.press('Escape');
  await pickFormat(page, 'Выбор ответа');
  await startRound(page, 5);
  assert.equal(await page.locator('#options button').count(), 4);
  for (const id of ['#recallPrompt', '#recallRate', '#recallNote', '#feedback']) {
    assert.equal(await page.locator(id).isVisible(), false, id);
  }
  assert.deepEqual(page.errors, []);
});

test('телефон: «Вспомни сам» без горизонтальной прокрутки', LIMIT, async (t) => {
  const page = await openPage(t, { width: 360, height: 780 });
  if (!page) return;
  await keepRecallQuestions(page, false);
  const overflow = () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  await pickFormat(page, 'Вспомни сам');
  await startRound(page, 5);
  assert.equal(await overflow(), 0, 'стадия «вспомнить»');
  await page.locator('#revealAnswer').click();
  assert.equal(await overflow(), 0, 'ответ и самооценка');
  assert.deepEqual(page.errors, []);
});

const currentStatement = (page) => page.evaluate(() => ({
  id: state.round[state.position].id, isTrue: state.statement.isTrue, zh: state.statement.zh,
}));

test('верно или нет: ошибка объясняется, возвращается в раунде и повторяется в том же формате', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  await pickFormat(page, 'Верно или нет');
  await startRound(page, 5);
  let questions = 0;
  let wrongId = null;
  while (await page.locator('#quizView').isVisible()) {
    questions += 1;
    assert.ok(questions <= 6, 'раунд не заканчивается');
    assert.equal(await page.locator('#tfPanel').isVisible(), true);
    assert.equal(await page.locator('#options button').count(), 0);
    const statement = await currentStatement(page);
    assert.equal(await page.locator('#tfOption').innerText(), statement.zh);
    const mistake = questions === 1;
    // ← — «верно», → — «неверно»; ошибаемся только на первом вопросе
    const sayTrue = mistake ? !statement.isTrue : statement.isTrue;
    await page.keyboard.press(sayTrue ? 'ArrowLeft' : 'ArrowRight');
    await page.locator('#nextButton:not(.hidden)').waitFor();
    if (mistake) {
      wrongId = statement.id;
      const record = bank.find((r) => r.id === statement.id);
      const right = record.options.find((o) => o.id === record.answer.optionId);
      assert.equal(await page.locator('#feedback.bad').isVisible(), true);
      assert.ok((await page.locator('#feedback').textContent()).includes(right.zh), 'нет правильного ответа');
      assert.match(await page.locator('#scoreLabel').textContent(), /серия 0/);
    }
    if (questions === 6) assert.equal(statement.id, wrongId, 'шестым должен вернуться ошибочный вопрос');
    await page.keyboard.press('Enter');
  }
  assert.equal(await page.locator('#finalScore').textContent(), '4 / 5');
  assert.match(await page.locator('#mistakeList li').first().textContent(), /«(не)?верно» для/);
  await page.locator('#repeatMistakes').click();
  assert.equal(await page.locator('#tfPanel').isVisible(), true, 'повтор ошибок — в том же формате');
  assert.deepEqual(page.errors, []);
});

test('верно или нет: угаданное «верно» не выводит вопрос из «Ошибок»', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  const target = bank.find((r) => r.answer.state === 'verified');
  await page.evaluate((id) => localStorage.setItem('lingvo-trainer:v1', JSON.stringify({
    version: 1,
    progress: { [id]: { attempts: 1, correct: 0, completed: true, lastCorrect: false, box: 0, dueAt: 0 } },
  })), target.id);
  await page.reload();
  await page.locator('#setupView .mode-option', { hasText: 'Ошибки' }).click();
  await pickFormat(page, 'Верно или нет');
  await startRound(page, 5);
  const statement = await currentStatement(page);
  assert.equal(statement.id, target.id);
  await page.locator(statement.isTrue ? '#tfTrue' : '#tfFalse').click();
  assert.equal(await page.locator('#feedback.good').isVisible(), true);
  await page.locator('#leaveRound').click();
  assert.equal(await page.locator('#eligibleNotice').textContent(), 'Под фильтры подходит вопросов: 1.');
  assert.deepEqual(page.errors, []);
});

test('телефон: «Верно или нет» с длинным вариантом без горизонтальной прокрутки', LIMIT, async (t) => {
  const page = await openPage(t, { width: 360, height: 780 });
  if (!page) return;
  await page.evaluate(() => {
    for (const r of QUESTION_BANK) for (const o of r.options) o.zh = `${o.zh}中华人民共和国全国人民代表大会常务委员会`;
  });
  const overflow = () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  await pickFormat(page, 'Верно или нет');
  await startRound(page, 5);
  assert.equal(await overflow(), 0, 'карточка с предложенным ответом');
  await page.locator('#tfTrue').click();
  assert.equal(await overflow(), 0, 'разбор ответа');
  assert.deepEqual(page.errors, []);
});

/* ---------- раздел «Чэнъюй» ---------- */

async function openChengyu(page) {
  await page.locator('#navChengyu').click();
  await page.locator('#cySetupView').waitFor();
}

/** Задание на экране: по чэнъюю в клетках, у обратного задания — по русской пословице. */
async function currentChengyu(page, bank) {
  const proverbShown = await page.locator('#cyProverb').isVisible();
  if (proverbShown) {
    const proverb = (await page.locator('#cyProverb').textContent()).replace(/^«|»$/g, '');
    return bank.find((r) => r.prompt === proverb);
  }
  const chengyu = await page.locator('#cyChengyu').getAttribute('aria-label');
  return bank.find((r) => r.chengyu === chengyu && r.kind !== 'reverse');
}

test('чэнъюй: раунд с верным и неверным ответом, разбор, итоги и справочник', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await page.evaluate(() => CHENGYU_BANK);
  // 35 олимпиадных и принятые составленные
  assert.equal(bank.filter((r) => r.occurrences).length, 35);
  assert.ok(bank.length > 35);
  await openChengyu(page);
  assert.equal(await page.locator('#navChengyu').getAttribute('aria-current'), 'page');
  assert.equal(await page.locator('#cyStatTotal').textContent(), String(bank.length));
  await page.locator('input[name="cySize"][value="5"]').check();
  await page.locator('#cyStartButton').click();
  await page.locator('#cyQuizView').waitFor();
  assert.equal(await page.locator('#cyProgressLabel').textContent(), 'Задание 1 из 5');
  assert.equal(await page.locator('.site-nav').isVisible(), false, 'в раунде навигация скрыта');

  let wrongRecord = null;
  for (let n = 0; n < 5; n += 1) {
    const record = await currentChengyu(page, bank);
    assert.ok(record, 'задание на экране не найдено в банке');
    assert.match(await page.locator('#cySourceLabel').textContent(),
      record.occurrences ? /^ВсОШ 20\d\d\/\d\d · .+ этап · задание \d+$/ : /^Составленное задание$/);
    const correct = n !== 0;
    const optionId = correct ? record.answer : record.options.find((o) => o.id !== record.answer).id;
    // клавиатура: буква по видимому порядку
    const shown = await page.locator('#cyOptions button').evaluateAll((b) => b.map((x) => x.dataset.optionId));
    await page.keyboard.press(`Digit${shown.indexOf(optionId) + 1}`);
    await page.locator('#cyFeedback.good, #cyFeedback.bad').waitFor();
    assert.equal(await page.locator('#cyFeedback .verdict strong').textContent(), correct ? 'Верно' : 'Неверно');
    assert.match(await page.locator('#cyFeedback').textContent(), /Смысл/);
    if (!correct) wrongRecord = record;
    await page.keyboard.press('Enter');
  }
  await page.locator('#cyResultsView').waitFor();
  assert.match(await page.locator('#cyFinalScore').textContent(), /^4\s*\/ 5$/);
  assert.equal(await page.locator('#cyMistakeList li').count(), 1);
  assert.equal(await page.locator('#cyRepeatMistakes').isVisible(), true);

  // ошибка сохранилась: набор «Ошибки» находит ровно это задание
  await page.locator('#cyBackToSetup').click();
  await page.locator('#cySetupView .mode-option', { hasText: 'Ошибки' }).click();
  assert.match(await page.locator('#cyEligibleNotice').textContent(), /^Доступно 1 задание/);
  const stored = await page.evaluate(() => JSON.parse(localStorage.getItem('lingvo-trainer:chengyu:v1')));
  assert.equal(stored.progress[wrongRecord.id].lastCorrect, false);
  // прогресс основного раздела не тронут
  assert.equal(await page.evaluate(() => localStorage.getItem('lingvo-trainer:v1')), null);

  await page.locator('#cyOpenReference').click();
  await page.locator('#cyReferenceView').waitFor();
  assert.equal(await page.locator('#cyReferenceList article').count(), bank.length);
  await page.locator('#cyReferenceSearch').fill('bei gong she');
  assert.equal(await page.locator('#cyReferenceList article').count(), 1);
  const row = page.locator('#cyReferenceList article').first();
  await row.locator('summary').click();
  assert.match(await row.locator('.cy-key').textContent(), /У страха глаза велики/);
  await page.keyboard.press('Escape');
  await page.keyboard.press('Escape');
  await page.locator('#cySetupView').waitFor();
  // адрес следует за разделом: из «Тренировки» перезагрузка не возвращает в «Чэнъюй»
  assert.equal(new URL(page.url()).hash, '#chengyu');
  await page.locator('#navSetup').click();
  assert.equal(new URL(page.url()).hash, '');
  await page.reload();
  assert.equal(await page.locator('#setupView').isVisible(), true);
  assert.deepEqual(page.errors, []);
});

test('чэнъюй: ссылка #chengyu открывает раздел, телефон без горизонтальной прокрутки', LIMIT, async (t) => {
  const page = await openPage(t, { width: 360, height: 780 });
  if (!page) return;
  await page.goto(`${baseUrl}#chengyu`);
  await page.locator('#cySetupView').waitFor();
  const overflow = () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.equal(await overflow(), 0, 'начало раздела');
  await page.locator('input[name="cySize"][value="all"]').check();
  await page.locator('#cyStartButton').click();
  await page.locator('#cyQuizView').waitFor();
  assert.equal(await page.locator('#cyProgressTrack').isVisible(), true, 'длинный раунд — полоса, а не кружки');
  await page.locator('#cyOptions button').first().click();
  assert.equal(await overflow(), 0, 'задание с разбором');
  await page.locator('#cyLeaveRound').click();
  await page.locator('#cyOpenReference').click();
  await page.locator('#cyReferenceList article summary').first().click();
  assert.equal(await overflow(), 0, 'справочник');
  assert.deepEqual(page.errors, []);
});

test('фильтр «Откуда вопросы» и пиньинь: раунд из дополнений, транскрипция по кнопке в шапке', LIMIT, async (t) => {
  const page = await openPage(t, { width: 375, height: 812 });
  if (!page) return;
  const bank = await page.evaluate(() => QUESTION_BANK);
  const additions = bank.filter((record) => record.origin === 'addition').length;
  await page.locator('input[name="studyOrigin"][value="addition"]').check({ force: true });
  assert.match(await page.locator('#eligibleNotice').textContent(), new RegExp(`: ${additions}\\.`));
  await page.locator('#startButton').click();
  await page.locator('#quizView').waitFor();
  assert.equal(await page.locator('#sourceLabel').textContent(), 'Проверенное дополнение');
  // транскрипция в разметке есть, но видна только по настройке — и переключается посреди вопроса
  const reading = page.locator('#options .pinyin').first();
  assert.equal(await reading.isVisible(), false);
  await page.locator('#pinyinToggle').click();
  assert.equal(await reading.isVisible(), true);
  assert.equal(await page.locator('#pinyinToggle').getAttribute('aria-pressed'), 'true');
  // клавиша P — то же, что кнопка; по коду клавиши, поэтому и на русской раскладке
  await page.keyboard.press('KeyP');
  assert.equal(await reading.isVisible(), false);
  await page.keyboard.press('KeyP');
  assert.equal(await reading.isVisible(), true);
  // на телефоне после ответа видна кнопка «Следующий вопрос», после неё — снова начало вопроса
  await page.locator('#options button').first().click();
  // докрутка к кнопке, но вердикт разбора не уезжает за верх экрана
  await page.waitForFunction(() => {
    const next = document.getElementById('nextButton').getBoundingClientRect();
    const verdict = document.querySelector('#feedback .verdict').getBoundingClientRect();
    return verdict.top >= 0 && (next.bottom <= innerHeight || verdict.top < 40);
  });
  await page.locator('#nextButton').click();
  await page.waitForFunction(() => Math.abs(document.getElementById('quizView').getBoundingClientRect().top) < 40);
  await page.reload();
  assert.equal(await page.evaluate(() => document.documentElement.dataset.pinyin), 'on', 'настройка пережила перезагрузку');
  assert.equal(await page.locator('input[name="studyOrigin"][value="addition"]').isChecked(), true);
  assert.deepEqual(page.errors, []);
});

test('телефон: с включённым пиньинем ни один вопрос и вариант не выходит за край экрана', LIMIT, async (t) => {
  const page = await openPage(t, { width: 375, height: 812 });
  if (!page) return;
  await page.locator('#startButton').click();
  await page.locator('#quizView').waitFor();
  await page.locator('#pinyinToggle').click();
  // каждый вопрос банка рисуется в раунде теми же функциями интерфейса
  const result = await page.evaluate(() => {
    const overflowing = [];
    let rubies = 0;
    for (const record of QUESTION_BANK) {
      renderOptions(record);
      document.getElementById('questionText').replaceChildren(...questionNodes(record.questionRu));
      rubies += document.querySelectorAll('#questionText ruby').length;
      if (document.documentElement.scrollWidth > document.documentElement.clientWidth) overflowing.push(record.id);
    }
    return { overflowing, rubies };
  });
  assert.deepEqual(result.overflowing, []);
  assert.ok(result.rubies > 0, 'над китайскими вставками вопроса есть транскрипция');
  assert.deepEqual(page.errors, []);
});

test('главная: режим, формат и темы свёрнуты, в заголовке — текущий выбор', LIMIT, async (t) => {
  const page = await openPage(t, { width: 375, height: 812 }, { folded: true });
  if (!page) return;
  for (const id of ['#modeFold', '#formatFold', '#topicsFold']) {
    assert.equal(await page.locator(id).getAttribute('open'), null, `${id} раскрыт`);
  }
  assert.equal(await page.locator('input[name="studyMode"][value="new"]').isVisible(), false);
  assert.equal(await page.locator('#modeValue').textContent(), 'Все вопросы');
  assert.equal(await page.locator('#topicsValue').textContent(), 'все темы');
  await page.locator('#topicsFold > summary').click();
  await page.locator('input[name="studyOrigin"][value="olympiad"]').check({ force: true });
  assert.equal(await page.locator('#topicsValue').textContent(), 'все темы · только с олимпиад');
  await page.locator('#modeFold > summary').click();
  await page.locator('input[name="studyMode"][value="new"]').check({ force: true });
  assert.equal(await page.locator('#modeValue').textContent(), 'Новые');
  // Enter на заголовке раздела раскрывает его, а не начинает раунд («Enter — начать раунд»)
  await page.locator('#formatFold > summary').focus();
  await page.keyboard.press('Enter');
  assert.notEqual(await page.locator('#formatFold').getAttribute('open'), null);
  assert.equal(await page.evaluate(() => state.view), 'setup');
  // стрелка раскрытия не входит в имя раздела для чтения с экрана
  assert.equal(await page.locator('#modeFold .fold-arrow').getAttribute('aria-hidden'), 'true');
  // свёрнутое не мешает начать раунд
  await page.locator('#startButton').click();
  await page.locator('#quizView').waitFor();
  assert.deepEqual(page.errors, []);
});

test('телефон: после ответа с длинным разбором видна кнопка «Следующий вопрос», много источников свёрнуто', LIMIT, async (t) => {
  const page = await openPage(t, { width: 375, height: 667 });
  if (!page) return;
  await page.locator('input[name="roundSize"][value="all"]').check({ force: true });
  await page.locator('#startButton').click();
  await page.locator('#quizView').waitFor();
  // вопрос с самым длинным пояснением и больше чем двумя источниками
  const longest = await page.evaluate(() => QUESTION_BANK.filter((r) => r.evidence.length > 2)
    .sort((a, b) => b.explanation.ru.length - a.explanation.ru.length)[0].id);
  for (let step = 0; step < 2000; step += 1) {
    const id = await page.evaluate(() => state.round[state.position].id);
    if (id === longest) break;
    await page.evaluate(() => { state.position += 1; renderQuestion(); });
  }
  await page.locator('#options button').first().click();
  await page.waitForFunction(() => {
    const next = document.getElementById('nextButton').getBoundingClientRect();
    return next.top >= 0 && next.bottom <= innerHeight;
  }, null, { timeout: 5000 });
  assert.equal(await page.locator('#feedback details.feedback-sources').count(), 1);
  assert.equal(await page.locator('#feedback .feedback-sources a').first().isVisible(), false);
  assert.deepEqual(page.errors, []);
});

test('телефон: во «Вспомни сам» после самооценки видна кнопка «Следующий вопрос»', LIMIT, async (t) => {
  const page = await openPage(t, { width: 375, height: 667 });
  if (!page) return;
  await page.locator('input[name="studyFormat"][value="recall"]').check({ force: true });
  await page.locator('#startButton').click();
  await page.locator('#quizView').waitFor();
  // вопрос без обязательных вариантов и с самым длинным пояснением
  await page.evaluate(() => {
    const longest = QUESTION_BANK.filter((r) => !needsOptions(r))
      .sort((a, b) => b.explanation.ru.length - a.explanation.ru.length)[0];
    startRoundWith([longest], 'recall');
  });
  await page.locator('#revealAnswer').click();
  await page.locator('#recallRate button').first().click();
  await page.waitForFunction(() => {
    const next = document.getElementById('nextButton').getBoundingClientRect();
    return next.top >= 0 && next.bottom <= innerHeight;
  }, null, { timeout: 5000 });
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'nextButton');
  assert.deepEqual(page.errors, []);
});
