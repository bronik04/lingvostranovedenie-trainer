"""Удаление записей поверх собранного банка.

Иногда две записи спрашивают об одном факте с разных сторон и с разными ответами
(«В какой части Китая больше всего людей?» → 东部 и «Особенность распределения
населения?» → 东多西少). Склеить их нельзя — у них разные варианты и ответы, — и автор
оставляет одну. Удалённая запись уходит из банка, а её id записывается в `mergedIds`
оставшейся: ученик отвечал на вопрос о том же факте, и его прогресс переезжает
(`migrateProgress` в `src/quiz.mjs`). Варианты, пояснение и появления удалённой
записи оставшаяся не получает: это другой вопрос.

Слой идёт после склеек: правки и проверки удалённой записи остаются в файлах, но в
банк не попадают.
"""

from __future__ import annotations

from pathlib import Path

from strict_json import loads_unique

FIELDS = {'keptIn', 'reason'}


def validate_retired(retired: object, bank: list[dict]) -> list[str]:
    if not isinstance(retired, dict):
        return ['удаления должны быть словарём id → запись']
    errors: list[str] = []
    known = {record['id'] for record in bank}
    for record_id, item in retired.items():
        if record_id not in known:
            errors.append(f'{record_id}: такой записи в банке нет')
        if not isinstance(item, dict):
            errors.append(f'{record_id}: запись удаления должна быть объектом')
            continue
        unknown = set(item) - FIELDS
        if unknown:
            errors.append(f'{record_id}: неизвестные поля {sorted(unknown)}')
        if not isinstance(item.get('reason'), str) or not item['reason'].strip():
            errors.append(f'{record_id}: не указана причина удаления')
        kept = item.get('keptIn')
        if kept == record_id:
            errors.append(f'{record_id}: запись оставлена сама вместо себя')
        elif kept not in known:
            errors.append(f'{kept}: такой записи в банке нет')
        elif kept in retired:
            errors.append(f'{kept}: оставленная запись сама удалена')
    return errors


def apply_retired(bank: list[dict], retired: dict[str, dict]) -> list[dict]:
    errors = validate_retired(retired, bank)
    if errors:
        raise ValueError('некорректные удаления:\n - ' + '\n - '.join(errors))
    by_id = {record['id']: record for record in bank}
    moved: dict[str, list[str]] = {}
    for record_id, item in retired.items():
        # вместе с удалённой записью переезжают и id, влитые в неё раньше
        moved.setdefault(item['keptIn'], []).extend([record_id, *by_id[record_id].get('mergedIds', [])])
    result = []
    for record in bank:
        if record['id'] in retired:
            continue
        if record['id'] in moved:
            record = {**record, 'mergedIds': sorted([*record.get('mergedIds', []), *moved[record['id']]])}
        result.append(record)
    return result


def load_retired(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    retired = loads_unique(path.read_text('utf-8'), 'удалениях')
    if not isinstance(retired, dict):
        raise ValueError('удаления должны быть словарём id → запись')
    return retired
