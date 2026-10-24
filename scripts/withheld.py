"""Олимпиадные задания, которые автор пока не публикует.

Запись собирается из первоисточника, как все, но в банк не попадает, пока в ней остаётся
сомнение, которое автор не разрешил: ответ ключа не подтверждён источниками, в формулировке
спорное утверждение, варианты с ошибками бланка. Это не удаление: когда сомнение снято,
строку отсюда убирают, и запись выходит под своим id.

Слой идёт после удалений `retired.json`: правки и проверки отложенной записи остаются в
файлах, но в банк не попадают.
"""

from __future__ import annotations

from pathlib import Path

from strict_json import loads_unique

FIELDS = {'reason', 'date'}


def validate_withheld(withheld: object, bank: list[dict]) -> list[str]:
    if not isinstance(withheld, dict):
        return ['отложенные задания должны быть словарём id → запись']
    errors: list[str] = []
    by_id = {record['id']: record for record in bank}
    for record_id, item in withheld.items():
        record = by_id.get(record_id)
        if record is None:
            errors.append(f'{record_id}: такой записи в банке нет')
        elif not record.get('occurrences'):
            errors.append(f'{record_id}: откладывать можно только олимпиадные задания — '
                          'принятый вопрос досье снимают через removed.json')
        elif record.get('mergedIds'):
            errors.append(f'{record_id}: в запись влиты {record["mergedIds"]} — '
                          'перенесённый на неё прогресс учеников пропал бы')
        if not isinstance(item, dict):
            errors.append(f'{record_id}: запись должна быть объектом')
            continue
        unknown = set(item) - FIELDS
        if unknown:
            errors.append(f'{record_id}: неизвестные поля {sorted(unknown)}')
        if not isinstance(item.get('reason'), str) or not item['reason'].strip():
            errors.append(f'{record_id}: не указана причина')
        if not isinstance(item.get('date'), str) or not item['date'].strip():
            errors.append(f'{record_id}: не указана дата решения')
    return errors


def apply_withheld(bank: list[dict], withheld: dict[str, dict]) -> list[dict]:
    errors = validate_withheld(withheld, bank)
    if errors:
        raise ValueError('некорректные отложенные задания:\n - ' + '\n - '.join(errors))
    return [record for record in bank if record['id'] not in withheld]


def load_withheld(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    withheld = loads_unique(path.read_text('utf-8'), 'отложенных заданиях')
    if not isinstance(withheld, dict):
        raise ValueError('отложенные задания должны быть словарём id → запись')
    return withheld
