// First impression: loading bar, controls card, settings, WebGL2-missing message. Contact sheet via tests/sheet.py.
import { chromium, devices } from 'playwright';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const OUT = process.argv[3] ?? '/tmp/ui2';
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
const ok = (c, m) => console.log(c ? 'OK  ' : 'FAIL', m);
const views = [['pc', { viewport: { width: 1280, height: 720 } }], ['ph', { ...devices['iPhone 13'], viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true }], ['pl', { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true }]];
for (const [n, opt] of views) {
  const ctx = await browser.newContext(opt);
  const page = await ctx.newPage();
  await page.goto(`${BASE}/?help&t=12:00`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1800);
  await page.screenshot({ path: `${OUT}/${n}_1load.png` });
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.waitForTimeout(1200);
  ok(await page.evaluate(() => !document.getElementById('loading')), `${n}: loading removed`);
  await page.screenshot({ path: `${OUT}/${n}_2help.png` });
  await page.click('#helpcard');
  await page.waitForTimeout(600);
  ok(await page.evaluate(() => !document.getElementById('helpcard')), `${n}: help dismissed`);
  await page.click('#btn-menu'); await page.click('#m-settings'); await page.waitForTimeout(200);
  await page.click('[data-gfx=sparen]'); await page.waitForTimeout(200);
  ok(await page.evaluate(() => localStorage.getItem('sbz-settings').includes('sparen') && window.sbxRenderer.getPixelRatio() === 0.75), `${n}: sparen applied+saved`);
  await page.screenshot({ path: `${OUT}/${n}_3settings.png` });
  await ctx.close();
}
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
const page = await ctx.newPage();
await page.addInitScript(() => { const g = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext = function (t, ...a) { return t === 'webgl2' ? null : g.call(this, t, ...a); }; });
await page.goto(`${BASE}/`); await page.waitForTimeout(800);
ok(await page.evaluate(() => document.getElementById('ld-msg').textContent.includes('WebGL')), 'no-WebGL2 message');
await page.screenshot({ path: `${OUT}/err.png` });
await browser.close();
