"""Review page of the top-down check: every site with a json in data/build/scopes/topcheck/ -> preview/topcheck/index.html
plus one jpg sheet per site (untracked: images stay out of git). Optional preview/topcheck/notes.html is placed after the
sites (session notes, findings explained). topcheck.py calls this after each run.

  python3 pipeline/scopes/topcheck_page.py [--game http://localhost:5191]     (game = dev server the "where" links open)
"""
import html
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
from ramp_sites import site as site_cfg  # noqa: E402

SRC = os.path.join(ROOT, "data", "build", "scopes", "topcheck")
OUT = os.path.join(ROOT, "preview", "topcheck")
KIND = {"interior holes": "hole in the deck", "edge holes": "deck narrower than the bridge", "below LiDAR": "missing surface",
        "steps": "step between slabs", "blocked": "invisible wall", "sink": "sinking / floating"}
SHOWN = 15     # findings per site before the rest is folded


def detail(k, c):
    if k == "interior holes":
        return "ground visible through the deck; " + ("you fall through" if c["walkable"] < 0.5 else "physics still carries you (drawn hole only)")
    if k == "edge holes":
        return f"{c['w']:.1f} m of bridge without deck; " + ("you fall off" if c["walkable"] < 0.5 else "physics still carries you")
    if k == "below LiDAR":
        return f"reality {c['depth']:.1f} m higher here ({c['drawn']})"
    if k == "steps":
        return f"{c['dz']:.2f} m step over {c['len']:.0f} m"
    if k == "blocked":
        return f"body pushed {c['push']:.2f} m inside the deck"
    if k == "sink":
        return f"stand height {c['dz']:+.2f} m against the drawn deck"
    return ""


def table(rows):
    return ("<div class=tw><table><thead><tr><th>id</th><th>what</th><th>size</th><th>where (open in game)</th><th>detail</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table></div>")


def title(site):
    try:
        t = site_cfg(site).get("title", site)
    except SystemExit:
        return site
    return t.split(" (")[0]


def section(site, J, game):
    by = {c["id"]: c for key in ("holes", "below", "steps", "blocked", "sinks") for c in J[key]}
    img = f"{site}.jpg"
    Image.open(os.path.join(SRC, f"{site}.png")).convert("RGB").save(os.path.join(OUT, img), quality=82)
    rows = []
    for k, i in sorted(((k, i) for k, ids in J["gating"].items() for i in ids), key=lambda ki: -by[ki[1]]["m2"]):
        c = by[i]
        size = f"{c['len']:.0f} m" if k == "steps" else f"{c['m2']:.0f} m²"
        rows.append(f"<tr><td class=id>{i}</td><td>{KIND[k]}</td><td class=num>{size}</td>"
                    f"<td class=num><a href=\"{game}/?at={c['x']:.0f},{c['y']:.0f},0\" target=_blank rel=noopener>{c['x']:.0f}, {c['y']:.0f}</a></td>"
                    f"<td>{html.escape(detail(k, c))}</td></tr>")
    notes = []
    rail = [c for c in J["below"] if c["drawn"] == "rail deck too low"]
    if rail:
        notes.append(f"Reported, not counted: rail deck drawn up to {max(c['depth'] for c in rail):.0f} m below the LiDAR bridge surface "
                     f"({sum(c['m2'] for c in rail):.0f} m², rail rows, not ramp rows).")
    if J["unmodelled"]:
        notes.append(f"{len(J['unmodelled'])} cadastre bridge(s) in the box carry no deck at all (footbridges and similar), shown blue, not counted.")
    name, verdict = title(site), J["verdict"]
    counts = " · ".join(f"{len(v)} {KIND[k]}" for k, v in J["gating"].items() if v) or "nothing over the gate"
    chip = (f"<a class=\"chip {verdict.lower()}\" href=\"#{site}\"><span>{html.escape(name)}</span><b>{verdict}</b>"
            f"<small>{len(rows)} findings</small></a>")
    body = f"""
<section id="{site}">
  <header class=sh><h2>{html.escape(name)}</h2><span class="pill {verdict.lower()}">{verdict}</span></header>
  <p class=meta>{counts}. Cadastre bridge covered by drawn deck: {J['av_covered']:.0%}. LiDAR on {J['lidar_share']:.0%} of the traffic area.</p>
  <a class=sheet href="{img}" target=_blank rel=noopener><img src="{img}" alt="{html.escape(name)}: SWISSIMAGE, game from above, findings" loading=lazy></a>
  {''.join(f'<p class=note>{html.escape(x)}</p>' for x in notes)}
  {table(rows[:SHOWN]) if rows else table(['<tr><td colspan=5>No finding over the gate.</td></tr>'])}
  {f'<details><summary>{len(rows) - SHOWN} more findings</summary>{table(rows[SHOWN:])}</details>' if len(rows) > SHOWN else ''}
</section>"""
    return chip, body


def build(game="http://localhost:5191"):
    os.makedirs(OUT, exist_ok=True)
    sites = []
    for f in sorted(os.listdir(SRC)):
        if f.endswith(".json") and os.path.exists(os.path.join(SRC, f[:-5] + ".png")):
            sites.append((f[:-5], json.load(open(os.path.join(SRC, f)))))
    sites.sort(key=lambda sj: (sj[1]["verdict"] != "FAIL", sj[0].startswith("auto_"), sj[0]))
    parts = [section(s, J, game) for s, J in sites]
    nf = os.path.join(OUT, "notes.html")
    notes = open(nf).read() if os.path.exists(nf) else ""
    page = (TEMPLATE.replace("%%CHIPS%%", "".join(p[0] for p in parts)).replace("%%SECTIONS%%", "".join(p[1] for p in parts))
            .replace("%%NOTES%%", notes).replace("%%GAME%%", html.escape(game)))
    out = os.path.join(OUT, "index.html")
    open(out, "w").write(page)
    return out


TEMPLATE = r'''<title>Deck Top Check</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Barlow:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: one reading column; per site a header, the three-panel sheet at full width, then its findings table. */
:root {
  --bg: #f3f4f6; --panel: #ffffff; --fg: #1d232b; --muted: #5d6773; --line: #d9dde3;
  --accent: #0088a8; --fail: #c62f2f; --fail-bg: #fbe7e6; --pass: #23794a; --pass-bg: #e3f3ea;
  --display: "Barlow Condensed", "Arial Narrow", sans-serif; --body: "Barlow", "Helvetica Neue", Arial, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #12161b; --panel: #1a2027; --fg: #e4e8ed; --muted: #98a3b0; --line: #2c343e;
  --accent: #39b6d4; --fail: #ff7a72; --fail-bg: #3a1f20; --pass: #6fd39b; --pass-bg: #18332a; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #12161b; --panel: #1a2027; --fg: #e4e8ed; --muted: #98a3b0; --line: #2c343e;
  --accent: #39b6d4; --fail: #ff7a72; --fail-bg: #3a1f20; --pass: #6fd39b; --pass-bg: #18332a; color-scheme: dark }
body { background: var(--bg); color: var(--fg); font: 400 16px/1.5 var(--body); }
main { max-width: 1180px; margin: 0 auto; padding: 32px 16px 64px; display: grid; gap: 40px; }
h1, h2 { font-family: var(--display); font-weight: 700; letter-spacing: .01em; text-transform: uppercase; text-wrap: balance; margin: 0; line-height: 1.05; }
h1 { font-size: clamp(2rem, 5vw, 3rem); }
h2 { font-size: 1.9rem; }
.lede { max-width: 68ch; color: var(--muted); margin: 8px 0 0; }
.lede b { color: var(--fg); font-weight: 600; }
.chips { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
.chip { display: grid; gap: 2px; padding: 14px 16px; background: var(--panel); border: 1px solid var(--line); border-left: 4px solid var(--line); text-decoration: none; color: var(--fg); }
.chip.fail { border-left-color: var(--fail); } .chip.pass { border-left-color: var(--pass); }
.chip span { font-family: var(--display); font-size: 1.3rem; text-transform: uppercase; font-weight: 600; }
.chip b { font-size: .8rem; letter-spacing: .08em; } .chip.fail b { color: var(--fail); } .chip.pass b { color: var(--pass); }
.chip small { color: var(--muted); font-family: var(--mono); font-size: .8rem; }
.chip:focus-visible, a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: .9rem; color: var(--muted); }
.legend i { display: inline-block; width: 12px; height: 12px; margin-right: 6px; vertical-align: -1px; border: 1px solid rgba(127,127,127,.4); }
section { display: grid; gap: 12px; }
.sh { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
.pill { font-size: .78rem; font-weight: 600; letter-spacing: .08em; padding: 2px 8px; }
.pill.fail { color: var(--fail); background: var(--fail-bg); } .pill.pass { color: var(--pass); background: var(--pass-bg); }
.meta { margin: 0; color: var(--muted); }
.sheet { display: block; background: #141414; border: 1px solid var(--line); }
.sheet img { display: block; width: 100%; height: auto; }
.note { margin: 0; font-size: .92rem; color: var(--muted); }
.tw { overflow-x: auto; background: var(--panel); border: 1px solid var(--line); }
table { border-collapse: collapse; width: 100%; font-size: .93rem; }
th, td { text-align: left; padding: 7px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-weight: 600; color: var(--muted); font-size: .8rem; letter-spacing: .06em; text-transform: uppercase; white-space: nowrap; }
tbody tr:last-child td { border-bottom: 0; }
.id, .num { font-family: var(--mono); font-variant-numeric: tabular-nums; white-space: nowrap; }
.id { font-weight: 500; }
a { color: var(--accent); }
.how { max-width: 72ch; display: grid; gap: 8px; }
.how h2 { font-size: 1.4rem; }
.how p, .how ul { margin: 0; }
.how code { font-family: var(--mono); font-size: .88em; }
details summary { cursor: pointer; color: var(--accent); padding: 6px 0; }
details[open] summary { margin-bottom: 8px; }
</style>
<main>
  <header>
    <h1>Deck top check</h1>
    <p class="lede">The game rendered straight from above, compared with the <b>cadastre bridge outlines</b>, the <b>LiDAR surface</b> and <b>SWISSIMAGE</b>. Each sheet shows SWISSIMAGE, the game from above, and the findings. Links in the tables open the game at that spot (%%GAME%%). Coordinates are game metres.</p>
  </header>
  <nav class="chips" aria-label="Sites">%%CHIPS%%</nav>
  <div class="legend" aria-label="Colours on the findings panel">
    <span><i style="background:#ff2828"></i>hole in the deck</span>
    <span><i style="background:#ff9628"></i>deck narrower than the bridge</span>
    <span><i style="background:#dc006e"></i>missing surface (below LiDAR)</span>
    <span><i style="background:#ff00ff"></i>step between slabs</span>
    <span><i style="background:#ffdc00"></i>invisible wall</span>
    <span><i style="background:#ffffff"></i>sinking / floating</span>
    <span><i style="background:#3caa3c"></i>terrain over the deck</span>
    <span><i style="background:#00dcff"></i>cadastre road bridge outline</span>
    <span><i style="background:#284690"></i>cadastre bridge without deck</span>
    <span><i style="background:#693255"></i>rail deck below LiDAR (not counted)</span>
    <span><i style="background:#00aa96"></i>game above LiDAR (not counted)</span>
  </div>
  %%SECTIONS%%
  %%NOTES%%
  <section class="how">
    <h2>How the check works</h2>
    <p>A headless browser loads the game, renders the site box with an orthographic camera at 0.5 m per pixel and reads back three height images: the drawn deck surface (without parapets and piers), the rail decks, and the tile mesh. At every pixel it also asks the game's own collision code where a body would stand and whether it gets pushed. A site fails on a hole of 1 m² or more inside the deck, a deck at least 1.5 m narrower than the bridge, a surface at least 1.5 m below LiDAR over 4 m², a step run of 2 m, an invisible wall of 1 m², or sinking over 2 m².</p>
    <p>Run it with <code>python3 pipeline/scopes/topcheck.py &lt;site&gt;</code> while the dev server is up. The city table now shows this verdict next to the scorer's, and a scorer PASS no longer stands if the drawn decks fail.</p>
  </section>
</main>
'''


if __name__ == "__main__":
    g = sys.argv[sys.argv.index("--game") + 1] if "--game" in sys.argv else "http://localhost:5191"
    print(build(g))
