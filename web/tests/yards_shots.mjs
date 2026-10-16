// Yards check: 6 top-down views (block edges) + 4 courtyard-entrance views -> preview/yards_shots/*.png, sheet via yards_sheet.py
// node tests/yards_shots.mjs   (dev server on :5173)
import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'node:fs';
const OUT = new URL('../../preview/yards_shots/', import.meta.url).pathname; mkdirSync(OUT, { recursive: true });
const TOP = { kalkbreite: [400, -1209], erismannhof: [240, -516], egli: [-396, -48], baeckerstr: [991, -1060], roentgen: [775, 349], idaplatz: [-130, -1127] };
const EYE = { kalk_e: [380, -1180, 0.4], erism_e: [240, -540, 1.2], egli_e: [-380, -20, 2.6], ida_e: [-150, -1110, 0.3] }; // x, y, heading (rad, CCW from east)
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 800 } })).newPage();
const errs = []; p.on('pageerror', (e) => errs.push(String(e)));
await p.goto('http://localhost:5173/?at=400,-1209,0&t=12:00');
await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
async function shot(name, x, y, mode, hd) {
  await p.evaluate(([x, y]) => { window.sbxPlayer.teleport?.(x, y); }, [x, y]).catch(() => {});
  await p.goto(`http://localhost:5173/?at=${x},${y},0&t=12:00`); await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 }); await p.waitForTimeout(5000);
  const url = await p.evaluate(([x, y, mode, hd]) => {
    const { sbxRenderer: r, sbxScene: s, sbxCamera: c0, sbxTiles: t, sbxPlayer: pl } = window;
    pl.mesh.visible = false; t.cull(x, y, 400);
    const c = c0.clone(); c.aspect = 1;
    if (mode === 'top') { const H = 3000, size = 120; c.fov = 2 * Math.atan(size / 2 / H) * 180 / Math.PI; c.near = H - 200; c.far = H + 200; c.position.set(x, H, -y); c.up.set(0, 0, -1); c.lookAt(x, 0, -y); }
    else { c.fov = 60; c.near = .1; c.far = 400; c.up.set(0, 1, 0); c.position.set(x, 1.7, -y); c.lookAt(x + Math.cos(hd) * 10, 1.5, -(y + Math.sin(hd) * 10)); }
    c.updateProjectionMatrix(); r.setSize(800, 800, false); r.render(s, c); return r.domElement.toDataURL('image/png');
  }, [x, y, mode, hd]);
  writeFileSync(OUT + name + '.png', Buffer.from(url.split(',')[1], 'base64'));
}
for (const [k, [x, y]] of Object.entries(TOP)) await shot('top_' + k, x, y, 'top');
for (const [k, [x, y, h]] of Object.entries(EYE)) await shot(k, x, y, 'eye', h);
console.log('errors', errs.length, errs.slice(0, 3));
await b.close();
