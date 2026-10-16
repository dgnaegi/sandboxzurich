// Before/after shots of the worst road spots: ground view + oblique view -> preview/_roads_<tag>_<name>_{g,o}.png
// node tests/roads_shots.mjs <tag> [places.json]   (places from pipeline/roads_places.py); sheet: tests/roads_sheet.py
import { chromium } from 'playwright';
import { writeFileSync, readFileSync } from 'node:fs';
const tag = process.argv[2] ?? 'before';
const places = JSON.parse(readFileSync(process.argv[3] ?? '../logs/roads_places.json', 'utf8'));
const OUT = new URL('../../preview/', import.meta.url).pathname;
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
for (const [i, pl] of places.entries()) {
  await p.goto(`http://localhost:5173/?at=${pl.x},${pl.y},0&t=12:00&nopost`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
  await p.waitForTimeout(6000);
  for (const mode of ['g', 'o']) {
    const url = await p.evaluate(([pl, mode]) => {
      const { sbxRenderer: r, sbxScene: s, sbxCamera: c0, sbxTiles: t, sbxPlayer: pp } = window;
      pp.mesh.visible = false;
      t.cull(pl.x, pl.y, 400);
      const c = c0.clone(); c.fov = 65; c.aspect = 16 / 9; c.near = 0.1; c.far = 600;
      const back = mode === 'g' ? 14 : 30, up = mode === 'g' ? 1.7 : 18;
      const cx = pl.x - pl.dx * back, cy = pl.y - pl.dy * back;
      const gz = t.ground(cx, cy), tz = t.ground(pl.x + pl.dx * 15, pl.y + pl.dy * 15);
      c.position.set(cx, gz + up, -cy); c.up.set(0, 1, 0);
      c.lookAt(pl.x + pl.dx * 15, mode === 'g' ? gz + 1.2 : tz, -(pl.y + pl.dy * 15)); c.updateProjectionMatrix();
      r.setSize(800, 450, false); r.render(s, c);
      return r.domElement.toDataURL('image/png');
    }, [pl, mode]);
    writeFileSync(`${OUT}_roads_${tag}_${i}_${mode}.png`, Buffer.from(url.split(',')[1], 'base64'));
  }
  console.log(tag, i, pl.name);
}
await b.close();
