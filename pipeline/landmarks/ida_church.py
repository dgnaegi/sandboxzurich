"""Herz-Jesu-Kirche Wiedikon (Aemtlerstrasse/Idastrasse, Kirchenbau 1921, kath.): hellbeiger Putz, steiles Satteldach (Biberschwanz), schlanker Turm mit Pyramidenhelm.
Grundriss/Hoehen swissBUILDINGS3D 914B47B7; Fassade prozedural. Photos: research/idaplatz.md (Commons 'Zuerich Wiedikon Aussenansicht', #38 in ida_index.json).
-> web/public/models/landmarks/ida_herzjesu.glb + overrides/landmarks_ida.json"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import k93_kirchen as KK, k93_lib as L, k93_kit as K, terrain

OVR = KK.F.ROOT + "/pipeline/overrides/landmarks_ida.json"


def mats(M):
    # Putz warm apricot-beige (Commons #38 in Abendlicht: ~#c9b08c im Licht, nicht cremeweiss); Nave: ein Band kleiner Rundbogenfenster im oberen Drittel
    win = K.tile(4, 1, 72, 128, K.window(wall="#cdb48e", frame="#e9dfc6", glass="#363f48", fw=0.24, fh=0.07, top=0.50, cols=1, rows=2, arch=True, surround="#d9c5a0", sill="#b9a584", noise=6, lit_col=(255, 200, 130)), seed=51, lit=0.1)
    WL = M.mat("wall", rough=0.95, tex=win[0], emis=win[1], repeat=True)
    PL = M.mat("plinth", rough=0.95, tex=K.stone_tex("#8f8777", 0.25, seed=12, rustic=0.15), repeat=True)
    RO = M.mat("roof", rough=0.85, tex=K.tile_roof_tex("#4f3c36", seed=13, var=0.2), repeat=True)
    SP = M.mat("spire", rough=0.7, tex=K.tile_roof_tex("#6a4034", seed=14, var=0.15), repeat=True)
    ck = KK.round_clock(); CKM = M.mat("clock", rough=0.5, tex=ck, emis=ck.point(lambda v: int(v * 0.55)), repeat=False)
    from PIL import Image   # gable triangles + cornice take the same warm Putz (flat trim material rendered cream-white)
    TR = M.mat("trim", rough=0.9, tex=K.noisy(Image.new("RGB", (64, 64), "#d3bd96"), 5, 5, 0.5), repeat=True)
    return (WL, PL, RO, TR, SP, WL, CKM)


if __name__ == "__main__":
    o = (-163.0, -1273.0)
    KK.build("Herz Jesu", [dict(oid="914B47B7", p=o, eave=11.5, rise=7.0, ttop=41.0, spire=9.0, tw=5.4, style="old")], o, "ida_herzjesu.glb", mats)
    z = round(float(KK.H.at(*o)), 2)
    d = json.load(open(OVR)) if os.path.exists(OVR) else {"landmarks": []}
    d["landmarks"] = [e for e in d["landmarks"] if e["name"] != "Herz-Jesu-Kirche Wiedikon"] + [
        {"name": "Herz-Jesu-Kirche Wiedikon", "model": "/models/landmarks/ida_herzjesu.glb", "x": o[0], "y": o[1], "z": z, "heading": 0, "hide": [[-163.1, -1273.0]]}]
    json.dump(d, open(OVR, "w"), indent=1, ensure_ascii=False); print("z", z)
