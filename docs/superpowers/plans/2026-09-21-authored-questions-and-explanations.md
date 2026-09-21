# Дополнения к олимпиадной базе и пояснения: план реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (\`- [ ]\`) syntax for tracking.

**Goal:** Добавить подтверждённые дополнения к олимпиадной базе, улучшить разбор ответов и подготовить рост банка до 1000 вопросов.

**Architecture:** Олимпиадная часть продолжает собираться из \`sources/\`. Авторские записи живут в \`data/authored/questions.json\`, проверяются \`scripts/authored.py\` и присоединяются \`scripts/merge_bank.py\` к каноническому банку. Ревизии существующих объяснений живут отдельной волной и накладываются при слиянии. UI использует \`origin\`, не меняя формат прогресса или логику раундов.

**Tech Stack:** Python 3 standard library, Node built-in test runner, vanilla JavaScript, static HTML/CSS.

**Spec:** \`docs/superpowers/specs/2026-09-21-authored-questions-and-explanations-design.md\`

## Global Constraints

- Сайт остаётся одним автономным HTML-файлом: без сервера, библиотек и сетевого хранения.
- Вопросы пишутся по-русски, варианты — по-китайски.
- \`sources/\` не меняется, а \`data/bank.json\` создают только скрипты.
- У дополнения есть \`origin: "addition"\`, четыре варианта, проверенный ответ и официальная HTTP(S)-ссылка.
- Новое или переработанное пояснение содержит от трёх до пяти предложений.
- Каждое заметное изменение фиксируется в \`CHANGELOG.md\`.

## Review Focus

- Дополнение без ссылки, с \`javascript:\` URL или неполными реквизитами доказательства останавливает сборку — Task 1.
- Ссылка обратного вопроса на отсутствующую или на ту же формулировку запись отклоняется — Task 1.
- Олимпиадная запись после слияния не получает метку дополнения — Task 2.
- Источник в карточке появляется только после «Показать ответ» и открывается безопасно — Task 3.
- Первая волна даёт 25 дополнений и 25 ревизий без ручного изменения \`data/bank.json\` — Task 4.

### Task 1: Контракт авторских дополнений

**Files:**
- Create: \`scripts/authored.py\`
- Create: \`data/authored/questions.json\`
- Create: \`test/test_authored.py\`
- Modify: \`scripts/merge_bank.py\`
- Modify: \`scripts/build_html.py\`

**Interfaces:**
- \`sentence_count(text: str) -> int\` считает предложения, оканчивающиеся на \`.!\?\`.
- \`validate_authored(records: list[dict], olympiad_bank: list[dict]) -> list[str]\` возвращает все ошибки.
- \`load_authored(path: Path, olympiad_bank: list[dict]) -> list[dict]\` читает JSON, валидирует его и добавляет отсутствующие \`occurrences: []\` и \`parseWarnings: []\`.
- \`merge_bank.merge()\` добавляет авторские записи после олимпиадных записей и до сортировки.

- [ ] **Step 1: Написать падающие тесты контракта**

В \`test/test_authored.py\` создать фабрику \`addition(**overrides)\` с допустимыми полями: ID \`addition-001\`, \`origin: "addition"\`, тема, русский вопрос, варианты \`北京\`, \`上海\`, \`广州\`, \`西安\`, ответ \`o1\`, три предложения и доказательство с \`url: "https://www.gov.cn/example"\`, \`authority: "official"\`, названием и датой.

Добавить эти проверки:

\`\`\`python
def test_accepts_complete_addition(self):
    self.assertEqual(validate_authored([addition()], [olympiad_record()]), [])

def test_rejects_unsafe_or_missing_evidence(self):
    self.assertTrue(validate_authored([addition(evidence=[])], []))
    bad = [{'title': 'x', 'url': 'javascript:alert(1)', 'checkedAt': '2026-09-21',
            'authority': 'official'}]
    self.assertTrue(validate_authored([addition(evidence=bad)], []))

def test_rejects_duplicate_and_invalid_reverse_link(self):
    base = [olympiad_record(id='olympiad-1', questionRu='Какой город является столицей Китая?')]
    self.assertTrue(validate_authored([addition(questionRu=base[0]['questionRu'])], base))
    self.assertTrue(validate_authored([addition(derivedFrom='missing')], base))
    self.assertTrue(validate_authored([addition(derivedFrom='olympiad-1',
                    questionRu=base[0]['questionRu'])], base))

def test_rejects_bad_options_and_sentence_count(self):
    self.assertTrue(validate_authored([addition(options=addition()['options'][:3])], []))
    self.assertTrue(validate_authored([addition(explanation={'ru': 'Одно предложение.'})], []))
    self.assertTrue(validate_authored([addition(explanation={'ru': 'Раз. Два. Три. Четыре. Пять. Шесть.'})], []))
\`\`\`

- [ ] **Step 2: Подтвердить, что тесты падают**

Run: \`python3 -m unittest test.test_authored -v\`

Expected: FAIL — модуля \`authored\` ещё нет.

- [ ] **Step 3: Реализовать валидатор**

В \`scripts/authored.py\` использовать \`normalize.normalize_text\`, \`normalize.language_errors\`, \`taxonomy.TOPICS\` и \`urllib.parse.urlparse\`. Проверять \`origin == "addition"\`; одну из семи тем; ровно четыре непустых китайских варианта с уникальными ID; ответ \`{"optionId": существующий_id, "state": "verified"}\`; объяснение из 3–5 предложений; каждое доказательство с HTTP(S), непустым host, \`title\`, \`checkedAt\`, \`authority == "official"\`.

Сравнивать нормализованный текст нового вопроса с текстами олимпиады и дополнений. При \`derivedFrom\` требовать существующий олимпиадный ID и отличающуюся формулировку. Невалидный верхний JSON-тип или хотя бы одна ошибка вызывают \`ValueError\`. Создать \`data/authored/questions.json\` со значением \`[]\`.

- [ ] **Step 4: Подключить дополнения к сборке**

В \`scripts/merge_bank.py\` вызвать \`load_authored(ROOT / "data/authored/questions.json", bank)\` после применения \`verification\`, расширить им \`bank\`, затем использовать существующую сортировку. В \`scripts/build_html.py\` вызвать \`validate_authored\` для авторских записей и отклонять любую незнакомую строку \`origin\`. Старые олимпиадные объяснения по длине пока не проверять.

- [ ] **Step 5: Запустить проверку и создать первый коммит**

Run: \`python3 -m unittest test.test_authored test.test_merge test.test_build_invariants -v && python3 scripts/merge_bank.py && python3 scripts/build_html.py && git diff --check\`

Expected: PASS; при пустом списке дополнений банк остаётся из 421 записи.

Commit:
\`\`\`bash
git add scripts/authored.py scripts/merge_bank.py scripts/build_html.py data/authored/questions.json test/test_authored.py data/bank.json data/review/merge.md dist/lingvostranovedenie-trainer.html
git commit -m "Добавить проверку дополнений к базе"
\`\`\`

### Task 2: Ревизии качественных пояснений

**Files:**
- Create: \`scripts/explanations.py\`
- Create: \`data/review/explanation-wave-1.json\`
- Create: \`test/test_explanations.py\`
- Modify: \`scripts/merge_bank.py\`

**Interfaces:**
- \`validate_revisions(revisions: dict[str, dict], bank: list[dict]) -> list[str]\` проверяет ID существующих олимпиадных вопросов, 3–5 предложений и официальные ссылки.
- \`apply_revisions(bank: list[dict], revisions: dict[str, dict]) -> list[dict]\` заменяет объяснение и доказательства, добавляет \`explanationRevision: 2\` и \`explanationReviewedAt\`.

- [ ] **Step 1: Написать падающие тесты**

В \`test/test_explanations.py\` создать олимпиадную запись \`2015-16-mun-2\` и функцию \`revision(text)\` с официальной ссылкой. Проверить, что ревизия из трёх предложений меняет только \`explanation\`/ \`evidence\` и добавляет версию с датой. Отдельно проверить отказ для отсутствующего ID, одного предложения и URL \`ftp://example.org\`.

\`\`\`python
updated = apply_revisions([record()], {'2015-16-mun-2': revision('Факт верен. Контекст его поясняет. Поэтому выбран этот вариант.')})[0]
self.assertEqual(updated['explanationRevision'], 2)
self.assertEqual(updated['answer'], record()['answer'])
self.assertTrue(validate_revisions({'missing': revision()}, [record()]))
self.assertTrue(validate_revisions({'2015-16-mun-2': revision('Коротко.')}, [record()]))
\`\`\`

- [ ] **Step 2: Подтвердить падение**

Run: \`python3 -m unittest test.test_explanations -v\`

Expected: FAIL — модуля \`explanations\` ещё нет.

- [ ] **Step 3: Реализовать и подключить ревизии**

В \`scripts/explanations.py\` переиспользовать \`sentence_count\` и проверку доказательства из \`authored.py\`. \`apply_revisions\` не изменяет вопрос, варианты, ответ, тему или \`occurrences\`. В \`merge_bank.py\` загрузить \`data/review/explanation-wave-1.json\`, применить проверенные ревизии после \`verification\`; пустой объект \`{}\` допустим.

- [ ] **Step 4: Запустить проверку и закоммитить механизм**

Run: \`python3 -m unittest test.test_explanations test.test_merge test.test_build_invariants -v && python3 scripts/merge_bank.py && git diff --check\`

Expected: PASS; пустая первая волна не меняет 421 олимпиадную запись.

Commit:
\`\`\`bash
git add scripts/explanations.py scripts/merge_bank.py data/review/explanation-wave-1.json test/test_explanations.py data/bank.json data/review/merge.md
git commit -m "Добавить волны качественных пояснений"
\`\`\`

### Task 3: Происхождение и источники в интерфейсе

**Files:**
- Modify: \`src/quiz.mjs\`
- Modify: \`src/quiz.ui.js\`
- Modify: \`src/template.html\`
- Modify: \`src/quiz.css\`
- Modify: \`test/quiz.test.mjs\`

**Interfaces:**
- \`recordOrigin(record) -> { label: string, isAddition: boolean }\` возвращает \`{ label: "Дополнение к олимпиадной базе", isAddition: true }\` для дополнения и \`{ label: "Олимпиадная база", isAddition: false }\` для остальных.
- Карточка базы добавляет список \`record.evidence\` внутри существующего \`details.row-reveal\`.

- [ ] **Step 1: Написать падающий Node-тест**

\`\`\`js
test('происхождение отличает дополнение от олимпиадного вопроса', () => {
  assert.deepEqual(recordOrigin(record('olympiad')), { label: 'Олимпиадная база', isAddition: false });
  assert.deepEqual(recordOrigin(record('addition', { origin: 'addition' })), {
    label: 'Дополнение к олимпиадной базе', isAddition: true,
  });
});
\`\`\`

- [ ] **Step 2: Подтвердить падение**

Run: \`node --test test/quiz.test.mjs\`

Expected: FAIL — \`recordOrigin\` не экспортируется.

- [ ] **Step 3: Реализовать UI**

Экспортировать \`recordOrigin\` из \`src/quiz.mjs\`. В \`src/template.html\` добавить скрытую плашку \`#originPill\` рядом с тематической. В \`renderQuestion()\` показывать её только у дополнения; для олимпиады сохранить год, этап и номер.

В \`appendDatabaseRows()\` выводить тег происхождения. После \`.row-why\` и до закрытия \`details\` выводить «Источники» и список, созданный теми же \`safeSourceUrl\`, \`escapeHtml\`, \`target="_blank"\` и \`rel="noopener noreferrer"\`, что у разбора после ответа. При пустом \`evidence\` не создавать заголовок. В CSS дать плашке и тегу компактный стиль из существующих цветов.

- [ ] **Step 4: Проверить и закоммитить интерфейс**

Run: \`node --test test/*.test.mjs && python3 scripts/build_html.py && git diff --check\`

Expected: PASS; собранный HTML содержит плашку и источники внутри раскрываемой карточки.

Commit:
\`\`\`bash
git add src/quiz.mjs src/quiz.ui.js src/template.html src/quiz.css test/quiz.test.mjs dist/lingvostranovedenie-trainer.html
git commit -m "Показать происхождение и источники вопросов"
\`\`\`

### Task 4: Первая подтверждённая волна

**Files:**
- Modify: \`data/authored/questions.json\`
- Modify: \`data/review/explanation-wave-1.json\`
- Modify: \`data/bank.json\`, \`data/review/merge.md\`, \`dist/lingvostranovedenie-trainer.html\` (только результат скриптов)
- Modify: \`CHANGELOG.md\`

**Interfaces:**
- Авторский файл получает ровно 25 записей с ID \`addition-001\` … \`addition-025\`.
- Файл ревизий получает ровно 25 обновлённых олимпиадных объяснений с \`reviewedAt: "2026-09-21"\`.

- [ ] **Step 1: Отобрать подтверждённые факты**

Для каждого факта открыть и проверить конкретную официальную страницу: \`neac.gov.cn\`, \`npc.gov.cn\`, \`moe.gov.cn\`, \`mofcom.gov.cn\`, \`stats.gov.cn\`, \`ihchina.cn\`, \`beijing.gov.cn\`, \`shanghai.gov.cn\` или \`sport.gov.cn\`. Не использовать главную страницу раздела, только страницу, прямо подтверждающую факт. Сохранить её название, URL и дату проверки в доказательстве.

- [ ] **Step 2: Создать 25 дополнений**

Распределить 8 вопросов по географии, 5 по истории и государству, 4 по обществу, 4 по культуре, 4 по экономике, образованию, науке или спорту. Если это обратный вопрос, указать \`derivedFrom\`; проверять другую сторону исходного факта: место → объект, дата → событие, орган → полномочие, термин → определение. Не делать почти буквальный пересказ. Для каждого объяснения написать 3–5 предложений: факт, контекст, связь с вопросом и, когда полезно, отличие от похожего варианта.

- [ ] **Step 3: Переписать 25 слабых объяснений**

Выбрать 25 наиболее коротких нынешних объяснений, при равной длине равномерно по темам. В \`explanation-wave-1.json\` хранить \`explanation\`, \`evidence\` и \`reviewedAt\`. Не менять вопрос, варианты или ответ. Каждый текст должен дать факт, контекст и причину выбора в 3–5 предложениях.

- [ ] **Step 4: Полностью проверить данные и обновить журнал**

Run: \`python3 scripts/merge_bank.py && python3 scripts/taxonomy.py && python3 scripts/build_html.py && python3 -m unittest discover -s test -t . -v && node --test test/*.test.mjs\`

Expected: обе тестовые команды PASS; сборка сообщает 446 записей и 446 подтверждённых ответов; в банке 25 \`origin: "addition"\` и 25 \`explanationRevision: 2\`.

Добавить в \`CHANGELOG.md\` одну запись: дополнения помечены, карточка базы показывает источники, первая волна создала 25 подтверждённых вопросов и улучшила 25 пояснений.

- [ ] **Step 5: Проверить diff и закоммитить данные**

Run: \`git diff --check && git status --short\`

Commit:
\`\`\`bash
git add data/authored/questions.json data/review/explanation-wave-1.json data/bank.json data/review/merge.md dist/lingvostranovedenie-trainer.html CHANGELOG.md
git commit -m "Добавить первую волну подтверждённых вопросов"
\`\`\`

### Task 5: Итоговая проверка и публикация

**Files:** нет, кроме минимального исправления дефекта в его владельце.

- [ ] **Step 1: Прогнать финальные проверки**

Run: \`python3 -m unittest discover -s test -t . -v && node --test test/*.test.mjs && python3 scripts/build_html.py && git diff --check && git status --short\`

Expected: PASS, успешная сборка, чистое рабочее дерево.

- [ ] **Step 2: Проверить сценарий в браузере**

Открыть локальный \`dist\`. Найти дополнение в раунде, убедиться в плашке, ответить неверно и прочитать разбор. В базе раскрыть тот же ответ и проверить источник. Затем открыть переработанный олимпиадный вопрос: у него нет метки дополнения, но есть новое пояснение и источник.

- [ ] **Step 3: Провести независимый обзор и устранить дефекты**

Попросить обзор с фокусом на валидацию данных, происхождение, небезопасные URL, обратные вопросы и совместимость с существующим банком. Для найденного дефекта сначала добавить воспроизводящий тест, затем минимальное исправление и повторить Step 1.

- [ ] **Step 4: Опубликовать**

Run: \`git push origin master\`

Expected: push успешен, GitHub Actions пересобирает и публикует статическую версию.
