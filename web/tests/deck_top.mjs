// Top-down deck check, rendering half of pipeline/scopes/topcheck.py. For each job box (game metres, north up, orthographic):
//   <out>/<id>_photo.png  the game from above (noon, no fog, player hidden), 2 px per grid cell
//   <out>/<id>.bin        Float32 planes, W x H each, row 0 = north, NaN = nothing there:
//     deck   height of the drawn road / tram / foot deck surface (bridge rows rebuilt without piers, parapets, undersides, railings)
//     rail   the same for rail decks (not walkable)
//     glb    height of the tile mesh (terrain, buildings, streets) seen from above
//     walk   walkable deck height at the drawn (or the nearest drawn, <= 4 m) deck height: BridgeIndex.heightAt, what the body uses
//     feet   height the body stands at there (Tiles.groundAt: deck, terrain or the blend at ramp feet)
//     ground terrain height (Tiles.ground)
//     push   metres a 0.35 m body standing on the drawn deck is pushed (railings, footprints): > 0 = something solid there
//   <out>/<id>.json       { W, H, res, box, planes, missing (tiles not loaded) }
//   node tests/deck_top.mjs <jobs.json> <out-dir> [base-url=http://localhost:5190]
//   jobs.json: [{ "id": "gerold_0", "box": [x0, y0, x1, y1], "res": 0.5 }, ...]  (boxes up to ~300 m: tiles load 450 m around)
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const [,, jobsFile, out, BASE = 'http://localhost:5190'] = process.argv;
const jobs = JSON.parse(fs.readFileSync(jobsFile, 'utf8'));
fs.mkdirSync(out, { recursive: true });
const b = await chromium.launch({ args: ['--use-gl=angle', '--ignore-gpu-blocklist'] });

for (const job of jobs) {
  const [x0, y0, x1, y1] = job.box, res = job.res ?? 0.5, cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
  const p = await (await b.newContext({ viewport: { width: 1000, height: 800 } })).newPage();
  p.on('pageerror', (e) => console.error(job.id, 'pageerror', e.message));
  await p.goto(`${BASE}/?at=${cx.toFixed(1)},${cy.toFixed(1)},0&t=12:00`);
  await p.waitForFunction(() => window.sbxReady, null, { timeout: 120000 });
  // every tile the box touches must be in (world.json lists the existing ones)
  const missing = await p.evaluate(async ([x0, y0, x1, y1]) => {
    const T = window.sbxTiles, s = T.world.tile;
    const want = T.world.tiles.filter((t) => (t.ix + 1) * s > x0 && t.ix * s < x1 && (t.iy + 1) * s > y0 && t.iy * s < y1).map((t) => t.name);
    for (let k = 0; k < 90 && want.some((n) => !T.loaded.has(n)); k++) await new Promise((r) => setTimeout(r, 500));
    return want.filter((n) => !T.loaded.has(n));
  }, job.box);
  await p.waitForTimeout(3000);
  const r = await p.evaluate(async ([x0, y0, x1, y1, res]) => {
    const url = (re) => performance.getEntriesByType('resource').map((e) => e.name).find((n) => re.test(n));
    const THREE = await import(url(/\/node_modules\/\.vite\/deps\/three\.js/));
    const BR = await import(url(/\/src\/world\/bridges\.ts/) ?? '/src/world/bridges.ts');
    const { sbxRenderer: R, sbxScene: S, sbxTiles: T, sbxPlayer: P } = window;
    const W = Math.round((x1 - x0) / res), H = Math.round((y1 - y0) / res), N = W * H;
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, CH = 2000;
    const cam = new THREE.OrthographicCamera(-(x1 - x0) / 2, (x1 - x0) / 2, (y1 - y0) / 2, -(y1 - y0) / 2, 1, CH + 1000);
    cam.position.set(cx, CH, -cy); cam.up.set(0, 0, -1); cam.lookAt(cx, 0, -cy); cam.updateMatrixWorld(); cam.updateProjectionMatrix();

    // photo
    P.mesh.visible = false; T.cull(cx, cy, 2000);
    const fog = S.fog; S.fog = null;
    const size = new THREE.Vector2(); R.getSize(size); const pr = R.getPixelRatio();
    R.setPixelRatio(1); R.setSize(2 * W, 2 * H, false); R.render(S, cam);   // the game may run below pixel ratio 1
    const photo = R.domElement.toDataURL('image/png');
    S.fog = fog;

    // height passes: world height packed into RGB (mm + 1000 m offset, 24 bit), alpha = covered
    const hmat = new THREE.ShaderMaterial({
      side: THREE.DoubleSide,
      vertexShader: 'varying float vY; void main() { vec4 w = modelMatrix * vec4(position, 1.0); vY = w.y; gl_Position = projectionMatrix * viewMatrix * w; }',
      fragmentShader: 'varying float vY; void main() { float v = floor((vY + 1000.0) * 1000.0 + 0.5); float r = floor(v / 65536.0); float g = floor((v - r * 65536.0) / 256.0); float b = v - r * 65536.0 - g * 256.0; gl_FragColor = vec4(r / 255.0, g / 255.0, b / 255.0, 1.0); }',
    });
    const rt = new THREE.WebGLRenderTarget(W, H, { minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter, type: THREE.UnsignedByteType, depthBuffer: true });
    const pass = (meshes) => {
      const sc = new THREE.Scene();
      for (const m of meshes) sc.add(m);
      R.setRenderTarget(rt); R.setClearColor(0x000000, 0); R.clear(); R.render(sc, cam); R.setRenderTarget(null);
      const px = new Uint8Array(N * 4); R.readRenderTargetPixels(rt, 0, 0, W, H, px);
      const h = new Float32Array(N).fill(NaN);
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {   // GL row 0 = south; out row 0 = north
        const i = (y * W + x) * 4;
        if (px[i + 3] === 0) continue;
        h[(H - 1 - y) * W + x] = (px[i] * 65536 + px[i + 1] * 256 + px[i + 2]) / 1000 - 1000;
      }
      return h;
    };
    const proxy = (src, geo) => { const m = new THREE.Mesh(geo ?? src.geometry, hmat); m.applyMatrix4(src.matrixWorld); m.frustumCulled = false; return m; };
    const glbMeshes = [], deckMeshes = [], railMeshes = [];
    const SKIP = [0x9b988f, 0x6f6d68, 0x5d6468].map((h) => new THREE.Color(h));   // parapet/curb, underside/piers, railings
    for (const [name, g] of T.loaded) {
      if (!g) continue;   // tile still loading (placeholder)
      g.updateMatrixWorld(true);
      let host = null;
      g.traverse((o) => { if (o.isMesh && !o.isInstancedMesh && /^mesh_/.test(o.name)) glbMeshes.push(proxy(o)); if (o.name === 'bridges' && o.isMesh) host = o; });
      const rows = T.bridges.owners?.get(name);
      if (!rows?.decks?.length) continue;
      for (const [list, decks] of [[deckMeshes, rows.decks.filter((d) => d.kind !== 'rail')], [railMeshes, rows.decks.filter((d) => d.kind === 'rail')]]) {
        const built = decks.length ? BR.buildBridges({ decks, piers: [] })[0] : null;
        if (!built) continue;
        const src = built.geometry, P3 = src.attributes.position, Nn = src.attributes.normal, C = src.attributes.color, keep = [];
        for (let t = 0; t < P3.count; t += 3) {
          if (Math.abs(Nn.getY(t)) < 0.5) continue;   // walls, parapet faces, railing strips
          const c = [C.getX(t), C.getY(t), C.getZ(t)];
          if (SKIP.some((k) => Math.abs(k.r - c[0]) + Math.abs(k.g - c[1]) + Math.abs(k.b - c[2]) < 2e-3)) continue;
          for (let v = t; v < t + 3; v++) keep.push(P3.getX(v), P3.getY(v), P3.getZ(v));
        }
        const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(keep, 3));
        list.push(proxy(host ?? new THREE.Object3D(), geo));
      }
    }
    const deck = pass(deckMeshes), rail = pass(railMeshes), glb = pass(glbMeshes);
    R.setPixelRatio(pr); R.setSize(size.x, size.y, false);

    // physics at every cell: walkable deck at the drawn height (holes: nearest drawn height within 4 m as the hint)
    const hint = Float32Array.from(deck), q = [];
    for (let i = 0; i < N; i++) if (!Number.isNaN(hint[i])) q.push(i);
    for (let step = 0, lim = Math.round(4 / res); step < lim && q.length; step++) {
      const nxt = [];
      for (const i of q) {
        const x = i % W, y = (i - x) / W;
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const u = x + dx, v = y + dy, j = v * W + u;
          if (u < 0 || v < 0 || u >= W || v >= H || !Number.isNaN(hint[j])) continue;
          hint[j] = hint[i]; nxt.push(j);
        }
      }
      q.length = 0; q.push(...nxt);
    }
    const walk = new Float32Array(N).fill(NaN), feet = new Float32Array(N).fill(NaN), ground = new Float32Array(N), push = new Float32Array(N).fill(NaN);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const i = y * W + x, wx = x0 + (x + 0.5) * res, wy = y1 - (y + 0.5) * res;
      ground[i] = T.ground(wx, wy);
      const z = hint[i];
      if (Number.isNaN(z)) continue;
      const d = T.bridges.heightAt(wx, wy, z, 1.0, 1.0);
      if (d !== null) walk[i] = d;
      feet[i] = T.groundAt(wx, wy, z);
      if (!Number.isNaN(deck[i])) { const [px, py] = T.resolveBody(wx, wy, 0.35, feet[i]); push[i] = Math.hypot(px - wx, py - wy); }
    }
    const b64 = (arrs) => {
      const all = new Uint8Array(arrs.reduce((s, a) => s + a.byteLength, 0));
      let o = 0; for (const a of arrs) { all.set(new Uint8Array(a.buffer), o); o += a.byteLength; }
      let s = ''; for (let k = 0; k < all.length; k += 0x8000) s += String.fromCharCode.apply(null, all.subarray(k, k + 0x8000));
      return btoa(s);
    };
    return { W, H, photo, bin: b64([deck, rail, glb, walk, feet, ground, push]), nDeck: deckMeshes.length, nGlb: glbMeshes.length };
  }, [x0, y0, x1, y1, res]);
  fs.writeFileSync(path.join(out, `${job.id}_photo.png`), Buffer.from(r.photo.split(',')[1], 'base64'));
  fs.writeFileSync(path.join(out, `${job.id}.bin`), Buffer.from(r.bin, 'base64'));
  fs.writeFileSync(path.join(out, `${job.id}.json`), JSON.stringify({ W: r.W, H: r.H, res, box: job.box, planes: ['deck', 'rail', 'glb', 'walk', 'feet', 'ground', 'push'], missing, nDeck: r.nDeck, nGlb: r.nGlb }));
  console.log(`${job.id}: ${r.W}x${r.H}, ${r.nDeck} deck tiles, ${r.nGlb} tile meshes${missing.length ? `, MISSING ${missing.join(' ')}` : ''}`);
  await p.context().close();
}
await b.close();
