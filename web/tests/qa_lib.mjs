// Shared QA helpers
import { chromium, devices } from 'playwright';
export const OUT = new URL('../../preview/', import.meta.url).pathname;
export const VP = {
  phoneP: { ...devices['iPhone 13'], viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true },
  phoneL: { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true },
  pc: { viewport: { width: 1280, height: 720 } },
};
export async function open(browser, vp, url, { wait = true } = {}) {
  const ctx = await browser.newContext(VP[vp]);
  const page = await ctx.newPage();
  const log = { errors: [], warns: [], bad: [], long: 0 };
  page.on('pageerror', (e) => log.errors.push('pageerror: ' + e.message.slice(0, 200)));
  page.on('console', (m) => { if (m.type() === 'error') log.errors.push(m.text().slice(0, 200)); if (m.type() === 'warning') log.warns.push(m.text().slice(0, 160)); });
  page.on('response', (r) => { if (r.status() >= 400) log.bad.push(r.status() + ' ' + r.url().slice(0, 140)); });
  page.on('response', (r) => { if (/html/.test(r.headers()['content-type'] ?? '') && !/\/$|\.html|\?/.test(r.url()) ) log.bad.push('HTML-FALLBACK ' + r.url().slice(0, 140)); });
  page.on('requestfailed', (r) => log.bad.push('FAIL ' + r.url().slice(0, 140)));
  const t0 = Date.now();
  await page.goto(url);
  if (wait) await page.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
  log.loadMs = Date.now() - t0;
  const cdp = vp === 'pc' ? null : await ctx.newCDPSession(page);
  return { ctx, page, log, cdp };
}
export const touch = (cdp, type, pts) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: pts.map(([x, y], i) => ({ x, y, id: i })) });
export const launch = () => chromium.launch({ args: ['--js-flags=--expose-gc', '--use-gl=angle', '--enable-precise-memory-info'] });
export const P = (page) => page.evaluate(() => ({ x: +window.sbxPlayer.x.toFixed(2), y: +window.sbxPlayer.y.toFixed(2), z: +window.sbxPlayer.z.toFixed(2), s: +window.sbxPlayer.speed.toFixed(2) }));
