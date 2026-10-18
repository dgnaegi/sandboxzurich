"""Photo fetch for Le Calvados (Idaplatz 4) via fetch_v3 -> data/raw/photos/calvados/, meta research/calvados_photos.json."""
import sys; sys.path.insert(0, "/Users/danielgnagi/sandboxzurich/pipeline/photos")
import fetch_v3 as F
def sites(): return [("calv", "Le Calvados Idaplatz 4", "place", *F.local_ll(-164, -1108), 70)]
F.sites = sites
F.OUT_DIR = F.ROOT / "data" / "raw" / "photos" / "calvados"
F.META = F.ROOT / "research" / "calvados_photos.json"
F.SITES_OUT = F.ROOT / "research" / "calvados_sites.json"
F.N_ML, F.N_COMMONS, F.N_PANO = 40, 10, 12
if __name__ == "__main__": F.main()
