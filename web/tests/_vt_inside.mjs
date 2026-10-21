// Ad-hoc: player placed inside the Stadttunnel bike tunnel (deck height) -> screenshots
import { chromium } from 'playwright';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const out = process.argv[2];
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
page.on('console', (m) => { if (m.type() === 'error') console.log('console', m.text().slice(0, 200)); });
await page.goto('http://localhost:5173/?at=1466,-733,0.51&t=13:00&nopost');
await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
await page.waitForTimeout(2500);
const deck = JSON.parse(require('fs').readFileSync('public/data/velotunnel_decks.json','utf8')).decks[0].p;
const pts = [deck[6], deck[25], deck[45], deck[70]];
let n = 0;
for (const [x, y, z] of pts) {
  const info = await page.evaluate(([x, y, z]) => { const p = window.sbxPlayer, t = window.sbxTiles; p.x = x; p.y = y; p.z = z; p.yaw = 0.51; p.heading = 0.51; return { z, ga: t.groundAt(x, y, z) }; }, [x, y, z]);
  await page.keyboard.down('KeyW'); await page.waitForTimeout(1200); await page.keyboard.up('KeyW');
  console.log(' after walk', JSON.stringify(await page.evaluate(() => { const p = window.sbxPlayer; return [p.x.toFixed(1), p.y.toFixed(1), p.z.toFixed(2)]; })));
  console.log(x, y, JSON.stringify(info));
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${out}_${n++}.png` });
}
await b.close();
