"""Apply 'everywhere' renames (pipeline/overrides/names.json) to all generated game data: web/public/data/**/*.json and
web/public/tiles/*.json. Idempotent; run after build_testarea.py and after any data generator (see docs/HANDOFF.md, pipeline order).
Usage: .venv/bin/python pipeline/apply_names.py"""
import glob
import json
import re

from config import ROOT

REN = {k: v["name"] for k, v in json.load(open(ROOT / "pipeline" / "overrides" / "names.json"))["everywhere"].items()}
PAT = re.compile(r"(?<![\w-])(" + "|".join(map(re.escape, REN)) + r")(?![\w])")


def main():
    files = glob.glob(str(ROOT / "web/public/data/**/*.json"), recursive=True) + glob.glob(str(ROOT / "web/public/tiles/*.json"))
    changed = hits = 0
    for f in files:
        s = open(f, encoding="utf-8").read()
        t, n = PAT.subn(lambda m: REN[m.group(1)], s)
        if n:
            json.loads(t)  # stays valid JSON
            open(f, "w", encoding="utf-8").write(t)
            changed += 1; hits += n
    print(f"apply_names: {hits} replacements in {changed} of {len(files)} files")


if __name__ == "__main__":
    main()
