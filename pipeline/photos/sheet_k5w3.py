"""Contact sheets for wave 3 / Kreis 5 (uses research/v3/photos_k5w3.json). Usage: python sheet_k5w3.py [id,id]"""
import contact_sheet_v3 as C
C.META = C.ROOT / "research" / "v3" / "photos_k5w3.json"
if __name__ == "__main__":
    C.main()
