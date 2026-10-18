// Crash test: drive a stolen car at ~28 m/s into a house wall -> no tunnelling, damage rises, repeated crashes wreck it
// (engine dead, prompt "Auto kaputt"); also a hard bike crash drops the rider. Desktop (keys) and touch (stick).
// Contact sheet: preview/crash_v1.jpg (dent, smoke, wreck).
import { chromium, devices } from 'playwright';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const ok = (c, m) => { console.log(c ? 'OK  ' : 'FAIL', m); if (!c) process.exitCode = 1; };
const prev = new URL('../../preview/', import.meta.url).pathname;
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
const shots = [];

async function run(touch) {
  const tag = touch ? 'touch' : 'desktop';
  const ctx = await browser.newContext(touch ? { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true } : { viewport: { width: 960, height: 540 } });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => { console.log('pageerror', e.message); process.exitCode = 1; });
  const cdp = touch ? await ctx.newCDPSession(page) : null;
  await page.goto(`${BASE}/?at=785,-635,0.37&t=12:00&nopost`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
  await page.waitForTimeout(1500);
  if (touch) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 150, y: 260, id: 0 }] }); await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); }
  const car = await page.evaluate(() => {
    const p = window.sbxPlayer, list = window.sbxParked.near(p.x, p.y, 120).sort((a, b) => Math.hypot(a.x - p.x, a.y - p.y) - Math.hypot(b.x - p.x, b.y - p.y));
    const s = list.find((c) => !window.sbxBikes.nearest(c.x, c.y, 9)) ?? list[0];
    p.teleport(s.x + Math.cos(s.h) * 2.4, s.y - Math.sin(s.h) * 2.4, 0);
    return !!s;
  });
  ok(car, `${tag}: parked car found`);
  await page.waitForTimeout(300);
  if (touch) await page.tap('#btn-use'); else await page.keyboard.press('KeyE');
  await page.waitForFunction(() => !!window.sbxPlayer.driving, null, { timeout: 8000 }).catch(() => {});
  ok(await page.evaluate(() => !!window.sbxPlayer.driving), `${tag}: in the car`);
  await page.waitForFunction(() => getComputedStyle(document.getElementById('carhp')).display !== 'none', null, { timeout: 3000 }).catch(() => {}); // shown by the next frame
  ok(await page.evaluate(() => getComputedStyle(document.getElementById('carhp')).display !== 'none'), `${tag}: HP bar visible while driving`);

  const gas = async (on) => {
    if (touch) {
      if (on) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 150, y: 260, id: 0 }] }); await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 150, y: 200, id: 0 }] }); }
      else await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    } else if (on) await page.keyboard.down('KeyW'); else await page.keyboard.up('KeyW');
  };
  // place the car 18 m from a wall (found by a ray search), heading at it, speed 28 m/s; a recorder checks every frame that no corner is inside a building
  const crash = (i) => page.evaluate(async () => {
    const t = window.sbxTiles, c = window.sbxPlayer.driving;
    c.dead = false; // (only used when re-testing)
    // find a wall with a clear straight run-up of >= 14 m (several sample lines side by side), starting spot free
    let wall = null, hx = 0, d = 14;
    for (let a = 0; a < 6.28 && !wall; a += 0.05) for (let r = 16; r < 120 && !wall; r += 1) {
      const x = c.x + Math.cos(a) * r, y = c.y + Math.sin(a) * r;
      if (!t.colliders.inside(x, y) || t.colliders.inside(x - Math.cos(a) * 0.6, y - Math.sin(a) * 0.6)) continue;
      const h = Math.atan2(Math.cos(a), Math.sin(a)), sx = Math.sin(h), sy = Math.cos(h), rx = sy, ry = -sx;
      let free = true;
      for (const l of [-0.9, 0, 0.9]) free &&= t.colliders.freeFraction(x - sx * d + rx * l, y - sy * d + ry * l, x - sx * 0.7 + rx * l, y - sy * 0.7 + ry * l, 40) === 1 && !t.colliders.inside(x - sx * d + rx * l, y - sy * d + ry * l);
      if (free) { wall = { x, y, a }; hx = h; }
    }
    if (!wall) return null;
    c.x = wall.x - Math.sin(hx) * d; c.y = wall.y - Math.cos(hx) * d; c.h = hx; c.vx = Math.sin(hx) * 28; c.vy = Math.cos(hx) * 28; c.speed = 28;
    const dmg0 = c.damage; let inside = 0, frames = 0, vmax = 28;
    const corners = () => { const f = [Math.sin(c.h), Math.cos(c.h)], r = [f[1], -f[0]], out = []; for (const a of [-1, 1]) for (const b of [-1, 1]) out.push([c.x + f[0] * a * c.half.l * 0.85 + r[0] * b * c.half.w * 0.85, c.y + f[1] * a * c.half.l * 0.85 + r[1] * b * c.half.w * 0.85]); return out; };
    await new Promise((res) => { const tick = () => { frames++; if (corners().some(([x, y]) => t.colliders.inside(x, y))) inside++; if (frames < 90) requestAnimationFrame(tick); else res(); }; tick(); });
    return { dmg0, dmg: c.damage, inside, speed: c.speed, dead: c.dead, d, wallDist: Math.hypot(wall.x - c.x, wall.y - c.y) };
  }, i);
  let last = 0;
  for (let i = 0; i < 5; i++) {
    await gas(true);
    const r = await crash(i);
    await gas(false);
    if (!r) { ok(false, `${tag}: no wall found`); break; }
    console.log(`   crash ${i}:`, JSON.stringify(r));
    ok(r.inside === 0, `${tag}: crash ${i}: no corner ever inside a building`);
    ok(r.dmg > r.dmg0 || r.dead, `${tag}: crash ${i}: damage ${r.dmg0.toFixed(2)} -> ${r.dmg.toFixed(2)}`);
    ok(Math.abs(r.speed) < 12, `${tag}: crash ${i}: speed after ${r.speed.toFixed(1)}`);
    if (i === 0) { await page.waitForTimeout(500); shots.push(await page.screenshot({ type: 'jpeg', quality: 70 })); }
    if (i === 1) { await page.waitForTimeout(400); shots.push(await page.screenshot({ type: 'jpeg', quality: 70 })); }
    last = r.dmg;
    if (r.dead) break;
    // reset the car away from the wall: reverse out
    await page.evaluate(() => { const c = window.sbxPlayer.driving; c.vx = c.vy = 0; c.speed = 0; });
  }
  const dead = await page.evaluate(() => window.sbxPlayer.driving?.dead);
  ok(dead, `${tag}: car is wrecked after repeated crashes (damage ${last.toFixed(2)})`);
  await page.waitForTimeout(500);
  const state = await page.evaluate(() => ({ prompt: document.getElementById('prompt').textContent, hp: document.querySelector('#carhp i').style.width }));
  ok(/kaputt/.test(state.prompt), `${tag}: prompt "${state.prompt}", HP bar ${state.hp}`);
  await gas(true); await page.waitForTimeout(800);
  const v = await page.evaluate(() => Math.abs(window.sbxPlayer.speed));
  ok(v < 3, `${tag}: dead engine does not accelerate (${v.toFixed(1)} m/s)`);
  await gas(false);
  if (!touch) { shots.push(await page.screenshot({ type: 'jpeg', quality: 70 })); }
  await page.waitForTimeout(1500);
  if (touch) await page.tap('#btn-use'); else await page.keyboard.press('KeyE');
  await page.waitForFunction(() => !window.sbxPlayer.driving, null, { timeout: 10000 }).catch(() => {});
  ok(await page.evaluate(() => !window.sbxPlayer.driving), `${tag}: got out of the wreck`);
  ok(await page.evaluate(() => window.sbxCarUse.wrecks.length > 0), `${tag}: wreck stays behind`);

  if (!touch) { // bike: hard crash drops the rider
    const r = await page.evaluate(async () => {
      const p = window.sbxPlayer, t = window.sbxTiles;
      const s = window.sbxBikes.nearest(p.x, p.y, 400); if (!s) return null;
      p.teleport(s.x, s.y + 0.0, 0); await new Promise((r) => setTimeout(r, 300));
      window.sbxBikes.take(s); p.mount(s);
      let wall = null;
      for (let a = 0; a < 6.28 && !wall; a += 0.1) for (let r = 4; r < 60; r += 1.5) { const x = p.x + Math.cos(a) * r, y = p.y + Math.sin(a) * r; if (t.colliders.inside(x, y)) { wall = { x, y, a }; break; } }
      if (!wall) return { nowall: true };
      p.heading = Math.atan2(Math.cos(wall.a), Math.sin(wall.a)); p.x = wall.x - Math.sin(p.heading) * 8; p.y = wall.y - Math.cos(p.heading) * 8; p.speed = 9;
      return { ok: true };
    });
    if (r?.ok) {
      await page.keyboard.down('KeyW'); await page.keyboard.down('ShiftLeft');
      await page.waitForFunction(() => !window.sbxPlayer.riding, null, { timeout: 5000 }).catch(() => {});
      await page.keyboard.up('KeyW'); await page.keyboard.up('ShiftLeft');
      ok(await page.evaluate(() => !window.sbxPlayer.riding && window.sbxPlayer.fallT > 0), `${tag}: hard bike crash -> rider falls off`);
    } else console.log('   (bike test skipped:', JSON.stringify(r), ')');
  }
  await ctx.close();
}
await run(false);
await run(true);
await browser.close();
if (shots.length) {
  fs.mkdirSync(prev, { recursive: true });
  const files = shots.map((b, i) => { const f = `/tmp/crash_${i}.jpg`; fs.writeFileSync(f, b); return f; });
  try { execFileSync('python3', ['-c', `
from PIL import Image
import sys
ims=[Image.open(f).convert('RGB') for f in sys.argv[2:]]
w=500; ims=[i.resize((w,int(i.height*w/i.width))) for i in ims]
S=Image.new('RGB',(w*len(ims),max(i.height for i in ims)))
for k,i in enumerate(ims): S.paste(i,(k*w,0))
S.save(sys.argv[1],quality=80)`, prev + 'crash_v1.jpg', ...files]); console.log('sheet preview/crash_v1.jpg'); } catch (e) { console.log('sheet failed', e.message); }
}
