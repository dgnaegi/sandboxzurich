"""Study area: union of Kreise 3,4,5,9 + 300 m buffer (LV95 metres), helpers for WGS84."""
import json
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parent.parent
KREISE = ROOT / "research" / "kreise_poly_simplified.json"
BUFFER_M = 300
_to_lv = Transformer.from_crs(4326, 2056, always_xy=True).transform
_to_wgs = Transformer.from_crs(2056, 4326, always_xy=True).transform


def area_lv95():
    d = json.load(open(KREISE))
    polys = [transform(_to_lv, Polygon([(lon, lat) for lat, lon in pts])) for pts in d.values()]
    return unary_union(polys).buffer(BUFFER_M).simplify(15)


def area_wgs84():
    return transform(_to_wgs, area_lv95())


def bbox_wgs84():
    """(west, south, east, north)"""
    return area_wgs84().bounds


def bbox_lv95():
    return area_lv95().bounds


def overpass_poly():
    """Overpass poly: string 'lat lon lat lon ...' of the exterior ring (largest polygon)."""
    g = area_wgs84()
    if g.geom_type == "MultiPolygon":
        g = max(g.geoms, key=lambda p: p.area)
    return " ".join(f"{y:.5f} {x:.5f}" for x, y in list(g.exterior.coords)[:-1])


if __name__ == "__main__":
    print("bbox wgs84", bbox_wgs84())
    print("bbox lv95", bbox_lv95())
    print("area km2", area_lv95().area / 1e6, "poly pts", len(overpass_poly().split()) // 2)
