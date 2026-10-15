import csv,re,sys
R='/Users/danielgnagi/gtazurich/research/'
osm=list(csv.DictReader(open(R+'pois_kreis3_osm.csv',encoding='utf-8')))
done={r['osm_id'] for r in csv.DictReader(open(R+'pois_kreis3.csv',encoding='utf-8'))}
SKIP=re.compile(r'kindergarten|childcare|school|playground|pitch|artwork|information|car_sharing|bicycle_rental|office=|architect|sports_centre|social_facility|kiosk|toilets|recycling|waste|bench|hospital|pharmacy|bank')
PRI=[('bahnhof wiedikon',0),('schmiede',1),('weststr',2),('idaplatz',3),('idastr',3),('zurlinden',4),('badenerstr',5),('gertrud',6),('birmensdorfer',7)]
def pri(r):
    a=(r['address']+' '+r['name']).lower()
    for k,p in PRI:
        if k in a: return p
    return 8
todo=[r for r in osm if r['osm_id'] not in done and not SKIP.search(r['kind'])]
todo.sort(key=lambda r:(pri(r), r['address'], r['name']))
n=int(sys.argv[1]) if len(sys.argv)>1 else 25
for r in todo[:n]:
    print('|'.join([r['osm_id'],r['name'],r['kind'],r['address'] or '-',r['website'] or '-']))
print(f'# remaining={len(todo)}',file=sys.stderr)
