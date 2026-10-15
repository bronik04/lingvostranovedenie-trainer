#!/usr/bin/env python3
"""Контрольные суммы первоисточников."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_manifest(folder: Path) -> None:
    entries = []
    for path in sorted(folder.iterdir()):
        if path.suffix not in {'.docx', '.pdf'}:
            continue
        data = path.read_bytes()
        entries.append({
            'name': path.name,
            'sha256': hashlib.sha256(data).hexdigest(),
            'bytes': len(data),
        })
    target = folder / 'manifest.json'
    target.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(entries)} источников записано в {target}')


def main() -> None:
    # бланки лингвострановедения — в корне sources/, бланки ЛГ-теста для раздела
    # «Чэнъюй» — в sources/chengyu/ со своим манифестом
    write_manifest(ROOT / 'sources')
    write_manifest(ROOT / 'sources/chengyu')


if __name__ == '__main__':
    main()
