// usage: node tests/wildposters_shots.mjs  -> ../logs/wp_shots/NN.png (several walls, day + night); sheet via tests/sheet.py
import { chromium } from 'playwright';
import fs from 'fs';
const tiles = ['1_-5', '0_-5', '1_-4', '0_-4', '2_-5', '-1_-5'];
const picks = [];
for (const t of tiles) {
  const f = `public/tiles/t_${t}.json`;
  if (!fs.existsSync(f)) continue;
  const w = JSON.parse(fs.readFileSync(f, 'utf8')).wild ?? [];
  for (let i = 0; i < w.length && picks.length < 8; i += Math.max(1, Math.floor(w.length / 2))) picks.push(w[i]);
}
fs.mkdirSync('../logs/wp_shots', { recursive: true });
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 500 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
let i = 0;
for (const [x, y, , tx, ty] of picks) {
  const nx = ty, ny = -tx, px = x + nx * 3.2, py = y + ny * 3.2, yaw = Math.atan2(-nx, -ny);
  const t = i % 4 === 3 ? '22:30' : '13:00';
  await p.goto(`http://localhost:5173/?at=${px.toFixed(1)},${py.toFixed(1)},${yaw.toFixed(3)}&t=${t}`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await p.waitForTimeout(3000);
  await p.screenshot({ path: `../logs/wp_shots/${String(i++).padStart(2, '0')}.png` });
}
await b.close();
