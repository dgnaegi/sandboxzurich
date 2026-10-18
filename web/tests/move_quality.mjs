// move2: walking past poles/signs (circle colliders) must slide, not stick; also reports steer/stop numbers. Usage: node tests/move_quality.mjs [base]
import { chromium } from 'playwright';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const ok = (c, m) => { console.log(c ? 'OK  ' : 'FAIL', m); if (!c) process.exitCode = 1; };
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
const routes = [[785, -635], [731, -602], [800, -760]];
let stuck = 0, total = 0;
for (const [rx, ry] of (process.env.SKIP_POLES ? [] : routes)) {
  const page = await (await browser.newContext({ viewport: { width: 800, height: 450 } })).newPage();
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  await page.goto(`${BASE}/?at=${rx},${ry},0&t=12:00&nopost`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
  await page.waitForTimeout(2000);
  const poles = await page.evaluate(() => {
    const p = window.sbxPlayer, t = window.sbxTiles, out = []; if (!t) return [window.sbxReady, Object.keys(window).filter(k=>k.startsWith("sbx")).join()];
    for (const l of t.colliders.circles.values()) for (const c of l) {
      if (Math.hypot(c[0] - p.x, c[1] - p.y) < 90 && c[2] < 0.5) out.push(c);
    }
    return out.slice(0, 12);
  });
  for (const c of poles) {
    // approach each pole head-on (0.1 m off-centre) from the south, walk north for 2.5 s
    const r = await page.evaluate(async (c) => {
      const p = window.sbxPlayer, t = window.sbxTiles;
      if (t.colliders.inside(c[0], c[1] - 3) || t.colliders.inside(c[0], c[1] + 3)) return null;
      p.teleport(c[0] + 0.1, c[1] - 3, 0); p.yaw = 0;
      return { y0: p.y };
    }, c);
    if (!r) continue;
    await page.keyboard.down('KeyW');
    await page.waitForTimeout(4000);
    await page.keyboard.up('KeyW');
    const y1 = await page.evaluate(() => window.sbxPlayer.y);
    total++;
    const passed = y1 > c[1] + 0.5; if (total < 4) console.log("pole", c.map((v) => v.toFixed(2)).join(), "y0", r.y0.toFixed(2), "y1", y1.toFixed(2));
    if (!passed) stuck++;
  }
  await page.context().close();
}
if (!process.env.SKIP_POLES) ok(total > 0, `tested ${total} poles on ${routes.length} routes`);
if (!process.env.SKIP_POLES) ok(stuck <= Math.floor(total * 0.1), `stuck at poles: ${stuck}/${total}`);

// ---- car: braking distance at 30/50 km/h, rail-bed smoothness, stuck count -----------------------------------
const page = await (await browser.newContext({ viewport: { width: 800, height: 450 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
await page.goto(`${BASE}/?at=785,-635,0.37&t=12:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
await page.waitForTimeout(1500);
await page.evaluate(() => {
  const p = window.sbxPlayer, list = window.sbxParked.near(p.x, p.y, 120).sort((a, b) => Math.hypot(a.x - p.x, a.y - p.y) - Math.hypot(b.x - p.x, b.y - p.y)), l = list.find((c) => !window.sbxBikes.nearest(c.x, c.y, 9)) ?? list[0];
  p.teleport(l.x + Math.cos(l.h) * 2.4, l.y - Math.sin(l.h) * 2.4, 0);
});
await page.waitForTimeout(400);
await page.keyboard.press('KeyE');
await page.waitForFunction(() => !!window.sbxPlayer.driving, null, { timeout: 8000 }).catch(() => {});
ok(await page.evaluate(() => !!window.sbxPlayer.driving), 'in car');
// free straight: scan headings/positions around for 70 m without footprint
const line = await page.evaluate(() => {
  const c = window.sbxPlayer.driving, col = window.sbxTiles.colliders;
  for (let r = 0; r < 300; r += 15) for (let a = 0; a < 6.28; a += 0.5) for (let h = 0; h < 6.28; h += 0.4) {
    const x = c.x + Math.cos(a) * r, y = c.y + Math.sin(a) * r;
    if (col.freeFraction(x, y, x + Math.sin(h) * 90, y + Math.cos(h) * 90, 45) === 1 && !col.inside(x, y)) return { x, y, h };
  }
  return null;
});
ok(!!line, `free straight ${JSON.stringify(line)}`);
if (line) for (const kmh of [30, 50]) {
  await page.evaluate(({ x, y, h, v }) => { const c = window.sbxPlayer.driving; c.x = x; c.y = y; c.h = h; c.speed = v; c.vx = Math.sin(h) * v; c.vy = Math.cos(h) * v; c.steer = 0; }, { ...line, v: kmh / 3.6 });
  await page.keyboard.down('KeyS');
  const t0 = Date.now(); let st;
  for (;;) {
    st = await page.evaluate(() => { const c = window.sbxPlayer.driving; return { x: c.x, y: c.y, v: c.speed }; });
    if (Math.abs(st.v) < 0.3 || Date.now() - t0 > 6000) break;
    await page.waitForTimeout(40);
  }
  await page.keyboard.up('KeyS');
  const d = Math.hypot(st.x - line.x, st.y - line.y);
  console.log(`INFO brake ${kmh} km/h: ${d.toFixed(1)} m (ideal at 7 m/s^2: ${((kmh / 3.6) ** 2 / 14).toFixed(1)} m)`);
  ok(d < (kmh / 3.6) ** 2 / 14 * 2.2 + 3, `braking ${kmh} km/h in ${d.toFixed(1)} m`);
  await page.waitForTimeout(300);
}
// rail bed: drive across railway land at 12 m/s, sample z / pitch each frame, report jitter (RMS of 2nd difference)
const rail = await page.evaluate(async () => {
  const z = (await (await fetch('/data/railzone.json')).json()).zones;
  const inR = (x, y) => z.some((q) => x >= q.b[0] && x <= q.b[2] && y >= q.b[1] && y <= q.b[3] && q.r.reduce((n, r) => { let c = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const [xi, yi] = r[i], [xj, yj] = r[j]; if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c; } return n + (c ? 1 : 0); }, 0) & 1);
  const col = window.sbxTiles.colliders;
  for (const q of z) for (let x = q.b[0]; x < q.b[2]; x += 7) for (let y = q.b[1]; y < q.b[3]; y += 7) {
    if (!window.sbxTiles.inPlay(x, y) || !inR(x, y)) continue;
    for (let h = 0; h < 3.15; h += 0.3) { const ok2 = [0, 10, 20, 30, 40, 50, 60].every((d) => window.sbxTiles.inPlay(x + Math.sin(h) * d, y + Math.cos(h) * d) && inR(x + Math.sin(h) * d, y + Math.cos(h) * d) && !col.inside(x + Math.sin(h) * d, y + Math.cos(h) * d)); if (ok2 && col.circleAhead(x, y, Math.sin(h), Math.cos(h), 60, 2.5) === Infinity && col.freeFraction(x, y, x + Math.sin(h) * 60, y + Math.cos(h) * 60, 60) === 1 && col.freeFraction(x + 3, y, x + 3 + Math.sin(h) * 60, y + Math.cos(h) * 60, 60) === 1) return { x, y, h }; }
  }
  return null;
});
console.log('INFO rail start', JSON.stringify(rail));
if (rail) {
  await page.evaluate(({ x, y, h }) => { const p = window.sbxPlayer, c = p.driving; c.x = x; c.y = y; c.h = h; p.x = x; p.y = y; c.vx = c.vy = 0; c.speed = 10; c.vx = Math.sin(h) * 10; c.vy = Math.cos(h) * 10; c.steer = 0; p.yaw = h;
    window.__s = []; const f = () => { if (!window.__s) return; window.__s.push([c.z, c.pitch, c.roll, c.speed, c.x, c.y]); requestAnimationFrame(f); }; f(); }, rail);
  await page.waitForTimeout(2500);
  await page.evaluate(({ h }) => { const c = window.sbxPlayer.driving; c.speed = 10; c.vx = Math.sin(h) * 10; c.vy = Math.cos(h) * 10; }, rail);
  await page.keyboard.down('KeyW'); await page.waitForTimeout(3000); await page.keyboard.up('KeyW');
  const m = await page.evaluate(() => { const s = window.__s.slice(40); window.__s = null; const dist = Math.hypot(s[s.length - 1][4] - s[0][4], s[s.length - 1][5] - s[0][5]); const rms = (k) => { const v = []; for (let i = 2; i < s.length; i++) v.push(Math.abs(s[i][k] - 2 * s[i - 1][k] + s[i - 2][k])); v.sort((a, b) => a - b); return v[Math.floor(v.length * 0.9)]; };   // p90 of |2nd difference|
    return { tr: s.filter((_, i) => i % 25 === 0).map((q) => [+q[3].toFixed(1), +q[4].toFixed(1), +q[5].toFixed(1)]), n: s.length, dist, z: rms(0), pitch: rms(1), roll: rms(2), vmin: Math.min(...s.map((q) => q[3])) }; });
  console.log('INFO rail probe', JSON.stringify(await page.evaluate(({ h }) => { const c = window.sbxPlayer.driving, t = window.sbxTiles, o = []; for (let d = 0; d < 40; d += 3) { const x = c.x + Math.sin(h) * d, y = c.y + Math.cos(h) * d, [qx, qy] = t.resolveBody(x, y, 0.6, c.z); o.push([d, +t.ground(x, y).toFixed(2), t.colliders.inside(x, y) ? 1 : 0, +Math.hypot(qx - x, qy - y).toFixed(2), t.inPlay(x, y) ? 1 : 0]); } return { x: c.x, y: c.y, z: c.z, hp: c.damage, circ: (() => { const r = []; for (const l of window.sbxTiles.colliders.circles.values()) for (const q of l) if (Math.hypot(q[0] - c.x, q[1] - c.y) < 5) r.push(q.map((v) => +v.toFixed(2))); return r; })(), pk: window.sbxParked.near(c.x, c.y, 8).length, obs: window.sbxPlayer.drive.hooks.obstacles().filter((b) => Math.hypot(b.x - c.x, b.y - c.y) < 12).map((b) => [+b.x.toFixed(1), +b.y.toFixed(1), b.hl, b.hw, b.id ?? null]), o: o.length }; }, rail)));
  console.log('INFO rail jitter', JSON.stringify(m));
  ok(m.z < 0.02 && m.pitch < 0.01, `rail bed smooth (z2 ${m.z.toFixed(4)}, pitch2 ${m.pitch.toFixed(4)}), slowest ${m.vmin.toFixed(1)} m/s`);
}

// ---- bike: braking distance from 7 m/s, head-on poles (stuck / fall count) -------------------------------------
await page.evaluate(() => { const c = window.sbxPlayer.driving; c.speed = c.vx = c.vy = 0; });
await page.keyboard.press('KeyE');   // leave the car
await page.waitForFunction(() => !window.sbxPlayer.driving, null, { timeout: 8000 }).catch(() => {});
await page.waitForTimeout(500);
await page.evaluate(() => { const p = window.sbxPlayer, b = window.sbxBikes.nearest(p.x, p.y, 300); p.teleport(b.x + 0.6, b.y, 0); });
await page.waitForTimeout(1500);
await page.keyboard.press('KeyE'); await page.waitForTimeout(400);
const mounted = await page.evaluate(() => !!window.sbxPlayer.riding);
ok(mounted, 'on bike');
if (mounted) {
  const bl = line ?? null;
  if (bl) {
    await page.evaluate(({ x, y, h }) => { const p = window.sbxPlayer; p.teleport(x, y, h); p.heading = h; p.speed = 7; }, bl);
    await page.keyboard.down('KeyS');
    const t0 = Date.now(); let st;
    for (;;) { st = await page.evaluate(() => ({ x: window.sbxPlayer.x, y: window.sbxPlayer.y, v: window.sbxPlayer.speed })); if (st.v < 0.3 || Date.now() - t0 > 6000) break; await page.waitForTimeout(40); }
    await page.keyboard.up('KeyS');
    const d = Math.hypot(st.x - bl.x, st.y - bl.y);
    console.log(`INFO bike brake 25 km/h: ${d.toFixed(1)} m`);
    ok(d < 12, `bike braking from 7 m/s in ${d.toFixed(1)} m`);
  }
  const poles = await page.evaluate(() => { const p = window.sbxPlayer, t = window.sbxTiles, out = []; for (const l of t.colliders.circles.values()) for (const c of l) if (Math.hypot(c[0] - p.x, c[1] - p.y) < 120 && c[2] < 0.5 && !t.colliders.inside(c[0], c[1] - 6) && !t.colliders.inside(c[0], c[1] + 4)) out.push(c); return out.slice(0, 10); });
  let bs = 0, falls = 0;
  for (const c of poles) {
    await page.evaluate((c) => { const p = window.sbxPlayer; p.teleport(c[0] + 0.15, c[1] - 6, 0); p.heading = 0; p.speed = 5; p.fallT = 0; window.__f = 0; p.onBikeCrash = () => { window.__f++; }; }, c);
    await page.keyboard.down('KeyW'); await page.waitForTimeout(3000); await page.keyboard.up('KeyW');
    const r = await page.evaluate(() => ({ y: window.sbxPlayer.y, f: window.__f > 0 }));
    if (r.f) falls++;
    if (r.y < c[1] + 0.5 && !r.f) bs++;
  }
  console.log(`INFO bike poles ${poles.length}: stuck ${bs}, falls ${falls}`);
  ok(bs <= Math.floor(poles.length * 0.1), `bike stuck at poles ${bs}/${poles.length}`);
}
await browser.close();
