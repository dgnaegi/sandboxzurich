// Oblique low shots of road surface at given spots (road_smooth contact sheet).
// node tests/road_smooth_shots.mjs outPrefix "x,y;x,y;..."   -> outPrefix_0.jpg ...
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
const [,, pre, spots] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 640, height: 400 } })).newPage();
const list = spots.split(';').map((s) => s.split(',').map(Number));
for (let i = 0; i < list.length; i++) {
  const [x, y] = list[i];
  await p.goto(`http://localhost:5173/?at=${x},${y},0&t=12:00&nopost`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
  await p.waitForTimeout(5000);
  const url = await p.evaluate(([x, y]) => {
    const { sbxRenderer: r, sbxScene: s, sbxCamera: c0, sbxPlayer: pl } = window;
    pl.mesh.visible = false;
    const c = c0.clone(), g = pl.mesh.position.y;
    c.fov = 55; c.aspect = 640 / 400; c.near = 0.3; c.far = 400;
    c.position.set(x + 12, g + 5, -y + 12); c.up.set(0, 1, 0); c.lookAt(x - 6, g, -y - 6); c.updateProjectionMatrix();
    r.setSize(640, 400, false);
    r.render(s, c); return r.domElement.toDataURL('image/jpeg', 0.8);
  }, [x, y]);
  writeFileSync(`${pre}_${i}.jpg`, Buffer.from(url.split(',')[1], 'base64'));
}
await b.close();
