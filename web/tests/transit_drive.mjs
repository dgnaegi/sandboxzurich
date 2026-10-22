// Driving trams and buses: step up to a passing vehicle (E), drive, brake, get out. Desktop (keys) and phone (stick + buttons).
// Usage: node tests/transit_drive.mjs [base] ; SHOTS=dir saves screenshots (for the contact sheet).
import { chromium, devices } from 'playwright';
import fs from 'fs';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const SHOTS = process.env.SHOTS;
if (SHOTS) fs.mkdirSync(SHOTS, { recursive: true });
const ok = (c, m) => { console.log(c ? 'OK  ' : 'FAIL', m); if (!c) process.exitCode = 1; };
const browser = await chromium.launch({ args: ['--use-gl=angle'] });

async function run(touch) {
  const tag = touch ? 'touch' : 'desktop';
  const ctx = await browser.newContext(touch ? { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true } : { viewport: { width: 960, height: 540 } });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => { console.log('pageerror', e.message); process.exitCode = 1; });
  page.on('console', (m) => { if (m.type() === 'error') console.log('console.error', m.text().slice(0, 200)); });
  const cdp = touch ? await ctx.newCDPSession(page) : null;
  await page.goto(`${BASE}/?at=957,-1196,0&t=12:00&nopost`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
  await page.waitForTimeout(1000);
  if (touch) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 150, y: 260, id: 0 }] }); await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); }
  const shot = async (name) => { if (SHOTS) await page.screenshot({ path: `${SHOTS}/${tag}_${name}.png` }); };
  const stick = async (dx, dy) => {   // hold the stick at an offset (phone)
    held = true;
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 150, y: 260, id: 0 }] });
    const n = 6;
    for (let i = 1; i <= n; i++) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 150 + (dx * i * 9) / n * 6, y: 260 + (dy * i * 9) / n * 6, id: 0 }] }); await page.waitForTimeout(20); }
  };
  let held = false;
  const release = async () => { if (!held) return; held = false; await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); };

  for (const kind of ['tram', 'bus']) {
    // many vehicles: short headway; place the player on a line (trams: on the Hardbruecke deck if the line has one)
    const spot = await page.evaluate((kind) => {
      const T = window.sbxTransit; T.headway = 20;
      const lines = T.lines.map((L, li) => ({ L, li })).filter((o) => (kind === 'tram') === o.L.tram && o.L.len > 600);
      let best = null;
      for (const o of lines) {
        if (kind === 'tram' && o.L.ref !== '8') continue;
        const zs = o.L.zs ?? [];
        let run = 0;   // longest stretch of bridge deck on this line
        for (let i = 0; i < zs.length; i++) { run = zs[i] != null ? run + 1 : 0; if (run > 6 && kind === 'tram') { best = { li: o.li, s: o.L.cum[i - 3] }; break; } }
        if (best) break;
        if (!best && kind === 'bus') best = { li: o.li, s: o.L.len * 0.4 };
      }
      best ??= { li: lines[0].li, s: lines[0].L.len * 0.4 };
      const p = [0, 0, 0, 0]; T.poseAt(best.li, best.s, p);
      window.sbxPlayer.teleport(p[0], p[1], 0);
      return { li: best.li, ref: T.lines[best.li].ref, x: p[0], y: p[1] };
    }, kind);
    ok(!!spot, `${tag} ${kind}: spot on line ${spot.ref} (${spot.x.toFixed(0)}, ${spot.y.toFixed(0)})`);
    await page.waitForTimeout(3500); // tiles stream in
    // wait for a vehicle of that line near, then stand beside its middle
    let target = null;
    for (let i = 0; i < 60 && !target; i++) {
      target = await page.evaluate(({ li, kind }) => {
        const T = window.sbxTransit, P = window.sbxPlayer;
        for (let j = 0; j < T.nNear; j++) {
          const r = T.near[j];
          if (r.li !== li) continue;
          const spec = T.spec(T.specName(T.line(r.li), r.k)), p = [0, 0, 0, 0];
          T.poseAt(r.li, r.sh - spec.length * 0.35, p);
          // right-hand side of the vehicle, 2.6 m from its axis
          P.teleport(p[0] + Math.cos(p[3]) * 2.6, p[1] - Math.sin(p[3]) * 2.6, 0);
          return { x: p[0], y: p[1] };
        }
        return null;
      }, { li: spot.li, kind });
      if (!target) await page.waitForTimeout(250);
    }
    ok(!!target, `${tag} ${kind}: vehicle came by`);
    if (!target) continue;
    await page.waitForTimeout(120);
    const prompt = await page.evaluate(() => document.getElementById('prompt').textContent);
    ok(new RegExp(kind === 'tram' ? 'Tram fahren' : 'Bus fahren').test(prompt), `${tag} ${kind}: prompt "${prompt}"`);
    if (touch) await page.tap('#btn-use'); else await page.keyboard.press('KeyE');
    await page.waitForFunction(() => !!window.sbxPlayer.driving, null, { timeout: 5000 }).catch(() => {});
    ok(await page.evaluate(() => !!window.sbxPlayer.driving), `${tag} ${kind}: got in`);
    await page.waitForTimeout(250);
    const hud = await page.evaluate(() => document.getElementById('transithud').textContent);
    ok(/→/.test(hud), `${tag} ${kind}: HUD "${hud}"`);
    const st0 = await page.evaluate(() => { const d = window.sbxPlayer.driving; return { x: d.x, y: d.y, h: d.h, s: d.s ?? 0, tram: !!d.isTram }; });
    ok(st0.tram === (kind === 'tram'), `${tag} ${kind}: driving a ${st0.tram ? 'tram' : 'bus'}`);
    // gas for 10 s (bus: the last 4 s steering right)
    if (touch) await stick(0, -1); else await page.keyboard.down('KeyW');
    let maxDh = 0, h0 = null;
    for (let i = 0; i < 20; i++) {
      await page.waitForTimeout(500);
      if (i === 5) await shot('drive_' + kind);
      if (kind === 'bus' && i >= 8) { // steer right for 2 s, then left for 2 s (a street is narrow)
        const dir = i < 12 ? 1 : -1;
        if (i === 8 || i === 12) { if (touch) { await release(); await stick(dir, -1); } else { await page.keyboard.up('KeyD'); await page.keyboard.up('KeyA'); await page.keyboard.down(dir > 0 ? 'KeyD' : 'KeyA'); } }
        const h = await page.evaluate(() => window.sbxPlayer.driving.h);
        if (process.env.DBG) console.log(i, h.toFixed(2), (await page.evaluate(() => window.sbxPlayer.driving.speed)).toFixed(1));
        h0 ??= h; maxDh = Math.max(maxDh, Math.abs(Math.atan2(Math.sin(h - h0), Math.cos(h - h0))));
        if (i === 11) await shot('turn_bus');
      }
    }
    const st1 = await page.evaluate(() => { const d = window.sbxPlayer.driving; return { x: d.x, y: d.y, h: d.h, s: d.s ?? 0, v: d.speed, z: d.z }; });
    const dist = Math.hypot(st1.x - st0.x, st1.y - st0.y);
    ok(Number.isFinite(st1.x + st1.y + st1.z + st1.h) && Number.isFinite(st1.v), `${tag} ${kind}: no NaN (z ${st1.z.toFixed(1)})`);
    ok(dist > 25, `${tag} ${kind}: drove ${dist.toFixed(0)} m in 10 s, speed ${st1.v.toFixed(1)} m/s${kind === 'tram' ? `, s +${(st1.s - st0.s).toFixed(0)}` : ''}`);
    if (kind === 'tram') ok(st1.s > st0.s + 20, `${tag} tram: progress along the line`);
    if (kind === 'bus') { ok(maxDh > 0.15, `${tag} bus: steering changed the heading by up to ${maxDh.toFixed(2)} rad`); if (touch) await release(); else { await page.keyboard.up('KeyD'); await page.keyboard.up('KeyA'); } }
    // let go, then brake with S / stick down until standing
    if (touch) { await release(); await stick(0, 1); } else { await page.keyboard.up('KeyW'); await page.keyboard.down('KeyS'); }
    await page.waitForFunction(() => Math.abs(window.sbxPlayer.driving.speed) < 0.3, null, { timeout: 15000 }).catch(() => {});
    const vStop = await page.evaluate(() => window.sbxPlayer.driving.speed);
    ok(Math.abs(vStop) < 0.5, `${tag} ${kind}: braked to ${vStop.toFixed(2)} m/s`);
    if (touch) await release(); else await page.keyboard.up('KeyS');
    if (kind === 'tram') { // doors open at a stop: park the tram on the platform of the next stop
      const dr = await page.evaluate(() => {
        const d = window.sbxPlayer.driving, L = window.sbxTransit.line(d.li), st = L.stops.find((q) => q.s - (d.s - d.vlen / 2) > 5);
        if (!st) return null;
        d.s = st.s + d.vlen / 2 - 3; d.speed = 0; return st.name;
      });
      await page.waitForTimeout(700);
      const open = await page.evaluate(() => window.sbxPlayer.driving.doorsOpen);
      ok(dr && open, `${tag} tram: doors open at stop ${dr}`);
      await shot('stop_tram');
    }
    if (kind === 'tram') { // a car on the rails 18 m ahead: the tram stops hard in front of it
      const gap = await page.evaluate(() => {
        const P = window.sbxPlayer, d = P.driving, T = window.sbxTransit, p = [0, 0, 0, 0];
        d.s = Math.max(d.minS + 1, d.s - 40); T.poseAt(d.li, d.s + 18, p);
        const old = P.drive.hooks.obstacles; window.__oldObs = old;
        window.__oldPk = P.drive.hooks.parked; P.drive.hooks.parked = () => [];
        P.drive.hooks.obstacles = () => [{ x: p[0], y: p[1], fx: Math.sin(p[3]), fy: Math.cos(p[3]), hl: 2.2, hw: 0.9, id: 99 }];
        window.__hits = 0; d.onImpact = () => { window.__hits++; };
        return 18;
      });
      if (touch) await stick(0, -1); else await page.keyboard.down('KeyW');
      for (let q = 0; q < 9; q++) { await page.waitForTimeout(1000); if (process.env.DBG) console.log(await page.evaluate(() => { const d = window.sbxPlayer.driving; return [d.s.toFixed(1), d.speed.toFixed(2), d.minS.toFixed(0), window.__hits].join(' '); })); }
      if (touch) await release(); else await page.keyboard.up('KeyW');
      const r = await page.evaluate(() => { const d = window.sbxPlayer.driving; window.sbxPlayer.drive.hooks.obstacles = window.__oldObs; window.sbxPlayer.drive.hooks.parked = window.__oldPk; return { v: d.speed, hits: window.__hits, moved: d.s }; });
      ok(r.hits >= 1 && Math.abs(r.v) < 0.1, `${tag} tram: hit the obstacle (${r.hits} impact), stopped (${r.v.toFixed(2)} m/s)`);
      await page.waitForTimeout(300);
    }
    // get out (E): player stands beside the vehicle on the ground
    if (touch) await page.tap('#btn-use'); else await page.keyboard.press('KeyE');
    await page.waitForFunction(() => !window.sbxPlayer.driving, null, { timeout: 5000 }).catch(() => {});
    const out = await page.evaluate(() => { const P = window.sbxPlayer; return { driving: !!P.driving, x: P.x, y: P.y, z: P.z, vis: P.body.root.visible }; });
    ok(!out.driving && out.vis && Number.isFinite(out.z), `${tag} ${kind}: got out (z ${out.z.toFixed(1)})`);
    const dv = await page.evaluate(() => { const P = window.sbxPlayer, T = window.sbxTransit; return T.colliders().concat([]).reduce((m, c) => Math.min(m, Math.hypot(c.x - P.x, c.y - P.y)), 99); });
    ok(dv > 1.2, `${tag} ${kind}: stands ${dv.toFixed(1)} m from the nearest body centre, not inside`);
    // it stays put and can be taken again
    await page.waitForTimeout(300);
    const again = await page.evaluate(() => /fahren/.test(document.getElementById('prompt').textContent) || !!window.sbxTransitUse.nearest());
    ok(again, `${tag} ${kind}: standing vehicle can be taken again`);
    await page.evaluate(() => { window.sbxPlayer.teleport(window.sbxPlayer.x + 400, window.sbxPlayer.y, 0); });
    await page.waitForTimeout(800);
  }
  await ctx.close();
}

await run(false);
await run(true);
await browser.close();
