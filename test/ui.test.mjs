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

/** Кнопка раунда наверху главной: при пустом прогрессе — «Начать первый раунд». */
const startButton = (page) => page.locator('#firstStart:visible, #startButton:visible');

async function startRound(page, size) {
  await page.locator(`input[name="roundSize"][value="${size}"]`).check();
  await startButton(page).click();
  await page.locator('#quizView').waitFor();
}

const hashOf = (page) => new URL(page.url()).hash;

const reviewEntries = (page) => page.evaluate(() =>
  JSON.parse(localStorage.getItem('lingvo-trainer:review:v1')).entries);

test('отладка: отметка, комментарий, перезагрузка и выгрузка точного контекста', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  assert.equal(await page.locator('#reviewToggle').count(), 1);
  await startRound(page, 10);
  assert.equal(await page.locator('#reviewBar').isVisible(), false);
  await page.keyboard.press('Control+Shift+KeyE');
  assert.equal(await page.locator('#reviewBar').isVisible(), true);
  const record = await currentRecord(page, await bankOf(page));
  const shown = await page.locator('#options button').evaluateAll((buttons) => buttons.map((b) => ({
    optionId: b.dataset.optionId, text: b.querySelector('.option-text').firstChild.textContent,
  })));
  await page.locator('#reviewFlag').click();
  let [entry] = await reviewEntries(page);
  assert.equal(entry.questionId, record.id);
  assert.equal(entry.comment, '');
  assert.deepEqual(entry.context.shownOptions, shown);
  assert.deepEqual(entry.snapshot, record);
  await page.locator('#reviewCommentOpen').click();
  const comment = 'Два ответа выглядят верными <img src=x onerror=alert(1)>';
  await page.locator('#reviewComment').fill(comment);
  await page.keyboard.press('Escape');
  assert.equal(hashOf(page), '#round');
  assert.equal(await page.locator('#reviewDialog').isVisible(), false);
  await page.reload();
  assert.equal(await page.locator('#reviewBar').isVisible(), true);
  [entry] = await reviewEntries(page);
  assert.equal(entry.comment, comment);
  assert.deepEqual(entry.context.shownOptions, shown, 'снимок не заменился после перемешивания');
  await page.locator('#reviewOpenList').click();
  assert.equal(await page.locator('#reviewList img').count(), 0);
  assert.match(await page.locator('#reviewList').innerText(), /Два ответа/);
  const saved = await page.evaluate(async () => {
    let blob;
    URL.createObjectURL = (value) => { blob = value; return 'blob:test'; };
    HTMLAnchorElement.prototype.click = () => {};
    document.getElementById('reviewExport').click();
    return JSON.parse(await blob.text());
  });
  assert.equal(saved.type, 'lingvo-question-review');
  assert.deepEqual(saved.entries, [entry]);
  assert.equal((await reviewEntries(page)).length, 1, 'выгрузка оставляет отметки');
  assert.deepEqual(await page.evaluate(() => state.progress), {});
  assert.deepEqual(page.errors, []);
});

test('отладка: предложенный ответ «Верно или нет» и клавиши внутри окна', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await page.locator('label:has(input[name="studyFormat"][value="truefalse"])').click();
  await startRound(page, 10);
  await page.keyboard.press('Meta+Shift+KeyE');
  const statement = await page.evaluate(() => state.statement);
  await page.locator('#reviewCommentOpen').click();
  assert.deepEqual((await reviewEntries(page))[0].context.statement, statement);
  await page.locator('#reviewClose').focus();
  await page.keyboard.press('1');
  await page.keyboard.press('p');
  assert.equal(await page.evaluate(() => state.answered), false);
  assert.notEqual(await page.locator('html').getAttribute('data-pinyin'), 'on');
  await page.keyboard.press('Escape');
  await page.locator('#tfTrue').click();
  await page.locator('#nextButton').click();
  assert.equal(await page.locator('#reviewFlag').innerText(), 'Отметить вопрос');
  assert.equal((await reviewEntries(page)).length, 1);
});

test('отладка: телефон, чэнъюй, редактирование и снятие отметки', LIMIT, async (t) => {
  const page = await openPage(t, { width: 375, height: 667 });
  if (!page) return;
  await viewMenuItem(page, 'reviewMenu');
  await page.locator('#navChengyu').click();
  await page.locator('#cyFirstStart').click();
  await page.locator('#cyReviewFlag').click();
  const record = await page.evaluate(() => cy.round[cy.position]);
  assert.equal((await reviewEntries(page))[0].section, 'chengyu');
  assert.equal((await reviewEntries(page))[0].questionId, record.id);
  await page.locator('#reviewOpenList').click();
  await page.locator('#reviewList button').first().click();
  await page.locator('#reviewComment').fill('Проверить русский аналог');
  await page.locator('#reviewBack').click();
  assert.match(await page.locator('#reviewList').innerText(), /Проверить русский аналог/);
  const box = await page.locator('#reviewDialog').boundingBox();
  assert.ok(box.x >= 0 && box.x + box.width <= 375);
  assert.ok(box.y >= 0 && box.y + box.height <= 667);
  await page.locator('#reviewList button').first().click();
  await page.locator('#reviewRemove').click();
  assert.equal((await reviewEntries(page)).length, 0);
  assert.equal(await page.locator('#reviewExport').isDisabled(), true);
  await page.locator('#reviewClose').click();
  assert.equal(await page.locator('#cyQuizView').isVisible(), true);
  assert.deepEqual(page.errors, []);
});

test('отладка: «Вспомни сам» не раскрывает ответ при отметке', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await page.evaluate(() => {
    const record = QUESTION_BANK.find((r) => !needsOptions(r));
    startRoundWith([record], 'recall');
  });
  await page.keyboard.press('Control+Shift+KeyE');
  await page.locator('#reviewFlag').click();
  const [entry] = await reviewEntries(page);
  assert.equal(entry.context.format, 'recall');
  assert.equal(entry.context.stage, 'recall');
  assert.deepEqual(entry.context.shownOptions, []);
  assert.equal(await page.locator('#recallPrompt').isVisible(), true);
  assert.equal(await page.locator('#feedback').isVisible(), false);
});

test('отладка: недоступное хранилище явно сообщает об отсутствии сохранения', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await page.evaluate(() => {
    Storage.prototype.setItem = () => { throw new Error('quota'); };
  });
  await startRound(page, 10);
  await page.keyboard.press('Control+Shift+KeyE');
  await page.locator('#reviewFlag').click();
  assert.match(await page.locator('#reviewStorageWarning').innerText(), /выгрузите/i);
  await page.locator('#reviewOpenList').click();
  assert.equal(await page.locator('#reviewList button').count(), 1);
  assert.equal(await page.locator('#reviewExport').isEnabled(), true);
});

test('отладка: повреждённый список не перезаписывается новой отметкой', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await page.evaluate(() => localStorage.setItem('lingvo-trainer:review:v1', '{broken'));
  await page.reload();
  await startRound(page, 10);
  await page.keyboard.press('Control+Shift+KeyE');
  await page.locator('#reviewFlag').click();
  assert.equal(await page.evaluate(() => localStorage.getItem('lingvo-trainer:review:v1')), '{broken');
  assert.match(await page.locator('#reviewStorageWarning').innerText(), /выгрузите/i);
});

test('отладка: удаление в другой вкладке закрывает устаревший редактор с объяснением', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await startRound(page, 10);
  await page.keyboard.press('Control+Shift+KeyE');
  await page.locator('#reviewCommentOpen').click();
  await page.locator('#reviewComment').fill('Первый комментарий');
  const other = await page.context().newPage();
  await other.goto(baseUrl);
  await other.locator('#reviewOpenList').click();
  await other.locator('#reviewList button').first().click();
  await other.locator('#reviewRemove').click();
  await page.waitForFunction(() => document.getElementById('reviewCount').textContent === '0');
  assert.equal(await page.locator('#reviewEditor').isVisible(), false);
  assert.match(await page.locator('#reviewStatus').innerText(), /другой вкладке/);
  assert.deepEqual(await reviewEntries(page), []);
});

test('отладка: копирование отчёта с запасным ручным способом', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await startRound(page, 10);
  await page.keyboard.press('Control+Shift+KeyE');
  await page.locator('#reviewCommentOpen').click();
  await page.locator('#reviewComment').fill('Проверить формулировку');
  await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', {
    configurable: true, value: { writeText: async (text) => { window.copiedReview = text; } },
  }));
  await page.locator('#reviewCopy').click();
  const copied = await page.evaluate(() => window.copiedReview);
  assert.ok(copied.includes((await reviewEntries(page))[0].questionId));
  assert.match(copied, /Проверить формулировку/);
  await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', {
    configurable: true, value: { writeText: async () => { throw new Error('denied'); } },
  }));
  await page.locator('#reviewCopy').click();
  await page.locator('#reviewCopyText').waitFor();
  assert.equal(await page.locator('#reviewCopyText').inputValue(), copied);
});

/** Ответ на вопрос на экране и переход дальше; record — запись банка (см. currentRecord). */
async function answerAndNext(page, bank, correct) {
  const record = await currentRecord(page, bank);
  await answer(page, record, correct);
  await page.locator('#nextButton').click();
  return record;
}

/** Телефон: пиньинь и вопрос по-китайски — в меню «Вид». */
async function viewMenuItem(page, id) {
  if (!(await page.locator('#viewMenu').isVisible())) await page.locator('#viewToggle').click();
  await page.locator(`#${id}`).click();
}

test('главная открывается без ошибок и считает банк', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  assert.ok(bank.length > 400);
  assert.equal(await page.locator('#bankCount').textContent(), `Пройдено 0 из ${bank.length}`);
  // числа банка — в подвале, а не над заголовком
  const seasons = new Set(bank.flatMap((r) => r.occurrences.map((o) => o.year))).size;
  const footer = await page.locator('#footerNote').textContent();
  assert.match(footer, new RegExp(`^В базе ${bank.length} вопрос\\S*: \\d+ из заданий ВсОШ за ${seasons} сезон`), footer);
  assert.match(footer, /, 7 тем\. /, footer);
  // первый визит: заголовок, вводный абзац и кнопка первого раунда; надзаголовка и ряда чисел нет
  assert.equal(await page.locator('#firstHero').isVisible(), true);
  assert.equal(await page.locator('#nextRound').isVisible(), false);
  assert.equal(await page.locator('#setupView .ink-eyebrow, #setupView .stats').count(), 0);
  assert.equal(await page.locator('#firstStart').textContent(), 'Начать первый раунд');
  assert.equal(await page.locator('#firstStart').isEnabled(), true);
  assert.equal(await page.locator('#firstCaption').textContent(),
    '10 случайных вопросов из всех тем. Режим, формат и темы — ниже.');
  assert.equal(await page.locator('#setupView .ink-btn--primary:visible').count(), 1);
  const description = await page.locator('meta[name="description"]').getAttribute('content');
  assert.ok(description.startsWith(`${bank.length} `), description);
  assert.deepEqual(page.errors, []);
});

test('главная после первых ответов: «Следующий раунд», быстрые входы, длина в строке настроек', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  // длина раунда — в подписи первого визита
  await page.locator('input[name="roundSize"][value="20"]').check();
  assert.equal(await page.locator('#firstCaption').textContent(),
    '20 случайных вопросов из всех тем. Режим, формат и темы — ниже.');
  await page.locator('input[name="roundSize"][value="all"]').check();
  assert.match(await page.locator('#firstCaption').textContent(), /^Все вопросы базы в случайном порядке\./);
  // одна ошибка в прогрессе: главная — «Следующий раунд»
  const record = bank.find((r) => r.answer.state === 'verified');
  await page.evaluate((id) => localStorage.setItem('lingvo-trainer:v1', JSON.stringify({
    version: 1, progress: { [id]: { attempts: 1, correct: 0, completed: true, lastCorrect: false, box: 0, dueAt: 0 } },
  })), record.id);
  await page.reload();
  assert.equal(await page.locator('#firstHero').isVisible(), false);
  assert.equal(await page.locator('#nextTitle').textContent(), 'Следующий раунд');
  await page.locator('input[name="roundSize"][value="5"]').check();
  assert.equal(await page.locator('#nextSummary').textContent(), 'Все вопросы, выбор ответа, 5 вопросов, все темы.');
  const all = eligible(bank, ALL, {}).length;
  assert.equal(await page.locator('#eligibleNotice').textContent(), `Подходит вопросов: ${all}, в раунде будет 5.`);
  assert.equal(await page.locator('#setupView .ink-btn--primary:visible').count(), 1);
  // быстрые входы: «Ошибки» и «Пора повторить» — с числом; режим главной они не меняют
  assert.equal(await page.locator('#quickMistakes').isVisible(), true);
  assert.equal(await page.locator('#quickMistakes .quick-number').textContent(), '1');
  assert.equal(await page.locator('#quickMistakes .quick-unit').textContent(), 'вопрос');
  assert.equal(await page.locator('#quickDue .quick-number').textContent(), '1');
  await page.locator('#quickMistakes').click();
  await page.locator('#quizView').waitFor();
  assert.equal(await page.locator('#progressLabel').textContent(), 'Вопрос 1 из 1');
  assert.equal((await currentRecord(page, bank)).id, record.id);
  assert.equal(await page.evaluate(() => state.filters.mode), 'all');
  // без ошибок и сроков быстрых входов нет
  await page.evaluate((id) => localStorage.setItem('lingvo-trainer:v1', JSON.stringify({
    version: 1, progress: { [id]: { attempts: 1, correct: 1, completed: true, lastCorrect: true, box: 1, dueAt: Date.now() + 1e9 } },
  })), record.id);
  await page.evaluate(() => sessionStorage.clear());
  await page.goto(baseUrl);
  await page.reload();
  assert.equal(await page.locator('#nextMain').isVisible(), true);
  assert.equal(await page.locator('#quickStarts').isVisible(), false);
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
  assert.equal(await page.locator('#resultText').textContent(), 'Вопросы с ошибками вернутся в режиме «Ошибки» и при повторении.');
  assert.equal(await page.locator('#repeatMistakes').textContent(), 'Повторить ошибки раунда (1)');
  // в итогах — ошибка с ответом ученика и верным ответом, и одна главная кнопка
  const wrongRecord = bank.find((r) => r.id === wrongId);
  const mistakes = page.locator('#mistakeList > li');
  assert.equal(await mistakes.count(), 1);
  const mistake = await mistakes.first().locator('.mistake-head').textContent();
  assert.ok(mistake.includes(wrongRecord.questionRu), mistake);
  assert.ok(mistake.includes(`✕ ${wrongPick}`), mistake);
  const right = wrongRecord.options.find((o) => o.id === wrongRecord.answer.optionId).zh;
  assert.ok(mistake.includes(`✓ ${right}`), mistake);
  assert.equal(await page.locator('#resultsView .ink-btn--primary:visible').count(), 1);
  assert.equal(await page.locator('#repeatMistakes').getAttribute('class'), 'ink-btn ink-btn--primary');
  assert.match(await page.locator('#newRound').getAttribute('class'), /ink-btn--secondary/);
  assert.equal(await page.locator('#newRoundNote').textContent(), 'Новый раунд — снова 10 вопросов, все вопросы, все темы.');
  // совета заглянуть в базу и ссылки на неё в итогах больше нет
  assert.doesNotMatch(await page.locator('#resultsView .results-score').textContent(), /базу/);

  await page.locator('#repeatMistakes').click();
  assert.equal(await page.locator('#progressLabel').textContent(), 'Вопрос 1 из 1');
  assert.equal((await currentRecord(page, bank)).id, wrongId);
  assert.deepEqual(page.errors, []);
});

test('клавиатура: цифра отвечает, Enter ведёт дальше, Esc выходит', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  // Esc без ответов — на главную, и раунд не остаётся незаконченным
  await page.keyboard.press('Enter');
  await page.locator('#quizView').waitFor();
  await page.keyboard.press('Escape');
  await page.locator('#setupView').waitFor();
  assert.equal(await page.locator('#resumePanel').isVisible(), false);
  await page.keyboard.press('Enter');
  await page.locator('#quizView').waitFor();
  await page.keyboard.press('Digit1');
  await page.locator('#nextButton:not(.hidden)').waitFor();
  assert.equal(await page.locator('#options button:not(:disabled)').count(), 0);
  await page.keyboard.press('Enter');
  assert.match(await page.locator('#progressLabel').textContent(), /^Вопрос 2 из/);
  // Esc после ответа — итоги по отвеченным, второй Esc — главная
  await page.keyboard.press('Escape');
  await page.locator('#resultsView').waitFor();
  assert.match(await page.locator('#finalScore').textContent(), /^[01] \/ 1$/);
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
  await page.locator('#resultsView').waitFor();
  await page.locator('#backToSetup').click();
  await page.reload();
  assert.equal(await page.locator('#bankCount').textContent(), `Пройдено 1 из ${bank.length}`);
  await page.locator('#setupView .mode-option', { hasText: 'Ошибки' }).click();
  assert.equal(await page.locator('#eligibleNotice').textContent(), 'Подходит вопросов: 1, в раунде будет 1.');
  assert.deepEqual(page.errors, []);
});

test('фильтр по теме считает вопросы темы', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  const topic = 'История и государство';
  const expected = eligible(bank, { ...ALL, topics: [topic] }, {}).length;
  await page.locator('#topicControls label', { hasText: topic }).locator('input').check();
  const notice = `Подходит вопросов: ${expected}, в раунде будет 10.`;
  assert.equal(await page.locator('#eligibleNotice').textContent(), notice);
  // первый визит: настройки тронуты — под кнопкой строка настроек и счёт
  assert.equal(await page.locator('#firstCaption').textContent(),
    `Все вопросы, выбор ответа, 10 вопросов, раздел: история. ${notice}`);
  assert.equal(await page.locator('#topicControls label', { hasText: topic }).locator('.topic-progress').textContent(),
    `0/${expected}`);
  await page.locator('#clearFilters').click();
  assert.equal(await page.locator('#eligibleNotice').textContent(),
    `Подходит вопросов: ${eligible(bank, ALL, {}).length}, в раунде будет 10.`);
  assert.deepEqual(page.errors, []);
});

test('числа на пилюлях режима считаются под фильтры', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  const modes = ['all', 'new', 'mistakes', 'due'];
  const counts = () => page.locator('input[name="studyMode"] + .ink-pill .pill-count').allTextContents();
  const expected = (filters, progress) => modes.map((mode) => String(eligible(bank, { ...filters, mode }, progress).length));
  assert.deepEqual(await counts(), expected(ALL, {}));
  const topic = 'Россия и межкультурный блок';
  await page.locator('#topicControls label', { hasText: topic }).locator('input').check();
  assert.deepEqual(await counts(), expected({ ...ALL, topics: [topic] }, {}));
  // ошибка по теме — в «Ошибках» и в «Повторении»; в заголовок свёрнутого режима число не идёт
  const record = bank.find((r) => r.topic === topic && r.answer.state === 'verified');
  const progress = { [record.id]: { attempts: 1, correct: 0, completed: true, lastCorrect: false, box: 0, dueAt: 0 } };
  await page.evaluate((value) => localStorage.setItem('lingvo-trainer:v1', JSON.stringify({ version: 1, progress: value })), progress);
  await page.reload();
  assert.deepEqual(await counts(), expected({ ...ALL, topics: [topic] }, progress));
  assert.deepEqual((await counts()).slice(2), ['1', '1']);
  assert.equal(await page.locator('#modeValue').textContent(), 'Все вопросы');
  assert.deepEqual(page.errors, []);
});

test('база: поиск по-китайски и раскрытие ответа', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  await page.locator('#navDatabase').click();
  await page.locator('#databaseView').waitFor();
  await page.locator('#databaseSearch').fill('颐和园');
  assert.match(await page.locator('#foundCount').textContent(), /^Найден[о]? [1-9]\d* вопрос/);
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
    // русское название верного ответа здесь не проверяется — его отдельный тест
    delete target.answer.gloss;
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
  await page.locator('#resultsView').waitFor();
  await page.locator('#navDatabase').click();
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
  // банк страницы, а не data/bank.json: часть записей data/site.json не пускает на сайт
  const bank = await bankOf(page);
  const record = bank.find((r) => r.options.filter((o) => o.gloss).length === 3);
  assert.ok(record, 'в банке нет вопроса с подписями у всех трёх неверных вариантов');
  await page.evaluate((id) => startRoundWith([QUESTION_BANK.find((r) => r.id === id)]), record.id);
  await page.locator(`#options button[data-option-id="${record.answer.optionId}"]`).click();
  for (const option of record.options) {
    // под верным вариантом — русское название ответа, если оно есть (у вопросов досье)
    const gloss = option.id === record.answer.optionId ? record.answer.gloss : option.gloss;
    const note = page.locator(`#options button[data-option-id="${option.id}"] .option-gloss`);
    assert.equal(await note.count(), gloss ? 1 : 0, `${record.id}/${option.id}: число подписей`);
    if (gloss) assert.equal(await note.textContent(), gloss, `${record.id}/${option.id}`);
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
  assert.equal(await page.locator('#eligibleNotice').textContent(), 'Подходит вопросов: 1, в раунде будет 1.');

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
  await page.locator('#resultsView').waitFor();
  await page.locator('#navDatabase').click();
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
  await page.locator('#resultsView').waitFor();
  assert.equal(await overflow(), 0, 'итоги с раскрытой ошибкой');
  await page.locator('#navDatabase').click();
  const first = page.locator('#databaseList article').first();
  await first.locator('summary').click();
  assert.equal(await first.locator('.row-answer').isVisible(), true, 'ответ в базе не раскрылся');
  assert.equal(await overflow(), 0, 'база с раскрытым ответом');
  // главная после первого ответа: «Следующий раунд», быстрые входы и открытое меню «Вид»
  await page.locator('#navSetup').click();
  await page.locator('#viewToggle').click();
  assert.equal(await page.locator('#quickMistakes').isVisible(), true);
  assert.equal(await overflow(), 0, 'главная с быстрыми входами');
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
  await page.locator('#resultsView').waitFor();
  await page.locator('#backToSetup').click();
  await page.locator('#setupView .mode-option', { hasText: 'Ошибки' }).click();
  assert.equal(await page.locator('#eligibleNotice').textContent(), 'Подходит вопросов: 1, в раунде будет 1.');
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
  const record = await currentRecord(page, bank);
  // в банке есть задания с тремя вариантами
  assert.equal(await page.locator('#options button').count(), Math.min(4, record.options.length));
  assert.match(await page.locator('#recallNote').textContent(), /«вспомнил неточно»/);
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
  const record = await currentRecord(page, await bankOf(page));
  assert.equal(await page.locator('#options button').count(), Math.min(4, record.options.length));
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
  assert.match(await page.locator('#mistakeList > li').first().textContent(), /«(не)?верно» для/);
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
  await page.locator('#resultsView').waitFor();
  await page.locator('#backToSetup').click();
  assert.equal(await page.locator('#eligibleNotice').textContent(), 'Подходит вопросов: 1, в раунде будет 1.');
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

/** Ответ на задание на экране (верный или любой неверный); возвращает запись банка. */
async function cyAnswer(page, bank, correct) {
  const record = await currentChengyu(page, bank);
  const optionId = correct ? record.answer : record.options.find((o) => o.id !== record.answer).id;
  await page.locator(`#cyOptions button[data-option-id="${optionId}"]`).click();
  return record;
}

/** Ответ и переход к следующему заданию (или к итогам). */
async function cyAnswerAndNext(page, bank, correct) {
  const record = await cyAnswer(page, bank, correct);
  await page.locator('#cyNextButton').click();
  return record;
}

/** Раунд из начала раздела: кнопка наверху — «Начать первый раунд» или «Начать раунд». */
async function cyStartRound(page, size) {
  await page.locator(`input[name="cySize"][value="${size}"]`).check();
  await page.locator('#cyFirstStart:visible, #cyStartButton:visible').click();
  await page.locator('#cyQuizView').waitFor();
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
  // в шапке раздела — его счёт, а не прогресс основного банка
  assert.equal(await page.locator('#bankCount').textContent(), `Решено 0 из ${bank.length}`);
  await cyStartRound(page, 5);
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
    // удар печати — только в основном раунде: «Чэнъюй» пока без движения
    assert.deepEqual(await cssAnimations(page), []);
    assert.match(await page.locator('#cyFeedback').textContent(), /Смысл/);
    if (!correct) wrongRecord = record;
    await page.keyboard.press('Enter');
  }
  await page.locator('#cyResultsView').waitFor();
  assert.match(await page.locator('#cyFinalScore').textContent(), /^4\s*\/ 5$/);
  assert.equal(await page.locator('#bankCount').textContent(), `Решено 5 из ${bank.length}`);
  assert.equal(await page.locator('#cyMistakeList > li').count(), 1);
  assert.equal(await page.locator('#cyRepeatMistakes').isVisible(), true);

  // ошибка сохранилась: набор «Ошибки» находит ровно это задание
  await page.locator('#cyBackToSetup').click();
  await page.locator('#cySetupView .mode-option', { hasText: 'Ошибки' }).click();
  assert.equal(await page.locator('#cyEligibleNotice').textContent(), 'Подходит заданий: 1, в раунде будет 1.');
  const stored = await page.evaluate(() => JSON.parse(localStorage.getItem('lingvo-trainer:chengyu:v1')));
  assert.equal(stored.progress[wrongRecord.id].lastCorrect, false);
  // прогресс основного раздела не тронут
  assert.equal(await page.evaluate(() => localStorage.getItem('lingvo-trainer:v1')), null);

  await page.locator('#cyQuickReference').click();
  await page.locator('#cyReferenceView').waitFor();
  assert.equal(hashOf(page), '#chengyu/reference');
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
  assert.match(await page.locator('#bankCount').textContent(), /^Пройдено 0 из \d+$/);
  await page.reload();
  assert.equal(await page.locator('#setupView').isVisible(), true);
  assert.deepEqual(page.errors, []);
});

test('чэнъюй: ссылка #chengyu открывает раздел, телефон без горизонтальной прокрутки', LIMIT, async (t) => {
  const page = await openPage(t, { width: 360, height: 780 });
  if (!page) return;
  await page.goto(`${baseUrl}#chengyu`);
  await page.locator('#cySetupView').waitFor();
  // и при загрузке страницы сразу по такой ссылке: адрес не теряется
  await page.reload();
  await page.locator('#cySetupView').waitFor();
  assert.equal(hashOf(page), '#chengyu');
  const overflow = () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.equal(await overflow(), 0, 'начало раздела');
  await cyStartRound(page, 'all');
  assert.equal(await page.locator('#cyProgressTrack').isVisible(), true, 'длинный раунд — полоса, а не кружки');
  await page.locator('#cyOptions button').first().click();
  assert.equal(await overflow(), 0, 'задание с разбором');
  await page.locator('#cyLeaveRound').click();
  await page.locator('#cyResultsView').waitFor();
  assert.equal(await overflow(), 0, 'итоги с раскрытой ошибкой');
  await page.locator('#cyResultsReference').click();
  await page.locator('#cyReferenceList article summary').first().click();
  assert.equal(await overflow(), 0, 'справочник');
  assert.deepEqual(page.errors, []);
});

test('чэнъюй: первый визит, «Следующий раунд» с быстрыми входами, числа на пилюлях и в подвале', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await page.evaluate(() => CHENGYU_BANK);
  await openChengyu(page);
  // первый визит: заголовок, вводный абзац и кнопка — одним блоком; ряда чисел и надписи над заголовком нет
  assert.equal(await page.locator('#cyFirstHero').isVisible(), true);
  assert.equal(await page.locator('#cyNextRound').isVisible(), false);
  assert.equal(await page.locator('#cySetupView .ink-eyebrow, #cySetupView .stats').count(), 0);
  assert.equal(await page.locator('#cyFirstCaption').textContent(), '10 случайных заданий из всех тем. Набор, темы и длина — ниже.');
  assert.equal(await page.locator('#cySetupView .ink-btn--primary:visible').count(), 1);
  // «Как не попасться на ложного друга» — ниже кнопки
  const button = await page.locator('#cyFirstStart').boundingBox();
  const steps = await page.locator('.cy-steps').boundingBox();
  assert.ok(steps.y > button.y + button.height, 'советы под кнопкой');
  // числа — в подвале
  const olympiad = bank.filter((r) => r.occurrences?.length).length;
  assert.equal(await page.locator('#footerNote').textContent(),
    `В разделе ${bank.length} заданий: ${olympiad} из вариантов ВсОШ за 8 сезонов и ${bank.length - olympiad} составленных`
    + ' по той же схеме и сверенных со словарями, 8 тем.');
  const pills = () => page.locator('#cySetupView .mode-option .pill-count').allTextContents();
  assert.deepEqual(await pills(), [String(bank.length), String(bank.length), '0']);

  // после раунда с ошибкой: «Следующий раунд», быстрый вход «Ошибки», числа на пилюлях
  await cyStartRound(page, 5);
  await cyAnswerAndNext(page, bank, false);
  for (let n = 0; n < 4; n += 1) await cyAnswerAndNext(page, bank, true);
  await page.locator('#cyBackToSetup').click();
  await page.locator('#cySetupView').waitFor();
  assert.equal(await page.locator('#cyFirstHero').isVisible(), false);
  assert.equal(await page.locator('#cyNextMain').isVisible(), true);
  assert.equal(await page.locator('#cyNextSummary').textContent(), 'Все задания, 5 заданий, все темы.');
  assert.equal(await page.locator('#cyEligibleNotice').textContent(), `Подходит заданий: ${bank.length}, в раунде будет 5.`);
  assert.deepEqual(await pills(), [String(bank.length), String(bank.length - 5), '1']);
  assert.equal(await page.locator('#cyQuickMistakes').isVisible(), true);
  assert.equal(await page.locator('#cyQuickMistakes .quick-count').textContent(), '1задание');
  assert.equal(await page.locator('#cyQuickReference .quick-number').textContent(), String(bank.length));
  // строка настроек следует за темами и набором; быстрый вход — раунд из ошибок, набор не меняется
  await page.locator('#cyGroupControls label').first().click();
  assert.match(await page.locator('#cyNextSummary').textContent(), /^Все задания, 5 заданий, тема «Труд и старание»\.$/);
  await page.locator('#cyGroupControls label').first().click();
  // «Настроить раунд» — к «Набору», фокус на выбранном наборе; адрес не меняется
  await page.locator('#cySettingsLink').click();
  assert.equal(await page.evaluate(() => document.activeElement.name + ':' + document.activeElement.value), 'cyMode:all');
  assert.equal(hashOf(page), '#chengyu');
  await page.locator('#cyQuickMistakes').click();
  await page.locator('#cyQuizView').waitFor();
  assert.equal(await page.locator('#cyProgressLabel').textContent(), 'Задание 1 из 1');
  await page.goBack();
  await page.locator('#cySetupView').waitFor();
  assert.equal(await page.locator('input[name="cyMode"]:checked').getAttribute('value'), 'all');
  // набор без подходящих заданий: главная кнопка — «Начать обычный раунд» (все задания всех тем)
  await page.evaluate(() => { cy.progress = {}; cyDiscardRound(); });
  await page.locator('#cySetupView .mode-option', { hasText: 'Новые' }).click();
  await page.evaluate(() => { for (const r of CHENGYU_BANK) cy.progress[r.id] = { attempts: 1, correct: 1, lastCorrect: true }; cyRenderSetup(); });
  assert.equal(await page.locator('#cyEligibleNotice').textContent(), 'Под выбранные условия нет заданий. Выберите другие темы или набор.');
  assert.equal(await page.locator('#cyStartButton').isDisabled(), true);
  assert.equal(await page.locator('#cySetupView .ink-btn--primary:visible').count(), 1);
  await page.locator('#cyEmptyAll').click();
  await page.locator('#cyQuizView').waitFor();
  assert.equal(await page.locator('#cyProgressLabel').textContent(), 'Задание 1 из 5');
  assert.equal(await page.evaluate(() => cy.filters.mode), 'all');
  assert.deepEqual(page.errors, []);
});

test('чэнъюй: «назад» из раунда, итогов и справочника ведёт к началу раздела; незаконченный раунд продолжается', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await page.evaluate(() => CHENGYU_BANK);
  await openChengyu(page);
  assert.equal(hashOf(page), '#chengyu');
  await cyStartRound(page, 10);
  assert.equal(hashOf(page), '#chengyu/round');
  await cyAnswerAndNext(page, bank, true);
  const second = await cyAnswer(page, bank, false);
  await page.goBack();
  await page.locator('#cySetupView').waitFor();
  assert.equal(hashOf(page), '#chengyu');
  // вместо «Следующего раунда» — плашка: ход раунда и две кнопки, главная из них одна
  assert.equal(await page.locator('#cyNextMain').isVisible(), false);
  assert.equal(await page.locator('#cyResumePanel').isVisible(), true);
  assert.equal(await page.locator('#cyResumeProgress').textContent(), 'Задание 2 из 10, верно 1.');
  assert.equal(await page.locator('#cyResumeSettings').textContent(), ' Все задания, все темы.');
  assert.equal(await page.locator('#cyResumeSteps li.ink-step--correct').count(), 1);
  assert.equal(await page.locator('#cyResumeSteps li.ink-step--wrong').count(), 1);
  assert.equal(await page.locator('#cyResumeSaved').textContent(), 'Ответы на первые два задания уже сохранены в прогрессе.');
  assert.equal(await page.locator('#cySetupView .ink-btn--primary:visible').count(), 1);
  // «вперёд» и Enter на плашке возвращают в тот же раунд, к тому же разбору
  await page.goForward();
  await page.locator('#cyQuizView').waitFor();
  assert.equal(await page.locator('#cyProgressLabel').textContent(), 'Задание 2 из 10');
  await page.goBack();
  await page.locator('#cySetupView').waitFor();
  await page.keyboard.press('Enter');
  await page.locator('#cyQuizView').waitFor();
  assert.equal((await currentChengyu(page, bank)).id, second.id);
  assert.equal(await page.locator('#cyFeedback.bad').isVisible(), true, 'разбор ответа остался на месте');
  // итоги: «назад» — к началу раздела, раунд закончен, плашки нет
  await page.keyboard.press('Escape');
  await page.locator('#cyResultsView').waitFor();
  assert.equal(hashOf(page), '#chengyu/results');
  await page.goBack();
  await page.locator('#cySetupView').waitFor();
  assert.equal(await page.locator('#cyNextMain').isVisible(), true);
  assert.equal(await page.locator('#cyResumePanel').isVisible(), false);
  // справочник: «назад» — к началу раздела
  await page.locator('#cyQuickReference').click();
  await page.locator('#cyReferenceView').waitFor();
  assert.equal(hashOf(page), '#chengyu/reference');
  await page.goBack();
  await page.locator('#cySetupView').waitFor();
  assert.equal(hashOf(page), '#chengyu');
  // «Закончить раунд» без ответов — к началу раздела, раунд не остаётся незаконченным
  await cyStartRound(page, 5);
  await page.locator('#cyLeaveRound').click();
  await page.locator('#cySetupView').waitFor();
  assert.equal(await page.locator('#cyResumePanel').isVisible(), false);
  // переход шапкой в «Тренировку» и обратно: «назад» ведёт на прежний экран, а не в раунд «Чэнъюй»
  await page.locator('#navSetup').click();
  await page.locator('#setupView').waitFor();
  assert.equal(hashOf(page), '');
  await page.goBack();
  await page.locator('#cySetupView').waitFor();
  assert.equal(hashOf(page), '#chengyu');
  assert.deepEqual(page.errors, []);
});

test('переходы шапкой между разделами: раунд каждого раздела — своя запись, «назад» ведёт к началу раздела', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await page.evaluate(() => CHENGYU_BANK);
  const mainBank = await bankOf(page);
  // из итогов основного раунда в «Чэнъюй»: «назад» из раунда «Чэнъюй» — к началу раздела, а не на главную
  await startRound(page, 5);
  await page.keyboard.press('Escape');
  await page.locator('#setupView').waitFor();
  await openChengyu(page);
  await cyStartRound(page, 5);
  await page.goBack();
  await page.locator('#cySetupView').waitFor();
  assert.equal(hashOf(page), '#chengyu');
  // плашка: продолжить и выйти без ответов — раунд не остаётся незаконченным
  await page.keyboard.press('Enter');
  await page.locator('#cyQuizView').waitFor();
  await page.keyboard.press('Escape');
  await page.locator('#cySetupView').waitFor();
  // три раза: итоги раунда «Чэнъюй», «Тренировка», итоги основного раунда, снова «Чэнъюй»
  for (let n = 0; n < 3; n += 1) {
    await openChengyu(page);
    await cyStartRound(page, 5);
    await cyAnswer(page, bank, true);
    await page.locator('#cyLeaveRound').click();
    await page.locator('#cyResultsView').waitFor();
    await page.locator('#navSetup').click();
    await page.locator('#setupView').waitFor();
    await startButton(page).click();
    await page.locator('#quizView').waitFor();
    await answer(page, await currentRecord(page, mainBank), true);
    await page.keyboard.press('Escape');
    await page.locator('#resultsView').waitFor();
  }
  // каждое «назад» меняет экран: двух записей одного экрана подряд нет
  const screens = [await page.evaluate(() => `${state.view} ${location.hash}`)];
  for (let n = 0; n < 4; n += 1) {
    await page.goBack();
    await page.waitForFunction((last) => `${state.view} ${location.hash}` !== last, screens.at(-1));
    screens.push(await page.evaluate(() => `${state.view} ${location.hash}`));
  }
  assert.deepEqual(screens, ['results #results', 'setup ', 'cy-setup #chengyu', 'setup ', 'cy-setup #chengyu']);
  // итоги «Чэнъюй» → «Тренировка» → снова «Чэнъюй»: новый раунд — новая запись, «назад» — к началу раздела
  await cyStartRound(page, 5);
  await cyAnswer(page, bank, true);
  await page.locator('#cyLeaveRound').click();
  await page.locator('#cyResultsView').waitFor();
  await page.locator('#navSetup').click();
  await page.locator('#setupView').waitFor();
  await openChengyu(page);
  await cyStartRound(page, 5);
  await page.goBack();
  await page.locator('#cySetupView').waitFor();
  assert.equal(hashOf(page), '#chengyu');
  assert.deepEqual(page.errors, []);
});

test('чэнъюй: перезагрузка посреди раунда возвращает на то же задание, итоги — на итоги', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await page.evaluate(() => CHENGYU_BANK);
  await openChengyu(page);
  await cyStartRound(page, 5);
  const wrong = await cyAnswerAndNext(page, bank, false);
  const second = await currentChengyu(page, bank);
  await page.reload();
  await page.locator('#cyQuizView').waitFor();
  assert.equal(hashOf(page), '#chengyu/round');
  assert.equal(await page.locator('#cyProgressLabel').textContent(), 'Задание 2 из 5');
  assert.equal((await currentChengyu(page, bank)).id, second.id);
  assert.equal(await page.locator('#cyProgressSteps li.ink-step--wrong').count(), 1);
  assert.equal(await page.locator('#bankCount').textContent(), `Решено 1 из ${bank.length}`);
  // отвеченное задание второй раз не задаётся: после перезагрузки — следующее
  await cyAnswer(page, bank, true);
  await page.reload();
  await page.locator('#cyQuizView').waitFor();
  assert.equal(await page.locator('#cyProgressLabel').textContent(), 'Задание 3 из 5');
  for (let n = 0; n < 3; n += 1) await cyAnswerAndNext(page, bank, true);
  await page.locator('#cyResultsView').waitFor();
  assert.match(await page.locator('#cyFinalScore').textContent(), /^4\s*\/ 5$/);
  await page.reload();
  await page.locator('#cyResultsView').waitFor();
  assert.equal(hashOf(page), '#chengyu/results');
  assert.match(await page.locator('#cyFinalScore').textContent(), /^4\s*\/ 5$/);
  assert.ok((await page.locator('#cyMistakeList').textContent()).includes(wrong.kind === 'reverse' ? wrong.prompt : wrong.chengyu));
  // «назад» после перезагрузки итогов ведёт к началу раздела
  await page.goBack();
  await page.locator('#cySetupView').waitFor();
  assert.deepEqual(page.errors, []);
});

test('чэнъюй: «Закончить раунд» — итоги по отвеченным, ошибки раскрываются, «Новый раунд» и «Повторить ошибки»', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await page.evaluate(() => CHENGYU_BANK);
  // обратное задание с подписями неверных вариантов (подписи есть только у них) и прямое
  const picked = [
    bank.find((r) => r.kind === 'reverse' && r.options.some((o) => o.id !== r.answer && o.gloss)),
    bank.find((r) => r.kind === 'analog'),
  ];
  assert.ok(picked.every(Boolean));
  await openChengyu(page);
  await page.locator('input[name="cySize"][value="20"]').check();
  await page.evaluate((ids) => cyStartRoundWith(ids.map((id) => CHENGYU_BANK.find((r) => r.id === id)).concat(
    CHENGYU_BANK.filter((r) => !ids.includes(r.id)).slice(0, 3))), picked.map((r) => r.id));
  const wrongOptions = [];
  for (const record of picked) {
    const wrong = record.options.find((o) => o.id !== record.answer && (o.gloss || record.kind === 'analog'));
    wrongOptions.push(wrong);
    await page.locator(`#cyOptions button[data-option-id="${wrong.id}"]`).click();
    await page.locator('#cyNextButton').click();
  }
  await cyAnswer(page, bank, true);
  await page.locator('#cyLeaveRound').click();
  await page.locator('#cyResultsView').waitFor();
  assert.equal(hashOf(page), '#chengyu/results');
  assert.match(await page.locator('#cyFinalScore').textContent(), /^1\s*\/ 3$/, 'по отвеченным, а не по всему раунду');
  assert.equal(await page.locator('#cyRepeatMistakes').textContent(), 'Повторить ошибки раунда (2)');
  assert.equal(await page.locator('#cyNewRoundNote').textContent(), 'Новый раунд — снова 20 заданий, все задания, все темы.');
  assert.equal(await page.locator('#cyResultsView .ink-btn--primary:visible').count(), 1);
  assert.equal(await page.locator('#cyResultsReference').textContent(), 'Открыть справочник чэнъюй');
  const heads = page.locator('#cyMistakeList .mistake-head');
  const panels = page.locator('#cyMistakeList .mistake-panel');
  assert.equal(await heads.count(), 2);
  assert.equal(await heads.nth(0).getAttribute('aria-expanded'), 'true');
  assert.equal(await panels.nth(1).isVisible(), false);
  assert.ok((await heads.nth(0).textContent()).includes(`Ваш ответ ✕ ${wrongOptions[0].text}, верно ✓ `));
  assert.deepEqual(await panels.nth(0).locator('.cy-facts dt').allTextContents(), ['Ответ', 'Смысл', 'Ловушка']);
  assert.equal(await panels.nth(0).locator('.mistake-gloss').textContent(),
    `Ваш ответ ${wrongOptions[0].text} — ${wrongOptions[0].gloss.replace(/\.$/, '')}.`);
  // с клавиатуры: Enter раскрывает вторую ошибку и сворачивает первую; у прямого — буквально, смысл, ловушка
  await heads.nth(1).focus();
  await page.keyboard.press('Enter');
  assert.equal(await panels.nth(1).isVisible(), true);
  assert.equal(await panels.nth(0).isVisible(), false);
  assert.deepEqual((await panels.nth(1).locator('.cy-facts dt').allTextContents()).slice(0, 3), ['Буквально', 'Смысл', 'Ловушка']);
  assert.equal(await panels.nth(1).locator('.cy-facts dd').nth(1).textContent(), picked[1].meaning);
  assert.ok((await heads.nth(1).textContent()).includes(`Ваш ответ ✕ ${wrongOptions[1].text}, верно ✓ `));
  // «Повторить ошибки» — раунд из двух ошибок, той же записью истории
  const historyLength = await page.evaluate(() => history.length);
  await page.locator('#cyRepeatMistakes').click();
  await page.locator('#cyQuizView').waitFor();
  assert.equal(await page.evaluate(() => history.length), historyLength);
  assert.equal(await page.locator('#cyProgressLabel').textContent(), 'Задание 1 из 2');
  await cyAnswerAndNext(page, bank, true);
  await cyAnswerAndNext(page, bank, true);
  await page.locator('#cyResultsView').waitFor();
  // без ошибок: главная кнопка — «Новый раунд»; он повторяет настройки раунда, а не раздела
  assert.equal(await page.locator('#cyResultText').textContent(), 'Весь раунд без ошибок.');
  assert.equal(await page.locator('#cyRepeatMistakes').isVisible(), false);
  assert.equal(await page.locator('#cyResultMistakes').isVisible(), false);
  assert.match(await page.locator('#cyNewRound').getAttribute('class'), /ink-btn--primary/);
  await page.evaluate(() => { cy.size = 5; });
  await page.locator('#cyNewRound').click();
  await page.locator('#cyQuizView').waitFor();
  assert.equal(await page.locator('#cyProgressLabel').textContent(), 'Задание 1 из 20');
  await page.goBack();
  await page.locator('#cySetupView').waitFor();
  assert.deepEqual(page.errors, []);
});

test('чэнъюй, телефон: кнопка раунда внизу — только когда верхняя ушла за край экрана', LIMIT, async (t) => {
  const page = await openPage(t, { width: 375, height: 812 });
  if (!page) return;
  const bank = await page.evaluate(() => CHENGYU_BANK);
  await openChengyu(page);
  const bar = page.locator('#cyStartBar');
  const shownBar = () => page.waitForFunction(() => {
    const element = document.getElementById('cyStartBar');
    return element.classList.contains('is-shown') && element.getBoundingClientRect().bottom <= innerHeight + 0.5;
  });
  assert.equal(await bar.isVisible(), false);
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  await shownBar();
  assert.equal(await page.locator('#cyStartBarText').textContent(), `Все темы, 10 из ${bank.length} подходящих`);
  // полоса не закрывает подвал
  const footer = await page.locator('.ink-footer p').last().boundingBox();
  assert.ok(footer.y + footer.height <= (await bar.boundingBox()).y, 'подвал под полосой');
  await page.locator('#cyBarStart').click();
  await page.locator('#cyQuizView').waitFor();
  assert.equal(await bar.isVisible(), false);
  // при плашке «Раунд не закончен» полосы нет
  await cyAnswer(page, bank, true);
  await page.goBack();
  await page.locator('#cyResumePanel').waitFor();
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  assert.equal(await page.evaluate(() => document.getElementById('cyStartBar').classList.contains('is-shown')), false);
  // полоса основного раздела в «Чэнъюй» не появляется, и наоборот
  assert.equal(await page.evaluate(() => document.getElementById('startBar').classList.contains('is-shown')), false);
  await page.locator('#navSetup').click();
  await page.locator('#setupView').waitFor();
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  await page.waitForFunction(() => document.getElementById('startBar').classList.contains('is-shown'));
  assert.equal(await page.evaluate(() => document.getElementById('cyStartBar').classList.contains('is-shown')), false);
  assert.deepEqual(page.errors, []);
});

test('фильтр «Откуда вопросы» и пиньинь: раунд из дополнений, транскрипция из меню «Вид»', LIMIT, async (t) => {
  const page = await openPage(t, { width: 375, height: 812 });
  if (!page) return;
  const bank = await page.evaluate(() => QUESTION_BANK);
  const additions = bank.filter((record) => record.origin === 'addition').length;
  await page.locator('input[name="studyOrigin"][value="addition"]').check({ force: true });
  assert.match(await page.locator('#eligibleNotice').textContent(), new RegExp(`: ${additions},`));
  await startButton(page).click();
  await page.locator('#quizView').waitFor();
  // над дополнением одна метка «Дополнение», без «Проверенного дополнения» рядом
  assert.equal(await page.locator('#sourceLabel').isVisible(), false);
  assert.equal(await page.locator('#originPill').textContent(), 'Дополнение');
  assert.equal(await page.locator('#originPill').isVisible(), true);
  // на телефоне переключатели вида — не в шапке, а в меню «Вид»
  for (const id of ['#pinyinToggle', '#questionZhToggle', '#themeToggle', '#viewMenu']) {
    assert.equal(await page.locator(id).isVisible(), false, id);
  }
  // транскрипция в разметке есть, но видна только по настройке — и переключается посреди вопроса
  const reading = page.locator('#options .pinyin').first();
  assert.equal(await reading.isVisible(), false);
  await page.locator('#viewToggle').click();
  assert.equal(await page.locator('#viewToggle').getAttribute('aria-expanded'), 'true');
  await page.locator('#pinyinMenu').click();
  assert.equal(await reading.isVisible(), true);
  assert.equal(await page.locator('#pinyinMenu').getAttribute('aria-pressed'), 'true');
  assert.equal(await page.locator('#pinyinState').textContent(), 'вкл');
  // клавиша P — то же, что кнопка; по коду клавиши, поэтому и на русской раскладке
  await page.keyboard.press('KeyP');
  assert.equal(await reading.isVisible(), false);
  assert.equal(await page.locator('#pinyinState').textContent(), 'выкл');
  await page.keyboard.press('KeyP');
  assert.equal(await reading.isVisible(), true);
  // Esc закрывает меню, а не раунд; фокус возвращается на «Вид»
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('#viewMenu').isVisible(), false);
  assert.equal(await page.locator('#quizView').isVisible(), true);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'viewToggle');
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

test('китайский текст вопроса: скрыт по умолчанию, открывается кнопкой для одного вопроса и настройкой в шапке', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  assert.equal(await page.locator('#questionZhToggle').getAttribute('aria-pressed'), 'false');
  await page.evaluate(() => {
    const [withZh, other] = QUESTION_BANK.filter((r) => r.questionZh);
    startRoundWith([withZh, other, QUESTION_BANK.find((r) => !r.questionZh)], 'choice');
  });
  await page.locator('#quizView').waitFor();
  const zh = page.locator('#questionZh');
  const reveal = page.locator('#questionZhReveal');
  assert.equal(await zh.isVisible(), false);
  // кнопка открывает текст только у этого вопроса
  await reveal.click();
  assert.equal(await zh.isVisible(), true);
  assert.equal(await reveal.isVisible(), false);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'questionZh', 'фокус не теряется');
  await page.locator('#options button').first().click();
  await page.locator('#nextButton').click();
  assert.equal(await zh.isVisible(), false, 'у следующего вопроса текст снова скрыт');
  assert.equal(await reveal.isVisible(), true);
  // настройка в шапке показывает его у всех вопросов
  await page.locator('#questionZhToggle').click();
  assert.equal(await zh.isVisible(), true);
  assert.equal(await reveal.isVisible(), false);
  // у вопроса без китайского текста нет ни текста, ни кнопки
  await page.locator('#options button').first().click();
  await page.locator('#nextButton').click();
  assert.equal(await zh.isVisible(), false);
  assert.equal(await reveal.isVisible(), false);
  // настройка переживает перезагрузку и действует в «Вопросах в базе»
  await page.reload();
  assert.equal(await page.evaluate(() => document.documentElement.dataset.questionZh), 'on');
  assert.equal(await page.locator('#questionZhToggle').getAttribute('aria-pressed'), 'true');
  assert.equal(await page.locator('#questionZhLabel').textContent(), 'Вопрос 中文: вкл');
  // перезагрузка вернула в тот же раунд, где навигации нет: из раунда — в итоги, оттуда в базу
  await page.locator('#leaveRound').click();
  await page.locator('#navDatabase').click();
  const rowZh = page.locator('.row-zh-question').first();
  await rowZh.waitFor();
  assert.equal(await rowZh.isVisible(), true);
  await page.locator('#questionZhToggle').click();
  assert.equal(await rowZh.isVisible(), false);
  assert.deepEqual(page.errors, []);
});

test('телефон: с включённым пиньинем ни один вопрос и вариант не выходит за край экрана', LIMIT, async (t) => {
  const page = await openPage(t, { width: 375, height: 812 });
  if (!page) return;
  await startButton(page).click();
  await page.locator('#quizView').waitFor();
  await viewMenuItem(page, 'pinyinMenu');
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
  await startButton(page).click();
  await page.locator('#quizView').waitFor();
  assert.deepEqual(page.errors, []);
});

test('телефон: после ответа с длинным разбором видна кнопка «Следующий вопрос», много источников свёрнуто', LIMIT, async (t) => {
  const page = await openPage(t, { width: 375, height: 667 });
  if (!page) return;
  await page.locator('input[name="roundSize"][value="all"]').check({ force: true });
  await startButton(page).click();
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
  await startButton(page).click();
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

/* ---------- адреса экранов, незаконченный раунд, итоги ---------- */

test('«назад» из раунда, итогов и базы ведёт на главную; незаконченный раунд продолжается', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  await startRound(page, 10);
  assert.equal(hashOf(page), '#round');
  await answerAndNext(page, bank, true);
  const second = await currentRecord(page, bank);
  await answer(page, second, false);
  await page.goBack();
  await page.locator('#setupView').waitFor();
  assert.equal(hashOf(page), '');
  // вместо «Следующего раунда» — плашка: ход раунда и две кнопки, главная из них одна
  assert.equal(await page.locator('#nextMain').isVisible(), false);
  assert.equal(await page.locator('#resumeTitle').textContent(), 'Раунд не закончен');
  assert.equal(await page.locator('#resumeProgress').textContent(), 'Вопрос 2 из 10, верно 1.');
  assert.equal(await page.locator('#resumeSettings').textContent(), ' Все вопросы, выбор ответа, все темы.');
  assert.equal(await page.locator('#resumeSteps li.ink-step--correct').count(), 1);
  assert.equal(await page.locator('#resumeSteps li.ink-step--wrong').count(), 1);
  assert.equal(await page.locator('#resumeSaved').textContent(), 'Ответы на первые два вопроса уже сохранены в прогрессе.');
  assert.equal(await page.locator('#setupView .ink-btn--primary:visible').count(), 1);
  // «вперёд» и Enter на плашке возвращают в тот же раунд, к тому же разбору
  await page.goForward();
  await page.locator('#quizView').waitFor();
  assert.equal(await page.locator('#progressLabel').textContent(), 'Вопрос 2 из 10');
  await page.goBack();
  await page.locator('#setupView').waitFor();
  await page.keyboard.press('Enter');
  await page.locator('#quizView').waitFor();
  assert.equal((await currentRecord(page, bank)).id, second.id);
  assert.equal(await page.locator('#feedback.bad').isVisible(), true, 'разбор ответа остался на месте');
  // итоги: «назад» — на главную, раунд закончен, плашки нет
  await page.locator('#leaveRound').click();
  await page.locator('#resultsView').waitFor();
  assert.equal(hashOf(page), '#results');
  await page.goBack();
  await page.locator('#setupView').waitFor();
  assert.equal(await page.locator('#nextMain').isVisible(), true);
  assert.equal(await page.locator('#resumePanel').isVisible(), false);
  // база: «назад» — на главную
  await page.locator('#navDatabase').click();
  await page.locator('#databaseView').waitFor();
  assert.equal(hashOf(page), '#database');
  await page.goBack();
  await page.locator('#setupView').waitFor();
  // «Начать новый раунд» заменяет незаконченный без вопроса
  await startRound(page, 5);
  await answer(page, await currentRecord(page, bank), true);
  await page.goBack();
  await page.locator('#resumeNew').click();
  await page.locator('#quizView').waitFor();
  assert.equal(await page.locator('#progressLabel').textContent(), 'Вопрос 1 из 5');
  assert.equal(await page.locator('#progressSteps li.ink-step--correct').count(), 0);
  await page.goBack();
  await page.locator('#resumePanel').waitFor();
  assert.equal(await page.locator('#resumeProgress').textContent(), 'Вопрос 1 из 5, верно 0.');
  assert.equal(await page.locator('#resumeSaved').isVisible(), false, 'ответов в новом раунде ещё нет');
  // загруженный из файла прогресс заменяет и незаконченный раунд: плашка обещала бы сохранённые ответы
  page.once('dialog', (dialog) => dialog.accept());
  await page.locator('#importProgressFile').setInputFiles({
    name: 'progress.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify({ version: 1, progress: {} })),
  });
  await page.locator('#resumePanel').waitFor({ state: 'hidden' });
  assert.equal(await page.locator('#firstHero').isVisible(), true);
  assert.deepEqual(page.errors, []);
});

test('перезагрузка посреди раунда возвращает на тот же вопрос, итоги — на итоги', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  await startRound(page, 5);
  const wrong = await answerAndNext(page, bank, false);
  const second = await currentRecord(page, bank);
  await page.reload();
  await page.locator('#quizView').waitFor();
  assert.equal(hashOf(page), '#round');
  assert.equal(await page.locator('#progressLabel').textContent(), 'Вопрос 2 из 5');
  assert.equal((await currentRecord(page, bank)).id, second.id);
  assert.equal(await page.locator('#progressSteps li.ink-step--wrong').count(), 1);
  // отвеченный вопрос второй раз не задаётся: после перезагрузки — следующий
  await answer(page, second, true);
  await page.reload();
  await page.locator('#quizView').waitFor();
  assert.equal(await page.locator('#progressLabel').textContent(), 'Вопрос 3 из 5');
  // повтор ошибки пережил перезагрузку: шестым вернётся первый вопрос
  await answerAndNext(page, bank, true);
  await answerAndNext(page, bank, true);
  await answerAndNext(page, bank, true);
  assert.equal(await page.locator('#progressLabel').textContent(), 'Вопрос 6 из 6');
  assert.equal(await page.locator('#retryPill').isVisible(), true);
  await answerAndNext(page, bank, true);
  await page.locator('#resultsView').waitFor();
  assert.equal(await page.locator('#finalScore').textContent(), '4 / 5');
  await page.reload();
  await page.locator('#resultsView').waitFor();
  assert.equal(hashOf(page), '#results');
  assert.equal(await page.locator('#finalScore').textContent(), '4 / 5');
  assert.ok((await page.locator('#mistakeList').textContent()).includes(wrong.questionRu));
  assert.deepEqual(page.errors, []);
});

test('«Закончить раунд»: итоги по отвеченным, «Новый раунд» с теми же настройками, без ошибок главная — «Новый раунд»', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  await startRound(page, 20);
  await answerAndNext(page, bank, true);
  await answer(page, await currentRecord(page, bank), false);
  await page.locator('#leaveRound').click();
  await page.locator('#resultsView').waitFor();
  assert.equal(await page.locator('#finalScore').textContent(), '1 / 2');
  assert.equal(await page.locator('#resultCounts').textContent(), '✓ верно — 1✕ с ошибкой — 1');
  assert.equal(await page.locator('#newRoundNote').textContent(), 'Новый раунд — снова 20 вопросов, все вопросы, все темы.');
  // настройки главной после раунда меняются, а «Новый раунд» повторяет раунд
  await page.evaluate(() => { state.size = 5; state.format = 'truefalse'; });
  await page.locator('#newRound').click();
  await page.locator('#quizView').waitFor();
  assert.equal(await page.locator('#progressLabel').textContent(), 'Вопрос 1 из 20');
  assert.equal(await page.locator('#options button').count() > 0, true, 'формат раунда — выбор ответа');
  assert.equal(hashOf(page), '#round');
  // раунд без ошибок: главная кнопка — «Новый раунд», «Повторить ошибки» нет
  await page.evaluate(() => startRoundWith([QUESTION_BANK.find((r) => r.answer.state === 'verified')], 'choice'));
  await answerAndNext(page, bank, true);
  await page.locator('#resultsView').waitFor();
  assert.equal(await page.locator('#resultText').textContent(), 'Весь раунд без ошибок.');
  assert.equal(await page.locator('#repeatMistakes').isVisible(), false);
  assert.equal(await page.locator('#resultMistakes').isVisible(), false);
  assert.match(await page.locator('#newRound').getAttribute('class'), /ink-btn--primary/);
  assert.equal(await page.locator('#resultsView .ink-btn--primary:visible').count(), 1);
  await page.locator('#backToSetup').click();
  await page.locator('#setupView').waitFor();
  assert.equal(hashOf(page), '');
  assert.deepEqual(page.errors, []);
});

test('ошибки в итогах раскрываются: пояснение, подпись выбранного варианта, свёрнутые источники', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  // два вопроса с постоянными четырьмя вариантами и подписью у неверного варианта
  const picked = bank.filter((r) => r.options.length === 4 && r.evidence.length && r.explanation.ru
    && r.options.some((o) => o.id !== r.answer.optionId && o.gloss)).slice(0, 2);
  assert.equal(picked.length, 2);
  await page.evaluate((ids) => startRoundWith(ids.map((id) => QUESTION_BANK.find((r) => r.id === id)), 'choice'),
    picked.map((r) => r.id));
  const wrongOptions = [];
  for (const record of picked) {
    const wrong = record.options.find((o) => o.id !== record.answer.optionId && o.gloss);
    wrongOptions.push(wrong);
    await page.locator(`#options button[data-option-id="${wrong.id}"]`).click();
    await page.locator('#nextButton').click();
  }
  // повторы ошибок в конце раунда
  while (await page.locator('#quizView').isVisible()) await answerAndNext(page, bank, true);
  await page.locator('#resultsView').waitFor();
  const heads = page.locator('#mistakeList .mistake-head');
  const panels = page.locator('#mistakeList .mistake-panel');
  assert.equal(await heads.count(), 2);
  assert.deepEqual([await heads.nth(0).getAttribute('aria-expanded'), await heads.nth(1).getAttribute('aria-expanded')],
    ['true', 'false']);
  assert.equal(await panels.nth(0).isVisible(), true);
  assert.equal(await panels.nth(1).isVisible(), false);
  assert.ok((await heads.nth(0).textContent()).includes(`Ваш ответ ✕ ${wrongOptions[0].zh}, верно ✓ `));
  assert.equal(await panels.nth(0).locator('.mistake-why').textContent(), picked[0].explanation.ru);
  assert.equal(await panels.nth(0).locator('.mistake-gloss').textContent(),
    `Ваш ответ ${wrongOptions[0].zh} — ${wrongOptions[0].gloss.replace(/\.$/, '')}.`);
  assert.equal(await panels.nth(0).locator('.mistake-sources summary').textContent(), `Источники (${picked[0].evidence.length})`);
  assert.equal(await panels.nth(0).locator('.mistake-sources a').first().isVisible(), false, 'источники свёрнуты');
  // с клавиатуры: Enter раскрывает вторую ошибку и сворачивает первую, повторный — сворачивает
  await heads.nth(1).focus();
  await page.keyboard.press('Enter');
  assert.equal(await heads.nth(1).getAttribute('aria-expanded'), 'true');
  assert.equal(await panels.nth(1).isVisible(), true);
  assert.equal(await panels.nth(0).isVisible(), false);
  await page.keyboard.press('Enter');
  assert.equal(await panels.nth(1).isVisible(), false);
  assert.deepEqual(page.errors, []);
});

test('телефон: кнопка раунда внизу — только когда верхняя ушла за край экрана', LIMIT, async (t) => {
  const page = await openPage(t, { width: 375, height: 812 });
  if (!page) return;
  const bank = await bankOf(page);
  // главные кнопки, которые сейчас видны в окне
  const primariesInView = () => page.evaluate(() => [...document.querySelectorAll('.ink-btn--primary')].filter((button) => {
    const rect = button.getBoundingClientRect();
    return button.getClientRects().length && getComputedStyle(button).visibility !== 'hidden'
      && rect.bottom > 0 && rect.top < innerHeight;
  }).length);
  const bar = page.locator('#startBar');
  assert.equal(await bar.isVisible(), false);
  assert.equal(await primariesInView(), 1);
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  // полоса выезжает снизу: считаем кнопки, когда она встала на место
  await page.waitForFunction(() => {
    const element = document.getElementById('startBar');
    return element.classList.contains('is-shown') && element.getBoundingClientRect().bottom <= innerHeight + 0.5;
  });
  assert.equal(await bar.isVisible(), true);
  assert.equal(await page.locator('#startBarText').textContent(),
    `Все темы, 10 из ${eligible(bank, ALL, {}).length} подходящих`);
  assert.equal(await primariesInView(), 1);
  // полоса не закрывает подвал
  const footer = await page.locator('.ink-footer p').last().boundingBox();
  const barBox = await bar.boundingBox();
  assert.ok(footer.y + footer.height <= barBox.y, 'подвал под полосой');
  await page.locator('#barStart').click();
  await page.locator('#quizView').waitFor();
  assert.equal(await bar.isVisible(), false);
  // при плашке «Раунд не закончен» полосы нет: её «Начать раунд» заменил бы незаконченный раунд
  await page.goBack();
  await page.locator('#resumePanel').waitFor();
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  assert.equal(await page.evaluate(() => document.getElementById('startBar').classList.contains('is-shown')), false);
  await page.locator('#resumeButton').click();
  await page.locator('#quizView').waitFor();
  // на ноутбуке полосы нет
  await page.setViewportSize({ width: 1280, height: 860 });
  await page.locator('#leaveRound').click();
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  assert.equal(await bar.isVisible(), false);
  assert.deepEqual(page.errors, []);
});

/* ---------- подборки, база, сетка вариантов, русское название ответа ---------- */

test('темы раунда: разделы или подборки — один способ, выбор сохраняется и попадает в раунд', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  const dossiers = [...new Set(bank.map((r) => r.dossier).filter(Boolean))];
  await page.locator('input[name="topicsBy"][value="dossiers"]').check({ force: true });
  assert.equal(await page.locator('#topicControls').isVisible(), false);
  const names = await page.locator('#dossierControls .topic-name').allTextContents();
  assert.equal(names.length, dossiers.length);
  assert.equal(await page.locator('#dossiersCount').textContent(), String(dossiers.length));
  // названия — из досье, два заменены
  assert.ok(names.includes('Четыре великих и другие наборы') && names.includes('Известные люди'), names.join(', '));
  assert.ok(!names.includes('Наборы') && !names.includes('Люди'));
  // у каждой подборки банка свой знак и короткое имя для строки настроек: новое досье их требует
  assert.deepEqual(await page.evaluate(() => [...new Set(QUESTION_BANK.map((r) => r.dossier).filter(Boolean))]
    .filter((id) => !DOSSIER_MARKS[id] || !DOSSIER_SHORT[id])), []);
  const inSets = bank.filter((r) => r.dossier).length;
  assert.equal(await page.locator('#topicsHelp').textContent(),
    `Подборки собраны по темам досье: ${inSets} из ${bank.length} вопросов.`);
  for (const name of ['Кухня и блюда', 'Праздники']) {
    await page.locator('#dossierControls label', { hasText: name }).locator('input').check();
  }
  const filters = { ...ALL, dossiers: ['cuisine', 'holidays'] };
  const expected = eligible(bank, filters, {}).length;
  assert.equal(await page.locator('#eligibleNotice').textContent(), `Подходит вопросов: ${expected}, в раунде будет 10.`);
  assert.match(await page.locator('#firstCaption').textContent(), /, подборки: кухня и блюда, праздники\. /);
  assert.equal(await page.locator('#topicsValue').textContent(), '2 подборки');
  assert.equal(await page.locator('#topicsFoot').textContent(), `Выбрано: 2 подборки, ${expected} вопросов.`);
  // выбор переживает перезагрузку и попадает в раунд
  await page.reload();
  assert.equal(await page.locator('input[name="topicsBy"][value="dossiers"]').isChecked(), true);
  await startRound(page, 10);
  const round = await page.evaluate(() => state.round.map((r) => r.dossier));
  assert.ok(round.every((id) => id === 'cuisine' || id === 'holidays'), round.join(', '));
  await page.keyboard.press('Escape');
  // переключение на разделы сбрасывает отметки подборок: в раунд снова идут все вопросы
  await page.locator('input[name="topicsBy"][value="sections"]').check({ force: true });
  assert.equal(await page.evaluate(() => state.filters.dossiers.length), 0);
  assert.equal(await page.locator('#topicsValue').textContent(), 'все темы');
  assert.equal(await page.locator('#eligibleNotice').textContent(),
    `Подходит вопросов: ${eligible(bank, ALL, {}).length}, в раунде будет 10.`);
  assert.deepEqual(page.errors, []);
});

test('база: «Мои ответы», строка найденного, подсветка и «Тренировать найденные»', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  const found = await page.evaluate(() => QUESTION_BANK.filter((r) => matchesDatabaseSearch(r, 'чай')).map((r) => r.id));
  const [wrongId, rightId] = found;
  await page.evaluate(([wrong, right]) => localStorage.setItem('lingvo-trainer:v1', JSON.stringify({ version: 1, progress: {
    [wrong]: { attempts: 1, correct: 0, completed: true, lastCorrect: false, box: 0, dueAt: 0 },
    [right]: { attempts: 1, correct: 1, completed: true, lastCorrect: true, box: 1, dueAt: Date.now() + 1e9 },
  } })), [wrongId, rightId]);
  await page.reload();
  await page.locator('#navDatabase').click();
  await page.locator('#databaseView').waitFor();
  // фильтр «Мои ответы» вместо «Статуса»; без поиска и фильтра раунда из найденного нет
  assert.deepEqual(await page.locator('#databaseMine option').allTextContents(), ['Все', 'С ошибкой', 'Верно', 'Не отвечал']);
  assert.equal(await page.locator('#trainFound').isVisible(), false);
  await page.locator('#databaseSearch').fill('чай');
  const n = found.length;
  assert.equal(await page.locator('#foundCount').textContent(),
    `${n % 10 === 1 && n % 100 !== 11 ? 'Найден' : 'Найдено'} ${n} вопрос${n % 10 === 1 && n % 100 !== 11 ? '' : (n % 10 >= 2 && n % 10 <= 4 && !(n % 100 >= 12 && n % 100 <= 14) ? 'а' : 'ов')}`);
  assert.equal(await page.locator('#foundMine').textContent(), `1 с ошибкой, 1 верно, ${n - 2} ещё не отвечали`);
  assert.equal(await page.locator('#trainFound').textContent(), `Тренировать найденные (${n})`);
  assert.match(await page.locator('#trainFound').getAttribute('class'), /ink-btn--primary/);
  // у каждой карточки — свой результат; найденное слово подсвечено, и только с начала слова
  const wrongCard = page.locator('#databaseList article', { hasText: bank.find((r) => r.id === wrongId).questionRu }).first();
  assert.equal(await wrongCard.locator('.my.bad').innerText(), '✕ последний ответ — ошибка');
  assert.ok(await page.locator('#databaseList .my.none').count() > 0);
  const marks = await page.locator('#databaseList h3 mark').allTextContents();
  assert.ok(marks.length > 0);
  assert.ok(marks.every((text) => /^ча[йяюеи]/i.test(text)), marks.join(', '));
  // «С ошибкой» оставляет одну карточку, «Тренировать найденные» — раунд из неё
  await page.locator('#databaseMine').selectOption('wrong');
  assert.equal(await page.locator('#databaseList article').count(), 1);
  assert.equal(await page.locator('#foundMine').textContent(), '1 с ошибкой, 0 верно, 0 ещё не отвечали');
  await page.locator('#trainFound').click();
  await page.locator('#quizView').waitFor();
  assert.equal(await page.locator('#progressLabel').textContent(), 'Вопрос 1 из 1');
  assert.equal(await page.evaluate(() => state.round[0].id), wrongId);
  // «назад» — на главную: база и раунд из неё заняли одну запись истории после главной
  assert.equal(hashOf(page), '#round');
  await page.goBack();
  await page.locator('#setupView').waitFor();
  assert.equal(hashOf(page), '');
  assert.deepEqual(page.errors, []);
});

test('раунд, собранный не по фильтрам главной, показывает подпись источника и переживает перезагрузку', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  // на главной — год, которого у части найденных вопросов нет
  const year = await page.evaluate(() => QUESTION_BANK.flatMap((r) => r.occurrences.map((o) => o.year)).sort()[0]);
  await page.locator('#topicsFold details.more > summary').click();
  await page.locator('#yearFilter').selectOption(year);
  await page.locator('#navDatabase').click();
  await page.locator('#databaseSearch').fill('чай');
  await page.locator('#trainFound').click();
  await page.locator('#quizView').waitFor();
  // каждый вопрос раунда рисуется: подпись — по фильтрам раунда, иначе первое появление вопроса
  const labels = await page.evaluate(() => state.round.map((record, index) => {
    state.position = index;
    renderQuestion();
    const label = document.getElementById('sourceLabel');
    // у олимпиадного вопроса подпись есть всегда, у дополнения её нет
    return record.origin === 'addition' ? label.hidden : !label.hidden && label.textContent.startsWith('ВсОШ ');
  }));
  assert.ok(labels.length > 1 && labels.every(Boolean));
  assert.ok(await page.evaluate((y) => state.round.some((r) => r.origin !== 'addition'
    && !r.occurrences.some((o) => o.year === y)), year), 'в раунде есть вопрос без выбранного года');
  await page.evaluate(() => { state.position = 0; renderQuestion(); saveRound(); });
  await page.reload();
  await page.locator('#quizView').waitFor();
  assert.match(await page.locator('#progressLabel').textContent(), /^Вопрос 1 из \d+$/);
  // повреждённый снимок раунда не ломает главную
  await page.evaluate(() => {
    const saved = JSON.parse(sessionStorage.getItem('lingvo-trainer:round:v1'));
    delete saved.wrongIds;
    sessionStorage.setItem('lingvo-trainer:round:v1', JSON.stringify(saved));
  });
  await page.reload();
  await page.locator('#setupView').waitFor();
  assert.equal(await page.locator('#firstHero').isVisible(), true);
  assert.deepEqual(page.errors, []);
});

test('телефон: варианты столбиком, русское название верного — под иероглифами, как подписи неверных', LIMIT, async (t) => {
  const page = await openPage(t, { width: 375, height: 812 });
  if (!page) return;
  // сетку два на два для коротких вариантов автор отклонил 2026-10-25: и короткие — столбиком
  const short = await page.evaluate(() => QUESTION_BANK.find((r) => r.options.length === 4 && r.answer.gloss
    && r.options.every((o) => [...o.zh.trim()].length <= 4) && r.options.filter((o) => o.gloss).length === 3).id);
  await page.evaluate((id) => startRoundWith([QUESTION_BANK.find((r) => r.id === id)], 'choice'), short);
  const xs = await page.locator('#options button').evaluateAll((buttons) => buttons.map((b) => Math.round(b.getBoundingClientRect().x)));
  assert.equal(new Set(xs).size, 1, 'один столбец');
  await page.locator('#options button').first().click();
  const record = await page.evaluate((id) => QUESTION_BANK.find((r) => r.id === id), short);
  // подпись — в своём варианте, под текстом и по его левому краю; оба прямоугольника — одним замером:
  // после ответа страница на телефоне плавно докручивается
  const places = await page.locator('#options button').evaluateAll((buttons) => buttons.map((button) => {
    const notes = button.querySelectorAll('.option-gloss');
    const caption = button.querySelector('.option-text').getBoundingClientRect();
    const note = notes[0]?.getBoundingClientRect();
    return notes.length === 1 && note.y >= caption.bottom - 1 && Math.abs(note.x - caption.x) <= 1;
  }));
  assert.deepEqual(places, [true, true, true, true]);
  const correct = page.locator(`#options button[data-option-id="${record.answer.optionId}"] .option-gloss`);
  assert.equal(await correct.textContent(), record.answer.gloss);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth), 0);
  assert.deepEqual(page.errors, []);
});

test('русское название верного ответа: под вариантом, в разборе и в итогах; у вопроса без названия — как раньше', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  // название вне досье — из glosses.json (решение автора 2026-10-26), у досье — из ячейки; показ один
  const withName = (r) => r.answer.gloss && r.options.length === 4 && r.answer.gloss.includes(' — ');
  const named = bank.find((r) => !r.dossier && withName(r));
  assert.ok(named, 'на сайте нет вопроса вне досье с названием верного ответа');
  const plain = bank.find((r) => !r.answer.gloss && r.answer.state === 'verified' && r.options.length === 4);
  const name = named.answer.gloss.split(' — ')[0];
  const right = named.options.find((o) => o.id === named.answer.optionId).zh;
  await page.evaluate((ids) => startRoundWith(ids.map((id) => QUESTION_BANK.find((r) => r.id === id)), 'choice'),
    [named.id, plain.id]);
  await answer(page, named, false);
  const correct = page.locator(`#options button[data-option-id="${named.answer.optionId}"]`);
  assert.equal(await correct.locator('.option-gloss').textContent(), named.answer.gloss);
  assert.equal(await page.locator('#feedback .verdict span').first().textContent(), `Правильный ответ: ${right} — ${name}.`);
  await page.locator('#nextButton').click();
  // без названия: под верным вариантом подписи нет, в разборе — только иероглифы
  await answer(page, plain, false);
  assert.equal(await page.locator(`#options button[data-option-id="${plain.answer.optionId}"] .option-gloss`).count(), 0);
  const plainRight = plain.options.find((o) => o.id === plain.answer.optionId).zh;
  assert.equal(await page.locator('#feedback .verdict span').first().textContent(), `Правильный ответ: ${plainRight}.`);
  await page.locator('#leaveRound').click();
  await page.locator('#resultsView').waitFor();
  const answers = page.locator('#mistakeList .mistake-answers');
  assert.ok((await answers.first().textContent()).endsWith(`✓ ${right} — ${name}`));
  assert.ok((await answers.nth(1).textContent()).endsWith(`✓ ${plainRight}`));
  assert.deepEqual(page.errors, []);
});

/** CSS-анимации страницы: «элемент::псевдоэлемент:имя». Переходы (CSSTransition) не в счёт; законченная
 * анимация с заливкой (fill) остаётся в списке, поэтому повтор удара ловит runningAnimations. */
function cssAnimations(page) {
  return page.evaluate(() => document.getAnimations()
    .filter((animation) => animation instanceof CSSAnimation)
    .map((animation) => `${animation.effect.target.id || animation.effect.target.className}`
      + `${animation.effect.pseudoElement ?? ''}:${animation.animationName}`)
    .sort());
}

/** Идущие сейчас CSS-анимации — после finishAnimations их быть не должно, пока печать не ставят заново. */
function runningAnimations(page) {
  return page.evaluate(() => document.getAnimations()
    .filter((animation) => animation instanceof CSSAnimation && animation.playState === 'running')
    .map((animation) => animation.animationName)
    .sort());
}

function finishAnimations(page) {
  return page.evaluate(() => { for (const animation of document.getAnimations()) animation.finish(); });
}

/** Печать разбора и круг краски: вид псевдоэлементов .verdict. */
const sealStyle = (page) => page.locator('#feedback .verdict').evaluate((verdict) => {
  const seal = getComputedStyle(verdict, '::before');
  const ring = getComputedStyle(verdict, '::after');
  return { sealAnimation: seal.animationName, ringDisplay: ring.display, ringColor: ring.color,
    sealColor: seal.color, sealFill: seal.backgroundColor };
});

test('удар печати: движется только печать разбора, а при «уменьшить движение» она сразу на месте и без круга', LIMIT, async (t) => {
  for (const reducedMotion of ['no-preference', 'reduce']) {
    const page = await openPage(t);
    if (!page) return;
    await page.emulateMedia({ reducedMotion });
    const moving = reducedMotion === 'no-preference';
    const expected = moving ? ['verdict::after:seal-ring', 'verdict::before:seal-stamp'] : [];
    const bank = await bankOf(page);
    const choice = bank.find((r) => r.options.length === 4 && r.answer.state === 'verified');
    await page.evaluate((id) => startRoundWith([QUESTION_BANK.find((r) => r.id === id)], 'choice'), choice.id);
    assert.deepEqual(await cssAnimations(page), [], `${reducedMotion}: до ответа ничего не движется`);
    // ошибка — печать 错, круг краски киноварью, как сама печать
    await answer(page, choice, false);
    assert.deepEqual(await cssAnimations(page), expected, `${reducedMotion}: 错`);
    let style = await sealStyle(page);
    assert.equal(style.sealAnimation, moving ? 'seal-stamp' : 'none');
    assert.equal(style.ringDisplay, moving ? 'block' : 'none');
    if (moving) assert.equal(style.ringColor, style.sealColor, 'круг 错 — цвета печати');
    // верный ответ — печать 对, круг нефритом, как заливка печати
    await page.evaluate((id) => startRoundWith([QUESTION_BANK.find((r) => r.id === id)], 'choice'), choice.id);
    await answer(page, choice, true);
    assert.deepEqual(await cssAnimations(page), expected, `${reducedMotion}: 对`);
    style = await sealStyle(page);
    if (moving) assert.equal(style.ringColor, style.sealFill, 'круг 对 — цвета печати');
    // «Вспомни сам»: печать 答 — по тому же правилу; самооценка печать заново не ставит
    await page.evaluate(() => startRoundWith([QUESTION_BANK.find((r) => !needsOptions(r))], 'recall'));
    assert.deepEqual(await cssAnimations(page), [], `${reducedMotion}: до «Показать ответ»`);
    await page.locator('#revealAnswer').click();
    assert.match(await page.locator('#feedback').getAttribute('class'), /\breveal\b/);
    assert.deepEqual(await cssAnimations(page), expected, `${reducedMotion}: 答`);
    style = await sealStyle(page);
    assert.equal(style.ringDisplay, moving ? 'block' : 'none');
    if (moving) assert.equal(style.ringColor, style.sealColor, 'круг 答 — цвета печати');
    await finishAnimations(page);
    await page.locator('#recallRate button').first().click();
    assert.deepEqual(await runningAnimations(page), [], `${reducedMotion}: самооценка печать заново не ставит`);
    assert.deepEqual(page.errors, []);
  }
});

test('удар печати не повторяется, когда ученик возвращается к отвеченному вопросу', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  await startRound(page, 5);
  await answer(page, await currentRecord(page, bank), false);
  assert.deepEqual(await runningAnimations(page), ['seal-ring', 'seal-stamp'], 'ответ ставит печать');
  await finishAnimations(page);
  // знак сайта → «Продолжить раунд»: тот же вопрос с разбором, печать уже стоит
  await page.locator('#homeLink').click();
  await page.locator('#setupView').waitFor();
  await page.locator('#resumeButton').click();
  await page.locator('#quizView').waitFor();
  assert.equal(await page.locator('#feedback').isVisible(), true);
  assert.deepEqual(await runningAnimations(page), [], '«Продолжить раунд»');
  // системные «назад» и «вперёд»
  await page.goBack();
  await page.locator('#setupView').waitFor();
  await page.goForward();
  await page.locator('#quizView').waitFor();
  assert.equal(await page.locator('#feedback').isVisible(), true);
  assert.deepEqual(await runningAnimations(page), [], '«назад» и «вперёд»');
  assert.deepEqual(page.errors, []);
});

test('надписи без капслока: тема со знаком над вопросом и в базе, заголовок итогов', LIMIT, async (t) => {
  const page = await openPage(t);
  if (!page) return;
  const bank = await bankOf(page);
  // знаки тем — те же, что в списке тем на главной
  const marks = Object.fromEntries(await page.locator('#topicControls .topic-check').evaluateAll((labels) => labels
    .map((label) => [label.querySelector('.topic-name').textContent, label.querySelector('.topic-mark').textContent])));
  assert.ok(Object.keys(marks).length >= 7, 'список тем на главной');
  await startRound(page, 5);
  const record = await currentRecord(page, bank);
  assert.equal(await page.locator('#topicLabel').textContent(), record.topic);
  assert.equal(await page.locator('#topicMark').textContent(), marks[record.topic]);
  const line = page.locator('#quizView .topic-line');
  assert.equal(await line.evaluate((element) => getComputedStyle(element).textTransform), 'none');
  assert.equal(await page.locator('#quizView .ink-eyebrow').count(), 0);
  await answer(page, record, true);
  await page.locator('#leaveRound').click();
  await page.locator('#resultsView').waitFor();
  const title = page.locator('#resultsView .results-score h2');
  assert.equal(await title.textContent(), 'Раунд завершён');
  assert.equal(await title.evaluate((element) => getComputedStyle(element).textTransform), 'none');
  assert.equal(await page.locator('#resultsView .ink-eyebrow').count(), 0);
  // карточки базы: знак темы киноварью перед названием темы
  await page.locator('#navDatabase').click();
  await page.locator('#databaseView').waitFor();
  const cards = await page.locator('#databaseList article .topic-line').evaluateAll((lines) => lines.slice(0, 20)
    .map((topicLine) => [topicLine.querySelector('.wide-only')?.textContent ?? topicLine.lastChild.textContent,
      topicLine.querySelector('.topic-mark').textContent, getComputedStyle(topicLine).textTransform]));
  assert.equal(cards.length, 20);
  for (const [topic, mark, transform] of cards) {
    assert.equal(mark, marks[topic], topic);
    assert.equal(transform, 'none');
  }
  assert.deepEqual(page.errors, []);
});
