import { chromium } from 'playwright';
const out = process.argv[2];
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
await page.goto(`http://localhost:5173/?at=1462,-737,0&t=13:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
await page.waitForTimeout(3000);
let i = 0;
for (const [x, y, yaw] of [[1466.5,-731,0.59],[1469,-727.5,0.59],[1472,-722,-2.5]]) {
  await page.evaluate(([x,y,yaw]) => { const p = window.sbxPlayer; p.x = x; p.y = y; p.yaw = yaw; p.heading = yaw; }, [x,y,yaw]);
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `${out}_vt2_${i++}.png` });
}
await b.close();
