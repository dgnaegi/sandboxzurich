// Free-camera shots in the HB test server (port 5176, tiles from scratch build). Usage: node hb_game_shot.mjs out_prefix json
// views: [{p:[x,y,h], l:[x,y,h], fov:50, t:"12:00", w:800, hh:450}]  (x,y local metres; h = metres above ground at that point)
import { chromium } from '/Users/danielgnagi/sandboxzurich/web/node_modules/playwright/index.mjs';
const [,, prefix, js, tdef] = process.argv;
const views = JSON.parse(js);
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await (await b.newContext({ viewport: { width: views[0].w || 800, height: views[0].hh || 450 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
const v0 = views[0];
await p.goto(`http://127.0.0.1:5176/?at=${v0.l[0]},${v0.l[1]}&t=${v0.t || tdef || '12:00'}`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
let i = 0;
const place = (v) => {
  const w = window, cam = w.sbxCamera, pl = w.sbxPlayer, T = w.sbxTiles, g = (x, y) => T.ground(x, y);
  if (!cam.__free) { cam.__free = 1; cam.__set = cam.position.set.bind(cam.position); cam.__look = cam.lookAt.bind(cam); cam.position.set = () => cam.position; cam.lookAt = () => {}; }
  pl.mesh.visible = false;
  if (!w.__hid) { w.__hid = 1; const st = document.createElement('style'); st.textContent = 'body > *:not(canvas){display:none !important}'; document.head.appendChild(st); }
  if (v.nob) w.sbxScene.traverse((o) => { if (o.name === 'buildings') o.visible = false; });
  const P = v.p, L = v.l;
  cam.__set(P[0], v.az !== undefined ? v.az : g(P[0], P[1]) + P[2], -P[1]);   // az/lz: absolute eye / look z (local metres)
  cam.fov = v.fov || 50; cam.updateProjectionMatrix();
  cam.__look(L[0], v.lz !== undefined ? v.lz : g(L[0], L[1]) + L[2], -L[1]);
};
for (const v of views) {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
      await p.evaluate(([v]) => { window.sbxPlayer.teleport(v.l[0], v.l[1], 0); }, [v]);
      await p.waitForTimeout(v.wait || 5000);
      await p.evaluate(place, v);
      await p.waitForTimeout(900);
      await p.evaluate(place, v);
      await p.screenshot({ path: `${prefix}_${i}.jpg`, type: 'jpeg', quality: 82 });
      break;
    } catch (e) { console.log('retry', attempt, String(e).slice(0, 80)); await p.waitForTimeout(3000); }
  }
  i++;
}
await b.close();
