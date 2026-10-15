import { chromium, devices } from 'playwright';
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const p = await (await b.newContext({ ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true })).newPage();
await p.goto(`http://localhost:5173/?at=${process.argv[2]}`);
await p.waitForFunction(() => window.gtaReady, null, { timeout: 60000 });
await p.waitForTimeout(4000);
console.log(await p.evaluate(() => {
  const S = window.gtaScene, by = new Map();
  S.children.forEach((top, i) => {
    let n = 0, vis = 0;
    top.traverseVisible((o) => { if (o.isMesh || o.isLineSegments) vis++; });
    if (vis) by.set(`#${i} ${top.type} ${top.name || ''} kids=${top.children.length} ud=${Object.keys(top.userData).join(',')}`, vis);
  });
  return [...by].sort((a, b) => b[1] - a[1]).slice(0, 12).map(([k, v]) => `${String(v).padStart(5)} ${k}`).join('\n');
}));
await b.close();
