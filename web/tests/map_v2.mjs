// Map screenshots (desktop + phone): overview, zoomed, radar crops, clock panel -> preview/map_v2_parts/*.png (sheet made by tests/map_v2_sheet.py)
import { chromium, devices } from 'playwright';
import { mkdirSync } from 'fs';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const out = new URL('../../preview/map_v2_parts/', import.meta.url).pathname;
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
for (const mobile of [false, true]) {
  const ctx = await browser.newContext(mobile
    ? { ...devices['iPhone 13'], viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true }
    : { viewport: { width: 1280, height: 720 } });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  const tag = mobile ? 'phone' : 'desktop';
  await page.goto(`${BASE}/?at=785,-635,0.37&t=17:30&nopost`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.waitForTimeout(1500);
  const r = await page.locator('#radar').boundingBox();
  await page.screenshot({ path: `${out}${tag}_radar.png`, clip: { x: 0, y: 0, width: Math.min(r.width + 40, 260), height: r.height + 40 } });
  await page.evaluate(() => window.sbxMap.toggle(true));
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${out}${tag}_map.png` });
  await page.evaluate(() => { const m = window.sbxMap; m.showVelo = true; m.data.loadVelo(); m.view.cx = 785; m.view.cy = -600; m.view.s = window.innerWidth < 500 ? 0.9 : 0.8; m.baseKey = ''; });
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${out}${tag}_zoom.png` });
  await page.evaluate(() => { window.sbxMap.toggle(false); });
  await page.tap?.call(page, '#clock').catch(() => {});
  if (!mobile) await page.click('#clock').catch(() => {});
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${out}${tag}_clock.png` });
  const t = await page.evaluate(() => { const m = window.sbxMap; const t0 = performance.now(); for (let i = 0; i < 30; i++) m.drawRadar(785, -635, i * 0.1, 0, []); return (performance.now() - t0) / 30; });
  console.log(tag, 'radar draw ms', t.toFixed(2));
  await ctx.close();
}
await browser.close();
