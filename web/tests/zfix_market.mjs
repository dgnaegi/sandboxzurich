import { chromium } from 'playwright';
const OUT = new URL('../../preview/', import.meta.url).pathname;
const browser = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const page = await (await browser.newContext({ viewport: { width: 800, height: 450 } })).newPage();
await page.goto('http://localhost:5173/?at=672,-930&day=5&t=11:00');
await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
await page.waitForTimeout(9000);
console.log(await page.evaluate(() => { const p = window.sbxPlayer; return [p.x, p.y, p.yaw]; }));
for (const [i, yaw] of [0, 1.57, 3.14, 4.71].entries()) {
  await page.evaluate((y) => { window.sbxPlayer.yaw = y; }, yaw);
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${OUT}zfix_flohmarkt_${i}.jpg`, type: 'jpeg', quality: 60 });
}
await browser.close();
