// Scene sweep over the whole play area: per tile, query the loaded scene (not images).
// node tests/sweep.mjs [BASE=http://localhost:5199] [out=research/sweep.json] [tileFilter regex]
// Start the snapshot server first: node tests/sweep_server.mjs <distDir> 5199
// Checks: ground holes, ground mismatch (mesh vs tiles.ground), floating / buried mesh components, buildings on carriageway,
// buildings without collider, collider without building, z-fight (coplanar up-faces), landmark base vs ground / road, NPC & traffic in footprints.
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';

const BASE = process.argv[2] ?? 'http://localhost:5199';
const OUT = process.argv[3] ?? new URL('../../research/sweep.json', import.meta.url).pathname;
const FILTER = process.argv[4] ? new RegExp(process.argv[4]) : null;

const analyse = (name) => {
  const T = window.sbxTiles, g = T.loaded.get(name);
  if (!g) return { name, missing: true };
  const S = T.world.tile, mm = name.match(/t_(-?\d+)_(-?\d+)/), X0 = +mm[1] * S, Y0 = +mm[2] * S, N = S; // 1 m raster
  const meshes = [];
  const nearG = T.props.get(name)?.near, cut = nearG ? g.children.indexOf(nearG) : g.children.length;
  g.children.forEach((c, ci) => { if (ci < cut) c.traverse((o) => { if (o.isMesh && !o.isInstancedMesh) { o.userData.__glb = true; meshes.push(o); } }); else if (c.name === 'bridges' || c.name === 'decals') c.traverse((o) => { if (o.isMesh && !o.isInstancedMesh) meshes.push(o); }); });
  const hits = Array.from({ length: N * N }, () => null);
  const res = { name, issues: [] };
  const add = (type, x, y, extra) => res.issues.push({ type, x: +x.toFixed(1), y: +y.toFixed(1), ...extra });
  // ---- pass 1: components of mesh_0 (welded by position)
  const parent = new Map(); const find = (a) => { let r = a; while (parent.get(r) !== r) r = parent.get(r); while (parent.get(a) !== r) { const n = parent.get(a); parent.set(a, r); a = n; } return r; };
  const key = (x, y, z) => Math.round(x * 20) + ',' + Math.round(y * 20) + ',' + Math.round(z * 20);
  const tris = []; // per mesh {m, a:[x,y,z]x3, ka}
  meshes.forEach((m, mi) => {
    m.updateMatrixWorld(true);
    const pos = m.geometry.attributes.position, idx = m.geometry.index, n = idx ? idx.count : pos.count, v = new window.sbxCamera.position.constructor();
    const cache = new Map();
    const P = (i) => { let p = cache.get(i); if (!p) { v.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld); p = [v.x, v.y, v.z]; cache.set(i, p); } return p; };
    for (let t = 0; t < n; t += 3) {
      const ia = idx ? idx.getX(t) : t, ib = idx ? idx.getX(t + 1) : t + 1, ic = idx ? idx.getX(t + 2) : t + 2;
      const a = P(ia), b = P(ib), c = P(ic);
      const ka = key(...a), kb = key(...b), kc = key(...c);
      if (meshes[mi].userData.__glb) { for (const k of [ka, kb, kc]) if (!parent.has(k)) parent.set(k, k); parent.set(find(ka), find(kb)); parent.set(find(kb), find(kc)); }
      tris.push({ mi, a, b, c, ka });
    }
  });
  // ---- raster of up/down faces
  for (let ti = 0; ti < tris.length; ti++) {
    const { mi, a, b, c, ka } = tris[ti];
    const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx, nl = Math.hypot(nx, ny, nz) || 1;
    if (Math.abs(ny) / nl < 0.5) continue;
    const up = ny > 0, comp = meshes[mi].userData.__glb ? find(ka) : '#' + mi;
    // 2D (x, -z)
    const ax = a[0], ay = -a[2], bx = b[0], by = -b[2], cx = c[0], cy = -c[2];
    const minx = Math.max(0, Math.floor(Math.min(ax, bx, cx) - X0)), maxx = Math.min(N - 1, Math.floor(Math.max(ax, bx, cx) - X0));
    const miny = Math.max(0, Math.floor(Math.min(ay, by, cy) - Y0)), maxy = Math.min(N - 1, Math.floor(Math.max(ay, by, cy) - Y0));
    const d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy); if (Math.abs(d) < 1e-9) continue;
    for (let j = miny; j <= maxy; j++) for (let i = minx; i <= maxx; i++) {
      const px = X0 + i + 0.5, py = Y0 + j + 0.5;
      const l1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / d, l2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / d, l3 = 1 - l1 - l2;
      if (l1 < 0 || l2 < 0 || l3 < 0) continue;
      const y = l1 * a[1] + l2 * b[1] + l3 * c[1];
      (hits[j * N + i] ??= []).push({ y, mi, up, comp, bm: Math.min(l1, l2, l3), ti });
    }
  }
  const inPoly = (x, y) => T.inPlay(x, y);
  const cells = { hole: [], mism: [], roofNoCol: [], colNoRoof: [], bldRoad: [], zf: [] };
  const grid = (arr) => { const s = new Set(arr.map((c) => c.j * N + c.i)); return s; };
  for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
    const x = X0 + i + 0.5, y = Y0 + j + 0.5, h = hits[j * N + i];
    if (!inPoly(x, y)) continue;
    const gnd = T.ground(x, y), inB = T.colliders.inside(x, y);
    const ups = (h ?? []).filter((q) => q.up).sort((p, q) => p.y - q.y);
    const near = ups.filter((q) => Math.abs(q.y - gnd) < 0.7);
    if (!near.length && !inB && !T.inWater(x, y)) cells.hole.push({ i, j, x, y, gnd, nearest: ups.length ? ups.reduce((p, q) => Math.abs(q.y - gnd) < Math.abs(p.y - gnd) ? q : p).y - gnd : null });
    else if (near.length) { const top = near[near.length - 1]; if (Math.abs(top.y - gnd) > 0.25 && !inB) cells.mism.push({ i, j, x, y, d: top.y - gnd }); }
    const roof = ups.filter((q) => meshes[q.mi].userData.__glb && q.y > gnd + 3.5);
    if (roof.length && !inB && !T.bridges.heightAt(x, y, gnd, 40)) cells.roofNoCol.push({ i, j, x, y, d: roof[0].y - gnd });
    if (roof.length && T.onRoad(x, y)) cells.bldRoad.push({ i, j, x, y, d: roof[0].y - gnd });
    if (inB && !ups.some((q) => q.y > gnd + 2)) cells.colNoRoof.push({ i, j, x, y, d: 0 });
    // z-fight between up faces (or down faces) of different triangles
    for (const side of [true, false]) {
      const hs = (h ?? []).filter((q) => q.up === side && q.bm > 0.02).sort((p, q) => p.y - q.y);
      for (let k = 1; k < hs.length; k++) if (hs[k].y - hs[k - 1].y < 0.02 && hs[k].ti !== hs[k - 1].ti && hs[k].comp !== hs[k - 1].comp) { { const A = meshes[hs[k - 1].mi], B = meshes[hs[k].mi], nm = (o) => o.userData.__glb ? 'ground' : o.name; if (A.material.polygonOffset || B.material.polygonOffset || B.name === 'decals' || A.name === 'decals' || A.parent?.name === 'decals' || B.parent?.name === 'decals') break; cells.zf.push({ i, j, x, y, d: hs[k].y - hs[k - 1].y, pair: nm(A) + '/' + nm(B), up: side }); }; break; }
    }
  }
  // cluster cells (8-neighbour, gap 2)
  const cluster = (arr, type, minN, extra) => {
    const m = new Map(arr.map((c) => [c.j * N + c.i, c])); const seen = new Set();
    for (const [k, c0] of m) {
      if (seen.has(k)) continue; const st = [k]; seen.add(k); const mem = [];
      while (st.length) { const q = st.pop(), c = m.get(q); mem.push(c); const qi = q % N, qj = (q / N) | 0;
        for (let dj = -2; dj <= 2; dj++) for (let di = -2; di <= 2; di++) { const ni = qi + di, nj = qj + dj; if (ni < 0 || nj < 0 || ni >= N || nj >= N) continue; const kk = nj * N + ni; if (m.has(kk) && !seen.has(kk)) { seen.add(kk); st.push(kk); } } }
      if (mem.length < minN) continue;
      const cx = mem.reduce((s, c) => s + c.x, 0) / mem.length, cy = mem.reduce((s, c) => s + c.y, 0) / mem.length;
      add(type, cx, cy, { n: mem.length, ...extra(mem) });
    }
  };
  const mx = (mem, f) => +Math.max(...mem.map(f)).toFixed(2);
  cluster(cells.hole, 'ground_hole', 4, (m) => ({ nearest: m[0].nearest == null ? 'no surface' : +m[0].nearest.toFixed(1) }));
  cluster(cells.mism, 'ground_mismatch', 12, (m) => ({ maxdz: mx(m, (c) => Math.abs(c.d)) }));
  cluster(cells.roofNoCol, 'building_no_collider', 10, (m) => ({ h: mx(m, (c) => c.d) }));
  cluster(cells.colNoRoof, 'collider_no_building', 20, () => ({}));
  cluster(cells.bldRoad, 'building_on_road', 6, (m) => ({ h: mx(m, (c) => c.d) }));
  for (const pair of new Set(cells.zf.map((c) => c.pair))) cluster(cells.zf.filter((c) => c.pair === pair), 'zfight_' + pair.replace('/', '_'), 6, () => ({ pair }));
  // ---- floating / buried components of mesh_0
  const comps = new Map();
  for (const t of tris) {
    if (!meshes[t.mi].userData.__glb) continue; const r = find(t.ka); let c = comps.get(r);
    if (!c) comps.set(r, c = { n: 0, minY: 1e9, maxY: -1e9, mx: 0, my: 0, x0: 1e9, x1: -1e9, y0: 1e9, y1: -1e9 });
    c.n++;
    for (const p of [t.a, t.b, t.c]) { if (p[1] < c.minY) { c.minY = p[1]; c.mx = p[0]; c.my = -p[2]; } c.maxY = Math.max(c.maxY, p[1]); c.x0 = Math.min(c.x0, p[0]); c.x1 = Math.max(c.x1, p[0]); c.y0 = Math.min(c.y0, -p[2]); c.y1 = Math.max(c.y1, -p[2]); }
  }
  res.comps = comps.size;
  for (const [r, c] of comps) {
    if (c.n > 4000) continue;
    const i = Math.floor(c.mx - X0), j = Math.floor(c.my - Y0); if (i < 0 || j < 0 || i >= N || j >= N) continue;
    const sup = (hits[j * N + i] ?? []).filter((q) => q.up && q.comp !== r && q.y <= c.minY + 0.3).reduce((m, q) => Math.max(m, q.y), -1e9);
    const gnd = T.ground(c.mx, c.my), base = sup > -1e8 ? sup : gnd, fl = c.minY - base;
    const size = Math.max(c.x1 - c.x0, c.y1 - c.y0), hgt = c.maxY - c.minY;
    const cxm = (c.x0 + c.x1) / 2, cym = (c.y0 + c.y1) / 2; let att = false;
    for (let a = 0; a < 16 && !att; a++) for (const rr of [1.2, 2.5]) if (T.colliders.inside(cxm + Math.cos(a * 0.3927) * (size / 2 + rr), cym + Math.sin(a * 0.3927) * (size / 2 + rr)) || T.colliders.inside(cxm, cym)) att = true;
    if (fl > 0.6 && att) { res.attached = (res.attached ?? 0) + 1; continue; }
    if (fl > 0.6 && T.inPlay(c.mx, c.my)) add(T.bridges.heightAt(c.mx, c.my, c.minY, 60) != null ? 'floating_over_deck' : 'floating_component', (c.x0 + c.x1) / 2, (c.y0 + c.y1) / 2, { n: c.n, above: +fl.toFixed(1), size: +size.toFixed(1), hgt: +hgt.toFixed(1), z: +c.minY.toFixed(1) });
    else if (fl < -0.8 && c.maxY < gnd - 0.3 && c.n >= 2) add('buried_component', c.mx, c.my, { n: c.n, below: +(-fl).toFixed(1), hgt: +hgt.toFixed(1) });
  }
  return res;
};

const landmarkCheck = () => {
  const T = window.sbxTiles, V = window.sbxCamera.position.constructor, out = [];
  window.sbxScene.traverse((o) => {
    if (!o.name?.startsWith('landmark:') || o.userData.__swept) return;
    o.userData.__swept = true; o.updateMatrixWorld(true);
    let minY = 1e9, pts = [], v = new V();
    o.traverse((m) => { if (!m.isMesh) return; const pos = m.geometry.attributes.position; for (let i = 0; i < pos.count; i += 2) { v.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld); pts.push([v.x, v.y, -v.z]); if (v.y < minY) minY = v.y; } });
    if (!pts.length) return;
    const low = pts.filter((p) => p[1] < minY + 1.5), gs = low.map((p) => T.ground(p[0], p[1]));
    const gmin = Math.min(...gs), gmax = Math.max(...gs), avg = gs.reduce((s, q) => s + q, 0) / gs.length;
    const onRoad = low.filter((p) => T.onRoad(p[0], p[1])).length;
    const cx = low.reduce((s, p) => s + p[0], 0) / low.length, cy = low.reduce((s, p) => s + p[1], 0) / low.length;
    out.push({ name: o.name.slice(9), x: +cx.toFixed(1), y: +cy.toFixed(1), minY: +minY.toFixed(2), gmin: +gmin.toFixed(2), gmax: +gmax.toFixed(2), floatAbove: +(minY - gmin).toFixed(2), sunk: +(gmax - minY).toFixed(2), roadFrac: +(onRoad / low.length).toFixed(2), nLow: low.length });
  });
  return out;
};

const actors = () => {
  const T = window.sbxTiles, out = [];
  for (const p of window.sbxCrowd.peds ?? []) if (p.x != null && T.colliders.inside(p.x, p.y)) out.push({ type: 'npc_in_building', x: +p.x.toFixed(1), y: +p.y.toFixed(1) });
  for (const a of window.sbxTraffic.agents ?? []) if (a.alive && T.colliders.inside(a.x, a.y)) out.push({ type: 'traffic_in_building', x: +a.x.toFixed(1), y: +a.y.toFixed(1), kind: a.kind });
  for (const p of window.sbxParked?.slots ?? []) if (p.x != null && T.colliders.inside(p.x, p.y)) out.push({ type: 'parked_in_building', x: +p.x.toFixed(1), y: +p.y.toFixed(1) });
  return out;
};

const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });
const p = await (await b.newContext({ viewport: { width: 640, height: 360 } })).newPage();
const errs = [];
p.on('pageerror', (e) => errs.push('pageerror ' + e.message.slice(0, 150)));
p.on('console', (m) => { if (m.type() === 'warning' && /tile failed/.test(m.text())) errs.push(m.text().slice(0, 150)); });
p.on('response', (r) => { if (r.status() >= 400) errs.push(r.status() + ' ' + r.url().slice(0, 100)); });
await p.goto(`${BASE}/?at=0,0,0&t=12:00&nopost`);
await p.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
const tiles = await p.evaluate(() => window.sbxTiles.world.tiles.map((t) => ({ name: t.name, ix: t.ix, iy: t.iy, s: window.sbxTiles.world.tile })));
const results = [], lms = [], act = [];
let n = 0;
for (const t of tiles) {
  if (FILTER && !FILTER.test(t.name)) continue;
  const cx = (t.ix + 0.5) * t.s, cy = (t.iy + 0.5) * t.s;
  try {
    await p.evaluate(async ([x, y]) => { window.sbxPlayer.teleport(x, y, 0); await window.sbxTiles.update(x, y); }, [cx, cy]);
    await p.waitForTimeout(1200);
    const r = await p.evaluate(analyse, t.name);
    results.push(r);
    lms.push(...(await p.evaluate(landmarkCheck)));
    act.push(...(await p.evaluate(actors)).map((a) => ({ ...a, tile: t.name })));
    n++;
    if (n % 20 === 0) { console.log(n, '/', tiles.length, t.name, r.issues?.length); writeFileSync(OUT, JSON.stringify({ results, lms, act, errs }, null, 0)); }
  } catch (e) { console.log('ERR', t.name, e.message.slice(0, 200)); results.push({ name: t.name, error: e.message.slice(0, 200), issues: [] }); }
}
writeFileSync(OUT, JSON.stringify({ results, lms, act, errs }, null, 0));
console.log('done', n, 'tiles; issues', results.reduce((s, r) => s + r.issues.length, 0), 'landmarks', lms.length, 'actors', act.length, 'errs', errs.length);
await b.close();
