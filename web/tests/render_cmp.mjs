// Before/after look comparison: fixed points x 3 times of day -> contact sheet. Usage: node tests/render_cmp.mjs <name> [phone]
import { chromium, devices } from 'playwright';
import { mkdirSync } from 'node:fs';
const name = process.argv[2] ?? 'before'; const phone = process.argv[3] === 'phone';
const BASE = 'http://localhost:5173';
const OUT = `/private/tmp/claude-501/-Users-danielgnagi-sandboxzurich/c6777b7a-a5e5-418a-994d-c9027f86d233/scratchpad/${name}${phone ? '_phone' : ''}/`;
mkdirSync(OUT, { recursive: true });
const P = { helvetia: '760,-905,-0.3', langstrasse: '785,-635,0.37', rosaluxemburg: '-1463,458,-0.40', letzigrund: '-969,-60,3.14', hardau: '-470,-170,3.4' };
const T = { mittag: '12:30', abend: '18:15', nacht: '22:30' };
const browser = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const ctx = await browser.newContext(phone ? { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true } : { viewport: { width: 1280, height: 720 } });
const page = await ctx.newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
for (const [p, at] of Object.entries(P)) for (const [t, hm] of Object.entries(T)) {
  await page.goto(`${BASE}/?at=${at}&t=${hm}`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `${OUT}${p}_${t}.png` });
}
await browser.close();
console.log('done', OUT);
