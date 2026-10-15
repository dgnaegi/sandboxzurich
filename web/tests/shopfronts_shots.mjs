// usage: node tests/shopfronts_shots.mjs  (reads ../logs/shopfronts_pick.json, writes ../logs/sf_shots/NN.png, 1040x390)
import { chromium } from 'playwright';
import fs from 'fs';
const pick = JSON.parse(fs.readFileSync('../logs/shopfronts_pick.json', 'utf8'));
fs.mkdirSync('../logs/sf_shots', { recursive: true });
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 1040, height: 390 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
let i = 0;
for (const o of pick) {
  const D = Number(process.env.SF_DIST ?? 4.2);
  const px = o.x + o.nx * D, py = o.y + o.ny * D, yaw = Math.atan2(-o.nx, -o.ny);
  await p.goto(`http://localhost:5173/?at=${px.toFixed(1)},${py.toFixed(1)},${yaw.toFixed(3)}&t=${process.env.SF_T ?? '13:00'}`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await p.waitForTimeout(3500);
  await p.screenshot({ path: `../logs/sf_shots/${String(i++).padStart(2, '0')}.png` });
}
await b.close();
