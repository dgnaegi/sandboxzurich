// Small picture per conspicuous sweep point -> preview/sweep_tmp/<type>_<k>.jpg ; then pipeline/sweep_sheets.py builds preview/sweep_*.jpg contact sheets.
// node tests/sweep_shots.mjs [BASE] [perType=6] [typesRegex]
import { chromium } from 'playwright';
import { readFileSync, mkdirSync } from 'node:fs';
const BASE = process.argv[2] ?? 'http://localhost:5199', PER = Number(process.argv[3] ?? 6), TYPES = new RegExp(process.argv[4] ?? '.');
const root = new URL('../../', import.meta.url).pathname;
const d = JSON.parse(readFileSync(process.env.SWEEP_JSON ?? root + 'research/sweep.json', 'utf8'));
const by = {};
for (const r of d.results) for (const i of r.issues) (by[i.type] ??= []).push({ ...i, tile: r.name });
for (const m of d.lms ?? []) if (m.floatAbove > 0.4 || m.roadFrac > 0.15) (by.landmark ??= []).push({ x: m.x, y: m.y, n: m.floatAbove * 100 + m.roadFrac * 100, tile: m.name });
for (const a of d.act ?? []) (by[a.type] ??= []).push({ x: a.x, y: a.y, n: 1, tile: a.tile });
mkdirSync(root + 'preview/sweep_tmp', { recursive: true });
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 640, height: 400 } })).newPage();
await p.goto(`${BASE}/?at=0,0,0&t=12:00&nopost`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
for (const [type, list] of Object.entries(by)) {
  if (!TYPES.test(type)) continue;
  const pick = list.sort((a, b) => (b.above ?? b.n ?? 0) - (a.above ?? a.n ?? 0)).filter((q, i, a) => a.findIndex((o) => Math.hypot(o.x - q.x, o.y - q.y) < 30) === i).slice(0, PER);
  let k = 0;
  for (const q of pick) {
    const back = type.startsWith('floating') || type === 'landmark' ? 22 : 12;
    await p.evaluate(async ([x, y, back]) => {
      const T = window.sbxTiles, pl = window.sbxPlayer;
      pl.teleport(x, y - back, 0); await T.update(x, y);
      pl.teleport(x, y - back, 0);
    }, [q.x, q.y, back]);
    await p.waitForTimeout(1800);
    await p.screenshot({ path: `${root}preview/sweep_tmp/${type}_${k++}.jpg`, type: 'jpeg', quality: 70 });
    console.log(type, k - 1, q.tile, q.x, q.y);
  }
}
await b.close();
