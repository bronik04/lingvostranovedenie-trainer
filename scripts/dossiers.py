"""Досье: таблица проверенных фактов по одной теме и вопросы, которые ссылаются на её ячейки.

Спецификация — docs/superpowers/specs/2026-10-14-dossier-money-pilot-design.md.
Вопрос не пишет варианты сам: правильный — ячейка таблицы, неверные — та же колонка в
соседних строках (общий набор), подписи к ним — из ячеек. В банк идут только вопросы,
принятые автором (`status: "accepted"`).
"""

from __future__ import annotations

import re

from authored import evidence_errors
from glosses import MAX_LENGTH
from normalize import CYRILLIC

KINDS = {'zh', 'ru'}
TABLE_FIELDS = {'columns', 'rows', 'required', 'datedQuestions'}
ROW_SERVICE_FIELDS = {'id', 'sources', 'olympiad'}
CELL_FIELDS = {'zh', 'ru', 'gloss'}
MIN_SOURCES = 2
SLUG = re.compile(r'[a-z0-9][a-z0-9-]*')


def _cell_errors(where: str, cell: object) -> list[str]:
    if not isinstance(cell, dict):
        return [f'{where}: ячейка-вариант должна быть объектом']
    errors: list[str] = []
    unknown = set(cell) - CELL_FIELDS
    if unknown:
        errors.append(f'{where}: неизвестные поля ячейки {sorted(unknown)}')
    zh = cell.get('zh')
    if not isinstance(zh, str) or not zh.strip():
        errors.append(f'{where}: пустой текст варианта')
    elif CYRILLIC.search(zh):
        errors.append(f'{where}: текст варианта не по-китайски: {zh!r}')
    names = cell.get('ru', [])
    if not isinstance(names, list) or not all(isinstance(name, str) and name.strip() for name in names):
        errors.append(f'{where}: ru — список русских названий')
    gloss = cell.get('gloss')
    if gloss is not None:
        if not isinstance(gloss, str) or not gloss.strip() or '\n' in gloss:
            errors.append(f'{where}: подпись — одна непустая строка')
        elif len(gloss) > MAX_LENGTH:
            errors.append(f'{where}: подпись длиннее {MAX_LENGTH} символов')
    return errors


def _source_errors(where: str, sources: object) -> list[str]:
    if not isinstance(sources, list) or len(sources) < MIN_SOURCES:
        return [f'{where}: нужно не меньше {MIN_SOURCES} источников']
    errors = [f'{where}: {message}' for message in evidence_errors(sources)]
    for index, item in enumerate(sources, start=1):
        if isinstance(item, dict) and (not isinstance(item.get('quote'), str) or not item['quote'].strip()):
            errors.append(f'{where}: у источника {index} нет цитаты')
    urls = [item.get('url') for item in sources if isinstance(item, dict)]
    if len(set(urls)) != len(urls):
        errors.append(f'{where}: источники повторяются')
    return errors


def _row_errors(name: str, index: int, row: object, table: dict, seen_rows: set[str]) -> list[str]:
    if not isinstance(row, dict):
        return [f'{name}: строка {index} должна быть объектом']
    columns = table['columns']
    row_id = row.get('id')
    where = f'{name}/{row_id}' if isinstance(row_id, str) else f'{name}/строка {index}'
    errors: list[str] = []
    if not isinstance(row_id, str) or not SLUG.fullmatch(row_id):
        errors.append(f'{where}: нет id строки (латиница, цифры, дефис)')
    elif row_id in seen_rows:
        errors.append(f'{where}: повторяющийся id строки')
    else:
        seen_rows.add(row_id)
    unknown = set(row) - set(columns) - ROW_SERVICE_FIELDS
    if unknown:
        errors.append(f'{where}: необъявленные колонки {sorted(unknown)}')
    for column in table.get('required', []):
        if column not in row:
            errors.append(f'{where}: нет обязательной колонки {column}')
    for column, kind in columns.items():
        if column not in row:
            continue
        if kind == 'zh':
            errors += _cell_errors(f'{where}.{column}', row[column])
        elif not isinstance(row[column], str) or not row[column].strip():
            errors.append(f'{where}.{column}: описательная ячейка — непустая строка')
    errors += _source_errors(where, row.get('sources'))
    olympiad = row.get('olympiad', [])
    if not isinstance(olympiad, list) or not all(isinstance(item, str) for item in olympiad):
        errors.append(f'{where}: olympiad — список id олимпиадных вопросов')
    return errors


def validate_dossier(dossier: object) -> list[str]:
    if not isinstance(dossier, dict):
        return ['досье должно быть объектом']
    errors: list[str] = []
    if not isinstance(dossier.get('id'), str) or not re.fullmatch(r'[a-z][a-z0-9-]*', dossier['id']):
        errors.append('у досье нет id (латиница, цифры, дефис)')
    if not isinstance(dossier.get('title'), str) or not dossier['title'].strip():
        errors.append('у досье нет названия')
    tables = dossier.get('tables')
    if not isinstance(tables, dict) or not tables:
        return errors + ['в досье нет таблиц']
    # id строки — id варианта в банке, поэтому он уникален во всём досье, а не только в таблице
    seen_rows: set[str] = set()
    for name, table in tables.items():
        if not isinstance(table, dict):
            errors.append(f'{name}: таблица должна быть объектом')
            continue
        unknown = set(table) - TABLE_FIELDS
        if unknown:
            errors.append(f'{name}: неизвестные поля таблицы {sorted(unknown)}')
        columns = table.get('columns')
        if not isinstance(columns, dict) or not columns or any(kind not in KINDS for kind in columns.values()):
            errors.append(f'{name}: колонки — словарь имя → zh или ru')
            continue
        reserved = set(columns) & ROW_SERVICE_FIELDS
        if reserved:
            errors.append(f'{name}: имена колонок заняты служебными полями {sorted(reserved)}')
        required = table.get('required', [])
        if not isinstance(required, list) or any(column not in columns for column in required):
            errors.append(f'{name}: required называет необъявленную колонку')
            table = {**table, 'required': []}
        if not isinstance(table.get('datedQuestions', False), bool):
            errors.append(f'{name}: datedQuestions — true или false')
        rows = table.get('rows')
        if not isinstance(rows, list):
            errors.append(f'{name}: rows должен быть списком')
            continue
        for index, row in enumerate(rows, start=1):
            errors += _row_errors(name, index, row, table, seen_rows)
    return errors


EVIDENCE_FIELDS = ('title', 'url', 'checkedAt', 'authority')


def _rows(dossier: dict, table: str) -> dict[str, dict]:
    return {row['id']: row for row in dossier['tables'][table]['rows']}


def answer_cell(question: dict, dossier: dict) -> tuple[str, dict]:
    fact = question['fact']
    rows = _rows(dossier, fact['table'])
    if 'options' in fact:
        ref = fact['answer']
        return ref['row'], rows[ref['row']][ref['column']]
    return fact['row'], rows[fact['row']][fact['ask']]


def _candidates(question: dict, dossier: dict) -> list[tuple[str, dict]]:
    """Все неверные варианты по порядку таблицы, ещё без сведения повторов."""
    fact = question['fact']
    rows = _rows(dossier, fact['table'])
    if 'options' in fact:
        return [(ref['row'], rows[ref['row']][ref['column']])
                for ref in fact['options'] if ref != fact['answer']]
    excluded = set(question.get('exclude', []))
    where = fact.get('where', {})
    return [(row_id, row[fact['ask']]) for row_id, row in rows.items()
            if row_id != fact['row'] and row_id not in excluded and fact['ask'] in row
            and all(column in row and row[column]['zh'] == value for column, value in where.items())]


def question_options(question: dict, dossier: dict) -> tuple[list[dict], str]:
    answer_id, answer = answer_cell(question, dossier)
    options = [{'id': answer_id, 'zh': answer['zh'].strip()}]
    seen = {options[0]['zh']}
    for row_id, cell in _candidates(question, dossier):
        text = cell['zh'].strip()
        if text in seen:
            continue
        seen.add(text)
        option = {'id': row_id, 'zh': text}
        if cell.get('gloss'):
            option['gloss'] = cell['gloss'].strip()
        options.append(option)
    return options, answer_id


def dossier_records(dossier: dict, questions: list[dict]) -> list[dict]:
    rows = {row['id']: row for table in dossier['tables'].values() for row in table['rows']}
    records = []
    for question in questions:
        if question['status'] != 'accepted':
            continue
        options, answer_id = question_options(question, dossier)
        records.append({
            'id': question['id'],
            'origin': 'addition',
            'dossier': dossier['id'],
            'topic': question['topic'],
            'topicSource': 'authored',
            'questionRu': question['questionRu'],
            'questionZh': None,
            'options': options,
            'answer': {'optionId': answer_id, 'state': 'verified'},
            'explanation': {'ru': question['explanation'].strip()},
            'evidence': [{key: item[key] for key in EVIDENCE_FIELDS} for item in rows[answer_id]['sources']],
            'occurrences': [],
            'parseWarnings': [],
        })
    return records
