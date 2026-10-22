// Ad-hoc: player inside the Langstrassen-Unterfuehrung (street floor + passage) -> PC and phone shots. usage: node tests/_lu_inside.mjs <outprefix>
import { chromium } from 'playwright';
const out = process.argv[2];
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const A = [894.04, -363.94], D = [0.402, 0.916], N = [0.916, -0.402];
const at = (s, o) => [A[0] + D[0] * s + N[0] * o, A[1] + D[1] * s + N[1] * o];
const spots = [[at(12, 0), -8.25, 0.42], [at(30, 0), -8.4, 0.42], [at(29, 0), -8.4, 3.6], [at(17, 0), -8.3, 3.6]];
for (const [tag, vp, touch] of [['pc', { width: 800, height: 450 }, false], ['ph', { width: 390, height: 700 }, true]]) {
  const ctx = await b.newContext({ viewport: vp, hasTouch: touch, isMobile: touch });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  await page.goto('http://localhost:5173/?at=900,-340,0&t=13:00&nopost' + (touch ? '&touch=1' : ''));
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.waitForTimeout(2500);
  let n = 0;
  for (const [[x, y], z, yaw] of spots) {
    const r = await page.evaluate(([x, y, z, yaw]) => { const p = window.sbxPlayer; p.x = x; p.y = y; p.z = z; p.yaw = yaw; p.heading = yaw; return window.sbxTiles.groundAt(x, y, z); }, [x, y, z, yaw]);
    await page.waitForTimeout(2500);
    console.log(tag, n, x.toFixed(1), y.toFixed(1), 'ground', JSON.stringify(r), JSON.stringify(await page.evaluate(() => { const p = window.sbxPlayer; return [p.x.toFixed(1), p.y.toFixed(1), p.z.toFixed(2)]; })));
    await page.screenshot({ path: `${out}_${tag}_${n++}.png` });
  }
  await ctx.close();
}
await b.close();
