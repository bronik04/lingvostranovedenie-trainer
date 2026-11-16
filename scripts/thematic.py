"""Сборка отдельного банка вопросов и проверка ссылок тематических блоков."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from normalize import language_errors

DATA = Path(__file__).resolve().parents[1] / 'data/thematic'


def load_thematic(bank: list[dict], full_bank: list[dict]) -> tuple[list[dict], list[dict]]:
    blocks = json.loads((DATA / 'blocks.json').read_text('utf-8'))
    questions = json.loads((DATA / 'questions.json').read_text('utf-8'))
    verified = {record['id'] for record in bank
                if record['answer']['state'] == 'verified' and record['answer']['optionId']}
    occupied = {record['id'] for record in full_bank}
    thematic_ids = set()
    for record in questions:
        record_id = record['id']
        if record_id in occupied or record_id in thematic_ids:
            raise ValueError(f'{record_id}: повторяющийся id тематического вопроса')
        if 'adaptedFrom' in record:
            if record['adaptedFrom'] not in verified:
                raise ValueError(f'{record_id}: исходный вопрос должен быть доступен и проверен')
        else:
            evidence = record.get('evidence', [])
            if not evidence or any(not item['title'].strip() or not urlsplit(item['url']).hostname
                                   or urlsplit(item['url']).scheme != 'https' for item in evidence):
                raise ValueError(f'{record_id}: новому вопросу нужны ссылки на источники')
        options = record['options']
        option_ids = {option['id'] for option in options}
        chinese = [option['zh'] for option in options]
        if len(options) != 4 or len(option_ids) != 4 or len(set(chinese)) != 4:
            raise ValueError(f'{record_id}: нужны четыре разных варианта')
        if record['answer']['optionId'] not in option_ids:
            raise ValueError(f'{record_id}: ответ указывает на несуществующий вариант')
        errors = language_errors(record['questionRu'], chinese)
        if errors:
            raise ValueError(f'{record_id}: {", ".join(errors)}')
        thematic_ids.add(record_id)

    block_ids = set()
    for block in blocks:
        block_id = block['id']
        if block_id in block_ids or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', block_id):
            raise ValueError(f'{block_id}: некорректный или повторяющийся id блока')
        block_ids.add(block_id)
        if not block['title'].strip() or not block['summary'] or any(not item.strip() for item in block['summary']):
            raise ValueError(f'{block_id}: нужны заголовок и конспект')
        steps = block['steps']
        ids = {step['questionId'] for step in steps}
        if not steps or len(ids) != len(steps):
            raise ValueError(f'{block_id}: нужны вопросы без повторяющихся id')
        missing = ids - (verified | thematic_ids)
        if missing:
            raise ValueError(f'{block_id}: недоступные вопросы: {sorted(missing)}')
        if any(not step['answerLabel'].strip() or not step['explanation'].strip() for step in steps):
            raise ValueError(f'{block_id}: каждому вопросу нужны ответ по-русски и пояснение')
    return blocks, questions
