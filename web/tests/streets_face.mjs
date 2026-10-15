// Views objects from the front: camera 7 m in front of (x,y) along facing angle h (math angle, local frame), looking at it.
// node tests/streets_face.mjs out_prefix x,y,z,h[,dist] ...
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
const [,, out, ...pts] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 500, height: 400 } })).newPage();
let i = 0;
for (const pt of pts) {
  const [x, y, z, h, d = 7] = pt.split(',').map(Number);
  await p.goto(`http://localhost:5173/?at=${x},${y},0&t=12:00`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
  await p.waitForTimeout(5000);
  const url = await p.evaluate(([x, y, z, h, d]) => {
    const { sbxRenderer: r, sbxScene: s, sbxCamera: c0, sbxTiles: t, sbxPlayer: pl } = window;
    pl.mesh.visible = false; t.cull(x, y, 400);
    const c = c0.clone(); c.fov = 50; c.aspect = 500 / 400; c.near = 0.1; c.far = 300; c.up.set(0, 1, 0);
    c.position.set(x + Math.cos(h) * d, z + 2.6, -(y + Math.sin(h) * d)); c.lookAt(x, z + 2.4, -y); c.updateProjectionMatrix();
    r.setSize(500, 400, false); r.render(s, c);
    return r.domElement.toDataURL('image/png');
  }, [x, y, z, h, d]);
  writeFileSync(`${out}_${i++}.png`, Buffer.from(url.split(',')[1], 'base64'));
}
await b.close();
