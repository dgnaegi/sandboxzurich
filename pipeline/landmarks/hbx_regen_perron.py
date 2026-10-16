"""Rebuild hb_perron.glb only (no manifest / merge / decks write)."""
import hb_perron as HP
from hb_kit import *
m, cl = HP.build()
raw = RAWDIR / "hb_perron.glb"; m.write(str(raw)); out = OUTDIR / "hb_perron.glb"
r = common._sp.run([str(ROOT / "web/node_modules/.bin/gltfpack"), "-i", str(raw), "-o", str(out), "-cc", "-kn"], capture_output=True, text=True)
print(r.returncode, m.tri_count(), out.stat().st_size // 1024, "kB")
