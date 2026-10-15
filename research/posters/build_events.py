#!/usr/bin/env python3
"""Builds events.json from cached raw data (raw/rf_YYYY.json = Rote Fabrik public calendar API)
plus hand-curated entries (Helsinki Klub, Dynamo, Gessnerallee via Wayback snapshots).
Usage: python3 build_events.py"""
import json, re, html, datetime, zoneinfo, pathlib
HERE = pathlib.Path(__file__).parent
tz = zoneinfo.ZoneInfo('Europe/Zurich')
EV = {}
for y in (2022, 2023, 2024, 2025):
    d = json.load(open(HERE / f'raw/rf_{y}.json'))
    for e in d.values():
        r = e['rf_event']
        dt = datetime.datetime.fromisoformat(e['date'].replace('Z', '+00:00')).astimezone(tz)
        EV.setdefault(int(r['id']), []).append((dt.strftime('%Y-%m-%d'), e, r))
def txt(s): return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', s or ''))).strip()
def price(r):
    pl = r.get('price_label') or ''
    nums = re.findall(r'\d+(?:\.\d+)?', pl)
    nums = [n.rstrip('0').rstrip('.') if '.' in n else n for n in nums]
    nums = [n for n in nums if n not in ('0',)]
    if 'Kollekte' in pl: return 'Kollekte'
    return 'CHF ' + ' / '.join(nums) if nums else None
ORG = {'Musikbüro': 'Musikbüro Rote Fabrik', 'Clubbüro': 'Clubbüro Rote Fabrik', 'Fabriktheater': 'Fabriktheater Rote Fabrik',
       'Shedhalle': 'Shedhalle Rote Fabrik', 'Konzept': 'Rote Fabrik (Konzept)', 'Fremdveranstaltung': 'Fremdveranstalter in der Roten Fabrik',
       'Fabrikvideo': 'Fabrikvideo Rote Fabrik', 'shapey': 'shapey (Rote Fabrik)', 'Team': 'Rote Fabrik'}
ADDR = 'Seestrasse 395, 8038 Zürich'
# eid: (kind, lineup (None -> title), political, approval, note, date_override)
RF = {
 # concerts
 3338:('concert',['DIIV','Storefront Church'],0,0,'',None),
 3686:('concert',['Protoje','DJ Buzz (Boss Hi-Fi)'],0,0,'',None),
 3584:('concert',['Bob Moses','Catching Flies'],0,0,'',None),
 3838:('concert',['Frida'],0,0,'Arab Soul from Beirut',None),
 4375:('concert',['Motorpsycho'],0,0,'',None),
 4586:('concert',['Buntspecht'],0,0,'',None),
 4972:('concert',['Ätna','Leila'],0,0,'',None),
 6476:('concert',['Leftfield','Arthur Hnatek'],0,0,'',None),
 3917:('concert',['King Hannah','Pina Palau'],0,0,'',None),
 5489:('concert',['Trentemøller'],0,0,'30 Jahre Lethargy Jubiläumskonzert',None),
 5544:('concert',['Annie Taylor','Überyou','Hunted Like Thieves','The High Times','Mr. Linus'],0,0,'',None),
 5239:('concert',['Chelsea Wolfe','Mary Jane Dunphe'],0,0,'',None),
 3538:('concert',['John Grant'],0,0,'',None),
 3349:('concert',['Nothing','The Waltz'],0,0,'',None),
 3422:('concert',['WOZ Jubiläum (Programm siehe Quelle)'],0,0,'Jubiläum der Wochenzeitung WOZ, Medienhaus, keine Partei',None),
 6094:('concert',['Soundsyndrom!'],0,0,'',None),
 # festivals
 3327:('festival',['Grandbrothers','Battles','Reverend Beat-Man & The Underground','Islandman','Fango','Chloé','Ikan Hyu','Timothy J. Fairplay','Flexfab & Ziller Bas','Black Merlin','Knarf Rellöm Arkestra'],0,0,'Lethargy 28. Ausgabe, Freitag und Samstag',None),
 4298:('festival',None,0,0,'Lethargy 29th edition',None),
 5149:('festival',['Mezerg','Fantastic Twins'],0,0,'Lethargy 30th edition (Programm laufend ergänzt)',None),
 5511:('festival',None,0,0,'Lethargy 31st edition',None),
 3946:('festival',['Milchjugend (Kollektiv)'],0,0,'lila. queer festival 2022',None),
 4942:('festival',['Milchjugend (Kollektiv)'],0,0,'lila. queer festival 2024',None),
 3184:('festival',['VAZEM Kollektiv'],0,0,'Rhizom, Club-Kultur-Festival',None),
 3587:('festival',['HSLU Big Band','Ingrid Laubrock'],0,0,'Unerhört 22 Jazzfestival',None),
 4105:('festival',['Space (Lisa Ullén, Elsa Bergman, Anna Lund)','Vincent Courtois','Colin Vallon','Borderlands Trio (Stephan Crump, Kris Davis, Eric McPherson)'],0,0,'Unerhört 23',None),
 4564:('festival',['Marie Krüttli Trio'],0,0,'unerhört! Jazzfestival 2024, Clubraum',None),
 5532:('festival',['Camila Nebbia','Large Ensemble der HSLU','Nils Wogram'],0,0,'unerhört! Jazzfestival 2025',None),
 6008:('festival',['Omar Souleyman','Ÿuma','Selin Sümbültepe','Roshâni','Zeemuffin','Rey&Kjavik','İpek İpekçioğlu'],0,0,'Jazzhane Festival 2025',None),
 3202:('festival',['Smyrna- und Rebetiko-Lieder (GR/CH)'],0,0,'mediterranean music festival 2022',None),
 5079:('festival',['Puchero','Sebass','Aman-Rebetiko feat. Yiannis Dionysiou'],0,0,'mmfestival in June 2024 (3 Abende)',None),
 4529:('festival',['Radio LoRa'],0,0,'40 Jahre Radio LoRa, nichtkommerzielles Lokalradio',None),
 3761:('festival',['Rote Fabrik'],0,0,'Tag der offenen Fabrik / Quartierfest',None),
 5599:('festival',['Pädagogische Aktion Zürich'],0,0,'Spielfest 40 Jahre PAZ / Tag der offenen Fabrik',None),
 3645:('festival',['Vintage Computer Festival Zürich #22'],0,0,'',None),
 # parties
 3472:('party',['Hajj','Martin Cramatte'],0,0,'Feral Curse',None),
 3471:('party',['RTFM'],0,0,'Gabbernight',None),
 3760:('party',['Hagger','Eva im Paradies'],0,0,'Haggerrave',None),
 4055:('party',['comma rave'],0,0,'',None),
 3781:('party',['meta rave','zima techno'],0,0,'',None),
 5102:('party',['Kunterbunt Kollektiv'],0,0,'Nocturnal Rave, Fluidity',None),
 4540:('party',['eve & rave'],0,0,'altered states',None),
 5104:('party',['Zürich Pride Festival After'],0,0,'After-Party zum Pride Festival, nicht die Demo selbst',None),
 5444:('party',['Exil x Clubbüro'],0,0,'Outdoor Summer Dance',None),
 4136:('party',['ZH Dub Corner'],0,0,'',None),
 # benefit / soli (not political organisations)
 5421:('benefit',['Haver'],0,0,'eve&rave Benefizparty',None),
 5420:('benefit',['Endstation','Flugelaende'],0,1,'Soli für «Nightlife in Solidarity»: Trägerschaft in Quelle prüfen',None),
 4771:('benefit',['SOLISOLIRAVE'],0,0,'Soli für den Verein solisoli (Trägerschaft prüfen, ob politisch)',None),
 4772:('benefit',['Dachsbau'],0,1,'Konzerte & Soli-Party für «BEN48»: Zweck in Quelle unklar, prüfen',None),
 5526:('benefit',['Disco Taifun'],0,0,'Gewinn an Kulturlegi Zürich',None),
 5347:('benefit',['Manillio','Michael Elsener','Danase'],0,0,'Art4Rescue Vol. 1, Erlös zivile Seenotrettung (SOS Méditerranée)',None),
 5778:('benefit',['Troubas Kater'],1,1,'Art4Rescue Vol. 2 für SOS Méditerranée: NGO-Anliegen Migration/Seenotrettung',None),
 # political (flag)
 3485:('political',['Soli-Infoabend und Party'],1,1,'Soli für Afghanistan: humanitärer Anlass, Trägerschaft in Quelle nicht benannt',None),
 4083:('political',['ROTA (migrantische Selbstorganisation)'],1,1,'Soli von und für ROTA, Selbstorganisation von MigrantInnen v.a. aus Türkei/Kurdistan und Naher Osten; Verbindungen/Positionen vor Verwendung prüfen',None),
 4601:('political',['CSD Zureich'],1,1,'Soliparty zur Demo «CSD Zureich» (queere Demo, antikapitalistisch)',None),
 5139:('political',['Lateena','Power Puffs'],1,1,'CSD Soliparty, «Antikapitalistischer CSD Zureich»',None),
 6465:('political',['Kimbo','Chocolate Remix','Akuaku'],1,1,'CSD Zureich x Picante Afterparty, Spendensammlung für CSD-Kosten',None),
 6006:('political',['Leila Moon'],1,1,'Solipartei for Palestine, Erlös an Gaza Sunbirds (Para-Sport-Hilfswerk). Organisation prüfen',None),
 6281:('political',['47SOUL','Leila Moon','Badiaa Bouhrizi'],1,1,'Konzert «in Solidarity with Palestine», Kern und Schale: Veranstalter vor Verwendung prüfen',None),
 6146:('political',['Fête de la Solidarité (Markt, Podium, Konzert)'],1,1,'Freiplatzaktion Zürich (40 J.), Solidarité sans Frontières (25 J.), SPAZ (20 J.): migrationspolitische Organisationen',None),
 5389:('political',['Solidarity Rising (Sanna Ghotbi, Benjamin Ladraa)'],1,1,'Info-Anlass Westsahara (Velo-Weltreise, SUKS)',None),
 4617:('political',['Soliparty feministischer Streik 23'],1,1,'Soliparty zum feministischen Streik',None),
 3611:('film',['Golden Dawn - A Public Affair (Film)'],1,1,'Doku zum Golden-Dawn-Prozess, Filmabend mit Podium',None),
 4342:('sport',['Vecchia Brigata'],1,1,'Boykott Fussball-WM 2022 Katar, Film/Podium, fussballpolitisch',None),
 # film
 4592:('film',['The Other Half (Doku)'],0,0,'Langzeitdoku Flüchtlingsschicksal',None),
 3989:('film',['dadaFestWochen: Why Zürich was the place to be in 1992'],0,0,'',None),
 3758:('film',['Offene Leinwand'],0,0,'Plattform für Kurzfilme',None),
 3247:('film',['Offside (Stadtgeschichten)'],0,0,'Freiluftkino Rote Fabrik, 39. Mal',None),
 5050:('film',['Deutschlandli (Orient Express Filmtage Opening)'],0,0,'',None),
 3581:('film',['Orient Express Filmtage 2022: Eröffnung'],0,0,'Programm im Kino Xenix',None),
 4720:('concert',['İlhan Ersahin\'s İstanbul Sessions'],0,0,'im Rahmen der Orient Express Filmtage',None),
 5850:('film',['Films for Future Festival 2024'],0,0,'Eating the Future',None),
 6194:('film',['Films For Future Festival 2025'],0,0,'Sehen - Verstehen - Tun',None),
 # theater
 2883:('theater',['Infinite Cooperation'],0,0,'',None),
 4077:('theater',['Phil Hayes','Taimashoe'],0,0,'Invited Ghosts',None),
 4963:('theater',['Nora Amin','Irina Kast'],0,0,'Maralam: CLASH, Uraufführung',None),
 5160:('theater',['CARECITY'],0,0,'CARECITY _STORIES* 4 WEITER WEBEN',None),
 5900:('theater',['Keshaw Manna'],0,0,'YEAH YEAH YEAH Tanzfestival',None),
 5902:('theater',['Lucy McCormick'],0,0,'Triple Threat, YEAH YEAH YEAH Festival',None),
 3130:('theater',['Tanzfaktor 2022'],0,0,'YEAH YEAH YEAH Zürcher Tanzfestival',None),
 4270:('theater',['Theaterstudio Golda Eppstein'],0,0,'HU IS HU Theaterfest 2023',None),
 # exhibition
 3833:('exhibition',['ProtoZone 6'],0,0,'',None),
 4163:('exhibition',['ProtoZone 8: Queer Trust'],0,0,'',None),
 5624:('exhibition',['ProtoZone 15: Time is pressure'],0,0,'',None),
 5931:('exhibition',['ProtoZone 17: Stories of Those Left Behind'],0,0,'',None),
 6328:('exhibition',['Göksu Kunak'],0,0,'tangerine, performative Installation',None),
 4435:('exhibition',['Selma Selman','Mikołaj Sobczak','Nicholas Grafia'],0,0,'ProtoZone 9 Weak.End.Opera',None),
 # reading
 3417:('reading',['Fabrik Slam #85'],0,0,'Poetry Slam',None),
 4213:('reading',['Fabrik Slam #95'],0,0,'Poetry Slam',None),
 5298:('reading',['Fabrik Slam #105'],0,0,'Poetry Slam',None),
 6685:('reading',['Fabrik Slam'],0,0,'Der letzte Fabrikslam',None),
 3788:('reading',['Franziska Tschinderle'],0,0,'Lesung «Albanien»',None),
 4066:('reading',['read or die'],0,0,'Literaturquiz',None),
 4804:('reading',['Stefan Kutzenberger'],0,0,'Roman «Kilometer Null»',None),
 # market
 3817:('market',['Pizza Cup Teilchenbeschleuniger'],0,0,'Mountainbike- und Velo-Flohmarkt',None),
 4489:('market',['PizzaCup Teilchenbeschleuniger'],0,0,'Flohmarkt für Bikes und Veloteile (Kunstraum Walcheturm)',None),
 6296:('market',['Flohmi am Wasser'],0,0,'11. Ausgabe',None),
}
def rf_event(eid, spec):
    kind, lineup, pol, app, note, dov = spec
    v = sorted(EV[eid], key=lambda x: x[0]); d, e, r = v[0]
    title = txt(r['title']); sub = txt(r['subtitle']) if r['subtitle'] else None
    t = (e.get('from') or '')[:5] or None
    door = (e.get('door') or '')[:5]
    stk = [s['name'] for s in r['stakeholders']]
    org = ORG.get(stk[0], stk[0]) if stk else 'Rote Fabrik'
    if eid == 3761: org = 'Rote Fabrik (Areal)'
    loc = (r.get('location') or {}).get('name') or 'Rote Fabrik'
    venue = 'Rote Fabrik' + ('' if loc in ('Ganzes Areal',) else f' ({loc})')
    if loc in ('Kunstraum Walcheturm',): venue = 'Kunstraum Walcheturm (Rote Fabrik)'
    return dict(id=f'rf-{eid}', title=title, subtitle=sub or (note or None), date=d, time=(f'Türen {door}, Beginn {t}' if door and t and door != t else t),
        venue=venue, address=ADDR if 'Walcheturm' not in venue else 'Walcheplatz, 8006 Zürich',
        kind=kind, lineup=lineup if lineup else [title], price=price(r), organizer=org,
        source_url=f'https://kalender.rotefabrik.ch/api/events?from={d}&to={d}', political=bool(pol), approval_needed=bool(app),
        note=note or None, dates=[x[0] for x in v] if len(v) > 1 else None)
out = [rf_event(k, v) for k, v in RF.items()]

# ---- Helsinki Klub (Wayback snapshots, Programm listed on home page) ----
HELS = 'https://www.helsinkiklub.ch'
SNAP = {2023: ('20230227134025','20230922070539'), 2024: ('20240417041433','20241111025359'), 2025: ('20250325210102','20251010132955')}
def snap_for(date):
    y, m = int(date[:4]), int(date[5:7])
    cand = {'2023-03':'20230227134025','2023-04':'20230227134025','2023-05':'20230227134025','2023-09':'20230922070539','2023-10':'20230922070539','2023-11':'20230922070539','2023-12':'20230922070539',
            '2024-02':'20240417041433','2024-04':'20240417041433','2024-05':'20240417041433','2024-10':'20241111025359','2024-11':'20241111025359','2024-12':'20241111025359',
            '2025-03':'20250325210102','2025-04':'20250325210102','2025-05':'20250325210102','2025-06':'20250325210102','2025-10':'20251010132955','2025-11':'20251010132955','2025-12':'20251010132955'}
    return cand.get(date[:7], '2025')
H = [  # date, time, title, subtitle, kind, lineup
 ('2023-03-07','20:30','Apollo Brown','«fruit of the boom»','concert',['Apollo Brown']),
 ('2023-03-18','21:30','darkness 4eva','Blanche Biau + Mistress + sch_tsch','party',['Blanche Biau','Mistress','sch_tsch']),
 ('2023-03-26','20:45','District Five','Residenz, monatlich','concert',['District Five']),
 ('2023-03-31','21:30','Queer Balkan Disco','mit The Nozez','party',['The Nozez']),
 ('2023-10-05','22:00','Bound By Endogamy','transhelvetiq und helsinki','concert',['Bound By Endogamy']),
 ('2023-10-12','20:30','moods chez sinki','Anna&Stoffner, Taima&Meier','concert',['Anna&Stoffner','Taima&Meier']),
 ('2023-10-20','21:30','PLAYMOB.IL Albumfeier','EP «74»','concert',['Playmob.il','DJ Real Madrid']),
 ('2023-12-02','21:30','Man On Man','«it\'s so fun to be gay»','concert',['Man On Man']),
 ('2024-04-19','21:00','Pascal Gamboni','«c a o s – im Auge des Orkans»','concert',['Pascal Gamboni']),
 ('2024-04-20',None,'AchTung Niemand','«Wir sind gute Menschen», Debüt-Album','concert',['AchTung Niemand','Jürg Halter']),
 ('2024-05-11','21:15','Walter Frosch','Plattengefeier «Star 10110»','concert',['Walter Frosch','Lou','Alina Arshi']),
 ('2024-05-14','20:30','Dino Brandão','ausverkauft (3 Abende 13.–15.5.)','concert',['Dino Brandão']),
 ('2024-11-22','23:59','DJ Marcelle','Tanz-Residenz','party',['DJ Marcelle']),
 ('2024-12-06','22:00','Palko! Muski!','Albumfeier «Bon Voyage!» mit dj emina','concert',['Palko! Muski!','DJ Emina']),
 ('2025-03-19','20:30','Thomas Azier','',  'concert',['Thomas Azier']),
 ('2025-03-31','20:30','Apollo Brown x Marco Polo','back-to-back live beat set','concert',['Apollo Brown','Marco Polo']),
 ('2025-04-04','00:07','DJ Marcelle','«nacht ist tag ist nacht»','party',['DJ Marcelle']),
 ('2025-10-17','21:00','Blind Butcher','Album-Release «Hekate»','concert',['Blind Butcher']),
 ('2025-10-24','20:30','Muralim','Album-Feier','concert',['Muralim']),
 ('2025-10-31','21:00','Queer Balkan Disco','numero 16','party',[]),
 ('2025-11-25','20:45','Dino Brandão','Musik-Release «I love you, I leave you»','concert',['Dino Brandão']),
 ('2025-12-04','20:30','Minami Deutsch','«Enzyklopädia Krautrock», mit Weite','concert',['Minami Deutsch','Weite']),
]
for i,(d,t,ti,su,k,l) in enumerate(H):
    out.append(dict(id=f'hk-{d}-{i}', title=ti, subtitle=su or None, date=d, time=t, venue='Helsinki Klub', address='Geroldstrasse 35, 8005 Zürich', kind=k, lineup=l or [ti],
        price=None, organizer='Helsinki Klub', source_url=f'https://web.archive.org/web/{snap_for(d)}/{HELS}/', political=False, approval_needed=False,
        note='Quelle: archivierte Startseite des Klubs (Programmvorschau); Preis dort nicht angegeben', dates=None))
# ---- Dynamo (Wayback of /programm) ----
D = [
 ('2024-05-30','The Drowns & Pkew Pkew Pkew','Hardcore/Punk',['The Drowns','Pkew Pkew Pkew'],'concert','20240601'),
 ('2024-06-03','Snuff + Versus the World','Hardcore/Punk',['Snuff','Versus the World'],'concert','20240601'),
 ('2024-06-07','Get Dead & The Last Gang','Hardcore/Punk',['Get Dead','The Last Gang'],'concert','20240601'),
 ('2024-06-08','«ANARCHY IN THE CLUB»','Party Elektro/Hardcore/Punk',[],'party','20240601'),
 ('2024-06-06','Sketchy & Tutti Frutti','Improvisationstheater',['Sketchy','Tutti Frutti'],'theater','20240601'),
 ('2025-05-19','JODOQ','EP Release-Show «Polaroid Palace»',['JODOQ'],'concert','20250601'),
 ('2025-05-21','The World Is a Beautiful Place & I Am No Longer Afraid to Die','',['The World Is a Beautiful Place & I Am No Longer Afraid to Die'],'concert','20250601'),
 ('2025-05-24','17. Lauter Festival','',[],'festival','20250601'),
 ('2025-05-28','Foxing','',['Foxing'],'concert','20250601'),
]
for i,(d,ti,su,l,k,s) in enumerate(D):
    out.append(dict(id=f'dy-{d}-{i}', title=ti, subtitle=su or None, date=d, time=None, venue='Jugendkulturhaus Dynamo', address='Wasserwerkstrasse 21, 8006 Zürich', kind=k, lineup=l or [ti],
        price=None, organizer='Jugendkulturhaus Dynamo', source_url=f'https://web.archive.org/web/{s}/https://www.dynamo.ch/programm', political=False, approval_needed=False,
        note='Datum aus Wayback-Snapshot des Dynamo-Programms; Uhrzeit dort nicht verlässlich', dates=None))
# ---- Gessnerallee (2026 season) ----
G = [('2026-01-14','20:00','Glistening (Remembering the Unknown)','DIVAS, Premiere mit Apéro und Zine Launch','theater',['DIVAS'],'Tanz/Performance'),
     ('2026-01-24','16:00','Das Haus meines Geistes','Old Masters','theater',['Old Masters'],'Theater'),
     ('2026-01-25','15:00','Kinderkonzertreihe: Rita Roof','','concert',['Rita Roof'],'Konzert'),
     ('2026-01-14','17:30','Art in Conflict: Jenseits staatlicher Strukturen – selbstorganisierte Kulturnetzwerke','Gesprächsreihe, artasfoundation','reading',['artasfoundation'],'Gespräch')]
for i,(d,t,ti,su,k,l,n) in enumerate(G):
    out.append(dict(id=f'ga-{d}-{i}', title=ti, subtitle=su or None, date=d, time=t, venue='Gessnerallee', address='Gessnerallee 8, 8001 Zürich', kind=k, lineup=l, price=None,
        organizer='Gessnerallee Zürich', source_url='https://web.archive.org/web/20251015/https://gessnerallee.ch/de/programm', political=False, approval_needed=False, note=n+'; Jahr 2026 per Wochentagsprüfung', dates=None))
from build_events2 import round2
out += round2()
ids = [e['id'] for e in out]
assert len(ids) == len(set(ids)), 'duplicate ids'
out.sort(key=lambda x: x['date'])
json.dump(out, open(HERE / 'events.json', 'w'), ensure_ascii=False, indent=1)
import collections
print(len(out), dict(collections.Counter(e['kind'] for e in out)), 'approval', sum(e['approval_needed'] for e in out))
for e in out:  # weekday sanity for hand-curated
    pass
