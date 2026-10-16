"""Карта покрытия: какие темы страноведения закрыты вопросами банка и сколько их не хватает до цели.

Темы — `data/coverage.json`: у каждой категория олимпиады, название, откуда тема (олимпиада, книга
автора, видеокурс, заметки об идеях) и слова для поиска. Вопрос относится к теме, если слово стоит
в его тексте или в вариантах (без вариантов, добавленных досье: они о соседних фактах). Отчёт —
`data/review/coverage.md`: доли категорий в олимпиаде и в банке, сколько вопросов каждой категории
нужно к цели, пустые и слабые темы, вопросы вне тем — по ним видно, чего не хватает списку тем.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from taxonomy import TOPICS  # noqa: E402

ORIGINAL_OPTION = re.compile(r'o\d+')
FEW = 3  # тема с меньшим числом вопросов — слабая


def validate_themes(themes: object) -> list[str]:
    if not isinstance(themes, list):
        return ['themes должен быть списком']
    errors: list[str] = []
    seen: set[str] = set()
    for theme in themes:
        theme_id = theme.get('id') if isinstance(theme, dict) else None
        if not isinstance(theme_id, str) or not theme_id:
            errors.append(f'тема без id: {theme}')
            continue
        if theme_id in seen:
            errors.append(f'{theme_id}: повтор id')
        seen.add(theme_id)
        if theme.get('topic') not in TOPICS:
            errors.append(f'{theme_id}: категории «{theme.get("topic")}» нет среди семи')
        if not isinstance(theme.get('title'), str) or not theme['title'].strip():
            errors.append(f'{theme_id}: нет title')
        match = theme.get('match')
        if not isinstance(match, list) or not match or not all(isinstance(m, str) and m.strip() for m in match):
            errors.append(f'{theme_id}: match — непустой список слов')
        sources = theme.get('sources')
        if not isinstance(sources, list) or not sources:
            errors.append(f'{theme_id}: sources — откуда тема (олимпиада, книга, курс, идеи)')
    return errors


def _haystack(record: dict) -> str:
    options = [option for option in record['options']
               if 'dossier' not in record or ORIGINAL_OPTION.fullmatch(option['id'])]
    return _fold(' '.join([record['questionRu'], record.get('questionZh') or '']
                          + [option['zh'] for option in options]))


def _fold(text: str) -> str:
    # «учёных» и «ученых» — одно слово: в банке встречаются оба написания
    return text.lower().replace('ё', 'е')


def theme_matches(bank: list[dict], themes: list[dict]) -> dict[str, list[str]]:
    texts = [(record['id'], _haystack(record)) for record in bank]
    return {theme['id']: [record_id for record_id, text in texts
                          if any(_fold(word) in text for word in theme['match'])]
            for theme in themes}


def topic_shares(bank: list[dict]) -> dict[str, dict]:
    olympiad = [record for record in bank if record.get('occurrences')]
    return {topic: {'olympiad': sum(1 for r in olympiad if r.get('topic') == topic) / len(olympiad) if olympiad else 0,
                    'bank': sum(1 for r in bank if r.get('topic') == topic)}
            for topic in TOPICS}


def coverage_report(bank: list[dict], themes: list[dict], target: int) -> str:
    matches = theme_matches(bank, themes)
    shares = topic_shares(bank)
    lines = ['# Карта покрытия', '',
             f'В банке {len(bank)} вопросов. Цель — {target}: доли категорий как в олимпиаде, ни одной '
             'пустой темы из материалов автора. Собирается сборкой (`scripts/coverage_map.py`), темы — '
             '`data/coverage.json`. Счёт по словам — приблизительный: вопрос может попасть в несколько '
             'тем, а тема — собрать соседние вопросы; пустые и слабые темы при этом видны точно.', '',
             '## Категории', '',
             '| Категория | Доля в олимпиаде | В банке | Нужно к цели | Не хватает |', '|---|---|---|---|---|']
    for topic in TOPICS:
        need = round(shares[topic]['olympiad'] * target)
        have = shares[topic]['bank']
        lines.append(f'| {topic} | {round(shares[topic]["olympiad"] * 100)} % | {have} | {need} | {max(need - have, 0)} |')
    for topic in TOPICS:
        own = [theme for theme in themes if theme['topic'] == topic]
        if not own:
            continue
        lines += ['', f'## {topic}', '', '| Тема | Вопросов | Откуда |', '|---|---|---|']
        for theme in sorted(own, key=lambda t: len(matches[t['id']])):
            count = len(matches[theme['id']])
            mark = ' — пусто' if count == 0 else ' — мало' if count < FEW else ''
            lines.append(f'| {theme["title"]}{mark} | {count} | {", ".join(theme["sources"])} |')
    empty = [theme for theme in themes if not matches[theme['id']]]
    lines += ['', '## Пустые темы', '']
    lines += [f'- {theme["title"]} ({theme["topic"]})' for theme in empty] or ['- нет']
    covered = {record_id for ids in matches.values() for record_id in ids}
    outside = [record for record in bank if record['id'] not in covered]
    lines += ['', '## Вопросы вне тем', '',
              f'{len(outside)} вопросов не попали ни в одну тему — по ним видно, чего не хватает списку тем.', '']
    lines += [f'- `{record["id"]}` — {record["questionRu"][:100]}' for record in outside] or ['- нет']
    return '\n'.join(lines) + '\n'


def main() -> None:
    bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
    data = json.loads((ROOT / 'data/coverage.json').read_text('utf-8'))
    errors = validate_themes(data['themes'])
    if errors:
        raise SystemExit('некорректные темы data/coverage.json:\n - ' + '\n - '.join(errors))
    (ROOT / 'data/review/coverage.md').write_text(coverage_report(bank, data['themes'], data['target']), encoding='utf-8')
    matches = theme_matches(bank, data['themes'])
    empty = sum(1 for ids in matches.values() if not ids)
    print(f'карта покрытия: тем {len(data["themes"])}, пустых {empty}; отчёт: data/review/coverage.md')


if __name__ == '__main__':
    main()
