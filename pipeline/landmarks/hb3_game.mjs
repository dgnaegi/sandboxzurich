// hb3: normal third-person game camera at 8 places (player teleported, z set for underground levels). node hb3_game.mjs out_prefix [port] [w] [h]
import { chromium } from '/Users/danielgnagi/sandboxzurich/web/node_modules/playwright/index.mjs';
const [,, prefix, port = '5173', vw = '800', vh = '450'] = process.argv;
const A = (-21 * Math.PI) / 180, O = [1760, -650], GZ = -2.9;
const tw = (d, c) => [O[0] + d * Math.cos(A) - c * Math.sin(A), O[1] + d * Math.sin(A) + c * Math.cos(A)];
const yawOf = (dd, dc) => { const a = tw(0, 0), c = tw(dd, dc); return Math.atan2(c[0] - a[0], c[1] - a[1]); };
const V = [[-33, 8, 0.14, 0, -1], [-33, -7.5, -3.3, 0, -1], [-33, -40, -5.3, 0, -1], [20, -92, -5.3, 1, 0], [60, -66, 0, 0, -1], [40, -68.1, -16, 1, 0], [114.8, -60, -10.5, 0, 1], [60, -60, 0, 0, -1]];
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await (await b.newContext({ viewport: { width: +vw, height: +vh } })).newPage();
p.on('pageerror', (e) => { if (!/arc/.test(e.message)) console.log('pageerror', e.message.slice(0, 100)); });
const s0 = tw(-33, 8);
await p.goto(`http://127.0.0.1:${port}/?at=${s0[0]},${s0[1]}&t=12:00`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
await p.addStyleTag({ content: '#hud,.hud,#touch{display:none!important}' });
let i = 0;
for (const [d, c, z, dd, dc] of V) {
  const q = tw(d, c);
  await p.evaluate(([x, y, yaw, z]) => { window.sbxPlayer.z = z; window.sbxPlayer.teleport(x, y, yaw); }, [q[0], q[1], yawOf(dd, dc), GZ + z]);
  await p.waitForTimeout(6500);
  await p.screenshot({ path: `${prefix}_${i++}.jpg`, type: 'jpeg', quality: 82 });
}
await b.close();
