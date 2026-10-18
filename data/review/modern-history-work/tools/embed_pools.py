"""Какой общий набор получит каждый встраиваемый вопрос по текущим черновикам: python3 embed_pools.py.

Пишет embed-pools.md: формулировка, исходные варианты, весь набор колонки (where: та же страна, что у
ответа; у events.name — ещё тот же kind) с подписями. Это предпросмотр для сверщиков и писателей: окончательные
where/exclude задаёт писатель.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TABLE_OF = {'ev': 'events', 'fig': 'figures', 'tr': 'treaties'}
rows = {'events': [], 'figures': [], 'treaties': []}
for file in sorted((HERE / 'drafts').glob('*.json')):
    rows[TABLE_OF[file.name.split('-', 1)[0]]] += json.loads(file.read_text('utf-8'))
targets = json.loads((HERE / 'embed-targets.json').read_text('utf-8'))
out = ['# Наборы встраиваний по текущим черновикам', '']
for qid, t in targets.items():
    table, column = t['place'].split('.')
    answer = next((r for r in rows[table] if isinstance(r.get(column), dict) and r[column]['zh'] == t['answer']), None)
    out += [f'## {qid} — {t["place"]}', '', f'«{t["questionRu"]}» ({t.get("questionZh") or "—"})', '',
            f'Исходные варианты: {", ".join(t["options"])}; ответ {t["answer"]}', '']
    if answer is None:
        out += ['Строки ответа ещё нет.', '']
        continue
    where = {'country': answer['country']['zh']}
    if table == 'events' and column == 'name':
        where['kind'] = answer.get('kind', {}).get('zh')
    out.append(f'where {where}; строка ответа {answer["id"]}')
    out.append('')
    for r in rows[table]:
        cell = r.get(column)
        if not isinstance(cell, dict) or any((r.get(k) or {}).get('zh') != v for k, v in where.items()):
            continue
        mark = '**ответ**' if r is answer else ('исходный' if cell['zh'] in t['options'] else 'добавлен')
        out.append(f'- {cell["zh"]} ({r["id"]}, {mark}) — {cell.get("gloss", "без подписи")}')
    out.append('')
(HERE / 'embed-pools.md').write_text('\n'.join(out), 'utf-8')
print('embed-pools.md:', len(targets), 'вопросов')
