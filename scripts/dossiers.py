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
        if not isinstance(gloss, str) or not gloss.strip():
            errors.append(f'{where}: подпись — одна непустая строка')
        else:
            # те же правила текста, что у glosses.json: ученик видит подписи одинаково
            errors += [f'{where}: {message}' for message in gloss_text_errors(gloss, zh if isinstance(zh, str) else '')]
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


QUESTION_FIELDS = {'id', 'status', 'topic', 'fact', 'questionRu', 'explanation', 'exclude', 'check'}
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


def _name_pattern(name: str) -> re.Pattern:
    words = re.findall(r'\w+', name.lower())
    if not words or not CYRILLIC.search(name):
        return re.compile(re.escape(name.lower()))
    return re.compile(r'(?<!\w)' + r'\W+'.join(re.escape(_stem(word)) + r'\w*' for word in words))


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


def _content_errors(where: str, question: dict, dossier: dict) -> list[str]:
    """Проверки, которым нужны целые ссылки: набор вариантов и текст вопроса."""
    errors: list[str] = []
    fact = question['fact']
    _, answer = answer_cell(question, dossier)
    twins = [row_id for row_id, cell in _candidates(question, dossier) if cell['zh'].strip() == answer['zh'].strip()]
    if twins:
        errors.append(f'{where}: неверный вариант совпадает с правильным: {twins}')
    options, _ = question_options(question, dossier)
    if len(options) - 1 < MIN_WRONG:
        errors.append(f'{where}: в наборе меньше {MIN_WRONG} неверных вариантов')
    unglossed = [option['id'] for option in options[1:] if 'gloss' not in option]
    if unglossed:
        errors.append(f'{where}: у неверных вариантов нет подписи: {unglossed}')
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


def validate_questions(questions: object, dossier: dict, bank: list[dict] | None = None) -> list[str]:
    """`bank` — записи банка без вопросов этого досье: с ними сверяются повторы формулировок."""
    if not isinstance(questions, list):
        return ['вопросы досье должны быть списком']
    errors: list[str] = []
    seen: set[str] = set()
    whole: list[dict] = []
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
        if not broken and text is not None:
            errors += _content_errors(where, question, dossier)
            if named:
                whole.append(question)
    # утечки: ответ одного вопроса не должен стоять в тексте другого
    answers = {question['id']: answer_cell(question, dossier)[1] for question in whole}
    for question in whole:
        for other_id, answer in answers.items():
            if other_id == question['id']:
                continue
            names = _mentions(question['questionRu'], answer)
            if names:
                errors.append(f'{question["id"]}: текст называет ответ вопроса {other_id}: {names}')
    errors += _wording_errors(whole, bank or [])
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


def load_dossier(dossier_path: Path, questions_path: Path,
                 bank: list[dict] | None = None) -> tuple[dict, list[dict]]:
    dossier = loads_unique(dossier_path.read_text('utf-8'), 'досье')
    errors = validate_dossier(dossier)
    if errors:
        raise ValueError(f'некорректное досье {dossier_path.name}:\n - ' + '\n - '.join(errors))
    questions = loads_unique(questions_path.read_text('utf-8'), 'вопросах досье')
    errors = validate_questions(questions, dossier, [record for record in bank or []
                                                     if record.get('dossier') != dossier['id']])
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
    else:
        text = ' '.join(str(value).split())
    return text.replace('|', '\\|')


def dossier_report(dossier: dict, questions: list[dict]) -> str:
    lines = [f'# Досье «{dossier["title"]}»', '',
             f'Файл пишет сборка (`scripts/dossiers.py`). Править — `data/dossiers/{dossier["id"]}.json` '
             f'и `data/dossiers/{dossier["id"]}-questions.json`.', '']
    for name, table in dossier['tables'].items():
        columns = list(table['columns'])
        lines += [f'## Таблица `{name}` — строк: {len(table["rows"])}', '']
        if table['rows']:
            lines.append('| id | ' + ' | '.join(columns) + ' | olympiad |')
            lines.append('|' + '---|' * (len(columns) + 2))
            for row in table['rows']:
                cells = ' | '.join(_report_cell(row.get(column)) for column in columns)
                lines.append(f'| {row["id"]} | {cells} | {", ".join(row.get("olympiad", []))} |')
            lines.append('')
    accepted = sum(1 for question in questions if question['status'] == 'accepted')
    lines += [f'## Вопросы — принято {accepted} из {len(questions)}', '']
    for question in questions:
        options, _ = question_options(question, dossier)
        check = question.get('check') or {}
        lines += [f'### {question["id"]} · {question["status"]} · проверка: {check.get("verdict", "нет")}', '',
                  question['questionRu'], '',
                  f'- Ответ: {options[0]["zh"]}',
                  # подписи принимает автор — значит, он их видит здесь
                  '- Неверные:', *(f'  - {option["zh"]} — {option.get("gloss", "без подписи")}'
                                   for option in options[1:]),
                  f'- Тема: {question["topic"]}',
                  f'- Пояснение: {question["explanation"].strip()}']
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


def main() -> None:
    """Проверка всех досье без сборки банка: её запускают агенты, пока пишут досье."""
    root = Path(__file__).resolve().parents[1]
    bank_path = root / 'data/bank.json'
    bank = json.loads(bank_path.read_text('utf-8')) if bank_path.exists() else []
    for table_path, questions_path in dossier_paths(root / 'data/dossiers'):
        data, questions = load_dossier(table_path, questions_path, bank)
        accepted = sum(1 for question in questions if question['status'] == 'accepted')
        rows = sum(len(table['rows']) for table in data['tables'].values())
        print(f'{data["id"]}: строк {rows}, вопросов {len(questions)}, принято {accepted} — ошибок нет')


if __name__ == '__main__':
    main()
