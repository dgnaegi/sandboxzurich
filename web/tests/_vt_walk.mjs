// Ad-hoc: walk from the Europaplatz ramp into the Velotunnel along its axis, log height per 0.4 s; screenshots every 2 s
import { chromium } from 'playwright';
const out = process.argv[2], yaw = Number(process.argv[3] ?? 0.6), at = process.argv[4] ?? '1458,-743';
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await (await b.newContext({ viewport: { width: 640, height: 360 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
await page.goto(`http://localhost:5173/?at=${at},${yaw}&t=13:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
await page.waitForTimeout(2500);
await page.evaluate((yaw) => { const p = window.sbxPlayer; p.yaw = yaw; p.heading = yaw; }, yaw);
await page.keyboard.down('KeyW');
for (let i = 0; i < 40; i++) {
  await page.waitForTimeout(400);
  await page.evaluate((yaw) => { const p = window.sbxPlayer; p.yaw = yaw; }, yaw);
  const r = await page.evaluate(() => { const p = window.sbxPlayer, t = window.sbxTiles; return [p.x.toFixed(1), p.y.toFixed(1), p.z.toFixed(2), t.ground(p.x, p.y).toFixed(2)]; });
  console.log(i, r.join(' '));
  if (i % 5 === 4) await page.screenshot({ path: `${out}_${(i + 1) / 5}.png` });
}
await b.close();
