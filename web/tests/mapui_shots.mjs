// Map UI shots (desktop, phone portrait, phone landscape): overview, close-up, radar -> dir given as argv[2]
import { chromium, devices } from 'playwright';
import { mkdirSync } from 'fs';
const out = process.argv[2]; mkdirSync(out, { recursive: true });
const BASE = 'http://localhost:5173';
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
const cfgs = { desktop: { viewport: { width: 1280, height: 720 } },
  portrait: { ...devices['iPhone 13'], viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true },
  land: { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true } };
for (const [tag, cfg] of Object.entries(cfgs)) {
  const ctx = await browser.newContext(cfg); const page = await ctx.newPage();
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  await page.goto(`${BASE}/?at=785,-635,0.37&t=17:30&nopost`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.waitForTimeout(1500);
  const r = await page.locator('#radar').boundingBox();
  await page.screenshot({ path: `${out}/${tag}_radar.png`, clip: { x: 0, y: 0, width: r.x + r.width + 20, height: r.y + r.height + 20 } });
  await page.evaluate(() => window.sbxMap.toggle(true)); await page.waitForTimeout(600);
  await page.screenshot({ path: `${out}/${tag}_map.png` });
  await page.evaluate(() => { const m = window.sbxMap; m.view.cx = 785; m.view.cy = -600; m.view.s = 1.4; m.baseKey = ''; });
  await page.waitForTimeout(700);
  await page.screenshot({ path: `${out}/${tag}_close.png` });
  await ctx.close();
}
await browser.close();
