// Top-down render of the game at the street-audit control points (pipeline/ortho.py resolves them).
// usage: node pipeline/ortho_render.mjs [name,name,...]   -> data/build/ortho_game/<name>.png (needs dev server on :5173)
import { chromium } from '../web/node_modules/playwright/index.mjs';
import fs from 'fs';
const pts = JSON.parse(fs.readFileSync('data/build/ortho_points.json'));
const only = process.argv[2]?.split(',');
const W = 120, PX = 1200;
fs.mkdirSync('data/build/ortho_game', { recursive: true });
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await (await b.newContext({ viewport: { width: 640, height: 400 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
for (const [name, [x, y]] of Object.entries(pts)) {
  if (only && !only.includes(name)) continue;
  await p.goto(`http://localhost:5173/?at=${x.toFixed(1)},${y.toFixed(1)},0&t=13:00&nopost=1`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 240000 });
  await p.waitForTimeout(5000);
  const url = await p.evaluate(async ([x, y, W, PX]) => {
    const T = await import('/node_modules/.vite/deps/three.js');
    const r = new T.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    r.setSize(PX, PX); r.shadowMap.enabled = true;
    const s = window.sbxScene; const fn = s.fog?.near, ff = s.fog?.far; if (s.fog) { s.fog.near = 1e6; s.fog.far = 2e6; }
    const c = new T.OrthographicCamera(-W / 2, W / 2, W / 2, -W / 2, 1, 2000);
    c.position.set(x, 600, -y); c.up.set(0, 0, -1); c.lookAt(x, 0, -y);
    r.render(s, c);
    const u = r.domElement.toDataURL('image/png'); r.dispose(); if (s.fog) { s.fog.near = fn; s.fog.far = ff; } return u;
  }, [x, y, W, PX]);
  fs.writeFileSync(`data/build/ortho_game/${name}.png`, Buffer.from(url.split(',')[1], 'base64'));
  console.log(name);
}
await b.close();
