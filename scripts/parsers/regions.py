"""Задания региональных вариантов школьного и муниципального этапов (9–11 классы).

Варианты разных регионов лежат вне репозитория (больше 100 МБ PDF), поэтому первоисточник здесь —
расшифровка `data/regions/variants.json`: текст задания дословно из бланка, номер, официальный ключ,
путь к файлу в папке вариантов автора и контрольная сумма файла. Совпадение
расшифровки с бланками проверяет `python3 scripts/regions.py --sources <папка вариантов>`.

В банк идут только задания со статусом `add` из `data/review/regions.json`: остальные уже есть в банке,
повторяют другое региональное задание, узкие, сомнительные или не подходят по формату — решение и
причина записаны там же.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECISIONS = ROOT / 'data/review/regions.json'


def task_id(variant: dict, task: dict) -> str:
    """«2025-26-mun-spb-3»: регион входит в id, иначе задание 3 Петербурга совпало бы с московским."""
    return f"{variant['id']}-{task['number']}"


def records(variants: list[dict], decisions: dict[str, dict]) -> list[dict]:
    result = []
    for variant in variants:
        for task in variant['tasks']:
            if decisions.get(task_id(variant, task), {}).get('status') != 'add':
                continue
            result.append({
                'sourceFile': variant['origin'][0]['file'],
                'year': variant['year'],
                'stage': variant['stage'],
                'stageCode': variant['stageCode'],
                'region': variant['region'],
                'regionCode': variant['regionCode'],
                'grades': variant['grades'],
                'number': task['number'],
                'sourceOrdinal': None,
                'questionRu': task['questionRu'],
                'questionZh': task['questionZh'],
                'options': list(task['options']),
                'officialKeyIndex': task['officialKeyIndex'],
                'topic': None,
                'parseWarnings': ['расшифровано по картинке страницы'] if task.get('transcribed') else [],
            })
    return result


def parse(path: Path) -> list[dict]:
    variants = json.loads(path.read_text('utf-8'))
    decisions = json.loads(DECISIONS.read_text('utf-8'))
    return records(variants, decisions)
