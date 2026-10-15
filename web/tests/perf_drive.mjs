// DRIVING variant of perf.mjs: steal a parked car, drive 10 s (phone viewport, 4x CPU throttle).
// Phone-like performance check: iPhone viewport, CPU throttled 4x (CDP), walk for 10 s, report fps and budgets.
// GPU is still the Mac's, so this tests CPU/JS/draw-call load, not mobile GPU fill rate.
import { chromium, devices } from 'playwright';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const browser = await chromium.launch({ args: ['--use-gl=angle', '--enable-precise-memory-info'] });
const ctx = await browser.newContext({ ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true });
const page = await ctx.newPage();
const cdp = await ctx.newCDPSession(page);
await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
const t0 = Date.now();
await page.goto(`${BASE}/?at=785,-635,0.37&debug`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
const loadS = (Date.now() - t0) / 1000;
await page.evaluate(() => {
  window._f = 0;
  const f = () => { window._f++; requestAnimationFrame(f); };
  requestAnimationFrame(f);
});
await page.evaluate(async () => { const p = window.sbxPlayer, c = window.sbxParked.near(p.x, p.y, 200)[0]; p.teleport(c.x + Math.cos(c.h) * 2.4, c.y - Math.sin(c.h) * 2.4, 0); await new Promise((r) => setTimeout(r, 400)); const n = window.sbxCarUse.nearest(); if (n) await window.sbxCarUse.enter(n); });
console.log('driving:', await page.evaluate(() => !!window.sbxPlayer.driving));
await page.keyboard.down('KeyW');
await page.waitForTimeout(10000);
await page.keyboard.up('KeyW');
const r = await page.evaluate(() => ({ frames: window._f, stats: document.getElementById('stats').textContent }));
const bytes = await page.evaluate(() => performance.getEntriesByType('resource').reduce((a, e) => a + (e.transferSize || 0), 0));
console.log(`load ${loadS.toFixed(1)} s · ${(bytes / 1e6).toFixed(1)} MB transferred · avg ${(r.frames / 10).toFixed(0)} fps (CPU 4x throttled) · ${r.stats}`);
await browser.close();
