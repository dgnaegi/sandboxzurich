// QA: A<->B teleport ping-pong; textures/geometries/heap should plateau (leak check)
import { launch, open } from './qa_lib.mjs';
const BASE = process.argv[2] ?? 'http://localhost:5199'; const vp = process.argv[3] ?? 'pc';
const b = await launch();
const { page, cdp } = await open(b, vp, `${BASE}/?at=789,-873,0&t=12:00&nopost`);
const A = [789, -873], B = [58, 117], C = [-491, -690];
for (let i = 0; i < 9; i++) {
  const [x, y] = [A, B, C][i % 3];
  await page.evaluate(async ([x, y]) => { await window.sbxTiles.update(x, y); window.sbxPlayer.teleport(x, y, 0); }, [x, y]);
  await page.waitForTimeout(3500);
  console.log(vp, i, [x, y], JSON.stringify(await page.evaluate(() => { const i = window.sbxRenderer.info; window.gc && window.gc(); return { heapGC: Math.round(performance.memory.usedJSHeapSize / 1e6), tex: i.memory.textures, geo: i.memory.geometries, heap: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1e6) : 0, scene: window.sbxScene.children.length, tiles: window.sbxTiles.loaded?.size }; })));
}
await b.close();
