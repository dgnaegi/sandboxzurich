// Before/after contact sheet of 4 stops: "before" blocks stops_equip.json (generic fallback set). Output preview/stops_equip.jpg
import { chromium } from 'playwright';
import { writeFileSync, readFileSync } from 'node:fs';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const OUT = new URL('../../preview/', import.meta.url).pathname;
import { readFileSync as rf } from 'node:fs';
const EQ = JSON.parse(rf(new URL('../public/data/stops_equip.json', import.meta.url)));
const C = { Helvetiaplatz: [743, -888], Stauffacher: [970, -1166], 'Bahnhof Wiedikon': [581, -1388], 'Escher-Wyss-Platz': [518, 663] };
// view from the track side, 8 m in front of the nearest real shelter, looking at it
const S = Object.fromEntries(Object.entries(C).map(([n, [x, y]]) => {
  const s = EQ.sh.filter((q) => q[2] < 20).sort((a, b) => Math.hypot(a[0] - x, a[1] - y) - Math.hypot(b[0] - x, b[1] - y))[0];
  const a = (s[4] * Math.PI) / 180, fx = Math.cos(a) * s[5], fy = -Math.sin(a) * s[5];
  return [n, [s[0] + fx * 9, s[1] + fy * 9, Math.atan2(-fx, -fy)]];
}));
const YAW = Number(process.env.YAWOFF ?? 0), BACK = Number(process.env.BACK ?? 10);
const browser = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const files = [];
for (const mode of ['before', 'after']) {
  const ctx = await browser.newContext({ viewport: { width: 960, height: 540 } });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  if (mode === 'before') await page.route('**/stops_equip.json', (r) => r.abort());
  for (const [name, [x, y, h]] of Object.entries(S)) {
    const px = x, py = y;
    await page.goto(`${BASE}/?at=${px.toFixed(1)},${py.toFixed(1)},${(h + YAW).toFixed(2)}&t=11:00`);
    await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
    await page.waitForTimeout(3000);
    const f = `${OUT}_se_${mode}_${name.replace(/\W/g, '')}.png`;
    await page.screenshot({ path: f }); files.push([mode, name, f]);
  }
  await ctx.close();
}
const sheet = await (await browser.newContext({ viewport: { width: 1600, height: 900 } })).newPage();
const img = (f) => `<img src="data:image/png;base64,${readFileSync(f).toString('base64')}" style="width:394px;display:block">`;
const names = Object.keys(S);
await sheet.setContent(`<body style="margin:0;background:#111;color:#fff;font:14px sans-serif"><table cellspacing=2>${['before', 'after'].map((m) => `<tr><td>${m}</td>${names.map((n) => `<td>${img(files.find((f) => f[0] === m && f[1] === n)[2])}</td>`).join('')}</tr>`).join('')}</table>`);
await sheet.screenshot({ path: `${OUT}stops_equip.jpg`, type: 'jpeg', quality: 80 });
await browser.close();
