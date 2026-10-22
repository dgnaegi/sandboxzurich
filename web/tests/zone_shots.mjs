// Zone camera points (pipeline/overrides/zones.json): PC + phone shots and one contact sheet.
// Usage: node tests/zone_shots.mjs <zone 1-5> [before|after] [baseUrl]   (LIMIT=n for a quick test, ONLY=1,3 for some points)
// -> preview/zone<N>_<tag>/<nn>_<pc|phone>.jpg and preview/zone<N>_<tag>.jpg. Yaw = nearest street direction (cam.yaw overrides).
import { chromium, devices } from 'playwright';
import { mkdirSync, readFileSync } from 'node:fs';

const zoneId = Number(process.argv[2]);
const tag = process.argv[3] ?? 'before';
const BASE = process.argv[4] ?? 'http://localhost:5173';
const ROOT = new URL('../../', import.meta.url).pathname;
const zone = JSON.parse(readFileSync(`${ROOT}pipeline/overrides/zones.json`, 'utf8')).zones.find((z) => z.id === zoneId);
if (!zone) throw new Error('unknown zone');
const streets = JSON.parse(readFileSync(`${ROOT}web/public/data/districts.json`, 'utf8')).streets;
const only = process.env.ONLY?.split(',').map(Number);   // ONLY=1,3 = just these points (1-based)
const cams = zone.cams.filter((_, i) => !only || only.includes(i + 1)).slice(0, Number(process.env.LIMIT ?? 99));

function streetYaw(x, y) {
  let best = 40, yaw = 0;
  for (const s of streets) for (let i = 1; i < s.p.length; i++) {
    const [ax, ay] = s.p[i - 1], [bx, by] = s.p[i];
    const dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy || 1;
    const t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / l2));
    const d = Math.hypot(x - (ax + t * dx), y - (ay + t * dy));
    if (d < best) { best = d; yaw = Math.atan2(dx, dy); }
  }
  return yaw;
}

const DIR = `${ROOT}preview/zone${zoneId}_${tag}/`;
mkdirSync(DIR, { recursive: true });
const VP = {
  pc: { viewport: { width: 1280, height: 720 } },
  phone: { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true },
};
const browser = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const files = { pc: [], phone: [] };
for (const [vp, opts] of Object.entries(VP)) {
  const page = await (await browser.newContext(opts)).newPage();
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  for (const [i, c] of cams.entries()) {
    const yaw = c.yaw ?? streetYaw(c.x, c.y);
    await page.goto(`${BASE}/?at=${c.x},${c.y},${yaw.toFixed(2)}${c.z != null ? `,${c.z}` : ''}&t=13:00&nopost`);
    await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
    await page.waitForTimeout(3000);
    const f = `${DIR}${String(i + 1).padStart(2, '0')}_${vp}.jpg`;
    await page.screenshot({ path: f, type: 'jpeg', quality: 80 });
    files[vp].push([c.name, f]);
  }
}
const sheet = await (await browser.newContext({ viewport: { width: 1600, height: 900 } })).newPage();
const grid = (list, w) => list.map(([n, f]) => `<div style="position:relative;width:${w}px"><img src="data:image/jpeg;base64,${readFileSync(f).toString('base64')}" style="width:${w}px;display:block"><span style="position:absolute;left:3px;top:3px;background:#000a;color:#fff;font:12px sans-serif;padding:1px 4px">${n}</span></div>`).join('');
await sheet.setContent(`<body style="margin:0;background:#222;display:flex;flex-wrap:wrap;width:1600px;gap:0">${grid(files.pc, 400)}${grid(files.phone, 400)}</body>`);
await sheet.waitForTimeout(800);
await sheet.screenshot({ path: `${ROOT}preview/zone${zoneId}_${tag}.jpg`, type: 'jpeg', quality: 75, fullPage: true });
await browser.close();
console.log('done', `preview/zone${zoneId}_${tag}.jpg`, cams.length, 'points');
