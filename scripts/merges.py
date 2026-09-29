"""Склейка дублей поверх собранного банка.

Слияние сборки склеивает записи с одним набором вариантов и одной формулировкой,
а перефразированный вопрос с теми же вариантами остаётся отдельной записью. Такие
пары склеиваются здесь вручную: ключ — id записи, которая остаётся, `absorbs` — id
записей, которые в неё вливаются. Появления (год, этап, номер) переходят в оставшуюся
запись, поэтому фильтры по году и этапу по-прежнему находят вопрос, а `mergedIds`
позволяет странице перенести прогресс ученика с прежних id.

Склейка идёт после правок `editorial.json`: сравнение вариантов опирается на уже
исправленный текст. Правки и волны проверки для влитых записей остаются в файлах,
но в банк не попадают.
"""

from __future__ import annotations

from pathlib import Path

from normalize import normalize_text
from strict_json import loads_unique

STAGE_ORDER = {'pri': 0, 'shk': 1, 'mun': 2, 'reg': 3, 'zak': 4}
ENTRY_FIELDS = {'absorbs', 'reason'}


def _answer_text(record: dict) -> str | None:
    for option in record['options']:
        if option['id'] == record['answer'].get('optionId'):
            return normalize_text(option['zh'])
    return None


def _option_texts(record: dict) -> set[str]:
    return {normalize_text(option['zh']) for option in record['options']}


def _spot(occurrence: dict) -> tuple:
    return occurrence['year'], occurrence['stageCode'], occurrence['number']


def _key_and_spot_errors(keep: dict, absorbed: dict) -> list[str]:
    """Официальный ключ влитой записи обязан указывать на тот же ответ, а появления — не повторяться."""
    errors: list[str] = []
    absorbed_text = {option['id']: normalize_text(option['zh']) for option in absorbed['options']}
    answer = _answer_text(keep)
    for occurrence in absorbed['occurrences']:
        key = occurrence.get('officialKey')
        if key and absorbed_text.get(key) != answer:
            errors.append(f'{absorbed["id"]}: официальный ключ появления {occurrence["year"]} '
                          f'{occurrence["stageCode"]} расходится с ответом {keep["id"]} — '
                          'это конфликт ключей, а не дубль')
    taken = {_spot(o) for o in keep['occurrences'] if o['number'] is not None}
    for occurrence in absorbed['occurrences']:
        if occurrence['number'] is not None and _spot(occurrence) in taken:
            errors.append(f'{absorbed["id"]}: появление {_spot(occurrence)} уже есть у {keep["id"]}')
    return errors


def validate_merges(merges: object, bank: list[dict]) -> list[str]:
    if not isinstance(merges, dict):
        return ['склейки должны быть словарём id → запись']
    errors: list[str] = []
    by_id = {record['id']: record for record in bank}
    claimed: dict[str, str] = {}
    for keep_id, item in merges.items():
        keep = by_id.get(keep_id)
        if keep is None:
            errors.append(f'{keep_id}: такой записи в банке нет')
            continue
        if not isinstance(item, dict):
            errors.append(f'{keep_id}: склейка должна быть объектом')
            continue
        unknown = set(item) - ENTRY_FIELDS
        if unknown:
            errors.append(f'{keep_id}: неизвестные поля {sorted(unknown)}')
        if not isinstance(item.get('reason'), str) or not item['reason'].strip():
            errors.append(f'{keep_id}: не указана причина склейки')
        absorbs = item.get('absorbs')
        if not isinstance(absorbs, list) or not absorbs or not all(isinstance(i, str) for i in absorbs):
            errors.append(f'{keep_id}: absorbs должен быть непустым списком id')
            continue
        if len(set(absorbs)) != len(absorbs):
            errors.append(f'{keep_id}: id повторяются в absorbs')
        if not keep.get('occurrences'):
            errors.append(f'{keep_id}: склеивать можно только олимпиадные вопросы')
        if keep['answer'].get('state') != 'verified':
            errors.append(f'{keep_id}: ответ не проверен, склеивать рано')
        for absorbed_id in absorbs:
            if absorbed_id == keep_id:
                errors.append(f'{keep_id}: запись влита сама в себя')
                continue
            if absorbed_id in merges:
                errors.append(f'{absorbed_id}: влитая запись сама принимает другие')
            if absorbed_id in claimed:
                errors.append(f'{absorbed_id}: влита дважды ({claimed[absorbed_id]} и {keep_id})')
            claimed[absorbed_id] = keep_id
            absorbed = by_id.get(absorbed_id)
            if absorbed is None:
                errors.append(f'{absorbed_id}: такой записи в банке нет')
                continue
            if not absorbed.get('occurrences'):
                errors.append(f'{absorbed_id}: склеивать можно только олимпиадные вопросы')
            if absorbed['answer'].get('state') != 'verified':
                errors.append(f'{absorbed_id}: ответ не проверен, склеивать рано')
            elif _option_texts(absorbed) != _option_texts(keep):
                errors.append(f'{absorbed_id}: варианты не совпадают с {keep_id}')
            elif _answer_text(absorbed) != _answer_text(keep):
                errors.append(f'{absorbed_id}: ответ не совпадает с {keep_id}')
            else:
                errors += _key_and_spot_errors(keep, absorbed)
    return errors


def _reindexed(absorbed: dict, keep: dict) -> list[dict]:
    """Появления влитой записи с официальным ключом в id вариантов оставшейся.

    Ключ хранится как id варианта, а в разных записях варианты одного вопроса стоят в
    разном порядке и под разными id: перенесённый как есть, он указал бы на чужой вариант.
    """
    keep_ids = {normalize_text(option['zh']): option['id'] for option in keep['options']}
    absorbed_text = {option['id']: normalize_text(option['zh']) for option in absorbed['options']}
    return [{**occurrence, 'officialKey': keep_ids[absorbed_text[occurrence['officialKey']]]}
            if occurrence.get('officialKey') else occurrence
            for occurrence in absorbed['occurrences']]


def apply_merges(bank: list[dict], merges: dict[str, dict]) -> list[dict]:
    errors = validate_merges(merges, bank)
    if errors:
        raise ValueError('некорректные склейки:\n - ' + '\n - '.join(errors))
    by_id = {record['id']: record for record in bank}
    absorbed_ids = {absorbed_id for item in merges.values() for absorbed_id in item['absorbs']}
    result = []
    for record in bank:
        if record['id'] in absorbed_ids:
            continue
        item = merges.get(record['id'])
        if item is None:
            result.append(record)
            continue
        absorbed = [by_id[absorbed_id] for absorbed_id in item['absorbs']]
        occurrences = sorted(
            [*record['occurrences'], *(o for other in absorbed for o in _reindexed(other, record))],
            key=lambda o: (o['year'], STAGE_ORDER.get(o['stageCode'], 9),
                           o['number'] if o['number'] is not None else 10_000))
        # источники влитых записей не теряются: лишняя ссылка укрепляет ответ
        evidence = list(record.get('evidence', []))
        known = {entry['url'] for entry in evidence}
        for other in absorbed:
            for entry in other.get('evidence', []):
                if entry['url'] not in known:
                    evidence.append(entry)
                    known.add(entry['url'])
        result.append({**record, 'occurrences': occurrences, 'evidence': evidence,
                       'mergedIds': sorted(item['absorbs'])})
    return result


def load_merges(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    merges = loads_unique(path.read_text('utf-8'), 'склейках')
    if not isinstance(merges, dict):
        raise ValueError('склейки должны быть словарём id → запись')
    return merges
