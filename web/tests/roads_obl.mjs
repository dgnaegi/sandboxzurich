// Oblique views for road checks: node tests/roads_obl.mjs outprefix "x,y,dirDeg;x,y,dirDeg..."  (dir = look direction in degrees, 0 = east, 90 = north)
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
const [,, prefix, list] = process.argv;
const pts = list.split(';').map(s => s.split(',').map(Number));
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 640, height: 400 } })).newPage();
await p.goto(`http://localhost:5173/?at=${pts[0][0]},${pts[0][1]},0&t=12:00`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
await p.waitForTimeout(4000);
let i = 0;
for (const [x, y, d] of pts) {
  await p.evaluate(([x, y]) => { window.sbxPlayer.mesh.visible = false; window.sbxTiles.cull(x, y, 400); }, [x, y]);
  await p.evaluate(([x, y]) => window.sbxPlayer.teleport(x, y, 0), [x, y]);
  await p.waitForTimeout(5000);
  const url = await p.evaluate(([x, y, d]) => {
    const { sbxRenderer: r, sbxScene: s, sbxCamera: c0 } = window;
    const c = c0.clone(); c.fov = 55; c.aspect = 640 / 400; c.near = 0.3; c.far = 600;
    const a = d * Math.PI / 180, dx = Math.cos(a), dy = Math.sin(a), dist = 38;
    const gx = x - dx * dist, gy = y - dy * dist;
    c.position.set(gx, (window.sbxPlayer.z ?? 0) + 9, -gy);
    c.up.set(0, 1, 0); c.lookAt(x, 0, -y); c.updateProjectionMatrix();
    r.setSize(640, 400, false); r.render(s, c); return r.domElement.toDataURL('image/jpeg', 0.8);
  }, [x, y, d]);
  writeFileSync(`${prefix}_${i++}.jpg`, Buffer.from(url.split(',')[1], 'base64'));
}
await b.close();
