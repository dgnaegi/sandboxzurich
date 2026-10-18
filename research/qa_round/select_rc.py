# Selects reference-photo/game-position pairs for the reality check. Output: research/qa_round/rc_shots.json
import json,math,collections,numpy as np,sys
C=np.array([[-1527.6227055560475,111173.30935718861],[75502.4568037623,1031.9047813145494],[-570641.6500799963,-5276635.687803476]])
def loc(lat,lon): return (np.array([lat,lon,1])@C).tolist()
stops=json.load(open('research/qa_round/_stops.json'))
photos=json.load(open('research/fidelity_photos_local.json'))
photos=[p for p in photos if p.get('heading') is not None]
# street polylines
els=json.load(open('data/raw/osm/part_highway_r.json'))['elements']
nodes={e['id']:loc(e['lat'],e['lon']) for e in els if e['type']=='node'}
NAMES=['Hardstrasse','Hohlstrasse','Badenerstrasse','Seebahnstrasse','Militärstrasse','Feldstrasse','Bullingerstrasse','Pfingstweidstrasse','Europaallee','Zurlindenstrasse','Langstrasse','Weststrasse','Birmensdorferstrasse','Hardturmstrasse','Querstrasse','Kanzleistrasse','Magnusstrasse','Ankerstrasse','Stauffacherstrasse','Sihlfeldstrasse','Gertrudstrasse','Eisgasse','Josefstrasse','Gasometerstrasse','Heinrichstrasse']
ways=collections.defaultdict(list)
for e in els:
    if e['type']=='way' and e.get('tags',{}).get('name') in NAMES and 'highway' in e['tags']:
        ways[e['tags']['name']].append([nodes[n] for n in e['nodes'] if n in nodes])
def dseg(p,a,b):
    ax,ay=a;bx,by=b;px,py=p;dx,dy=bx-ax,by-ay;L=dx*dx+dy*dy
    t=0 if L==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L));return math.hypot(px-ax-t*dx,py-ay-t*dy)
def dstreet(p,name): return min((dseg(p,w[i],w[i+1]) for w in ways[name] for i in range(len(w)-1)),default=1e9)
EXC=['Lochergut','Helvetiaplatz','Bäckeranlage','Limmatplatz','Escher-Wyss-Platz','Albisriederplatz','Schmiede Wiedikon','Lindenplatz','Zürich Hauptbahnhof','Bahnhofplatz/HB','Bahnhofquai/HB','Bahnhofstrasse/HB','Sihlpost/HB','Kalkbreite/Bhf. Wiedikon','Röntgenstrasse','Hardplatz']
exc=[stops[n] for n in EXC if n in stops]
exc+=[[1,-900]] # placeholder none
def excluded(p): return any(math.hypot(p['x']-e[0],p['y']-e[1])<110 for e in exc)
STOPS=['Stauffacher','Bahnhof Wiedikon','Zürich Wiedikon','Goldbrunnenplatz','Letzigrund','Hardturm','Toni-Areal','Schiffbau','Bahnhof Altstetten','Bahnhof Hardbrücke','Güterbahnhof','Werd','Kanonengasse','Militär-/Langstrasse','Löwenbräu','Technopark','Museum für Gestaltung','Friedhof Sihlfeld','Altes Krematorium','Zypressenstrasse','Gutstrasse','Bertastrasse','Zwinglihaus','Aargauerstrasse','Bernoulli-Häuser','Bezirksgebäude','Kernstrasse','Wipkingerplatz','Zürich Selnau','Löwenplatz','Albisrank','Manesseplatz','Letzipark','Siemens','Hubertus','Kappeli','Freihofstrasse','Herdernstrasse','Förrlibuckstrasse','Lettenstrasse','Quellenstrasse','Rosengartenstrasse','Zürich Landesmuseum','Kronenstrasse','Sportweg','Bahnhof Selnau','Heuried','Zürich Binz','Bahnhof Wipkingen','Zürich Altstetten','Hertersteg']
out=[];used=set()
def cand(f):
    return sorted([p for p in photos if not excluded(p) and f(p)[0]],key=lambda p:f(p)[1])
for n in STOPS:
    if n not in stops: continue
    s=stops[n]
    c=cand(lambda p:(math.hypot(p['x']-s[0],p['y']-s[1])<60,math.hypot(p['x']-s[0],p['y']-s[1])))
    c=[p for p in c if p['file'] not in used][:2]
    for p in c: used.add(p['file'])
    out.append(dict(place=n,kind='stop',cx=s[0],cy=s[1],photos=c))
for n in NAMES:
    if not ways[n]: continue
    c=[p for p in photos if not excluded(p) and dstreet((p['x'],p['y']),n)<9 and p['file'] not in used]
    sel=[]
    for p in c:
        if all(math.hypot(p['x']-q['x'],p['y']-q['y'])>350 for q in sel): sel.append(p)
    for k,p in enumerate(sel[:3]):
        used.add(p['file']);out.append(dict(place=f'{n} #{k+1}',kind='street',cx=p['x'],cy=p['y'],photos=[p]))
json.dump(out,open('research/qa_round/rc_sel.json','w'),ensure_ascii=False,indent=0)
print(len(out));
for o in out: print(o['place'],len(o['photos']),[(round(p['x']),round(p['y']),p['heading']) for p in o['photos']][:1])
