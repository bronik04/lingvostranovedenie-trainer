"""Подписи к неверным вариантам и названия верных ответов поверх собранного банка.

Подпись — одна строка по-русски о том, что такое неверный вариант: название и
один опознавательный факт. Подпись к варианту-ответу — русское название верного
ответа (решение автора 2026-10-26): сборка кладёт её в `answer.gloss`, как у
вопросов досье, и в разборе ученик видит название — часть до « — ».

Любая подпись хранится вместе с копией текста варианта: если
вариант потом исправят через editorial.json, подпись перестанет совпадать, и
сборка остановится, чтобы подпись перепроверили, а не показали к другому тексту.
Источник подписи хранится для аудита и в интерфейс не попадает.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from strict_json import loads_unique

MAX_LENGTH = 90
CYRILLIC = re.compile(r'[А-Яа-яЁё]')
CJK = re.compile(r'[\u4e00-\u9fff]')
ENTRY_FIELDS = {'reviewedAt', 'options'}
GLOSS_FIELDS = {'zh', 'ru', 'source'}


def gloss_text_errors(text: object, zh: str) -> list[str]:
    """Правила текста подписи — общие для glosses.json и ячеек досье (scripts/dossiers.py)."""
    if not isinstance(text, str) or not CYRILLIC.search(text):
        return ['подпись не по-русски']
    errors: list[str] = []
    if len(text) > MAX_LENGTH:
        errors.append(f'подпись длиннее {MAX_LENGTH} символов')
    if '— —' in text or ' '.join(text.split()) != text:
        errors.append('подпись не в одну строку, двойное тире или лишние пробелы')
    # только китайский текст: вариант-год «1911» подпись начинает с года
    if CJK.search(zh) and zh in text:
        errors.append('подпись повторяет сам вариант по-китайски')
    return errors


def _source_ok(source: object) -> bool:
    if not isinstance(source, dict):
        return False
    if not isinstance(source.get('url'), str):
        return False
    url = urlparse(source['url'])
    title = source.get('title')
    return url.scheme in {'http', 'https'} and bool(url.netloc) and isinstance(title, str) and bool(title.strip())


def answer_name_errors(text: object) -> list[str]:
    """Название верного ответа — «Название — факт»: в разборе показывается часть до « — »."""
    if isinstance(text, str) and ' — ' in text and text.split(' — ')[0].strip():
        return []
    return ['название верного ответа — «Название — факт»']


def validate_glosses(glosses: object, bank: list[dict]) -> list[str]:
    if not isinstance(glosses, dict):
        return ['подписи должны быть словарём id → запись']
    errors: list[str] = []
    by_id = {record['id']: record for record in bank}
    for record_id, item in glosses.items():
        record = by_id.get(record_id)
        if record is None:
            errors.append(f'{record_id}: такой записи в банке нет')
            continue
        if not isinstance(item, dict):
            errors.append(f'{record_id}: запись подписей должна быть объектом')
            continue
        unknown = set(item) - ENTRY_FIELDS
        if unknown:
            errors.append(f'{record_id}: неизвестные поля {sorted(unknown)}')
        if not isinstance(item.get('reviewedAt'), str) or not item['reviewedAt'].strip():
            errors.append(f'{record_id}: нет даты проверки')
        if record['answer'].get('state') != 'verified' or not record['answer'].get('optionId'):
            errors.append(f'{record_id}: подпись к вопросу без проверенного ответа')
        options = item.get('options')
        if not isinstance(options, dict) or not options:
            errors.append(f'{record_id}: нет ни одной подписи')
            continue
        current = {option['id']: option['zh'] for option in record['options']}
        for option_id, gloss in options.items():
            where = f'{record_id}/{option_id}'
            if option_id not in current:
                errors.append(f'{where}: такого варианта нет')
                continue
            if not isinstance(gloss, dict):
                errors.append(f'{where}: подпись должна быть объектом')
                continue
            if option_id == record['answer']['optionId']:
                if 'dossier' in record:
                    errors.append(f'{where}: название верного ответа берётся из ячейки досье')
                errors.extend(f'{where}: {message}' for message in answer_name_errors(gloss.get('ru')))
            unknown = set(gloss) - GLOSS_FIELDS
            if unknown:
                errors.append(f'{where}: неизвестные поля {sorted(unknown)}')
            if gloss.get('zh') != current[option_id]:
                errors.append(f'{where}: вариант изменился ({gloss.get("zh")!r} → {current[option_id]!r}), '
                              'подпись нужно перепроверить')
            errors.extend(f'{where}: {message}' for message in gloss_text_errors(gloss.get('ru'), current[option_id]))
            if not _source_ok(gloss.get('source')):
                errors.append(f'{where}: нет источника с HTTP(S)-ссылкой и названием')
    return errors


def apply_glosses(bank: list[dict], glosses: dict[str, dict]) -> list[dict]:
    errors = validate_glosses(glosses, bank)
    if errors:
        raise ValueError('некорректные подписи к вариантам:\n - ' + '\n - '.join(errors))
    updated = []
    for record in bank:
        item = glosses.get(record['id'])
        if item is None:
            updated.append(record)
            continue
        answer_id = record['answer']['optionId']
        updated.append({**record, 'options': [
            {**option, 'gloss': item['options'][option['id']]['ru']}
            if option['id'] in item['options'] and option['id'] != answer_id else option
            for option in record['options']]}
            | ({'answer': {**record['answer'], 'gloss': item['options'][answer_id]['ru']}}
               if answer_id in item['options'] else {}))
    return updated


def load_glosses(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    glosses = loads_unique(path.read_text('utf-8'), 'подписях')
    if not isinstance(glosses, dict):
        raise ValueError('подписи должны быть словарём id → запись')
    return glosses
