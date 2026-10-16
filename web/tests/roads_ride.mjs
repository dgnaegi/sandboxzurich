// Ride quality: drive a virtual car at 8 m/s along street axes and measure the vertical acceleration of the
// height the game gives vehicles (tiles.groundAt = hmap minus curb mask). Usage:
//   node tests/roads_ride.mjs <label> [lines.json] [base-url]   -> logs/roads_ride_<label>.json
// lines.json: [{ "name": "...", "pts": [[x,y],[x,y],...] }, ...] (local metres)
import { chromium } from 'playwright';
import fs from 'node:fs';

const label = process.argv[2] ?? 'now';
const lines = JSON.parse(fs.readFileSync(process.argv[3] ?? '../logs/roads_ride_lines.json', 'utf8'));
const BASE = process.argv[4] ?? 'http://localhost:5173';
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await (await browser.newContext({ viewport: { width: 640, height: 360 } })).newPage();
const [sx, sy] = lines[0].pts[0];
await page.goto(`${BASE}/?at=${sx},${sy},0&t=12:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
const out = [];
for (const L of lines) {
  const [x0, y0] = L.pts[0];
  await page.evaluate(([x, y]) => window.sbxPlayer.teleport(x, y, 0), [x0, y0]);
  await page.evaluate(async ([x, y]) => { await window.sbxTiles.update(x, y); }, [x0, y0]);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(async (pts) => {
    const T = window.sbxTiles, V = 8, DT = 0.125, step = V * DT;
    // sample the axis every 1 m; bridge decks (stepped deck heights are a separate topic) split the ride into ground runs
    const runs = [[]];
    let carry = 0, zp = T.ground(pts[0][0], pts[0][1]);
    for (let i = 0; i + 1 < pts.length; i++) {
      const [ax, ay] = pts[i], [bx, by] = pts[i + 1], len = Math.hypot(bx - ax, by - ay);
      for (let s = carry; s < len; s += step) {
        const x = ax + (bx - ax) * s / len, y = ay + (by - ay) * s / len;
        const dh = T.bridges.heightAt(x, y, zp);
        if (dh != null) { zp = dh; if (runs[runs.length - 1].length) runs.push([]); }
        else { const z = T.ground(x, y); runs[runs.length - 1].push([x, y, z]); zp = z; }
        carry = s + step - len;
      }
    }
    const acc = [], sl = [], at = [];
    for (const r of runs) {
      for (let i = 1; i + 1 < r.length; i++) acc.push((r[i - 1][2] - 2 * r[i][2] + r[i + 1][2]) / (DT * DT));
      for (let i = 1; i < r.length; i++) { sl.push(Math.abs(r[i][2] - r[i - 1][2]) / step); at.push(r[i]); }
    }
    const rms = Math.sqrt(acc.reduce((a, b) => a + b * b, 0) / Math.max(1, acc.length));
    const mx = acc.reduce((a, b) => Math.max(a, Math.abs(b)), 0);
    if (!sl.length) return { at: '-', n: 0, len: 0, rms_az: 0, max_az: 0, max_slope: 0, jolts_gt_1ms2: 0 };
    const im = sl.indexOf(Math.max(...sl));
    return { at: at[im].slice(0, 2).map((v) => Math.round(v)).join(','), n: acc.length, len: acc.length * step, rms_az: rms, max_az: mx, max_slope: Math.max(...sl), jolts_gt_1ms2: acc.filter((a) => Math.abs(a) > 1).length };
  }, L.pts);
  out.push({ name: L.name, ...r });
  console.log(label, L.name, JSON.stringify(Object.fromEntries(Object.entries(r).map(([k, v]) => [k, typeof v === 'number' ? +v.toFixed(2) : v]))));
}
fs.writeFileSync(`../logs/roads_ride_${label}.json`, JSON.stringify(out, null, 1));
await browser.close();
