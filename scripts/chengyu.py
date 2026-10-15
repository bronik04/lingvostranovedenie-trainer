"""Раздел «Чэнъюй»: проверка данных и сверка олимпиадных заданий с PDF.

Данные: `data/chengyu/olympiad.json` (задания ВсОШ «подберите аналог фразеологизму»)
и `data/chengyu/drafts.json` (составленные задания, в раздел идут только принятые
автором). Спецификация — `docs/superpowers/specs/2026-10-15-chengyu-mode-design.md`.

    python3 scripts/chengyu.py            # проверка формы данных
    python3 scripts/chengyu.py --sources  # плюс сверка с PDF (нужен poppler)
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/chengyu'
SOURCES = ROOT / 'sources/chengyu'

GROUPS = {
    'work': 'Труд и старание',
    'char': 'Характер и чувства',
    'speech': 'Слово и речь',
    'fable': 'Притчи и истории',
    'luck': 'Удача и беда',
    'measure': 'Сколько, как быстро, насколько похоже',
    'mind': 'Знание и понимание',
    'people': 'Люди вместе',
}
KINDS = {'analog', 'reverse', 'odd'}
STAGES = {'pri', 'shk', 'mun', 'reg', 'zak'}
KEY_CHECKS = {'table', 'inline', 'bold', 'visual'}
LETTERS = ['A', 'B', 'C', 'D']
HAN = re.compile(r'^[一-鿿]{4}$')
YEAR = re.compile(r'^20\d\d-\d\d$')
DRAFT_STATUSES = {'draft', 'accepted'}
VERDICTS = {'accept', 'fix', 'drop'}


def load(name: str) -> list[dict]:
    path = DATA / name
    return json.loads(path.read_text('utf-8')) if path.exists() else []


def published(olympiad: list[dict], drafts: list[dict]) -> list[dict]:
    """Записи, которые видит ученик: олимпиадные и принятые составленные."""
    accepted = [d for d in drafts
                if d.get('status') == 'accepted' and d.get('check', {}).get('verdict') == 'accept']
    return olympiad + [{**d, 'origin': 'authored'} for d in accepted]


def _record_errors(record: dict, olympiad: bool) -> list[str]:
    where = record.get('id', '?')
    errors: list[str] = []
    for field in ('id', 'kind', 'chengyu', 'pinyin', 'options', 'answer', 'group',
                  'literal', 'meaning', 'trap'):
        if not record.get(field):
            errors.append(f'{where}: нет поля {field}')
    if errors:
        return errors
    if record['kind'] not in KINDS:
        errors.append(f'{where}: неизвестный вид задания {record["kind"]!r}')
    if not HAN.match(record['chengyu']):
        errors.append(f'{where}: чэнъюй должен быть из четырёх иероглифов')
    if record['id'] != f'cy-{record["chengyu"]}':
        errors.append(f'{where}: id должен быть cy-<чэнъюй>')
    if record['group'] not in GROUPS:
        errors.append(f'{where}: тема вне списка восьми: {record["group"]!r}')
    options = record['options']
    if [o.get('id') for o in options] != LETTERS:
        errors.append(f'{where}: варианты должны идти с id A, B, C, D')
    texts = [o.get('text', '').strip() for o in options]
    if any(not t for t in texts) or len(set(texts)) != len(texts):
        errors.append(f'{where}: пустой или повторяющийся вариант')
    if record['answer'] not in LETTERS:
        errors.append(f'{where}: ответ должен быть одной из букв A–D')
    if record['kind'] == 'reverse':
        if not record.get('prompt'):
            errors.append(f'{where}: у обратного задания нет русской пословицы (prompt)')
        if _answer_text(record) != record['chengyu']:
            errors.append(f'{where}: у обратного задания ответ — сам чэнъюй записи')
        for option in options:
            if option['id'] != record['answer'] and not option.get('gloss'):
                errors.append(f'{where}: у неверного варианта {option["id"]} нет подписи')
    if olympiad:
        occurrences = record.get('occurrences') or []
        if not occurrences:
            errors.append(f'{where}: олимпиадное задание без occurrences')
        for occurrence in occurrences:
            if not YEAR.match(occurrence.get('year', '')):
                errors.append(f'{where}: год {occurrence.get("year")!r} не в виде 2022-23')
            if occurrence.get('stageCode') not in STAGES:
                errors.append(f'{where}: неизвестный этап {occurrence.get("stageCode")!r}')
            if not isinstance(occurrence.get('number'), int):
                errors.append(f'{where}: нет номера задания')
            if not occurrence.get('instruction'):
                errors.append(f'{where}: нет формулировки задания из бланка (instruction)')
            if 'part' in occurrence and not isinstance(occurrence['part'], int):
                errors.append(f'{where}: пункт задания (part) — число')
            if occurrence.get('keyCheck') not in KEY_CHECKS:
                errors.append(f'{where}: keyCheck — одно из {sorted(KEY_CHECKS)}')
            for field in ('tasks', 'answers'):
                if not occurrence.get(field):
                    errors.append(f'{where}: нет файла {field}')
    else:
        if record.get('status') not in DRAFT_STATUSES:
            errors.append(f'{where}: status — draft или accepted')
        verdict = (record.get('check') or {}).get('verdict')
        if record.get('status') == 'accepted' and verdict != 'accept':
            errors.append(f'{where}: принятый черновик без вердикта проверки accept')
        if verdict is not None and verdict not in VERDICTS:
            errors.append(f'{where}: вердикт проверки — accept, fix или drop')
        if record.get('occurrences'):
            errors.append(f'{where}: у составленного задания не бывает occurrences')
    return errors


def validate(olympiad: list[dict], drafts: list[dict]) -> list[str]:
    errors: list[str] = []
    for record in olympiad:
        errors += _record_errors(record, olympiad=True)
    for record in drafts:
        errors += _record_errors(record, olympiad=False)
    seen: set[str] = set()
    for record in olympiad + drafts:
        if record.get('id') in seen:
            errors.append(f'{record.get("id")}: повторяющийся id (чэнъюй уже есть)')
        seen.add(record.get('id'))
    return errors


# --- Сверка с PDF ----------------------------------------------------------------------

def _norm(text: str) -> str:
    """Без регистра, пробелов, знаков препинания, ё/е и вида тире."""
    return re.sub(r'[\W_]+', '', text.lower().replace('ё', 'е'))


@lru_cache(maxsize=None)
def _pdf_text(name: str, layout: bool = False) -> str:
    args = ['pdftotext'] + (['-layout'] if layout else []) + [str(SOURCES / name), '-']
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


@lru_cache(maxsize=None)
def _runs(name: str) -> list[tuple[str, bool]]:
    """Текстовые фрагменты PDF по порядку и признак полужирного (pdftohtml -xml: тег <b>
    или шрифт Bold)."""
    xml = subprocess.run(['pdftohtml', '-xml', '-i', '-stdout', '-q', str(SOURCES / name)],
                         capture_output=True, text=True, check=True).stdout
    bold_fonts = {m.group(1) for m in re.finditer(r'<fontspec id="(\d+)"[^>]*family="[^"]*Bold[^"]*"', xml)}
    runs = []
    for m in re.finditer(r'<text [^>]*font="(\d+)"[^>]*>(.*?)</text>', xml):
        raw = m.group(2)
        text = html.unescape(re.sub(r'<[^>]+>', '', raw))
        if _norm(text):
            runs.append((text, '<b>' in raw or m.group(1) in bold_fonts))
    return runs


CYR_LETTERS = str.maketrans({'А': 'A', 'В': 'B', 'С': 'C'})
LETTER_LINE = re.compile(r'^\s*(?:[ABCDАВС]\s+)*[ABCDАВС]\s*$')
NUMBER_LINE = re.compile(r'^\s*(?:\d{1,2}\s+)*\d{1,2}\s*$')
TASK_NUMBER = re.compile(r'(?:Задание|№)\s*(\d+)|^\s*(\d+)\s*[.．)]')
SECTION_HEADER = re.compile(r'(Ключи к|ЛИНГВОСТРАНОВЕД|Лингвострановед)', re.I)
# сколько строк после чэнъюя занимают его варианты (с колонтитулами и пустыми строками)
OPTION_WINDOW = 30
# сколько строк над чэнъюем ищется номер задания
NUMBER_WINDOW = 8


def _key_tables(text: str) -> list[dict[int, str]]:
    """Таблицы ключей: строка номеров, под ней строка букв; продолжение нумерации
    (1–10, затем 11–20) — та же таблица, номер с начала — новая."""
    lines = [line for line in text.splitlines() if line.strip()]
    tables: list[dict[int, str]] = []
    for upper, lower in zip(lines, lines[1:]):
        if not (NUMBER_LINE.match(upper) and LETTER_LINE.match(lower)):
            continue
        numbers = [int(n) for n in upper.split()]
        letters = lower.translate(CYR_LETTERS).split()
        if len(numbers) != len(letters):
            continue
        pairs = dict(zip(numbers, letters))
        if tables and numbers[0] == max(tables[-1]) + 1:
            tables[-1].update(pairs)
        else:
            tables.append(pairs)
    return tables


def table_key(name: str, number: int) -> str | None:
    """Буква ключа лексико-грамматического теста из таблиц PDF ответов."""
    text = _pdf_text(name, layout=True)
    header = re.search(r'лексико-грамматическ', text, re.I)
    if header:
        # раздел ЛГ-теста — до заголовка следующего раздела: иначе ключи
        # лингвострановедения с продолжающейся нумерацией приклеятся к таблице
        section = text[header.end():]
        following = SECTION_HEADER.search(section)
        tables = _key_tables(section[:following.start()] if following else section)
        return tables[0].get(number) if tables else None
    tables = _key_tables(text)
    if number > 20:
        found = [t[number] for t in tables if number in t]
        return found[0] if len(found) == 1 else None
    lg = [t for t in tables if min(t) == 1 and max(t) == 20]
    return lg[0].get(number) if lg else None


def _key_lines(lines: list[str], record: dict, occurrence: dict) -> list[int]:
    """Строки бланка, с которых начинается задание: строка с чэнъюем (у обратного —
    с пословицей). Если китайский шрифт не извлекается — строка перед первым вариантом."""
    if occurrence.get('textLayer') == 'garbled':
        first = _norm(record['options'][0]['text'])
        return [i - 1 for i, line in enumerate(lines) if first and _norm(line) == first]
    key = _norm(record['prompt'] if record['kind'] == 'reverse' else record['chengyu'])
    return [i for i, line in enumerate(lines) if key and key in _norm(line)]


def _number_ok(lines: list[str], at: int, occurrence: dict) -> bool:
    """Номер задания (и пункта) — ближайшие номера над строкой чэнъюя."""
    found = []
    for line in reversed(lines[max(0, at - NUMBER_WINDOW):at + 1]):
        match = TASK_NUMBER.search(line)
        if match:
            found.append(int(match.group(1) or match.group(2)))
    if not occurrence.get('part'):
        return found[:1] == [occurrence['number']]
    # пункт задания: ближайший номер — пункт, а «Задание N» может стоять выше, за
    # колонтитулом страницы, поэтому ищется в окне шире
    tasks = [int(m.group(1)) for line in reversed(lines[max(0, at - 3 * NUMBER_WINDOW):at + 1])
             for m in [re.search(r'(?:Задание|№)\s*(\d+)', line)] if m]
    return found[:1] == [occurrence['part']] and tasks[:1] == [occurrence['number']]


def _options_in_order(lines: list[str], at: int, record: dict) -> bool:
    """Варианты A–D идут по порядку сразу после строки чэнъюя."""
    tail = _norm(' '.join(lines[at + 1:at + 1 + OPTION_WINDOW]))
    position = 0
    for option in record['options']:
        found = tail.find(_norm(option['text']), position)
        if found < 0:
            return False
        position = found + len(_norm(option['text']))
    return True


def _bold_answer_ok(name: str, record: dict) -> str | None:
    """Полужирный в PDF ответов: после чэнъюя этого задания выделен ответ и только он
    (в PDF-формах полужирные все варианты — такое выделение ключом не считается)."""
    runs = _runs(name)
    key = _norm(record['prompt'] if record['kind'] == 'reverse' else record['chengyu'])
    starts = [i for i, (text, _) in enumerate(runs) if key in _norm(text)]
    if not starts:
        return 'в PDF ответов нет этого задания'
    window = runs[starts[0] + 1:starts[0] + 1 + OPTION_WINDOW]

    def bold(text: str) -> bool:
        target = _norm(text)
        return any(is_bold and (_norm(run) == target or (len(_norm(run)) > 3 and target.startswith(_norm(run))))
                   for run, is_bold in window)

    answer = next(o['text'] for o in record['options'] if o['id'] == record['answer'])
    if not bold(answer):
        return f'ответ «{answer}» не выделен полужирным'
    if any(bold(o['text']) for o in record['options'] if o['id'] != record['answer']):
        return 'полужирным выделен не только ответ'
    return None


def _answer_text(record: dict) -> str | None:
    return next((o['text'] for o in record['options'] if o.get('id') == record.get('answer')), None)


def check_sources(olympiad: list[dict]) -> list[str]:
    """Каждое задание есть в бланке на своём месте: номер, формулировка, варианты по
    порядку; ключ подтверждён PDF ответов."""
    errors: list[str] = []
    manifest = json.loads((SOURCES / 'manifest.json').read_text('utf-8'))
    listed = {entry['name']: entry for entry in manifest}
    on_disk = {p.name for p in SOURCES.glob('*.pdf')}
    if set(listed) != on_disk:
        errors.append(f'sources/chengyu: манифест и файлы расходятся: {sorted(set(listed) ^ on_disk)}')
    for name, entry in listed.items():
        path = SOURCES / name
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            errors.append(f'sources/chengyu/{name}: контрольная сумма не совпадает')
    for record in olympiad:
        where = record['id']
        answer_text = _answer_text(record)
        if answer_text is None:
            errors.append(f'{where}: ответ не указывает на вариант')
            continue
        for occurrence in record['occurrences']:
            tasks, answers = occurrence['tasks'], occurrence['answers']
            label = f'{where} ({occurrence["year"]}, задание {occurrence["number"]})'
            if tasks not in listed or answers not in listed:
                errors.append(f'{label}: файл не из sources/chengyu: {tasks} / {answers}')
                continue
            lines = _pdf_text(tasks).splitlines()
            starts = _key_lines(lines, record, occurrence)
            if not starts:
                errors.append(f'{label}: в бланке {tasks} нет этого задания')
                continue
            placed = [at for at in starts if _options_in_order(lines, at, record)]
            if not placed:
                errors.append(f'{label}: в бланке {tasks} после задания нет вариантов A–D в этом порядке')
                continue
            if not any(_number_ok(lines, at, occurrence) for at in placed):
                errors.append(f'{label}: номер задания не совпадает с бланком')
            if _norm(occurrence.get('instruction', '')) not in _norm(' '.join(lines)):
                errors.append(f'{label}: в бланке нет формулировки «{occurrence.get("instruction")}»')
            method = occurrence['keyCheck']
            if method == 'table':
                letter = table_key(answers, occurrence['number'])
                if letter != record['answer']:
                    errors.append(f'{label}: по таблице {answers} ключ {letter}, в данных {record["answer"]}')
            elif method == 'inline':
                # «11 B ни рыба ни мясо» или «8. язык мой – враг мой»: номер, буква, если
                # есть, — та же, что в данных, и текст ответа в той же строке
                text = _pdf_text(answers, layout=True)
                pattern = rf'(?:^|\s){occurrence["number"]}[.)]?\s+(?:([A-D])\s+)?\S'
                found = False
                for line in text.splitlines():
                    for match in re.finditer(pattern, line):
                        letter_ok = match.group(1) in (None, record['answer'])
                        if letter_ok and _norm(answer_text) in _norm(line[match.start():]):
                            found = True
                if not found:
                    errors.append(f'{label}: в {answers} нет строки «{occurrence["number"]} {answer_text}»')
            elif method == 'bold':
                problem = _bold_answer_ok(answers, record)
                if problem:
                    errors.append(f'{label}: {answers}: {problem}')
    return errors


def visual_keys(olympiad: list[dict]) -> list[str]:
    """Задания, ключ которых сверен глазами (отметка в PDF-форме)."""
    return [f'{r["id"]} ({o["year"]}, {o["stageCode"]}, задание {o["number"]})'
            for r in olympiad for o in r['occurrences'] if o['keyCheck'] == 'visual']


def main() -> None:
    olympiad, drafts = load('olympiad.json'), load('drafts.json')
    errors = validate(olympiad, drafts)
    if '--sources' in sys.argv:
        errors += check_sources(olympiad)
    if errors:
        print(f'нарушений: {len(errors)}')
        for message in errors:
            print(' -', message)
        raise SystemExit(1)
    accepted = sum(1 for d in drafts if d.get('status') == 'accepted')
    print(f'чэнъюй: олимпиадных {len(olympiad)}, черновиков {len(drafts)} (принято {accepted})')
    if '--sources' in sys.argv:
        print('ключи сверены глазами:', ', '.join(visual_keys(olympiad)) or 'нет')


if __name__ == '__main__':
    main()
