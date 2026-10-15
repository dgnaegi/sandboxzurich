"""Specs for npc_16..npc_39 (pure python, shared by gen_cloth_tex.py, build_human.py, make_manifest.py).

Zürich Kreis 4/5 mix: mostly 20-40, some mid/old (65+), 4 children. race = (asian, caucasian, african) blend,
skin = skin-material race. Textures are recoloured per figure (shirt colour + jeans variant) in gen_cloth_tex.py.
"""
C = dict(black=(0.06, 0.06, 0.07), charcoal=(0.2, 0.21, 0.23), white=(0.9, 0.9, 0.88), cream=(0.82, 0.76, 0.62), navy=(0.08, 0.12, 0.28),
         forest=(0.1, 0.24, 0.16), burgundy=(0.38, 0.08, 0.13), mustard=(0.72, 0.52, 0.12), grey=(0.5, 0.5, 0.5), lblue=(0.45, 0.62, 0.8),
         olive=(0.28, 0.3, 0.14), camel=(0.58, 0.42, 0.26), red=(0.68, 0.1, 0.08), pink=(0.78, 0.5, 0.56), teal=(0.08, 0.42, 0.42),
         yellow=(0.88, 0.7, 0.1), orange=(0.8, 0.35, 0.08), lilac=(0.55, 0.45, 0.65), brown=(0.3, 0.2, 0.12), sky=(0.3, 0.55, 0.85))
CAU, AFR, ASI = (0.05, 0.9, 0.05), (0.05, 0.1, 0.85), (0.85, 0.1, 0.05)
MED, SAS, MEA = (0.1, 0.7, 0.2), (0.35, 0.4, 0.25), (0.1, 0.72, 0.18)   # mediterranean, south asian, middle eastern blends
HAIR = dict(black=(0.08, 0.06, 0.05), brown=(0.3, 0.2, 0.12), blond=(0.8, 0.68, 0.45), ginger=(0.6, 0.25, 0.12), grey=(0.62, 0.62, 0.62), white=(0.8, 0.8, 0.8))
# keys: sex, ac (child|young|mid|old), race, skin, seed, outfit, shirt, jeans (natural|dark|black|light), hair, hc, hat, hatc, shoe, age, props
SPECS = [
 dict(sex="f", ac="young", race=CAU, skin="caucasian", outfit="female_casualsuit01", shirt="white", jeans="natural", hair="long01", hc="brown", shoe=5),
 dict(sex="m", ac="young", race=CAU, skin="caucasian", outfit="male_casualsuit05", shirt="olive", jeans="dark", hair="short02", hc="brown", hat="beanie", hatc="black", shoe=3),
 dict(sex="f", ac="young", race=ASI, skin="asian", outfit="female_sportsuit01", shirt="grey", jeans="black", hair="ponytail01", hc="black", shoe=5),
 dict(sex="m", ac="young", race=AFR, skin="african", outfit="male_casualsuit06", shirt="mustard", jeans="black", hair="short04", hc="black", shoe=5),
 dict(sex="f", ac="young", race=AFR, skin="african", outfit="female_casualsuit02", shirt="teal", jeans="light", hair="afro01", hc="black", shoe=5),
 dict(sex="m", ac="young", race=CAU, skin="caucasian", outfit="male_casualsuit01", shirt="charcoal", jeans="dark", hair="short01", hc="blond", shoe=4),
 dict(sex="f", ac="young", race=MED, skin="caucasian", outfit="female_elegantsuit01", shirt="camel", jeans="dark", hair="bob01", hc="black", shoe=4),
 dict(sex="m", ac="young", race=MEA, skin="caucasian", outfit="male_casualsuit04", shirt="navy", jeans="black", hair="short03", hc="black", hat="beanie", hatc="burgundy", shoe=5),
 dict(sex="f", ac="young", race=CAU, skin="caucasian", outfit="male_casualsuit02", shirt="burgundy", jeans="light", hair="ponytail01", hc="ginger", shoe=5),
 dict(sex="m", ac="young", race=ASI, skin="asian", outfit="male_casualsuit06", shirt="grey", jeans="natural", hair="short01", hc="black", hat="cap", hatc="navy", shoe=5),
 dict(sex="f", ac="young", race=SAS, skin="asian", outfit="female_casualsuit01", shirt="pink", jeans="dark", hair="long01", hc="black", shoe=3),
 dict(sex="m", ac="young", race=CAU, skin="caucasian", outfit="male_casualsuit05", shirt="black", jeans="black", hair="short04", hc="brown", shoe=4),
 dict(sex="f", ac="mid", race=CAU, skin="caucasian", outfit="female_elegantsuit01", shirt="charcoal", jeans="dark", hair="bob02", hc="brown", shoe=4),
 dict(sex="m", ac="mid", race=CAU, skin="caucasian", outfit="male_casualsuit01", shirt="camel", jeans="dark", hair="short03", hc="brown", shoe=3),
 dict(sex="f", ac="mid", race=AFR, skin="african", outfit="female_casualsuit01", shirt="mustard", jeans="natural", hair="braid01", hc="black", shoe=5),
 dict(sex="f", ac="old", race=CAU, skin="caucasian", outfit="female_elegantsuit01", shirt="cream", jeans="dark", hair="bob02", hc="grey", shoe=4, props=["cane"]),
 dict(sex="m", ac="old", race=CAU, skin="caucasian", outfit="male_casualsuit01", shirt="navy", jeans="dark", hair=None, hc="grey", hat="cap", hatc="grey", shoe=3, props=["cane"]),
 dict(sex="f", ac="old", race=CAU, skin="caucasian", outfit="female_casualsuit01", shirt="burgundy", jeans="dark", hair="bob01", hc="white", shoe=4, props=["walker"]),
 dict(sex="m", ac="old", race=AFR, skin="african", outfit="male_casualsuit06", shirt="grey", jeans="dark", hair="short01", hc="white", shoe=3),
 dict(sex="m", ac="old", race=CAU, skin="caucasian", outfit="male_casualsuit05", shirt="olive", jeans="dark", hair=None, hc="grey", hat="cap", hatc="brown", shoe=3),
 dict(sex="f", ac="child", race=CAU, skin="caucasian", outfit="female_casualsuit01", shirt="yellow", jeans="natural", hair="ponytail01", hc="blond", shoe=5, age=0.12),
 dict(sex="m", ac="child", race=AFR, skin="african", outfit="male_casualsuit06", shirt="red", jeans="natural", hair="short04", hc="black", shoe=5, age=0.15),
 dict(sex="f", ac="child", race=ASI, skin="asian", outfit="female_casualsuit02", shirt="teal", jeans="natural", hair="braid01", hc="black", shoe=5, age=0.10),
 dict(sex="m", ac="child", race=CAU, skin="caucasian", outfit="male_casualsuit04", shirt="sky", jeans="natural", hair="short02", hc="brown", hat="cap", hatc="red", shoe=5, age=0.17),
]
FIRST = 16
for i, s in enumerate(SPECS): s["seed"] = 300 + i
