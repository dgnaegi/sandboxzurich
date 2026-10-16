// QA: count live THREE objects (queryObjects) vs. objects reachable from the scene -> orphans = leak
import { chromium } from 'playwright';
const BASE = process.argv[2] ?? 'http://localhost:5199', N = +(process.argv[3] ?? 6);
const b = await chromium.launch({ args: ['--js-flags=--expose-gc', '--use-gl=angle', '--enable-precise-memory-info'] });
const ctx = await b.newContext({ viewport: { width: 1280, height: 720 } });
const page = await ctx.newPage();
await page.goto(`${BASE}/?at=789,-873,0&t=12:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
const cdp = await ctx.newCDPSession(page);
const pts = [[789, -873], [58, 117], [-491, -690]];
async function count(kind) {
  const expr = `(() => { let p = null; window.sbxScene.traverse((o) => { if (p) return; if ('${kind}' === 'inst' && o.isInstancedMesh) p = Object.getPrototypeOf(o); if ('${kind}' === 'mesh' && o.isMesh && !o.isInstancedMesh && !o.isSkinnedMesh) p = Object.getPrototypeOf(o); if ('${kind}' === 'skin' && o.isSkinnedMesh) p = Object.getPrototypeOf(o); }); return p; })()`;
  const h = (await cdp.send('Runtime.evaluate', { expression: expr })).result;
  const { objects } = await cdp.send('Runtime.queryObjects', { prototypeObjectId: h.objectId });
  const r = await cdp.send('Runtime.callFunctionOn', { objectId: objects.objectId, functionDeclaration: 'function(){return this.length}', returnByValue: true });
  return r.result.value;
}
async function snap(label) {
  await page.evaluate(() => window.gc());
  const inScene = await page.evaluate(() => { let i = 0, m = 0, s = 0; window.sbxScene.traverse((o) => { if (o.isInstancedMesh) i++; else if (o.isSkinnedMesh) s++; else if (o.isMesh) m++; }); return { inst: i, mesh: m, skin: s }; });
  const live = { inst: await count('inst'), mesh: await count('mesh'), skin: await count('skin') };
  const heap = await page.evaluate(() => Math.round(performance.memory.usedJSHeapSize / 1e6));
  console.log(label, 'heap', heap, 'scene', JSON.stringify(inScene), 'live', JSON.stringify(live));
}
await snap('start');
for (let i = 0; i < N; i++) {
  const [x, y] = pts[i % 3];
  await page.evaluate(async ([x, y]) => { await window.sbxTiles.update(x, y); window.sbxPlayer.teleport(x, y, 0); }, [x, y]);
  await page.waitForTimeout(3000);
  await snap('jump' + i);
}
await b.close();
