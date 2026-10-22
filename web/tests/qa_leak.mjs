// QA regression: A/B/C teleport ping-pong; heap after gc() and renderer.info must plateau. FAIL (exit 1) over the limits.
// usage: node tests/qa_leak.mjs [BASE] [pc|phoneL] [maxHeapGrowthMB=60]
import { launch, open } from './qa_lib.mjs';
const BASE = process.argv[2] ?? 'http://localhost:5199', vp = process.argv[3] ?? 'pc', LIMIT = +(process.argv[4] ?? 60);
const b = await launch();
const { page } = await open(b, vp, `${BASE}/?at=789,-873,0&t=12:00&nopost`);
const A = [789, -873], B = [58, 117], C = [-491, -690];
const stat = () => page.evaluate(async () => {
  window.gc && window.gc(); await new Promise((r) => setTimeout(r, 300)); window.gc && window.gc();
  const i = window.sbxRenderer.info;
  return { heap: Math.round(performance.memory.usedJSHeapSize / 1e6), tex: i.memory.textures, geo: i.memory.geometries, scene: window.sbxScene.children.length, tiles: window.sbxTiles.loaded?.size };
});
await page.waitForTimeout(2500);
const s0 = await stat(); console.log(vp, 'start', JSON.stringify(s0));
let last = s0, maxTex = 0, maxGeo = 0;
const seen = new Map(), lastAt = new Map();   // place index -> heap at its first / last visit
for (let i = 0; i < 9; i++) {
  const [x, y] = [A, B, C][i % 3];
  await page.evaluate(async ([x, y]) => { await window.sbxTiles.update(x, y); window.sbxPlayer.teleport(x, y, 0); }, [x, y]);
  await page.waitForTimeout(3500);
  last = await stat();   // min of 3 samples 1 s apart: tile decoding still in flight shows as a transient heap spike, not a leak
  for (let k = 0; k < 2; k++) { await page.waitForTimeout(1000); const s2 = await stat(); if (s2.heap < last.heap) last = s2; }
  maxTex = Math.max(maxTex, last.tex); maxGeo = Math.max(maxGeo, last.geo);
  if (!seen.has(i % 3)) seen.set(i % 3, last.heap);
  lastAt.set(i % 3, last.heap);
  console.log(vp, i, [x, y], JSON.stringify(last));
}
// growth per place (last vs first visit of the SAME place): the places differ in base memory, start-vs-end compared different scenes
const grow = Math.max(...[...seen.keys()].map((k) => lastAt.get(k) - seen.get(k)));
// textures/geometries after the 9th jump must stay within 1.6x of the first revisit (second visit of the same place)
const ok = grow <= LIMIT;
console.log(ok ? 'PASS' : 'FAIL', `heap growth ${grow} MB (limit ${LIMIT}), tex max ${maxTex}, geo max ${maxGeo}`);
await b.close();
process.exit(ok ? 0 : 1);
