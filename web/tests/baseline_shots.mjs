// Baseline: reference photo | game shot from the same spot and heading (research/zones/baseline_picks.json).
// Usage: node tests/baseline_shots.mjs [baseUrl]   -> preview/baseline_shots/*.png, preview/baseline_sheet_{1,2}.jpg
import { chromium } from 'playwright';
import { mkdirSync, readFileSync } from 'node:fs';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const ROOT = new URL('../../', import.meta.url).pathname;
const picks = JSON.parse(readFileSync(`${ROOT}research/zones/baseline_picks.json`, 'utf8'));
const DIR = `${ROOT}preview/baseline_shots/`;
mkdirSync(DIR, { recursive: true });
const CAM = 5.5; // player camera sits this far behind the player
const browser = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const page = await (await browser.newContext({ viewport: { width: 1280, height: 720 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
for (const [i, p] of picks.entries()) {
  const yaw = (p.heading * Math.PI) / 180;
  const x = p.x + Math.sin(yaw) * CAM, y = p.y + Math.cos(yaw) * CAM;
  await page.goto(`${BASE}/?at=${x.toFixed(1)},${y.toFixed(1)},${yaw.toFixed(3)}&t=13:00&nopost`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.waitForTimeout(3500);
  p.shot = `${DIR}b${String(i + 1).padStart(2, '0')}.png`;
  await page.screenshot({ path: p.shot });
  console.log(i + 1, 'zone', p.zone, p.x, p.y, p.heading);
}
const sheet = await (await browser.newContext({ viewport: { width: 1600, height: 900 } })).newPage();
for (const [s, chunk] of [picks.slice(0, 8), picks.slice(8)].entries()) {
  const cell = (p, i) => `<div style="display:flex;width:800px;height:300px;position:relative">
    <img src="data:image/jpeg;base64,${readFileSync(ROOT + p.file).toString('base64')}" style="width:350px;height:300px;object-fit:cover">
    <img src="data:image/png;base64,${readFileSync(p.shot).toString('base64')}" style="width:450px;height:300px;object-fit:cover">
    <div style="position:absolute;left:4px;top:4px;background:#000a;color:#fff;font:bold 16px sans-serif;padding:2px 6px">#${s * 8 + i + 1} Z${p.zone}</div></div>`;
  await sheet.setContent(`<body style="margin:0;background:#222;display:flex;flex-wrap:wrap;width:1600px">${chunk.map(cell).join('')}</body>`);
  await sheet.waitForTimeout(600);
  await sheet.screenshot({ path: `${ROOT}preview/baseline_sheet_${s + 1}.jpg`, type: 'jpeg', quality: 80, fullPage: true });
}
await browser.close();
