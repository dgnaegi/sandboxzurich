"""Ramp sites for the scope pipeline (research/bridges/scopes_plan.md).

Coordinates are game metres (x = E - 2681400, y = N - 1248700). `match` selects the deck rows (name substring or a tuple of
them; "" with a `seed` (x, y, r) selects the chains passing within r of the seed, for unnamed rows), `fetch` is the box the
cadastre and imagery are fetched for (whole structure incl. landings), `view` the box the overlay shows and the scores are
computed in (the ramp part of the site). `python3 pipeline/scopes/overlay.py <site> --rows` draws the rows to pick from.
"""
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


def site(name):
    if name not in SITES:
        raise SystemExit(f"unknown site {name!r}; known: {', '.join(SITES)}")
    return dict(SITES[name], name=name)
