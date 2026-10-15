import { chromium } from 'playwright';
const [,, out, ...ats] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
let i = 0;
for (const at of ats) {
  await p.goto(`http://localhost:5173/?at=${at}`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
  await p.waitForTimeout(7000);
  const n = await p.evaluate(() => { let c = 0; window.sbxScene.traverse((o) => { if (o.name?.startsWith?.('r_') || o.userData?.rail) c++; }); return c; });
  console.log(at, 'railobj', n, await p.textContent('#stats'));
  await p.screenshot({ path: `${out}_${i++}.png` });
}
await b.close();
