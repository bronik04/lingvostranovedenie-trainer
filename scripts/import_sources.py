"""Прогон всех парсеров: sources/ -> data/raw/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from parsers import bank423, categories310, pdf_papers, vsosh

JOBS = [
    ('bank423', 'Банк вопросов — лингвострановедение (423, с ответами).docx', bank423.parse),
    ('categories310', 'Вопросы по категориям (310 шт).docx', categories310.parse),
    ('vsosh', 'Лингвострановедение ВсОШ.docx', vsosh.parse),
    ('paper-2022-23-mun', 'Лингвострановедение 2022-23 — Муниципальный.pdf', pdf_papers.parse),
    ('paper-2022-23-reg', 'Лингвострановедение 2022-23 — Региональный.pdf', pdf_papers.parse),
    ('paper-2022-23-zak', 'Лингвострановедение 2022-23 — Заключительный.pdf', pdf_papers.parse),
    ('paper-2023-24', 'Лингвострановедение 2023-24.pdf', pdf_papers.parse),
    ('paper-2024-25', 'Лингвострановедение 2024-25.pdf', pdf_papers.parse),
]


def main() -> None:
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    index = []
    for slug, filename, parse in JOBS:
        path = ROOT / 'sources' / filename
        if not path.exists():
            print(f'пропуск, файла нет: {filename}')
            continue
        records = parse(path)
        (raw / f'{slug}.json').write_text(
            json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        index.append({'slug': slug, 'sourceFile': filename, 'records': len(records)})
        print(f'{slug}: {len(records)}')
    (raw / 'index.json').write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
