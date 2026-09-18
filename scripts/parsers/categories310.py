"""Разбор файла «Вопросы по категориям (310 шт).docx»."""

from __future__ import annotations

import re
from pathlib import Path

from docx_text import paragraphs

HEADER = re.compile(
    r'^(?P<ordinal>\d+)\.\s+(?P<year>\d{4}[–-]\d{4}),\s*(?P<stage>[^,]+?)\s*этап,\s*№\s*(?P<number>\d+)$'
)
OPTION = re.compile(r'^(?P<letter>[A-D])[.、．)]\s*(?P<text>\S.*)$')
SECTION = re.compile(r'^\d+\.\s+(?P<topic>[^—]+?)\s+—\s+\d+\s+вопрос')

STAGES = {
    'Пригласительный': ('пригласительный', 'pri'),
    'Школьный': ('школьный', 'shk'),
    'Муниципальный': ('муниципальный', 'mun'),
    'Региональный': ('региональный', 'reg'),
    'Заключительный': ('заключительный', 'zak'),
}


def _short_year(value: str) -> str:
    start, end = re.split(r'[–-]', value)
    return f'{start}-{end[2:]}'


def parse(path: Path) -> list[dict]:
    lines = paragraphs(path)
    records: list[dict] = []
    topic: str | None = None
    index = 0
    while index < len(lines):
        line = lines[index]
        section = SECTION.match(line)
        if section:
            topic = section.group('topic').strip()
            index += 1
            continue
        header = HEADER.match(line)
        if not header:
            index += 1
            continue
        question = lines[index + 1] if index + 1 < len(lines) else ''
        options: list[str] = []
        cursor = index + 2
        while cursor < len(lines) and len(options) < 4:
            option = OPTION.match(lines[cursor])
            if not option:
                break
            options.append(option.group('text').strip())
            cursor += 1
        if len(options) == 4:
            stage, code = STAGES.get(header.group('stage').strip(), (header.group('stage').strip(), 'unk'))
            records.append({
                'sourceFile': path.name,
                'year': _short_year(header.group('year')),
                'stage': stage,
                'stageCode': code,
                'grades': '',
                'number': int(header.group('number')),
                'questionRu': question.strip(),
                'questionZh': None,
                'options': options,
                'officialKeyIndex': None,
                'topic': topic,
                'parseWarnings': [],
            })
        index = cursor
    return records
