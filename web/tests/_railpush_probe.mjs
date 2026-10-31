// Probe BridgeIndex.railPush internals at a point: which deck segments are considered and what they would push.
//   node railpush_probe.mjs <x> <y> <z> [rad=1.0] [base=http://localhost:5190]
import { chromium } from 'playwright';
const [x, y, z] = process.argv.slice(2, 5).map(Number), rad = Number(process.argv[5] ?? 1.0), BASE = process.argv[6] ?? 'http://localhost:5190';
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await (await b.newContext({ viewport: { width: 640, height: 360 } })).newPage();
await page.goto(`${BASE}/?at=${x},${y},0,${z}&t=12:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
const out = await page.evaluate(([x, y, z, rad]) => {
  const B = window.sbxTiles.bridges, cell = B.cell, l = B.grid.get(Math.floor(x / cell) + ',' + Math.floor(y / cell)) ?? [];
  const rows = [];
  for (const { d, i } of l) {
    const a = d.p[i], c = d.p[i + 1], dx = c[0] - a[0], dy = c[1] - a[1], len2 = dx * dx + dy * dy;
    const t = ((x - a[0]) * dx + (y - a[1]) * dy) / len2, zc = a[2] + (c[2] - a[2]) * t;
    const len = Math.sqrt(len2), nx = -dy / len, ny = dx / len, lat = (x - (a[0] + dx * t)) * nx + (y - (a[1] + dy * t)) * ny;
    const hw = (lat > 0 ? d.wl?.[i] : d.wr?.[i]) ?? d.w / 2;
    rows.push({ name: d.name, kind: d.kind, w: d.w, i, t: +t.toFixed(2), zc: +zc.toFixed(2), lat: +lat.toFixed(2), hw, ex: +(Math.abs(lat) - (hw + 0.05 - rad)).toFixed(2), el: +(zc - (d.g[i] + (d.g[i + 1] - d.g[i]) * t)).toFixed(2), inT: t >= 0 && t <= 1, inZ: Math.abs(zc - z) <= 1.2 });
  }
  const push = B.railPush(x, y, z, rad), h = B.heightAt(x, y, z, 1.5, 1.0), g = window.sbxTiles.ground(x, y);
  return { push: [+push[0].toFixed(2), +push[1].toFixed(2)], heightAt: h, ground: +g.toFixed(2), rows };
}, [x, y, z, rad]);
console.log(JSON.stringify({ at: [x, y, z], push: out.push, heightAt: out.heightAt, ground: out.ground }));
for (const r of out.rows.filter((r) => r.inT && r.inZ)) console.log(' considered', JSON.stringify(r));
console.log(' other rows in cell:', out.rows.filter((r) => !(r.inT && r.inZ)).map((r) => `${r.kind}/${r.name || '-'} i${r.i} t${r.t} zc${r.zc}`).join(' | '));
await b.close();
