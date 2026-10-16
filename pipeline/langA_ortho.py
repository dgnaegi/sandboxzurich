"""High-res SWISSIMAGE (swisstopo OGD, 0.12 m/px) crops around Langstrasse measurement spots -> data/raw/ortho_langstrasse/<name>.jpg (120 m box)."""
import sys, urllib.request, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; D = ROOT / "data/raw/ortho_langstrasse"; D.mkdir(parents=True, exist_ok=True)
OX, OY = 2681400, 1248700
SPOTS = {"limmatplatz": (1105, 25), "heinrich": (1030, -100), "josef": (985, -190), "dienerstr": (868, -440), "hohlstr": (800, -600),
         "militaer": (690, -850), "stauffacher": (625, -1010)}
URL = ("https://wms.geo.admin.ch/?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=ch.swisstopo.swissimage&STYLES=&CRS=EPSG:2056"
       "&BBOX={a},{b},{c},{d}&WIDTH=1000&HEIGHT=1000&FORMAT=image/jpeg")
def get(name, x, y, half=60):
    f = D / f"{name}.jpg"
    if f.exists(): return f
    # WMS 1.3.0 EPSG:2056 axis order = northing,easting
    u = URL.format(a=OX + x - half, b=OY + y - half, c=OX + x + half, d=OY + y + half)
    req = urllib.request.Request(u, headers={"User-Agent": "sandboxzurich-research/1.0"})
    for i in range(6):
        try:
            f.write_bytes(urllib.request.urlopen(req, timeout=120).read()); time.sleep(1); return f
        except Exception as e:
            print("retry", name, e); time.sleep(5 * (i + 1))
    return None
if __name__ == "__main__":
    for n, (x, y) in SPOTS.items(): print(get(n, x, y))
