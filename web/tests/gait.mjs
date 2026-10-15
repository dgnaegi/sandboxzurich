// Gait strip: the player's walk / run clip sampled at fixed phases, side view -> <OUT>_<clip>_<i>.png (+ contact sheet preview/gait_after.jpg via PIL, see CLI args).
// usage: node tests/gait.mjs [base] [outPrefix] [clip:speed,...]   e.g. node tests/gait.mjs http://localhost:5173 ../preview/gait walk:1.4,run:4.0
import { chromium } from 'playwright';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const OUT = process.argv[3] ?? '../preview/gait';
const CLIPS = (process.argv[4] ?? 'walk:1.4,run:4.0').split(',').map((s) => s.split(':'));
const N = 8;
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const page = await (await b.newContext({ viewport: { width: 800, height: 600 }, deviceScaleFactor: 2 })).newPage();
page.on('console', (m) => { if (m.type() === 'error') console.log('CONSOLE', m.text().slice(0, 200)); });
page.on('framenavigated', (f) => console.log('NAV', f.url().slice(0, 80)));
await page.goto(`${BASE}/?at=760,-560,1.5708`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
await page.waitForTimeout(4000);
for (const [clip, vs] of CLIPS) {
  await page.evaluate(([v]) => {
    const p = window.sbxPlayer, h = p.body;
    h.setSpeed = h.__set ?? h.setSpeed; h.mixer.update = h.__upd ?? h.mixer.update;
    h.__set = h.setSpeed; h.__upd = h.mixer.update;
    p.tiles.colliders.freeFraction = () => 1;           // camera never pulled in by walls
    h.setSpeed(v); for (let i = 0; i < 30; i++) h.mixer.update(0.05); // finish the cross-fade
    h.setSpeed = () => {}; h.mixer.update = () => {};
    p.pitch = 0.05; p.yaw = p.heading + Math.PI / 2; // camera at the player's side
  }, [+vs]);
  await page.waitForTimeout(2500); // camera distance settles
  for (let i = 0; i < N; i++) {
    await page.evaluate(([clip, i, N]) => {
      const h = window.sbxPlayer.body;
      for (const [n, a] of Object.entries(h.actions)) { a.enabled = n === clip; a.setEffectiveWeight(n === clip ? 1 : 0); }
      const a = h.actions[clip]; a.paused = false; a.time = (a.getClip().duration * i) / N; h.__upd.call(h.mixer, 0);
    }, [clip, i, N]);
    await page.waitForTimeout(150);
    await page.screenshot({ path: `${OUT}_${clip}_${i}.png`, clip: { x: 290, y: 255, width: 220, height: 215 } });
  }
}
await b.close();
