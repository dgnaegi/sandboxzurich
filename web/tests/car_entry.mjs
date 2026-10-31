// QA: car entry on a slow network + stuck failsafe (player/vehicle_use.ts, player/stuck.ts).
// 1. Slow network (drive model delayed 2.5 s): E on a parked car must not remove the car; walking away during the download
//    cancels the entry, nobody is teleported back, the parked car is still there.
// 2. Mounting a scooter during the download: when the model arrives the player gets off, the scooter is left standing, no
//    scooter model rides along in the car or sticks to the figure after getting out.
// 3. Stuck: boxed in by a ring of posts (tree-and-fence trap), holding the throttle shows the hint after ~4.5 s and frees
//    the car after ~7 s via the nearest legal spot (rescues counter); idling never triggers it. Usage: node tests/car_entry.mjs [base]
import { launch, open } from './qa_lib.mjs';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const URL = `${BASE}/?at=785,-635,0.37&t=12:00&nohelp&nopost`;
const b = await launch();
let fails = 0;
const check = (name, ok, extra = '') => { console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${extra ? '  ' + extra : ''}`); if (!ok) fails++; };
const standByCar = (page) => page.evaluate(() => {
  const p = window.sbxPlayer, list = window.sbxParked.near(p.x, p.y, 120).filter((s) => !s.taken).sort((a, b) => Math.hypot(a.x - p.x, a.y - p.y) - Math.hypot(b.x - p.x, b.y - p.y));
  const s = list[0]; if (!s) return null;
  p.teleport(s.x + Math.cos(s.h) * 2.4, s.y - Math.sin(s.h) * 2.4, 0);
  window.__slot = s;
  return { x: +s.x.toFixed(1), y: +s.y.toFixed(1), type: s.type };
});
const slowModels = (page, ms) => page.route('**/models/cars/*_drive.glb*', async (route) => { await new Promise((r) => setTimeout(r, ms)); await route.continue(); });
const state = (page) => page.evaluate(() => { const p = window.sbxPlayer, cu = window.sbxCarUse; return { driving: !!p.driving, riding: !!p.riding, loading: cu.loading, taken: window.__slot?.taken ?? null, scooterVisible: p.scooter.group.visible, bikeVisible: p.rig.group.visible, bodyVisible: p.body.root.visible, d: window.__slot ? +Math.hypot(p.x - window.__slot.x, p.y - window.__slot.y).toFixed(1) : null }; });

// --- 1. slow network, walk away ---------------------------------------------------------------------------------
{
  const { ctx, page, log } = await open(b, 'pc', URL);
  await slowModels(page, 2500);
  await page.waitForTimeout(1200);
  const car = await standByCar(page);
  check('1 parked car found', !!car, JSON.stringify(car));
  await page.waitForTimeout(300);
  const t0 = await page.evaluate(() => { const cu = window.sbxCarUse, t = cu.nearest(); if (!t) return null; void cu.enter(t); return { loading: cu.loading, taken: window.__slot.taken, prompt: '' }; });
  check('1 E starts the download, car stays parked', !!t0 && t0.loading && !t0.taken, JSON.stringify(t0));
  await page.waitForTimeout(400);
  check('1 prompt says loading', /geladen/.test(await page.evaluate(() => document.getElementById('prompt').textContent)));
  await page.evaluate(() => { const p = window.sbxPlayer; p.teleport(p.x + 12, p.y + 12, 0); });   // walk out of reach
  await page.waitForTimeout(3200);
  const s1 = await state(page);
  check('1 walked away: entry cancelled, no teleport back, car still parked', !s1.driving && !s1.taken && !s1.loading && s1.d > 10, JSON.stringify(s1));
  check('1 no page errors', log.errors.filter((e) => !/cloudflareinsights|ERR_FAILED/.test(e)).length === 0, log.errors.slice(0, 2).join(' | '));
  await ctx.close();
}

// --- 2. slow network, mount a scooter during the download -----------------------------------------------------------
{
  const { ctx, page, log } = await open(b, 'pc', URL);
  await slowModels(page, 2500);
  await page.waitForTimeout(1200);
  await standByCar(page);
  await page.waitForTimeout(300);
  const t0 = await page.evaluate(() => {
    const cu = window.sbxCarUse, t = cu.nearest(); if (!t) return null; void cu.enter(t);
    const p = window.sbxPlayer, sc = window.sbxScooters;
    sc.drop(p.x + 1.0, p.y, p.z, 0, window.__slot.color);   // a rental scooter right here
    const slot = sc.nearest(p.x + 1.0, p.y, 2); if (!slot) return { noScooter: true };
    sc.take(slot); p.mount(slot);   // what E does on a scooter (main.ts use())
    return { loading: cu.loading, riding: !!p.riding, scooterVisible: p.scooter.group.visible, dropped: sc.dropped.count };
  });
  check('2 on the scooter while the model loads', !!t0 && t0.loading && t0.riding && t0.scooterVisible, JSON.stringify(t0));
  await page.waitForTimeout(3200);
  const s2 = await state(page);
  const after = await page.evaluate(() => window.sbxScooters.dropped.count);
  check('2 model arrived: in the car, off the scooter, scooter model hidden', s2.driving && !s2.riding && !s2.scooterVisible && !s2.bikeVisible && s2.taken, JSON.stringify(s2));
  check('2 scooter left standing (one more dropped scooter)', !!t0 && after === t0.dropped + 1, `${t0?.dropped} -> ${after}`);
  await page.evaluate(() => window.sbxCarUse.exit());
  await page.waitForTimeout(300);
  const s2b = await state(page);
  check('2 got out: walking figure, nothing glued to it', !s2b.driving && !s2b.riding && !s2b.scooterVisible && !s2b.bikeVisible && s2b.bodyVisible, JSON.stringify(s2b));
  check('2 no page errors', log.errors.filter((e) => !/cloudflareinsights|ERR_FAILED/.test(e)).length === 0, log.errors.slice(0, 2).join(' | '));
  await ctx.close();
}

// --- 3. stuck against a wall -> hint, then rescue --------------------------------------------------------------------
{
  const { ctx, page, log } = await open(b, 'pc', URL);
  await page.waitForTimeout(1200);
  await standByCar(page);
  await page.waitForTimeout(300);
  const got = await page.evaluate(async () => { const cu = window.sbxCarUse, t = cu.nearest(); if (!t) return false; await cu.enter(t); return !!window.sbxPlayer.driving; });
  check('3 in the car', got);
  // the trap: a ring of trunks (solid circles, like trees or fence posts) around the car, no way out in any direction
  const placed = await page.evaluate(() => {
    const p = window.sbxPlayer, car = p.driving, t = window.sbxTiles;
    const rows = [];
    for (let k = 0; k < 8; k++) { const a = (k / 8) * Math.PI * 2; rows.push([car.x + Math.cos(a) * 3.0, car.y + Math.sin(a) * 3.0, 0.9]); }
    t.colliders.addCircles('qa-trap', rows);
    return { x: +car.x.toFixed(1), y: +car.y.toFixed(1), ring: rows.length };
  });
  check('3 car boxed in by a ring of posts', !!placed, JSON.stringify(placed));
  const hints = [];
  const start = await page.evaluate(() => ({ x: window.sbxPlayer.driving.x, y: window.sbxPlayer.driving.y, rescues: window.sbxCarUse.rescues }));
  await page.keyboard.down('KeyW');
  let rescuedAt = null, warnAt = null;
  for (let i = 0; i < 36; i++) {   // up to 10.8 s
    await page.waitForTimeout(300);
    const s = await page.evaluate(() => ({ rescues: window.sbxCarUse.rescues, hint: document.getElementById('drivehint')?.textContent ?? '', op: document.getElementById('drivehint')?.style.opacity ?? '0', speed: +Math.abs(window.sbxPlayer.driving?.speed ?? 0).toFixed(1) }));
    if (s.hint && !hints.includes(s.hint)) hints.push(s.hint);
    if (warnAt === null && /Festgefahren/.test(s.hint)) warnAt = (i + 1) * 0.3;
    if (s.rescues > start.rescues) { rescuedAt = (i + 1) * 0.3; break; }
  }
  await page.keyboard.up('KeyW');
  const end = await page.evaluate(() => { const c = window.sbxPlayer.driving, col = window.sbxTiles.colliders; return { x: c.x, y: c.y, inside: col.inside(c.x, c.y), speed: +Math.abs(c.speed).toFixed(1), legal: window.sbxTiles.inPlay(c.x, c.y) }; });
  const moved = Math.hypot(end.x - start.x, end.y - start.y);
  // 2 s of path have to exist first, so the hint lands at ~4.5 s and the rescue at ~7 s after the throttle goes down
  check('3 hint "Festgefahren" after 2.5 s of stuckness', warnAt !== null && warnAt >= 3.0 && warnAt <= 6.5, `at ${warnAt?.toFixed(1)}s; hints: ${hints.join(' | ')}`);
  check('3 rescued 2.5 s after the hint', rescuedAt !== null && rescuedAt >= 5.5 && rescuedAt <= 9.5 && rescuedAt - warnAt >= 1.8, `at ${rescuedAt?.toFixed(1)}s`);
  check('3 car set down outside the ring on clear ground', moved > 3.5 && !end.inside && end.legal, `moved ${moved.toFixed(1)} m -> ${end.x.toFixed(1)},${end.y.toFixed(1)} speed ${end.speed}`);
  // idling with the throttle released must never trigger it
  const r0 = await page.evaluate(() => window.sbxCarUse.rescues);
  await page.waitForTimeout(6000);
  check('3 idle: no rescue', (await page.evaluate(() => window.sbxCarUse.rescues)) === r0);
  check('3 no page errors', log.errors.filter((e) => !/cloudflareinsights|ERR_FAILED/.test(e)).length === 0, log.errors.slice(0, 2).join(' | '));
  await ctx.close();
}

await b.close();
console.log(fails ? `CAR_ENTRY FAIL ${fails}` : 'CAR_ENTRY OK');
process.exit(fails ? 1 : 0);
