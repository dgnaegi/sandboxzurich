"""Photo | isolated-model comparison rows for the wave-5 landmarks -> preview/lm10_<id>.jpg and preview/lm10_all.jpg.
Usage: python k4w5_compare.py [id,id,...|sheet]   (needs dev server on :5173; the game tiles are NOT rebuilt, so only the isolated model is shown)"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
from common import ll, ROOT

PREV = ROOT / "preview"; WEB = ROOT / "web"
OVR = json.load(open(ROOT / "pipeline/overrides/landmarks_k4w5.json"))["landmarks"]
LM = {e["name"]: e for e in OVR}
M = {}
for f in ("photos_k4w4.json", "photos_k5w3.json", "photos_k4w5.json"):
    try: M.update(json.load(open(ROOT / "research/v3" / f)))
    except Exception as ex: print("meta", f, ex)
# id: (title, [(site, photo idx, target_h)])
SPECS = {
    "zett_haus": ("Zett-Haus Badenerstrasse", [("zett_haus", 2, 8), ("zett_haus", 5, 8)]),
    "apollo": ("Apollo-Haus Stauffacherstrasse", [("apollo_stauffacher", 2, 12), ("apollo_stauffacher", 1, 12)]),
    "crowne": ("Hotelbau Badenerstrasse 420", [("crowne_plaza", 3, 10), ("crowne_plaza", 0, 10)]),
    "albis_ost": ("Albisriederplatz Eckhaus", [("albisriederplatz_ost", 1, 10), ("albisriederplatz_ost", 6, 10)]),
    "langstr_eck": ("Langstrasse Eckhaus Cremegelb", [("langstrasse_sued", 6, 9), ("langstrasse_sued", 5, 9)]),
    "langstr_grau": ("Langstrasse Geschaeftsbau grau", [("langstrasse_sued", 0, 9), ("langstrasse_sued", 3, 9)]),
    "pfingstweid": ("Hochhaus Pfingstweidstrasse", [("hochhaus_pfingstweid", 5, 30), ("hochhaus_pfingstweid", 12, 30)]),
}
try: SPECS.update(json.load(open(ROOT / "pipeline/landmarks/k4w5_specs.json")))
except Exception: pass


def cam_for(entry, ph):
    bx, by = entry["x"], entry["y"]
    if ph.get("lat") is None or ph.get("source") == "commons":
        return (bx - 28, by - 48), (bx, by)
    return ll(ph["lat"], ph["lon"]), (bx, by)


def run(ids):
    for sid in ids:
        title, rows = SPECS[sid]; e = LM[title]; mviews = []
        for site, idx, th in rows:
            ph = M[site]["photos"][idx]; (cx, cy), (tx, ty) = cam_for(e, ph)
            mviews.append(f"{cx - e['x']:.1f},{cy - e['y']:.1f},1.9,{tx - e['x']:.1f},{ty - e['y']:.1f},{th},55")
        subprocess.run(["node", str(ROOT / "pipeline/landmarks/view_shot.mjs"), str(PREV / f"_cmpm_{sid}"), title, *mviews], cwd=WEB, capture_output=True, timeout=600)
        out = Image.new("RGB", (1280, 480 * len(rows)), (20, 20, 20))
        for i, (site, idx, th) in enumerate(rows):
            ph = M[site]["photos"][idx]
            a = Image.open(ROOT / ph["file"]).convert("RGB"); a.thumbnail((640, 480)); out.paste(a, (0, i * 480))
            try: out.paste(Image.open(PREV / f"_cmpm_{sid}_{i}.jpg").convert("RGB").resize((640, 480)), (640, i * 480))
            except Exception as ex: print("missing", sid, i, ex)
            d = ImageDraw.Draw(out); d.rectangle([0, i * 480, 300, i * 480 + 16], fill=(0, 0, 0)); d.text((4, i * 480 + 3), f"photo {site}#{idx} | model", fill=(255, 220, 0))
        out.save(PREV / f"lm10_{sid}.jpg", quality=84); print("lm10", sid)
        for f in PREV.glob(f"_cmpm_{sid}_*.jpg"): f.unlink()


def sheet():
    fs = [f for f in sorted(PREV.glob("lm10_*.jpg")) if f.name != "lm10_all.jpg"]
    cols = 3; W = 800; Hh = 300
    s = Image.new("RGB", (cols * W, ((len(fs) + cols - 1) // cols) * Hh), (20, 20, 20))
    for i, f in enumerate(fs):
        im = Image.open(f).convert("RGB"); im = im.crop((0, 0, im.width, min(im.height, 480))); im.thumbnail((W, Hh)); s.paste(im, ((i % cols) * W, (i // cols) * Hh))
    s.thumbnail((2400, 4000)); s.save(PREV / "lm10_all.jpg", quality=80); print("sheet", len(fs))


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else None
    if a != "sheet": run(a.split(",") if a else list(SPECS))
    sheet()
