"""Vergleichsbilder Foto <-> Spiel fuer die k93-Landmarks -> preview/lm3_<id>.jpg (1600 px breit) + Gesamtbogen preview/lm3_k93.jpg.
Braucht den Dev-Server (localhost:5173) und fertig gebaute Kacheln. Usage: .venv/bin/python pipeline/landmarks/lm3_make.py [id ...]"""
import json, math, os, subprocess, sys
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PH = json.load(open(ROOT + "/research/v3/photos.json"))
TMP = os.environ.get("LM3_TMP", "/tmp/lm3"); os.makedirs(TMP, exist_ok=True)

def frame(cx, cy, a_deg):
    a = math.radians(a_deg); ca, sa = math.cos(a), math.sin(a)
    return lambda u, v, h: [round(cx + u * ca - v * sa, 2), round(cy + u * sa + v * ca, 2), h]

ST = frame(-968.9, -165.9, 52.5); AL = frame(-2082.0, 738.0, 0); KI = frame(-2405.0, 250.0, 0); DR = frame(457.0, -1185.0, 0)
WI = frame(544.1, -1403.4, 0); KR = frame(-704.0, -757.0, 0); LB = frame(314.2, -1561.5, 0)
SITES = {
    "letzigrund": dict(photo=("letzigrund", [10, 9]), views=[dict(p=ST(-30, -24, 1.7), l=ST(10, 30, 11), fov=75), dict(p=ST(-24, -39, 11), l=ST(10, 38, 15), fov=70)]),
    "bhf_altstetten": dict(photo=("bhf_altstetten", [24, 17]), views=[dict(p=AL(40, -40, 2.5), l=AL(0, 0, 12), fov=60), dict(p=AL(-40, 25, 2.0), l=AL(-51, 17.6, 3.5), fov=55)]),
    "kirchen_altstetten": dict(photo=("kirchen_altstetten", [16, 23]), views=[dict(p=KI(-60, -30, 2), l=KI(-20, -5, 15), fov=60), dict(p=KI(20, -40, 2), l=KI(0, 0, 14), fov=60)]),
    "dreifaltigkeit_wiedikon": dict(photo=("dreifaltigkeit_wiedikon", [2, 1]), views=[dict(p=DR(-25, -32, 2), l=DR(0, 0, 14), fov=60)]),
    "bhf_wiedikon": dict(photo=("bhf_wiedikon", [24, 17]), views=[dict(p=WI(-24, -24, 2.5), l=WI(0, 0, 6), fov=60, t="21:30"), dict(p=WI(-24, -24, 2.5), l=WI(0, 0, 6), fov=60)]),
    "krematorium_haupttor": dict(photo=("krematorium_haupttor", [12, 10]), views=[dict(p=KR(3, 19, 1.7), l=KR(-3, 11.7, 2.3), fov=60)]),
    "krematorium_sihlfeld": dict(photo=("krematorium_sihlfeld", [0]), views=[dict(p=KR(10, -24, 2.2), l=KR(25, -1, 4), fov=55)]),
    "loewenbrunnen": dict(photo=("loewenbrunnen", [20]), views=[dict(p=LB(7.8, 4.5, 2.2), l=LB(0, 0, 2), fov=50)]),
}

def fit(im, w, h):
    im = im.convert("RGB"); r = min(w / im.width, h / im.height); im = im.resize((int(im.width * r), int(im.height * r)))
    c = Image.new("RGB", (w, h), (24, 24, 24)); c.paste(im, ((w - im.width) // 2, (h - im.height) // 2)); return c

def main(ids):
    for sid in ids or SITES:
        S = SITES[sid]; key, idxs = S["photo"]
        shots = []
        for k, v in enumerate(S["views"]):
            pre = f"{TMP}/{sid}_{k}"
            subprocess.run(["node", ROOT + "/pipeline/landmarks/free_shot.mjs", pre, json.dumps([v]), v.get("t", "12:00")], check=False, capture_output=True)
            shots.append(pre + "_0.jpg")
        rows = []
        for k, sh in enumerate(shots):
            ph = PH[key]["photos"][idxs[min(k, len(idxs) - 1)]]["file"]
            L = fit(Image.open(ROOT + "/" + ph), 800, 450); R = fit(Image.open(sh), 800, 450)
            row = Image.new("RGB", (1600, 450)); row.paste(L, (0, 0)); row.paste(R, (800, 0)); rows.append(row)
        out = Image.new("RGB", (1600, 450 * len(rows)))
        for k, r in enumerate(rows): out.paste(r, (0, 450 * k))
        out.save(f"{ROOT}/preview/lm3_{sid}.jpg", quality=84); print("wrote", sid)

if __name__ == "__main__":
    main(sys.argv[1:])
