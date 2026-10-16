// Bird's-eye before/after of rooftop furniture (roofRadius 0 vs 250) at fixed spots -> preview/roofs_<name>_{before,after}.png
// node tests/roofs_shots.mjs   (dev server on :5173; tile build with "roofs" rows needed). Sheet: tests/roofs_sheet.py
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
const SPOTS = { hardbruecke: [28, 112, 70], prime: [45, 222, 90], lochergut: [105, -891, 60], helvetia: [800, -850, 60] };
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 520 } })).newPage();
for (const [name, [x, y, h]] of Object.entries(SPOTS)) {
  await p.goto(`http://localhost:5173/?at=${x},${y},0&t=12:00&nopost`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await p.waitForTimeout(5000);
  for (const [tag, rad] of [['before', 0], ['after', 250]]) {
    const url = await p.evaluate(([x, y, h, rad]) => {
      const { sbxRenderer: r, sbxScene: s, sbxCamera: c0, sbxTiles: t, sbxPlayer: pl } = window;
      pl.mesh.visible = false; t.roofRadius = rad; t.cull(x, y, 400);
      const c = c0.clone(); c.fov = 55; c.aspect = 800 / 520; c.near = 1; c.far = 2000;
      c.position.set(x, h + 30, -y + 85); c.up.set(0, 1, 0); c.lookAt(x, 20, -y); c.updateProjectionMatrix();
      r.setSize(800, 520, false); r.render(s, c); return r.domElement.toDataURL('image/png');
    }, [x, y, h, rad]);
    writeFileSync(`preview/roofs_${name}_${tag}.png`, Buffer.from(url.split(',')[1], 'base64'));
  }
}
await b.close();
