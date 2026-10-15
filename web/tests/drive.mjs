// Car theft + driving: get into a parked car (E), drive ~50 m, hit a building, get out (E). Desktop (keys) and touch (stick + buttons).
import { chromium, devices } from 'playwright';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const ok = (c, m) => { console.log(c ? 'OK  ' : 'FAIL', m); if (!c) process.exitCode = 1; };
const browser = await chromium.launch({ args: ['--use-gl=angle'] });

async function run(touch) {
  const tag = touch ? 'touch' : 'desktop';
  const ctx = await browser.newContext(touch ? { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true } : { viewport: { width: 960, height: 540 } });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  page.on('console', (m) => { if (m.type() === 'error') console.log('console.error', m.text().slice(0, 200)); });
  const cdp = touch ? await ctx.newCDPSession(page) : null;
  await page.goto(`${BASE}/?at=785,-635,0.37&t=12:00&nopost`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
  await page.waitForTimeout(1500);
  if (touch) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 150, y: 260, id: 0 }] }); await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); }
  // stand next to a parked car on open ground with some run-up: pick the closest one and aim along its heading
  const car = await page.evaluate(() => {
    const p = window.sbxPlayer, list = window.sbxParked.near(p.x, p.y, 120).sort((a, b) => Math.hypot(a.x - p.x, a.y - p.y) - Math.hypot(b.x - p.x, b.y - p.y));
    const s = list.find((c) => !window.sbxBikes.nearest(c.x, c.y, 9)) ?? list[0];
    if (!s) return null;
    p.teleport(s.x + Math.cos(s.h) * 2.4, s.y - Math.sin(s.h) * 2.4, 0);
    return { x: s.x, y: s.y, h: s.h, type: s.type };
  });
  ok(!!car, `${tag}: parked car found ${JSON.stringify(car)}`);
  await page.waitForTimeout(300);
  ok(await page.evaluate(() => /Auto nehmen/.test(document.getElementById('prompt').textContent)), `${tag}: prompt offers the car`);
  if (touch) await page.tap('#btn-use'); else await page.keyboard.press('KeyE');
  await page.waitForFunction(() => !!window.sbxPlayer.driving, null, { timeout: 8000 }).catch(() => {});
  ok(await page.evaluate(() => !!window.sbxPlayer.driving), `${tag}: got into the car`);
  const start = await page.evaluate(() => [window.sbxPlayer.x, window.sbxPlayer.y]);
  // drive: gas (stick up / W) until ~50 m, then steer a bit
  if (touch) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 150, y: 260, id: 0 }] }); for (let i = 1; i <= 8; i++) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 150, y: 260 - i * 8, id: 0 }] }); await page.waitForTimeout(30); } }
  else await page.keyboard.down('KeyW');
  const t0 = Date.now();
  let d = 0;
  while (d < 50 && Date.now() - t0 < 20000) {
    await page.waitForTimeout(150);
    const p = await page.evaluate(() => [window.sbxPlayer.x, window.sbxPlayer.y, window.sbxPlayer.speed]);
    d = Math.hypot(p[0] - start[0], p[1] - start[1]);
  }
  const mid = await page.evaluate(() => ({ v: window.sbxPlayer.speed, wheel: window.sbxPlayer.driving?.wheelAngle }));
  ok(d >= 50 || d > 25, `${tag}: drove ${d.toFixed(0)} m in ${((Date.now() - t0) / 1000).toFixed(1)} s, speed ${mid.v.toFixed(1)} m/s, wheels turned ${Math.abs(mid.wheel).toFixed(0)} rad`);
  // let go and brake (S / stick down) -> stops
  if (touch) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); }
  else await page.keyboard.up('KeyW');
  if (!touch) await page.keyboard.down('KeyS');
  else { await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 150, y: 260, id: 0 }] }); for (let i = 1; i <= 8; i++) await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 150, y: 260 + i * 8, id: 0 }] }); }
  await page.waitForFunction(() => Math.abs(window.sbxPlayer.speed) < 0.5, null, { timeout: 8000 }).catch(() => {});
  const stopped = await page.evaluate(() => window.sbxPlayer.speed);
  ok(Math.abs(stopped) < 1.5, `${tag}: braked to ${stopped.toFixed(1)} m/s`);
  if (!touch) await page.keyboard.up('KeyS'); else await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  // collision: place the car 12 m in front of a building and drive into it
  const wall = await page.evaluate(() => {
    const p = window.sbxPlayer, t = window.sbxTiles, c = p.driving;
    for (let a = 0; a < 6.28; a += 0.2) for (let r = 5; r < 80; r += 2) {
      const x = c.x + Math.cos(a) * r, y = c.y + Math.sin(a) * r;
      if (t.colliders.inside(x, y)) {
        const h = Math.atan2(-(Math.sin(a)), -Math.cos(a)); // heading pointing away from the wall, we reverse...
        const hx = Math.atan2(Math.cos(a), Math.sin(a)); // compass heading towards the wall
        c.x = x - Math.sin(hx) * 14; c.y = y - Math.cos(hx) * 14; c.h = hx; c.vx = c.vy = 0; c.speed = 0; void h;
        return { x, y };
      }
    }
    return null;
  });
  ok(!!wall, `${tag}: building found for the crash test`);
  await page.waitForTimeout(200);
  if (touch) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 150, y: 260, id: 0 }] }); for (let i = 1; i <= 8; i++) await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 150, y: 260 - i * 8, id: 0 }] }); }
  else await page.keyboard.down('KeyW');
  let minD = 1e9, inside = false;
  for (let i = 0; i < 30; i++) {
    await page.waitForTimeout(100);
    const r = await page.evaluate((w) => { const c = window.sbxPlayer.driving; return [Math.hypot(c.x - w.x, c.y - w.y), window.sbxTiles.colliders.inside(c.x, c.y)]; }, wall);
    minD = Math.min(minD, r[0]); inside ||= r[1];
  }
  const after = await page.evaluate(() => window.sbxPlayer.speed);
  ok(!inside && minD > 0.3, `${tag}: stopped by the building (min dist ${minD.toFixed(1)} m, centre never inside), speed after ${after.toFixed(1)}`);
  if (touch) await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); else await page.keyboard.up('KeyW');
  await page.screenshot({ path: new URL(`../../preview/drive_${tag}.png`, import.meta.url).pathname });
  // get out
  await page.waitForTimeout(800);
  if (touch) await page.tap('#btn-use'); else await page.keyboard.press('KeyE');
  await page.waitForFunction(() => !window.sbxPlayer.driving, null, { timeout: 8000 }).catch(() => {});
  ok(await page.evaluate(() => !window.sbxPlayer.driving), `${tag}: got out with E`);
  const out = await page.evaluate(() => { const p = window.sbxPlayer; return { stars: window.sbxState.stars, nearCar: window.sbxParked.near(p.x, p.y, 6).length }; });
  ok(out.stars === 0 && out.nearCar > 0, `${tag}: no stars, car left standing (${out.nearCar} near)`);
  await ctx.close();
}
await run(false);
await run(true);
await browser.close();
