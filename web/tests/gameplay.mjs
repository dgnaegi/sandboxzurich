// Gameplay smoke test: walk to a parked bike, press E (mount), ride 3 s, press E (dismount), check missions start.
import { chromium } from 'playwright';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await browser.newPage({ viewport: { width: 960, height: 540 } });
page.on('pageerror', (e) => console.log('pageerror', e.message));
await page.goto(`${BASE}/?at=785,-635,0.37&t=12:00&nopost&missions`);
await page.waitForFunction(() => window.gtaReady, null, { timeout: 60000 });
const ok = (c, msg) => console.log(c ? 'OK  ' : 'FAIL', msg);
// put the player next to the nearest parked bike
const bike = await page.evaluate(() => {
  const p = window.gtaPlayer, b = window.gtaBikes.nearest(p.x, p.y, 200);
  if (b) p.teleport(b.x + 0.6, b.y, 0);
  return b && { x: b.x, y: b.y };
});
ok(!!bike, `bike found ${JSON.stringify(bike)}`);
await page.waitForTimeout(300);
await page.keyboard.press('KeyE');
await page.waitForTimeout(300);
ok(await page.evaluate(() => !!window.gtaPlayer.riding), 'mounted with E');
const a = await page.evaluate(() => [window.gtaPlayer.x, window.gtaPlayer.y]);
await page.keyboard.down('KeyW'); await page.waitForTimeout(3000); await page.keyboard.up('KeyW');
const b = await page.evaluate(() => [window.gtaPlayer.x, window.gtaPlayer.y, window.gtaPlayer.speed]);
ok(Math.hypot(b[0] - a[0], b[1] - a[1]) > 4, `rode ${Math.hypot(b[0] - a[0], b[1] - a[1]).toFixed(1)} m, speed ${b[2].toFixed(1)} m/s`);
await page.waitForTimeout(2500);
await page.keyboard.press('KeyE');
await page.waitForTimeout(300);
ok(await page.evaluate(() => !window.gtaPlayer.riding), 'dismounted with E');
console.log('stars', await page.evaluate(() => window.gtaState.stars), 'money', await page.evaluate(() => window.gtaState.money));
// mission: step onto the Velokurier start beacon
await page.evaluate(() => window.gtaPlayer.teleport(770, -893, 0));
await page.waitForTimeout(800);
ok(await page.evaluate(() => document.getElementById('mission').textContent.includes('Velokurier')), 'mission started at beacon');
await page.screenshot({ path: new URL('../../preview/gameplay.png', import.meta.url).pathname });
await browser.close();
