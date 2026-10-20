"""Curated start spots -> web/public/data/spawns.json.

Seeds: (name, x, y, look_x, look_y) in local metres. The seed is only a wish point near a known place; with --snap the
game (Playwright, dev server) moves each seed to the nearest legal pavement/square spot with a free view and aims the
yaw at the look target (see web/tests/qa_spawn.mjs --snap). Without --snap the raw seeds are written.
Usage: .venv/bin/python pipeline/spawns.py [--snap [http://localhost:5173]]
"""
import json, math, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'web/public/data/spawns.json'

SEEDS = [
    ('Ni-Una-Menos-Platz', 784, -886, 808, -857),
    ('Langstrasse Mitte', 842, -483, 829, -570),
    ('Langstrasse Brauerstrasse', 755, -672, 740, -740),
    ('Idaplatz', -125, -1117, -163, -1113),
    ('Bullingerplatz', -41, -496, -96, -438),
    ('Stauffacher', 957, -1196, 930, -1290),   # was in a courtyard (951,-1221), moved to the crossing 2026-10-20
    ('Escher-Wyss-Platz', 450, 750, 778, 625),
    ('Turbinenplatz', -4, 633, -3, 754),
    ('Josefwiese', 486, 201, 434, 292),
    ('Lochergut', 70, -945, 105, -892),
    ('Roentgenplatz', 758, 124, 781, 130),
    ('Letzigrund', -1060, -240, -990, -180),
    ('Kasernenareal', 1117, -840, 1233, -928),
    ('Kanzlei', 690, -985, 707, -943),
    ('Baeckeranlage', 528, -693, 645, -732),
    ('Limmatplatz', 1130, 60, 1129, 188),
    ('Hardplatz', -108, -195, -120, -361),
    ('Albisriederplatz', -469, -668, -526, -695),
    ('Hohlstrasse Kollerhof', 745, -737, 752, -773),
    ('Lindenplatz Altstetten', -2380, 360, -2405, 250),
    ('Bahnhof Wiedikon', 470, -1415, 544, -1403),
    ('Schlachthof Herdernstrasse', -800, 20, -837, 34),
    ('Freitag-Turm', 209, 150, 209, 176),
    ('HB Bahnhofplatz', 1735, -700, 1760, -650),
    ('HB Europaallee', 1330, -560, 1400, -601),
]


def raw():
    out = []
    for n, x, y, lx, ly in SEEDS:
        out.append({'name': n, 'x': x, 'y': y, 'yaw': round(math.atan2(lx - x, ly - y), 3), 'look': [lx, ly]})
    return out


def main():
    OUT.write_text(json.dumps({'spawns': raw()}, ensure_ascii=False, indent=1))
    print(f'{len(SEEDS)} seeds written to {OUT.relative_to(ROOT)}')
    if '--snap' in sys.argv:
        i = sys.argv.index('--snap')
        url = sys.argv[i + 1] if len(sys.argv) > i + 1 else 'http://localhost:5173'
        subprocess.run(['node', 'web/tests/qa_spawn.mjs', url, 'pc', '--snap'], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
