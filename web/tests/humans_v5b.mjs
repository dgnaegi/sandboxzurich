// Contact sheet of people in the live game: node tests/humans_v4.mjs  -> preview/humans_v5b.jpg (+ preview/hv5b/*.jpg)
// Teleports to a few places (stop, bench, fountain, bar, street, lawn), waits for the crowd, then frames the nearest distinct people
// with a free camera (same trick as pipeline/landmarks/free_shot.mjs). Env: SPOTS='[{"n":"x","at":[x,y],"t":"14:00","dist":3.2,"k":3}]'
import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process'; import fs from 'node:fs';
const R = new URL('../../', import.meta.url).pathname, OUT = R + 'preview/hv5b/';
fs.mkdirSync(OUT, { recursive: true });
const SPOTS = process.env.SPOTS ? JSON.parse(process.env.SPOTS) : [
  { n: 'stop', at: [716, -854], t: '14:00', k: 3 }, { n: 'bench', at: [805, -842], t: '14:00', k: 3 }, { n: 'fount', at: [796, -632], t: '15:00', k: 3 },
  { n: 'bar', at: [858, -792], t: '21:30', k: 3 }, { n: 'street', at: [731, -602], t: '17:30', k: 4 }, { n: 'lawn', at: [582, 154], t: '15:00', k: 3 },
];
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
p.on('pageerror', (e) => { if (!/arc'/.test(e.message)) console.log('pageerror', e.message); });
await p.goto(`http://localhost:5173/?at=${SPOTS[0].at[0]},${SPOTS[0].at[1]}&t=${SPOTS[0].t}`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
const shots = [];
for (const s of SPOTS) {
  await p.evaluate(([s]) => { window.sbxPlayer.teleport(s.at[0], s.at[1], 0); }, [s]);
  await p.waitForTimeout(s.wait || 7000);
  const targets = await p.evaluate(([s]) => {
    const out = [], v = new (window.sbxScene.position.constructor)();
    window.sbxScene.traverse((o) => { if (o.isSkinnedMesh) { o.getWorldPosition(v); const d = Math.hypot(v.x - s.at[0], -v.z - s.at[1]); if (d < 45 && o.visible) { let a = o, vis = true; while (a) { if (!a.visible) vis = false; a = a.parent; } if (vis) out.push({ x: v.x, y: v.y, z: v.z, d }); } } });
    out.sort((a, b) => a.d - b.d); const pick = [];
    for (const t of out) if (pick.every((q) => Math.hypot(q.x - t.x, q.z - t.z) > 5)) pick.push(t);
    return pick.slice(0, s.k || 3);
  }, [s]);
  console.log(s.n, 'people', targets.length);
  let i = 0;
  for (const t of targets) {
    await p.evaluate(([t, dist]) => {
      const w = window, cam = w.sbxCamera;
      if (!cam.__free) { cam.__free = 1; cam.__set = cam.position.set.bind(cam.position); cam.__look = cam.lookAt.bind(cam); cam.position.set = () => cam.position; cam.lookAt = () => {}; w.sbxPlayer.mesh.visible = false;
        const st = document.createElement('style'); st.textContent = 'body > *:not(canvas){display:none !important}'; document.head.appendChild(st); }
      cam.__set(t.x + dist * 0.6, t.y + t.cy, t.z + dist * 0.8); cam.fov = 45; cam.updateProjectionMatrix(); cam.__look(t.x, t.y + t.ly, t.z);
    }, [{ ...t, cy: +process.env.CAMY || 1.5, ly: +process.env.LOOKY || 1.0 }, s.dist || 3.4]);
    await p.waitForTimeout(500);
    const f = `${OUT}${s.n}_${i++}.jpg`; await p.screenshot({ path: f, type: 'jpeg', quality: 82 }); shots.push(f);
  }
}
await b.close();
const sel = shots.slice(0, 24);
execFileSync(R + '.venv/bin/python', ['-I', R + 'web/tests/sheet.py', R + 'preview/humans_v5b.jpg', '4', '400', ...sel]);
console.log('sheet', sel.length);
