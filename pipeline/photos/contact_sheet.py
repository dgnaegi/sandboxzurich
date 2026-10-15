"""Build a numbered contact sheet (200 px thumbs, 8 columns) from streetscape.json."""
import json
import sys

from PIL import Image, ImageDraw

ROOT = "/Users/danielgnagi/gtazurich"
META = ROOT + "/research/photos/streetscape.json"
OUT = ROOT + "/preview/ref_streetscape.jpg"
COLS, CELL_W, CELL_H, LABEL_H = 8, 200, 150, 16


def main(meta=META, out=OUT):
    imgs = json.load(open(meta, encoding="utf-8"))["images"]
    rows = (len(imgs) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * CELL_W, rows * (CELL_H + LABEL_H)), (30, 30, 30))
    draw = ImageDraw.Draw(sheet)
    for i, rec in enumerate(imgs):
        x = (i % COLS) * CELL_W
        y = (i // COLS) * (CELL_H + LABEL_H)
        try:
            im = Image.open(f"{ROOT}/{rec['local_path']}")
            im.thumbnail((CELL_W - 4, CELL_H - 4))
            sheet.paste(im.convert("RGB"), (x + 2, y + 2))
        except OSError as e:
            print(f"skip {rec['index']}: {e}", file=sys.stderr)
        draw.text((x + 4, y + CELL_H + 1), f"#{rec['index']}", fill=(255, 220, 0))
    sheet.save(out, "JPEG", quality=80)
    print(f"{len(imgs)} images, sheet {sheet.size}")


if __name__ == "__main__":
    main()
