// Desktop perf: 1280x720, walk 10 s, fps + budgets (no CPU throttle).
import { chromium } from 'playwright';
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const page = await (await b.newContext({ viewport: { width: 1280, height: 720 } })).newPage();
await page.goto('http://localhost:5173/?at=785,-635,0.37&debug');
await page.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
await page.evaluate(() => { window._f = 0; const f = () => { window._f++; requestAnimationFrame(f); }; requestAnimationFrame(f); });
await page.keyboard.down('KeyW'); await page.waitForTimeout(10000); await page.keyboard.up('KeyW');
const r = await page.evaluate(() => ({ f: window._f, s: document.getElementById('stats').textContent }));
console.log(`avg ${(r.f / 10).toFixed(0)} fps · ${r.s}`); await b.close();
