// Ad-hoc: tram decks at Kasernenstrasse/Sihlpost -> shots. usage: node tests/_tram_flat.mjs <outprefix>
import { chromium } from 'playwright';
const out = process.argv[2];
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const spots = [[1395, -828, 2.4, 'a'], [1370, -838, 0.6, 'b'], [1450, -862, 1.9, 'c']];
for (const [tag, vp, touch] of [['pc', { width: 800, height: 450 }, false], ['ph', { width: 390, height: 700 }, true]]) {
  const ctx = await b.newContext({ viewport: vp, hasTouch: touch, isMobile: touch });
  const page = await ctx.newPage();
  await page.goto('http://localhost:5173/?at=1395,-828,0&t=13:00&nopost' + (touch ? '&touch=1' : ''));
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.waitForTimeout(2500);
  let n = 0;
  for (const [x, y, yaw] of spots) {
    await page.evaluate(([x, y, yaw]) => { const p = window.sbxPlayer; p.x = x; p.y = y; p.z = window.sbxTiles.groundAt(x, y, 5) + 0.2; p.yaw = yaw; p.heading = yaw; }, [x, y, yaw]);
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${out}_${tag}_${n++}.png` });
  }
  await ctx.close();
}
await b.close();
