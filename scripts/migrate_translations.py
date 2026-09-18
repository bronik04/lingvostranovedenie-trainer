"""Перенос переводов старого проекта на ключ, не зависящий от нумерации."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from normalize import normalize_text

OLD = Path.home() / 'Documents/Codex/2026-09-17/html/work'


def main() -> None:
    old_bank = json.loads((OLD / 'question_bank.json').read_text('utf-8'))
    old_translations = json.loads((OLD / 'manual_translations.json').read_text('utf-8'))
    by_id = {record['id']: record for record in old_bank}

    translations: dict[str, str] = {}
    skipped: list[str] = []
    for record_id, russian in old_translations.items():
        record = by_id.get(record_id)
        if record is None or not record.get('questionZh'):
            skipped.append(record_id)
            continue
        translations[normalize_text(record['questionZh'])] = russian.strip()

    target = ROOT / 'data/translations.json'
    target.write_text(
        json.dumps(dict(sorted(translations.items())), ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(f'перенесено переводов: {len(translations)}, пропущено: {len(skipped)}')
    if skipped:
        print('пропущенные ключи:', ', '.join(skipped[:10]))


if __name__ == '__main__':
    main()
