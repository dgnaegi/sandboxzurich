// Zone 4 houses: facade photo (research/zones/z4/photos.json crop) | game shot from the photo spot, same heading.
// Photo spot = house entrance point minus dist_m along bearing (both from the facade fetch). Usage: node tests/z4_houses_cmp.mjs [baseUrl]
// -> preview/facades_v4_shots/*.png, preview/${OUTN}.jpg
import { chromium } from 'playwright';
import { mkdirSync, readFileSync } from 'node:fs';

const BASE = process.argv[2] ?? 'http://localhost:5173';
const ROOT = new URL('../../', import.meta.url).pathname;
const photos = JSON.parse(readFileSync(`${ROOT}research/zones/z4/photos.json`, 'utf8'));
const targets = Object.fromEntries(JSON.parse(readFileSync(`${ROOT}research/zones/z4/targets.json`, 'utf8')).map((t) => [t.addr, t]));
const ADDR = (process.env.ADDR ?? 'Birmensdorferstrasse 301,Zentralstrasse 78,Idastrasse 15,Zurlindenstrasse 29,Bertastrasse 1,Kalkbreitestrasse 136').split(',');
const DIR = `${ROOT}preview/facades_v4_shots/`;
mkdirSync(DIR, { recursive: true });
const CAM = 5.5, BACK = Number(process.env.BACK ?? 8), OUTN = process.env.OUTN ?? 'facades_v4_x';
const picks = ADDR.map((a) => {
  const t = targets[a], ph = photos[a].photos[0], b = (ph.bearing * Math.PI) / 180;
  return { a, tx: t.x, ty: t.y, file: ph.file, x: t.x - Math.sin(b) * ph.dist_m, y: t.y - Math.cos(b) * ph.dist_m, yaw: b };
});
const browser = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const page = await (await browser.newContext({ viewport: { width: 1280, height: 720 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
for (const [i, p] of picks.entries()) {
  const x = p.x - Math.sin(p.yaw) * (BACK - CAM), y = p.y - Math.cos(p.yaw) * (BACK - CAM);
  await page.goto(`${BASE}/?at=${x.toFixed(1)},${y.toFixed(1)},${p.yaw.toFixed(3)}&t=13:00&nopost&exact`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.evaluate(([tx, ty, px, py]) => { // free camera: from the photo spot, 5 m above ground, looking at the house (z 8 m up)
    const R = window.sbxRenderer, cam = window.sbxCamera, orig = R.render.bind(R);
    const g = window.sbxPlayer.z;
    R.render = (s, c) => { cam.position.set(px, g + 4.5, -py); cam.lookAt(tx, g + 9, -ty); cam.updateMatrixWorld(); return orig(s, c); };
  }, [p.tx, p.ty, p.x, p.y]); await page.waitForTimeout(2500);
  p.shot = `${DIR}h${i + 1}.png`;
  await page.screenshot({ path: p.shot });
}
const sheet = await (await browser.newContext({ viewport: { width: 1600, height: 900 } })).newPage();
const cell = (p) => `<div style="display:flex;width:800px;height:300px;position:relative">
  <img src="data:image/jpeg;base64,${readFileSync(ROOT + p.file).toString('base64')}" style="width:400px;height:300px;object-fit:cover">
  <img src="data:image/png;base64,${readFileSync(p.shot).toString('base64')}" style="width:400px;height:300px;object-fit:cover">
  <div style="position:absolute;left:4px;top:4px;background:#000a;color:#fff;font:bold 15px sans-serif;padding:2px 6px">${p.a}</div></div>`;
await sheet.setContent(`<body style="margin:0;background:#222;display:flex;flex-wrap:wrap;width:1600px">${picks.map(cell).join('')}</body>`);
await sheet.waitForTimeout(600);
await sheet.screenshot({ path: `${ROOT}preview/${OUTN}.jpg`, type: 'jpeg', quality: 80, fullPage: true });
await browser.close();
console.log('done');
