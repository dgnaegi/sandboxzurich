// Driving quality: an autopilot drives the real road graph on several streets; crashes / bumps / stuck time are logged with their trigger.
// Usage: node tests/drive_route.mjs [base]   (env ROUTES=name,name to limit; KM=0.6 route length)
import { chromium } from 'playwright';
import fs from 'node:fs';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const roads = JSON.parse(fs.readFileSync(new URL('../public/data/roads.json', import.meta.url)));
const ANCH = { Langstrasse: [842, -484], Badenerstrasse: [-986, -308], Hardstrasse: [189, 347], Seebahnstrasse: [542, -1445], Idaplatz: [-168, -1094], Hohlstrasse: [499, -596], Sihlfeldstrasse: [13, -934], Zurlindenstrasse: [86, -1285] };
const want = (process.env.ROUTES ?? Object.keys(ANCH).join(',')).split(','), LEN = (+process.env.KM || 0.6) * 1000;
const nodes = roads.nodes, cars = roads.cars, outs = nodes.map(() => []);
cars.forEach((e, i) => outs[e.a].push(i));
function route(ax, ay) {
  let best = -1, bd = 1e9;
  cars.forEach((e, i) => { if (e.w < 5.5 || e.p.length < 8) return; for (let k = 0; k < e.p.length; k += 2) { const d = Math.hypot(e.p[k] - ax, e.p[k + 1] - ay); if (d < bd) { bd = d; best = i; } } });
  const pts = []; let len = 0, e = cars[best];
  const seen = new Set();
  while (e && len < LEN && !seen.has(e)) {
    seen.add(e);
    for (let k = 0; k < e.p.length; k += 2) { const q = [e.p[k], e.p[k + 1]]; const l = pts[pts.length - 1]; if (!l || Math.hypot(q[0] - l[0], q[1] - l[1]) > 0.5) { if (l) len += Math.hypot(q[0] - l[0], q[1] - l[1]); pts.push(q); } }
    // continue straight: choose outgoing edge with least heading change
    const p = e.p, n = p.length, h0 = Math.atan2(p[n - 1] - p[n - 3], p[n - 2] - p[n - 4]);
    let nb = null, bt = 0.6;
    for (const j of outs[e.b]) { const f = cars[j]; if (f.b === e.a) continue; const h1 = Math.atan2(f.p[3] - f.p[1], f.p[2] - f.p[0]); const t = Math.abs(Math.atan2(Math.sin(h1 - h0), Math.cos(h1 - h0))); if (t < bt) { bt = t; nb = f; } }
    e = nb;
  }
  // smooth (Chaikin x2) and resample every 2 m
  let q = pts; for (let it = 0; it < 3; it++) { const o = [q[0]]; for (let i = 0; i < q.length - 1; i++) { const a = q[i], b = q[i + 1]; o.push([a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25], [a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75]); } o.push(q[q.length - 1]); q = o; }
  const res = [q[0]]; let acc = 0;
  for (let i = 1; i < q.length; i++) { const d = Math.hypot(q[i][0] - q[i - 1][0], q[i][1] - q[i - 1][1]); acc += d; if (acc >= 2) { res.push(q[i]); acc = 0; } }
  return res;
}
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
let totFwd = 0, totKm = 0, totCrash = 0, totBump = 0; const all = [];
for (const name of want) {
  const [ax, ay] = ANCH[name]; const pts = route(ax, ay);
  const km = pts.reduce((s, p, i) => i ? s + Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) : 0, 0) / 1000;
  const page = await (await browser.newContext({ viewport: { width: 640, height: 360 } })).newPage();
  page.on('console', (m) => { if (process.env.TRACE && m.text().startsWith('t ')) console.log(m.text()); });
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  await page.goto(`${BASE}/?at=${pts[0][0].toFixed(0)},${pts[0][1].toFixed(0)},0&t=12:00&nopost`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
  await page.waitForTimeout(2500);
  const r = await page.evaluate(async ({ pts, off, TRACE }) => {
    const p = window.sbxPlayer, t = window.sbxTiles;
    const list = window.sbxParked.near(p.x, p.y, 400).sort((a, b) => Math.hypot(a.x - p.x, a.y - p.y) - Math.hypot(b.x - p.x, b.y - p.y));
    const s = list[0]; if (!s) return { err: 'no parked car' };
    p.teleport(s.x + Math.cos(s.h) * 2.4, s.y - Math.sin(s.h) * 2.4, 0);
    await new Promise((r) => setTimeout(r, 400));
    window.sbxCarUse.enter({ kind: 'parked', slot: s });
    for (let i = 0; i < 50 && !p.driving; i++) await new Promise((r) => setTimeout(r, 100));
    const c = p.driving; if (!c) return { err: 'not in car' };
    // right-lane offset path
    const path = pts.map((q, i) => { const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)]; const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1; return [q[0] + (dy / l) * off, q[1] - (dx / l) * off]; });
    const h0 = Math.atan2(path[3][0] - path[0][0], path[3][1] - path[0][1]);
    c.x = path[0][0]; c.y = path[0][1]; c.h = h0; c.vx = c.vy = 0; c.speed = 0; c.damage = 0; c.dead = false;
    window.sbxCarUse.tiles ?? 0;
    const ev = [], bumps = [];
    const colls = t.colliders;
    const nearest = (x, y) => { let b = null, bd = 9; for (let i = Math.floor(x / 25) - 1; i <= Math.floor(x / 25) + 1; i++) for (let j = Math.floor(y / 25) - 1; j <= Math.floor(y / 25) + 1; j++) for (const k of colls.circles.get(`${i},${j}`) ?? []) { const d = Math.hypot(k[0] - x, k[1] - y) - k[2]; if (d < bd) { bd = d; b = k; } } return b ? `circle r=${b[2].toFixed(2)}` : null; };
    const describe = (x, y, obb) => obb ? (obb.id !== undefined ? 'traffic car' : obb.ref ? 'parked car' : 'obb') : nearest(x, y) ?? (colls.insideBuilding(x, y) ? 'building' : colls.inside(x, y) ? 'footprint' : (colls.resolve(x, y, 1.2)[0] !== x ? 'building-edge' : 'unknown'));
    const prev = c.onCrash;
    c.onCrash = (k) => { ev.push({ s: +k.strength.toFixed(1), x: +k.px.toFixed(1), y: +k.py.toFixed(1), what: describe(k.px, k.py, k.obb), v: +c.speed.toFixed(1), pd: +Math.min(...pts.map((q) => Math.hypot(q[0] - k.px, q[1] - k.py))).toFixed(1), dev: +Math.min(...path.map((q) => Math.hypot(q[0] - c.x, q[1] - c.y))).toFixed(1) }); prev?.(k); };
    // autopilot
    let rev = 0, recov = 0, tr = 0, tp = 0, idx = 0, dist = 0, stuck = 0, stuckT = 0, lastPos = [c.x, c.y], t0 = performance.now(), maxStuck = 0, lastSp = 0, soft = 0;
    window.sbxActions.kb.x = 0; window.sbxActions.kb.y = 0;
    await new Promise((res) => {
      const tick = () => {
        if (!p.driving) return res();
        // advance idx to the closest point ahead
        let bd = 1e9; for (let i = idx; i < Math.min(path.length, idx + 60); i++) { const d = Math.hypot(path[i][0] - c.x, path[i][1] - c.y); if (d < bd) { bd = d; idx = i; } }
        let j = idx; while (j < path.length - 1 && Math.hypot(path[j][0] - c.x, path[j][1] - c.y) < 9 + Math.abs(c.speed) * 0.9) j++;
        const tx = path[j][0] - c.x, ty = path[j][1] - c.y;
        const e = Math.atan2(Math.sin(Math.atan2(tx, ty) - c.h), Math.cos(Math.atan2(tx, ty) - c.h));
        window.sbxActions.kb.x = Math.max(-1, Math.min(1, e * 1.0));
        const vt = 9 * (1 - Math.min(0.6, Math.abs(e)));
        window.sbxActions.kb.y = Math.max(-1, Math.min(1, (vt - c.speed) * 0.6));
        if (rev > 0) { rev -= 1 / 60; window.sbxActions.kb.y = -1; window.sbxActions.kb.x = -window.sbxActions.kb.x; }
        else if (stuckT > 1.5) { rev = 1.6; stuckT = 0; recov++; }
        // soft bump: sudden speed loss without onCrash
        if (lastSp - c.speed > 1.5 && Math.abs(c.speed) < lastSp) soft++;
        lastSp = c.speed;
        if (Math.hypot(c.x - lastPos[0], c.y - lastPos[1]) < 0.3) { stuckT += 1 / 60; } else { stuckT = 0; lastPos = [c.x, c.y]; }
        maxStuck = Math.max(maxStuck, stuckT);
        if (TRACE && (tr = (tr ?? 0) + 1) % 30 === 0) console.log('t', c.x.toFixed(1), c.y.toFixed(1), 'v', c.speed.toFixed(1), 'idx', idx, 'dev', bd.toFixed(1), 'kb', window.sbxActions.kb.x.toFixed(2), window.sbxActions.kb.y.toFixed(2), 'fps', (1000 / (performance.now() - (tp ?? 0))).toFixed(0), (tp = performance.now(), ''));
        if (idx >= path.length - 3 || performance.now() - t0 > 150000 || recov > 6) return res();
        requestAnimationFrame(tick);
      };
      tick();
    });
    window.sbxActions.kb.x = 0; window.sbxActions.kb.y = 0;
    return { recov, ev, idx, n: path.length, dmg: c.damage, maxStuck, soft, secs: (performance.now() - t0) / 1000 };
  }, { pts, off: 0.8, TRACE: !!process.env.TRACE });
  if (r.err) { console.log(name, 'ERR', r.err); await page.context().close(); continue; }
  const done = pts.slice(0, r.idx).reduce((s, p, i, a) => i ? s + Math.hypot(p[0] - a[i - 1][0], p[1] - a[i - 1][1]) : 0, 0) / 1000;
  totKm += done; totCrash += r.ev.length; totFwd += r.ev.filter((e) => e.v > 0.5).length; totBump += r.soft;
  console.log(`${name}: ${done.toFixed(2)} km of ${km.toFixed(2)} in ${r.secs.toFixed(0)}s, crashes ${r.ev.length} (${(r.ev.length / Math.max(done, .05)).toFixed(1)}/km), soft bumps ${r.soft}, dmg ${r.dmg.toFixed(2)}, recoveries ${r.recov}`);
  const by = {}; for (const e of r.ev) by[e.what] = (by[e.what] ?? 0) + 1; console.log('   by cause', JSON.stringify(by));
  for (const e of r.ev.slice(0, 4)) console.log('   ', JSON.stringify(e));
  all.push({ name, ...r, done });
  await page.context().close();
}
console.log(`FORWARD crashes ${totFwd} (${(totFwd / Math.max(totKm, .05)).toFixed(1)}/km)`);
console.log(`TOTAL ${totKm.toFixed(2)} km, crashes ${totCrash} (${(totCrash / Math.max(totKm, .05)).toFixed(1)}/km), soft bumps ${totBump}`);
fs.writeFileSync(process.env.OUT ?? '/tmp/drive_route.json', JSON.stringify(all));
await browser.close();
