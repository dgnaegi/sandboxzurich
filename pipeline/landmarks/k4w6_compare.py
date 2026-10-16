"""Photo | isolated-model comparison rows for the wave-5 landmarks -> preview/lm11_<id>.jpg and preview/lm11_all.jpg.
Usage: python k4w6_compare.py [id,id,...|sheet]   (needs dev server on :5173; the game tiles are NOT rebuilt, so only the isolated model is shown)"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
from common import ll, ROOT

PREV = ROOT / "preview"; WEB = ROOT / "web"
OVR = json.load(open(ROOT / "pipeline/overrides/landmarks_k4w6.json"))["landmarks"]
LM = {e["name"]: e for e in OVR}
M = {}
for f in ("photos_k4w6.json",):
    try: M.update(json.load(open(ROOT / "research/v3" / f)))
    except Exception as ex: print("meta", f, ex)
# id: (title, [(site, photo idx, target_h)])
SPECS = {
    "limmat": ("Schulhaus Limmat", [("sh_limmat", 3, 8), ("sh_limmat", 1, 8)]),
    "feld": ("Schulhaus Feld (Aussersihl)", [("sh_feld", 7, 9), ("sh_feld", 1, 9)]),
    "kern": ("Schulhaus Kern (Aussersihl)", [("sh_kern", 8, 9)]),
    "hohl": ("Schulhaus Hohl (Aussersihl)", [("sh_hohl", 2, 9), ("sh_hohl", 5, 9)]),
    "sihlfeld": ("Schulhaus Sihlfeld", [("sh_sihlfeld", 0, 9), ("sh_sihlfeld", 1, 9)]),
    "schuetze": ("Schulhaus und Quartierzentrum Schuetze", [("sh_schuetze", 8, 10), ("sh_schuetze", 5, 10)]),
    "pfingstweid": ("Schulhaus Pfingstweid", [("sh_pfingstweid", 24, 7), ("sh_pfingstweid", 3, 7)]),
    "wengi": ("Schulhaus Wengi", [("sh_wengi", 1, 9), ("sh_wengi", 3, 9)]),
    "kappeli": ("Schulhaus Kappeli", [("sh_kappeli", 1, 7), ("sh_kappeli", 3, 7)]),
    "ortsmuseum": ("Ortsmuseum Wiedikon", [("ortsmuseum_wiedikon", 1, 6), ("ortsmuseum_wiedikon", 3, 6)]),
}


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
        out.save(PREV / f"lm11_{sid}.jpg", quality=84); print("lm11", sid)
        for f in PREV.glob(f"_cmpm_{sid}_*.jpg"): f.unlink()


def sheet():
    fs = [f for f in sorted(PREV.glob("lm11_*.jpg")) if f.name != "lm11_all.jpg"]
    cols = 3; W = 800; Hh = 300
    s = Image.new("RGB", (cols * W, ((len(fs) + cols - 1) // cols) * Hh), (20, 20, 20))
    for i, f in enumerate(fs):
        im = Image.open(f).convert("RGB"); im = im.crop((0, 0, im.width, min(im.height, 480))); im.thumbnail((W, Hh)); s.paste(im, ((i % cols) * W, (i // cols) * Hh))
    s.thumbnail((2400, 4000)); s.save(PREV / "lm11_all.jpg", quality=80); print("sheet", len(fs))


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else None
    if a != "sheet": run(a.split(",") if a else list(SPECS))
    sheet()
