import json,sys
sys.path.insert(0,'.')
from places_def import PLACES
from notes import N
R='/Users/danielgnagi/sandboxzurich/research/places_k45'
ph=json.load(open(R+'/places_photos.json')); ce=json.load(open('centers.json'))
K={"char":"Charakter","landmarks":"Landmarks (Sichtbefunde)","facades":"Fassadenfarben/-stile","ground":"Bodenbelaege","furniture":"Stadtmobiliar","oev":"OeV","green":"Gruen","shops":"Laeden/Bars (Fakten)","atmo":"Atmosphaere"}
out=[]
for slug,(name,kr,la,lo,rad,qs) in PLACES.items():
    n=N[slug]; cx,cy=ce[slug]
    L=[f"# {name} (Kreis {kr})",f"Lage: WGS84 {la},{lo}; lokal x={cx} y={cy} (m, Radius der Analyse {rad} m). Vorschau-Kontaktbogen: preview/ref_k45_{slug}.jpg, Fotos: data/raw/photos/places_k45/{slug}/NN.jpg",
       "Hinweis: Tramlinien/Namen mit '?' unverifiziert; Hoehen aus OSM/Web; Farben aus Sicht (Naeherung).",""]
    for k,t in K.items(): L+= [f"## {t}",n[k],""]
    L+=["## OSM/Denkmalinventar (Skript-Auszug, lokale Meter)",'```',open(f'osm_{slug}.txt').read().strip(),'```',"","## Fotos"]
    for i,r in enumerate(ph.get(slug,[]),1): L.append(f"{i:02d}. {r['commons_title']} | {r['author'][:40]} | {r['license']} | {r['page']}")
    open(f'{R}/{slug}.md','w').write("\n".join(L)+"\n")
    out.append({"slug":slug,"name":name,"kreis":kr,"lat":la,"lon":lo,"local_x":cx,"local_y":cy,"radius_m":rad,"doc":f"research/places_k45/{slug}.md","contact_sheet":f"preview/ref_k45_{slug}.jpg","photos":ph.get(slug,[])})
json.dump({"generated":"2026-10-15","sources":["Wikimedia Commons (licenses per photo)","OSM (ODbL)","Stadt Zuerich Denkmalinventar","Wikipedia/Web (KVA, Kalkbreite)"],"places":out},open(R+'/places.json','w'),ensure_ascii=False,indent=1)
print(len(out))
