"""Какие записи банка попадают на сайт.

`data/bank.json` — весь банк со всеми слоями, а на сайт по настройке `data/site.json` может идти не всё:
- `showRegional` — показывать ли вопросы из региональных вариантов (появления с `regionCode`,
  `scripts/parsers/regions.py`);
- `showEmbeddedIn` — досье, чьи встраивания региональных записей показываются и при `showRegional: false`;
- `showRegionalIds` — отдельные региональные записи, которые показываются всё равно.
- `hiddenQuestions` — явно снятые автором с тренировок записи (id → reason, date), независимо от региональных исключений.
Скрытая запись остаётся в банке: её правки, проверки, встраивания и группы фактов на месте, прогресс учеников
под её id ждёт возвращения.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / 'data/site.json'


def load_settings(path: Path = SETTINGS) -> dict:
    return json.loads(path.read_text('utf-8')) if path.exists() else {}


def embedded_by(dossiers: Path = ROOT / 'data/dossiers') -> dict[str, str]:
    """Олимпиадная запись → досье, принятый вопрос которого её встраивает (черновик запись не открывает)."""
    result = {}
    for path in sorted(dossiers.glob('*-questions.json')):
        for question in json.loads(path.read_text('utf-8')):
            if question.get('embeds') and question.get('status') == 'accepted':
                result[question['embeds']] = path.name.removesuffix('-questions.json')
    return result


def site_bank(bank: list[dict], settings: dict, embeds: dict[str, str] | None = None) -> list[dict]:
    """Банк для сайта: с редакторским отбором, затем с фильтром региональных появлений."""
    hidden = settings.get('hiddenQuestions', {})
    if not isinstance(hidden, dict):
        raise ValueError('hiddenQuestions должен быть словарём id → reason, date')
    by_id = {record['id'] for record in bank}
    for record_id, entry in hidden.items():
        if record_id not in by_id:
            raise ValueError(f'hiddenQuestions: {record_id} — такой записи в банке нет')
        if not isinstance(entry, dict) or any(
                not isinstance(entry.get(field), str) or not entry[field].strip()
                for field in ('reason', 'date')):
            raise ValueError(f'hiddenQuestions: {record_id} — нужны reason и date')
    if hidden:
        bank = [record for record in bank if record['id'] not in hidden]
    if settings.get('showRegional', True):
        return bank
    keep_dossiers = set(settings.get('showEmbeddedIn', []))
    keep_ids = set(settings.get('showRegionalIds', []))
    embeds = embeds or {}
    result = []
    for record in bank:
        if record['id'] in keep_ids or embeds.get(record['id']) in keep_dossiers:
            result.append(record)
            continue
        occurrences = record.get('occurrences', [])
        kept = [o for o in occurrences if not o.get('regionCode')]
        if occurrences and not kept:
            continue
        result.append(record if len(kept) == len(occurrences) else {**record, 'occurrences': kept})
    return result
