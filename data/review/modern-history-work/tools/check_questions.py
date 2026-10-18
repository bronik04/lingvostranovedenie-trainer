"""Проверка черновиков вопросов «Истории XIX–XX веков»: python3 check_questions.py [<папка>] [--report].

Берёт досье проекта и подставляет вопросы «Истории XIX–XX веков» из папки (по умолчанию questions/):
modern-history-questions.json (или modern-history-china.json и modern-history-russia.json) становится файлом
вопросов досье, так что утечки между вопросами обоих писателей и всех досье видны сразу. Проверяет
всё, что проверит сборка: вопросы, встраивания, ссылки, утечки. С --report пишет отчёт
<папка>/modern-history-report.md. Правки записей банка из <папка>/modern-history-editorial-*.json
(`explanation`, `questionRu`, `options`) подставляются в банк так, как их наложит сборка.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path('/Users/bronik04/Documents/Projects/lingvostranovedenie-trainer/.claude/worktrees/dossier-modern-history-6f7767')
ARGS = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
DRAFTS = Path(ARGS[0]).resolve() if ARGS else Path(__file__).resolve().parent / 'questions'
sys.path.insert(0, str(ROOT / 'scripts'))
from dossiers import check_dossiers, dossier_report  # noqa: E402
from glosses import load_glosses  # noqa: E402
from fact_groups import load_fact_groups  # noqa: E402

bank = json.loads((ROOT / 'data/bank.json').read_text('utf-8'))
proposals = {}
for path in sorted(DRAFTS.glob('modern-history-editorial*.json')):
    for qid, edit in json.loads(path.read_text('utf-8')).items():
        if qid in proposals:
            for key in ('explanation', 'questionRu'):
                if key in edit and key in proposals[qid]:
                    print(f'{qid}: {key} правят оба файла правок')
            options = {**proposals[qid].get('options', {}), **edit.get('options', {})}
            proposals[qid] = {**proposals[qid], **edit}
            if options:
                proposals[qid]['options'] = options
        else:
            proposals[qid] = edit
for record in bank:
    edit = proposals.get(record['id'])
    if not edit:
        continue
    if 'explanation' in edit:
        record['explanation'] = {**record.get('explanation', {}), 'ru': edit['explanation']}
    if 'questionRu' in edit:
        record['questionRu'] = edit['questionRu']
    for option in record['options']:
        if option['id'] in edit.get('options', {}):
            option['zh'] = edit['options'][option['id']]
questions = []
names = ['modern-history-questions.json'] if (DRAFTS / 'modern-history-questions.json').exists() else ['modern-history-china.json', 'modern-history-russia.json']
for name in names:
    if (DRAFTS / name).exists():
        questions += json.loads((DRAFTS / name).read_text('utf-8'))
with tempfile.TemporaryDirectory() as tmp:
    directory = Path(tmp)
    for path in (ROOT / 'data/dossiers').glob('*.json'):
        shutil.copy(path, directory / path.name)
    (directory / 'modern-history-questions.json').write_text(json.dumps(questions, ensure_ascii=False), encoding='utf-8')
    errors, loaded = check_dossiers(directory, bank, load_glosses(ROOT / 'data/review/glosses.json'),
                                    load_fact_groups(ROOT / 'data/review/fact-groups.json'))
for data, qs in loaded:
    if data['id'] == 'modern-history':
        print(f'modern-history: вопросов {len(qs)}')
        if '--report' in sys.argv:
            (DRAFTS / 'modern-history-report.md').write_text(dossier_report(data, qs, bank), encoding='utf-8')
print('\n'.join(errors) if errors else 'ошибок нет')
sys.exit(1 if errors else 0)
