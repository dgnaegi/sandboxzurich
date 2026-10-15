// Clock panel: tap the HUD clock -> panel -> "Nacht" (23:00) -> night; pause, speed, weekday, Esc/outside closes (phone and desktop).
import { chromium, devices } from 'playwright';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
const ok = (c, m) => console.log(c ? 'OK  ' : 'FAIL', m);
const shot = (n) => new URL(`../../preview/clock_${n}.png`, import.meta.url).pathname;

for (const mobile of [true, false]) {
  const ctx = await browser.newContext(mobile
    ? { ...devices['iPhone 13'], viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true }
    : { viewport: { width: 1280, height: 720 } });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  await page.goto(`${BASE}/?at=785,-635,0.37&t=12:00&nopost`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  const tag = mobile ? 'phone' : 'desktop';
  const vis = () => page.evaluate(() => getComputedStyle(document.getElementById('clockpanel')).display === 'block');
  const tap = (sel) => (mobile ? page.tap(sel) : page.click(sel));
  await tap('#clock');
  ok(await vis(), `${tag}: tap on clock opens panel`);
  await tap('#clockpanel [data-min="1380"]');
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => ({ min: window.sbxClock.min, night: window.sbxDaytime.night, label: document.getElementById('clock').textContent }));
  ok(r.min >= 1380 && r.min < 1385 && r.night > 0.5, `${tag}: Nacht 23:00 -> min ${r.min.toFixed(1)}, night ${r.night.toFixed(2)}, label "${r.label}"`);
  await page.screenshot({ path: shot(tag) });
  await tap('#clockpanel [data-rate="60"]');
  await tap('#cp-pause');
  await page.evaluate(() => { const s = document.getElementById('cp-slider'); s.value = '435'; s.dispatchEvent(new Event('input', { bubbles: true })); });
  await tap('#clockpanel [data-day="5"]');
  const t0 = await page.evaluate(() => window.sbxClock.min);
  await page.waitForTimeout(800);
  const s = await page.evaluate(() => ({ min: window.sbxClock.min, day: window.sbxClock.day, rate: window.sbxClock.rate, paused: window.sbxClock.paused }));
  ok(Math.abs(s.min - 435) < 1 && s.day === 5 && s.rate === 60 && s.paused && s.min === t0, `${tag}: slider 7:15, Sa, 60x, paused (${JSON.stringify(s)})`);
  await tap('#cp-pause');
  await page.waitForTimeout(1000);
  ok(await page.evaluate((m) => window.sbxClock.min > m + 20, s.min), `${tag}: 60x running advances`);
  if (mobile) { await page.tap('#radar'); await page.waitForTimeout(200); ok(!(await vis()), 'phone: outside tap closes panel'); }
  else {
    await page.mouse.click(640, 400);
    ok(!(await vis()), 'desktop: outside click closes');
    await tap('#clock'); ok(await vis(), 'desktop: reopen');
    await page.keyboard.press('Escape');
    ok(!(await vis()), 'desktop: Esc closes');
  }
  await ctx.close();
}
await browser.close();
