"""Run an Overpass query with mirror fallback.

Usage: python pipeline/overpass.py query.overpassql out.json
"""
import sys

import requests

MIRRORS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]
# overpass-api.de answers 406 without a User-Agent.
# overpass.kumi.systems returned 0 for area()/map_to_area queries (2026-10-14); use poly: filters.
HEADERS = {"User-Agent": "sandboxzurich/0.1 (https://github.com/dgnaegi/sandboxzurich)"}


def run(query: str, timeout: int = 600) -> str:
    for url in MIRRORS:
        try:
            r = requests.post(url, data={"data": query}, headers=HEADERS, timeout=timeout)
        except requests.RequestException as e:
            print(f"fail {url}: {e}", file=sys.stderr)
            continue
        if r.status_code == 200:
            print(f"ok {url}", file=sys.stderr)
            return r.text
        print(f"{r.status_code} {url}", file=sys.stderr)
    raise RuntimeError("all Overpass mirrors failed")


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        text = run(f.read())
    with open(sys.argv[2], "w") as f:
        f.write(text)
