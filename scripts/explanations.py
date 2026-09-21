"""Проверка и применение волн улучшенных пояснений."""

from __future__ import annotations

import json
from pathlib import Path

from authored import evidence_errors, sentence_count


def validate_revisions(revisions: dict[str, dict], bank: list[dict]) -> list[str]:
    if not isinstance(revisions, dict):
        return ['волна пояснений должна быть объектом']

    by_id = {record['id']: record for record in bank if record.get('origin') is None}
    errors: list[str] = []
    for record_id, revision in revisions.items():
        if record_id not in by_id:
            errors.append(f'{record_id}: неизвестный олимпиадный вопрос')
            continue
        if not isinstance(revision, dict):
            errors.append(f'{record_id}: ревизия должна быть объектом')
            continue
        explanation = revision.get('explanation')
        if not isinstance(explanation, str) or not explanation.strip():
            errors.append(f'{record_id}: нет пояснения')
        elif not 3 <= sentence_count(explanation) <= 5:
            errors.append(f'{record_id}: пояснение должно состоять из 3–5 предложений')
        errors.extend(f'{record_id}: {message}' for message in evidence_errors(revision.get('evidence')))
        if not isinstance(revision.get('reviewedAt'), str) or not revision['reviewedAt'].strip():
            errors.append(f'{record_id}: нет даты ревизии')
    return errors


def apply_revisions(bank: list[dict], revisions: dict[str, dict]) -> list[dict]:
    errors = validate_revisions(revisions, bank)
    if errors:
        raise ValueError('некорректные ревизии пояснений:\n - ' + '\n - '.join(errors))
    updated = []
    for record in bank:
        revision = revisions.get(record['id'])
        if revision is None:
            updated.append(record)
            continue
        updated.append({
            **record,
            'explanation': {'ru': revision['explanation'].strip()},
            'evidence': revision['evidence'],
            'explanationRevision': 2,
            'explanationReviewedAt': revision['reviewedAt'],
        })
    return updated


def load_revisions(path: Path, bank: list[dict]) -> dict[str, dict]:
    revisions = json.loads(path.read_text('utf-8'))
    errors = validate_revisions(revisions, bank)
    if errors:
        raise ValueError('некорректные ревизии пояснений:\n - ' + '\n - '.join(errors))
    return revisions
