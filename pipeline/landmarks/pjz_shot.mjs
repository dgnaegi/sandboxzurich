// Isolated PJZ model views (no game): node pjz_shot.mjs <outprefix> px,py,pz,lx,ly,lz[,fov] ...   (model-local metres)
import { chromium } from '/Users/danielgnagi/sandboxzurich/web/node_modules/playwright/index.mjs';
const [,, out, ...views] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 600 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
let i = 0;
for (const v of views) {
  const [px, py, pz, lx, ly, lz, fov = 50] = v.split(',').map(Number);
  await p.goto(`http://localhost:5173/_pjz_view.html?p=${px},${py},${pz}&l=${lx},${ly},${lz}&fov=${fov}`);
  await p.waitForFunction(() => window.done, null, { timeout: 60000 });
  await p.screenshot({ path: `${out}_${i++}.jpg`, type: 'jpeg', quality: 85 });
}
await b.close();
