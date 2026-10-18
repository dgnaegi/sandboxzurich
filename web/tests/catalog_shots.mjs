// Object catalog before/after contact sheet (6 places). "before" = ?nocatalog (generic fountains/shelters). Output preview/catalog_cmp.jpg
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const OUT = new URL('../../preview/', import.meta.url).pathname;
const EQ = JSON.parse(readFileSync(new URL('../public/data/stops_equip.json', import.meta.url)));
const shelter = (x, y) => {   // view from the track side, 9 m in front of the nearest real shelter
  const s = EQ.sh.filter((q) => q[2] < 20).sort((a, b) => Math.hypot(a[0] - x, a[1] - y) - Math.hypot(b[0] - x, b[1] - y))[0];
  const a = (s[4] * Math.PI) / 180, fx = Math.cos(a) * s[5], fy = -Math.sin(a) * s[5];
  return [s[0] + fx * 9, s[1] + fy * 9, Math.atan2(-fx, -fy)];
};
const south = (x, y, d = 6) => [x, y - d, 0];
const S = {
  'Bullingerplatz': south(-44.17, -499.11), 'Idaplatz': south(-142, -1095), 'Helvetiaplatz': south(770, -860),
  'Stauffacher': shelter(998, -1144), 'Albisriederplatz': south(-513, -650), 'Escher-Wyss-Platz': shelter(518.7, 675),
};
const browser = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const files = {};
for (const mode of ['before', 'after']) {
  const ctx = await browser.newContext({ viewport: { width: 960, height: 540 } });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  page.on('console', (m) => { if (m.type() === 'warning' && m.text().includes('catalog')) console.log(m.text()); });
  for (const [name, [x, y, h]] of Object.entries(S)) {
    await page.goto(`${BASE}/?at=${x.toFixed(1)},${y.toFixed(1)},${h.toFixed(2)}&t=11:00${mode === 'before' ? '&nocatalog' : ''}`);
    await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
    await page.waitForTimeout(3000);
    const f = `${OUT}_cat_${mode}_${name.replace(/\W/g, '')}.jpg`;
    await page.screenshot({ path: f, type: 'jpeg', quality: 80 }); (files[mode] ??= []).push(f);
  }
  await ctx.close();
}
const sheet = await (await browser.newContext({ viewport: { width: 1560, height: 300 } })).newPage();
const img = (f) => `<img src="data:image/jpeg;base64,${readFileSync(f).toString('base64')}" style="width:258px;display:block">`;
await sheet.setContent(`<body style="margin:0;background:#111;color:#fff;font:12px sans-serif"><table cellspacing=1 style="width:1560px">${['before', 'after'].map((m) => `<tr>${files[m].map((f) => `<td>${img(f)}</td>`).join('')}</tr>`).join('')}<tr>${Object.keys(S).map((n) => `<td>${n}</td>`).join('')}</tr></table>`);
await sheet.waitForTimeout(500);
await sheet.screenshot({ path: `${OUT}catalog_cmp.jpg`, type: 'jpeg', quality: 82, fullPage: true });
await browser.close();
