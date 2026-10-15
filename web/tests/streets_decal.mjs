// Top-down close-ups oriented along a heading (up = driving direction). node tests/streets_decal.mjs out_prefix x,y,h[,size] ...
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
const [,, out, ...pts] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 500, height: 500 } })).newPage();
let i = 0;
for (const pt of pts) {
  const [x, y, h, size = 12] = pt.split(',').map(Number);
  await p.goto(`http://localhost:5173/?at=${x},${y},0&t=12:00`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
  await p.waitForTimeout(5000);
  const url = await p.evaluate(([x, y, h, size]) => {
    const { sbxRenderer: r, sbxScene: s, sbxCamera: c0, sbxTiles: t, sbxPlayer: pl } = window;
    pl.mesh.visible = false; t.cull(x, y, 400); s.traverse((o) => { if (o.name === 'trees' || o.name === 'fartrees') o.visible = false; });
    const c = c0.clone(), H = 300;
    c.fov = 2 * Math.atan(size / 2 / H) * 180 / Math.PI; c.aspect = 1; c.near = 100; c.far = 600;
    c.position.set(x, H, -y); c.up.set(Math.sin(h), 0, -Math.cos(h)); c.lookAt(x, 0, -y); c.updateProjectionMatrix();
    const fog = s.fog; s.fog = null; r.setSize(500, 500, false); r.render(s, c);
    const d = r.domElement.toDataURL('image/png'); s.fog = fog; return d;
  }, [x, y, h, size]);
  writeFileSync(`${out}_${i++}.png`, Buffer.from(url.split(',')[1], 'base64'));
}
await b.close();
