"""Встраивание олимпиадного вопроса в досье.

Вопрос досье с полем `embeds` не создаёт новую запись: олимпиадная запись остаётся собой (id,
формулировка, появления, исходные варианты и их id — на них держится прогресс учеников), но
получает общий набор неверных вариантов из той же колонки таблицы и подписи ко всем неверным
вариантам — из ячеек таблицы (`embed_record` в scripts/dossiers.py). Слой идёт после склеек и
удалений (`embeds` — итоговый id) и до `glosses.json`. Спецификация —
docs/superpowers/specs/2026-10-15-dossiers-myths-space-design.md.
"""

from __future__ import annotations

from dossiers import embed_record, original_record


def _embeds(loaded: list[tuple[dict, list[dict]]], drafts: bool):
    for dossier, questions in loaded:
        for question in questions:
            if 'embeds' in question and (drafts or question['status'] == 'accepted'):
                yield dossier, question


def embed_errors(bank: list[dict], loaded: list[tuple[dict, list[dict]]], glosses: dict[str, dict],
                 drafts: bool = False) -> list[str]:
    """Всё, что помешает встраиванию. `drafts` — проверять и черновики (проверка досье без сборки)."""
    by_id = {record['id']: record for record in bank}
    merged_into = {old: record['id'] for record in bank for old in record.get('mergedIds', [])}
    own_questions = {question['id'] for _, questions in loaded for question in questions if 'embeds' not in question}
    errors: list[str] = []
    embedded_by: dict[str, str] = {}
    for dossier, question in _embeds(loaded, drafts):
        where = f'{dossier["id"]}/{question["id"]}'
        target = question['embeds']
        record = by_id.get(target)
        if record is None:
            hint = f' — влита в {merged_into[target]}' if target in merged_into else ''
            errors.append(f'{where}: в банке нет записи {target}{hint}')
            continue
        if target in embedded_by:
            errors.append(f'{where}: запись {target} уже встроена вопросом {embedded_by[target]}')
            continue
        embedded_by[target] = where
        if target in own_questions:
            errors.append(f'{where}: {target} — вопрос досье, его не встраивают')
            continue
        # черновик подписи из glosses.json не трогает: банк живёт с ними, пока вопрос не принят
        if target in glosses and question['status'] == 'accepted':
            errors.append(f'{where}: у {target} есть подписи в glosses.json — перенесите их в ячейки таблицы')
            continue
        _, problems = embed_record(original_record(record), question, dossier)
        errors += [f'{where}: {problem}' for problem in problems]
    return errors


def apply_embeds(bank: list[dict], loaded: list[tuple[dict, list[dict]]],
                 glosses: dict[str, dict]) -> list[dict]:
    errors = embed_errors(bank, loaded, glosses)
    if errors:
        raise ValueError('некорректные встраивания:\n - ' + '\n - '.join(errors))
    updates: dict[str, dict] = {}
    by_id = {record['id']: record for record in bank}
    for dossier, question in _embeds(loaded, drafts=False):
        updates[question['embeds']], _ = embed_record(by_id[question['embeds']], question, dossier)
    return [updates.get(record['id'], record) for record in bank]
