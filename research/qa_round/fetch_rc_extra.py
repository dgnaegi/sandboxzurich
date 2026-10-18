# Panoramax reference photos for places that had none in the local cache. Output: rc_extra.json (same schema as rc_shots.json)
import json,requests,numpy as np,math,time,os
C=np.array([[-1527.6227055560475,111173.30935718861],[75502.4568037623,1031.9047813145494],[-570641.6500799963,-5276635.687803476]])
def loc(lat,lon): return (np.array([lat,lon,1])@C).tolist()
A=C[:2].T; b0=C[2]
def inv(x,y): return np.linalg.solve(A,np.array([x,y])-b0).tolist()
stops=json.load(open('research/qa_round/_stops.json'))
P={'Stauffacher':stops['Stauffacher'],'Bahnhof Wiedikon':stops['Bahnhof Wiedikon'],'Goldbrunnenplatz':stops['Goldbrunnenplatz'],'Letzigrund':stops['Letzigrund'],
'Schiffbau':stops['Schiffbau'],'Werd (Werdplatz)':stops['Werd'],'Kanonengasse (Kasernenareal)':stops['Kanonengasse'],'Friedhof Sihlfeld':stops['Friedhof Sihlfeld'],
'Museum fuer Gestaltung (Toni/Pfingstweid)':stops['Museum für Gestaltung'],'Zuerich Selnau':stops['Zürich Selnau'],'Albisrank':stops['Albisrank'],'Wipkingerplatz':stops['Wipkingerplatz'],'Siemens (Albisriederstr.)':stops['Siemens'],'Kappeli':stops['Kappeli'],'Letzipark':stops['Letzipark'],'Hubertus':stops['Hubertus']}
out=[];H={'User-Agent':'sandboxzurich/0.1 (research)'}
for name,(x,y) in P.items():
    lat,lon=inv(x,y);d=0.0005
    try:
        r=requests.get('https://api.panoramax.xyz/api/search',params={'bbox':f'{lon-d*1.5},{lat-d},{lon+d*1.5},{lat+d}','limit':40},headers=H,timeout=40).json()
    except Exception as e: print(name,'err',e);continue
    best=None
    for f in r.get('features',[]):
        pr=f['properties'];lo,la=f['geometry']['coordinates'];az=pr.get('view:azimuth')
        if az is None or pr.get('pers:fov') is None and False: continue
        if pr.get('geovisio:status','ready')!='ready': continue
        dm=math.hypot(*[a-b for a,b in zip(loc(la,lo),(x,y))])
        dt=pr.get('datetime','')[:4]
        sc=dm+(0 if dt>='2022' else 40)
        if best is None or sc<best[0]: best=(sc,f,loc(la,lo),az)
    if not best: print(name,'none');continue
    _,f,(px,py),az=best
    url=f['assets'].get('sd',f['assets'].get('hd'))['href']
    fn=f"data/raw/photos/rc/{f['id']}.jpg"
    if not os.path.exists(fn):
        open(fn,'wb').write(requests.get(url,headers=H,timeout=60).content);time.sleep(0.5)
    pr=f['properties']
    out.append(dict(place=name,x=round(px,1),y=round(py,1),hdg=az,file=fn,author=(f.get('providers') or [{}])[0].get('name',''),license=pr.get('license','CC-BY-SA-4.0'),url='https://panoramax.openstreetmap.fr/#focus=pic&pic='+f['id'],source='panoramax',dt=pr.get('datetime','')[:10]))
    print(name,round(px),round(py),az,pr.get('datetime','')[:10])
json.dump(out,open('research/qa_round/rc_extra.json','w'),ensure_ascii=False,indent=0)
