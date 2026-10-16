"""Варианты, которые формат «Верно или нет» не предлагает.

Неверный в олимпиадном вопросе вариант бывает верен как отдельное утверждение:
«средняя высота нагорья — выше 3000 м» правда, хотя ответ на вопрос — «выше 4500 м».
В «Верно или нет» такой вариант выдал бы ошибку за верный ответ. Слой хранит,
какие варианты исключить, вместе с копией их текста: если вариант потом исправят
через editorial.json, сборка остановится, чтобы исключение перепроверили.
В выборе из четырёх и во «Вспомни сам» вопрос не меняется.
"""

from __future__ import annotations

from pathlib import Path

from strict_json import loads_unique

ENTRY_FIELDS = {'exclude', 'reason'}


def validate_truefalse(layer: object, bank: list[dict]) -> list[str]:
    if not isinstance(layer, dict):
        return ['исключения «Верно или нет» должны быть словарём id → запись']
    errors: list[str] = []
    by_id = {record['id']: record for record in bank}
    for record_id, item in layer.items():
        record = by_id.get(record_id)
        if record is None:
            errors.append(f'{record_id}: такой записи в банке нет')
            continue
        if not isinstance(item, dict):
            errors.append(f'{record_id}: запись исключений должна быть объектом')
            continue
        unknown = set(item) - ENTRY_FIELDS
        if unknown:
            errors.append(f'{record_id}: неизвестные поля {sorted(unknown)}')
        if not isinstance(item.get('reason'), str) or not item['reason'].strip():
            errors.append(f'{record_id}: нет причины')
        exclude = item.get('exclude')
        if not isinstance(exclude, dict) or not exclude:
            errors.append(f'{record_id}: не исключено ни одного варианта')
            continue
        current = {option['id']: option['zh'] for option in record['options']}
        right = record['answer'].get('optionId')
        for option_id, zh in exclude.items():
            where = f'{record_id}/{option_id}'
            if option_id not in current:
                errors.append(f'{where}: такого варианта нет')
            elif option_id == right:
                errors.append(f'{where}: исключён правильный ответ')
            elif zh != current[option_id]:
                errors.append(f'{where}: вариант изменился ({zh!r} → {current[option_id]!r}), '
                              'исключение нужно перепроверить')
        if not any(option_id != right and option_id not in exclude for option_id in current):
            errors.append(f'{record_id}: не осталось ни одного неверного варианта для «Верно или нет»')
    return errors


def apply_truefalse(bank: list[dict], layer: dict[str, dict]) -> list[dict]:
    errors = validate_truefalse(layer, bank)
    if errors:
        raise ValueError('некорректные исключения «Верно или нет»:\n - ' + '\n - '.join(errors))
    updated = []
    for record in bank:
        item = layer.get(record['id'])
        if item is None:
            updated.append(record)
            continue
        updated.append({**record, 'options': [
            {**option, 'trueFalse': False} if option['id'] in item['exclude'] else option
            for option in record['options']]})
    return updated


def load_truefalse(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    layer = loads_unique(path.read_text('utf-8'), 'исключениях «Верно или нет»')
    if not isinstance(layer, dict):
        raise ValueError('исключения «Верно или нет» должны быть словарём id → запись')
    return layer
