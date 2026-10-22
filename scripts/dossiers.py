"""Досье: таблица проверенных фактов по одной теме и вопросы, которые ссылаются на её ячейки.

Спецификация — docs/superpowers/specs/2026-10-14-dossier-money-pilot-design.md.
Вопрос не пишет варианты сам: правильный — ячейка таблицы, неверные — та же колонка в
соседних строках (общий набор), подписи к ним — из ячеек. В банк идут только вопросы,
принятые автором (`status: "accepted"`).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from authored import evidence_errors, sentence_count
from glosses import gloss_text_errors
from normalize import CYRILLIC, completeness_errors, fragment_pairs, language_errors, normalize_text
from strict_json import loads_unique
from taxonomy import TOPICS

KINDS = {'zh', 'ru'}
# sides — стороны ядра, core — строка ядра (решение автора 2026-10-21): нет разметки — каркас не утверждён
TABLE_FIELDS = {'columns', 'rows', 'required', 'datedQuestions', 'sides'}
ROW_SERVICE_FIELDS = {'id', 'sources', 'olympiad', 'core', 'skipSides'}
CELL_FIELDS = {'zh', 'ru', 'gloss', 'ref', 'from'}
LINK = re.compile(r'[a-z][a-z0-9-]*/[a-z][a-z0-9_-]*/[a-z0-9][a-z0-9-]*')
LINK_FIELDS = ('ref', 'from')
MIN_SOURCES = 2
SLUG = re.compile(r'[a-z0-9][a-z0-9-]*')
# id исходных вариантов записей банка: строка досье не может так называться (встраивание)
OPTION_ID = re.compile(r'o\d+')


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
        if not isinstance(gloss, str) or not gloss.strip():
            errors.append(f'{where}: подпись — одна непустая строка')
        else:
            # те же правила текста, что у glosses.json: ученик видит подписи одинаково
            errors += [f'{where}: {message}' for message in gloss_text_errors(gloss, zh if isinstance(zh, str) else '')]
    links = [field for field in LINK_FIELDS if field in cell]
    if len(links) > 1:
        errors.append(f'{where}: у ячейки одна ссылка — ref или from')
    for field in links:
        if not isinstance(cell[field], str) or not LINK.fullmatch(cell[field]):
            errors.append(f'{where}: {field} — «досье/таблица/строка»')
    return errors


def _source_errors(where: str, sources: object) -> list[str]:
    if not isinstance(sources, list) or len(sources) < MIN_SOURCES:
        return [f'{where}: нужно не меньше {MIN_SOURCES} источников']
    errors = [f'{where}: {message}' for message in evidence_errors(sources)]
    for index, item in enumerate(sources, start=1):
        if isinstance(item, dict) and (not isinstance(item.get('quote'), str) or not item['quote'].strip()):
            errors.append(f'{where}: у источника {index} нет цитаты')
    urls = [item['url'] for item in sources if isinstance(item, dict) and isinstance(item.get('url'), str)]
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
    elif OPTION_ID.fullmatch(row_id):
        errors.append(f'{where}: id строки вида «o5» зарезервирован за вариантами олимпиадных вопросов')
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
    if not isinstance(row.get('core', False), bool):
        errors.append(f'{where}: core — true или false')
    # стороны, которые автор решил у этой строки не спрашивать (например, узкое происхождение названия)
    skip = row.get('skipSides', [])
    sides = table.get('sides', [])
    if not isinstance(skip, list) or any(not isinstance(side, str) or side not in sides for side in skip):
        errors.append(f'{where}: skipSides — стороны из sides таблицы')
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
        if not isinstance(columns, dict) or not columns or any(not isinstance(kind, str) or kind not in KINDS
                                                                   for kind in columns.values()):
            errors.append(f'{name}: колонки — словарь имя → zh или ru')
            continue
        reserved = set(columns) & ROW_SERVICE_FIELDS
        if reserved:
            errors.append(f'{name}: имена колонок заняты служебными полями {sorted(reserved)}')
        required = table.get('required', [])
        if not isinstance(required, list) or any(not isinstance(column, str) or column not in columns
                                                 for column in required):
            errors.append(f'{name}: required называет необъявленную колонку')
            table = {**table, 'required': []}
        if not isinstance(table.get('datedQuestions', False), bool):
            errors.append(f'{name}: datedQuestions — true или false')
        sides = table.get('sides', [])
        if not isinstance(sides, list) or any(not isinstance(side, str) or columns.get(side) != 'zh'
                                              for side in sides):
            errors.append(f'{name}: sides — список колонок zh этой таблицы')
        elif len(set(sides)) != len(sides):
            errors.append(f'{name}: sides: колонки повторяются')
        rows = table.get('rows')
        if not isinstance(rows, list):
            errors.append(f'{name}: rows должен быть списком')
            continue
        for index, row in enumerate(rows, start=1):
            errors += _row_errors(name, index, row, table, seen_rows)
    return errors


def validate_links(dossiers: dict[str, dict]) -> list[str]:
    """Ссылки ячеек на строки того же или других досье: `ref` — тот же персонаж (текст совпадает), `from` — назван по."""
    errors: list[str] = []
    for dossier_id, dossier in dossiers.items():
        for table_name, table in dossier['tables'].items():
            for row in table['rows']:
                for column, kind in table['columns'].items():
                    cell = row.get(column)
                    if kind != 'zh' or not isinstance(cell, dict):
                        continue
                    for field in LINK_FIELDS:
                        if field not in cell:
                            continue
                        where = f'{dossier_id}/{table_name}/{row["id"]}.{column}'
                        target_dossier, target_table, target_row = cell[field].split('/')
                        rows = {item['id']: item for item in
                                dossiers.get(target_dossier, {}).get('tables', {}).get(target_table, {}).get('rows', [])}
                        target = rows.get(target_row)
                        if target is None:
                            errors.append(f'{where}: {field} ведёт в несуществующую строку {cell[field]}')
                        elif field == 'ref':
                            name = target.get('name', {}).get('zh') if isinstance(target.get('name'), dict) else None
                            if name != cell['zh']:
                                errors.append(f'{where}: ref {cell[field]} — у строки другое название '
                                              f'({name!r} ≠ {cell["zh"]!r})')
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


def _candidate_glosses(question: dict, dossier: dict) -> dict[str, str]:
    glosses: dict[str, str] = {}
    for _, cell in _candidates(question, dossier):
        if cell.get('gloss'):
            glosses.setdefault(cell['zh'].strip(), cell['gloss'].strip())
    return glosses


def _column_glosses(question: dict, dossier: dict) -> dict[str, set[str]]:
    fact = question['fact']
    glosses: dict[str, set[str]] = {}
    for row in dossier['tables'][fact['table']]['rows']:
        cell = row.get(fact['ask'])
        if isinstance(cell, dict) and cell.get('gloss'):
            glosses.setdefault(cell['zh'].strip(), set()).add(cell['gloss'].strip())
    return glosses


def original_record(record: dict) -> dict:
    """Запись до встраивания. В bank.json после сборки у встроенной записи уже есть добавленные
    варианты (id строк таблицы), подписи и строка ответа `factRow`; исходные варианты — с id вида o1, o2…"""
    if 'dossier' not in record:
        return record
    options = [{key: value for key, value in option.items() if key != 'gloss'}
               for option in record['options'] if OPTION_ID.fullmatch(option['id'])]
    return {key: value for key, value in record.items() if key not in {'dossier', 'factRow'}} | {'options': options}


def embed_record(record: dict, question: dict, dossier: dict) -> tuple[dict | None, list[str]]:
    """Олимпиадная запись со встроенным набором из таблицы и подписями — и что этому мешает.

    Чистая функция: её зовут слой встраивания (scripts/embeds.py), проверка досье и отчёт.
    """
    answer_id = record.get('answer', {}).get('optionId')
    if record.get('answer', {}).get('state') != 'verified' or answer_id is None:
        return None, [f'ответ {record["id"]} не проверен — встраивать рано']
    answer = next((option for option in record['options'] if option['id'] == answer_id), None)
    if answer is None:
        return None, [f'у {record["id"]} нет варианта-ответа {answer_id}']
    table_options, _ = question_options(question, dossier)
    if answer['zh'].strip() != table_options[0]['zh']:
        return None, [f'ответ {record["id"]} ({answer["zh"].strip()}) не совпадает с ячейкой '
                      f'({table_options[0]["zh"]})']
    errors: list[str] = []
    # подпись исходного варианта — сначала из набора вопроса (where, exclude), иначе из всей
    # колонки, если у этого текста там одна подпись
    own = _candidate_glosses(question, dossier)
    column = _column_glosses(question, dossier)
    options: list[dict] = []
    for option in record['options']:
        option = {key: value for key, value in option.items() if key != 'gloss'}
        if option['id'] != answer_id:
            text = option['zh'].strip()
            gloss = own.get(text)
            if gloss is None and len(column.get(text, ())) == 1:
                gloss = next(iter(column[text]))
            if gloss is not None:
                option['gloss'] = gloss
            elif column.get(text):
                errors.append(f'для варианта {text} в таблице несколько подписей — уточните where или exclude')
            else:
                errors.append(f'для варианта {text} нет ячейки с подписью в таблице')
        options.append(option)
    ids = {option['id'] for option in options}
    texts = {option['zh'].strip() for option in options}
    for added in table_options[1:]:
        if added['zh'] in texts:
            continue
        if added['id'] in ids:
            errors.append(f'id строки {added["id"]} совпадает с id варианта записи')
            continue
        options.append(added)
        ids.add(added['id'])
        texts.add(added['zh'])
    # текст ответа вырезается: неверный вариант может быть частью ответа (荷花 в 荷花王)
    explanation = record.get('explanation', {}).get('ru', '').replace(answer['zh'].strip(), '')
    named = [option['zh'].strip() for option in options
             if option['id'] != answer_id and option['zh'].strip() in explanation]
    if named:
        errors.append(f'пояснение {record["id"]} называет неверные варианты {named} — '
                      'на экране их может не оказаться; правка в editorial.json')
    return {**record, 'options': options, 'dossier': dossier['id'],
            'factRow': fact_place(question, dossier)[0]}, errors


def dossier_records(dossier: dict, questions: list[dict]) -> list[dict]:
    rows = {row['id']: row for table in dossier['tables'].values() for row in table['rows']}
    records = []
    for question in questions:
        if question['status'] != 'accepted' or 'embeds' in question:
            continue
        options, answer_id = question_options(question, dossier)
        records.append({
            'id': question['id'],
            'origin': 'addition',
            'dossier': dossier['id'],
            # строка ответа: раунд не ставит рядом вопросы об одной строке
            'factRow': fact_place(question, dossier)[0],
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


QUESTION_FIELDS = {'id', 'status', 'topic', 'fact', 'questionRu', 'explanation', 'exclude', 'check', 'embeds'}
# встраивание олимпиадного вопроса: текст, пояснение и тема — у олимпиадной записи
EMBED_FIELDS = {'id', 'embeds', 'status', 'fact', 'exclude', 'check'}
EMBED_FACT_FIELDS = {'table', 'row', 'ask', 'where'}
FACT_FIELDS = {'table', 'row', 'ask', 'given', 'where', 'options', 'answer'}
STATUSES = {'draft', 'accepted'}
VERDICTS = {'accept', 'fix', 'drop'}
MIN_WRONG = 3
MIN_EXPLICIT = 4
# год выпуска, а не четырёхзначный номинал («2000 рублей», «1000 юаней»)
YEAR = re.compile(r'(?<!\d)(?:1[6-9]|20)\d\d(?!\d)(?!\s*(?:руб|юан|元|卢布))', re.IGNORECASE)
SERIES = re.compile(r'сери', re.IGNORECASE)
# окончания русских слов: подсказка «хризантемой» — та же «хризантема»
ENDINGS = sorted(['ами', 'ями', 'ого', 'его', 'ому', 'ему', 'ыми', 'ими', 'ых', 'их', 'ой', 'ей', 'ий', 'ый',
                  'ая', 'яя', 'ое', 'ее', 'ую', 'юю', 'ов', 'ев', 'ам', 'ям', 'ах', 'ях', 'ом', 'ем',
                  'а', 'я', 'ь', 'й', 'о', 'е', 'ы', 'и', 'у', 'ю'], key=len, reverse=True)
MIN_STEM = 3


def _stem(word: str) -> str:
    for ending in ENDINGS:
        if word.endswith(ending) and len(word) - len(ending) >= MIN_STEM:
            return word[:-len(ending)]
    return word


SURNAME = re.compile(r'[А-ЯЁ]\w*(?:ов|ев|ёв|ин|ын)$')


def _name_pattern(name: str) -> re.Pattern:
    words = re.findall(r'\w+', name)
    if not words or not CYRILLIC.search(name):
        return re.compile(re.escape(name.lower()))
    # фамилия на -ов/-ев/-ин склоняется после суффикса (Меньшова, Меньшову): без него основа
    # «меньш» находила бы «меньше» и «меньшего»
    stems = [word.lower() if SURNAME.match(word) else _stem(word.lower()) for word in words]
    return re.compile(r'(?<!\w)' + r'\W+'.join(re.escape(stem) + r'\w*' for stem in stems))


def _mentions(text: str, cell: dict) -> list[str]:
    """Названия ответа, которые стоят в тексте: китайское — как есть, русские — в любом падеже."""
    lowered = text.lower()
    return [name for name in [cell['zh'], *cell.get('ru', [])]
            if name.strip() and _name_pattern(name).search(lowered)]


def _reference_errors(where: str, question: dict, dossier: dict) -> list[str]:
    fact = question.get('fact')
    if not isinstance(fact, dict):
        return [f'{where}: нет fact']
    errors: list[str] = []
    unknown = set(fact) - FACT_FIELDS
    if unknown:
        errors.append(f'{where}: неизвестные поля fact {sorted(unknown)}')
    table = dossier['tables'].get(fact['table']) if isinstance(fact.get('table'), str) else None
    if table is None:
        return errors + [f'{where}: нет таблицы {fact.get("table")!r}']
    columns = table['columns']
    rows = {row['id']: row for row in table['rows']}

    def cell_ref(label: str, row_id: object, column: object) -> list[str]:
        if not isinstance(row_id, str) or row_id not in rows:
            return [f'{where}: {label} — нет строки {row_id!r}']
        if not isinstance(column, str) or columns.get(column) != 'zh':
            return [f'{where}: {label} — колонка {column!r} не может быть вариантом']
        if column not in rows[row_id]:
            return [f'{where}: {label} — у строки {row_id} нет ячейки {column}']
        return []

    if 'options' in fact:
        extra = ({'row', 'ask', 'given', 'where'} & set(fact)) | ({'exclude'} if question.get('exclude') else set())
        if extra:
            errors.append(f'{where}: вопрос с явными вариантами не использует {sorted(extra)}')
        refs = fact['options']
        if (not isinstance(refs, list) or len(refs) < MIN_EXPLICIT
                or not all(isinstance(ref, dict) and set(ref) == {'row', 'column'} for ref in refs)):
            return errors + [f'{where}: options — не меньше четырёх ссылок {{row, column}}']
        for index, ref in enumerate(refs, start=1):
            errors += cell_ref(f'вариант {index}', ref['row'], ref['column'])
        named = [ref['row'] for ref in refs if isinstance(ref['row'], str)]
        if len(set(named)) != len(named):
            errors.append(f'{where}: одна строка — не больше одного варианта')
        if fact.get('answer') not in refs:
            errors.append(f'{where}: answer — не один из вариантов')
        return errors

    errors += cell_ref('ask', fact.get('row'), fact.get('ask'))
    if 'answer' in fact:
        errors.append(f'{where}: answer бывает только у вопроса с явными вариантами')
    if 'given' in fact:
        if fact['given'] == fact.get('ask'):
            errors.append(f'{where}: given совпадает с ask')
        else:
            errors += cell_ref('given', fact.get('row'), fact['given'])
    condition = fact.get('where', {})
    if not isinstance(condition, dict) or any(columns.get(column) != 'zh' for column in condition):
        errors.append(f'{where}: where — равенство по колонкам рода zh')
    elif isinstance(fact.get('row'), str) and fact['row'] in rows:
        answer_row = rows[fact['row']]
        if not all(column in answer_row and answer_row[column]['zh'] == value for column, value in condition.items()):
            errors.append(f'{where}: строка ответа не проходит where')
    exclude = question.get('exclude', [])
    if not isinstance(exclude, list) or any(not isinstance(row_id, str) or row_id not in rows for row_id in exclude):
        errors.append(f'{where}: exclude называет строку не из этой таблицы')
    elif fact.get('row') in exclude:
        errors.append(f'{where}: exclude убирает строку ответа')
    return errors


def _embed_errors(where: str, question: dict, embedded: set[str]) -> list[str]:
    target = question.get('embeds')
    if not isinstance(target, str) or not target.strip():
        return [f'{where}: embeds — id записи банка']
    errors: list[str] = []
    if target in embedded:
        errors.append(f'{where}: запись {target} уже встроена другим вопросом')
    embedded.add(target)
    extra = sorted(set(question) - EMBED_FIELDS)
    if extra:
        errors.append(f'{where}: у встраивания нет полей {extra} — текст, пояснение и тема у олимпиадной записи')
    fact = question.get('fact')
    if isinstance(fact, dict) and set(fact) - EMBED_FACT_FIELDS:
        errors.append(f'{where}: встраивание спрашивает колонку — без {sorted(set(fact) - EMBED_FACT_FIELDS)}')
    return errors


def _content_errors(where: str, question: dict, dossier: dict) -> list[str]:
    """Проверки, которым нужны целые ссылки: набор вариантов и текст вопроса."""
    errors: list[str] = []
    fact = question['fact']
    _, answer = answer_cell(question, dossier)
    twins = [row_id for row_id, cell in _candidates(question, dossier) if cell['zh'].strip() == answer['zh'].strip()]
    if twins:
        errors.append(f'{where}: неверный вариант совпадает с правильным: {twins}')
    options, _ = question_options(question, dossier)
    embedded = 'embeds' in question
    if not embedded and len(options) - 1 < MIN_WRONG:
        errors.append(f'{where}: в наборе меньше {MIN_WRONG} неверных вариантов')
    unglossed = [option['id'] for option in options[1:] if 'gloss' not in option]
    if unglossed:
        errors.append(f'{where}: у неверных вариантов нет подписи: {unglossed}')
    if embedded:
        return errors
    text = question['questionRu']
    hints = _mentions(text, answer)
    if hints:
        errors.append(f'{where}: вопрос называет свой ответ: {hints}')
    if 'given' in fact:
        given = _rows(dossier, fact['table'])[fact['row']][fact['given']]
        if given['zh'] not in text:
            errors.append(f'{where}: вопрос не называет значение given {given["zh"]!r}')
    if dossier['tables'][fact['table']].get('datedQuestions') and not (YEAR.search(text) or SERIES.search(text)):
        errors.append(f'{where}: вопрос не называет год или серию')
    return errors


def validate_questions(questions: object, dossier: dict, bank: list[dict] | None = None,
                       groups: dict[str, list[str]] | None = None) -> list[str]:
    """`bank` — записи банка без вопросов этого досье: с ними сверяются повторы формулировок.
    `groups` — группы фактов (`fact-groups.json`): вопросы одной группы друг другу не утечка."""
    if not isinstance(questions, list):
        return ['вопросы досье должны быть списком']
    errors: list[str] = []
    seen: set[str] = set()
    whole: list[dict] = []
    embedded_targets: set[str] = set()
    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            errors.append(f'вопрос {index} должен быть объектом')
            continue
        question_id = question.get('id')
        named = isinstance(question_id, str) and re.fullmatch(rf'{re.escape(dossier["id"])}-q\d+', question_id)
        where = question_id if named else f'вопрос {index}'
        if not named:
            errors.append(f'{where}: id — «{dossier["id"]}-qNN»')
        elif question_id in seen:
            errors.append(f'{where}: повторяющийся id')
            named = False
        else:
            seen.add(question_id)
        unknown = set(question) - QUESTION_FIELDS
        if unknown:
            errors.append(f'{where}: неизвестные поля вопроса {sorted(unknown)}')
        status = question.get('status')
        if not isinstance(status, str) or status not in STATUSES:
            errors.append(f'{where}: status — draft или accepted')
        embeds = 'embeds' in question
        text = None
        if embeds:
            errors += _embed_errors(where, question, embedded_targets)
        else:
            if question.get('topic') not in TOPICS:
                errors.append(f'{where}: тема вне списка семи категорий')
            text = question.get('questionRu')
            if not isinstance(text, str) or not text.strip():
                errors.append(f'{where}: нет текста вопроса')
                text = None
            else:
                # те же правила текста, что проверит сборка банка: ловим их ещё у черновика
                errors += [f'{where}: {message}' for message in language_errors(text, [])]
                errors += [f'{where}: {message}' for message in completeness_errors(text, None, [])]
            if not isinstance(question.get('explanation'), str) or not question['explanation'].strip():
                errors.append(f'{where}: нет пояснения')
            elif not 3 <= sentence_count(question['explanation']) <= 5:
                # то же правило, что у дополнений: сборка банка проверит его снова
                errors.append(f'{where}: пояснение должно состоять из 3–5 предложений')
        check = question.get('check')
        verdict = check.get('verdict') if isinstance(check, dict) else None
        if check is not None and (not isinstance(verdict, str) or verdict not in VERDICTS
                                  or not isinstance(check.get('note', ''), str)):
            errors.append(f'{where}: check — {{verdict: accept | fix | drop, note}}')
        if status == 'accepted' and verdict != 'accept':
            errors.append(f'{where}: принятый вопрос без вердикта проверки accept')
        broken = _reference_errors(where, question, dossier)
        errors += broken
        if not broken and (embeds or text is not None):
            errors += _content_errors(where, question, dossier)
            if named and not embeds:
                whole.append(question)
    # утечки: ответ одного вопроса не должен стоять в тексте другого
    answers = {question['id']: (answer_cell(question, dossier)[1], _answer_place(question, dossier))
               for question in whole}
    group_of = _group_owner(groups)
    for question in whole:
        place = _answer_place(question, dossier)
        for other_id, (answer, other_place) in answers.items():
            if (other_id == question['id'] or _bridged(place, other_place) or _same_row(place, other_place)
                    or _same_group(group_of, question['id'], other_id)):
                continue
            names = _mentions(question['questionRu'], answer)
            if names:
                errors.append(f'{question["id"]}: текст называет ответ вопроса {other_id}: {names}')
    errors += _wording_errors(whole, bank or [])
    return errors


def _answer_column(fact: dict) -> str:
    return fact['answer']['column'] if 'options' in fact else fact['ask']


def fact_place(question: dict, dossier: dict) -> tuple[str, str]:
    """Строка ответа (`досье/таблица/строка`) и сторона, с которой вопрос спрашивает строку: у
    обратного вопроса («какая провинция сокращённо называется 豫?») это `given`, иначе колонка ответа."""
    fact = question['fact']
    row_id, _ = answer_cell(question, dossier)
    return f'{dossier["id"]}/{fact["table"]}/{row_id}', fact.get('given') or _answer_column(fact)


def _answer_place(question: dict, dossier: dict) -> tuple[str, str, dict[str, set[str]]]:
    """Строка ответа (`досье/таблица/строка`), колонка ответа и ссылки строки: куда → из каких колонок."""
    place, _ = fact_place(question, dossier)
    fact = question['fact']
    column = _answer_column(fact)
    row_id, _ = answer_cell(question, dossier)
    row = _rows(dossier, fact['table'])[row_id]
    links: dict[str, set[str]] = {}
    for name, cell in row.items():
        if isinstance(cell, dict):
            for field in LINK_FIELDS:
                if field in cell:
                    links.setdefault(cell[field], set()).add(name)
    return place, column, links


def _bridged(place: tuple, other_place: tuple) -> bool:
    """Мостик: текст вопроса о строке может назвать ответ другого вопроса, только если это
    название (`name`) строки, на которую ссылается его строка, или ячейка другой строки,
    которая ссылается на его строку. Остальные ячейки связанной строки — утечка, как у любой."""
    row, _, links = place
    other_row, other_column, other_links = other_place
    return ((other_row in links and other_column == 'name')
            or other_column in other_links.get(row, set()))


def _same_row(place: tuple, other_place: tuple) -> bool:
    """Решение автора 2026-10-21: вопросы об одной строке — разные стороны одного факта, их
    взаимная подсказка не утечка; в один раунд их не ставит `factRow` (src/quiz.mjs)."""
    return place[0] == other_place[0]


def _group_owner(groups: dict[str, list[str]] | None) -> dict[str, str]:
    return {record_id: group_id for group_id, ids in (groups or {}).items() for record_id in ids}


def _same_group(group_of: dict[str, str], left: str, right: str) -> bool:
    """Записи одной группы фактов автор оставил вместе, хотя они подсказывают друг другу: это один
    факт или слово из ответа одного стоит в тексте другого (раунд не ставит их рядом), поэтому их
    взаимная подсказка не утечка."""
    return left in group_of and group_of[left] == group_of.get(right)


def cross_leak_errors(bank: list[dict], loaded: list[tuple[dict, list[dict]]],
                      groups: dict[str, list[str]] | None = None) -> list[str]:
    """Утечки по всем вопросам всех досье сразу — по окончательным текстам.

    Текст встроенного вопроса есть только в банке; текст своего вопроса берётся из банка, если
    запись уже там (с правками editorial.json), иначе — из файла вопросов (черновик).
    Решение автора 2026-10-15: мостик — не утечка (аппарат, связанный ссылкой с мифом, может
    называть его в вопросе о себе), а между досье одиночные иероглифы (唐, 秦) не ищутся — они
    стоят внутри других слов (唐僧, 秦始皇). Решение автора 2026-10-17: мостик — только название
    связанной строки или связующая ячейка (`_bridged`); прочие взаимные подсказки связанных строк
    закрывает группа фактов `groups` — по id записи (у встроенного вопроса — олимпиадной).
    Решение автора 2026-10-21: стороны одной строки — не утечка (`_same_row`).
    """
    by_id = {record['id']: record for record in bank}
    entries: list[tuple[str, str, str, dict, tuple, str]] = []
    for dossier, questions in loaded:
        for question in questions:
            if 'embeds' in question:
                record = by_id.get(question['embeds'])
                if record is None:
                    continue
                # китайская формулировка ученику тоже видна
                text = ' '.join([record['questionRu'], record.get('questionZh') or ''])
            else:
                record = by_id.get(question['id'])
                text = record['questionRu'] if record else question['questionRu']
            entries.append((dossier['id'], f'{dossier["id"]}/{question["id"]}', text,
                            answer_cell(question, dossier)[1], _answer_place(question, dossier),
                            question.get('embeds', question['id'])))
    group_of = _group_owner(groups)
    errors: list[str] = []
    for dossier_id, label, text, _, place, record_id in entries:
        for other_dossier, other, _, answer, other_place, other_record in entries:
            if (other == label or _bridged(place, other_place) or _same_row(place, other_place)
                    or _same_group(group_of, record_id, other_record)):
                continue
            if other_dossier != dossier_id and len(answer['zh'].strip()) == 1:
                answer = {**answer, 'zh': ''}
            names = _mentions(text, answer)
            if names:
                errors.append(f'{label}: текст называет ответ вопроса {other}: {names}')
    return errors

def _wording_errors(questions: list[dict], bank: list[dict]) -> list[str]:
    """Повторы и обрезки формулировок — между вопросами досье и с банком, как в сборке."""
    errors: list[str] = []
    known = {normalize_text(record['questionRu']): record['id'] for record in bank}
    first: dict[str, str] = {}
    for question in questions:
        key = normalize_text(question['questionRu'])
        if key in known:
            errors.append(f'{question["id"]}: формулировка уже есть в базе ({known[key]})')
        elif key in first:
            errors.append(f'{question["id"]}: повторяет формулировку {first[key]}')
        else:
            first[key] = question['id']
    ids = {question['id'] for question in questions}
    pairs = fragment_pairs([(record['id'], record['questionRu']) for record in bank]
                           + [(question['id'], question['questionRu']) for question in questions])
    for left, right in pairs:
        if left in ids or right in ids:
            errors.append(f'{right if right in ids else left}: формулировка выглядит обрезком {left if right in ids else right}')
    return errors


def load_dossier(dossier_path: Path, questions_path: Path, bank: list[dict] | None = None,
                 groups: dict[str, list[str]] | None = None) -> tuple[dict, list[dict]]:
    dossier = loads_unique(dossier_path.read_text('utf-8'), 'досье')
    errors = validate_dossier(dossier)
    if errors:
        raise ValueError(f'некорректное досье {dossier_path.name}:\n - ' + '\n - '.join(errors))
    questions = loads_unique(questions_path.read_text('utf-8'), 'вопросах досье')
    # свои вопросы досье (дополнения) из прошлой сборки не в счёт; встроенные олимпиадные — в счёт
    errors = validate_questions(questions, dossier, [record for record in bank or []
                                                     if not (record.get('origin') == 'addition'
                                                             and record.get('dossier') == dossier['id'])],
                                groups)
    if errors:
        raise ValueError(f'некорректные вопросы {questions_path.name}:\n - ' + '\n - '.join(errors))
    return dossier, questions


def _report_cell(value: object) -> str:
    if value is None:
        return ''
    if isinstance(value, dict):
        # русские названия видны автору: по ним сборка ищет подсказки и утечки
        names = value.get('ru', [])
        text = value['zh'] + (f' ({", ".join(names)})' if names else '')
        link = value.get('ref') or value.get('from')
        if link:
            text += f' → {link}'
    else:
        text = ' '.join(str(value).split())
    return text.replace('|', '\\|')


# первая строка отчёта сборки: по ней сборка отличает свой отчёт от ручного под тем же именем.
# Текст не менять: отчёты на диске со старой меткой остановили бы сборку.
REPORT_MARK = '<!-- Отчёт пишет сборка (scripts/merge_bank.py): не править, перезапишется. -->'
# так начинались отчёты сборки до метки (до 2026-10-17); их тоже можно перезаписать.
# Убрать, когда все ветки досье сольют master и их отчёты получат метку.
LEGACY_REPORT = re.compile(r'# Досье «[^\n]*»\n\nФайл пишет сборка \(`scripts/dossiers\.py`\)\.')


def is_build_report(text: str) -> bool:
    return text.startswith(REPORT_MARK + '\n') or LEGACY_REPORT.match(text) is not None


def report_overwrite_errors(paths) -> list[str]:
    """Ручные отчёты под именем отчёта сборки — сборка их затёрла бы."""
    # utf-8-sig: отчёт сборки, пересохранённый редактором с BOM, остаётся отчётом сборки
    return [f'{path.name} написан не сборкой, сборка его перезаписала бы; переименуйте ручной '
            f'отчёт в {path.stem}-<что>.md (например, {path.stem}-tables.md)'
            for path in paths if path.exists() and not is_build_report(path.read_text('utf-8-sig'))]


def write_dossier_reports(reports: dict[Path, str]) -> None:
    """Пишет отчёты досье. Ручной отчёт под именем отчёта сборки не затирается:
    сборка останавливается, не записав ни одного отчёта."""
    errors = report_overwrite_errors(reports)
    if errors:
        raise ValueError('ручные отчёты под именем отчёта сборки:\n - ' + '\n - '.join(errors))
    for path, text in reports.items():
        path.write_text(text, encoding='utf-8')


def dossier_report(dossier: dict, questions: list[dict], bank: list[dict] | None = None) -> str:
    lines = [REPORT_MARK, f'# Досье «{dossier["title"]}»', '',
             f'Файл пишет сборка (`scripts/merge_bank.py`). Править — `data/dossiers/{dossier["id"]}.json` '
             f'и `data/dossiers/{dossier["id"]}-questions.json`.', '']
    for name, table in dossier['tables'].items():
        columns = list(table['columns'])
        lines += [f'## Таблица `{name}` — строк: {len(table["rows"])}', '']
        if table.get('sides'):
            lines += [f'Стороны: {", ".join(table["sides"])}. Строки ядра отмечены ★.', '']
        if table['rows']:
            lines.append('| id | ' + ' | '.join(columns) + ' | olympiad |')
            lines.append('|' + '---|' * (len(columns) + 2))
            for row in table['rows']:
                cells = ' | '.join(_report_cell(row.get(column)) for column in columns)
                mark = ' ★' if row.get('core') else ''
                lines.append(f'| {row["id"]}{mark} | {cells} | {", ".join(row.get("olympiad", []))} |')
            lines.append('')
    accepted = sum(1 for question in questions if question['status'] == 'accepted')
    lines += [f'## Вопросы — принято {accepted} из {len(questions)}', '']
    by_id = {record['id']: record for record in bank or []}
    for question in questions:
        check = question.get('check') or {}
        header = f'### {question["id"]} · {question["status"]} · проверка: {check.get("verdict", "нет")}'
        problems: list[str] = []
        if 'embeds' in question:
            record = by_id.get(question['embeds'])
            header += f' · встраивает {question["embeds"]}'
            preview = None
            if record is not None:
                # и черновик, и принятый вопрос автор видит таким, каким его увидит ученик
                preview, problems = embed_record(original_record(record), question, dossier)
                text, topic = record['questionRu'], record.get('topic', '')
                explanation = record.get('explanation', {}).get('ru', '')
            else:
                text = f'(встраивает {question["embeds"]}; такой записи нет в банке)'
                topic, explanation = '—', '—'
            if preview is not None:
                answer = next(o for o in preview['options'] if o['id'] == preview['answer']['optionId'])
                wrong = [o for o in preview['options'] if o is not answer]
            else:
                options, _ = question_options(question, dossier)
                answer, wrong = options[0], options[1:]
        else:
            options, _ = question_options(question, dossier)
            answer, wrong = options[0], options[1:]
            text, topic, explanation = question['questionRu'], question['topic'], question['explanation'].strip()
        lines += [header, '', text, '',
                  f'- Ответ: {answer["zh"].strip()}',
                  # подписи принимает автор — значит, он их видит здесь
                  '- Неверные:', *(f'  - {option["zh"].strip()} — {option.get("gloss", "без подписи")}'
                                   for option in wrong),
                  f'- Тема: {topic}',
                  f'- Пояснение: {explanation}']
        lines += [f'- Ошибка встраивания: {problem}' for problem in problems]
        if check.get('note'):
            lines.append(f'- Замечание проверки: {check["note"]}')
        lines.append('')
    return '\n'.join(lines).rstrip('\n') + '\n'


QUESTIONS_SUFFIX = '-questions.json'


def dossier_paths(directory: Path) -> list[tuple[Path, Path]]:
    pairs = []
    for questions_path in sorted(directory.glob(f'*{QUESTIONS_SUFFIX}')):
        table_path = questions_path.with_name(questions_path.name.removesuffix(QUESTIONS_SUFFIX) + '.json')
        if not table_path.exists():
            raise ValueError(f'{questions_path.name}: нет таблицы досье {table_path.name}')
        pairs.append((table_path, questions_path))
    return pairs


def load_removed(path: Path) -> dict[str, dict]:
    """Снятые принятые вопросы (`data/review/removed.json`): id → причина и дата решения автора.
    Запись из банка удалена, но прогресс учеников под этим id остался в браузерах, поэтому id
    больше не выдаётся: новый вопрос под ним унаследовал бы чужой прогресс."""
    if not path.exists():
        return {}
    removed = json.loads(path.read_text('utf-8'))
    for record_id, entry in removed.items():
        if not isinstance(entry, dict) or not str(entry.get('reason', '')).strip() or not entry.get('date'):
            raise ValueError(f'{path.name}: {record_id} — нужны reason и date')
    return removed


def removed_id_errors(ids, removed: dict[str, dict]) -> list[str]:
    return [f'{record_id}: id снятого вопроса ({removed[record_id]["reason"]}) — возьмите новый номер'
            for record_id in ids if record_id in removed]


def check_dossiers(directory: Path, bank: list[dict], glosses: dict[str, dict],
                   groups: dict[str, list[str]] | None = None,
                   reports: Path | None = None,
                   removed: dict[str, dict] | None = None) -> tuple[list[str], list[tuple[dict, list[dict]]]]:
    """Все проверки досье без сборки банка — то, что остановит сборку, видно уже у черновиков.
    `reports` — каталог отчётов досье: ручной отчёт под именем отчёта сборки тоже ошибка.

    Ошибка одного досье не прячет остальные: сборщики и писатель работают параллельно. Свои
    вопросы досье берутся из файлов (bank.json обновляется только сборкой), встраивания — по
    записям банка, включая черновики.
    """
    from embeds import embed_errors  # embeds импортирует dossiers

    errors: list[str] = []
    loaded: list[tuple[dict, list[dict]]] = []
    try:
        pairs = dossier_paths(directory)
    except ValueError as error:
        return [str(error)], []
    for table_path, questions_path in pairs:
        try:
            loaded.append(load_dossier(table_path, questions_path, bank, groups))
        except ValueError as error:
            errors.append(str(error))
    olympiad_view = [record for record in bank if not (record.get('origin') == 'addition' and 'dossier' in record)]
    errors += validate_links({data['id']: data for data, _ in loaded})
    errors += cross_leak_errors(olympiad_view, loaded, groups)
    errors += embed_errors(bank, loaded, glosses, drafts=True)
    if reports is not None:
        errors += report_overwrite_errors(reports / f'dossier-{data["id"]}.md' for data, _ in loaded)
    errors += removed_id_errors((q['id'] for _, questions in loaded for q in questions), removed or {})
    return errors, loaded


def main() -> None:
    """Проверка всех досье без сборки банка: её запускают агенты, пока пишут досье."""
    from fact_groups import load_fact_groups
    from glosses import load_glosses

    root = Path(__file__).resolve().parents[1]
    bank_path = root / 'data/bank.json'
    bank = json.loads(bank_path.read_text('utf-8')) if bank_path.exists() else []
    errors, loaded = check_dossiers(root / 'data/dossiers', bank, load_glosses(root / 'data/review/glosses.json'),
                                    load_fact_groups(root / 'data/review/fact-groups.json'), root / 'data/review',
                                    load_removed(root / 'data/review/removed.json'))
    for data, questions in loaded:
        accepted = sum(1 for question in questions if question['status'] == 'accepted')
        rows = sum(len(table['rows']) for table in data['tables'].values())
        print(f'{data["id"]}: строк {rows}, вопросов {len(questions)}, принято {accepted}')
    if errors:
        raise SystemExit('ошибки досье:\n - ' + '\n - '.join(errors))
    print('ошибок нет')


if __name__ == '__main__':
    main()
