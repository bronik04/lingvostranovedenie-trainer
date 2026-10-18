import json,sys,re,glob
P='/Users/bronik04/Documents/Projects/lingvostranovedenie-trainer/.claude/worktrees/dossier-modern-history-6f7767'
b=json.load(open(P+'/data/bank.json'))
recs=[]
for r in b:
    recs.append((r['id'],(r.get('questionRu') or '')+' || '+(r.get('questionZh') or ''),' / '.join(o['zh'] for o in r['options']), r['answer'].get('optionId') if isinstance(r['answer'],dict) else r['answer']))
# dossier questions of other dossiers
for f in glob.glob(P+'/data/dossiers/*-questions.json'):
    if 'modern-history' in f: continue
    for q in json.load(open(f)):
        if 'questionRu' in q: recs.append((q['id'],q['questionRu']+' || '+q.get('questionZh',''),'',''))
for pat in sys.argv[1:]:
    print('=== ',pat)
    for i,t,o,a in recs:
        if re.search(pat,t,re.I):
            print('  ',i,'|',t[:220],'|',o[:120])
