// QA: does the walking player pass through parked cars / NPCs / trams? (colliders only know building footprints)
import { launch, open } from './qa_lib.mjs';
const BASE = process.argv[2] ?? 'http://localhost:5199';
const b = await launch();
const { page, log } = await open(b, 'pc', `${BASE}/?at=789,-873,0&t=12:00&nopost`);
await page.waitForTimeout(2000);
// parked car
const r1 = await page.evaluate(async () => {
  const p = window.sbxPlayer, list = window.sbxParked.near(p.x, p.y, 150);
  const c = list[0]; if (!c) return null;
  return { x: c.x, y: c.y, h: c.h, type: c.type, n: list.length };
});
console.log('parked sample', r1);
await page.evaluate((c) => { const p = window.sbxPlayer; const hx = Math.sin(c.h), hy = Math.cos(c.h); p.teleport(c.x - hx * 6, c.y - hy * 6, c.h); p.heading = c.h; }, r1);
await page.waitForTimeout(500);
await page.keyboard.down('Shift'); await page.keyboard.down('KeyW'); let minD = 99;
for (let i = 0; i < 40; i++) { await page.waitForTimeout(100); minD = Math.min(minD, await page.evaluate((c) => Math.hypot(window.sbxPlayer.x - c.x, window.sbxPlayer.y - c.y), r1)); }
await page.keyboard.up('KeyW'); await page.keyboard.up('Shift');
console.log('walked toward parked car centre: min dist', minD.toFixed(2), '(<0.9 = inside car body)');
// NPC
const ped = await page.evaluate(() => { const p = window.sbxPlayer; const q = window.sbxCrowd.peds.find((d) => Math.hypot(d.x - p.x, d.y - p.y) < 60 && d.speed > 0.3); return q && { x: q.x, y: q.y }; });
console.log('ped', ped);
// tram
const tr = await page.evaluate(() => { const p = window.sbxPlayer; const c = window.sbxTransit.colliders().map((v) => ({ x: v.x, y: v.y, len: v.len })).sort((a, b) => Math.hypot(a.x - p.x, a.y - p.y) - Math.hypot(b.x - p.x, b.y - p.y)); return c.slice(0, 2); });
console.log('trams', tr);
console.log('errors', log.errors.slice(0, 3));
await b.close();
