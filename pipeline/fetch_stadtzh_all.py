"""Fetch remaining Stadt Zürich OGD geo layers (CC0) for the game area via WFS GetFeature (GeoJSON, EPSG:4326).
Only layers not already present in data/raw/stadtzh*, clipped to the LV95 bbox of the WGS84 box 8.44-8.55 E / 47.36-47.40 N.
Usage: .venv/bin/python pipeline/fetch_stadtzh_all.py  (log: logs/fetch_stadtzh_all.log)"""
import json
import re
import sys

import requests

from config import ROOT

OUT = ROOT / "data" / "raw" / "stadtzh_all"
H = {"User-Agent": "gtazurich/0.1 (research)"}
CKAN = "https://data.stadt-zuerich.ch/api/3/action/package_search"
BBOX_LV95 = "2675648,1245944,2683894,1250503,EPSG:2056"  # from WGS84 box, see research/ogd_catalog.md

# (package substring, exact layer name)
SEL = [
    ("verkehrsachsensystem", "vas_basis"),
    ("verkehrsachsensystem", "vas_e_strassenbelag"),
    ("verkehrsachsensystem", "vas_e_verkehrstraeger"),
    ("verkehrsachsensystem", "vas_e_kunstbauten"),
    ("verkehrsachsensystem", "vas_e_steigung"),
    ("signalisierte_geschwindigk", "view_geoserver_tempo_ist"),
    ("signalisierte_geschwindigk", "view_gs_tempo_anpassungen"),
    ("erlaubte_fahrtrichtungen", "view_geoserver_einbahn_ist"),
    ("strassenklassierung", "view_strassenklassierung"),
    ("verkehrsknoten_mit_lichtsignalanlage", "tbl_knoten_p"),
    ("randabschluesse_konzeptpla", "view_randabschluss_konzept"),
    ("schulweguebergaenge", "aer_schulweg_sperrflaeche_a"),
    ("schulweguebergaenge", "poi_schulweg_att"),
    ("schulweguebergaenge", "poi_schulweg_l"),
    ("schulweguebergaenge", "poi_schulweg_view"),
    ("parkplatzverordnung", "parkplatzverordnung_a"),
    ("behindertenparkplaetze", "behindertenparkplaetze_dav_p"),
    ("oeffentlich_zugaengliche_parkhaeuser", "poi_parkhaus_att"),
    ("oeffentlich_zugaengliche_parkhaeuser", "poi_parkhaus_view"),
    ("sharing_zonen", "parkierzonen"),
    ("sharing_zonen", "parkverbotszonen"),
    ("sharing_zonen", "fahrverbotszonen"),
    ("velopruefstrecken", "poi_velopruefstrecken_l"),
    ("velopumpstationen", "velopumpstationen_p"),
    ("standorte_zuerivelo", "view_zuerivelo_publibike"),
    ("standorte_der_verkehrszaeh", "tbl_standort_zaehlung_miv_p"),
    ("standorte_der_automatische", "view_eco_standorte"),
    ("vbz_infrastruktur_ogd", "strecke_schienen"),
    ("vbz_infrastruktur_ogd", "strecke_gleisachse"),
    ("vbz_infrastruktur_ogd", "haltestellen_infosystem"),
    ("vbz_infrastruktur_ogd", "haltestellen_sitzgelegenheit"),
    ("vbz_infrastruktur_ogd", "haltestellen_wartehalle"),
    ("vbz_infrastruktur_ogd", "haltestellen_papierkorb"),
    ("vbz_infrastruktur_ogd", "haltestellen_plakatstelle"),
    ("vbz_infrastruktur_ogd", "haltestellen_haltebalken"),
    ("vbz_infrastruktur_ogd", "haltestellen_ticketautomat"),
    ("vbz_infrastruktur_ogd", "haltestellen_dfi_anzeiger"),
    ("vbz_infrastruktur_ogd", "haltestellen_blindenrillenpl"),
    ("vbz_baustellen", "poi_vbz_baustelle_view"),
    ("gruenflaechen", "gruenflaechen"),
    ("alleenkonzept", "alleenkonzept_baumreihen"),
    ("fachplanung_stadtnatur", "stadtnatur_ogd"),
    ("fachplanung_stadtnatur", "fpsn_vernetzung_ogd"),
    ("fachplanung_hitzeminderung", "fph_aufwertung_ogd"),
    ("fachplanung_hitzeminderung", "fph_hotspots_ogd"),
    ("fachplanung_hitzeminderung", "fph_massnahmengebiete_ogd"),
    ("biotoptypenkartierung", "btk_2020"),
    ("gebiete_mit_gartenstadt", "geb_gartenstadtcharakter_parzellenscharf"),
    ("inventar_der_natur", "nls_stzh_naturschutz"),
    ("inventar_der_natur", "nls_stzh_landschaftsschutz"),
    ("inventar_der_natur", "nls_stzh_aussichtspunkte"),
    ("gebaeudebrueter", "gebaeudebrueter_inventar"),
    ("familiengaerten", "poi_familiengarten_att"),
    ("park", "poi_park_view"),
    ("kunstbauteninventar", "view_kuba_flaechen"),
    ("kunstbauteninventar", "view_kuba_linien"),
    ("denkmalpflege_inventar", "denkmalpflege_inventar_p"),
    ("_gdp__inventar", "gdp_objekte"),
    ("liste_der_informationstafeln", "blaue_tafeln_p"),
    ("auszeichnung_fuer_gute_bau", "agb_objektinventar_a"),
    ("einzelbauten_und_einzelanl", "ee_objekt"),
    ("einzelbauten_und_einzelanl", "ee_pkt_element"),
    ("historische_dorfkerne", "historische_dorfkerne_a"),
    ("hochhaeuser", "alle_hochhaeuser"),
    ("lehrpfade", "fusstouren_punkt"),
    ("lehrpfade", "fusstouren_line"),
    ("stadtspaziergaenge_zueri", "view_zzf_fuss_poi"),
    ("stadtspaziergaenge_zueri", "view_zzf_fusstouren"),
    ("statistische_quartiere", "adm_statistische_quartiere_b"),
    ("statistische_quartiere", "adm_statistische_quartiere_v"),
    ("quartiere__basierend", "adm_verwaltungsquartiere_a"),
    ("quartiere__basierend", "adm_vermbezirke_a"),
    ("kleinquartiere", "kleinquartiere_2026"),
    ("gebietsnamen", "adm_gebietsnamen_a"),
    ("schulkreise", "adm_schulkreise_a"),
    ("aktuelle_tiefbauprojekte", "aer_baustellen_a"),
    ("abgeschlossene_tiefbauproj", "view_abgeschlossene_bauprojekte"),
    ("ahb_hochbauprojekte", "ahb_projekte_ogd"),
    ("oeffentliche_planauflagen", "view_planauflagen_aktuell"),
    ("lbk_laermschutzwand", "lbk_laermschutzwand"),
    ("stadttunnel", "stadttunnel"),
    ("gebaeude_verkippt", "zp_dach"),
    ("bauten___blockmodell", "bauten_blockmodell_max_3d"),
    ("zueri_wie_neu", "zwn_meldungen_p"),
    ("aktuelle_auflistung_von_vi", "liste_videokameras_stadtverw"),
    ("move_and_chill", "view_moveandchill"),
    ("musikschule", "poi_musikschule_view"),
    ("dienstleistungen", "poi_dienstleistung_view"),
    ("bauernhofladen", "poi_bauernhofladen_att"),
    ("hafenanlage", "hafenanlage"),
    ("schiffstandplaetze", "hafenanlage"),
    ("stillgewaesserinventar", "stillgewaesserinventar"),
    ("wasserrettung", "uebergaenge"),
    ("kommunaler_richtplan_verke", "komm_richt_verkehr_l"),
    ("spital", "poi_spital_view"),
]
# 3D city model variants: ground cover, buildings, roads, water (trees and contours excluded)
SEL_3D = ["bodenbedeckung_a", "bebauung_a", "strassennetz_l", "gewaessernetz_l"]


def log(*a):
    print(*a, flush=True)


def wanted(pkg_name, layer):
    for sub, lyr in SEL:
        if sub in pkg_name and lyr == layer:
            return True
    return "3d_stadtmodell" in pkg_name and layer in SEL_3D


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pkgs = []
    start = 0
    while True:
        r = requests.get(CKAN, params={"rows": 1000, "start": start}, headers=H, timeout=120).json()["result"]
        if not r["results"]:
            break
        pkgs += r["results"]
        start += len(r["results"])
        if start >= r["count"]:
            break
    done = set()
    for p in pkgs:
        if not p["name"].startswith("geo_"):
            continue
        wfs = next((x["url"] for x in p["resources"] if x["format"].upper() == "WFS"), None)
        if not wfs:
            continue
        wfs = wfs.split("?")[0]
        cap = requests.get(wfs, params={"SERVICE": "WFS", "REQUEST": "GetCapabilities", "VERSION": "1.1.0"},
                           headers=H, timeout=60).text
        for lyr in re.findall(r"<FeatureType[^>]*>\s*<Name>([^<]+)</Name>", cap):
            if not wanted(p["name"], lyr):
                continue
            dest = OUT / f"{p['name']}__{lyr}.geojson"
            done.add(dest.name)
            if dest.exists():
                log("skip", dest.name)
                continue
            r = requests.get(wfs, params={"SERVICE": "WFS", "VERSION": "1.1.0", "REQUEST": "GetFeature",
                                          "TYPENAME": lyr, "outputFormat": "GeoJSON", "srsName": "EPSG:4326",
                                          "BBOX": BBOX_LV95}, headers=H, timeout=900)
            if r.status_code == 200 and r.text.lstrip().startswith("{"):
                n = len(json.loads(r.text).get("features", []))
                dest.write_text(r.text)
                log("got", dest.name, n, "features", len(r.content) // 1024, "KB")
            else:
                log("FAIL", lyr, r.status_code)
    log("done", len(done), "layers")


if __name__ == "__main__":
    sys.exit(main())
