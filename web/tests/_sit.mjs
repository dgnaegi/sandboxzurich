import { chromium } from 'playwright';
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 600, height: 400 } })).newPage();
await p.goto(`http://localhost:5173/?at=538,-653,0&t=12:00`);
await p.waitForFunction(() => window.sbxReady && window.sbxCrowd, null, { timeout: 60000 });
await p.waitForTimeout(9000);
console.log(JSON.stringify(await p.evaluate(() => {
  const out = [];
  for (const s of window.sbxCrowd.spots.live) if (s.kind === 'sit') for (const h of s.people) {
    h.root.updateMatrixWorld(true);
    const bones = {}; h.root.traverse(o => { if (o.isBone && /hips|pelvis|root|foot_l|head$/i.test(o.name)) bones[o.name] = o.getWorldPosition(new o.position.constructor()).toArray().map(v => +v.toFixed(2)); });
    out.push({ spot: [s.x, s.y, s.z, +s.ry.toFixed(2)], root: h.root.position.toArray().map(v=>+v.toFixed(2)), bones });
  }
  return out.slice(0, 3);
}), null, 1));
await b.close();
