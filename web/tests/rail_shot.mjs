// Free camera shots of the railway. node tests/rail_shot.mjs out.jpg  "name:px,py,pz,tx,ty,tz[,fov]" ...  (local metres, z up; game started at first target)
// Several views -> one contact sheet is made by the caller (python). Time via env T=hh:mm (default 12:00).
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
const [,, outPrefix, ...views] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 500 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
for (const v of views) {
  const [name, rest] = v.split(':'); const a = rest.split(',').map(Number);
  await p.goto(`http://localhost:5173/?at=${process.env.AT || a[3] + ',' + a[4]},0&t=${process.env.T || '12:00'}`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
  await p.waitForTimeout(7000);
  const url = await p.evaluate(([a, tr, hide]) => {
    const { sbxRenderer: r, sbxScene: s, sbxCamera: c0, sbxTiles: t, sbxPlayer: pl } = window;
    pl.mesh.visible = false; if (window.HIDE) { /* noop */ } t.cull(a[3], a[4], 400);
    if (hide) window.sbxRail.group.visible = false;
    if (tr) { // TRAIN=routeIndex:stopIndex[:secondsAfterArrival] -> show that train standing at the stop
      const [ri, si, dt = 12] = tr.split(':').map(Number);
      const R = window.sbxRail.routes[ri]; let n = 0, seg = null;
      for (const g of R.segs) { if (g.ee) { if (n === si) { seg = g; break; } n++; } }
      const M = (R.offset + 20 * R.headway + seg.t0 + seg.T + dt) / 60;
      window.sbxRail.update(0, M, a[3], a[4]);
    }
    const c = c0.clone(); c.fov = a[6] || 60; c.aspect = 800 / 500; c.near = 0.3; c.far = 1500;
    c.position.set(a[0], a[2], -a[1]); c.up.set(0, 1, 0); c.lookAt(a[3], a[5], -a[4]); c.updateProjectionMatrix();
    r.setSize(800, 500, false); r.render(s, c); return r.domElement.toDataURL('image/jpeg', 0.85);
  }, [a, process.env.TRAIN || '', !!process.env.HIDE]);
  writeFileSync(`${outPrefix}_${name}.jpg`, Buffer.from(url.split(',')[1], 'base64'));
}
await b.close();
