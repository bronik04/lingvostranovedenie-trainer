"""Карта покрытия: какие темы представлены доступными на сайте вопросами.

Темы — `data/coverage.json`: у каждой категория олимпиады, название, откуда тема (олимпиада, книга
автора, видеокурс, заметки об идеях) и слова для поиска. Вопрос относится к теме, если слово стоит
в его тексте или в правильном ответе: неверные варианты — соседние факты, они тему не задают.
Русское слово ищется с начала слова («сад» не найдёт «посадку»), «ё» и «е» не различаются. Отчёт —
`data/review/coverage.md`: фактические доли категорий, пустые и слабые темы, вопросы вне тем.
Фильтр доступности тот же, что у сайта. Число вопросов не измеряет разнообразие фактов
и само по себе не доказывает содержательную полноту темы.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from taxonomy import TOPICS  # noqa: E402
from site_bank import embedded_by, load_settings, site_bank  # noqa: E402

FEW = 3  # тема с меньшим числом вопросов — слабая


def questions_word(count: int) -> str:
    """«1 вопрос», «994 вопроса», «1000 вопросов»."""
    if count % 10 == 1 and count % 100 != 11:
        return 'вопрос'
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return 'вопроса'
    return 'вопросов'


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
        if not isinstance(sources, list) or not sources or not all(isinstance(s, str) and s.strip() for s in sources):
            errors.append(f'{theme_id}: sources — откуда тема (олимпиада, книга, курс, идеи), непустые строки')
    return errors


def validate_coverage(data: object) -> list[str]:
    """Весь файл data/coverage.json: темы — чтобы сборка падала с понятным сообщением."""
    if not isinstance(data, dict):
        return ['data/coverage.json — словарь с ключом themes']
    errors: list[str] = []
    if 'themes' not in data:
        errors.append('нет ключа themes')
    else:
        errors += validate_themes(data['themes'])
    return errors


def _haystack(record: dict) -> str:
    answer_id = (record.get('answer') or {}).get('optionId')
    answer = [option['zh'] for option in record['options'] if option['id'] == answer_id]
    return _fold(' '.join([record['questionRu'], record.get('questionZh') or ''] + answer))


def _fold(text: str) -> str:
    # «учёных» и «ученых» — одно слово: в банке встречаются оба написания
    return text.lower().replace('ё', 'е')


CYRILLIC = re.compile(r'[а-я]')


def _pattern(word: str) -> re.Pattern:
    folded = re.escape(_fold(word))
    # русское слово — с начала слова, иероглифы — где угодно (в китайском нет пробелов)
    return re.compile(r'(?<![а-я])' + folded if CYRILLIC.match(_fold(word)) else folded)


def theme_matches(bank: list[dict], themes: list[dict]) -> dict[str, list[str]]:
    texts = [(record['id'], _haystack(record)) for record in bank]
    result: dict[str, list[str]] = {}
    for theme in themes:
        patterns = [_pattern(word) for word in theme['match']]
        result[theme['id']] = [record_id for record_id, text in texts if any(p.search(text) for p in patterns)]
    return result


def topic_shares(bank: list[dict]) -> dict[str, dict]:
    olympiad = [record for record in bank if record.get('occurrences')]
    return {topic: {'olympiad': sum(1 for r in olympiad if r.get('topic') == topic) / len(olympiad) if olympiad else 0,
                    'bank': sum(1 for r in bank if r.get('topic') == topic)}
            for topic in TOPICS}


def coverage_report(bank: list[dict], themes: list[dict]) -> str:
    """Отчёт по уже отфильтрованному для сайта банку."""
    matches = theme_matches(bank, themes)
    shares = topic_shares(bank)
    available = 'доступен' if len(bank) % 10 == 1 and len(bank) % 100 != 11 else 'доступны'
    lines = ['# Карта покрытия', '',
             f'На сайте {available} {len(bank)} {questions_word(len(bank))}. '
             'Скрытые вопросы исключены тем же фильтром `data/site.json`, что используется при сборке сайта, '
             'с учётом разрешённых встраиваний и отдельных исключений. Отдельный раздел «Чэнъюй» в эту карту не входит.', '',
             'Отчёт пишет сборка (`scripts/coverage_map.py`), темы — `data/coverage.json`. '
             'Счёт по словам в тексте вопроса и правильном ответе — приблизительный: '
             'вопрос может попасть в несколько тем, а слово — поймать чужой вопрос. '
             'Несколько вопросов об одном факте не означают широкий охват темы; число вопросов '
             'не доказывает её содержательную полноту. Отметка «мало» означает 1–2 вопроса и служит поводом для проверки.', '',
             '## Категории', '',
             'Доля среди олимпиадных считается только по доступным олимпиадным записям: '
             'каждая учитывается один раз независимо от числа появлений в бланках. '
             'Доли описывают текущий состав, а не задают квоты пополнения.', '',
             '| Категория | Доля среди олимпиадных | На сайте | Доля на сайте |', '|---|---|---|---|']
    for topic in TOPICS:
        have = shares[topic]['bank']
        share = round(have / len(bank) * 100) if bank else 0
        lines.append(f'| {topic} | {round(shares[topic]["olympiad"] * 100)} % | {have} | {share} % |')
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
    sparse = sorted((theme for theme in themes if 0 < len(matches[theme['id']]) < FEW),
                    key=lambda theme: len(matches[theme['id']]))
    lines += ['', '## Темы с 1–2 вопросами', '']
    lines += [f'- {theme["title"]} — {len(matches[theme["id"]])} {questions_word(len(matches[theme["id"]]))} '
              f'({theme["topic"]})' for theme in sparse] or ['- нет']
    covered = {record_id for ids in matches.values() for record_id in ids}
    outside = [record for record in bank if record['id'] not in covered]
    lines += ['', '## Вопросы вне тем', '',
              f'Не отнесено ни к одной теме: {len(outside)} {questions_word(len(outside))}. '
              'По ним видно, чего не хватает списку тем.', '']
    lines += [f'- `{record["id"]}` — {record["questionRu"][:100]}' for record in outside] or ['- нет']
    return '\n'.join(lines) + '\n'


def main() -> None:
    bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
    data = json.loads((ROOT / 'data/coverage.json').read_text('utf-8'))
    errors = validate_coverage(data)
    if errors:
        raise SystemExit('некорректные темы data/coverage.json:\n - ' + '\n - '.join(errors))
    bank = site_bank(bank, load_settings(ROOT / 'data/site.json'), embedded_by(ROOT / 'data/dossiers'))
    (ROOT / 'data/review/coverage.md').write_text(coverage_report(bank, data['themes']), encoding='utf-8')
    matches = theme_matches(bank, data['themes'])
    empty = sum(1 for ids in matches.values() if not ids)
    print(f'карта покрытия сайта: вопросов {len(bank)}, тем {len(data["themes"])}, пустых {empty}; '
          'отчёт: data/review/coverage.md')


if __name__ == '__main__':
    main()
