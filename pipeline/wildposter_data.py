"""Event data for wild posters: load research/posters/events.json (schema: id,title,subtitle,date,time,venue,address,kind,
lineup[],price,organizer,source_url,political,approval_needed), keep approval_needed=false, geocode roughly."""
import json
import re

from config import ROOT

EVENTS = ROOT / "research" / "posters" / "events.json"
ORIGIN = (2681400.0, 1248700.0)
# street keyword -> (lat, lon): coarse position for 'venues nearby' (no exact geocoding needed)
STREETS = {"langstrasse": (47.3768, 8.5290), "hohlstrasse": (47.3762, 8.5240), "badenerstrasse": (47.3735, 8.5200),
           "hardbrücke": (47.3875, 8.5170), "hardbruecke": (47.3875, 8.5170), "geroldstrasse": (47.3857, 8.5230),
           "limmatstrasse": (47.3830, 8.5340), "josefstrasse": (47.3860, 8.5290), "viaduktstrasse": (47.3880, 8.5240),
           "kanzlei": (47.3745, 8.5255), "stauffacher": (47.3735, 8.5275), "helvetiaplatz": (47.3731, 8.5270),
           "sihlquai": (47.3800, 8.5335), "zollstrasse": (47.3795, 8.5260), "bäckeranlage": (47.3750, 8.5250),
           "röntgenstrasse": (47.3815, 8.5300), "werdstrasse": (47.3712, 8.5265), "müllerstrasse": (47.3745, 8.5290),
           "hardstrasse": (47.3865, 8.5190), "schiffbau": (47.3870, 8.5230), "gessnerallee": (47.3775, 8.5340),
           "lagerstrasse": (47.3770, 8.5340), "seebahnstrasse": (47.3720, 8.5230), "sihlfeld": (47.3722, 8.5185), "seestrasse 395": (47.3430, 8.5370),
           "rote fabrik": (47.3430, 8.5370), "wasserwerkstrasse": (47.3890, 8.5400), "walcheplatz": (47.3790, 8.5400)}
SAMPLE = [
    {"id": "t1", "title": "Nacht der Tiefe", "subtitle": "Techno bis Sonnenaufgang", "date": "2019-11-09", "time": "23:00",
     "venue": "Club Beispiel", "address": "Hardstrasse 1", "kind": "club", "lineup": ["DJ Alpha", "Beta b2b Gamma", "Delta live"],
     "price": "CHF 20", "organizer": "Kollektiv Test"},
    {"id": "t2", "title": "Sommer Open Air", "subtitle": "", "date": "2018-07-21", "time": "16:00", "venue": "Hof Test",
     "address": "Langstrasse 100", "kind": "konzert", "lineup": ["Die Band Eins", "Zweite Welle", "Trio Drei", "Vier Vier"],
     "price": "Eintritt frei", "organizer": ""},
    {"id": "t3", "title": "Der zerbrochene Krug", "subtitle": "Lustspiel von Heinrich von Kleist", "date": "2021-02-05", "time": "20:00",
     "venue": "Theater Probe", "address": "Gessnerallee 8", "kind": "theater", "lineup": ["Regie: A. Muster"], "price": "ab CHF 25",
     "organizer": ""},
    {"id": "t4", "title": "Flohmarkt", "subtitle": "Trödel, Platten, Kleider", "date": "2022-05-14", "time": "10:00 - 17:00",
     "venue": "Kanzleiareal", "address": "Kanzleistrasse 56", "kind": "flohmarkt", "lineup": [], "price": "", "organizer": ""},
    {"id": "t5", "title": "Poetry Slam", "subtitle": "Offene Bühne", "date": "2020-01-17", "time": "20:30", "venue": "Kulturraum",
     "address": "Hohlstrasse 20", "kind": "lesung", "lineup": ["Moderation: C. Probe"], "price": "Kollekte", "organizer": ""}]


def load():
    """Returns (events, source) - only approval_needed=false; falls back to SAMPLE until the research file exists."""
    if EVENTS.exists():
        ev = [e for e in json.load(open(EVENTS)) if not e.get("approval_needed", False)]
        if ev:
            return ev, "events.json"
    return SAMPLE, "sample"


def xy(ev):
    """Local metres of the venue (coarse, street keyword), or None."""
    from pyproj import Transformer
    a = ((ev.get("address") or "") + " " + (ev.get("venue") or "")).lower()
    for k, (la, lo) in STREETS.items():
        if k in a:
            x, y = Transformer.from_crs(4326, 2056, always_xy=True).transform(lo, la)
            return [round(x - ORIGIN[0]), round(y - ORIGIN[1])]
    return None


DAYS = ["MO", "DI", "MI", "DO", "FR", "SA", "SO"]
MONTHS = ["JAN", "FEB", "MÄR", "APR", "MAI", "JUN", "JUL", "AUG", "SEP", "OKT", "NOV", "DEZ"]


def date_parts(ev):
    """(weekday, 'dd.mm.', year-or-'') from ISO date; falls back to the raw string."""
    import datetime
    m = re.match(r"(\d{4})-(\d\d)-(\d\d)", (ev.get("date") or "") or "")
    if not m:
        return "", (ev.get("date") or "") or "", ""
    d = datetime.date(int(m[1]), int(m[2]), int(m[3]))
    return DAYS[d.weekday()], f"{d.day}.{d.month:02d}.", str(d.year)


def year(ev):
    m = re.match(r"(\d{4})", (ev.get("date") or "") or "")
    return int(m[1]) if m else 2020


def kind_of(ev):
    k = ((ev.get("kind") or "") + " " + (ev.get("title") or "")).lower()
    for style, keys in (("flohmarkt", ("flohmarkt", "markt", "trödel", "bazar")), ("theater", ("theater", "lesung", "reading", "tanz", "slam", "kabarett", "oper", "performance", "film")),
                        ("neon", ("club", "party", "rave", "dj", "techno", "nacht", "disco")), ("lineup", ("konzert", "concert", "benefit", "live", "festival", "open air", "band", "gig"))):
        if any(w in k for w in keys):
            return style
    return "swiss"
