// Model-only viewer shots via web/lmview.html. Usage: node view.mjs out_prefix '<json views>'  views: [{m, p:[x,y,h], l:[x,y,h], fov, n, g}] (x,y relative to model origin)
import { chromium } from '/Users/danielgnagi/sandboxzurich/web/node_modules/playwright/index.mjs';
const [,, prefix, js] = process.argv;
const b = await chromium.launch({ args: ['--use-gl=angle', '--enable-unsafe-swiftshader'] });
const ctx = await b.newContext({ viewport: { width: 800, height: 450 } });
let i = 0;
for (const v of JSON.parse(js)) {
  const p = await ctx.newPage();
  p.on('pageerror', (e) => console.log('pageerror', e.message));
  const qs = new URLSearchParams({ m: v.m, p: v.p.join(','), l: v.l.join(','), fov: v.fov || 50, n: v.n || 0, g: v.g || '6d7068', gz: v.gz || 0 });
  await p.goto('http://localhost:5173/lmview.html?' + qs);
  await p.waitForFunction(() => window.done, null, { timeout: 40000 });
  await p.screenshot({ path: `${prefix}_${i++}.jpg`, type: 'jpeg', quality: 82 }); await p.close();
}
await b.close();
