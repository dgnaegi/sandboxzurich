// usage: node tests/facades_look.mjs out_prefix "x,y,yaw&t=11:00" ...   (contact sheet via PIL afterwards)
import { chromium } from 'playwright';
const [,, out, ...ats] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 640, height: 400 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
let i = 0;
for (const at of ats) {
  await p.goto(`http://localhost:5173/?at=${at}`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
  await p.waitForTimeout(5000);
  await p.screenshot({ path: `${out}_${i++}.png` });
}
await b.close();
