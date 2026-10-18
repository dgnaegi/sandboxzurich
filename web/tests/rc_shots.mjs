// usage: node tests/rc_shots.mjs shots.json outdir [vfov=80] [height=1.7]  (copy of fidelity_shots.mjs, eye 1.7 m)
// shots.json: [{id, x, y, hdg (compass degrees)}] -> outdir/game_<id>.png (800x600, first-person). Resumes; re-inits after page reloads.
import { chromium } from 'playwright';
import fs from 'fs';
const [,, shotsFile, outDir, vfov = '80', hgt = '1.7'] = process.argv;
const shots = JSON.parse(fs.readFileSync(shotsFile));
fs.mkdirSync(outDir, { recursive: true });
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 600 } })).newPage();
async function setup(s0) {
  await p.goto(`http://localhost:5173/?at=${s0.x},${s0.y},0&t=${s0.t ?? '13:00'}`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await p.addStyleTag({ content: 'body > *:not(canvas){visibility:hidden !important}' });
  await p.evaluate(([vf, h]) => {
    for (const c of document.querySelectorAll('canvas')) if (c !== window.sbxRenderer.domElement) c.style.display = 'none';
    const r = window.sbxRenderer, orig = r.render.bind(r), cam = window.sbxCamera, P = window.sbxPlayer;
    window.__fid = { x: 0, y: 0, hdg: 0 };
    r.render = (s, c) => {
      if (c === cam) {
        const f = window.__fid, z = window.sbxTiles.ground(f.x, f.y) + h;
        cam.fov = vf; cam.aspect = 4 / 3; cam.near = 0.2; cam.updateProjectionMatrix();
        cam.position.set(f.x, z, -f.y); cam.up.set(0, 1, 0);
        cam.lookAt(f.x + Math.sin(f.hdg), z, -(f.y + Math.cos(f.hdg)));
        P.mesh.visible = false;
      }
      orig(s, c);
    };
  }, [Number(vfov), Number(hgt)]);
}
let ok = false;
for (const s of shots) {
  const f = `${outDir}/game_${s.id}.png`;
  if (fs.existsSync(f) && !process.env.REDO) continue;
  for (let tries = 0; tries < 3; tries++) {
    try {
      if (!ok) { await setup(s); ok = true; }
      await p.evaluate((s) => { if (!window.__fid) throw new Error('reloaded'); window.sbxPlayer.teleport(s.x, s.y, 0); window.__fid = { x: s.x, y: s.y, hdg: s.hdg * Math.PI / 180 }; }, s);
      await p.waitForTimeout(s.wait ?? 3500);
      if (!(await p.evaluate(() => !!window.__fid))) throw new Error('reloaded');
      await p.screenshot({ path: f });
      break;
    } catch (e) { console.log('retry', s.id, String(e).slice(0, 80)); ok = false; }
  }
}
await b.close();
