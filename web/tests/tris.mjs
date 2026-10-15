import { chromium, devices } from 'playwright';
const at = process.argv[2] ?? '785,-635,0.37&t=17:40';
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const p = await (await b.newContext(process.env.PHONE ? { ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true } : { viewport: { width: 1280, height: 720 } })).newPage();
await p.goto(`http://localhost:5173/?at=${at}`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 60000 });
await p.waitForTimeout(4000);
console.log(await p.evaluate((CALLS) => {
  const by = new Map();
  const label = (o) => { if (o.isLineSegments) return 'lines:' + (o.parent?.name || o.parent?.parent?.name || '?'); const n = []; for (let q = o; q; q = q.parent) if (q.name) n.push(q.name); return (n.reverse().slice(0, 3).join('/') || (o.parent?.type + '>' + o.material?.type)).replace(/t_-?\d+_-?\d+/g, 't_*'); };
  window.sbxScene.traverseVisible((o) => {
    if (!o.isMesh && !o.isSkinnedMesh && !o.isInstancedMesh && !o.isLineSegments && !o.isPoints) return;
    const g = o.geometry, t = (g.index ? g.index.count : g.attributes.position.count) / 3 * (o.isInstancedMesh ? o.count : 1);
    const k = label(o) + (label(o) === 'props' ? (o.isInstancedMesh ? ':inst' + Math.round(g.attributes.position.count) : ':merged') : ''); const e = by.get(k) ?? [0, 0]; e[0] += t; e[1]++; by.set(k, e);
  });
  return [...by].sort((a, b) => b[1][CALLS ? 1 : 0] - a[1][CALLS ? 1 : 0]).slice(0, 18).map(([k, [t, c]]) => `${(t / 1e3).toFixed(0).padStart(6)}k ${String(c).padStart(4)}  ${k}`).join('\n');
}, !!process.env.CALLS));
await b.close();
