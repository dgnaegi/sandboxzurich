"""Round 2: additional venues. Called from build_events.py. Reads only cached raw data in raw/."""
import json, re, html, glob, pathlib
HERE = pathlib.Path(__file__).parent
def txt(s): return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', s or ''))).strip()
def ev(id, title, date, venue, address, kind, lineup, source_url, organizer, time=None, subtitle=None, price=None,
       political=False, approval=False, note=None):
    return dict(id=id, title=title, subtitle=subtitle, date=date, time=time, venue=venue, address=address, kind=kind,
                lineup=lineup or [title], price=price, organizer=organizer, source_url=source_url,
                political=political, approval_needed=approval, note=note, dates=None)

# ---------------- Gessnerallee (Statamic GraphQL, raw/gessnerallee.json) ----------------
GA_PICK = {  # (first show date, title prefix) -> (kind, lineup or None, note)
 ('2024-09-27','DOWN'):('concert',['Mélissa Guex'],''),
 ('2024-10-04','Navy Blue'):('theater',['Oona Doherty'],'Tanz'),
 ('2024-10-04','LA Timpa'):('concert',['LA Timpa','WAT TAKLAEW'],''),
 ('2024-11-07','Dawuna'):('concert',['Dawuna'],''),
 ('2024-12-07','untamed.night'):('party',['untamed.love'],''),
 ('2024-12-13','Unsightly Drag'):('theater',['Quiplash'],'Drag/Performance'),
 ('2025-01-15','COLD'):('theater',None,'Spoken-Word-Show'),
 ('2025-03-01','SONOSYNTHESIS'):('concert',['NÂR','Siavash Namehshiri'],''),
 ('2025-04-12','THE LIMIT'):('party',['Julian Zigerli'],'Party/Performance'),
 ('2025-05-22','Eat me Now'):('theater',['Arlette Dellers'],'Tanz/Performance'),
 ('2025-09-18','Neutralitätstheater'):('party',['dibbasey'],'Disco'),
 ('2025-09-21','KOMMANDO AJAX'):('reading',['Cemile Sahin'],''),
 ('2025-10-30','25th ZURICH'):('festival',['Zurich Jazznojazz Festival'],''),
 ('2025-11-07','Songs of the Wayfarer'):('theater',['Claire Cunningham'],'Tanz'),
 ('2026-01-29','Wen Keng'):('theater',['RRRRRR Collective'],'Performance/Musik'),
 ('2026-02-27','Collapse in 5 acts'):('theater',['Simone Aughterlony'],'Tanz/Performance'),
 ('2026-03-22','Fai Baba'):('concert',['Fai Baba','Amour sur Mars'],''),
 ('2026-03-27','The Blackest White'):('party',['Naya de Souza'],'Party/Performance'),
 ('2026-04-16','Zusammensein'):('reading',['Hadija Haruna-Oelker'],'Lesung'),
 ('2026-05-09','The Fur and Lace'):('party',['Liquid','Prince Zulu'],'Kiki Ball'),
 ('2026-05-10','Groove Gala'):('party',['Reut Nahum','Kilia'],'Rave'),
 ('2026-06-19','INSIDE_OUT'):('theater',['Kian Amadeus H.','Sarah Calört'],'Performance'),
 ('2026-10-02','Backslash Festival'):('festival',['Backslash Festival'],'Musik/Tanz/Performance'),
}
def gessnerallee():
    out = []; done = set()
    d = json.load(open(HERE / 'raw/gessnerallee.json'))['data']['entries']['data']
    for e in d:
        sh = sorted(s['start']['start'][:10] for s in e['shows'])
        if not sh: continue
        for (dt, pre), (kind, lineup, note) in GA_PICK.items():
            if sh[0] == dt and e['title'].startswith(pre) and (dt, pre) not in done:
                done.add((dt, pre))
                tm = sorted(e['shows'], key=lambda s: s['start']['start'])[0].get('start_time')
                artist = e.get('artist')
                out.append(ev(f"ga-{e['slug']}"[:60], txt(e['title']), dt, 'Gessnerallee', 'Gessnerallee 8, 8001 Zürich', kind,
                    lineup or ([artist] if artist else None), f"https://gessnerallee.ch/de/programm/{e['slug']}", 'Gessnerallee Zürich',
                    time=tm, subtitle=artist if lineup else None, note=(note + '; ' if note else '') + 'Quelle: CMS-API gessnerallee.ch (cms.gessnerallee.ch/graphql), Programm-URL nach Slug'))
    return out

# ---------------- Palais Mascotte (Nunight widget API, raw/mascotte/*.js) ----------------
MA_PICK = {5:'party',6:'party',7:'party',12:'party',21:'party',47:'party',73:'party',75:'party',99:'party',163:'festival',160:'party',172:'party',183:'party',50:'party'}
def mascotte():
    out = []
    for i, kind in MA_PICK.items():
        s = open(HERE / f'raw/mascotte/{i}.js').read()
        s = json.loads(re.match(r'cb\((.*)\)\s*;?\s*$', s, re.S).group(1))
        def g(c):
            m = re.search(r'class="%s"[^>]*>(.*?)</div>' % c, s, re.S); return txt(m.group(1)) if m else ''
        dm = re.search(r'(\d\d)\.(\d\d)\.(\d{4})', g('nu_event_date'))
        date = f'{dm[3]}-{dm[2]}-{dm[1]}'
        t = g('nu_event_time'); tm = re.match(r'(\d\d:\d\d)', t); tm = tm.group(1) if tm else None
        title = re.search(r'class="nu_event_title">(.*?)(?:<div|</div>)', s, re.S); title = txt(title.group(1))
        lineup = [x.strip() for x in re.split(r'[|,]', g('nu_event_artists') or g('nu_event_lineup')) if x.strip()]
        out.append((i, date, tm, title, lineup, g('nu_event_price')))
    res = []
    for i, date, tm, title, lineup, pr in out:
        pr = re.sub(r'^Entry:\s*', '', pr).strip()
        res.append(ev(f'pm-{i}', title, date, 'Palais Mascotte', 'Theaterstrasse 10, 8001 Zürich', MA_PICK[i], lineup, 'https://palaismascotte.nunight.com/nu/api/apiv1/event_widget_details.jsonp?id=%d&style=0&callback=cb' % i,
            'Palais Mascotte', time=tm, price=(pr if pr and 'Gratis' not in pr else (pr or None)), note='Quelle: Nunight-Widget-API des Palais Mascotte (Veranstalter-Daten)'))
    return res

# ---------------- Kino Xenix (static JSON monthly programmes, raw/xenix/) ----------------
XE_PICK = [  # (date, title prefix, kind)
 ('2022-07-25','Exils','film'),('2022-08-08','Summer of Soul','film'),('2023-07-26','Me and You','film'),('2023-08-16','Ruäch','film'),
 ('2024-07-16','Gimme Shelter','film'),('2024-08-07','One Night in Miami','film'),('2025-07-23','Before Sunrise','film'),
 ('2025-08-06','Gegen die Wand','film'),('2026-07-17','The Truman Show','film'),('2026-08-14','Midnight Cowboy','film'),
 ('2022-02-28','Zugluft','concert'),('2022-03-21','Ströiner','concert'),('2023-01-16','Kapällä Vörig','concert'),
 ('2022-11-26','CH-Body Politics: Programm 2','film'),('2022-05-02','The Souvenir','film'),('2023-09-15','Klassenverhältnisse','film'),
]
def xenix():
    res = []; seen = set()
    for f in sorted(glob.glob(str(HERE / 'raw/xenix/2*.json'))):
        d = json.load(open(f))
        for e in d['time_line']:
            for date, pre, kind in XE_PICK:
                if e['date'] == date and e['title'].startswith(pre) and (date, pre) not in seen:
                    seen.add((date, pre))
                    pre_ = (e.get('title_prepend') or '').strip(); app = (e.get('title_append') or '').strip()
                    sub = ' – '.join(x for x in (pre_.title() if pre_.isupper() else pre_, app) if x) or None
                    ld = [e['title']] if kind == 'concert' else [e['title']] + ([app] if app.startswith(('Mit ', 'mit ')) else [])
                    res.append(ev('xe-%s-%s' % (date, re.sub(r'\W+', '', e['title'])[:14]), txt(e['title']), date, 'Kino Xenix' if kind == 'film' else 'Xenix Bar', 'Kanzleistrasse 52, 8004 Zürich', kind, ld,
                        'https://www.xenix.ch' + e['url'], 'Kino Xenix', time=e['time'][:5], subtitle=sub,
                        note='Quelle: Xenix-Programm-JSON (static/json); Open-Air-Reihe %s' % ('Xenix Open Air' if pre_ == 'OPEN AIR' else '').strip()))
    return res


# ---------------- Wayback-based venues (raw/wayback/<venue>/<timestamp>.txt = text of archived start/programme page) ----------------
WB = HERE / 'raw/wayback'
import datetime
WD_DE = {'Mo':0,'Di':1,'Mi':2,'Do':3,'Fr':4,'Sa':5,'So':6}
WD_EN = {'Mon':0,'Tue':1,'Wed':2,'Thu':3,'Fri':4,'Sat':5,'Sun':6}
WD_LONG = {'Montag':0,'Dienstag':1,'Mittwoch':2,'Donnerstag':3,'Freitag':4,'Samstag':5,'Sonntag':6}
MO = {'Jan':1,'Feb':2,'Mar':3,'Mär':3,'März':3,'Apr':4,'April':4,'Mai':5,'May':5,'Jun':6,'Juni':6,'Jul':7,'Juli':7,'Aug':8,'Sep':9,'Sept':9,'Okt':10,'Oct':10,'Nov':11,'Dez':12,'Dec':12,
      'Januar':1,'Februar':2,'August':8,'September':9,'Oktober':10,'November':11,'Dezember':12}
def snaps(venue):
    for f in sorted((WB / venue).glob('*.txt')):
        yield f.name[:14], f.read_text().split('\n')
def _year(ts, mo, d, wd, table):
    y0 = int(ts[:4])
    for y in (y0, y0 + 1):
        try:
            if datetime.date(y, mo, d).weekday() == wd: return y
        except ValueError: pass
    return None
def wb_url(venue_url, ts): return f'https://web.archive.org/web/{ts}/{venue_url}'

def _moods_index():
    idx = {}
    for ts, L in snaps('moods'):
        for i, l in enumerate(L):
            if re.match(r'^\d\d$', l) and i + 3 < len(L) and L[i+1].rstrip('.') in MO and L[i+2].rstrip('.') in {**WD_DE, **WD_EN}:
                y = _year(ts, MO[L[i+1].rstrip('.')], int(l), {**WD_DE, **WD_EN}[L[i+2].rstrip('.')], None)
                if not y: continue
                blk = []; k = i + 3
                while k < len(L) and L[k] != 'More' and len(blk) < 8: blk.append(L[k]); k += 1
                idx.setdefault(f'{y}-{MO[L[i+1].rstrip(".")]:02d}-{int(l):02d}', []).append((ts, blk))
    return idx
MOODS = [  # (date, needle in block, kind, lineup, subtitle)
 ('2022-11-14','Kokoko!','concert',['Kokoko!'],'The Soundtrack of Kinshasa’s Tomorrow'),
 ('2022-11-17','Die Sterne','concert',['Die Sterne'],'«Hallo Euphoria Tour»'),
 ('2022-11-19','L´Oncle Soul','concert',['Ben (L´Oncle Soul)'],'Soul'),
 ('2022-11-26','Sina','concert',['Sina'],'«Ziitsammläri» (Mundart-Pop)'),
 ('2023-12-15','Shantel','concert',['Shantel & Bucovina Club Soundsystem'],'BalkanEkstra: Partizani Super Sonic Live Tour'),
 ('2023-12-16','Dub Spencer','concert',['Dub Spencer & Trance Hill','Umberto Echo'],'Live in Surround Tour'),
 ('2024-03-02','Grand Mother','concert',['GMF - Grand Mother’s Funck'],'30 Years Reunion Show'),
 ('2024-03-08','L\'Rain','festival',["L'Rain"],'Currents Festival'),
 ('2024-03-16','Noura Mint Seymali','concert',['Noura Mint Seymali'],'Psychedelic Desert Blues'),
 ('2024-08-07','Marcos Valle','concert',['Marcos Valle'],'Moods Summer Special'),
 ('2024-11-30','Sahra Halgan','concert',['Sahra Halgan'],'Desert Blues'),
 ('2024-12-03','DakhaBrakha','concert',['DakhaBrakha'],'BalkanEkstra: Ethno Chaos'),
 ('2025-11-27','Orchestra Baobab','concert',['Orchestra Baobab'],''),
 ('2025-12-12','Fulu Miziki','concert',['Fulu Miziki'],'Afrofuturistic Punk'),
 ('2026-03-27','Stella & The Longos','concert',['Stella & The Longos'],'«Amour Propre»'),
 ('2026-04-04','Imarhan','concert',['Imarhan'],'Tuareg Blues'),
 ('2026-04-09','Bahamadia','concert',['Bahamadia','The RuffCats Band','DJ Eclipse'],'Hip Hop Zoo & Moods present'),
]
def moods():
    idx = _moods_index(); out = []
    for date, needle, kind, lineup, sub in MOODS:
        ts, blk = next(x for x in idx[date] if needle in ' '.join(x[1]))
        tm = next((x for x in blk if re.match(r'^\d\d:\d\d$', x)), None)
        out.append(ev(f'mo-{date}-{re.sub(r"\W+", "", needle)[:10]}', lineup[0] if kind == 'concert' else sub, date, 'Moods', 'Schiffbaustrasse 6, 8005 Zürich', kind, lineup,
            wb_url('https://www.moods.ch/en', ts), 'Moods im Schiffbau', time=tm, subtitle=sub or None,
            note='Quelle: archivierte Moods-Startseite (Programmvorschau); Preis dort nicht angegeben; Adresse allgemein bekannt (Moods im Schiffbau)'))
    return out

NEU = [  # (date, title, kind, lineup, subtitle)
 ('2022-11-05','Red','theater',['Theater Neumarkt (Kinderstück)'],'Ein digitales Märchen'),
 ('2023-03-16','Le Sacre du Printemps','theater',['Le Sacre du Printemps'],None),
 ('2023-11-19','«Hässlichkeit» von Moshtari Hilal','reading',['Moshtari Hilal'],'ausverkauft'),
 ('2023-11-22','Memo von Nemo – Nachrichten aus der Tiefe','theater',['Memo von Nemo'],'Ein musikalischer Tauchgang für Lebewesen ab 6 Jahren'),
 ('2024-03-16','Vom Zeugenschutz des Raubwürgers','theater',['Kevin Rittberger (Text)'],'Uraufführung'),
 ('2024-08-22','Gloria – The Right to Be Desperate','theater',['Gloria'],'Ein Ausflug in die Welt der Therapie- und Beichtkultur'),
 ('2024-11-16',"Vanilla Sex #let's bee butterfly!",'theater',["Vanilla Sex"],'Chorgasse Neumarkt'),
 ('2025-03-19','Zer0 Gravity','theater',['Zer0 Gravity'],'Ein Solo zwischen Gnade des Chaos und Schwerkraft des Herzens'),
]
def neumarkt():
    idx = {}
    for ts, L in snaps('neumarkt'):
        j = [i for i, l in enumerate(L) if l.startswith('Next Events')]
        if not j: continue
        i = j[0] + 1
        while i < len(L) and L[i] != 'Alle Events':
            if re.match(r'^\d{1,2}$', L[i]) and L[i+1].rstrip('.') in MO:
                wm = re.match(r'^(\w+), (\d\d:\d\d)', L[i+2]); k = i + 3; blk = []
                while k < len(L) and not re.match(r'^\d{1,2}$', L[k]) and L[k] != 'Alle Events': blk.append(L[k]); k += 1
                if wm and blk:
                    y = _year(ts, MO[L[i+1].rstrip('.')], int(L[i]), WD_LONG.get(wm[1], -1), None)
                    if y: idx.setdefault(f'{y}-{MO[L[i+1].rstrip(".")]:02d}-{int(L[i]):02d}', (ts, wm[2], blk))
                i = k
            else: i += 1
    out = []
    for date, title, kind, lineup, sub in NEU:
        ts, tm, blk = idx[date]; assert blk[0].startswith(title[:12]), (date, blk)
        out.append(ev(f'tn-{date}', title, date, 'Theater Neumarkt', 'Neumarkt 5, 8001 Zürich', kind, lineup, wb_url('https://www.theaterneumarkt.ch/', ts),
            'Theater am Neumarkt', time=tm, subtitle=sub, note='Quelle: archivierte Startseite (Next Events); Preise: Wahlpreismodell des Hauses (drei Preise), Betrag nicht erfasst'))
    return out

PB = [  # (start date, title prefix, kind, lineup, venue note)
 ('2022-03-10','SPC Photo Awards',['Swiss Photo Club']),('2023-01-12','Luca Zanier',['Luca Zanier']),('2023-01-12','Schattenreise',['H.R. Giger']),
 ('2023-06-01','Echoes of Spirit',['ї [ji] collective']),('2023-06-08','Analoge Fotografie',['Paul Martin Padrutt']),
 ('2025-02-27','Künstlerporträts 1985',['Niklaus Stauss']),('2025-11-06','New York 1991',['Clément Olivier Meylan']),
 ('2026-03-12','Zürich am Fluss',['Urs Villiger']),('2026-03-12','Assemblagen',['GAF9.10.zh']),
 ('2025-11-06','45 Jahre Jugendunruhen',['okaj zürich']),
]
def photobastei():
    idx = {}
    for ts, L in snaps('photobastei'):
        for i, l in enumerate(L):
            m = re.match(r'^(\d+)/(\d+)/(\d\d) - (\d+)/(\d+)/(\d\d),?\s*(.*)$', l)
            if m and i + 2 < len(L):
                a = f'20{m[3]}-{int(m[1]):02d}-{int(m[2]):02d}'; b = f'20{m[6]}-{int(m[4]):02d}-{int(m[5]):02d}'
                idx.setdefault((a, L[i+1]), (ts, b, L[i+2], m[7]))
    out = []
    for a, pre, lineup in PB:
        k = next(k for k in idx if k[0] == a and k[1].startswith(pre)); ts, b, artist, loc = idx[k]
        pol = pre.startswith('45 Jahre')
        out.append(ev(f'pb-{a}-{re.sub(r"\W+", "", pre)[:10]}', k[1], a, 'Photobastei', 'Sihlquai 125, 8005 Zürich', 'exhibition', lineup, wb_url('https://www.photobastei.ch/', ts),
            'Photobastei', subtitle=f'Ausstellung bis {b}', political=pol, approval=pol,
            note=('Ausstellung zu den Zürcher Jugendunruhen (okaj zürich = kantonaler Dachverband der Jugendarbeit); Inhalt vor Verwendung prüfen. ' if pol else '') + 'Quelle: archivierte Startseite (Ausstellungen)'))
    return out

KZ = [  # (date, needle, kind, lineup, title)
 ('2022-01-27','Metzger','theater',['Die Metzger'],'Theatersport im Kanzlei Club: Metzger'),
 ('2022-02-24','HDTV','theater',['HDTV'],'Theatersport im Kanzlei Club: HDTV'),
 ('2022-04-09','Mü man','concert',['Mü man + Band'],'Konzert Mü man + Band'),
 ('2022-04-23','SmackWTG','concert',['SmackWTG','Chandro'],'Konzert SmackWTG & Chandro'),
 ('2022-05-19','Season Finale','theater',['Theatersport Zürich'],'Theatersport im Kanzlei Club: Season Finale'),
 ('2022-05-25','Noumuso','concert',['Noumuso'],'Noumuso LIVE'),
 ('2022-05-26','Sivilian','concert',['Sivilian'],'Sivilian @Summerbar'),
 ('2023-10-07','Soul Cypher','party',['Soul Cypher Swiss'],'Soul Cypher Swiss'),
 ('2023-12-21','HDTV vs','theater',['HDTV','Die Metzger'],'Theatersport: HDTV vs. Die Metzger'),
]
def kanzlei():
    idx = {}
    for ts, L in snaps('kanzlei'):
        for i, l in enumerate(L):
            if l in {**WD_EN, **WD_DE} and i + 3 < len(L) and re.match(r'^\d\d\.\d\d\.?$', L[i+1]):
                y = _year(ts, int(L[i+1][3:5]), int(L[i+1][:2]), {**WD_EN, **WD_DE}[l], None)
                if y: idx.setdefault(f'{y}-{L[i+1][3:5]}-{L[i+1][:2]}', []).append((ts, ' '.join(L[i+2:i+6])))
    out = []
    for date, needle, kind, lineup, title in KZ:
        ts, blk = next(x for x in idx[date] if needle in x[1])
        tm = re.search(r'ab (\d\d:\d\d)', blk)
        out.append(ev(f'kz-{date}', title, date, 'Kanzlei Club', 'Kanzleistrasse 56, 8004 Zürich', kind, lineup, wb_url('https://kanzlei.ch/', ts), 'Kanzlei Club',
            time=tm.group(1) if tm else None, note='Quelle: archivierte Programmseite des Clubs; Preis dort nicht angegeben'))
    return out

PZ = [  # (date, needle, title, kind, lineup, subtitle, time, price)
 ('2022-02-03','Nachtseminar','Nachtseminar','party',['DJs (siehe Quelle)'],'Open Format Hip Hop House, Donnerstag für Studierende','22:00',None),
 ('2022-02-04','Plaze to be','Plaze to be','party',['Klash','Whitecut','Mwp'],'Hip Hop R&B Afrobeats Dancehall & Latin','23:00','CHF 25'),
 ('2022-07-04','Declan McKenna','Declan McKenna','concert',['Declan McKenna'],'Only Show in Switzerland','19:30','CHF 46 (Vorverkauf)'),
 ('2022-08-24','Ocean Alley','Ocean Alley','concert',['Ocean Alley'],'Only Show in Switzerland','20:00','CHF 42 (Vorverkauf)'),
 ('2023-04-02','The Answer','The Answer','concert',['The Answer','Black Mirrors'],'Only Show in Switzerland','20:00','CHF 55 (Vorverkauf)'),
 ('2023-06-17','Official Pride Party','The Official Pride Party','party',['Plaza Klub & Hive Club'],'Lass uns darüber reden, House Pop Dance','23:00','CHF 30'),
 ('2023-06-24','Lemon','Lemon','party',['Croma','Rollo Tomasi','Bolleters'],'2000er, Charts, Hits, Techno','23:00',None),
 ('2024-03-22','Comedy Experience','Comedy Experience with Rachman Blake','theater',['Rachman Blake'],'Comedy live on stage','19:30','CHF 55 (Vorverkauf)'),
 ('2024-11-15','Dotan','Dotan','concert',['Dotan','Luca Fogale'],'Only Show in Switzerland','19:30','CHF 48 (Vorverkauf)'),
]
def plaza():
    idx = {}
    for ts, L in snaps('plaza'):
        for i, l in enumerate(L):
            m = re.match(r'^(Mo|Di|Mi|Do|Fr|Sa|So) (\d{1,2})$', l)
            if m and L[i+1] in MO:
                y = _year(ts, MO[L[i+1]], int(m[2]), WD_DE[m[1]], None)
                if y: idx.setdefault(f'{y}-{MO[L[i+1]]:02d}-{int(m[2]):02d}', []).append((ts, ' '.join(L[i+2:i+5])))
    out = []
    for date, needle, title, kind, lineup, sub, tm, pr in PZ:
        ts, blk = next(x for x in idx[date] if needle in x[1])
        out.append(ev(f'pz-{date}', title, date, 'Plaza Klub', 'Badenerstrasse 109, 8004 Zürich', kind, lineup, wb_url('https://www.plaza-zurich.ch/nu/events/event_list/', ts), 'Plaza Klub',
            time=tm, subtitle=sub, price=pr, note='Quelle: archivierte Eventliste des Plaza Klub'))
    return out

def misc():
    return [
     ev('bf-2026-10-09-dachs', 'Dachs & Friends', '2026-10-09', 'Bogen F', 'Viaduktstrasse 97, 8005 Zürich', 'concert', ['Luuk','Mel D','Crimer','Follia'],
        'https://www.bogenf.ch/konzerte/dachs-friends-ch', 'Bogen F (netz:werk)', time='20:30', price='CHF 35', note='Quelle: Website Bogen F (Konzertseite), ausverkauft'),
     ev('pt-2026-09-10-baile', 'BaileSystem Like Never Before – Special Edition', '2026-09-10', 'Provitreff', None, 'party',
        ['Cleiton Rasta','Victor Cena','Swag do Complexo','Bimba','JR The G'], 'https://provitreff.ch/', 'Provitreff / adalu', time='19:00',
        note='Quelle: Website Provitreff (Aktuell), VVK über Eventfrog; Adresse nicht auf der Seite, daher offen'),
    ]

def round2():
    return gessnerallee() + mascotte() + xenix() + moods() + neumarkt() + photobastei() + kanzlei() + plaza() + misc()
