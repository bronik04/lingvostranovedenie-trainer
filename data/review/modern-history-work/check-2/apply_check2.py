import json,sys,shutil
S='/private/tmp/claude-501/-Users-bronik04-Documents-Projects-lingvostranovedenie-trainer--claude-worktrees-dossier-modern-history-6f7767/b3342384-f33d-457d-85b3-74ba62552ef3/scratchpad/mh'
D=S+'/check-2'
shutil.copy(S+'/questions/modern-history-events.json', D+'/modern-history-events.json')
qs=json.load(open(D+'/modern-history-events.json'))
by={q['id']:q for q in qs}
QING=['ev-humen','ev-yapian1','ev-taiping','ev-yapian2','ev-jiawu','ev-wuxu','ev-baguo']
REP=['ev-xinhai','ev-xinwenhua','ev-wusi','ev-jiandang','ev-beifa','ev-nanchang','ev-jiuyiba','ev-changzheng','ev-zunyi','ev-xian','ev-qiqi','ev-nanjing','ev-kailuo']
PRC=['ev-kaiguo','ev-fensui','ev-gaige','ev-nanxun','ev-xianggang','ev-aomen']
def keep(rows, me, extra=()):
    allrows=QING+REP+PRC
    return [r for r in allrows if r not in rows and r!=me] + [r for r in extra if r!=me]
def ex(keepset, me, extra=()):
    allrows=QING+REP+PRC
    out=[r for r in allrows if r not in keepset and r!=me]
    return out+[r for r in extra if r not in out]
QINGPLUS=QING+['ev-xinhai']
REPS=REP
P={}
P['modern-history-q53']={'exclude':ex(PRC,'ev-gaige')}
for qid,row in [('q54','ev-humen'),('q56','ev-yapian2'),('q57','ev-taiping'),('q59','ev-jiawu'),('q62','ev-baguo')]:
    P['modern-history-'+qid]={'exclude':ex(QINGPLUS,row)}
P['modern-history-q55']={'exclude':ex(QINGPLUS,'ev-yapian1',['ev-humen']),
 'explanation':'Первая опиумная война (第一次鸦片战争) Англии против Китая началась в 1840 году. Английская экспедиция из сорока с лишним кораблей и более чем четырёх тысяч солдат начала блокаду устья Чжуцзяна и наступление на Гуанчжоу. Война продолжалась до 1842 года. С её начала в Китае отсчитывают новую историю.'}
P['modern-history-q68']={'exclude':ex(REPS,'ev-changzheng')}
P['modern-history-q71']={'exclude':ex(REPS,'ev-qiqi',['ev-nanjing'])}
P['modern-history-q73']={'exclude':ex(PRC,'ev-nanxun'),
 'questionRu':'В каком году прозвучали «южные беседы» (南方谈话)?'}
P['modern-history-q72']={'fact':{'table':'events','options':[{'row':'ev-kailuo','column':'year'},{'row':'ev-qiqi','column':'year'},{'row':'ev-ru-ww2','column':'year'},{'row':'ev-ru-stalingrad','column':'year'},{'row':'ev-ru-yalta','column':'year'}],'answer':{'row':'ev-kailuo','column':'year'}},
 'questionRu':'В каком году прошла Каирская конференция, на которой обсуждали совместную войну против Японии?'}
LEAD_QING=['ev-humen','ev-taiping','ev-wuxu']
LEAD_C20=['ev-beifa','ev-nanchang','ev-xian','ev-kaiguo','ev-gaige','ev-nanxun']
P['modern-history-q60']={'exclude':LEAD_C20,
 'explanation':'Реформаторов во время «Ста дней реформ» (戊戌变法) возглавлял Кан Ювэй (康有为). Реформы начались 11 июня 1898 года императорским указом «Мин дин го ши» и продолжались 103 дня, до дворцового переворота 21 сентября. В том же году Кан Ювэй и Лян Цичао основали в Пекине общество реформаторов «Баогохуэй».'}
P['modern-history-q66']={'exclude':LEAD_QING}
P['modern-history-q67']={'exclude':LEAD_QING}
P['modern-history-q70']={'exclude':LEAD_QING,'questionRu':'Кто был главным организатором Сианьского инцидента 1936 года?'}
P['modern-history-q58']={'questionRu':'Какое движение проходило под девизом 自强、求富?'}
P['modern-history-q74']={'explanation':'Вансяский договор (望厦条约) Китай подписал с США (美国) 3 июля 1844 года в деревне Ванся близ Макао. С американской стороны его подписал посланник Калеб Кушинг. США получили все права, добытые по итогам опиумной войны, кроме земли и контрибуции.'}
P['modern-history-q75']={'questionRu':'Какой цинский сановник подписал в 1844 году Хуанпуский договор?',
 'explanation':'Хуанпуский договор (黄埔条约) подписали 24 октября 1844 года цинский сановник Ци Ин (耆英) и французский посланник Лагрене. Ци Ин был тогда генерал-губернатором Лянгуана (两广总督). Франция, увидев, какие привилегии получила Англия по итогам Первой опиумной войны, потребовала того же.'}
P['modern-history-q62']['explanation']='Война восьми держав (八国联军侵华战争) против Китая шла в 1900 году. Англия, США, Франция, Россия, Германия, Япония, Италия и Австро-Венгрия под предлогом защиты своих граждан и посольств сосредоточили у Дагу 77 кораблей, после чего их войска вошли в Пекин. Затем одиннадцать государств заставили цинское правительство подчиниться.'
P['modern-history-q78']={'explanation':'Симоносекский договор (马关条约) подписан 17 апреля 1895 года в японском городе Симоносеки Ли Хунчжаном и Ито Хиробуми. Договор завершил японо-китайскую войну. Цинское правительство уступило Японии Тайвань, острова Пэнху и Ляодунский полуостров и обязалось выплатить 200 млн лян серебра контрибуции.'}
P['modern-history-q79']={'questionRu':'После какой войны одиннадцать держав и цинское правительство подписали Заключительный протокол?'}
for k,v in P.items():
    q=by[k]
    for f,val in v.items():
        if f=='fact' and 'options' in val:
            q['fact']=val
        else:
            q[f]=val
json.dump(qs,open(D+'/modern-history-events.json','w'),ensure_ascii=False,indent=2)
json.dump(P,open(D+'/proposed.json','w'),ensure_ascii=False,indent=2)
print(len(P))
