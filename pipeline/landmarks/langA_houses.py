"""Langstrasse Nord (Limmatplatz - Unterfuehrung): eight landmark houses read from Panoramax/Mapillary views (research/langstrasse_A.md).
Colours/signs are estimates from the photos (names as plain text, no logos). swissBUILDINGS3D ids from langA_find.py.
usage: langA_houses.py [name ...]  (default all)"""
import sys
from langA_kit import *

H = {
 "chicago": dict(title="Langstrasse/Neugasse Eckhaus Chicago Bar", ids=["ID_3450F018"], wall="#e2b886", frame="#f2ede0", eg_col="#4a1f1f", eg_h=4.0, awning=("#6b1f1f", 3.0, 1.0),
                 roof=("hip", "#6b4a3a", 4.5), eave_rise=4.5, cols=2, rows=3, fh=3.0, seed=201, signs=[dict(text="CHICAGO BAR", fg="#f1e3c8", bg="#3a1414", w=3.4, h=0.6, z=3.3, size=22, px=512)]),
 "coop": dict(title="Langstrasse/Neugasse Eckhaus gruen (Coop to go)", ids=["ID_5D01EE95"], wall="#a9bfa3", frame="#eef0e6", eg_col="#8e949a", eg_h=4.2, cornice=("#dfe6d8", 0.4, 0.4),
              roof=("hip", "#7a5240", 4.5), eave_rise=4.5, seed=202, signs=[dict(text="Coop to go", fg="#f4f4ee", bg="#6a8a70", w=4.0, h=0.7, z=3.4, size=22, px=512)]),
 "hotel210": dict(title="Langstrasse 210 Hotel Gasthaus (korallrot)", ids=["ID_88EF25D3"], wall="#e0795a", frame="#f4efe4", eg_col="#d9d2c4", eg_h=3.8,
                  roof=("flat", "#8a8780"), seed=203, signs=[dict(text="HOTEL GASTHAUS", fg="#f4f4f0", bg="#2c6e49", w=3.0, h=0.6, z=3.2, size=22, px=512)]),
 "kiosk206": dict(title="Langstrasse 206 terrakottaroter Eckbau", ids=["ID_E9DE647F"], wall="#d56a46", frame="#f2ece0", eg_col="#2a2d33", eg_h=4.0,
                  roof=("flat", "#8a8780"), seed=204, signs=[dict(text="KIOSK  TELECOM", fg="#ffffff", bg="#1f55b0", w=4.0, h=0.7, z=3.3, size=22, px=512)]),
 "cinque": dict(title="Langstrasse 215 graues Eckhaus (Cinque)", ids=["ID_61506631"], wall="#99a2a8", frame="#e8e4da", eg_col="#3a2a2a", eg_h=4.0, awning=("#8b2b24", 3.0, 1.2),
                roof=("hip", "#6a4a3c", 4.5), eave_rise=4.5, seed=205, signs=[dict(text="CINQUE", fg="#f4eee4", bg="#7a1f1f", w=2.6, h=0.6, z=3.2, size=24, px=512)]),
 "meixin": dict(title="Langstrasse/Josefstrasse Eckhaus ocker (MeiXin)", ids=["ID_733195EB"], wall="#e5c79b", frame="#f4efe2", eg_col="#3a3c3f", eg_h=3.9,
                roof=("flat", "#7a766e"), seed=206, signs=[dict(text="MEIXIN", fg="#f0e8d8", bg="#33363a", w=3.0, h=0.6, z=3.2, size=24, px=512)]),
 "werner": dict(title="Langstrasse gelbes Haus (Werners Head Shop)", ids=["ID_8852F416", "ID_6F18A541"], wall="#e8c25a", frame="#4f6b3a", eg_col="#4a3a2a", eg_h=3.6, awning=("#e9a82e", 3.0, 1.1),
                roof=("hip", "#a4543a", 3.5), eave_rise=3.5, seed=207, signs=[dict(text="WERNERS HEAD SHOP", fg="#3a2a10", bg="#f0d890", w=4.0, h=0.55, z=3.0, size=20, px=512)]),
 "burger243": dict(title="Langstrasse 243 ockergelb (Burgermeister)", ids=["ID_1B37268B"], wall="#e8b95a", frame="#f4efe2", eg_col="#1c1c1e", eg_h=4.0,
                   roof=("hip", "#7a5444", 4.5), eave_rise=4.5, seed=208, signs=[dict(text="BURGER MEISTER", fg="#ffffff", bg="#101010", glow="#ffffff", w=3.4, h=0.6, z=3.3, size=22, px=512)]),
}


def build(names=None):
    for k, v in H.items():
        if names and k not in names: continue
        v = dict(v); ids = v.pop("ids"); title = v.pop("title")
        blockA("langA_" + k, title, ids, **v)


if __name__ == "__main__":
    build(sys.argv[1:] or None)
