// Contact sheet: ramp up / deck / ramp down on six bridges -> preview/bridges_v2.jpg  (node tests/bridges_shots.mjs [out.jpg] [base-url])
import { chromium } from 'playwright';
import { execSync } from 'node:child_process';
import fs from 'node:fs';
const out = process.argv[2] ?? '../preview/bridges_v2.jpg', BASE = process.argv[3] ?? 'http://localhost:5173';
const routes = JSON.parse(fs.readFileSync(new URL('../../logs/bridge_routes.json', import.meta.url), 'utf8'));
const pick = [['cars', 'Hardbrücke', 1728], ['cars', 'Duttweilerbrücke'], ['bikes', 'Europabrücke'], ['cars', 'Kornhausbrücke'], ['cars', 'Sihlbrücke', 380], ['cars', 'Hohlstrasse']];
const sel = pick.map(([k, n, len]) => routes.find((r) => r.kind === k && r.name === n && (!len || r.len === len))).filter(Boolean);
const tmp = '/private/tmp/bshots/'; fs.mkdirSync(tmp, { recursive: true });
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await (await b.newContext({ viewport: { width: 480, height: 270 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
await page.goto(`${BASE}/?at=${sel[0].pts[0][0]},${sel[0].pts[0][1]},0&t=14:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
let n = 0;
for (const r of sel) {
  const spots = await page.evaluate(async (pts) => {
    const T = window.sbxTiles, cum = [0];
    for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    const at = (s) => { let i = 1; while (i < cum.length - 1 && cum[i] < s) i++; const t = (s - cum[i - 1]) / (cum[i] - cum[i - 1] || 1); return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * t, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * t]; };
    const L = cum[cum.length - 1], el = [];
    let z = null;
    for (let s = 0; s < L; s += 4) { const [x, y] = at(s); await T.update(x, y); const g = T.ground(x, y); z = z ?? g; const d = T.bridges.heightAt(x, y, z); z = d ?? g; el.push(d == null ? 0 : d - g); }
    const hi = el.map((e, i) => (e > 1.5 ? i : -1)).filter((i) => i >= 0);
    if (!hi.length) return null;
    const a = hi[0] * 4, c = hi[hi.length - 1] * 4, m = el.indexOf(Math.max(...el)) * 4;
    return [Math.max(0, a - 14), m, Math.min(L, c + 14)].map((s) => { const [x, y] = at(s), [x2, y2] = at(Math.min(L, s + 6)); return { x, y, h: Math.atan2(x2 - x, y2 - y) }; });
  }, r.pts);
  if (!spots) { console.log('no deck', r.name); continue; }
  for (const sp of spots) {
    await page.evaluate(async (sp) => { const P = window.sbxPlayer; await window.sbxTiles.update(sp.x, sp.y); P.teleport(sp.x, sp.y, sp.h); P.yaw = sp.h; P.pitch = 0.3; }, sp);
    await page.waitForTimeout(1300);
    await page.screenshot({ path: `${tmp}s${n++}.png` });
  }
}
await b.close();
execSync(`python3 - <<'PY'
from PIL import Image
n=${n}
W=Image.new('RGB',(1440,270*((n+2)//3)))
for i in range(n): W.paste(Image.open('${tmp}s%d.png'%i).resize((480,270)),((i%3)*480,(i//3)*270))
W.save('${out}',quality=80)
PY`);
console.log('wrote', out, n);
