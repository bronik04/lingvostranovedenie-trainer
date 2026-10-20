"""Отчёт о пробелах и граф ядра досье.

Карта покрытия (`scripts/coverage_map.py`) считает вопросы по словам; этот отчёт показывает, чего
не хватает сети. Ядро темы размечено в таблицах досье: строка — `core: true`, таблица — `sides`
(стороны, по которым спрашивают ядро). По досье без разметки — «каркас не утверждён» и базовые
цифры; по ядру — матрица «строка × сторона», прогноз (строки ядра, которых олимпиада ещё не
спрашивала), вопросы о строках вне ядра, изолированные узлы и ссылки в темы без каркаса. Сверху —
олимпиада по годам и этапам. Граф — папка заметок в формате Obsidian (`data/review/graph/`):
заметка на досье и на строку ядра, связи — `[[ссылки]]`. Спецификация —
docs/superpowers/specs/2026-10-20-dossier-core-network-design.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from dossiers import LINK_FIELDS, dossier_paths, fact_place  # noqa: E402
from strict_json import loads_unique  # noqa: E402
from taxonomy import TOPICS  # noqa: E402

STAGES = ['школьный', 'муниципальный', 'региональный', 'заключительный', 'пригласительный']
EMPTY = '—'


def _accepted(dossier: dict, questions: list[dict], bank: list[dict]) -> list[tuple[str, str, str, str]]:
    """Принятые вопросы досье: (id записи банка, текст, строка ответа, сторона). У встроенного
    вопроса запись — олимпиадная; текст берётся из банка, если запись уже там (с правками)."""
    by_id = {record['id']: record for record in bank}
    result = []
    for question in questions:
        if question['status'] != 'accepted':
            continue
        record_id = question.get('embeds', question['id'])
        text = by_id.get(record_id, {}).get('questionRu') or question.get('questionRu', '')
        place, side = fact_place(question, dossier)
        result.append((record_id, text, place, side))
    return result


def _rows(loaded: list[tuple[dict, list[dict]]]) -> dict[str, tuple[dict, str, dict]]:
    """Все строки всех досье: `досье/таблица/строка` → (досье, таблица, строка)."""
    return {f'{dossier["id"]}/{name}/{row["id"]}': (dossier, name, row)
            for dossier, _ in loaded for name, table in dossier['tables'].items() for row in table['rows']}


def _core_tables(dossier: dict) -> list[str]:
    return [name for name, table in dossier['tables'].items() if any(row.get('core') for row in table['rows'])]


def _links(row: dict) -> list[str]:
    return [cell[field] for cell in row.values() if isinstance(cell, dict) for field in LINK_FIELDS if field in cell]


def _node(place: str) -> str:
    dossier_id, _, row_id = place.split('/')
    return f'{dossier_id}.{row_id}'


def _count_table(title: str, keys: list[str], counts: dict[str, dict[str, int]]) -> list[str]:
    lines = [f'| {title} | ' + ' | '.join(keys) + ' | Всего |', '|' + '---|' * (len(keys) + 2)]
    for topic in TOPICS:
        if topic in counts:
            row = counts[topic]
            lines.append(f'| {topic} | ' + ' | '.join(str(row.get(key, 0)) for key in keys)
                         + f' | {sum(row.values())} |')
    return lines


def _olympiad_lines(bank: list[dict]) -> list[str]:
    by_year: dict[str, dict[str, int]] = {}
    by_stage: dict[str, dict[str, int]] = {}
    for record in bank:
        for occurrence in record.get('occurrences') or []:
            for counts, key in ((by_year, occurrence.get('year')), (by_stage, occurrence.get('stage'))):
                if key:
                    row = counts.setdefault(record.get('topic'), {})
                    row[key] = row.get(key, 0) + 1
    years = sorted({year for row in by_year.values() for year in row})
    stages = sorted({stage for row in by_stage.values() for stage in row},
                    key=lambda s: (STAGES.index(s) if s in STAGES else len(STAGES), s))
    lines = ['## Олимпиада по годам', '',
             'Число появлений олимпиадных заданий по категориям: сколько раз тему спрашивали.', '']
    lines += _count_table('Категория', years, by_year) if years else ['- олимпиадных заданий нет']
    lines += ['', '## Олимпиада по этапам', '']
    lines += _count_table('Категория', stages, by_stage) if stages else ['- олимпиадных заданий нет']
    return lines


def _baseline(dossier: dict, accepted: list[tuple[str, str, str, str]], questions: list[dict]) -> list[str]:
    sides: dict[str, set[str]] = {}
    for _, _, place, side in accepted:
        sides.setdefault(place, set()).add(side)
    rows = sum(len(table['rows']) for table in dossier['tables'].values())
    embedded = sum(1 for q in questions if q['status'] == 'accepted' and 'embeds' in q)
    return [f'- строк: {rows}', f'- принятых вопросов: {len(accepted)}', f'- строк с вопросом: {len(sides)}',
            f'- строк, спрошенных с двух и более сторон (разные колонки ответа): '
            f'{sum(1 for s in sides.values() if len(s) > 1)}',
            f'- встроено олимпиадных: {embedded}']


def _core_lines(dossier: dict, accepted: list[tuple[str, str, str, str]]) -> list[str]:
    lines: list[str] = []
    counts: dict[tuple[str, str], int] = {}
    for _, _, place, side in accepted:
        counts[(place, side)] = counts.get((place, side), 0) + 1
    outside: list[str] = []
    for name in _core_tables(dossier):
        table = dossier['tables'][name]
        sides = table.get('sides', [])
        lines += [f'#### Таблица `{name}`', '']
        if not sides:
            lines += ['Стороны не утверждены (`sides`).', '']
        lines += ['| строка | ' + ' | '.join(sides + ['олимпиада']) + ' |', '|' + '---|' * (len(sides) + 2)]
        core = set()
        for row in table['rows']:
            if not row.get('core'):
                continue
            place = f'{dossier["id"]}/{name}/{row["id"]}'
            core.add(place)
            cells = [str(counts[(place, side)]) if counts.get((place, side)) else EMPTY for side in sides]
            cells.append('да' if row.get('olympiad') else 'прогноз')
            lines.append(f'| {row["id"]} | ' + ' | '.join(cells) + ' |')
        lines.append('')
        prefix = f'{dossier["id"]}/{name}/'
        outside += [f'- {record_id} — {text}' for record_id, text, place, _ in accepted
                    if place.startswith(prefix) and place not in core]
    lines += ['#### Вопросы о строках вне ядра', '',
              'Кандидаты на перебор: встроить в ядро, переделать или снять в архив.', '']
    lines += outside or ['- нет']
    return lines


def _link_lines(loaded: list[tuple[dict, list[dict]]]) -> list[str]:
    rows = _rows(loaded)
    core = {place for place, (_, _, row) in rows.items() if row.get('core')}
    with_core = {(dossier['id'], name) for dossier, _ in loaded for name in _core_tables(dossier)}
    incoming = {target for _, _, row in rows.values() for target in _links(row)}
    isolated, no_core, outside = [], [], []
    for place in sorted(core):
        targets = _links(rows[place][2])
        if not targets and place not in incoming:
            isolated.append(f'- {place}')
        for target in targets:
            if target in core:
                continue
            dossier_id, table, _ = target.split('/')
            (outside if (dossier_id, table) in with_core else no_core).append(f'- {place} → {target}')
    return (['## Связи', '', '### Строки ядра без связей — изолированные узлы', '', 'Строки ядра без ссылок наружу и на себя.', '']
            + (isolated or ['- нет'])
            + ['', '### Ссылка из ядра ведёт в тему без каркаса', ''] + (no_core or ['- нет'])
            + ['', '### Ссылка из ядра ведёт в строку вне ядра', ''] + (outside or ['- нет']))


def network_report(loaded: list[tuple[dict, list[dict]]], bank: list[dict]) -> str:
    with_core = sum(1 for dossier, _ in loaded if _core_tables(dossier))
    lines = ['# Сеть досье: пробелы', '',
             'Файл пишет сборка (`scripts/network.py`). Ядро размечается в таблицах досье: `core` у строки, '
             '`sides` у таблицы. Граф для Obsidian — папка `data/review/graph/`: сборка каждый раз стирает в ней '
             'все заметки `*.md` и пишет заново, поэтому свои заметки в эту папку не кладите.', '',
             f'Досье: {len(loaded)}, с утверждённым каркасом: {with_core}.', '']
    lines += _olympiad_lines(bank)
    lines += ['', '## Досье']
    for dossier, questions in loaded:
        accepted = _accepted(dossier, questions, bank)
        lines += ['', f'### {dossier["title"]} (`{dossier["id"]}`)', '']
        if _core_tables(dossier):
            lines += _core_lines(dossier, accepted)
        else:
            lines += ['Ядро не размечено: каркас не утверждён.', ''] + _baseline(dossier, accepted, questions)
    lines += [''] + _link_lines(loaded)
    return '\n'.join(lines) + '\n'


def _title(row: dict, table: dict) -> str:
    first = next((column for column, kind in table['columns'].items() if kind == 'zh'), None)
    cell = row.get(first) if first else None
    if not isinstance(cell, dict):
        return row['id']
    ru = cell.get('ru') or []
    return f'{cell["zh"]} — {ru[0]}' if ru else cell['zh']


def graph_notes(loaded: list[tuple[dict, list[dict]]], bank: list[dict]) -> dict[str, str]:
    notes: dict[str, str] = {}
    for dossier, questions in loaded:
        accepted = _accepted(dossier, questions, bank)
        core_rows = [(name, row) for name, table in dossier['tables'].items() for row in table['rows'] if row.get('core')]
        body = [f'[[{dossier["id"]}.{row["id"]}]]' for _, row in core_rows] or ['Каркас не утверждён.']
        notes[f'{dossier["id"]}.md'] = '\n'.join([f'# {dossier["title"]}', '', *body]) + '\n'
        for name, row in core_rows:
            place = f'{dossier["id"]}/{name}/{row["id"]}'
            lines = [f'# {_title(row, dossier["tables"][name])}', '', f'Тема: [[{dossier["id"]}]]', '']
            links = _links(row)
            if links:
                lines += ['Связи:', *(f'- [[{_node(target)}]]' for target in links), '']
            lines += ['Вопросы:']
            lines += [f'- {side}: {record_id} — {text}' for record_id, text, p, side in accepted if p == place] or ['- нет']
            olympiad = row.get('olympiad') or []
            lines += ['', f'Олимпиада: {", ".join(olympiad)}' if olympiad else 'Олимпиада: ещё не спрашивала (прогноз)']
            notes[f'{_node(place)}.md'] = '\n'.join(lines) + '\n'
    return notes


def write_graph(directory: Path, notes: dict[str, str]) -> None:
    """Пишет заметки заново: старые `*.md` стираются (строка могла выйти из ядра), прочее — например,
    настройки Obsidian `.obsidian/` — остаётся."""
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.glob('*.md'):
        path.unlink()
    for name, text in notes.items():
        (directory / name).write_text(text, encoding='utf-8')


def main() -> None:
    bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
    loaded = [(loads_unique(table.read_text('utf-8'), 'досье'), loads_unique(questions.read_text('utf-8'), 'вопросах досье'))
              for table, questions in dossier_paths(ROOT / 'data/dossiers')]
    (ROOT / 'data/review/network.md').write_text(network_report(loaded, bank), encoding='utf-8')
    notes = graph_notes(loaded, bank)
    write_graph(ROOT / 'data/review/graph', notes)
    with_core = sum(1 for dossier, _ in loaded if _core_tables(dossier))
    print(f'сеть: досье {len(loaded)}, с каркасом {with_core}, заметок {len(notes)}; '
          'отчёт: data/review/network.md, граф: data/review/graph/')


if __name__ == '__main__':
    main()
