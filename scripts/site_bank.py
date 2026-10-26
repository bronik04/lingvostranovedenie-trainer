"""Какие записи банка попадают на сайт.

`data/bank.json` — весь банк со всеми слоями, а на сайт по настройке `data/site.json` может идти не всё.
Сейчас это одна настройка: `showRegional` — показывать ли вопросы из региональных вариантов
(появления с `regionCode`, `scripts/parsers/regions.py`). Скрытая запись остаётся в банке: её правки,
проверки, встраивания и группы фактов на месте, прогресс учеников под её id ждёт возвращения.
"""

from __future__ import annotations

import json
from pathlib import Path

SETTINGS = Path(__file__).resolve().parents[1] / 'data/site.json'


def load_settings(path: Path = SETTINGS) -> dict:
    return json.loads(path.read_text('utf-8')) if path.exists() else {}


def site_bank(bank: list[dict], settings: dict) -> list[dict]:
    """Банк для сайта: без записей, у которых все появления региональные, и без региональных появлений у остальных."""
    if settings.get('showRegional', True):
        return bank
    result = []
    for record in bank:
        occurrences = record.get('occurrences', [])
        kept = [o for o in occurrences if not o.get('regionCode')]
        if occurrences and not kept:
            continue
        result.append(record if len(kept) == len(occurrences) else {**record, 'occurrences': kept})
    return result
