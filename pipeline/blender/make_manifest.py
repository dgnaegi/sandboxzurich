import json, os
R = "/Users/danielgnagi/sandboxzurich"; out = []
SPD = {"child": 0.8, "young": 1.0, "mid": 0.95, "old": 0.6}   # walk-speed hint (multiplier on the game's base walk speed)
for fid in ["player"] + [f"npc_{i:02d}" for i in range(40)]:
    m = json.load(open(f"{R}/data/cache/humans/{fid}.json"))
    e = dict(id=fid, file=f"{fid}.glb", role="player" if fid == "player" else "npc", sex=m["sex"], age=m["age"], height=m.get("height"),
             walk_speed=SPD.get(m["age"], 1.0), anims=["idle", "walk", "run"] + ([] if fid == "player" else ["walk_slow", "stand_phone"]))
    if m.get("props"): e["props"] = m["props"]
    if m["age"] == "child": e["needs_adult"] = True
    out.append(e)
json.dump(out, open(f"{R}/web/public/models/humans/manifest.json", "w"), indent=1)
print("manifest", len(out))
