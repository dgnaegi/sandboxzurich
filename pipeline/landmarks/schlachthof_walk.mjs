// Walk-in test (port 5173): node schlachthof_walk.mjs name sx sy tx ty secs   -> teleports to start, finds the yaw towards target, walks (Shift+W), prints end position and distance to target.
import { chromium } from '/Users/danielgnagi/sandboxzurich/web/node_modules/playwright/index.mjs';
const [,, name, sx, sy, tx, ty, secs = '12'] = process.argv; const f = [+sx, +sy], t = [+tx, +ty];
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message.slice(0, 100)));
await p.goto(`http://localhost:5173/?at=${f[0]},${f[1]},0&t=12:00&nopost`);
await p.waitForFunction(() => window.sbxReady && window.sbxPlayer, null, { timeout: 120000 });
await p.evaluate(async ([f]) => { await window.sbxTiles.update(f[0], f[1]); }, [f]); await p.waitForTimeout(3500);
let best = null;
for (let k = 0; k < 16; k++) {
  const yaw = (k * Math.PI) / 8;
  await p.evaluate(([f, yaw]) => window.sbxPlayer.teleport(f[0], f[1], yaw), [f, yaw]);
  await p.keyboard.down('KeyW'); await p.waitForTimeout(300); await p.keyboard.up('KeyW');
  const e = await p.evaluate(() => [window.sbxPlayer.x, window.sbxPlayer.y]);
  const dx = e[0] - f[0], dy = e[1] - f[1], ux = t[0] - f[0], uy = t[1] - f[1], c = (dx * ux + dy * uy) / (Math.hypot(dx, dy) * Math.hypot(ux, uy) + 1e-9);
  if (!best || c > best.c) best = { yaw, c };
}
await p.evaluate(([f, yaw]) => window.sbxPlayer.teleport(f[0], f[1], yaw), [f, best.yaw]); await p.waitForTimeout(300);
await p.keyboard.down('Shift'); await p.keyboard.down('KeyW'); await p.waitForTimeout(+secs * 1000); await p.keyboard.up('KeyW'); await p.keyboard.up('Shift');
const e = await p.evaluate(() => [window.sbxPlayer.x, window.sbxPlayer.y]); const d = Math.hypot(e[0] - t[0], e[1] - t[1]);
console.log(`${name}: yawfit ${best.c.toFixed(2)} end [${e.map((v) => v.toFixed(1))}] dist to target ${d.toFixed(1)} m -> ${d < 6 ? 'REACHED' : 'BLOCKED'}`);
await b.close();
