# Режим отладки вопросов — план реализации

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Собирать замечания во время прохождения на компьютере и телефоне и выгружать их для Codex.

**Architecture:** Отдельный src/review.ui.js с локальным хранилищем и модальным окном,
подключённый после существующих интерфейсов. Снимок берётся из текущей записи и DOM
вариантов без повторного перемешивания. Существующие интерфейсы сообщают о новом вопросе.

**Tech Stack:** Vanilla JS, CSS дизайн-системы, localStorage, HTML dialog, Playwright/Node test.

**Spec:** docs/superpowers/specs/2026-10-31-question-review-design.md

## Global Constraints

- Один самодостаточный HTML, без сервера и новых зависимостей.
- Отдельное хранилище замечаний; стабильные id, банк и учебный прогресс не менять.
- Ctrl/⌘ + Shift + E и переключатель на телефоне.
- Стили только на семантических токенах существующей системы.

## Review Focus

- Точный набор и порядок случайных вариантов и предложенный ответ «Верно или нет».
- Перезагрузка и повторное редактирование не теряют комментарий или исходный снимок.
- Клавиши внутри окна не отвечают на вопрос и не завершают раунд.
- Ошибка localStorage не выглядит как успешное сохранение.
- Телефон 375px, тёмная тема, длинный текст и закрытие окна с возвратом фокуса.

### Task 1: Замечания в раундах и локальное сохранение

**Files:** src/review.ui.js, src/template.html, src/quiz.css, src/quiz.ui.js,
src/chengyu.ui.js, scripts/build_html.py, test/ui.test.mjs.

**Interfaces:** Событие `reviewchange` при смене вопроса; контроллер читает state/cy,
QUESTION_BANK/CHENGYU_BANK и показанные варианты из DOM. Хранилище
`lingvo-trainer:review:v1` = {version: 1, entries: [...]}; настройка отдельно.

- [x] Добавить браузерные тесты включения, отметки, комментария, перезагрузки и изоляции клавиш.
- [x] Запустить `node --test --test-name-pattern='отладка' test/ui.test.mjs`; увидеть отсутствие UI.
- [x] Реализовать контроллер, окно, стили и минимальные точки интеграции.
- [x] Проверить основной сценарий, точный контекст «Верно или нет», recall и чэнъюй.

### Task 2: Передача в Codex и проверка

**Files:** src/review.ui.js, test/ui.test.mjs, README.md, CHANGELOG.md, dist/lingvostranovedenie-trainer.html.

**Interfaces:** JSON {type: 'lingvo-question-review', version: 1, exportedAt, entries};
читаемый отчёт из тех же записей. Системная передача файла — при navigator.canShare.

- [x] Добавить проверки выгрузки без удаления отметок, снятия отметки, повреждённого/
  недоступного хранилища, телефона и безопасного вывода комментариев.
- [x] Реализовать выгрузку JSON, копирование и системную передачу файла.
- [x] Собрать `python3 scripts/build_html.py`.
- [x] Запустить `python3 -m unittest discover -s test -t .` и `node --test test/*.test.mjs`.
- [x] Визуально проверить компьютер, телефон и тёмную тему; провести независимое ревью.
- [x] Обновить README и CHANGELOG, проверить итоговый diff.
