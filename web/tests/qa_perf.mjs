// QA perf: 6 places x 60 s (walking), FPS avg/p1, long frames >50 ms, JS heap, renderer.info; phone = 4x CPU throttle
import { launch, open } from './qa_lib.mjs';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const vp = process.argv[3] ?? 'pc';
const SECS = +(process.argv[4] ?? 60);
const SPOTS = [['Helvetiaplatz', 789, -873], ['Langstrasse', 842, -483], ['Hardbruecke', 58, 117], ['HB-Rand/Limmatpl', 718, 410], ['Albisriederplatz', -491, -690], ['Altstetten', -2087, 794]];
const b = await launch();
const { page, log, cdp } = await open(b, vp, `${BASE}/?at=${SPOTS[0][1]},${SPOTS[0][2]},0&t=12:00&nopost`);
if (vp !== 'pc') await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
await page.addScriptTag({ content: `window.__f=[];let l=performance.now();(function f(t){window.__f.push(t-l);l=t;requestAnimationFrame(f)})(l);` });
for (const [n, x, y] of SPOTS) {
  await page.evaluate(async ([x, y]) => { await window.sbxTiles.update(x, y); window.sbxPlayer.teleport(x, y, 0); window.__f.length = 0; }, [x, y]);
  await page.waitForTimeout(2500); await page.evaluate(() => (window.__f.length = 0));
  // walk in a circle-ish: hold W, rotate the camera
  await page.keyboard.down('KeyW');
  for (let i = 0; i < SECS / 5; i++) { await page.evaluate(() => (window.sbxPlayer.yaw += 0.9)); await page.waitForTimeout(5000); }
  await page.keyboard.up('KeyW');
  const r = await page.evaluate(() => {
    const f = window.__f.slice().sort((a, c) => a - c), tot = f.reduce((a, c) => a + c, 0), i = window.sbxRenderer.info;
    return { fps: +(1000 * f.length / tot).toFixed(1), p99ms: +f[Math.floor(f.length * 0.99)].toFixed(1), max: +f[f.length - 1].toFixed(0), over50: f.filter((v) => v > 50).length, over100: f.filter((v) => v > 100).length, heapMB: performance.memory ? +(performance.memory.usedJSHeapSize / 1e6).toFixed(0) : null, tex: i.memory.textures, geo: i.memory.geometries, calls: i.render.calls, tris: +(i.render.triangles / 1e3).toFixed(0) + 'k', pos: [window.sbxPlayer.x | 0, window.sbxPlayer.y | 0] };
  });
  console.log(vp, n, JSON.stringify(r));
}
console.log('errors', log.errors.slice(0, 5), 'bad', log.bad.slice(0, 5));
await b.close();
