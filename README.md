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

## Документы

Спецификация: `docs/superpowers/specs/2026-09-18-lingvostranovedenie-trainer-design.md`
План работ: `docs/superpowers/plans/2026-09-18-lingvostranovedenie-trainer.md`
