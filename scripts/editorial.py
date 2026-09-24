"""Редакторские правки поверх собранного банка.

Правки ключуются по итоговому id записи и накладываются после слияния: id олимпиадного
вопроса вычисляется из его текста, поэтому править формулировку на входе слияния
нельзя — сменились бы id, и у учеников пропал бы прогресс. Первоисточники в
`sources/` остаются нетронутыми, а каждая правка хранит причину.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from normalize import completeness_errors, language_errors, normalize_text
from taxonomy import TOPICS

FIELDS = {'reason', 'questionRu', 'questionZh', 'options', 'explanation', 'topic'}
CHANGES = FIELDS - {'reason'}
CJK = re.compile(r'[\u4e00-\u9fff]')


def validate_editorial(edits: dict[str, dict], bank: list[dict]) -> list[str]:
    errors: list[str] = []
    by_id = {record['id']: record for record in bank}
    for record_id, edit in edits.items():
        record = by_id.get(record_id)
        if record is None:
            errors.append(f'{record_id}: такой записи в банке нет')
            continue
        if not isinstance(edit, dict):
            errors.append(f'{record_id}: правка должна быть объектом')
            continue
        unknown = set(edit) - FIELDS
        if unknown:
            errors.append(f'{record_id}: неизвестные поля {sorted(unknown)}')
        if not isinstance(edit.get('reason'), str) or not edit['reason'].strip():
            errors.append(f'{record_id}: не указана причина правки')
        if not CHANGES & set(edit):
            errors.append(f'{record_id}: правка ничего не меняет')

        question = edit.get('questionRu', record['questionRu'])
        question_zh = edit.get('questionZh', record.get('questionZh'))
        if 'questionZh' in edit and (not isinstance(question_zh, str)
                                     or not CJK.search(question_zh)):
            errors.append(f'{record_id}: китайская формулировка без иероглифов')
            question_zh = record.get('questionZh')
        options = {option['id']: option['zh'] for option in record['options']}
        replaced = edit.get('options', {})
        if not isinstance(replaced, dict):
            errors.append(f'{record_id}: options должен быть словарём id → текст')
            replaced = {}
        for option_id, text in replaced.items():
            if option_id not in options:
                errors.append(f'{record_id}: варианта {option_id} нет')
            elif not isinstance(text, str) or not text.strip():
                errors.append(f'{record_id}: пустой вариант {option_id}')
            else:
                options[option_id] = text.strip()
        texts = list(options.values())
        if len({normalize_text(text) for text in texts}) != len(texts):
            errors.append(f'{record_id}: после правки варианты повторяются')
        if not isinstance(question, str):
            errors.append(f'{record_id}: вопрос должен быть строкой')
        else:
            errors.extend(f'{record_id}: {message}' for message in language_errors(question, texts))
            errors.extend(f'{record_id}: {message}' for message in completeness_errors(
                question, question_zh, texts))

        if 'explanation' in edit and (not isinstance(edit['explanation'], str)
                                      or not edit['explanation'].strip()):
            errors.append(f'{record_id}: пустое пояснение')
        for field in ('questionRu', 'explanation'):
            text = edit.get(field)
            if isinstance(text, str) and ('— —' in text or '  ' in text):
                errors.append(f'{record_id}: в {field} двойное тире или двойной пробел')
        if 'topic' in edit and edit['topic'] not in TOPICS:
            errors.append(f'{record_id}: тема вне списка семи категорий')
    return errors


def apply_editorial(bank: list[dict], edits: dict[str, dict]) -> list[dict]:
    errors = validate_editorial(edits, bank)
    if errors:
        raise ValueError('некорректные редакторские правки:\n - ' + '\n - '.join(errors))
    updated = []
    for record in bank:
        edit = edits.get(record['id'])
        if edit is None:
            updated.append(record)
            continue
        result = {**record, 'editorial': {'reason': edit['reason'].strip()}}
        if 'questionRu' in edit:
            result['questionRu'] = edit['questionRu']
        if 'questionZh' in edit:
            result['questionZh'] = edit['questionZh'].strip()
        if 'options' in edit:
            result['options'] = [{**option, 'zh': edit['options'].get(option['id'], option['zh']).strip()}
                                 for option in record['options']]
        if 'explanation' in edit:
            result['explanation'] = {**record.get('explanation', {}), 'ru': edit['explanation'].strip()}
        if 'topic' in edit:
            result['topic'] = edit['topic']
            result['topicSource'] = 'editorial'
        updated.append(result)
    return updated


def load_editorial(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    edits = json.loads(path.read_text('utf-8'))
    if not isinstance(edits, dict):
        raise ValueError('редакторские правки должны быть словарём id → правка')
    return edits
