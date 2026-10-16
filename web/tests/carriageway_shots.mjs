// Top-down game views (size 120 m) at the 10 check places + 4 street views.  node tests/carriageway_shots.mjs <tag>
// -> preview/_carr_<tag>_<place>.png ; compose with pipeline/carriageway_cmp.py (ortho | before | after)
import { chromium } from 'playwright';
const tag = process.argv[2] ?? 'after';
const OUT = new URL('../../preview/', import.meta.url).pathname;
const PLACES = { langstrasse: [753, -557], helvetiaplatz: [785, -885], stauffacher: [960, -1245], albisriederplatz: [-495, -668],
  hardplatz: [-110, -175], escher_wyss: [455, 715], lochergut: [81, -958], idaplatz: [-140, -1135], bullingerplatz: [-41, -522], lindenplatz: [-2395, 350] };
const STREETS = { street_langstrasse: '753,-557,0.37', street_hardstrasse: '-110,-175,2.75', street_albisriederstr: '-495,-668,-0.76', street_stauffacherstr: '960,-1245,0.1' };
const clamp = (v) => Math.min(Math.max(v, Math.floor(v / 200) * 200 + 60), Math.floor(v / 200) * 200 + 140); // view inside one 200 m tile
for (const k of Object.keys(PLACES)) PLACES[k] = PLACES[k].map(clamp);
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const SIZE = 120, PX = 720;
for (const [name, [x, y]] of Object.entries(PLACES)) {
  const p = await (await b.newContext({ viewport: { width: PX, height: PX } })).newPage();
  await p.goto(`http://localhost:5173/?at=${x},${y},0&t=12:00`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await p.waitForTimeout(6000);
  const url = await p.evaluate(([x, y, size]) => {
    const { sbxRenderer: r, sbxScene: s, sbxCamera: c0, sbxTiles: t, sbxPlayer: pl } = window;
    pl.mesh.visible = false; t.cull(x, y, 400);
    const c = c0.clone(), H = 3000;
    c.fov = 2 * Math.atan(size / 2 / H) * 180 / Math.PI; c.aspect = 1; c.near = H - 200; c.far = H + 200;
    c.position.set(x, H, -y); c.up.set(0, 0, -1); c.lookAt(x, 0, -y); c.updateProjectionMatrix();
    const fog = s.fog; s.fog = null;
    r.setSize(r.domElement.width, r.domElement.width, false);
    r.render(s, c); const d = r.domElement.toDataURL('image/png'); s.fog = fog; return d;
  }, [x, y, SIZE]);
  (await import('node:fs')).writeFileSync(`${OUT}_carr_${tag}_${name}.png`, Buffer.from(url.split(',')[1], 'base64'));
  await p.context().close();
}
for (const [name, at] of Object.entries(STREETS)) {
  const p = await (await b.newContext({ viewport: { width: 960, height: 540 } })).newPage();
  await p.goto(`http://localhost:5173/?at=${at}&t=12:00`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await p.waitForTimeout(5000);
  await p.screenshot({ path: `${OUT}_carr_${tag}_${name}.png` });
  await p.context().close();
}
await b.close();
