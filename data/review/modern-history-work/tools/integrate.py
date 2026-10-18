"""Свести вопросы и правки писателей в проект: python3 integrate.py [--final <check.json>].

- questions/modern-history-china.json + questions/modern-history-events.json → data/dossiers/modern-history-questions.json
  (порядок по id, все status: draft);
- `check` каждого вопроса — вердикт проверяющего первого круга (check-1/2/3) и ответ писателя (agree-*.json);
  с --final — вердикт финального проверяющего поверх;
- правки записей банка: questions/modern-history-editorial-*.json + editorial-night.json → data/review/editorial.json
  (поля записи сливаются, `reason` дописывается через «; »).
"""
import json
import sys
from pathlib import Path

ROOT = Path('/Users/bronik04/Documents/Projects/lingvostranovedenie-trainer/.claude/worktrees/dossier-modern-history-6f7767')
HERE = Path(__file__).resolve().parent


def load(path: Path, default):
    return json.loads(path.read_text('utf-8')) if path.exists() else default


questions = []
for name in ('modern-history-china.json', 'modern-history-events.json'):
    questions += load(HERE / 'questions' / name, [])
questions.sort(key=lambda q: int(q['id'].rsplit('q', 1)[1]))
checks = {}
for n in (1, 2, 3):
    for item in load(HERE / f'check-{n}' / 'modern-history-check.json', []):
        checks[item['id']] = item
agree = {**load(HERE / 'agree-figures.json', {}), **load(HERE / 'agree-events.json', {})}
final = {}
if '--final' in sys.argv:
    for item in load(Path(sys.argv[sys.argv.index('--final') + 1]), []):
        final[item['id']] = item
for q in questions:
    q['status'] = 'draft'
    if q['id'] in final:
        item = final[q['id']]
        q['check'] = {'verdict': {'reject': 'drop'}.get(item['verdict'], item['verdict']), 'note': item['note']}
    elif q['id'] in checks:
        item = checks[q['id']]
        note = item['note']
        if item['verdict'] != 'accept':
            answer = agree.get(q['id'], {})
            note += (' [писатель согласен, правки внесены]' if answer.get('agree')
                     else f' [писатель не согласен: {answer.get("note", "ответа нет")}]')
        q['check'] = {'verdict': {'reject': 'drop'}.get(item['verdict'], item['verdict']), 'note': note}
(ROOT / 'data/dossiers/modern-history-questions.json').write_text(
    json.dumps(questions, ensure_ascii=False, indent=2) + '\n', 'utf-8')
print('вопросов:', len(questions))

path = ROOT / 'data/review/editorial.json'
editorial = json.loads(path.read_text('utf-8'))
sources = sorted((HERE / 'questions').glob('modern-history-editorial-*.json')) + [HERE / 'editorial-night.json']
touched = []
for source in sources:
    for qid, edit in load(source, {}).items():
        current = dict(editorial.get(qid, {}))
        reason = edit.get('reason')
        for key, value in edit.items():
            if key == 'reason':
                continue
            if key == 'options':
                current['options'] = {**current.get('options', {}), **value}
            else:
                current[key] = value
        if reason and reason not in current.get('reason', ''):
            current['reason'] = f'{current["reason"]}; {reason}' if current.get('reason') else reason
        editorial[qid] = current
        touched.append(qid)
path.write_text(json.dumps(editorial, ensure_ascii=False, indent=2) + '\n', 'utf-8')
print('правки editorial.json:', sorted(set(touched)))
