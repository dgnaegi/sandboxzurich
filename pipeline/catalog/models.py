"""Build all catalog models -> web/public/models/catalog/*.glb + index.json + atlas.png + preview/catalog_models.jpg.
Run: python3 pipeline/catalog/models.py   (needs numpy, Pillow). Variants without material (V7 wall fountain, V10) fall back to V2."""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from model_core import atlas_image, write_glb, ATLAS
from model_brunnen import BRUNNEN
from model_stops import STOPS
from model_moebel import MOEBEL
from model_sheet import sheet

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "web", "public", "models", "catalog")
LIMITS = {"V": 1500, "M": 800, "H": 1200}
FILES = {"V1": "brunnen_v1", "V2": "brunnen_v2", "V3": "brunnen_v3", "V4": "brunnen_v4", "V5": "brunnen_v5", "V6": "brunnen_v6", "V8": "brunnen_v8", "V9": "brunnen_v9",
         "H1": "wartehalle_h1", "H2": "wartehalle_h2", "H3": "ticketautomat_h3", "H4": "anzeige_wand_h4", "H5": "anzeige_decke_h5", "H6": "bank_kurz_h6", "H7": "bank_lang_h7",
         "mast_tram": "mast_tram", "mast_bus": "mast_bus", "M1": "leuchte_m1", "M1b": "seilleuchte_m1b", "M2": "kiosk_m2", "M3": "plakatstelle_m3"}
FALLBACK = {"V7": "V2", "V10": "V2"}


def main():
    os.makedirs(OUT, exist_ok=True)
    atlas = atlas_image(); atlas.save(os.path.join(OUT, "atlas.png"), optimize=True)
    atlas.resize((ATLAS // 2, ATLAS // 2), resample=3).save(os.path.join(OUT, "atlas_256.png"), optimize=True)
    index = {"atlas": "atlas.png", "atlas_size": ATLAS, "units": "m, y up, origin = footprint centre on ground, front = +z", "variants": {}, "fallback": FALLBACK}
    entries = []
    for grp in (BRUNNEN, STOPS, MOEBEL):
        for key, (fn, desc) in grp.items():
            m = fn(); lo, hi = m.bounds(); sz = (hi - lo).tolist()
            tris = m.tri_count(); lim = LIMITS["V" if key.startswith("V") else "H" if key.startswith(("H", "mast")) else "M"]
            assert tris <= (lim if key not in ("H3", "H4", "H5", "H6", "H7") else 800), (key, tris)
            radius = round(max(math.hypot(max(abs(lo[0]), abs(hi[0])), max(abs(lo[2]), abs(hi[2]))), 0.1), 2)
            ex = dict(variant=key, desc=desc, tris=tris, radius=radius, size=[round(v, 2) for v in sz])
            write_glb(m, os.path.join(OUT, FILES[key] + ".glb"), atlas, ex)
            index["variants"][key] = dict(file=FILES[key] + ".glb", desc=desc, tris=tris, radius=radius, size=ex["size"],
                                          bbox=[[round(v, 2) for v in lo], [round(v, 2) for v in hi]], bytes=os.path.getsize(os.path.join(OUT, FILES[key] + ".glb")))
            entries.append((key, m))
    json.dump(index, open(os.path.join(OUT, "index.json"), "w"), indent=1, ensure_ascii=False)
    sheet(entries, os.path.join(ROOT, "preview", "catalog_models.jpg"))
    for k, v in index["variants"].items(): print(k, v["tris"], v["radius"], v["size"], v["bytes"])


if __name__ == "__main__":
    main()
