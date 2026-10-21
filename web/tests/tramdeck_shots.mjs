// Tram decks (Hardbrücke + one other tram bridge): desktop + phone shots -> /private/tmp/tramdeck/<tag>_N.png  (node tests/tramdeck_shots.mjs <tag> [base-url])
import { chromium } from 'playwright';
import fs from 'node:fs';
const tag = process.argv[2] ?? 'after', BASE = process.argv[3] ?? 'http://localhost:5173';
const spots = process.env.SPOTS ? JSON.parse(process.env.SPOTS) : [[61, 149, 0.35], [145, 320, -2.54], [1174, -1185, 1.92]];
const views = [[800, 450], [360, 640]];
const tmp = '/private/tmp/tramdeck/'; fs.mkdirSync(tmp, { recursive: true });
const b = await chromium.launch({ args: ['--use-gl=angle'] });
let n = 0;
for (const [w, h] of views) {
  const page = await (await b.newContext({ viewport: { width: w, height: h } })).newPage();
  if (tag === 'before') await page.route(/\/tiles\/t_.*\.json$/, async (route) => {   // old behaviour: strip the open-side flags
    const r = await route.fetch(); const j = await r.json();
    for (const d of j.bridges?.decks ?? []) { delete d.ol; delete d.or; }
    await route.fulfill({ response: r, json: j });
  });
  page.on('pageerror', (e) => console.log('pageerror', e.message));
  await page.goto(`${BASE}/?at=${spots[0][0]},${spots[0][1]},0&t=14:00&nopost`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  for (const [x, y, hd] of spots) {
    await page.evaluate(async ([x, y, hd]) => { const P = window.sbxPlayer; await window.sbxTiles.update(x, y); P.teleport(x, y, hd); P.yaw = hd; }, [x, y, hd]);
    await page.waitForTimeout(4000);
    await page.evaluate(([x, y, hd]) => {   // free oblique camera above the tram deck, looking along it
      const { sbxRenderer: r, sbxScene: sc, sbxCamera: c0, sbxTiles: t, sbxPlayer: pl } = window;
      pl.mesh.visible = false;
      const z = t.bridges.heightAt(x, y, 1e3, 1e3, 1e3) ?? t.ground(x, y);
      const c = c0.clone(); c.near = 0.1; c.far = 400; c.aspect = r.domElement.width / r.domElement.height; c.updateProjectionMatrix();
      c.position.set(x - Math.sin(hd) * 13, z + 9, -(y - Math.cos(hd) * 13)); c.lookAt(x + Math.sin(hd) * 6, z, -(y + Math.cos(hd) * 6));
      window.__tc = c; const old = r.render.bind(r); r.render = (s2, c2) => old(s2, window.__tc);
    }, [x, y, hd]);
    await page.waitForTimeout(600);
    await page.screenshot({ path: `${tmp}${tag}_${n++}.png` });
  }
  await page.close();
}
await b.close();
