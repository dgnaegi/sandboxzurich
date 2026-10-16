// hb3: walk down/up the stairs with real key input; prints player z along the way. node hb3_walk.mjs [port]
import { chromium } from '/Users/danielgnagi/sandboxzurich/web/node_modules/playwright/index.mjs';
const port = process.argv[2] || '5173';
const A = (-21 * Math.PI) / 180, O = [1760, -650], GZ = -2.9;
const tw = (d, c) => [O[0] + d * Math.cos(A) - c * Math.sin(A), O[1] + d * Math.sin(A) + c * Math.cos(A)];
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await (await b.newContext({ viewport: { width: 500, height: 300 } })).newPage();
const s2 = tw(60, -74);
await p.goto(`http://127.0.0.1:${port}/?at=${s2[0]},${s2[1]}&t=12:00`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
await p.waitForTimeout(7000);
const yawOf = (dd, dc) => { const a = tw(0, 0), c = tw(dd, dc); return Math.atan2(c[0] - a[0], c[1] - a[1]); };
const info = () => p.evaluate((g) => { const pl = window.sbxPlayer; return { x: +pl.x.toFixed(1), y: +pl.y.toFixed(1), zrel: +(pl.z - g).toFixed(2) }; }, GZ);
const walk = async (label, from, yaw, ms, zr) => {
  await p.evaluate(([x, y, yaw, z]) => { if (z !== undefined) window.sbxPlayer.z = z; window.sbxPlayer.teleport(x, y, yaw); }, [...from, yaw, zr === undefined ? undefined : GZ + zr]);
  await p.waitForTimeout(500);
  await p.keyboard.down('w');
  const out = [];
  for (let i = 0; i < ms / 700; i++) { await p.waitForTimeout(700); out.push((await info()).zrel); }
  await p.keyboard.up('w');
  console.log(label, 'z(rel plateau) every 0.7 s:', out.join(' '), 'end', JSON.stringify(await info()));
};
await walk('S2 down (Bahnhofplatz -> Shopville)', tw(60, -74), yawOf(0, -1), 9000);
await walk('Shopville gang east', tw(60, -92), yawOf(1, 0), 4000);
await walk('S1 down (Querhalle)', tw(-33, 3), yawOf(0, -1), 9000);
await walk('S1 up', tw(-33, -16), yawOf(0, 1), 9000);
await walk('SL down (to Loewenstrasse)', tw(70, -90), yawOf(0, 1), 12000, -5.3);
await b.close();
