// Phone-mode GPU memory estimate at dense places (textures + geometry bytes), plus per-group breakdown.
import { chromium, devices } from 'playwright';
const BASE = process.argv[2] ?? 'http://localhost:5173';
const b = await chromium.launch({ args: ['--use-gl=angle'] });
const ctx = await b.newContext({ ...devices['iPhone 13'], viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true });
for (const [n, x, y] of [['langstrasse', 812, -590], ['hb', 1745, -700], ['hardbruecke', 300, -100]]) {
  const p = await ctx.newPage();
  await p.goto(`${BASE}/?at=${x},${y},0&t=12:00`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 120000 }); await p.waitForTimeout(8000);
  const r = await p.evaluate(() => {
    const sc = window.sbxScene ?? window.sbxRenderer?.__scene, R = window.sbxRenderer;
    const seenT = new Set(), seenG = new Set(); let tb = 0, gb = 0; const grp = {};
    const root = sc ?? null; if (!root) return { info: R.info.memory };
    root.traverse((o) => {
      if (!o.isMesh && !o.isInstancedMesh && !o.isPoints) return;
      let top = o; while (top.parent && top.parent !== root) top = top.parent;
      const key = (top.name || top.type).split(':')[0].slice(0, 24);
      let g = 0;
      if (!seenG.has(o.geometry)) { seenG.add(o.geometry); for (const a of Object.values(o.geometry.attributes)) g += a.array.byteLength; if (o.geometry.index) g += o.geometry.index.array.byteLength; }
      if (o.instanceMatrix) g += o.instanceMatrix.array.byteLength;
      let t = 0;
      for (const m of [].concat(o.material)) for (const k of ['map', 'normalMap', 'emissiveMap', 'alphaMap', 'roughnessMap', 'aoMap']) {
        const tx = m?.[k]; if (!tx || seenT.has(tx)) continue; seenT.add(tx); if ((tx.image?.height ?? 0) >= 8192) (window.__big ??= []).push(k + "|" + (m.name || m.type) + "|" + (o.name || o.parent?.name || "") + "|" + tx.uuid.slice(0,4));
        const im = tx.image; const w = im?.width ?? 0, h = im?.height ?? 0, d = im?.depth ?? 1; t += w * h * d * 4 * 1.33;
      }
      gb += g; tb += t; grp[key] = (grp[key] ?? 0) + g + t;
    });
    const big = []; seenT.forEach((tx) => { const im = tx.image; big.push([(tx.uuid.slice(0,4) + " " + tx.name || im?.src?.split("/").pop() || im?.constructor?.name || "?").slice(0, 30) + " " + (im?.width ?? 0) + "x" + (im?.height ?? 0) + "x" + (im?.depth ?? 1), (im?.width ?? 0) * (im?.height ?? 0) * (im?.depth ?? 1) * 5.3]); }); big.sort((a, b) => b[1] - a[1]);
    const top = Object.entries(grp).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, v]) => `${k} ${(v / 1e6).toFixed(0)}`);
    return { who: window.__big, big: big.slice(0, 14).map(([k, v]) => k + " " + (v / 1e6).toFixed(0)), texMB: (tb / 1e6).toFixed(0), geoMB: (gb / 1e6).toFixed(0), js: (performance.memory?.usedJSHeapSize / 1e6 | 0), calls: R.info.render.calls, info: R.info.memory, top };
  });
  console.log(n, JSON.stringify(r));
  await p.close();
}
await b.close();
