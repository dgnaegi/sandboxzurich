// Plaza/park comparison shots: one game view per place -> preview/plaza3_game_<id>.png (800x450), composed with the key photo
// by tests/plaza_sheet.py into preview/plaza3_<id>.jpg and the overview preview/plaza3_all.jpg.
// node tests/plaza.mjs [id,id,...]   (dev server on :5173)
import { chromium } from 'playwright';
const VIEWS = {
  roentgenplatz: '766,108,-0.22', helvetiaplatz: '785,-885,2.53', baeckeranlage: '505,-690,0.36', josefwiese: '500,185,-0.55',
  kasernenareal: '1190,-960,0.1', idaplatz: '-140,-1135,0.4', lindenplatz: '-2395,350,1.3', albisriederplatz: '-495,-668,-0.76',
  limmatplatz: '1135,25,-0.1', escher_wyss_platz: '455,715,-0.1', turbinenplatz: '0,600,0.25', stauffacher: '960,-1245,0.1',
  bullingerplatz: '-41,-522,0.17', hardplatz: '-110,-175,2.75', rosa_luxemburg_platz: '-1448,452,-1.06',
};
const only = process.argv[2]?.split(',');
const OUT = new URL('../../preview/', import.meta.url).pathname;
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
for (const [id, at] of Object.entries(VIEWS)) {
  if (only && !only.includes(id)) continue;
  await p.goto(`http://localhost:5173/?at=${at}&t=11:30`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
  await p.waitForTimeout(7000);
  await p.screenshot({ path: `${OUT}plaza3_game_${id}.png` });
  console.log(id, await p.textContent('#stats'));
}
await b.close();
