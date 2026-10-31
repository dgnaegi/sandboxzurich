"""Ramp sites for the scope pipeline (research/bridges/scopes_plan.md).

Coordinates are game metres (x = E - 2681400, y = N - 1248700). `match` selects the deck rows (name substring or a tuple of
them; "" with a `seed` (x, y, r) selects the chains passing within r of the seed, for unnamed rows), `fetch` is the box the
cadastre and imagery are fetched for (whole structure incl. landings), `view` the box the overlay shows and the scores are
computed in (the ramp part of the site). `python3 pipeline/scopes/overlay.py <site> --rows` draws the rows to pick from.
"""
import json
import os

SITES = {
    "gerold": {
        "title": "Geroldrampe (Hardbrücke to Geroldstrasse, by the Freitag tower)",
        "match": "Geroldrampe", "kinds": ("road",),
        "fetch": (30, 130, 310, 330),
        "view": (50, 150, 290, 310), "legend": "upper right",
    },
    "duttweiler": {
        "title": "Duttweilerbrücke south ramp",
        "match": "Duttweilerbrücke", "kinds": ("road",),
        "fetch": (-720, 40, -360, 640),
        "view": (-700, 60, -480, 340), "legend": "lower right",
    },
    # transfer sites (phase 4); pfingstweid / wipkingen boxes still to be checked (python3 pipeline/scopes/overlay.py <site> --rows)
    "pfingstweid": {"title": "Hardbrücke access ramp from Pfingstweidstrasse", "match": "", "seed": (105, 256, 6), "kinds": ("road",),
                    "fetch": (30, 150, 320, 480), "view": (50, 170, 300, 440), "legend": "upper right"},
    "wipkingen": {"title": "Hardbrücke Nord: Hardturmrampe and Sihlquai ramps at the Wipkingerbrücke", "match": ("Hardturmrampe", "Sihlquai-Südrampe", "Sihlquai-Nordrampe"),
                  "kinds": ("road",), "fetch": (280, 660, 640, 920), "view": (290, 680, 620, 900), "legend": "lower right"},
    "brauer": {"title": "Hohlstrasse bridge and Brauerstrasse ramp (over the Sihl line tracks)", "match": "Hohlstrasse", "kinds": ("road",),
               "fetch": (280, -580, 480, -380), "view": (285, -530, 425, -405), "legend": "lower right"},
}


AUTO = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "build", "scopes", "auto_sites.json")


def auto_sites():
    """Sites found by pipeline/scopes/discover.py (every elevated road chain group no hand site covers)."""
    if not os.path.exists(AUTO):
        return {}
    out = {}
    for k, v in json.load(open(AUTO)).items():
        v = dict(v); v["kinds"] = tuple(v["kinds"]); v["fetch"] = tuple(v["fetch"]); v["view"] = tuple(v["view"])
        v["sigs"] = {tuple(x) for x in v["sigs"]}
        out[k] = v
    return out


def site(name):
    S = SITES if name in SITES else auto_sites()
    if name not in S:
        raise SystemExit(f"unknown site {name!r}; known: {', '.join(SITES)} and {len(auto_sites())} automatic sites")
    return dict(S[name], name=name)
