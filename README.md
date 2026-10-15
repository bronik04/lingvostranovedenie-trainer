# Тренажёр по лингвострановедению (ВсОШ, китайский язык)

[![Deploy to GitHub Pages](https://github.com/bronik04/lingvostranovedenie-trainer/actions/workflows/pages.yml/badge.svg)](https://github.com/bronik04/lingvostranovedenie-trainer/actions/workflows/pages.yml)

Банк вопросов раздела «Лингвострановедение» Всероссийской олимпиады школьников
за 2015/16 — 2025/26 и тренажёр к нему: вопрос по-русски, варианты по-китайски,
у каждого ответа пояснение и ссылка на источник.

**Демо:** https://bronik04.github.io/lingvostranovedenie-trainer/
(GitHub Pages, `.github/workflows/pages.yml` — при каждом push в `master`
банк пересобирается из первоисточников, прогоняются оба набора тестов,
и только после этого публикуется новая версия).

Файл самодостаточный: можно просто скачать `dist/lingvostranovedenie-trainer.html`
и открыть его локально без сервера и интернета.

## Сборка

    python3 scripts/import_sources.py     # sources/ -> data/raw/
    python3 scripts/merge_bank.py         # data/raw/ -> data/bank.json + отчёты
    python3 scripts/taxonomy.py           # проставить темы
    python3 scripts/build_html.py         # data/bank.json -> dist/

Оформление — дизайн-система «Тушь и киноварь». `src/ink/` — копия её токенов и
компонентов: здесь не править, правка идёт в систему, сюда — новая копия. `src/fonts/` —
Cormorant Garamond и Onest (SIL OFL 1.1, тексты лицензий рядом); сборка встраивает их в
страницу, поэтому она работает без интернета. Стили самого тренажёра — `src/quiz.css`,
только семантические токены системы. Картинка превью ссылок пересобирается вручную:
`python3 scripts/render_og_image.py` (нужен Google Chrome).

## Тесты

    npm ci                                  # playwright-core для браузерного теста
    python3 -m unittest discover -s test -t . -v
    node --test test/*.test.mjs

`test/ui.test.mjs` открывает собранный `dist/` в установленном Google Chrome без окна
и проходит тренажёр как ученик: раунд, итоги, база, фильтры, телефон. Без Chrome
локально пропускается.

## Данные

`sources/` — неизменяемые первоисточники, их контрольные суммы в `sources/manifest.json`.
`data/bank.json` — канонический банк, единственный источник правды для сборки.
`data/review/` — отчёты слияния, рубрикации и волн проверки ответов.

К олимпиадным вопросам `merge_bank.py` добавляет дополнения `data/authored/questions.json`, затем
вопросы досье `data/dossiers/` (таблица фактов `<id>.json` и вопросы по её ячейкам
`<id>-questions.json`; в банк идут только принятые автором, проверка без сборки —
`python3 scripts/dossiers.py`). Ручные слои поверх собранного банка лежат в `data/review/` и
накладываются в таком порядке: `editorial.json` (правки текста) → `merges.json` (склейка дублей; с пометкой
`"distractors": "pool"` — один вопрос с общим набором неверных вариантов) → `retired.json`
(удалённые записи пар с разными ответами, прогресс переезжает на оставшуюся) →
`fact-groups.json` (метки «один факт», раунд берёт из группы один вопрос) → `glosses.json`
(подписи к неверным вариантам).

## Документы

Спецификация: `docs/superpowers/specs/2026-09-18-lingvostranovedenie-trainer-design.md`
План работ: `docs/superpowers/plans/2026-09-18-lingvostranovedenie-trainer.md`
