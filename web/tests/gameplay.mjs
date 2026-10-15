// Gameplay smoke test: walk to a parked bike, press E (mount), ride 3 s, press E (dismount), check that quests stay off.
import { chromium } from 'playwright';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await browser.newPage({ viewport: { width: 960, height: 540 } });
page.on('pageerror', (e) => console.log('pageerror', e.message));
await page.goto(`${BASE}/?at=785,-635,0.37&t=12:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
const ok = (c, msg) => console.log(c ? 'OK  ' : 'FAIL', msg);
// put the player next to the nearest parked bike
const bike = await page.evaluate(() => {
  const p = window.sbxPlayer, b = window.sbxBikes.nearest(p.x, p.y, 200);
  if (b) p.teleport(b.x + 0.6, b.y, 0);
  return b && { x: b.x, y: b.y };
});
ok(!!bike, `bike found ${JSON.stringify(bike)}`);
await page.waitForTimeout(300);
await page.keyboard.press('KeyE');
await page.waitForTimeout(300);
ok(await page.evaluate(() => !!window.sbxPlayer.riding), 'mounted with E');
const a = await page.evaluate(() => [window.sbxPlayer.x, window.sbxPlayer.y]);
await page.keyboard.down('KeyW'); await page.waitForTimeout(3000); await page.keyboard.up('KeyW');
const b = await page.evaluate(() => [window.sbxPlayer.x, window.sbxPlayer.y, window.sbxPlayer.speed]);
ok(Math.hypot(b[0] - a[0], b[1] - a[1]) > 4, `rode ${Math.hypot(b[0] - a[0], b[1] - a[1]).toFixed(1)} m, speed ${b[2].toFixed(1)} m/s`);
await page.waitForTimeout(2500);
await page.keyboard.press('KeyE');
await page.waitForTimeout(300);
ok(await page.evaluate(() => !window.sbxPlayer.riding), 'dismounted with E');
console.log('stars', await page.evaluate(() => window.sbxState.stars), 'money', await page.evaluate(() => window.sbxState.money));
// quests are disabled (User 2026-10-15): the former Velokurier beacon must not start anything
await page.evaluate(() => window.sbxPlayer.teleport(770, -893, 0));
await page.waitForTimeout(800);
ok(await page.evaluate(() => document.getElementById('mission').textContent === ''), 'quests are off (no mission on the beacon)');
await page.screenshot({ path: new URL('../../preview/gameplay.png', import.meta.url).pathname });
await browser.close();
