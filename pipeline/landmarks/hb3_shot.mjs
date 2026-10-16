// hb3 in-game views in the HB frame: node hb3_shot.mjs out_prefix '[[d,c,z, ld,lc,lz, fov], ...]' (z = metres above the hall plateau, model frame). Dev server :5173.
import { chromium } from '/Users/danielgnagi/sandboxzurich/web/node_modules/playwright/index.mjs';
const [,, prefix, js, port = '5173', vw = '900', vh = '500'] = process.argv;
const views = JSON.parse(js);
const A = (-21 * Math.PI) / 180, O = [1760, -650], GZ = -2.9;
const tw = (d, c) => [O[0] + d * Math.cos(A) - c * Math.sin(A), O[1] + d * Math.sin(A) + c * Math.cos(A)];
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await (await b.newContext({ viewport: { width: +vw, height: +vh } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
const l0 = tw(views[0][3], views[0][4]);
await p.goto(`http://127.0.0.1:${port}/?at=${l0[0]},${l0[1]}&t=12:00`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
const place = (v) => {
  const w = window, cam = w.sbxCamera, pl = w.sbxPlayer;
  if (!cam.__free) { cam.__free = 1; cam.__set = cam.position.set.bind(cam.position); cam.__look = cam.lookAt.bind(cam); cam.position.set = () => cam.position; cam.lookAt = () => {}; }
  pl.mesh.visible = false;
  if (!w.__hid) { w.__hid = 1; const st = document.createElement('style'); st.textContent = 'body > *:not(canvas){display:none !important}'; document.head.appendChild(st); }
  cam.__set(v.P[0], v.P[2], -v.P[1]); cam.fov = v.fov; cam.updateProjectionMatrix(); cam.__look(v.L[0], v.L[2], -v.L[1]);
};
let i = 0;
for (const v of views) {
  const P = tw(v[0], v[1]), L = tw(v[3], v[4]);
  const o = { P: [P[0], P[1], GZ + v[2]], L: [L[0], L[1], GZ + v[5]], fov: v[6] || 60 };
  await p.evaluate(([x, y, z]) => { window.sbxPlayer.z = z; window.sbxPlayer.teleport(x, y, 0); }, [...(v[7] ? tw(v[7][0], v[7][1]) : L), v[7] ? GZ + v[7][2] : GZ + 0.1]);   // v[7] = [d,c,z] underground player position
  await p.waitForTimeout(6000);
  await p.evaluate(place, o); await p.waitForTimeout(800); await p.evaluate(place, o);
  await p.screenshot({ path: `${prefix}_${i++}.jpg`, type: 'jpeg', quality: 80 });
}
await b.close();
