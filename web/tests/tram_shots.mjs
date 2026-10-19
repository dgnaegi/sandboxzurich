// Tram track look: spots from logs/tram_spots.json -> preview/tram_tracks_<tag>_<spot>.png ; sheet via sheet.py
import { chromium } from 'playwright';
import fs from 'fs';
const tag = process.argv[2] ?? 'a';
const OUT = new URL('../../preview/', import.meta.url).pathname;
const P = JSON.parse(fs.readFileSync(new URL('../../logs/tram_spots.json', import.meta.url)));
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const pg = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
pg.on('pageerror', (e) => console.log('pageerror', e.message));
for (const [n, [x, y, yaw]] of Object.entries(P)) {
  await pg.goto(`http://localhost:5173/?at=${x},${y},${yaw}&t=12:00&v=${tag}${Date.now()}`);
  await pg.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await pg.evaluate(() => { const p = window.sbxPlayer; p.pitch = 0.0; p.mesh.visible = false; });
  await pg.waitForTimeout(3500);
  await pg.screenshot({ path: `${OUT}tram_tracks_${tag}_${n}.png` });
}
await b.close();
