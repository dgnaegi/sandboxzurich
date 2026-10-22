// Rental e-scooter: walk to the nearest one, E to ride (desktop key + touch button), ride 8 s, dismount, scooter stays. Usage: node tests/scooter_ride.mjs [baseUrl]
import { chromium, devices } from 'playwright';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
let fails = 0;
const ok = (c, m) => { if (!c) fails++; console.log(c ? 'OK  ' : 'FAIL', m); };

async function run(mode) {
  const touchMode = mode === 'touch';
  let cdp = null;
  const ctx = await browser.newContext(touchMode ? { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true } : { viewport: { width: 1280, height: 720 } });
  const page = await ctx.newPage();
  const errs = []; page.on('pageerror', (e) => errs.push(e.message));
  await page.goto(`${BASE}/?at=${touchMode ? '-600,300' : '-22,14'},0&t=12:00${touchMode ? '' : '&nopost'}`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.waitForTimeout(1500);
  const info = await page.evaluate(() => {
    const p = window.sbxPlayer, list = [...window.sbxScooters.all()].filter((s) => !s.taken).sort((a, b) => Math.hypot(a.x - p.x, a.y - p.y) - Math.hypot(b.x - p.x, b.y - p.y));
    for (const s of list.slice(0, 40)) { // a scooter with no tram/bus/car/bike closer than itself
      const dx = 3 * Math.cos(s.h + 1.2), dy = 3 * Math.sin(s.h + 1.2);
      p.teleport(s.x + dx * 0.4, s.y + dy * 0.4, 0);
      const t = window.sbxTransitUse.nearest(), c = window.sbxCarUse.nearest();
      if (t || c || window.sbxBikes.nearest(s.x, s.y, 2.5)) continue;
      p.teleport(s.x + dx, s.y + dy, Math.atan2(-dx, -dy));
      return { x: s.x, y: s.y, bike: 0 };
    }
    return null;
  });
  ok(!!info, `${mode}: scooter found`);
  if (!info) return;
  await page.waitForTimeout(500);
  if (touchMode) { // walk with the joystick until close
    cdp = await ctx.newCDPSession(page);
    const t = (type, pts) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: pts.map(([x, y], i) => ({ x, y, id: i })) });
    await t('touchStart', [[150, 260]]); await t('touchMove', [[150, 220]]);
    for (let i = 0; i < 40; i++) { const d = await page.evaluate((s) => Math.hypot(window.sbxPlayer.x - s.x, window.sbxPlayer.y - s.y), info); if (d < 1.4) break; await page.waitForTimeout(60); }
    await t('touchEnd', []);
  } else {
    await page.keyboard.down('KeyW');
    for (let i = 0; i < 40; i++) { const d = await page.evaluate((s) => Math.hypot(window.sbxPlayer.x - s.x, window.sbxPlayer.y - s.y), info); if (d < 1.4) break; await page.waitForTimeout(60); }
    await page.keyboard.up('KeyW');
  }
  await page.waitForTimeout(300);
  const d0 = await page.evaluate((s) => Math.hypot(window.sbxPlayer.x - s.x, window.sbxPlayer.y - s.y), info);
  ok(d0 < 2.0, `${mode}: walked to scooter (${d0.toFixed(2)} m)`);
  if (info.bike) console.log('NOTE a bike is within 2 m of this scooter; nearest-wins applies');
  const hint = await page.evaluate(() => document.getElementById('prompt').textContent);
  ok(/Trottinett/.test(hint) || info.bike, `${mode}: hint "${hint}"`);
  if (touchMode) await page.tap('#btn-use'); else await page.keyboard.press('KeyE');
  await page.waitForTimeout(400);
  ok(await page.evaluate(() => window.sbxPlayer.riding?.type === 'scooter'), `${mode}: riding scooter`);
  const p0 = await page.evaluate(() => ({ x: window.sbxPlayer.x, y: window.sbxPlayer.y }));
  let vmax = 0, bad = false;
  if (touchMode) {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 150, y: 260, id: 0 }] });
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 150, y: 215, id: 0 }] });
  } else await page.keyboard.down('KeyW');
  for (let i = 0; i < 16; i++) {
    await page.waitForTimeout(500);
    const s = await page.evaluate(() => { const p = window.sbxPlayer; return { v: p.speed, ok: [p.x, p.y, p.z, p.speed, p.heading, p.scooter.lean].every(Number.isFinite), r: !!p.riding }; });
    vmax = Math.max(vmax, s.v); if (!s.ok) bad = true;
    if (!s.r) break;
  }
  if (touchMode) await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); else await page.keyboard.up('KeyW');
  const p1 = await page.evaluate(() => ({ x: window.sbxPlayer.x, y: window.sbxPlayer.y, riding: !!window.sbxPlayer.riding }));
  const prog = Math.hypot(p1.x - p0.x, p1.y - p0.y);
  ok(prog > 12, `${mode}: progress ${prog.toFixed(1)} m in 8 s`);
  ok(vmax <= 5.8 && vmax > 4, `${mode}: top speed ${vmax.toFixed(2)} m/s (limit 5.6)`);
  ok(!bad, `${mode}: no NaN`);
  // brake (desktop: S, released as soon as it stands, else it would roll backwards) / coast (touch) until it stands, max 7 s
  if (!touchMode) await page.keyboard.down('KeyS');
  let vs = 99;
  for (let t = 0; t < 70 && Math.abs(vs) >= 0.5; t++) { await page.waitForTimeout(100); vs = await page.evaluate(() => window.sbxPlayer.speed); }
  if (!touchMode) await page.keyboard.up('KeyS');
  ok(Math.abs(vs) < 0.5, `${mode}: stopped (${vs.toFixed(2)})`);
  if (touchMode) await page.tap('#btn-use'); else await page.keyboard.press('KeyE');
  await page.waitForTimeout(500);
  const end = await page.evaluate(() => {
    const p = window.sbxPlayer, s = window.sbxScooters.nearest(p.x, p.y, 3);
    return { riding: !!p.riding, stays: !!s, z: p.z, g: window.sbxTiles.groundAt(p.x, p.y, p.z), vis: window.sbxPlayer.scooter.group.visible };
  });
  ok(!end.riding && !end.vis, `${mode}: dismounted`);
  ok(end.stays, `${mode}: scooter stays where left`);
  ok(Math.abs(end.z - end.g) < 0.4, `${mode}: player on ground (dz ${(end.z - end.g).toFixed(2)})`);
  ok(errs.length === 0, `${mode}: no page errors ${errs[0] ?? ''}`);
  await ctx.close();
}
await run('desktop');
await run('touch');
await browser.close();
process.exit(fails ? 1 : 0);
