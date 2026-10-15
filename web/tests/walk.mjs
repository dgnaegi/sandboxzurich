// Walk test: W moves the player forward; walking into a facade stops at the wall.
import { chromium } from 'playwright';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 800, height: 450 } });
const pos = () => page.evaluate(() => [window.gtaPlayer.x, window.gtaPlayer.y].map((v) => +v.toFixed(2)));
// Langstrasse, looking along the street (NNE)
await page.goto(`${BASE}/?at=785,-635,0.37`);
await page.waitForFunction(() => window.gtaReady);
const a = await pos();
await page.keyboard.down('KeyW'); await page.waitForTimeout(1000); await page.keyboard.up('KeyW');
const b = await pos();
console.log('walk 1s', a, '->', b, 'dist', Math.hypot(b[0] - a[0], b[1] - a[1]).toFixed(2));
// turn towards the facade (west-north-west) and run into it for 4 s
await page.evaluate(() => { window.gtaPlayer.yaw = -1.2; });
await page.keyboard.down('ShiftLeft'); await page.keyboard.down('KeyW');
await page.waitForTimeout(4000);
await page.keyboard.up('KeyW'); await page.keyboard.up('ShiftLeft');
const c = await pos();
console.log('run 4s into wall', b, '->', c, 'dist', Math.hypot(c[0] - b[0], c[1] - b[1]).toFixed(2), '(free run would be ~34 m)');
await browser.close();
