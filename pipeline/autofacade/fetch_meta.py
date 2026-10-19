"""Mapillary image metadata (pose, camera) for zone 1 + 4 on a grid of small bboxes. Cached per cell in data/raw/autofacade/meta/.
Usage: python fetch_meta.py [zone ...]   (log: logs/autofacade_meta.log via shell redirect)"""
import json
import sys
import time

import requests

from common import CACHE, ZONES, ROOT, token, xy2ll

FIELDS = "id,computed_geometry,computed_compass_angle,compass_angle,camera_type,camera_parameters,captured_at,is_pano,width,height,sequence,thumb_1024_url,creator"
CELL = 100


def query(tok, x, y, size, depth=0):
    lo0, la0 = xy2ll(x, y)
    lo1, la1 = xy2ll(x + size, y + size)
    for t in range(3):
        r = requests.get("https://graph.mapillary.com/images", params={"access_token": tok, "bbox": f"{lo0:.6f},{la0:.6f},{lo1:.6f},{la1:.6f}", "fields": FIELDS, "limit": 2000},
                         headers={"User-Agent": "sandboxzurich/0.1 (research)"}, timeout=90)
        if r.ok:
            time.sleep(0.3)
            return r.json().get("data", [])
        print("err", r.status_code, r.text[:80], size, flush=True)
        if r.status_code == 500 and depth < 3:
            h = size / 2
            out = []
            for dx in (0, h):
                for dy in (0, h):
                    out += query(tok, x + dx, y + dy, h, depth + 1)
            return out
        time.sleep(5 * (t + 1))
    return None


def main():
    zs = [int(a) for a in sys.argv[1:]] or [1, 4]
    tok = token()
    d = CACHE / "meta"
    d.mkdir(parents=True, exist_ok=True)
    for z in zs:
        x0, y0, x1, y1 = ZONES[z]
        x0 -= 40; y0 -= 40; x1 += 40; y1 += 40
        for cx in range(int(x0), int(x1), CELL):
            for cy in range(int(y0), int(y1), CELL):
                f = d / f"c_{cx}_{cy}.json"
                if f.exists():
                    continue
                data = query(tok, cx, cy, CELL)
                if data is None:
                    continue
                json.dump(data, open(f, "w"))
                print(f"{f.name} {len(data)}", flush=True)
                time.sleep(0.3)


if __name__ == "__main__":
    main()
