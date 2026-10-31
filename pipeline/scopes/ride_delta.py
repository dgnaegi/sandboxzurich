"""Which bridge rides changed status against the gate baseline: the per-bridge improvement list for the PR text.

  python3 pipeline/scopes/ride_delta.py [logs/bridges_ride_v2c.log] [web/tests/fixtures/bridges_ride_baseline.json]
Prints one line per ride whose status (ok / raw / jump / stuck / fell / crash) differs, plus the rides not in the baseline.
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ORDER = ["ok", "raw", "jump", "crash", "fell", "stuck"]


def status(d):
    if d.get("stuck"):
        return "stuck"
    if d.get("fell"):
        return "fell"
    if d.get("crashes"):
        return "crash"
    if d.get("jumps"):
        return "jump"
    if d.get("rawJumps"):
        return "raw"
    return "ok"


def parse(log):
    out = {}
    for line in open(log):
        m = re.match(r"^(OK|FAIL)\s+(car|bike|foot)\s+(.*?)\s+(\{.*\})\s*$", line.strip())
        if not m:
            continue
        d = json.loads(m.group(4)); name = m.group(3).strip()
        out[(m.group(2), name)] = (status(d), d.get("progress"), d.get("len"))
    return out


def main():
    log = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "logs", "bridges_ride_v2c.log")
    base = json.load(open(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "web", "tests", "fixtures", "bridges_ride_baseline.json")))
    now = parse(log)
    bl = {}
    for key, v in base["rides"].items():
        mode, name, _ = key.split("|", 2)
        bl[(mode, name)] = (v["status"], v.get("progress"), v.get("len"))
    better, worse, new = [], [], []
    for k, (st, pr, ln) in sorted(now.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        if k not in bl:
            new.append(f"- {k[1]} ({k[0]}): {st}, progress {pr} of {ln} m (new route)"); continue
        bst, bpr, bln = bl[k]
        if bst == st and (pr or 0) == (bpr or 0):
            continue
        line = f"- {k[1]} ({k[0]}): {bst} → {st}, progress {bpr} → {pr} of {ln} m"
        (better if ORDER.index(st) < ORDER.index(bst) or (st == bst and (pr or 0) > (bpr or 0)) else worse).append(line)
    print(f"Rides vs baseline {base.get('label', '')} ({base.get('updated', '')}): {len(better)} better, {len(worse)} worse, {len(new)} new")
    for title, rows in (("Better", better), ("Worse", worse), ("New", new)):
        if rows:
            print(f"\n{title}:"); print("\n".join(rows))


if __name__ == "__main__":
    main()
