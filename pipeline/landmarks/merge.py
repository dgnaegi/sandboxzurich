"""Merge pipeline/overrides/landmarks_*.json -> web/public/data/landmarks.json (x, y, z, heading, model, name, hide)."""
import glob, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "pipeline", "overrides", "landmarks_*.json"))):
        out += json.load(open(f)).get("landmarks", [])
    json.dump({"landmarks": out}, open(os.path.join(ROOT, "web", "public", "data", "landmarks.json"), "w"), separators=(",", ":"))
    print("landmarks.json:", len(out), "entries")


if __name__ == "__main__":
    main()
