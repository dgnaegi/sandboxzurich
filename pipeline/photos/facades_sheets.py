"""Contact sheets (12 houses, 4x3, 1600 px wide) from facades_fetch crops -> research/buildings/sheets_v3/NNN.jpg.
Each cell is labelled with address, GWR year and floors. Sheet index in sheets.json (addresses per sheet).
Usage: python facades_sheets.py [--street X] [--skip-done]   (done = addresses already in v3 notes / notes_v3_raw.tsv)"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent.parent
D = ROOT / "research" / "buildings" / "sheets_v3"
RAW = ROOT / "data" / "raw" / "photos" / "facades"
W, H, LAB = 400, 400, 22


def done_set():
    f = D / "notes_v3_raw.tsv"
    s = set()
    if f.exists():
        for ln in f.read_text().splitlines():
            if ln.strip() and not ln.startswith("#"):
                s.add(ln.split("|")[0].strip())
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--street", default="")
    ap.add_argument("--from", dest="start", type=int, default=0)
    a = ap.parse_args()
    cand = json.load(open(D / "candidates.json"))
    def nrkey(v):
        n = "".join(ch for ch in v["nr"] if ch.isdigit())
        return (v["prio"], int(n) if n else 0, v["nr"])
    items = sorted([(k, v) for k, v in cand.items() if v["imgs"] and (not a.street or v["street"] == a.street)], key=lambda kv: nrkey(kv[1]))
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
    except OSError:
        font = ImageFont.load_default()
    sheets = {}
    for i in range(0, len(items), 12):
        grp = items[i:i + 12]
        sheet = Image.new("RGB", (4 * W, 3 * (H + LAB)), (24, 24, 24))
        dr = ImageDraw.Draw(sheet)
        for j, (addr, v) in enumerate(grp):
            x, y = (j % 4) * W, (j // 4) * (H + LAB)
            im = Image.open(RAW / v["imgs"][0]["file"]).resize((W - 2, H - 2))
            sheet.paste(im, (x + 1, y + LAB + 1))
            dr.text((x + 4, y + 2), f"{addr}  {v['year'] or '?'}  {v['floors'] or '?'}G", fill=(255, 230, 0), font=font)
        n = i // 12 + 1
        name = f"{n:03d}.jpg"
        sheet.save(D / name, "JPEG", quality=82)
        sheets[name] = [k for k, _ in grp]
    json.dump(sheets, open(D / "sheets.json", "w"), ensure_ascii=False, indent=0)
    print(len(items), "houses,", len(sheets), "sheets")


if __name__ == "__main__":
    main()
