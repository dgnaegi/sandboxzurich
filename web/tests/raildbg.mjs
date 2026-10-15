import { chromium } from 'playwright';
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const p = await (await b.newContext({ viewport: { width: 800, height: 450 } })).newPage();
p.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.log('console', m.text().slice(0, 200)); });
await p.goto('http://localhost:5173/?at=-2086,790,0');
await p.waitForFunction(() => window.gtaReady, null, { timeout: 60000 });
await p.waitForTimeout(6000);
console.log(await p.evaluate(() => {
  const r = window.gtaRail, out = [];
  out.push('tiles ' + [...r.tiles.keys()].join(' '));
  r.group.updateMatrixWorld(true); r.group.traverse((o) => { if (o.geometry && !o.geometry.boundingBox) o.geometry.computeBoundingBox(); if (o.isMesh || o.isLineSegments) { const bb = new o.geometry.boundingBox.constructor().setFromObject(o); o.geometry.computeBoundingBox(); out.push(`${o.type} v=${o.geometry.attributes.position.count} attrs=${Object.keys(o.geometry.attributes).join(',')} y=${bb.min.y.toFixed(1)}..${bb.max.y.toFixed(1)} x=${bb.min.x.toFixed(0)}..${bb.max.x.toFixed(0)} z=${bb.min.z.toFixed(0)}..${bb.max.z.toFixed(0)} mat=${o.material.type} vis=${o.visible}`); } });
  return out.slice(0, 14).join('\n');
}));
console.log('player z', await p.evaluate(() => window.gtaPlayer.z));
await b.close();
