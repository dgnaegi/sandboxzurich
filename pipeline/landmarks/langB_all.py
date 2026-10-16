"""Langstrasse Sued landmarks (bars, clubs, corner houses) built from one spec table. Usage: python langB_all.py [name,name|all]
Each entry: house facts read by hand from Panoramax/Mapillary 360 crops (research/langstrasse_B.md). Signs are free-font names, no logos."""
import sys
from langB_kit import *

# name: (title, [building ids], addr (GWR entrance for sign side), kwargs)
G = dict(frame="#f0ece0", glass="#2e3b46", sky="#8aa0ae", cols=2, rows=3, fh=3.1, bayw=2.5, win=(1.1, 1.65, 0.85), eg_kind="shop", cornice=("#cfc6b0", 0.3, 0.45), lit=0.45, deep_z=6.5)
S = {
 "rothaus": ("Rothaus Langstrasse 119", ["ID_44506752"], "Langstrasse 119", dict(wall="#8e4a38", frame="#e8e2d4", eg_h=4.4, eg_col="#2c2a28", base_col="#6d655c", cornice=("#c9bfa8", 0.3, 0.5),
             roof=("hip", "#5e4a42", 4.0), roof_d=5.0, eave_rise=4.0, seed=201, surround="#d9d0bc",
             signs=[dict(text="HOTEL ROTHAUS", fg="#efe6d2", bg="#3a2a24", w=5.2, h=0.7, z=3.4, size=26, px=1024)])),
 "rossi": ("Bar Caffe Rossi Sihlhallenstrasse", ["ID_36BD1ECB"], "Sihlhallenstrasse 5", dict(wall="#a0523c", frame="#ece5d2", eg_h=4.0, eg_col="#e8e0cc", base_col="#7a6a58", cornice=("#d8cdb4", 0.3, 0.4),
             roof=("hip", "#6a4a40", 4.0), roof_d=5.0, eave_rise=4.0, seed=202, awning=("#c4262e", 3.0, 1.0),
             signs=[dict(text="CAFFE ROSSI", fg="#d0272b", bg="#ece5d2", glow="#d0272b", w=4.2, h=0.7, z=3.3, size=26, px=1024)])),
 "lambada": ("Lambada Bar Club Disco Langstrasse 97", ["ID_BFE39584", "ID_8AEEBDB1"], "Dienerstrasse 43", dict(wall="#8f908c", frame="#d9d9d4", glass="#26323c", eg_h=4.4, eg_col="#16191d", base_col="#5a5a58",
             cornice=("#6c6d6a", 0.25, 0.4), roof=("flat", "#6a6a68"), seed=203, surround="#a9aaa6",
             signs=[dict(text="LAMBADA BAR", fg="#f6c04a", bg="#17120d", glow="#f6b02c", w=4.0, h=0.8, z=3.3, size=26, px=512),
                    dict(text="CLUB DISCO BAR", fg="#f4eedf", bg="#101418", glow="#e8e4d4", w=4.0, h=0.7, z=3.3, size=22, px=512, du=4.0)])),
 "diamond": ("Diamond Bagatelle Langstrasse 90", ["ID_7966DEE6", "ID_9AB41163"], "Langstrasse 93", dict(wall="#d3cfc0", frame="#e9e6da", eg_h=4.2, eg_col="#0d0e13", base_col="#2a2a2e",
             cornice=("#8a867c", 0.3, 0.5), roof=("hip", "#6c5a50", 4.0), roof_d=5.0, eave_rise=4.0, seed=204, awning=("#0e1016", 3.0, 0.9),
             signs=[dict(text="DIAMOND", fg="#e8ecf4", bg="#0b0c12", glow="#6f8cff", w=5.0, h=0.7, z=3.3, size=28, px=1024)])),
 "fattony": ("Fat Tony Langstrasse 135", ["ID_1E3D7492"], "Langstrasse 135", dict(wall="#5e7c9e", frame="#e6e6e2", eg_h=4.3, eg_col="#201f26", base_col="#3a3a40",
             cornice=("#b8c2cf", 0.25, 0.4), roof=("flat", "#6a6c70"), seed=205, awning=("#6e2430", 3.2, 1.2),
             signs=[dict(text="FAT TONY", fg="#f1e8d6", bg="#25222a", glow="#ff6a44", w=3.8, h=0.6, z=3.5, size=26, px=1024)])),
 "klaus": ("Klaus Bar Langstrasse 112", ["ID_55962674"], "Langstrasse 112", dict(wall="#d4a49c", frame="#f1ece0", eg_h=4.2, eg_col="#17130f", base_col="#4a4038",
             cornice=("#e6d6c4", 0.3, 0.4), roof=("hip", "#7a5a4c", 4.5), roof_d=5.0, eave_rise=4.5, seed=206, awning=("#5a1c1c", 3.0, 0.9),
             signs=[dict(text="KLAUS", fg="#f6e6d4", bg="#16120f", glow="#ff7a52", w=3.2, h=0.7, z=3.3, size=30, px=1024)])),
 "hungryduck": ("Eventhaus Langstrasse Hungry Duck", ["ID_27572E52"], "Brauerstrasse 33", dict(wall="#8f8b88", frame="#f0f0ee", glass="#202a32", eg_h=4.6, eg_col="#111417", base_col="#4a4a4a",
             cornice=("#7a7774", 0.25, 0.4), roof=("flat", "#6f6d69"), seed=207, fh=3.0, win=(1.5, 1.4, 0.9),
             signs=[dict(text="HUNGRY DUCK", fg="#f3d27a", bg="#8e1f22", glow="#ffcf5a", w=4.2, h=0.8, z=3.4, size=26, px=512),
                    dict(text="EVENTHAUS LANGSTRASSE", fg="#e9e9e9", bg="#101214", w=5.0, h=0.5, z=3.4, size=18, px=512, du=7.0)])),
 "blackout": ("Blackout Dienerstrasse 45", ["ID_BB8739C2"], "Dienerstrasse 45", dict(wall="#d9935f", frame="#f0e8d8", eg_h=4.0, eg_col="#1c1c1c", base_col="#6a6a66",
             cornice=("#e8d8c0", 0.3, 0.4), roof=("hip", "#7a5448", 4.0), roof_d=5.0, eave_rise=4.0, seed=208, awning=("#b02d2d", 3.0, 0.9),
             signs=[dict(text="BLACKOUT", fg="#d9b24a", bg="#0d0d0d", glow="#c9a23a", w=3.4, h=0.9, z=3.0, size=28, px=1024)])),
 "milano": ("Pizzeria Milano Militaerstrasse 109", ["ID_94022C80"], "Militärstrasse 109", dict(wall="#a4a8a0", frame="#eef0ec", eg_h=4.2, eg_col="#22302a", base_col="#4a4a46",
             cornice=("#8e918a", 0.3, 0.4), roof=("flat", "#706e6a"), seed=209, awning=("#f4f0e6", 3.0, 0.9),
             signs=[dict(text="MILANO", fg="#ffffff", bg="#c4262e", glow="#ff3a3a", w=3.4, h=0.7, z=3.2, size=28, px=1024)])),
 "sudaka": ("Sudaka Langstrasse", ["ID_78A0007E"], "Langstrasse 119", dict(wall="#d8d8d4", frame="#f4f4f0", eg_h=4.0, eg_col="#6f86a8", base_col="#6f86a8",
             cornice=("#bdbdb8", 0.25, 0.4), roof=("flat", "#707070"), seed=210,
             signs=[dict(text="Sudaka", fg="#2a3fb4", bg="#d8d8d4", w=3.0, h=0.7, z=3.0, size=28, px=1024)])),
 "gotthard": ("Gotthard Langstrasse 63", ["ID_199757B8"], "Langstrasse 63", dict(wall="#c9847a", frame="#f1e8dc", eg_h=4.3, eg_col="#2a2523", base_col="#6a5a52",
             cornice=("#e0cfc0", 0.3, 0.45), roof=("hip", "#7a5448", 4.0), roof_d=5.0, eave_rise=4.0, seed=211, awning=("#4a1f1a", 3.0, 1.0),
             signs=[dict(text="GOTTHARD", fg="#e8dcc4", bg="#2a2320", w=3.6, h=0.6, z=3.4, size=26, px=1024)])),
 "l104": ("Lounge Langstrasse 104", ["ID_5F9364B2"], "Langstrasse 104", dict(wall="#d9a14f", frame="#f1ead8", eg_h=4.3, eg_col="#2a211a", base_col="#6a5a48",
             cornice=("#e8d4a8", 0.3, 0.45), roof=("hip", "#7a4a3a", 4.0), roof_d=5.0, eave_rise=4.0, seed=212,
             signs=[dict(text="LOUNGE", fg="#f4e7c8", bg="#241a14", glow="#ffb84a", w=3.0, h=0.6, z=3.4, size=26, px=1024)])),
 "dien40": ("Dienerstrasse 40 Eckhaus rot", ["ID_717269DD"], "Dienerstrasse 40", dict(wall="#b4372c", frame="#efe6d6", eg_h=4.2, eg_col="#4a1c18", base_col="#5a3a32",
             cornice=("#d9b8a8", 0.3, 0.4), roof=("hip", "#6a4a3e", 4.0), roof_d=5.0, eave_rise=4.0, seed=213, awning=("#1f6d5c", 3.0, 1.0))),
 "negresco": ("Negresco Dienerstrasse 27", ["ID_69D86D04"], "Dienerstrasse 27", dict(wall="#b39a6a", frame="#f1e6d0", eg_h=4.0, eg_col="#2a1c22", base_col="#6a5a44",
             cornice=("#d8c8a0", 0.3, 0.4), roof=("hip", "#6c4a3c", 4.0), roof_d=5.0, eave_rise=4.0, seed=214, arch=True,
             signs=[dict(text="NEGRESCO", fg="#ff5fc8", bg="#1a0c18", glow="#ff2fb0", w=3.0, h=0.6, z=3.4, size=28, px=1024)])),
 "gambrinus": ("Gambrinus Langstrasse 103", ["ID_69165C47"], "Langstrasse 103", dict(wall="#a9b891", frame="#f1efe6", eg_h=4.3, eg_col="#2a2a2c", base_col="#8a867c",
             cornice=("#cfc8b4", 0.3, 0.45), roof=("hip", "#7a5a4c", 4.0), roof_d=5.0, eave_rise=4.0, seed=215,
             signs=[dict(text="GAMBRINUS", fg="#232323", bg="#f0f0ec", w=3.4, h=0.6, z=3.5, size=26, px=1024)])),
 "l20": ("Langstrasse 20 Granit-Eckhaus", ["ID_2B5C569C"], "Langstrasse 20", dict(wall="#3a3a3c", frame="#d9d6cc", eg_h=4.4, eg_col="#1a1a1c", base_col="#2a2a2c",
             cornice=("#585858", 0.3, 0.45), roof=("hip", "#4a4a4e", 4.0), roof_d=5.0, eave_rise=4.0, seed=216)),
 "zw37": ("Zwinglistrasse 37 blaues Eckhaus", ["ID_EC7C43C1"], "Zwinglistrasse 37", dict(wall="#7b93c4", frame="#f1efe6", eg_h=4.3, eg_col="#6a6a68", base_col="#6a6a68",
             cornice=("#d0d4dc", 0.3, 0.4), roof=("hip", "#6c5448", 4.0), roof_d=5.0, eave_rise=4.0, seed=217)),
 "lugano": ("Lugano Bar Langstrasse 108", ["ID_FD5FE5F1"], "Langstrasse 108a", dict(wall="#c4553f", frame="#f1e8da", eg_h=4.2, eg_col="#5a1e18", base_col="#5a3a32",
             cornice=("#e0c8b8", 0.3, 0.4), roof=("hip", "#6a4a3e", 4.0), roof_d=5.0, eave_rise=4.0, seed=218, awning=("#2a2a2a", 3.0, 0.9),
             signs=[dict(text="LUGANO BAR", fg="#f4ead8", bg="#a62a22", glow="#ff4a3a", w=3.6, h=0.6, z=3.4, size=26, px=512),
                    dict(text="KIOSK ASMIN", fg="#ffffff", bg="#1f5fb0", w=3.0, h=0.5, z=3.4, size=22, px=512, du=-5.0)])),
 "strauss": ("Strauss Bar Langstrasse 132", ["ID_02232B8B"], "Langstrasse 132", dict(wall="#d9a050", frame="#efe2c4", eg_h=4.3, eg_col="#3a2a22", base_col="#6e6a66",
             cornice=("#e4d0a0", 0.3, 0.45), roof=("hip", "#7a5040", 4.0), roof_d=5.0, eave_rise=4.0, seed=219,
             signs=[dict(text="STRAUSS", fg="#e8dcc0", bg="#6a2a22", glow="#ff9a4a", w=3.4, h=0.6, z=3.4, size=26, px=1024)])),
}


def build(only=None):
    for k, (title, ids, addr, kw) in S.items():
        if only and k not in only: continue
        kw = {**G, **kw}
        for s in kw.get("signs") or []: s["pref"] = front_of(ids[0], addr)
        try: blockB("langB_" + k, title, ids, **kw)
        except Exception as e: print("FAIL", k, repr(e)[:200])


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "all"
    build(None if a == "all" else a.split(","))
