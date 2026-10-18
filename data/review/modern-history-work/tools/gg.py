import re,sys,os
pat=re.compile(sys.argv[1]); n=int(os.environ.get('N','5'))
base=os.path.join(os.path.dirname(os.path.abspath(__file__)),'cache-fig-cn-1')
for f in sys.argv[2:]:
    print('###',f)
    t=open(f'{base}/{f}.txt',encoding='utf-8').read()
    for i,m in enumerate(pat.finditer(t)):
        if i>=n: break
        print('  ',t[max(0,m.start()-40):m.end()+50].replace('\n',' '))
