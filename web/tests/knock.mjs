// Knock-over objects: a car drives into bins / bollards / racks / sign posts -> they fall (no crash, little speed loss, collider gone, proxy mesh);
// walkers still glide around bins; lamp masts stay hard. Usage: node tests/knock.mjs [base]
import { chromium } from 'playwright';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const ok = (c, m) => { console.log(c ? 'OK  ' : 'FAIL', m); if (!c) process.exitCode = 1; };
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await (await browser.newContext({ viewport: { width: 800, height: 450 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
await page.goto(`${BASE}/?at=785,-635,0.37&t=12:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
await page.waitForTimeout(2500);
const cnt = await page.evaluate(() => {
  const t = window.sbxTiles, p = window.sbxPlayer, o = { k1: 0, k2: 0, mast: 0 };
  for (const l of t.colliders.circles.values()) for (const c of l) if (Math.hypot(c[0] - p.x, c[1] - p.y) < 250) { if (c[3] === 1) o.k1++; else if (c[3] === 2) o.k2++; }
  return o;
});
console.log('knockables within 250 m', JSON.stringify(cnt));
ok(cnt.k1 > 0 && cnt.k2 > 0, 'bins (kind 1) and sign posts/racks/bollards (kind 2) are registered');
// enter a car
await page.evaluate(() => {
  const p = window.sbxPlayer, list = window.sbxParked.near(p.x, p.y, 120).sort((a, b) => Math.hypot(a.x - p.x, a.y - p.y) - Math.hypot(b.x - p.x, b.y - p.y)), l = list.find((c) => !window.sbxBikes.nearest(c.x, c.y, 9)) ?? list[0];
  p.teleport(l.x + Math.cos(l.h) * 2.4, l.y - Math.sin(l.h) * 2.4, 0);
});
await page.waitForTimeout(400);
await page.keyboard.press('KeyE');
await page.waitForFunction(() => !!window.sbxPlayer.driving, null, { timeout: 8000 }).catch(() => {});
ok(await page.evaluate(() => !!window.sbxPlayer.driving), 'in car');
// for each kind: find up to 4 knockables with clear run-up and drive into each at ~8 m/s
const res = await page.evaluate(async () => {
  const t = window.sbxTiles, p = window.sbxPlayer, c = p.driving, col = t.colliders, out = [];
  let crashes = 0; const prev = c.onCrash; c.onCrash = (k) => { crashes++; window.__lastCrash = [+k.px.toFixed(1), +k.py.toFixed(1), !!k.obb, +k.strength.toFixed(1)]; prev?.(k); };
  const targets = [];
  for (const l of col.circles.values()) for (const r of l) if (r[3] && Math.hypot(r[0] - c.x, r[1] - c.y) < 220) targets.push(r);
  const seenKind = {};
  for (let r of targets) {
    const key = r[3] + ':' + r[2]; if ((seenKind[key] ?? 0) >= 2) continue;
    // approach from the south; need 12 m free of footprints and other circles
    let free = window.sbxParked.near(r[0], r[1] - 7, 10).length === 0 && !window.sbxTraffic.findCar?.(r[0], r[1] - 7, 12, false); for (let d = -3; d <= 14 && free; d += 1) for (const o of [-1.1, 0, 1.1]) { if (col.inside(r[0] + o, r[1] - d)) free = false; for (const l of col.circles.values()) for (const q of l) if (!q[3] && Math.hypot(q[0] - r[0] - o, q[1] - r[1] + d) < 1.0) free = false; }
    if (!free) continue;
    seenKind[key] = (seenKind[key] ?? 0) + 1;
    c.x = r[0] + 0.05; c.y = r[1] - 12; c.h = 0; c.vx = 0; c.vy = 8; c.speed = 8; c.damage = 0; c.dead = false; c.z = t.ground(c.x, c.y);
    window.sbxActions.kb.y = 0; await new Promise((r2) => setTimeout(r2, 900));   // let tiles stream in around the new spot
    const find = () => [...col.circles.values()].flat().find((q) => Math.abs(q[0] - r[0]) < 0.02 && Math.abs(q[1] - r[1]) < 0.02);
    r = find(); if (!r) continue;
    c.x = r[0] + 0.05; c.y = r[1] - 12; c.h = 0; c.vx = 0; c.vy = 8; c.speed = 8; c.damage = 0; c.dead = false; c.z = t.ground(c.x, c.y); c.zV = 0;
    const c0 = crashes, k0 = col.knocked;
    await new Promise((res) => { const t0 = performance.now(); const tick = () => { window.sbxActions.kb.y = 0.3; if (c.y > r[1] + 1.5 || performance.now() - t0 > 4000) res(); else requestAnimationFrame(tick); }; tick(); });
    const vEnd = c.speed, cr = crashes - c0, dm = c.damage;
    await new Promise((r2) => setTimeout(r2, 800));
    const stillThere = !!find();
    out.push({ kind: r[3], rad: r[2], crashes: cr, knocked: col.knocked - k0, dmg: dm, passed: c.y > r[1], dx: +(c.x - r[0]).toFixed(2), h: +c.h.toFixed(2), tgt: [+r[0].toFixed(1), +r[1].toFixed(1)], v: vEnd, stillThere, lc: window.__lastCrash });
  }
  window.sbxActions.kb.y = 0;
  return out;
});
for (const r of res) console.log('  ', JSON.stringify(r));
ok(res.length >= 2, `drove into ${res.length} knockables`);
ok(res.every((r) => r.knocked >= 1 && r.crashes === 0 && r.dmg === 0 && r.passed && !r.stillThere), 'every one fell: no crash, no damage, car drove on, collider removed');
ok(res.every((r) => r.v > 6.5), 'car keeps its speed (> 6.5 of 8 m/s)');
// hard things stay hard: drive into a tree / mast; pedestrians still bump into bins but walk through never-solid kind 2
const hard = await page.evaluate(async () => {
  const t = window.sbxTiles, c = window.sbxPlayer.driving, col = t.colliders; let crashes = 0; const prev = c.onCrash; c.onCrash = (k) => { crashes++; prev?.(k); };
  let tgt = null;
  for (const l of col.circles.values()) for (const r of l) { if (r[3] || r[2] < 0.25 || Math.hypot(r[0] - c.x, r[1] - c.y) > 200 || tgt) continue; let free = true; for (let d = -3; d <= 14 && free; d++) for (const o of [-1.1, 0, 1.1]) { if (col.inside(r[0] + o, r[1] - d)) free = false; for (const q of l) if (q !== r && Math.hypot(q[0] - r[0] - o, q[1] - r[1] + d) < 1.0) free = false; } if (free && window.sbxParked.near(r[0], r[1] - 7, 10).length === 0) tgt = r; }
  if (!tgt) return null;
  window.sbxActions.kb.y = 0; await new Promise((r) => setTimeout(r, 900));
  c.x = tgt[0]; c.y = tgt[1] - 12; c.h = 0; c.vx = 0; c.vy = 8; c.speed = 8; c.damage = 0; c.z = t.ground(c.x, c.y); c.zV = 0;
  await new Promise((res) => { const t0 = performance.now(); const tick = () => { window.sbxActions.kb.y = 0.3; if (crashes || c.y > tgt[1] + 2 || performance.now() - t0 > 3000) res(); else requestAnimationFrame(tick); }; tick(); });
  window.sbxActions.kb.y = 0;
  const k2 = [...col.circles.values()].flat().find((r) => r[3] === 2), k1 = [...col.circles.values()].flat().find((r) => r[3] === 1);
  return { r: tgt[2], crashes, dmg: c.damage, walkK2: k2 ? col.resolveCircles(k2[0] + 0.05, k2[1], 0.3).map((v, i) => Math.abs(v - k2[i])) : null, walkK1: k1 ? col.resolveCircles(k1[0] + 0.05, k1[1], 0.3).map((v, i) => Math.abs(v - k1[i])) : null };
});
console.log('  hard', JSON.stringify(hard));
ok(hard && hard.crashes >= 1, 'tree / mast still crashes the car');
ok(hard && hard.walkK2 && hard.walkK2[0] < 0.06 && hard.walkK1 && Math.hypot(...hard.walkK1) > 0.3, 'pedestrians: bins still solid, kind 2 posts do not block');
// geometry check: proxy meshes exist and hidden source collapsed
const proxies = await page.evaluate(() => { let n = 0; window.sbxScene.traverse((o) => { if (o.isMesh && o.onBeforeRender.toString().includes('{}')) n++; }); return n; });
ok(proxies >= res.length, `proxy meshes in scene: ${proxies}`);
await page.screenshot({ path: '../preview/knock_test.jpg', type: 'jpeg', quality: 60 });
await browser.close();
