// Tree look: 5 spots x day/evening -> preview/_trees_<tag>_<spot>_<t>.png ; sheet via sheet.py (trees_v2.jpg)
import { chromium } from 'playwright';
const tag = process.argv[2] ?? 'a';
const OUT = new URL('../../preview/', import.meta.url).pathname;
const P = { josef: '430,188,0.8', baeck: '500.6,-749.9,0.47', park: '513,-712,2.2', sihl: '-674,-1188,0.3', helv: '640,-800,1.2' };
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const pg = await (await b.newContext({ viewport: { width: 900, height: 520 } })).newPage();
pg.on('pageerror', (e) => console.log('pageerror', e.message));
pg.on('console', (m) => { if (m.type() === 'error') console.log('console', m.text().slice(0, 160)); });
for (const [pn, at] of Object.entries(P)) for (const [tn, t] of [['day', '12:00'], ['eve', '17:40']]) {
  await pg.goto(`http://localhost:5173/?at=${at}&t=${t}`);
  await pg.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await pg.waitForTimeout(4000);
  await pg.screenshot({ path: `${OUT}_trees_${tag}_${pn}_${tn}.png` });
}
await b.close();
