// Contact sheet of the drivable car rigs (and driven-car chase view). Output preview/vehicles_v2.jpg
import { chromium } from 'playwright';
import { execSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
const BASE = 'http://localhost:5173';
const out = new URL('../../preview/', import.meta.url).pathname, tmp = '/tmp/vsheet/';
mkdirSync(tmp, { recursive: true });
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const page = await (await b.newContext({ viewport: { width: 640, height: 400 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
await page.goto(`${BASE}/?at=785,-635,0.37&t=15:30&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
await page.waitForTimeout(1500);
const types = ['hatch', 'wagon', 'small', 'sedan', 'suv', 'van', 'sport'];
const colors = [0x5d6268, 0xe2e2df, 0x8c1c22, 0x1b2c4e, 0x1a1c20, 0xe2e2df, 0xf2c200];
await page.addStyleTag({ content: 'body > *:not(canvas) { display: none !important; }' });
await page.evaluate(() => { window.__upd = window.sbxPlayer.update; window.sbxPlayer.update = () => {}; window.sbxPlayer.mesh.visible = false; });
for (let i = 0; i < types.length; i++) {
  await page.evaluate(async ([type, col, i]) => {
    const { buildRig } = await import('/src/player/vehicle_model.ts');
    const p = window.sbxPlayer, sc = window.sbxScene;
    sc.getObjectByName('sheetcar')?.removeFromParent();
    const rig = await buildRig(type, new window.sbxScene.fog.color.constructor(col));
    rig.group.name = 'sheetcar';
    const x = p.x + 6, y = p.y + 0, z = window.sbxTiles.ground(x, y);
    rig.group.position.set(x, z, -y); rig.group.rotation.y = -1.0;
    rig.setWheels(0.5, i % 2 ? 0.3 : 0);
    rig.setLights({ brake: i % 3 === 0, reverse: false, night: 0, blink: i % 2 ? 1 : 0, blinkOn: true });
    sc.add(rig.group);
    const c = window.sbxCamera;
    c.position.set(x + 3.4, z + 1.6, -y + 5.2); c.lookAt(x, z + 0.6, -y);
    if (i >= 5) { c.position.set(x - 3.0, z + 1.5, -y - 5.0); c.lookAt(x, z + 0.7, -y); } // rear 3/4 for the last ones
  }, [types[i], colors[i], i]);
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${tmp}c${i}.png` });
}
// driven car on the road: take a passing car, drive, turn, brake (chase camera)
await page.evaluate(() => { window.sbxPlayer.update = window.__upd; window.sbxPlayer.mesh.visible = true; });
await page.evaluate(() => {
  const t = window.sbxTraffic, c = t.positions().find((v) => v.kind === 'car');
  window.sbxPlayer.teleport(c.x + Math.cos(c.heading + 1.57) * 1.8, c.y + Math.sin(c.heading + 1.57) * 1.8, 0);
});
await page.waitForTimeout(100);
await page.evaluate(async () => { const n = window.sbxCarUse.nearest(); if (n) await window.sbxCarUse.enter(n); });
await page.waitForTimeout(300);
console.log('driving', await page.evaluate(() => !!window.sbxPlayer.driving));
await page.keyboard.down('KeyW'); await page.waitForTimeout(2600);
await page.screenshot({ path: `${tmp}c7.png` });
await page.keyboard.down('KeyD'); await page.waitForTimeout(900);
await page.screenshot({ path: `${tmp}c8.png` });
await page.keyboard.up('KeyD'); await page.keyboard.up('KeyW'); await page.keyboard.down('KeyS'); await page.waitForTimeout(700);
await page.screenshot({ path: `${tmp}c9.png` });
await b.close();
execSync(`python3 - <<'PY'
from PIL import Image
import glob
ims=[Image.open(f'${tmp}c{i}.png').resize((400,250)) for i in range(10)]
import os
for k in (0,2):
    f='/tmp/bride/b%d.png'%k
    if os.path.exists(f): ims.append(Image.open(f).resize((400,250)))
W=Image.new('RGB',(1600,750))
for i,im in enumerate(ims): W.paste(im,((i%4)*400,(i//4)*250))
W.save('${out}vehicles_v2.jpg',quality=82)
PY`);
console.log('ok');
