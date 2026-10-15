// Shots for sites / crowds: node tests/life_shots.mjs [name,...]  -> ../preview/life_<name>_<vp>.png
import { chromium, devices } from 'playwright';
const BASE = 'http://localhost:5173';
const OUT = new URL('../../preview/', import.meta.url).pathname;
const POINTS = JSON.parse(process.env.PTS ?? '{}');
const VP = { desktop: { viewport: { width: 960, height: 540 } }, phone: { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true } };
const only = process.env.VP ? process.env.VP.split(',') : ['desktop'];
const browser = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
for (const vp of only) {
  const ctx = await browser.newContext(VP[vp]); const page = await ctx.newPage();
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.log('console', m.text().slice(0, 160)); });
  for (const [n, at] of Object.entries(POINTS)) {
    await page.goto(`${BASE}/?at=${at}&debug`);
    await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
    await page.waitForTimeout(4000);
    await page.screenshot({ path: `${OUT}life_${n}_${vp}.png` });
    console.log(n, vp, await page.textContent('#stats'));
  }
  await ctx.close();
}
await browser.close();
