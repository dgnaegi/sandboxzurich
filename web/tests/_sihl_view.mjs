import { chromium } from 'playwright';
const out = process.argv[2];
const views = [[1402,-828,-1.29,'sihl'],[1462,-737,0.6,'vt']];
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const shots = [];
for (const [vw, vh, tag] of [[800,450,'pc'],[390,700,'ph']]) {
  const page = await (await b.newContext({ viewport: { width: vw, height: vh } })).newPage();
  for (const [x,y,yaw,n] of views) {
    await page.goto(`http://localhost:5173/?at=${x},${y},0&t=13:00&nopost`);
    await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
    await page.waitForTimeout(3000);
    await page.evaluate(([x,y,yaw]) => { const p = window.sbxPlayer; p.x = x; p.y = y; p.yaw = yaw; p.heading = yaw; }, [x,y,yaw]);
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${out}_${n}_${tag}.png` });
  }
}
await b.close();
