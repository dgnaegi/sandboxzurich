"""SWISSIMAGE crop around the Quartiergarten Hard (swisstopo OGD). Usage: qgh_ortho.py cx cy half_m out.jpg (local metres)"""
import sys, requests
cx, cy, h, out = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
e, n = 2681400 + cx, 1248700 + cy
r = requests.get("https://wms.geo.admin.ch/", params=dict(SERVICE="WMS", VERSION="1.1.1", REQUEST="GetMap", LAYERS="ch.swisstopo.images-swissimage", STYLES="", SRS="EPSG:2056", BBOX=f"{e-h},{n-h},{e+h},{n+h}", WIDTH=1600, HEIGHT=1600, FORMAT="image/jpeg"))
open(out, "wb").write(r.content); print(r.status_code, len(r.content))
