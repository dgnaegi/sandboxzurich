// Ad-hoc views as one contact sheet (PC + phone per view): node tests/spot_shots.mjs <out.jpg> "x,y,yaw[,label];x,y,yaw[,label]" [baseUrl]
// x/y = local metres (x east, y north, as in ?at=), yaw in radians. Use for quick before/after checks of a single place.
import { chromium, devices } from 'playwright';
import { readFileSync } from 'node:fs';

const [out, spec, BASE = 'http://localhost:5173'] = process.argv.slice(2);
const views = spec.split(';').map((s) => { const [x, y, yaw, label] = s.split(','); return { x, y, yaw, label: label ?? `${x},${y}` }; });
const VP = {
  pc: { viewport: { width: 1280, height: 720 } },
  phone: { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true },
};
const browser = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const shots = [];
for (const [vp, opts] of Object.entries(VP)) {
  const page = await (await browser.newContext(opts)).newPage();
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  for (const v of views) {
    await page.goto(`${BASE}/?at=${v.x},${v.y},${v.yaw}&t=13:00&nopost`);
    await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
    await page.waitForTimeout(3000);
    shots.push([`${v.label} ${vp}`, (await page.screenshot({ type: 'jpeg', quality: 80 })).toString('base64')]);
  }
}
const sheet = await (await browser.newContext({ viewport: { width: 1600, height: 900 } })).newPage();
await sheet.setContent(`<body style="margin:0;background:#222;display:flex;flex-wrap:wrap;width:1600px">${shots.map(([n, b]) =>
  `<div style="position:relative;width:533px"><img src="data:image/jpeg;base64,${b}" style="width:533px;display:block"><span style="position:absolute;left:3px;top:3px;background:#000a;color:#fff;font:12px sans-serif;padding:1px 4px">${n}</span></div>`).join('')}</body>`);
await sheet.waitForTimeout(800);
await sheet.screenshot({ path: out, type: 'jpeg', quality: 75, fullPage: true });
await browser.close();
console.log('done', out, shots.length, 'shots');
