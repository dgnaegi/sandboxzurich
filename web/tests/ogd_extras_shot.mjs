// Plaque card + pump check: stand in front of the first plaque, screenshot -> preview/ogd_extras.jpg
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
const d = JSON.parse(readFileSync(new URL('../public/data/ogd_extras.json', import.meta.url)));
const t = d.tafeln.find((q) => q.x > -300 && q.x < 1500 && q.y > -1500 && q.y < 800) ?? d.tafeln[0];
const pu = d.pumps[0];
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: 960, height: 540 } });
p.on('pageerror', (e) => console.log('pageerror', e.message));
const OUT = new URL('../../preview/', import.meta.url).pathname;
const shots = [];
for (const [name, x, y, yaw] of [['plaque', t.x + t.nx * 4, t.y + t.ny * 4, Math.atan2(-t.nx, -t.ny)], ['pump', pu.x, pu.y - 4, 0]]) {
  await p.goto(`http://localhost:5173/?at=${x.toFixed(1)},${y.toFixed(1)},${yaw.toFixed(2)}&t=11:00`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 }); await p.waitForTimeout(3500);
  const f = `${OUT}_ogd_${name}.png`; await p.screenshot({ path: f }); shots.push(f);
  console.log(name, t.t, '| card:', (await p.evaluate(() => document.getElementById('plaque-card')?.style.display)));
}
const s = await (await b.newContext({ viewport: { width: 1920, height: 540 } })).newPage();
await s.setContent(`<body style="margin:0">${shots.map((f) => `<img src="data:image/png;base64,${readFileSync(f).toString('base64')}" width=960>`).join('')}`);
await s.screenshot({ path: `${OUT}ogd_extras.jpg`, type: 'jpeg', quality: 80 });
await b.close();
