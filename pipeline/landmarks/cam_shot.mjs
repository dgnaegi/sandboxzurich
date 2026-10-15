// Free-camera shots: node cam_shot.mjs <outprefix> <loadx,loady> view1 view2 ...  view = px,py,pz,tx,ty,tz[,fov]  (local m, z up, absolute)
import { chromium } from '/Users/danielgnagi/sandboxzurich/web/node_modules/playwright/index.mjs';
import { writeFileSync } from 'node:fs';
const [,, out, load, ...views] = process.argv;
const [lx, ly] = load.split(',').map(Number);
const W = 800, H = 600;
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: W, height: H } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
const tm = process.env.T || '12:00';
await p.goto(`http://localhost:5173/?at=${lx},${ly},0&t=${tm}`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
await p.waitForTimeout(7000);
let i = 0;
for (const v of views) {
  const [px, py, pz, tx, ty, tz, fov = 50] = v.split(',').map(Number);
  const url = await p.evaluate(async ([px, py, pz, tx, ty, tz, fov, W, H, lx, ly]) => {
    const { sbxRenderer: r, sbxScene: s, sbxCamera: c0, sbxTiles: t, sbxPlayer: pl } = window;
    pl.mesh.visible = false; await t.update(px, py); t.cull(px, py, 500);
    const c = c0.clone(); c.fov = fov; c.aspect = W / H; c.near = 0.1; c.far = 600; c.up.set(0, 1, 0);
    c.position.set(px, pz, -py); c.lookAt(tx, tz, -ty); c.updateProjectionMatrix();
    r.setSize(W, H, false); r.render(s, c);
    return r.domElement.toDataURL('image/jpeg', 0.9);
  }, [px, py, pz, tx, ty, tz, fov, W, H, lx, ly]);
  await p.waitForTimeout(1500);
  const url2 = await p.evaluate(([px, py, pz, tx, ty, tz, fov, W, H]) => {
    const { sbxRenderer: r, sbxScene: s, sbxCamera: c0 } = window;
    const c = c0.clone(); c.fov = fov; c.aspect = W / H; c.near = 0.1; c.far = 600; c.up.set(0, 1, 0);
    c.position.set(px, pz, -py); c.lookAt(tx, tz, -ty); c.updateProjectionMatrix();
    r.render(s, c); return r.domElement.toDataURL('image/jpeg', 0.9);
  }, [px, py, pz, tx, ty, tz, fov, W, H]);
  writeFileSync(`${out}_${i++}.jpg`, Buffer.from(url2.split(',')[1], 'base64'));
}
await b.close();
