"""Разбор оригинальных бланков олимпиады в PDF через системный pdftotext."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

HEADER_YEAR = re.compile(r'(?P<start>\d{4})\s*[-‒–]\s*(?P<end>\d{4})')
HEADER_STAGE = re.compile(r'(?P<stage>Пригласительный|Школьный|Муниципальный|Региональный|Заключительный)\s+этап')
SECTION_START = re.compile(r'^ЛИНГВОСТРАНОВЕДЕНИЕ')
SECTION_END = re.compile(r'^(ПИСЬМО|АУДИРОВАНИЕ|ЧТЕНИЕ|ЛЕКСИКА|ГРАММАТИКА|ГОВОРЕНИЕ|ПИСЬМЕННАЯ)')
QUESTION = re.compile(r'^(?:Задание\s+)?(?P<number>\d+)[.．]\s*(?P<text>\S.*)$')
OPTION = re.compile(r'^(?P<letter>[A-D])[.、．)]\s*(?P<text>\S.*)$')

STAGES = {
    'Пригласительный': 'pri', 'Школьный': 'shk', 'Муниципальный': 'mun',
    'Региональный': 'reg', 'Заключительный': 'zak',
}


def _text(path: Path) -> list[str]:
    result = subprocess.run(['pdftotext', str(path), '-'], capture_output=True, text=True, check=True)
    return [line.strip() for line in result.stdout.splitlines()]


def _header(lines: list[str]) -> tuple[str, str, str]:
    head = ' '.join(lines[:12])
    year_match = HEADER_YEAR.search(head)
    stage_match = HEADER_STAGE.search(head)
    year = f"{year_match.group('start')}-{year_match.group('end')[2:]}" if year_match else ''
    stage = stage_match.group('stage') if stage_match else ''
    return year, stage.lower(), STAGES.get(stage, 'unk')


def parse(path: Path) -> list[dict]:
    lines = _text(path)
    year, stage, code = _header(lines)

    inside = False
    records: list[dict] = []
    pending: dict | None = None
    for line in lines:
        if SECTION_START.match(line):
            inside = True
            continue
        if inside and SECTION_END.match(line):
            inside = False
        if not inside or not line:
            continue

        option = OPTION.match(line)
        if pending is not None and option:
            pending['options'].append(option.group('text').strip())
            if len(pending['options']) == 4:
                records.append(pending)
                pending = None
            continue

        question = QUESTION.match(line)
        if question:
            pending = {
                'sourceFile': path.name,
                'year': year,
                'stage': stage,
                'stageCode': code,
                'grades': '',
                'number': int(question.group('number')),
                'questionRu': question.group('text').strip(),
                'questionZh': None,
                'options': [],
                'officialKeyIndex': None,
                'topic': None,
                'parseWarnings': [],
            }
            continue

        if pending is not None and not pending['options']:
            # формулировка перенесена на следующую строку бланка — дописываем целиком
            pending['questionRu'] = f"{pending['questionRu']} {line}".strip()
    return records
