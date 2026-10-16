"""Contact sheets wave 5 (research/v3/photos_k4w5.json). Usage: python sheet_k4w5.py [id,id]"""
import contact_sheet_v3 as C
C.META = C.ROOT / "research" / "v3" / "photos_k4w5.json"
if __name__ == "__main__":
    C.main()
