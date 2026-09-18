"""Разбор файла «Банк вопросов — лингвострановедение (423, с ответами).docx»."""

from __future__ import annotations

import re
from pathlib import Path

from docx_text import paragraphs

QUESTION = re.compile(r'^(?P<number>\d+)\.\s+(?P<text>\S.*)$')
OPTIONS = re.compile(r'([A-D])\)\s*(.*?)(?=\s+[A-D]\)|$)')
ANSWER = re.compile(r'^Ответ:\s*(?P<key>[A-D]|в опубликованных ключах отсутствует)\s*·\s*(?P<source>.+)$')
SOURCE = re.compile(r'^(?P<year>\d{4}-\d{2}),\s*(?P<stage>[^,]+),\s*(?P<grades>.+)$')
CYRILLIC = re.compile(r'[А-Яа-яЁё]')

STAGES = {
    'пригл.': ('пригласительный', 'pri'),
    'школ.': ('школьный', 'shk'),
    'мун.': ('муниципальный', 'mun'),
    'рег.': ('региональный', 'reg'),
    'закл.': ('заключительный', 'zak'),
}


def _options(line: str) -> tuple[list[str], list[str]]:
    """Варианты в порядке A–D и предупреждения о дефектах строки.

    В источнике есть две испорченные строки: у вопроса про достопримечательность
    четвёртый вариант помечен буквой A вместо D, у вопроса про кухни варианта D нет
    вовсе. Буква, встреченная второй раз, не затирает первую — иначе «兵马俑» пропадёт.
    """
    found: dict[str, str] = {}
    duplicates: list[str] = []
    for letter, text in OPTIONS.findall(line):
        if letter in found:
            duplicates.append(letter)
            continue
        found[letter] = text.strip()
    options = [found.get(letter, '') for letter in 'ABCD']
    warnings: list[str] = []
    if duplicates:
        warnings.append(f'буква варианта повторяется: {", ".join(duplicates)}')
    missing = [letter for letter in 'ABCD' if not found.get(letter)]
    if missing:
        warnings.append(f'нет вариантов: {", ".join(missing)}')
    return options, warnings


def parse(path: Path) -> list[dict]:
    lines = paragraphs(path)
    records: list[dict] = []
    pending: dict | None = None
    for line in lines:
        question = QUESTION.match(line)
        if question and not line.startswith('Ответ:'):
            text = question.group('text').strip()
            pending = {
                'sourceFile': path.name,
                'number': int(question.group('number')),
                'questionRu': text if CYRILLIC.search(text) else None,
                'questionZh': None if CYRILLIC.search(text) else text,
                'options': [],
                'officialKeyIndex': None,
                'topic': None,
                'parseWarnings': [],
            }
            continue
        if pending is not None and not pending['options'] and OPTIONS.search(line):
            pending['options'], warnings = _options(line)
            pending['parseWarnings'].extend(warnings)
            continue
        answer = ANSWER.match(line)
        if pending is not None and answer:
            key = answer.group('key')
            pending['officialKeyIndex'] = None if key.startswith('в опубликованных') else 'ABCD'.index(key)
            source = SOURCE.match(answer.group('source').strip())
            if source:
                stage, code = STAGES.get(source.group('stage').strip(), (source.group('stage').strip(), 'unk'))
                pending.update({
                    'year': source.group('year'),
                    'stage': stage,
                    'stageCode': code,
                    'grades': source.group('grades').strip(),
                })
            else:
                pending.update({'year': '', 'stage': '', 'stageCode': 'unk', 'grades': ''})
                pending['parseWarnings'].append(f'не разобран источник: {answer.group("source")!r}')
            records.append(pending)
            pending = None
    return records
