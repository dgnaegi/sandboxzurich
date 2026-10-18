"""In-game display names for squares (pipeline/overrides/names.json). Stops/stations keep official names."""
import json

from config import ROOT

_SQ = {k: v["name"] for k, v in json.load(open(ROOT / "pipeline" / "overrides" / "names.json"))["squares"].items()}


def square(nm):
    """Display name for a square/place label; unchanged if no override."""
    return _SQ.get(nm, nm)
