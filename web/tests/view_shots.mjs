// Single game views (PC viewport) from a JSON list: node tests/view_shots.mjs <views.json> [baseUrl]
// views.json: [{"x":..,"y":..,"yaw":..,"out":"/abs/path.jpg"}, ...]  (local metres, yaw 0 = north, pi/2 = east). Used by pipeline/zones/zone_cmp.py.
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';

const views = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const BASE = process.argv[3] ?? 'http://localhost:5173';
const browser = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const page = await (await browser.newContext({ viewport: { width: 1280, height: 720 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
for (const v of views) {
  await page.goto(`${BASE}/?at=${v.x},${v.y},${v.yaw}&t=13:00&nopost`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: v.out, type: 'jpeg', quality: 80 });
}
await browser.close();
console.log('done', views.length, 'views');
