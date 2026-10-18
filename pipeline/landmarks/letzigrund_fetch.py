"""Photo fetch for Stadion Letzigrund via fetch_v3 -> data/raw/photos/letzigrund/, meta research/letzigrund_photos.json."""
import sys; sys.path.insert(0, "/Users/danielgnagi/sandboxzurich/pipeline/photos")
import fetch_v3 as F
def sites(): return [("letzi", "Stadion Letzigrund", "place", *F.local_ll(-969, -166), 140)]
F.sites = sites
F.OUT_DIR = F.ROOT / "data" / "raw" / "photos" / "letzigrund"
F.META = F.ROOT / "research" / "letzigrund_photos.json"
F.SITES_OUT = F.ROOT / "research" / "letzigrund_sites.json"
F.N_ML, F.N_COMMONS, F.N_PANO = 40, 25, 12
if __name__ == "__main__": F.main()
