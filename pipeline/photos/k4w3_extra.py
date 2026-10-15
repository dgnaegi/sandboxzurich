"""Commons text search for the k4w3 sites (wraps fetch_v3_extra with research/v3/photos_k4w3.json)."""
import sys
import fetch_v3 as F
import fetch_v3_extra as X
import k4w3_fetch as K   # sets F.META
X.QUERIES = {
    "kaserne": "Kaserne Zürich Kasernenstrasse", "zeughaeuser": "Zeughaus Zürich Kasernenareal",
    "amtshaus_helvetia": "Amtshaus Helvetiaplatz Zürich", "peter_paul": "St. Peter und Paul Kirche in Zürich",
    "sihlpost": "Sihlpost Zürich", "apollo_stauffacher": "Kino Apollo Zürich Stauffacherstrasse",
    "zett_haus": "Zett-Haus Zürich", "bezirksgebaeude": "Bezirksgebäude Zürich Badenerstrasse",
    "schulhaus_hohl": "Schulhaus Hohl Zürich", "schulhaus_feld": "Schulhaus Feld Zürich Feldstrasse",
    "hotel_25hours": "25hours Hotel Langstrasse", "zollhaus": "Zollhaus Zürich Genossenschaft",
    "unia_stauffacher": "Unia Zürich Stauffacher", "kollerhof": "Kollerhof Zürich",
}
sys.argv = ['x'] + sys.argv[1:]
X.main()
