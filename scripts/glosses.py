"""Подписи к неверным вариантам поверх собранного банка.

Подпись — одна строка по-русски о том, что такое неверный вариант: название и
один опознавательный факт. Она хранится вместе с копией текста варианта: если
вариант потом исправят через editorial.json, подпись перестанет совпадать, и
сборка остановится, чтобы подпись перепроверили, а не показали к другому тексту.
Источник подписи хранится для аудита и в интерфейс не попадает.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

MAX_LENGTH = 90
CYRILLIC = re.compile(r'[А-Яа-яЁё]')
ENTRY_FIELDS = {'reviewedAt', 'options'}
GLOSS_FIELDS = {'zh', 'ru', 'source'}


def _source_ok(source: object) -> bool:
    if not isinstance(source, dict):
        return False
    if not isinstance(source.get('url'), str):
        return False
    url = urlparse(source['url'])
    title = source.get('title')
    return url.scheme in {'http', 'https'} and bool(url.netloc) and isinstance(title, str) and bool(title.strip())


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
            if option_id == record['answer']['optionId']:
                errors.append(f'{where}: подпись у правильного варианта')
            if not isinstance(gloss, dict):
                errors.append(f'{where}: подпись должна быть объектом')
                continue
            unknown = set(gloss) - GLOSS_FIELDS
            if unknown:
                errors.append(f'{where}: неизвестные поля {sorted(unknown)}')
            if gloss.get('zh') != current[option_id]:
                errors.append(f'{where}: вариант изменился ({gloss.get("zh")!r} → {current[option_id]!r}), '
                              'подпись нужно перепроверить')
            text = gloss.get('ru')
            if not isinstance(text, str) or not CYRILLIC.search(text):
                errors.append(f'{where}: подпись не по-русски')
            else:
                if len(text) > MAX_LENGTH:
                    errors.append(f'{where}: подпись длиннее {MAX_LENGTH} символов')
                if '— —' in text or ' '.join(text.split()) != text:
                    errors.append(f'{where}: подпись не в одну строку, двойное тире или лишние пробелы')
                if current[option_id] in text:
                    errors.append(f'{where}: подпись повторяет сам вариант по-китайски')
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
        updated.append({**record, 'options': [
            {**option, 'gloss': item['options'][option['id']]['ru']} if option['id'] in item['options'] else option
            for option in record['options']]})
    return updated


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    keys = [key for key, _ in pairs]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise ValueError(f'в подписях повторяются ключи: {duplicates}')
    return dict(pairs)


def load_glosses(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    glosses = json.loads(path.read_text('utf-8'), object_pairs_hook=_no_duplicate_keys)
    if not isinstance(glosses, dict):
        raise ValueError('подписи должны быть словарём id → запись')
    return glosses
