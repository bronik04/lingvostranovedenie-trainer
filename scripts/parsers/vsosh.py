"""Разбор сводного сборника «Лингвострановедение ВсОШ.docx» и таблицы ключей."""

from __future__ import annotations

import re
from pathlib import Path

from docx_text import paragraphs

YEAR = re.compile(r'^(?P<start>\d{4})[–-](?P<end>\d{4})\s+уч\.\s*г\.$')
STAGE_LINE = re.compile(r'^(?P<stage>Пригласительный|Школьный|Муниципальный|Региональный|Заключительный)\s+этап$')
KEY_LINE = re.compile(r'^(?P<stage>Пригласительный|Школьный|Муниципальный|Региональный|Заключительный)\s+этап:\s*(?P<body>.+)$')
KEY_PAIR = re.compile(r'(\d+)\s*[—–-]\s*([A-D])')
QUESTION = re.compile(r'^(?P<number>\d+)[.、]\s+(?P<text>\S.*)$')
OPTION = re.compile(r'^(?P<letter>[A-D])[.、．)]\s*(?P<text>\S.*)$')
CYRILLIC = re.compile(r'[А-Яа-яЁё]')

STAGES = {
    'Пригласительный': ('пригласительный', 'pri'),
    'Школьный': ('школьный', 'shk'),
    'Муниципальный': ('муниципальный', 'mun'),
    'Региональный': ('региональный', 'reg'),
    'Заключительный': ('заключительный', 'zak'),
}


def _short_year(start: str, end: str) -> str:
    return f'{start}-{end[2:]}'


def parse_keys(lines: list[str]) -> dict[tuple[str, str, int], int]:
    keys: dict[tuple[str, str, int], int] = {}
    year = ''
    for line in lines:
        year_match = YEAR.match(line)
        if year_match:
            year = _short_year(year_match.group('start'), year_match.group('end'))
            continue
        key_match = KEY_LINE.match(line)
        if not key_match or not year:
            continue
        _, code = STAGES[key_match.group('stage')]
        for number, letter in KEY_PAIR.findall(key_match.group('body')):
            keys[(year, code, int(number))] = 'ABCD'.index(letter)
    return keys


def parse(path: Path) -> list[dict]:
    lines = paragraphs(path)
    keys = parse_keys(lines)
    records: list[dict] = []
    year = ''
    stage, code = '', 'unk'
    index = 0
    while index < len(lines):
        line = lines[index]
        year_match = YEAR.match(line)
        if year_match:
            year = _short_year(year_match.group('start'), year_match.group('end'))
            index += 1
            continue
        stage_match = STAGE_LINE.match(line)
        if stage_match:
            stage, code = STAGES[stage_match.group('stage')]
            index += 1
            continue
        question = QUESTION.match(line)
        if not question or KEY_LINE.match(line):
            index += 1
            continue
        options: list[str] = []
        cursor = index + 1
        while cursor < len(lines) and len(options) < 4:
            option = OPTION.match(lines[cursor])
            if not option:
                break
            options.append(option.group('text').strip())
            cursor += 1
        if len(options) == 4 and year:
            number = int(question.group('number'))
            text = question.group('text').strip()
            records.append({
                'sourceFile': path.name,
                'year': year,
                'stage': stage,
                'stageCode': code,
                'grades': '',
                'number': number,
                'questionRu': text if CYRILLIC.search(text) else None,
                'questionZh': None if CYRILLIC.search(text) else text,
                'options': options,
                'officialKeyIndex': keys.get((year, code, number)),
                'topic': None,
                'parseWarnings': [],
            })
            index = cursor
        else:
            index += 1
    return records
