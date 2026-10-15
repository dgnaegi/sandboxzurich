import csv, subprocess, re
R='/Users/danielgnagi/gtazurich/research/'
ok_map = {
 'n13540274646':('ok','','Zwinglistrasse 35, 8004 Zürich','https://katrahama.ch/'),
 'n13725108955':('ok','','Müllerstrasse 70, 8004 Zürich','https://gds.fm'),
 'n9992397570':('renamed','Navique AG','Europaallee 41, 8021 Zürich','https://www.navique.com/'),
 'n1391309505':('ok','','Stauffacherstrasse 54, 8004 Zürich','https://zuerich-4.emk-schweiz.ch/'),
 'n11894473301':('ok','','Stauffacherstrasse 60, 8004 Zürich','https://www.stadtbadzuerich.ch/'),
 'n3479479308':('ok','','Stauffacherstrasse 60, 8004 Zürich','https://www.stadtbadzuerich.ch/'),
 'n656516103':('ok','','Stauffacherstrasse 60, 8004 Zürich','https://www.restaurantvolkshaus.ch/'),
 'n5297598012':('ok','','Zeughausstrasse 60, 8004 Zürich','https://www.archezuerich.ch/arche-fuer-familien'),
 'n8704527465':('ok','','Dienerstrasse 76, Zürich','https://xn--wohnen-zrich-klb.heilsarmee.ch/'),
 'n8704527466':('ok','','Magnusstrasse 14, Zürich','https://xn--wohnen-zrich-klb.heilsarmee.ch/'),
 'n10900421299':('ok','','Molkenstrasse 6, 8004 Zürich','https://meinplatz.ch/de/standorte/wohnheim-molkenstrasse-6'),
 'n12160488708':('ok','','Müllerstrasse 71, 8004 Zürich','https://incontro-verein.ch/unsere-arbeit/'),
 'n425288506':('ok','','Stauffacherstrasse 96, 8004 Zürich','https://www.prenataldiagnostics.ch'),
 'n11844509219':('ok','','Kanonengasse 18a, 8004 Zürich','https://nadiagraf.com'),
 'n9893260545':('ok','','Kanonengasse 7, 8004 Zürich','https://zuri.net/de/zurich/burger-steaks/huncho-19105.htm'),
 'n311607525':('ok','','Stauffacherstrasse 96, 8004 Zürich','https://zuri.net/de/zurich/all-restaurants/casa-helvetia-25871.htm'),
 'n8203162120':('moved','','Konradstrasse 62, 8005 Zürich (Pfarrer-Sieber-Huus)','https://www.swsieber.ch/was-wir-tun/auffangen/gassencafe/'),
 'w1343977835':('ok','','Kasernenareal, 8004 Zürich','https://www.zh.ch/de/news-uebersicht/medienmitteilungen/2020/01/weiterentwicklung-kasernenareal-zuerich.html'),
 'w4533222':('ok','','Kasernenwiese, 8004 Zürich','https://www.zh.ch/de/news-uebersicht/medienmitteilungen/2020/01/weiterentwicklung-kasernenareal-zuerich.html'),
 'w28943682':('ok','','Kasernenwiese, 8004 Zürich','https://www.zh.ch/de/news-uebersicht/medienmitteilungen/2020/01/weiterentwicklung-kasernenareal-zuerich.html'),
}
unc = {
 'n11216071012':('Rotwandstrasse 53, 8004 Zürich (nur Footer der Website; Shop nicht bestätigt)','https://andreahinnen.com'),
 'n13952161540':('Badenerstrasse 329, 8040 Zürich (Hauptsitz laut Website, nicht Standort)','https://baumann-koelliker-gruppe.ch/'),
 'n12133693607':('','https://www.ufc.ch/de/locations/store/429/corner-services-zrich (404)'),
 'n9255553977':('Zertifikat der Website abgelaufen, Adresse nicht prüfbar','https://www.wolfstudio.ch/'),
 'n8194922105':('Europaallee 39 (OSM), auf Website keine Adresse','https://www.leonteq.com/'),
 'w121597493':('','https://www.labyrinthplatz.ch/ (keine Adresse auf Seite)'),
 'n1360776653':('Saisonbetrieb laut Website (Winterpause bis 1.5.2027), Adresse fehlt','https://www.summergarte.ch/'),
 'n920508503':('Talstrasse 66, 8001 Zürich (Kind of a Hotel; Swiss-Star-Standort nicht bestätigt)','https://swiss-star.com/'),
 'n4749159173':('Militärstrasse 76 (OSM), Website nennt nur Kreis 4','https://www.kanonengasse.ch/'),
 'n11216071023':('','https://velvetglam.ch (Domain nicht erreichbar)'),
 'n6592084080':('Adresse auf Website nicht genannt','https://gbanga.com'),
 'n10691351556':('Molkenstrasse 22 (OSM), Store-Seite nicht abrufbar','https://deuscustoms.eu/blogs/blog/store-deus-zurich (404)'),
 'n4869996382':('Website nennt nur Personenmeldeamt Süd (Stadthaus)','https://www.stadt-zuerich.ch/services-pma'),
 'n12160511961':('Adresse auf Website nicht genannt (Öffnung Fr 9-15 Uhr)','https://netz4.ch/imbiss54-2/'),
 'n1449647894':('','https://www.stadt-zuerich.ch/sd/de/index/unterstuetzung/drogen/kontaktundanlaufstellen.html (404)'),
 'w73306059':('Feldstrasse 136 (OSM), nicht auf Stadtseite bestätigt','https://www.stadt-zuerich.ch/sd/de/index/erschliessung/izs/wohnen/notunterkuenfte.html (keine Treffer)'),
 'w28943550':('Kasernenstrasse 29 (OSM), nicht bestätigt','https://www.stadt-zuerich.ch/sd/de/index/erschliessung/izs/wohnen/notunterkuenfte.html (keine Treffer)'),
 'n10877414546':('Lagerstrasse 32 (OSM); Websuche nennt Salon Saleh in Kreis 1, Adresse nicht bestätigt','Websuche Coiffeur Saleh Lagerstrasse 32 (Treatwell)'),
 'n12138506371':('','Websuche ohne Treffer'),
 'n5282153478':('Militärstrasse 85 (OSM); Websuche nur Coiffeur Rosy an Militärstrasse 76, Manu nicht gefunden','Websuche Coiffeur Militärstrasse Zürich'),
 'n10889806815':('','Websuche Nagelstudio Langstrasse: kein Treffer'),
 'n12512257502':('','Websuche Blumenkohlektiv: kein Treffer'),
 'n10596153317':('Dienerstrasse 68 (OSM); Websuche ohne Treffer','Websuche Caipi Bar Dienerstrasse 68'),
 'n1241219989':('Dienerstrasse 28 (OSM); Websuche ohne Treffer','Websuche Thai Tirak Dienerstrasse 28'),
 'n869269170':('','Websuche: nur Wanderlog "4You", keine Adresse'),
 'n11216071007':('Kanonengasse (OSM, Nr. fehlt); Websuche ohne Treffer','Websuche Barista Coffee Roasters Zürich'),
 'n1240990728':('Tellstrasse 10 (OSM); Imbiss Oder Wat laut zuri.net an Hohlstrasse 49','https://zuri.net/de/zurich/alle-take-aways/oder-wat-imbiss-24296.htm'),
 'n4424003112':('Rolandstrasse 9, 8004 Zürich (Listing); eine Quelle sagt temporär geschlossen','Websuche Now We Go Vegan Rolandstrasse 9'),
 'n5976303007':('Zwinglistrasse 3 (OSM); Websuche nicht gefunden, Gaijin Izakaya an anderer Adresse','Websuche Tsukada Gaijin Izakaya'),
 'n11216070999':('','')
}
done=set()
with open(R+'pois_kreis4.csv',newline='',encoding='utf-8') as f:
    for r in csv.DictReader(f): done.add(r['osm_id'])
rows=[]
with open(R+'pois_kreis4_osm.csv',newline='',encoding='utf-8') as f:
    for r in csv.DictReader(f):
        x=float(r['x']); y=float(r['y'])
        if not (600<=x<=1200 and -1000<=y<=-400): continue
        if r['osm_id'] in done: continue
        if re.search(r'kita|kindergarten|childcare|schul|school|hort', (r['name'] or '')+(r['kind'] or ''), re.I): continue
        oid=r['osm_id']
        if oid in ok_map:
            st,new,addr,src=ok_map[oid]
        elif oid in unc:
            addr,src=unc[oid]; st='unclear'; new=''
            if not addr: addr=r['address'] or ''
        else:
            st='unclear'; new=''; addr=r['address'] or ''
            src='Websuche/WebFetch ohne Treffer (Budget-Lauf 7)'
            if r['website']: src=r['website']+' (nicht verifiziert)'
        rows.append(f"{oid}|{st}|{new}|{addr}|{src}")
print('\n'.join(rows))
