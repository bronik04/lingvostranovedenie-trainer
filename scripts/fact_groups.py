"""Метки «один и тот же факт» поверх собранного банка.

Олимпиада повторяет вопрос из года в год, слегка меняя варианты: это разные
задания, и склеивать их нельзя, но в одном раунде ученику незачем видеть два вопроса
про один факт. Группа — это список таких записей; в записи она превращается в поле
`factGroup`, по которому раунд берёт из группы не больше одного вопроса.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

GROUP_ID = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')


def validate_fact_groups(groups: object, bank: list[dict]) -> list[str]:
    if not isinstance(groups, dict):
        return ['группы должны быть словарём id группы → список id записей']
    errors: list[str] = []
    known = {record['id'] for record in bank}
    owner: dict[str, str] = {}
    for group_id, ids in groups.items():
        if not GROUP_ID.match(group_id):
            errors.append(f'{group_id}: id группы — латиница, цифры и дефисы')
        if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
            errors.append(f'{group_id}: группа должна быть списком id записей')
            continue
        if len(set(ids)) < 2:
            errors.append(f'{group_id}: в группе должно быть хотя бы две разные записи')
        if len(set(ids)) != len(ids):
            errors.append(f'{group_id}: id повторяются')
        for record_id in ids:
            if record_id not in known:
                errors.append(f'{group_id}: записи {record_id} в банке нет')
            elif owner.get(record_id, group_id) != group_id:
                errors.append(f'{record_id}: состоит в двух группах ({owner[record_id]} и {group_id})')
            owner[record_id] = group_id
    return errors


def apply_fact_groups(bank: list[dict], groups: dict[str, list[str]]) -> list[dict]:
    errors = validate_fact_groups(groups, bank)
    if errors:
        raise ValueError('некорректные группы фактов:\n - ' + '\n - '.join(errors))
    owner = {record_id: group_id for group_id, ids in groups.items() for record_id in ids}
    return [{**record, 'factGroup': owner[record['id']]} if record['id'] in owner else record
            for record in bank]


def load_fact_groups(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    groups = json.loads(path.read_text('utf-8'))
    if not isinstance(groups, dict):
        raise ValueError('группы должны быть словарём id группы → список id записей')
    return groups
