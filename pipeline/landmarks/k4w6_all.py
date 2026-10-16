"""Build all wave-6 landmarks in ONE process (building cache is loaded once). Usage: python k4w6_all.py [id,id]"""
import importlib, sys, traceback
IDS = ["limmat", "feld", "kern", "hohl", "sihlfeld", "schuetze", "pfingstweid", "wengi", "ortsmuseum"]
if __name__ == "__main__":
    for i in (sys.argv[1].split(",") if len(sys.argv) > 1 else IDS):
        print("==", i, flush=True)
        try: importlib.import_module(f"k4w6_{i}").build()
        except Exception: traceback.print_exc()
