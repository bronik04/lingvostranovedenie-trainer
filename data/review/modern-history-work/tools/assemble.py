"""Свести черновики частей в data/dossiers/modern-history.json проекта.

    python3 assemble.py

Порядок строк — по списку частей ниже (части, которых ещё нет, пропускаются).
"""
import json
from pathlib import Path

ROOT = Path('/Users/bronik04/Documents/Projects/lingvostranovedenie-trainer/.claude/worktrees/dossier-modern-history-6f7767')
HERE = Path(__file__).resolve().parent
ORDER = {'events': ['ev-cn-1', 'ev-cn-2', 'ev-cn-3', 'ev-ru-1', 'ev-ru-2'],
         'figures': ['fig-cn-1', 'fig-cn-2', 'fig-mix', 'fig-ru-mil'],
         'treaties': ['tr-cn', 'tr-ru']}
path = ROOT / 'data/dossiers/modern-history.json'
data = json.loads(path.read_text('utf-8'))
for table, parts in ORDER.items():
    rows = []
    for part in parts:
        file = HERE / 'drafts' / f'{part}.json'
        if file.exists():
            rows += json.loads(file.read_text('utf-8'))
    data['tables'][table]['rows'] = rows
    print(table, len(rows))
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', 'utf-8')
