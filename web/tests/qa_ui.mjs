// QA: UI flows on phone landscape + PC: help card, menu, settings, imprint, clock, map open/zoom/jump (checks spawn spot).
import { launch, open, OUT, touch } from './qa_lib.mjs';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const tag = process.argv[3] ?? 'local';
const b = await launch();
for (const vp of ['phoneL', 'pc', 'phoneP']) {
  const { ctx, page, log, cdp } = await open(b, vp, `${BASE}/?at=789,-873,0.3&t=12:00&help&nopost`);
  const tap = async (sel) => { if (cdp) await page.tap(sel); else await page.click(sel); await page.waitForTimeout(500); };
  const shot = (n) => page.screenshot({ path: `${OUT}qa_review_ui_${tag}_${vp}_${n}.jpg`, type: 'jpeg', quality: 55 });
  await page.waitForTimeout(1200);
  const hc = await page.evaluate(() => document.getElementById('helpcard')?.innerText.replace(/\n/g, ' | '));
  console.log(vp, 'helpcard:', hc); await shot('1help');
  if (await page.$('#helpcard')) { await page.evaluate(() => document.getElementById('helpcard')?.click()); await page.waitForTimeout(600); }
  await tap('#btn-menu').catch((e) => console.log('menu btn fail', String(e).slice(0, 80)));
  await shot('2menu');
  console.log(vp, 'menu:', await page.evaluate(() => document.getElementById('menu')?.innerText.replace(/\n/g, ' | ')));
  await tap('#m-settings').catch(() => {}); await shot('3settings');
  console.log(vp, 'settings:', await page.evaluate(() => document.getElementById('menu')?.innerText.replace(/\n/g, ' | ').slice(0, 500)));
  // back / imprint
  await page.keyboard.press('Escape'); await page.waitForTimeout(300);
  const mv = await page.evaluate(() => getComputedStyle(document.getElementById('menu')).display);
  if (mv !== 'none') { await tap('#m-imprint').catch(() => {}); await shot('4imprint'); console.log(vp, 'imprint:', await page.evaluate(() => document.getElementById('menu')?.innerText.replace(/\n/g, ' | ').slice(0, 700))); }
  await page.keyboard.press('Escape'); await page.waitForTimeout(300);
  await page.evaluate(() => { const m = document.getElementById('menu'); if (m && getComputedStyle(m).display !== 'none') document.getElementById('m-continue')?.click(); });
  await page.waitForTimeout(400);
  // clock
  await tap('#clock').catch(() => {}); await shot('5clock');
  console.log(vp, 'clockpanel:', await page.evaluate(() => document.getElementById('clockpanel')?.innerText.replace(/\n/g, ' | ')));
  await page.evaluate(() => document.getElementById('clock')?.click()); await page.waitForTimeout(300);
  // map
  await tap('#radar'); await shot('6map');
  const vis = await page.evaluate(() => getComputedStyle(document.getElementById('bigmap')).display);
  console.log(vp, 'map display', vis, 'title', await page.evaluate(() => document.getElementById('bigmap-title')?.innerText), 'legend', await page.evaluate(() => document.getElementById('bigmap-legend')?.innerText.replace(/\n/g, ' | ')));
  // zoom in via button 3x then out 6x
  for (let i = 0; i < 3; i++) await tap('#bigmap-in'); await shot('7mapzoom');
  for (let i = 0; i < 7; i++) await tap('#bigmap-out'); await shot('8mapout');
  // jump by clicking a grid of points
  const W = (await page.evaluate(() => [innerWidth, innerHeight]));
  const res = [];
  await page.evaluate(async () => { const m = await import('/src/world/railzone.ts'); await m.loadRailZone(); window.__inRail = m.inRail; });
  for (let gy = 0; gy < 4; gy++) for (let gx = 0; gx < 5; gx++) {
    if (vp === 'phoneP' && (gx + gy) % 2) continue;
    const px = W[0] * (0.2 + gx * 0.15), py = W[1] * (0.25 + gy * 0.17);
    if ((await page.evaluate(() => getComputedStyle(document.getElementById('bigmap')).display)) === 'none') await tap('#radar');
    const before = await page.evaluate(() => [window.sbxPlayer.x, window.sbxPlayer.y]);
    if (cdp) { await touch(cdp, 'touchStart', [[px, py]]); await touch(cdp, 'touchEnd', []); await page.mouse.click(px, py).catch(() => {}); } else await page.mouse.click(px, py);
    await page.waitForTimeout(1800);
    const r = await page.evaluate(() => { const p = window.sbxPlayer, t = window.sbxTiles; const d = document.getElementById('bigmap'); return { x: +p.x.toFixed(1), y: +p.y.toFixed(1), z: +p.z.toFixed(1), ins: t.colliders.inside(p.x, p.y), rail: window.__inRail(p.x, p.y), play: t.inPlay(p.x, p.y), mapOpen: getComputedStyle(d).display !== 'none', place: document.getElementById('place-name')?.innerText }; });
    res.push({ click: [px | 0, py | 0], moved: Math.hypot(r.x - before[0], r.y - before[1]) > 3, ...r });
    if (res.length % 4 === 0 && vp === 'pc') await shot('9jump' + res.length);
  }
  console.log(vp, 'jumps', res.filter((r) => r.moved).length, '/', res.length);
  for (const r of res) if (r.moved && (r.ins || r.rail || !r.play)) console.log('  BAD spawn', JSON.stringify(r));
  console.log('  jumps:', res.map((r) => (r.moved ? `${r.x},${r.y}${r.rail ? 'R' : ''}${r.ins ? 'B' : ''}@z${r.z}` : '-')).join(' '));
  console.log(vp, 'errors', log.errors.slice(0, 5), 'bad', log.bad.slice(0, 5));
  await ctx.close();
}
await b.close();
