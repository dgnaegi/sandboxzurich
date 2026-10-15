import csv, re, sys
from difflib import SequenceMatcher
R='/Users/danielgnagi/sandboxzurich/research/'
GASTRO={'restaurant','bar','cafe','fast_food','pub','biergarten','nightclub','ice_cream'}
STOP=re.compile(r'\b(bar|restaurant|ristorante|pizzeria|cafe|café|kiosk|club|lounge|bistro)\b')
def norm(s): return re.sub(r'[^a-z0-9]','',STOP.sub('',(s or '').lower().replace('ü','u').replace('ö','o').replace('ä','a').replace('é','e')))
def street(s):
    m=re.match(r'\s*([^\d,]+?)\s*(\d+)',s or '')
    return (m.group(1).strip().lower(), m.group(2)) if m else None
done=set()
with open(R+'pois_kreis4.csv',newline='',encoding='utf-8') as f:
    for r in csv.DictReader(f): done.add(r['osm_id'])
gast=[]
with open(R+'gastro_match.csv',newline='',encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['result']=='matched': gast.append(r)
pois=[]
with open(R+'pois_kreis4_osm.csv',newline='',encoding='utf-8') as f:
    for r in csv.DictReader(f):
        x=float(r['x']); y=float(r['y'])
        if not (600<=x<=1200 and -1000<=y<=-400): continue
        if r['osm_id'] in done: continue
        kind=r['kind'] or ''
        if kind.split('=')[-1] not in GASTRO: continue
        pois.append(r)
accept=[]
for p in pois:
    best=None
    for g in gast:
        s=max(SequenceMatcher(None,norm(p['name']),norm(g['name'])).ratio(),
               SequenceMatcher(None,norm(p['name']),norm(g['osm_name'])).ratio())
        a=street(p['address']); ga=street(g['address'])
        addr = a and ga and a[1]==ga[1] and (a[0][:6]==ga[0][:6])
        score = s+(0.2 if addr else 0)
        if best is None or score>best[0]: best=(score,s,addr,g)
    if best and (best[1]>=0.85 or (best[2] and best[1]>=0.5)):
        accept.append((p,best[3]))
    elif best and best[0]>=0.6:
        print('REVIEW',p['osm_id'],p['name'],'|',best[3]['name'],round(best[1],2),file=sys.stderr)
for p,g in accept:
    print(f"{p['osm_id']}|ok||{g['address']}, Zürich|Stadt Zürich OGD Gastwirtschaftsbetriebe 2025")
print('gastro candidates',len(pois),'accepted',len(accept),file=sys.stderr)
