// Names/labels at 8 street corners -> preview/_names_<tag>_<i>.png ; node tests/names_shots.mjs before|after
import { chromium } from 'playwright';
const tag = process.argv[2] ?? 'a';
const OUT = new URL('../../preview/', import.meta.url).pathname;
import { readFileSync } from 'fs';
const P = JSON.parse(readFileSync(new URL('../../preview/_names_pts.json', import.meta.url)));
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const pg = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
pg.on('pageerror', (e) => console.log('pageerror', e.message));
for (const [i, at] of P.entries()) {
  await pg.goto(`http://localhost:5173/?at=${at}&t=14:00`);
  await pg.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await pg.waitForTimeout(5000);
  await pg.screenshot({ path: `${OUT}_names_${tag}_${i}.png` });
}
await b.close();
