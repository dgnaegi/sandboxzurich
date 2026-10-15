"""D2: extra Bundes- und Kantons-/Stadt-Geodaten fuer das Gebiet Kreis 3/4/5/9.

Quellen (alle OGD bzw. frei nutzbar, Quellenangabe pro Datensatz in research/geo_more.md):
  sbb     SBB Open Data (data.sbb.ch) Perron, Perronoberflaeche, Haltekante, Laermschutzwand/-wall, Bruecken, Bahnuebergaenge
  wfs     Kanton ZH OGD-WFS (maps.zh.ch/wfs/OGDZHWFS), GetFeature mit LV95-BBOX -> GeoJSON
  stadt   Stadt Zuerich OGD (WFS ogd-Host): Lichtsignal-Knoten, Denkmalpflege-Inventar, Laermschutzwand, Alleen, Blockmodell
  stac    geo.admin.ch STAC: swissTLM3D (gpkg.zip, 4.8 GB), Solarkataster Daecher (gpkg.zip), PV-Anlagen (csv.zip)
  clip    Zuschnitt der Downloads auf das Gebiet (pyogrio bbox) -> data/raw/geo_more/clipped/*.gpkg
  pv      PV-/Elektrizitaetsanlagen aus BFE-CSV -> clipped/pv_anlagen.csv

Usage: .venv/bin/python pipeline/fetch_geo_more.py [sbb|wfs|stadt|stac|clip ...]
Skript ist idempotent: vorhandene Dateien werden uebersprungen.
Ablage: data/raw/geo_more/ (nicht im Repo).
"""
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "geo_more"
CLIP = OUT / "clipped"
H = {"User-Agent": "sandboxzurich/0.1 (research)"}
TIMEOUT = 300

# Gebiet (LV95 m) laut Auftrag D2
LV_BBOX = (2678800, 1246900, 2683100, 1249900)
WGS_BBOX = (47.36, 8.44, 47.40, 8.55)  # lat/lon-Reihenfolge fuer SBB-Filter

SBB = "https://data.sbb.ch/api/explore/v2.1/catalog/datasets/"
SBB_SETS = {  # dataset -> Feld mit Geopunkt
    "perron": "geopos",
    "perronoberflache": "geopos",
    "haltestelle-haltekante": "geopos_haltestelle",
    "larmschutzwand": "geopos",
    "larmschutzwall": "geopos",
    "brucken": "geopos",
    "bahnubergang": "geoposition",
    "tunnel": "geopos",
}

WFS = "https://maps.zh.ch/wfs/OGDZHWFS"
# ogd-Layer -> Kurzname. Gewaehlt nach Relevanz fuer Stadtbild/Quests (siehe research/geo_more.md)
WFS_LAYERS = {
    "ogd-0415_stat_gebaeudealter_f": "gebaeudealter",
    "ogd-0272_stat_gebaeude_ha_f": "gebaeude_ha",
    "ogd-0248_giszhpub_en_gebaeude_volumen_ha_f": "gebaeude_volumen",
    "ogd-0368_giszhpub_arv_kaz_denkmalschutzobjekte_p": "denkmal_punkte",
    "ogd-0140_giszhpub_zvv_haltestellen_p": "zvv_haltestellen",
    "ogd-0108_giszhpub_zvv_s_bahn_linien_l": "sbahn_linien",
    "ogd-0597_awel_lh_gruenflaechen_2024_f": "gruenflaechen_2024",
    "ogd-0547_tba_fals_strl_lsw_status_lbk_l": "laermschutzwand_status",
    "ogd-0288_tba_fals_strl_brueckenbereich_f": "strassen_brueckenbereich",
    "ogd-0458_giszhpub_tba_str_inner_ausserorts_l": "kantonsstrassen_innerorts",
    "ogd-0202_giszhpub_tba_velo_mb_sk_netz_l_m": "velonetz_kanton",
}

STADT = {  # WFS-Service (ogd-Host) -> (Layername, Kurzname). Download-Portal (gpkg) ist fuer Skripte gesperrt.
    "Verkehrsknoten_mit_Lichtsignalanlage": ("tbl_knoten_p", "lichtsignal_knoten"),
    "Denkmalpflege_Inventar": ("denkmalpflege_inventar_p", "denkmalpflege_inventar"),
    "LBK_LAERMSCHUTZWAND": ("lbk_laermschutzwand", "laermschutzwand_stadt"),
    "Alleenkonzept": ("alleenkonzept_baumreihen", "alleen"),
    "Bauten___Blockmodell": ("bauten_blockmodell_2d", "bauten_blockmodell"),
}
STADT_WFS = "https://www.ogd.stadt-zuerich.ch/wfs/geoportal/"
CKAN = "https://data.stadt-zuerich.ch/api/3/action/package_show"

STAC = "https://data.geo.admin.ch/"
STAC_FILES = {
    "tlm": "ch.swisstopo.swisstlm3d/swisstlm3d_2026-02/swisstlm3d_2026-02_2056_5728.gpkg.zip",
    "solar": "ch.bfe.solarenergie-eignung-daecher/solarenergie-eignung-daecher/"
             "solarenergie-eignung-daecher_2056_generalized.gpkg.zip",
    "pv": "ch.bfe.elektrizitaetsproduktionsanlagen/elektrizitaetsproduktionsanlagen/"
          "elektrizitaetsproduktionsanlagen_2056.csv.zip",
}


def log(msg):
    print(msg, flush=True)


def download(url, dest, params=None):
    """Stream url to dest (skips if present). Returns dest."""
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 0:
        log(f"  skip {dest.name} (vorhanden)")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, params=params, headers=H, stream=True, timeout=TIMEOUT) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    tmp.rename(dest)
    log(f"  ok {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
    return dest


def fetch_sbb():
    log("SBB Open Data")
    where = "in_bbox({f},{s},{w},{n},{e})".format
    lat0, lon0, lat1, lon1 = WGS_BBOX
    for ds, field in SBB_SETS.items():
        dest = OUT / "sbb" / f"{ds}.geojson"
        if dest.exists():
            log(f"  skip {ds}")
            continue
        r = requests.get(
            f"{SBB}{ds}/exports/geojson",
            params={"where": where(f=field, s=lat0, w=lon0, n=lat1, e=lon1)},
            headers=H, timeout=TIMEOUT,
        )
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        log(f"  ok {ds}: {len(r.json().get('features', []))} Features")


def fetch_wfs():
    log("Kanton ZH OGD-WFS (BBOX LV95)")
    bbox = ",".join(str(v) for v in LV_BBOX) + ",urn:ogc:def:crs:EPSG::2056"
    for layer, short in WFS_LAYERS.items():
        dest = OUT / "wfs" / f"{short}.geojson"
        if dest.exists():
            log(f"  skip {short}")
            continue
        r = requests.get(WFS, params={
            "SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
            "TYPENAMES": "ms:" + layer, "BBOX": bbox, "COUNT": "50000",
            "OUTPUTFORMAT": "application/json",
        }, headers=H, timeout=TIMEOUT)
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        log(f"  ok {short}: {len(r.json().get('features', []))} Features")


def fetch_stadt():
    log("Stadt Zuerich OGD (WFS, LV95-BBOX -> GeoJSON)")
    bbox = ",".join(str(v) for v in LV_BBOX) + ",urn:ogc:def:crs:EPSG::2056"
    for svc, (layer, short) in STADT.items():
        dest = OUT / "stadt" / f"{short}.geojson"
        if dest.exists():
            log(f"  skip {short}")
            continue
        r = requests.get(STADT_WFS + svc, params={
            "SERVICE": "WFS", "VERSION": "1.1.0", "REQUEST": "GetFeature", "TYPENAME": layer,
            "BBOX": bbox, "outputFormat": "GeoJSON", "srsName": "EPSG:2056",
        }, headers=H, timeout=TIMEOUT)
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        log(f"  ok {short}: {len(r.json().get('features', []))} Features")


def fetch_stac():
    log("geo.admin.ch STAC (gross, Download im Hintergrund sinnvoll)")
    for key, rel in STAC_FILES.items():
        download(STAC + rel, OUT / key / Path(rel).name)


def _copy_bbox(src, layer, out):
    """Kopiert die Features einer Layer innerhalb LV_BBOX (pyogrio.raw, ohne geopandas)."""
    import pyogrio.raw as raw

    meta, _fids, geom, fields = raw.read(src, layer=layer, bbox=LV_BBOX)
    n = len(geom)
    if n:
        out.parent.mkdir(parents=True, exist_ok=True)
        raw.write(out, geom, fields, layer=layer, driver="GPKG", geometry_type=meta["geometry_type"],
                  crs=meta["crs"], fields=meta["fields"].tolist(), encoding="UTF-8")
    return n


def clip():
    """Zuschnitt auf das Gebiet; pyogrio liest nur die Bbox (GPKG-Rtree bzw. Zip-Stream)."""
    import pyogrio

    CLIP.mkdir(parents=True, exist_ok=True)
    log("Zuschnitt")
    sol = OUT / "solar" / "solarenergie-eignung-daecher_2056_generalized.gpkg.zip"
    if sol.exists() and not (CLIP / "solar_daecher.gpkg").exists():
        lyr = pyogrio.list_layers(f"/vsizip/{sol}")[0][0]
        n = _copy_bbox(f"/vsizip/{sol}", lyr, CLIP / "solar_daecher.gpkg")
        log(f"  solar_daecher: {n} Dachflaechen ({lyr})")
    tlm = OUT / "tlm" / "swisstlm3d_2026-02_2056_5728.gpkg.zip"
    if tlm.exists():
        layers = [l[0] for l in pyogrio.list_layers(f"/vsizip/{tlm}")]
        log(f"  TLM Layer: {len(layers)}")
        for lyr in layers:
            out = CLIP / f"tlm_{lyr}.gpkg"
            if out.exists():
                continue
            try:
                n = _copy_bbox(f"/vsizip/{tlm}", lyr, out)
            except Exception as e:  # Tabellen ohne Geometrie (z.B. Attribut-Layer) ueberspringen
                log(f"  tlm {lyr}: uebersprungen ({type(e).__name__})")
                continue
            log(f"  tlm {lyr}: {n}")


def clip_pv():
    """PV-/Elektrizitaetsanlagen (BFE) im Gebiet -> clipped/pv_anlagen.csv (de-Kategorien, Leistung, Neigung, Ausrichtung)."""
    import csv
    import io
    import zipfile

    src = OUT / "pv" / "elektrizitaetsproduktionsanlagen_2056.csv.zip"
    if not src.exists():
        return
    z = zipfile.ZipFile(src)

    def rows(name):
        return csv.DictReader(io.TextIOWrapper(z.open(name), encoding="utf-8-sig", errors="replace"))

    cat = {r["Catalogue_id"]: r["de"] for n in ("PlantCategoryCatalogue.csv", "MainCategoryCatalogue.csv")
           for r in rows(n)}
    lv = LV_BBOX
    det = {}
    for r in rows("PlantDetail.csv"):
        det.setdefault(r["ElectricityProductionPlantR"], r)
    out = CLIP / "pv_anlagen.csv"
    CLIP.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["xtf_id", "address", "postcode", "municipality", "egid", "start", "power_kw",
                    "maincat", "plantcat", "x", "y", "inclination", "orientation"])
        for r in rows("ElectricityProductionPlant.csv"):
            if not r["_x"] or not r["_y"]:
                continue
            x, y = float(r["_x"]), float(r["_y"])
            if not (lv[0] <= x <= lv[2] and lv[1] <= y <= lv[3]):
                continue
            d = det.get(r["xtf_id"], {})
            w.writerow([r["xtf_id"], r["Address"], r["PostCode"], r["Municipality"], r["EGID"],
                        r["BeginningOfOperation"], r["TotalPower"], cat.get(r["MainCategory"], ""),
                        cat.get(r["PlantCategory"], ""), x, y, d.get("Inclination", ""),
                        d.get("Orientation", "")])
            n += 1
    log(f"  pv_anlagen.csv: {n} Anlagen")


STEPS = {"sbb": fetch_sbb, "wfs": fetch_wfs, "stadt": fetch_stadt, "stac": fetch_stac, "clip": clip, "pv": clip_pv}

if __name__ == "__main__":
    steps = sys.argv[1:] or list(STEPS)
    for s in steps:
        STEPS[s]()
