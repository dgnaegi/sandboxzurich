// Ad-hoc: iconic screenshots with a free camera (no HUD) -> preview/iconic_<n>.jpg
// arg: JSON [{at:"x,y,yaw", t:"18:40", cam:[x,y,heightAboveGround], look:[x,y,heightAboveGround], fov}]
import { chromium } from 'playwright';
const shots = JSON.parse(process.argv[2]);
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const page = await (await b.newContext({ viewport: { width: 1600, height: 900 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
let n = Number(process.env.START ?? 0);
for (const s of shots) {
  await page.goto(`http://localhost:5173/?at=${s.at}&t=${s.t}`);
  await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
  await page.addStyleTag({ content: 'body > *:not(canvas){visibility:hidden !important}' });
  await page.evaluate((s) => {
    for (const c of document.querySelectorAll('canvas')) if (c !== window.sbxRenderer.domElement) c.style.display = 'none';
    const r = window.sbxRenderer, orig = r.render.bind(r), cam = window.sbxCamera, P = window.sbxPlayer, T = window.sbxTiles;
    r.render = (sc, c) => {
      if (c === cam) {
        const [x, y, h] = s.cam, [lx, ly, lh] = s.look;
        cam.fov = s.fov ?? 55; cam.updateProjectionMatrix();
        cam.position.set(x, T.ground(x, y) + h, -y); cam.lookAt(lx, T.ground(lx, ly) + lh, -ly);
        P.mesh.visible = !!s.player;
      }
      orig(sc, c);
    };
  }, s);
  await page.waitForTimeout(9000);
  await page.screenshot({ path: `../preview/iconic_${n++}.jpg`, quality: 90, type: 'jpeg' });
}
await b.close();
