"""Photo research for Hohlstrasse 291 / Egli-Siedlung / Zuercher Lighthouse (reuses fetch_v3)."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import fetch_v3 as f

def sites():
    S = []
    for sid, n, x, y, r in [("hz_egli", "Egli-Siedlung (Eglistrasse)", -425, -70, 110),
                            ("hz_hohl291", "Hohlstrasse 291-301", -335, -105, 90),
                            ("hz_lighthouse", "Zuercher Lighthouse (Eglistrasse 1)", -408, -22, 55)]:
        la, lo = f.local_ll(x, y)
        S.append((sid, n, "place", la, lo, r))
    return S
f.N_ML = 30
f.sites = sites
f.SITES_OUT = f.ROOT / "research/v3/sites_hz.json"
f.main()
