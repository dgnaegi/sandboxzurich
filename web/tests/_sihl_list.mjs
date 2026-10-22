import { chromium } from 'playwright';
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const page = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
await page.goto(`http://localhost:5173/?at=1462,-737,0&t=13:00&nopost`);
await page.waitForFunction(() => window.sbxReady, null, { timeout: 90000 });
await page.waitForTimeout(4000);
const r = await page.evaluate(() => {
  const out = []; const T = window.sbxScene.constructor;
  window.sbxScene.updateMatrixWorld(true);
  window.sbxScene.traverse((o) => {
    if (!o.isMesh && !o.isLine && !o.isInstancedMesh) return;
    const g = o.geometry; if (!g.boundingBox) g.computeBoundingBox();
    const bb = g.boundingBox.clone().applyMatrix4(o.matrixWorld);
    // three x=1466, z=+731 (y=-731)
    if (bb.min.x < 1472 && bb.max.x > 1458 && bb.min.z < 740 && bb.max.z > 724) {
      let p = o, path = []; while (p) { path.push(p.name || p.type); p = p.parent; }
      out.push(path.slice(0, 4).join('<') + ' ' + (o.isInstancedMesh ? 'inst' + o.count : '') + ' bb ' + [bb.min.x, bb.min.y, bb.min.z, bb.max.x, bb.max.y, bb.max.z].map((v) => v.toFixed(0)).join(','));
    }
  });
  return out;
});
console.log(r.join('\n'));
await b.close();
