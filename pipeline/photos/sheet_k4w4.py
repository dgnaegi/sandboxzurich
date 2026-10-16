"""Contact sheets wave 4 (research/v3/photos_k4w4.json). Usage: python sheet_k4w4.py [id,id]"""
import contact_sheet_v3 as C
C.META = C.ROOT / "research" / "v3" / "photos_k4w4.json"
if __name__ == "__main__":
    C.main()
