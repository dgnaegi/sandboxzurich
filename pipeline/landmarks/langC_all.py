"""Langstrasse landmarks C (bars, cafes, snacks between Limmatplatz and Stauffacher not yet covered by langA/langB). Usage: python langC_all.py [name,name|all]
Facts (colours, signs, awnings) from research/shops_v3 annotations + Mapillary/Panoramax crops (research/langstrasse_C.md). Free-font names only, no logos."""
import sys, math
import k4w4_kit as _k4
from langB_kit import *   # noqa

OVRC = ROOT / "pipeline" / "overrides" / "landmarks_langC.json"


def blockC(*a, **k):
    _k4.OVR4 = OVRC
    return _k4.block_model(*a, **k)


G = dict(frame="#f0ece0", glass="#2e3b46", sky="#8aa0ae", cols=2, rows=3, fh=3.1, bayw=2.5, win=(1.1, 1.65, 0.85), eg_kind="shop", cornice=("#cfc6b0", 0.3, 0.45), lit=0.45, deep_z=6.5)
HIP = lambda col: dict(roof=("hip", col, 4.0), roof_d=5.0, eave_rise=4.0)
# name: (title, id, venue xy (street side), kwargs)
S = {
 "kirroyal": ("Kir Royal Langstrasse 62", "ID_9751B62A", (728, -802), dict(wall="#b86f3c", frame="#efe4d0", eg_h=4.2, eg_col="#5a3a24", base_col="#6a5a48", cornice=("#e0c8a8", 0.3, 0.45), seed=301, **HIP("#6a4a3c"),
             signs=[dict(text="KIR ROYAL", fg="#f4d98a", bg="#3a1a18", glow="#ffb04a", w=3.4, h=0.7, z=3.3, size=26, px=1024)])),
 "longstreet": ("Longstreet Bar Club Langstrasse 92", "ID_C246E1E6", (788, -653), dict(wall="#9c8566", frame="#ece4d2", eg_h=4.3, eg_col="#1e2330", base_col="#7a6a54", cornice=("#c8b898", 0.3, 0.45), seed=302, arch=True,
             awning=("#2f5a9e", 3.0, 1.0), **HIP("#6a4a40"),
             signs=[dict(text="LONGSTREET BAR CLUB", fg="#e8e0d0", bg="#15203a", glow="#6f9cff", w=4.6, h=0.6, z=3.4, size=22, px=1024),
                    dict(text="GRILL", fg="#e8e0d0", bg="#2f5a9e", w=1.8, h=0.6, z=3.4, size=28, px=512, du=4.6)])),
 "leeward": ("Leeward Bar dunkelgruene Front", "ID_492518C1", (713, -779), dict(wall="#2f5d4e", frame="#e4eadf", eg_h=4.3, eg_col="#24302c", base_col="#2a3a34", cornice=("#587a6c", 0.3, 0.4), seed=303,
             awning=("#8b2a22", 3.0, 1.2), roof=("flat", "#706e6a"),
             signs=[dict(text="LEEWARD", fg="#f1e8d6", bg="#1d2a25", w=3.2, h=0.6, z=3.4, size=26, px=1024)])),
 "spaccio": ("Spaccio Langstrasse 61 Caffe", "ID_9A8B7281", (700, -807), dict(wall="#2f4a3e", frame="#f3f1ea", eg_h=4.1, eg_col="#2f4a3e", base_col="#2a3a32", cornice=("#cfd8cc", 0.25, 0.4), seed=304, **HIP("#6a4a40"),
             signs=[dict(text="CAFFE SPACCIO", fg="#e8412f", bg="#2f4a3e", glow="#e8412f", w=3.4, h=0.6, z=3.3, size=26, px=1024)])),
 "peeeng": ("Peeeng Langstrasse 67 bunte Hausfront", "ID_B0AEB012", (718, -768), dict(wall="#c9a48a", frame="#f2ecdc", eg_h=4.0, eg_col="#6a4a5a", base_col="#7a6a60", cornice=("#e6d2c0", 0.3, 0.4), seed=305,
             awning=("#e0dcd0", 3.0, 1.2), **HIP("#7a5448"),
             signs=[dict(text="PEEENG", fg="#ffe35a", bg="#7a2a6a", glow="#ff5ad0", w=3.0, h=0.7, z=3.3, size=30, px=1024)])),
 "allegrotto": ("Allegrotto Chickeria Langstrasse 81 Ecklokal", "ID_139C7E37", (748, -698), dict(wall="#c9c0b0", frame="#eee8da", eg_h=4.3, eg_col="#1a1a1c", base_col="#2b2b2d", cornice=("#a89e8a", 0.3, 0.45), seed=306, **HIP("#6a5448"),
             signs=[dict(text="ALLEGROTTO RESTAURANT", fg="#ffffff", bg="#1e1e1e", w=4.4, h=0.55, z=3.5, size=22, px=1024),
                    dict(text="CHICKERIA", fg="#f1ece0", bg="#2b2b2d", glow="#ffd04a", w=3.2, h=0.6, z=3.5, size=26, px=1024, du=5.0)])),
 "tipsy": ("Tipsy Tiger Langstrasse 133 hellblaues Eckhaus", "ID_72CD165B", (838, -462), dict(wall="#8fb0d0", frame="#f4f2ea", eg_h=4.3, eg_col="#2a2f33", base_col="#3a4046", cornice=("#c8d4e0", 0.3, 0.45), seed=307, **HIP("#6c5448"),
             signs=[dict(text="TIPSY TIGER", fg="#ff7a3a", bg="#1b1b1e", glow="#ff5a2a", w=3.8, h=0.7, z=3.4, size=28, px=1024),
                    dict(text="BAR & BITES", fg="#f2f2f2", bg="#2a2f33", w=2.6, h=0.5, z=3.4, size=22, px=512, du=4.8)])),
 "rasputin": ("Rasputin Bar gelbliche Fassade", "ID_2DE170D8", (829, -796), dict(wall="#c9a96a", frame="#f0e8d4", eg_h=4.2, eg_col="#2a2a2a", base_col="#6e6a64", cornice=("#e0cfa0", 0.3, 0.45), seed=308,
             awning=("#2a2a2a", 3.0, 1.0), **HIP("#6c4a3c"),
             signs=[dict(text="RASPUTIN", fg="#e8e0d0", bg="#1d1d1d", glow="#e03a2a", w=3.4, h=0.7, z=3.4, size=28, px=1024)])),
 "tenzmomo": ("Tenz Momo Hohlstrasse 44 Bierhalle-Haus", "ID_8456019E", (740, -718), dict(wall="#d8d0ac", frame="#f1ebd8", eg_h=4.5, eg_col="#3a2a22", base_col="#7a756c", cornice=("#e8dcb8", 0.3, 0.45), seed=309, arch=True, **HIP("#7a5448"),
             signs=[dict(text="TENZ MOMO", fg="#7a2a22", bg="#e8dcb8", w=3.4, h=0.6, z=3.4, size=28, px=1024)])),
 "aargauerhof": ("Aargauerhof Hohlstrasse 43 Eckhaus", "ID_1A94AA71", (730, -739), dict(wall="#a8aaa8", frame="#e8e6dc", eg_h=4.2, eg_col="#6f7378", base_col="#6f7378", cornice=("#c8c6bc", 0.3, 0.4), seed=310, **HIP("#6a5448"),
             signs=[dict(text="AARGAUERHOF", fg="#e6e6e0", bg="#6f7378", w=4.2, h=0.6, z=3.4, size=26, px=1024)])),
 "midway": ("Midway Bar hellblaues Eckhaus", "ID_5896E6B6", (734, -513), dict(wall="#8fb6d8", frame="#f4f2ea", eg_h=4.2, eg_col="#2f4f9e", base_col="#4a5a6e", cornice=("#cfe0ee", 0.3, 0.4), seed=311,
             awning=("#2f5fa8", 3.0, 1.0), **HIP("#6a5448"),
             signs=[dict(text="MIDWAY", fg="#f2f2f2", bg="#2f4f9e", w=2.8, h=0.7, z=3.3, size=30, px=1024)])),
 "goldengate": ("Golden Gate Bar Schoeneggstrasse 15", "ID_2D0FBE89", (768, -446), dict(wall="#c8c4bc", frame="#f0ece0", eg_h=4.2, eg_col="#2a2a2c", base_col="#6e6a64", cornice=("#a8a49a", 0.3, 0.4), seed=312,
             awning=("#2f5a44", 3.0, 1.0), **HIP("#6c4a3c"),
             signs=[dict(text="GOLDEN GATE BAR", fg="#e8d6a0", bg="#23352c", glow="#e8c870", w=4.2, h=0.6, z=3.4, size=24, px=1024)])),
 "piro": ("Piro Eckhaus Brauerstrasse 45", "ID_9F39188C", (760, -674), dict(wall="#b8b4a8", frame="#efe8d8", eg_h=4.2, eg_col="#4a4a46", base_col="#7a766c", cornice=("#d6d0bc", 0.3, 0.4), seed=313,
             awning=("#e8e4da", 3.0, 1.0), **HIP("#6a4a40"),
             signs=[dict(text="piro", fg="#ffffff", bg="#2e9a4a", glow="#6aff8a", w=2.4, h=0.7, z=3.3, size=32, px=1024)])),
 "stuba": ("Stuebae Brauerstrasse 42", "ID_BB420A18", (798, -678), dict(wall="#8a7f72", frame="#ece4d4", eg_h=4.2, eg_col="#3a2a24", base_col="#6a6258", cornice=("#bdb29e", 0.3, 0.45), seed=314,
             awning=("#b52a24", 3.0, 1.1), **HIP("#6c4a3c"),
             signs=[dict(text="STUBAE", fg="#f2ede4", bg="#b52a24", w=2.8, h=0.6, z=3.4, size=28, px=1024)])),
 "monroe": ("Monroe Brauerstrasse 26 dunkelblaues Eckhaus", "ID_8D7C1222", (862, -726), dict(wall="#2b3550", frame="#e8e2d2", eg_h=4.2, eg_col="#1a2034", base_col="#1e2438", cornice=("#4a5878", 0.3, 0.4), seed=315, arch=True, **HIP("#4a4a52"),
             signs=[dict(text="Monroe", fg="#f0d060", bg="#1a2034", glow="#f0c040", w=2.8, h=0.7, z=3.4, size=30, px=1024)])),
}


def build(only=None):
    for k, (title, bid_, xy, kw) in S.items():
        if only and k not in only: continue
        kw = {**G, **kw}
        b = bid(bid_)
        if not b: print("NO BUILDING", k); continue
        dx, dy = xy[0] - b["c"][0], xy[1] - b["c"][1]; n = math.hypot(dx, dy) or 1.0
        for s in kw.get("signs") or []: s["pref"] = (dx / n, dy / n)
        try: blockC("langC_" + k, title, [bid_], **kw)
        except Exception as e: print("FAIL", k, repr(e)[:300])


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "all"
    build(None if a == "all" else a.split(","))
