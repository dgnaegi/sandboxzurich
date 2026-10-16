"""Fetch frontal crops for each GWR entrance of Langstrasse Sued (see langB_entrances.py). -> research/shops_v3/photos_langB_entr.json"""
import json, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(Path(__file__).parent))
import langB_fetch as F
R = F.R; ROOT = F.ROOT
E = json.load(open(ROOT / "research/shops_v3/entrances_langB.json")); tok = R.token()
def run(e):
    try: return e["id"], F.work(e, tok)
    except Exception as ex: print("ERR", e["id"], repr(ex)[:80]); return e["id"], []
with ThreadPoolExecutor(5) as ex: meta = dict(ex.map(run, E))
json.dump(meta, open(ROOT / "research/shops_v3/photos_langB_entr.json", "w"), ensure_ascii=False)
print(len(E), "entrances", sum(len(v) for v in meta.values()), "views", sum(1 for v in meta.values() if v), "with views")
