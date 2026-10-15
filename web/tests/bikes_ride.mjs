// Ridden bike close-ups from the side (wheels/cranks split + lean). Output preview/bike_ride_*.png and bikes_ride_sheet.jpg
import { chromium } from 'playwright';
import { execSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
const tmp = '/tmp/bride/'; mkdirSync(tmp, { recursive: true });
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await (await b.newContext({ viewport: { width: 640, height: 400 } })).newPage();
page.on('pageerror', (e) => console.log('pageerror', e.message));
await page.goto('http://localhost:5173/?at=785,-635,0.37&t=15:30&nopost');
await page.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
await page.waitForTimeout(1200);
const types = ['city', 'trekking', 'ebike', 'cargo'];
let n = 0;
for (const type of types) {
  await page.evaluate((type) => {
    const p = window.sbxPlayer, s = window.sbxBikes.nearest(p.x, p.y, 300);
    p.dismount(); p.teleport(s.x + 3, s.y, 0);
    const slot = { ...s, type, color: s.color }; p.mount(slot);
    if (!p.__patched) { p.__patched = true; const o = p.update.bind(p); p.update = (dt, cam) => { o(dt, cam); const h = p.heading; cam.position.set(p.x + Math.cos(h) * 2.6, p.z + 1.0, -(p.y - Math.sin(h) * 2.6) ); cam.lookAt(p.x, p.z + 0.85, -p.y); }; }
  }, type);
  await page.keyboard.down('KeyW'); await page.waitForTimeout(1800);
  await page.keyboard.down('KeyD'); await page.waitForTimeout(500);
  await page.screenshot({ path: `${tmp}b${n++}.png` });
  await page.keyboard.up('KeyD'); await page.keyboard.up('KeyW'); await page.waitForTimeout(300);
}
await b.close();
execSync(`python3 - <<'PY'
from PIL import Image
ims=[Image.open('${tmp}b%d.png'%i).resize((400,250)) for i in range(4)]
W=Image.new('RGB',(1600,250))
for i,im in enumerate(ims): W.paste(im,(i*400,0))
W.save('/Users/danielgnagi/sandboxzurich/preview/bikes_ride_sheet.jpg',quality=82)
PY`);
