"""Ramp sites for the scope pipeline (research/bridges/scopes_plan.md).

Coordinates are game metres (x = E - 2681400, y = N - 1248700). `match` selects the deck rows (name substring, as in
pipeline/ramp_lidar.py), `fetch` is the box the cadastre and imagery are fetched for (whole structure incl. landings),
`view` the box the overlay shows and the scores are computed in (the ramp part of the site).
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
    # transfer sites (phase 4), boxes still to be checked
    "pfingstweid": {"title": "Hardbrücke ramp at Pfingstweidstrasse", "match": "Hardbrücke", "kinds": ("road",),
                    "fetch": (60, 230, 320, 480), "view": (80, 250, 300, 460)},
    "brauer": {"title": "Brauerstrasse ramp", "match": "Brauerstrasse", "kinds": ("road",),
               "fetch": (280, -580, 480, -380), "view": (300, -560, 460, -400)},
}


def site(name):
    if name not in SITES:
        raise SystemExit(f"unknown site {name!r}; known: {', '.join(SITES)}")
    return dict(SITES[name], name=name)
