// Touch controls on a phone viewport: joystick moves the player, the E button mounts a bike, radar opens the map.
import { chromium, devices } from 'playwright';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const browser = await chromium.launch({ args: ['--use-gl=angle'] });
const ctx = await browser.newContext({ ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true });
const page = await ctx.newPage();
const cdp = await ctx.newCDPSession(page);
const ok = (c, m) => console.log(c ? 'OK  ' : 'FAIL', m);
await page.goto(`${BASE}/?at=785,-635,0.37&t=12:00`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
const pos = () => page.evaluate(() => [window.sbxPlayer.x, window.sbxPlayer.y]);
const touch = (type, pts) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: pts.map(([x, y], i) => ({ x, y, id: i })) });
const a = await pos();
await touch('touchStart', [[150, 260]]);
for (let i = 1; i <= 10; i++) { await touch('touchMove', [[150, 260 - i * 6]]); await page.waitForTimeout(40); }
await page.waitForTimeout(1500);
await touch('touchEnd', []);
const b = await pos();
ok(Math.hypot(b[0] - a[0], b[1] - a[1]) > 2, `joystick moved ${Math.hypot(b[0] - a[0], b[1] - a[1]).toFixed(1)} m`);
ok(await page.evaluate(() => getComputedStyle(document.getElementById('touchbtns')).display !== 'none'), 'touch buttons visible');
await page.evaluate(() => { const p = window.sbxPlayer, s = window.sbxBikes.nearest(p.x, p.y, 200); if (s) p.teleport(s.x + 0.6, s.y, 0); });
await page.waitForTimeout(200);
await page.tap('#btn-use');
await page.waitForTimeout(300);
ok(await page.evaluate(() => !!window.sbxPlayer.riding), 'E button mounts bike');
await page.tap('#radar');
await page.waitForTimeout(300);
ok(await page.evaluate(() => getComputedStyle(document.getElementById('bigmap')).display === 'block'), 'radar tap opens map');
await page.screenshot({ path: new URL('../../preview/touch_map.png', import.meta.url).pathname });
await browser.close();
