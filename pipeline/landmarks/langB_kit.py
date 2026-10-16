"""Shared helpers for Langstrasse Sued landmarks (langB_*.py). Additive on k4w4_kit; registers into pipeline/overrides/landmarks_langB.json.
Photo basis: research/langstrasse_B.md (Panoramax/Mapillary 360 crops, CC BY-SA 4.0, only read for facts: colours, signs, awnings)."""
import json, math
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRB = ROOT / "pipeline" / "overrides" / "landmarks_langB.json"
_ENTR = None


def front_of(prefix, addr):
    """Unit vector from the building centroid to the GWR entrance `addr` (street-facing side) -> sign `pref`."""
    global _ENTR
    if _ENTR is None:
        _ENTR = {e["addr"]: e for e in json.load(open(ROOT / "research/shops_v3/entrances_langB.json"))}
    e = _ENTR.get(addr); b = bid(prefix)
    if not e or not b: return (0, -1)
    dx, dy = e["x"] - b["c"][0], e["y"] - b["c"][1]; n = math.hypot(dx, dy) or 1.0
    return (dx / n, dy / n)


def blockB(*a, **k):
    _k4.OVR4 = OVRB
    return _k4.block_model(*a, **k)
