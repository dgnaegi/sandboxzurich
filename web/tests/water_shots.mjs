// Water check: 4 river spots (eye view + top view), optional night. Output: preview/water_<tag>_<spot>[_n|_top].png
// node tests/water_shots.mjs <tag> [night]   (dev server on :5173)
import { chromium } from 'playwright';
const [,, tag = 'before', night] = process.argv;
const OUT = new URL('../../preview/', import.meta.url).pathname;
const SPOTS = { sihlhoelzli: [1254, -1410, -1.57], sihl_k4: [1382, -925, -1.57], limmat_wipkinger: [1051, 446, 2.36], limmat_hardbr: [637, 747, 2.09] };
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 960, height: 540 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
for (const [n, [x, y, yaw]] of Object.entries(SPOTS)) {
  for (const t of night ? ['22:30'] : ['12:30']) {
    await p.goto(`http://localhost:5173/?at=${x},${y},${yaw}&t=${t}`);
    await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
    await p.waitForTimeout(5000);
    await p.screenshot({ path: `${OUT}water_${tag}_${n}${night ? '_n' : ''}.png` });
    if (night) continue;
    const url = await p.evaluate(([x, y]) => {
      const { sbxRenderer: r, sbxScene: s, sbxCamera: c0, sbxTiles: tl, sbxPlayer: pl } = window;
      pl.mesh.visible = false; tl.cull(x, y, 400);
      const c = c0.clone(), H = 3000, size = 140;
      c.fov = 2 * Math.atan(size / 2 / H) * 180 / Math.PI; c.aspect = 1; c.near = H - 200; c.far = H + 200;
      c.position.set(x, H, -y); c.up.set(0, 0, -1); c.lookAt(x, 0, -y); c.updateProjectionMatrix();
      const fog = s.fog; s.fog = null; r.setSize(540, 540, false); r.render(s, c);
      const d = r.domElement.toDataURL('image/png'); s.fog = fog; pl.mesh.visible = true; return d;
    }, [x, y]);
    (await import('node:fs')).writeFileSync(`${OUT}water_${tag}_${n}_top.png`, Buffer.from(url.split(',')[1], 'base64'));
  }
}
await b.close();
