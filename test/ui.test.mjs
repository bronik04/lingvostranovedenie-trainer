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

/** Свежая вкладка с пустым localStorage; ошибки страницы копятся в errors. */
async function openPage(t, viewport = { width: 1280, height: 900 }) {
  if (skipReason) {
    t.skip(skipReason);
    return null;
  }
  const context = await browser.newContext({ viewport });
  t.after(() => context.close());
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
 * есть записи с одинаковым вопросом и вариантами, но разными id ответа
 * (2017-18-reg-3 и 2019-20-mun-qf8fe30). */
async function currentRecord(page, bank) {
  const question = await page.locator('#questionText').textContent();
  const shown = await page.locator('#options button').evaluateAll((buttons) => buttons
    .map((b) => `${b.dataset.optionId}=${b.querySelector('span:nth-child(2)').textContent}`).sort().join('|'));
  const matches = bank.filter((r) => r.questionRu === question
    && r.options.map((o) => `${o.id}=${o.zh}`).sort().join('|') === shown);
  assert.equal(matches.length, 1, `вопрос на экране не определить однозначно: ${question}`);
  return matches[0];
}

async function answer(page, record, correct) {
  const optionId = correct
    ? record.answer.optionId
    : record.options.find((o) => o.id !== record.answer.optionId).id;
  await page.locator(`#options button[data-option-id="${optionId}"]`).click();
}

async function startRound(page, size) {
  await page.locator('#settingsPanel > summary').click();
  await page.locator('#roundSize').selectOption(String(size));
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
  await startRound(page, 5);
  assert.equal(await page.locator('#progressLabel').textContent(), 'Вопрос 1 из 5');

  let wrongId = null;
  let questions = 0;
  while (await page.locator('#quizView').isVisible()) {
    const record = await currentRecord(page, bank);
    questions += 1;
    assert.ok(questions <= 6, 'раунд не заканчивается');
    if (questions === 6) assert.equal(record.id, wrongId, 'шестым должен вернуться ошибочный вопрос');
    // ошибаемся ровно один раз — на втором вопросе; повтор этой ошибки отвечаем верно
    const correct = questions !== 2;
    if (!correct) wrongId = record.id;
    await answer(page, record, correct);
    const feedback = page.locator('#feedback');
    assert.match(await feedback.getAttribute('class'), correct ? /\bgood\b/ : /\bbad\b/);
    assert.match(await feedback.textContent(), correct ? /^Верно/ : /^Неверно.*Правильный ответ/);
    await page.locator('#nextButton').click();
  }

  assert.equal(questions, 6, 'ошибочный вопрос должен вернуться в раунд один раз');
  await page.locator('#resultsView').waitFor();
  // повтор ошибки закрепляет ответ, но не исправляет счёт: из пяти вопросов верно четыре
  assert.equal(await page.locator('#finalScore').textContent(), '4 / 5');
  assert.doesNotMatch(await page.locator('#resultText').textContent(), /без ошибок/);
  assert.equal(await page.locator('#repeatMistakes').textContent(), 'Повторить ошибки раунда (1)');

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
  await page.locator('.mode-option', { hasText: 'Ошибки' }).click();
  assert.equal(await page.locator('#eligibleNotice').textContent(), 'Под фильтры подходит вопросов: 1.');
  assert.deepEqual(page.errors, []);
});

test('фильтр по теме считает вопросы темы', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  const topic = 'История и государство';
  const expected = eligible(bank, { ...ALL, topics: [topic] }, {}).length;
  await page.locator('#settingsPanel > summary').click();
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
  // glosses.json в пилоте ещё пуст: подписи подкладываются в банк прямо на странице —
  // одному неверному варианту и, для проверки, правильному (её показывать нельзя)
  const { record, wrongId } = await page.evaluate(() => {
    const target = QUESTION_BANK.find((r) => r.id === '2015-16-mun-1');
    const wrong = target.options.find((o) => o.id !== target.answer.optionId);
    wrong.gloss = 'Тестовая подпись к неверному варианту';
    target.options.find((o) => o.id === target.answer.optionId).gloss = 'Подпись правильного — не показывать';
    startRoundWith([target]);
    return { record: target, wrongId: wrong.id };
  });
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
