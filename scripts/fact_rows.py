"""Строка досье у олимпиадных записей, которые к ней только привязаны (решение автора 2026-10-25).

Строка досье перечисляет в `olympiad` задания, которые о ней спрашивали. Вопрос досье и встроенная
запись (`embeds`) получают `factRow` от своего слоя; привязанная запись — здесь, по всем строкам, где
она стоит: одна строка — строка `factRow`, несколько — их список. Раунд не ставит рядом записи с общей
строкой (`factKeys`, src/quiz.mjs), проверка подписей считает такие пары сторонами одной строки.
id, текст и варианты записи не меняются: прогресс учеников остаётся при ней. Слой идёт после
встраиваний — у встроенной записи строка уже есть (`dossier`).
"""

from __future__ import annotations


def attached_rows(bank: list[dict], loaded: list[tuple[dict, list[dict]]]) -> dict[str, list[str]]:
    """id записи → строки досье (`досье/таблица/строка`), к которым она привязана, по порядку.
    Влитый id ведёт к оставшейся записи; id, которого в банке нет (отложенное задание), пропускается."""
    final = {old: record['id'] for record in bank for old in record.get('mergedIds', [])}
    final |= {record['id']: record['id'] for record in bank}
    own = {record['id'] for record in bank if 'dossier' in record}
    rows: dict[str, set[str]] = {}
    for dossier, _ in loaded:
        for table_id, table in dossier['tables'].items():
            for row in table['rows']:
                for record_id in row.get('olympiad', []):
                    target = final.get(record_id)
                    if target is not None and target not in own:
                        rows.setdefault(target, set()).add(f'{dossier["id"]}/{table_id}/{row["id"]}')
    return {record_id: sorted(places) for record_id, places in rows.items()}


def apply_fact_rows(bank: list[dict], loaded: list[tuple[dict, list[dict]]]) -> list[dict]:
    rows = attached_rows(bank, loaded)
    return [{**record, 'factRow': rows[record['id']][0] if len(rows[record['id']]) == 1 else rows[record['id']]}
            if record['id'] in rows else record for record in bank]
