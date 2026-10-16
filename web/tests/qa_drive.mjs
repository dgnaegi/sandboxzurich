// QA: steal a car at several places and drive 35 s with wandering steering; sample clipping, stalls, camera, off-road
import { launch, open, OUT } from './qa_lib.mjs';
const BASE = process.argv[2] ?? 'http://localhost:5199';
const SP = [['Langstrasse', 842, -483, 0.37], ['Helvetiaplatz', 789, -873, 0.3], ['Kalkbreite', 393, -1202, 0], ['Albisrieder', -491, -690, 0], ['Josefwiese', 514, 197, 0], ['Lochergut', 65, -937, 0]];
const b = await launch();
const { page, log } = await open(b, 'pc', `${BASE}/?at=789,-873,0&t=12:00&nopost`);
await page.addScriptTag({ content: `window.__f=[];let l=performance.now();(function f(t){window.__f.push(t-l);l=t;requestAnimationFrame(f)})(l);` });
await page.evaluate(async () => { const m = await import('/src/world/railzone.ts'); await m.loadRailZone(); window.__inRail = m.inRail; });
for (const [n, x, y, yaw] of SP) {
  await page.evaluate(async ([x, y, yaw]) => { const p = window.sbxPlayer; if (p.driving) window.sbxCarUse.exit(); await window.sbxTiles.update(x, y); p.teleport(x, y, yaw); }, [x, y, yaw]);
  await page.waitForTimeout(2500);
  const got = await page.evaluate(async () => {
    const p = window.sbxPlayer, cu = window.sbxCarUse;
    const l = window.sbxParked.near(p.x, p.y, 150).sort((a, b) => Math.hypot(a.x - p.x, a.y - p.y) - Math.hypot(b.x - p.x, b.y - p.y))[0];
    if (!l) return false; p.teleport(l.x + Math.cos(l.h) * 2.4, l.y - Math.sin(l.h) * 2.4, 0);
    await new Promise((r) => setTimeout(r, 300));
    const t = cu.nearest(); if (!t) return false; await cu.enter(t); return !!p.driving;
  });
  if (!got) { console.log(n, 'could not enter car'); continue; }
  const st = { ins: 0, rail: 0, off: 0, stall: 0, cins: 0, n: 0, maxHp: 0, wheelDist: 0 };
  await page.evaluate(() => (window.__f.length = 0));
  await page.keyboard.down('KeyS'); await page.waitForTimeout(1300); await page.keyboard.up('KeyS');
  let last = null;
  for (let i = 0; i < 70; i++) {
    const steer = Math.sin(i / 6) > 0.35 ? 'KeyD' : Math.sin(i / 6) < -0.35 ? 'KeyA' : null;
    await page.keyboard.down('KeyW'); if (steer) await page.keyboard.down(steer);
    await page.waitForTimeout(500);
    if (steer) await page.keyboard.up(steer);
    const s = await page.evaluate(() => { const p = window.sbxPlayer, c = p.driving, t = window.sbxTiles, cam = window.sbxCamera; return c ? { x: c.x, y: c.y, v: p.speed, ins: t.colliders.inside(c.x, c.y), rail: window.__inRail(c.x, c.y), play: t.inPlay(c.x, c.y), cins: t.colliders.inside(cam.position.x, -cam.position.z), dmg: c.damage } : null; });
    if (!s) { console.log(n, 'car lost at step', i); break; }
    st.n++; if (s.ins) st.ins++; if (s.rail) st.rail++; if (!s.play) st.off++; if (s.cins) st.cins++; if (Math.abs(s.v) < 0.5) st.stall++; st.dmg = s.dmg; last = s;
  }
  await page.keyboard.up('KeyW');
  const f = await page.evaluate(() => { const a = window.__f.slice().sort((x, y) => x - y); return { fps: +(1000 * a.length / a.reduce((x, y) => x + y, 0)).toFixed(0), over50: a.filter((v) => v > 50).length, max: a[a.length - 1] | 0 }; });
  console.log(n, JSON.stringify({ ...st, ...f, end: last && [last.x | 0, last.y | 0] }));
  await page.screenshot({ path: `${OUT}qa_review_drive_${n}.jpg`, type: 'jpeg', quality: 55 });
}
console.log('errors', log.errors.slice(0, 5), 'bad', log.bad.slice(0, 5));
await b.close();
