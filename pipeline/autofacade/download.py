"""Download the selected Mapillary thumbs (1024 px) in parallel to data/raw/autofacade/img/<id>.jpg. Cached; skips existing.
Usage: python download.py [--only-bld file.json]   log -> logs/autofacade_dl.log"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

from common import CACHE

D = CACHE / "img"
D.mkdir(parents=True, exist_ok=True)
H = {"User-Agent": "sandboxzurich/0.1 (research)"}


def get(item):
    i, url = item
    f = D / f"{i}.jpg"
    if f.exists():
        return 0
    for _ in range(3):
        try:
            r = requests.get(url, headers=H, timeout=30)
            if r.ok:
                f.write_bytes(r.content)
                return 1
        except requests.RequestException:
            pass
    return -1


def main():
    need = json.load(open(CACHE / "imgs_needed.json"))
    ids = set(json.load(open(sys.argv[1]))) if len(sys.argv) > 1 else None
    items = [(i, u) for i, u in need.items() if ids is None or i in ids]
    ok = fail = 0
    with ThreadPoolExecutor(6) as ex:
        for n, r in enumerate(ex.map(get, items)):
            ok += r == 1; fail += r < 0
            if n % 500 == 0:
                print(n, len(items), "new", ok, "fail", fail, flush=True)
    print("done new", ok, "fail", fail, flush=True)


if __name__ == "__main__":
    main()
