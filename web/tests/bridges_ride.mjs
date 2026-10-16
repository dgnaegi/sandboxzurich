// Bridge ride quality: drive the real player car / ride the real bike / walk over every bridge route (pipeline/bridge_routes.py)
// with a deterministic 60 Hz loop (main loop paused) and measure vertical jumps, stalls, falls and rail hits.
//   node tests/bridges_ride.mjs [label=now] [filter-substring] [modes=car,bike,foot] [base-url]
// Fails (exit code 1) if any route has a jump > 0.1 m/frame, a stall, a fall or a crash.
import { chromium } from 'playwright';
import fs from 'node:fs';

const label = process.argv[2] ?? 'now', filt = process.argv[3] ?? '', modes = (process.argv[4] ?? 'car,bike,foot').split(',');
const BASE = process.argv[5] ?? 'http://localhost:5173';
const routes = JSON.parse(fs.readFileSync(new URL('../../logs/bridge_routes.json', import.meta.url), 'utf8'))
  .filter((r) => !filt || r.name.includes(filt) || `${Math.round(r.pts[0][0])}` === filt);
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await (await browser.newContext({ viewport: { width: 640, height: 360 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
await page.goto(`${BASE}/?at=785,-635,0.37&t=12:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
await page.waitForTimeout(1500);

// get into a parked car once (E), then freeze the main loop (open map) so only the test loop moves things
await page.evaluate(() => {
  const p = window.sbxPlayer, list = window.sbxParked.near(p.x, p.y, 120).sort((a, b) => Math.hypot(a.x - p.x, a.y - p.y) - Math.hypot(b.x - p.x, b.y - p.y));
  const s = list.find((c) => !window.sbxBikes.nearest(c.x, c.y, 9)) ?? list[0]; p.teleport(s.x + Math.cos(s.h) * 2.4, s.y - Math.sin(s.h) * 2.4, 0);
});
await page.waitForTimeout(300);
await page.keyboard.press('KeyE');
await page.waitForFunction(() => !!window.sbxPlayer.driving, null, { timeout: 8000 });
await page.evaluate(() => { window.sbxMap.open = true; });

const SIM = async ({ route, mode }) => {
  const P = window.sbxPlayer, T = window.sbxTiles, cam = window.sbxCamera;
  const actions = window.sbxActions;
  let pts = route.pts;
  { // keep the longest run inside the playable area (fence at the map border)
    const dense = []; for (let i = 0; i + 1 < pts.length; i++) { const n = Math.ceil(Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) / 2); for (let k = 0; k < n; k++) dense.push([pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k / n, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k / n]); }
    dense.push(pts[pts.length - 1]);
    let best = [0, 0], st = -1;
    dense.forEach((q, i) => { const ok = P.tiles.inPlay(q[0], q[1]); if (ok && st < 0) st = i; if ((!ok || i === dense.length - 1) && st >= 0) { const en = ok ? i : i - 1; if (en - st > best[1] - best[0]) best = [st, en]; st = -1; } });
    pts = dense.slice(best[0] + 3, Math.max(best[0] + 5, best[1] - 3));
  }
  const cum = [0];
  for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const L = cum[cum.length - 1];
  const at = (s) => { s = Math.max(0, Math.min(L, s)); let i = 1; while (i < cum.length - 1 && cum[i] < s) i++; const t = (s - cum[i - 1]) / (cum[i] - cum[i - 1] || 1); return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * t, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * t]; };
  const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
  const [x0, y0] = pts[0], [x1, y1] = at(6), h0 = Math.atan2(x1 - x0, y1 - y0);
  const car = P.driving;
  if (mode === 'car') {
    if (!car) throw new Error('no car');
    car.x = x0; car.y = y0; car.h = h0; car.vx = car.vy = car.speed = 0; car.damage = 0; car.dead = false;
  } else {
    if (P.driving) { /* leave the car: detach */ P.driving = null; P.body.root.visible = true; }
    if (mode === 'bike' && !P.riding) {
      const s = window.sbxBikes.slots.find((q) => !q.taken) ?? window.sbxBikes.slots[0];
      P.mount({ ...s, color: s.color });
    }
    if (mode === 'foot' && P.riding) { P.riding = null; P.rig.hide(); }
  }
  await T.update(x0, y0);
  if (mode !== 'car') { P.teleport(x0, y0, h0); P.heading = h0; P.z = T.groundAt(x0, y0, T.ground(x0, y0)); }
  else { car.z = T.groundAt(x0, y0, T.ground(x0, y0)); P.x = x0; P.y = y0; }
  let crashes = 0; if (car) car.onCrash = (c) => { if (onDeck(car)) { crashes++; r.crashAt = r.crashAt || `${c.px.toFixed(1)},${c.py.toFixed(1)} n=${c.nx.toFixed(2)},${c.ny.toFixed(2)} v=${c.strength.toFixed(1)} car=${car.x.toFixed(1)},${car.y.toFixed(1)} z=${car.z.toFixed(2)}`; } else r.crashOff = (r.crashOff || 0) + 1; };
  const ent = () => (mode === 'car' ? car : P);
  const dt = 1 / 60; P.fallT = 0;
  const onDeck = (e) => T.bridges.heightAt(e.x, e.y, e.z, 2.5) !== null;
  let dkPrev = false, s = 0, idx = 0, zPrev = ent().z, gPrev = T.groundAt(x0, y0, ent().z), frames = 0, lastS = 0, lastProg = 0;
  const r = { jumps: 0, maxJump: 0, rawJumps: 0, maxRaw: 0, stuck: false, fell: false, crashes: 0, off: 0, maxOff: 0, vmax: 0, zmax: -1e9, at: '' };
  const maxFrames = Math.ceil((L / (mode === 'car' ? 7 : mode === 'bike' ? 4.5 : 3)) * 60) + 600;
  while (frames < maxFrames) {
    const e = ent();
    // progress: closest point ahead within +-30 m of last s
    let best = 1e9, bs = s;
    for (let q = Math.max(0, s - 5); q <= Math.min(L, s + 40); q += 1) { const [px, py] = at(q); const d = Math.hypot(px - e.x, py - e.y); if (d < best) { best = d; bs = q; } }
    s = bs;
    if (s > L - 6) break;
    const look = mode === 'car' ? 5 + 0.7 * Math.abs(car.speed) : mode === 'bike' ? 4 + 0.5 * Math.abs(P.speed) : 3;
    const [tx, ty] = at(s + look), want = Math.atan2(tx - e.x, ty - e.y);
    const hd = mode === 'car' ? car.h : P.heading, err = wrap(want - hd);
    if (mode === 'car') {
      const vt = Math.abs(err) > 0.5 ? 6 : 11;
      car.update(dt, { throttle: Math.max(-1, Math.min(1, (vt - car.speed) * 0.6)), steer: Math.max(-1, Math.min(1, err * 1.4)), turbo: false }, null, () => []);
      P.x = car.x; P.y = car.y; P.z = car.z;
    } else if (mode === 'bike') {
      actions.move.x = Math.max(-1, Math.min(1, err * 2)); actions.move.y = 1; actions.run = false; actions.kb.x = actions.kb.y = 0;
      P.update(dt, cam);
    } else {
      P.yaw = want; actions.move.x = 0; actions.move.y = 1; actions.run = true; actions.kb.x = actions.kb.y = 0;
      P.update(dt, cam);
      if (Math.abs(P.yaw - want) > 1) P.yaw = want;
    }
    frames++;
    const z = e.z, g = T.groundAt(e.x, e.y, z);
    const dz = Math.abs(z - zPrev), dg = Math.abs(g - gPrev);
    if (dz > 0.1) { r.jumps++; if (dz > r.maxJump) { r.maxJump = dz; r.at = `${e.x.toFixed(0)},${e.y.toFixed(0)}`; } }
    const dkNow = T.bridges.heightAt(e.x, e.y, z) !== null; if (dg > 0.1 && (dkNow || dkPrev)) { if (!r.detail) r.detail = JSON.stringify({ x: +e.x.toFixed(1), y: +e.y.toFixed(1), z: +z.toFixed(2), g: +g.toFixed(2), gPrev: +gPrev.toFixed(2), terrain: +T.ground(e.x, e.y).toFixed(2), deck: T.bridges.heightAt(e.x, e.y, z), deckPrevZ: T.bridges.heightAt(e.x, e.y, gPrev) }); r.rawJumps++; r.maxRaw = Math.max(r.maxRaw, dg); if (!r.atRaw || dg > r.maxRaw - 1e-9) r.atRaw = `${e.x.toFixed(0)},${e.y.toFixed(0)}`; }
    if (z < g - 1.0 || z < zPrev - 0.9) r.fell = true;
    r.vmax = Math.max(r.vmax, Math.abs(e.speed ?? 0)); r.zmax = Math.max(r.zmax, z);
    r.maxOff = Math.max(r.maxOff, best); if (best > 6) r.off++;
    zPrev = z; gPrev = g; dkPrev = dkNow;
    if (frames % 45 === 0) (r.trace ??= []).push(`${s.toFixed(0)}:${z.toFixed(1)}/${T.ground(e.x, e.y).toFixed(1)}/${dkNow ? 'D' : '-'}`);
    if (mode !== 'car' && P.fallT > 0) { if (onDeck(e)) r.crashes++; else r.crashOff = (r.crashOff || 0) + 1; r.at = `${e.x.toFixed(0)},${e.y.toFixed(0)}`; break; }
    if (frames % 150 === 0) { // stall check + stream tiles
      if (s - lastProg < 0.8 && frames > 400) { r.stuck = onDeck(e) || !r.crashOff; r.stuckOff = !r.stuck; r.at = r.at || `${e.x.toFixed(0)},${e.y.toFixed(0)}`; break; }
      lastProg = s;
      await T.update(e.x, e.y);
    }
  }
  actions.move.x = actions.move.y = 0; actions.run = false;
  r.crashes += crashes; r.len = Math.round(L); r.progress = Math.round(s); if (frames >= maxFrames && !r.crashOff) r.stuck = true;
  return r;
};

const out = [];
const f2 = (v) => (typeof v === 'number' ? +v.toFixed(2) : v);
let bad = 0;
for (const mode of modes) {
  if (mode === 'bike' || mode === 'foot') await page.evaluate(() => {}); // car -> player switch handled in SIM
  for (const route of routes) {
    if (mode === 'car' && route.kind !== 'cars') continue;
    if (mode !== 'car' && route.kind !== 'bikes') continue;
    let r;
    try { r = await page.evaluate(SIM, { route, mode }); } catch (e) { r = { error: String(e).slice(0, 120) }; }
    const fail = r.error || r.jumps || r.rawJumps || r.stuck || r.fell || r.crashes;
    if (fail) bad++;
    out.push({ mode, name: route.name, start: route.pts[0], ...r });
    if (!process.env.TRACE) delete r.trace;
    console.log(fail ? 'FAIL' : 'OK  ', mode, route.name.padEnd(24), JSON.stringify(Object.fromEntries(Object.entries(r).map(([k, v]) => [k, f2(v)]))));
  }
}
fs.writeFileSync(new URL(`../../logs/bridges_ride_${label}.json`, import.meta.url), JSON.stringify(out, null, 1));
const sum = (k) => out.reduce((a, b) => a + (b[k] || 0), 0);
console.log(`SUMMARY ${label}: ${out.length} rides, ${bad} with problems; jump frames ${sum('jumps')} (max ${Math.max(0, ...out.map((o) => o.maxJump || 0)).toFixed(2)} m), raw-height jumps ${sum('rawJumps')} (max ${Math.max(0, ...out.map((o) => o.maxRaw || 0)).toFixed(2)} m), stuck ${out.filter((o) => o.stuck).length}, fell ${out.filter((o) => o.fell).length}, crashes ${sum('crashes')}`);
if (bad) process.exitCode = 1;
await browser.close();
