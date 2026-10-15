// Top-down view of the game at local (x, y), size metres, for comparison with the SWISSIMAGE orthophoto.
// node tests/topdown.mjs out.png x y [size=180] [px=900]
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
const [,, out, x, y, size = '180', px = '900'] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: Number(px), height: Number(px) } })).newPage();
await p.goto(`http://localhost:5173/?at=${x},${y},0&t=12:00`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
await p.waitForTimeout(6000);
const url = await p.evaluate(([x, y, size]) => {
  const { sbxRenderer: r, sbxScene: s, sbxCamera: c0, sbxTiles: t, sbxPlayer: pl } = window;
  pl.mesh.visible = false;
  t.cull(x, y, 400);
  const c = c0.clone(), H = 3000;
  c.fov = 2 * Math.atan(size / 2 / H) * 180 / Math.PI; c.aspect = 1; c.near = H - 200; c.far = H + 200;
  c.position.set(x, H, -y); c.up.set(0, 0, -1); c.lookAt(x, 0, -y); c.updateProjectionMatrix();
  const fog = s.fog; s.fog = null;
  r.setSize(r.domElement.width, r.domElement.width, false);
  r.render(s, c); const d = r.domElement.toDataURL('image/png'); s.fog = fog; return d;
}, [Number(x), Number(y), Number(size)]);
writeFileSync(out, Buffer.from(url.split(',')[1], 'base64'));
await b.close();
