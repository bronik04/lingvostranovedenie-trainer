"""Прогон всех парсеров: sources/ -> data/raw/."""

from __future__ import annotations

import json
import sys
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from parsers import bank423, categories310, cifrium, pdf_papers, regions, vsosh

JOBS = [
    ('bank423', 'Банк вопросов — лингвострановедение (423, с ответами).docx', bank423.parse),
    ('categories310', 'Вопросы по категориям (310 шт).docx', categories310.parse),
    ('vsosh', 'Лингвострановедение ВсОШ.docx', vsosh.parse),
    ('paper-2022-23-mun', 'Лингвострановедение 2022-23 — Муниципальный.pdf', pdf_papers.parse),
    ('paper-2022-23-reg', 'Лингвострановедение 2022-23 — Региональный.pdf', pdf_papers.parse),
    ('paper-2022-23-zak', 'Лингвострановедение 2022-23 — Заключительный.pdf', pdf_papers.parse),
    ('paper-2023-24', 'Лингвострановедение 2023-24.pdf', pdf_papers.parse),
    ('paper-2024-25', 'Лингвострановедение 2024-25.pdf', pdf_papers.parse),
    # в выгрузке Цифриума год не напечатан; муниципальный этап 2026/27 — со слов автора (2026-10-24).
    # Номер задания — порядок в разделе, классов и региона в id нет: вариант того же этапа для 7–8
    # классов или другого региона получил бы те же id и суффиксы -a/-b в зависимости от порядка —
    # такой выгрузке до первой сборки нужен свой сдвиг номеров
    # выгрузка оказалась вариантом Московской области (тот же файл лежит в папке региональных
    # вариантов); регион здесь только подпись, без кода региона: код вошёл бы в id и сбросил прогресс
    ('cifrium-2026-27-mun', 'Муниципальный этап 2026-27, 9–11 классы (Цифриум).pdf',
     partial(cifrium.parse, year='2026-27', region='Московская область')),
]
# региональные варианты: сами PDF лежат вне репозитория, источник — расшифровка (см. parsers/regions.py)
DATA_JOBS = [
    ('regions', 'data/regions/variants.json', regions.parse),
]


def main() -> None:
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    index = []
    for slug, filename, parse in [*JOBS, *DATA_JOBS]:
        path = ROOT / ('' if filename.startswith('data/') else 'sources') / filename
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
