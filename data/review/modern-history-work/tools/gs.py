import sys,re,pathlib
d=pathlib.Path(__file__).parent/'cache-fig-cn-2'
pat=sys.argv[1]; lim=int(sys.argv[3]) if len(sys.argv)>3 else 8
for f in sys.argv[2].split(','):
    t=(d/f'{f}.txt').read_text('utf-8')
    print('===',f)
    n=0
    for s in re.findall(r'[^。\n]*(?:'+pat+r')[^。\n]*[。\n]?',t):
        print('  ',s.strip()[:220]); n+=1
        if n>=lim: break
