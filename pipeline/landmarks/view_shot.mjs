// Isolated model views: node view_shot.mjs <outprefix> <modelname-prefix> view... ; view = px,py,pz,lx,ly,lz[,fov[,night]] (model-local m)
import { chromium } from '/Users/danielgnagi/sandboxzurich/web/node_modules/playwright/index.mjs';
const [,, out, name, ...views] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 600 } })).newPage();
p.on('pageerror', (e) => console.log('pageerror', e.message));
let i = 0;
for (const v of views) {
  const [px, py, pz, lx, ly, lz, fov = 50, n = 0] = v.split(',').map(Number);
  await p.goto(`http://localhost:5173/lmview.html?m=${encodeURIComponent(name)}&p=${px},${py},${pz}&l=${lx},${ly},${lz}&fov=${fov}&n=${n}&w=800&h=600`);
  await p.waitForFunction(() => window.done, null, { timeout: 60000 });
  await p.screenshot({ path: `${out}_${i++}.jpg`, type: 'jpeg', quality: 88 });
}
await b.close();
