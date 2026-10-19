// Catalog close-ups (<= 8 m) per variant: V3, V7, V8 fountains, DFI display (H4/H5), shelter, plus a phone viewport shot. Output preview/catalog_cmp2.jpg
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const OUT = new URL('../../preview/', import.meta.url).pathname;
const CAT = JSON.parse(readFileSync(new URL('../public/data/catalog.json', import.meta.url))).o;
const near = (v, filt = () => true) => CAT.filter((r) => r[0] === v && filt(r)).sort((a, b) => Math.hypot(a[1], a[2]) - Math.hypot(b[1], b[2]))[0];
// camera `d` metres from the object, looking at it; (ox, oy) = offset direction
const view = (r, d, ox = 0.6, oy = -0.8) => { const n = Math.hypot(ox, oy); return [r[1] + (ox / n) * d, r[2] + (oy / n) * d, Math.atan2(-ox, -oy)]; };
const h4 = near('H4'), h1 = CAT.filter((r) => r[0] === 'H1').sort((a, b) => Math.hypot(a[1] - h4[1], a[2] - h4[2]) - Math.hypot(b[1] - h4[1], b[2] - h4[2]))[0];
const S = {
  'V3 Bronzefiguren': view(near('V3'), 5.5, 1, -0.3), 'V7 Wandbrunnen': view(near('V7'), 5.5, 1, -0.3), 'V8 Notwasser': view(near('V8'), 4.5, 1, -0.3),
  'Anzeige H4': view(h4, 2.2, Math.sin(h4[3]), Math.cos(h4[3])), 'Wartehalle H1': view(h1, 3.5, Math.sin(h1[3]), Math.cos(h1[3])), 'V1 Saeule': view(near('V1'), 5.5, 1, -0.3),
};
const browser = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const files = [];
const ctx = await browser.newContext({ viewport: { width: 960, height: 540 } });
const page = await ctx.newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
for (const [name, [x, y, h]] of Object.entries(S)) {
  await page.goto(`${BASE}/?at=${x.toFixed(1)},${y.toFixed(1)},${h.toFixed(2)}&t=11:00&exact`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.waitForTimeout(3000);
  const f = `${OUT}_cat2_${name.replace(/\W/g, '')}.jpg`;
  await page.screenshot({ path: f, type: 'jpeg', quality: 80 }); files.push([name, f]);
}
await ctx.close();
const sheet = await (await browser.newContext({ viewport: { width: 1560, height: 300 } })).newPage();
const img = ([n, f]) => `<td><img src="data:image/jpeg;base64,${readFileSync(f).toString('base64')}" style="width:516px;display:block">${n}</td>`;
await sheet.setContent(`<body style="margin:0;background:#111;color:#fff;font:12px sans-serif"><table cellspacing=1 style="width:1560px"><tr>${files.slice(0, 3).map(img).join('')}</tr><tr>${files.slice(3).map(img).join('')}</tr></table>`);
await sheet.waitForTimeout(500);
await sheet.screenshot({ path: `${OUT}catalog_cmp2.jpg`, type: 'jpeg', quality: 80, fullPage: true });
await browser.close();
