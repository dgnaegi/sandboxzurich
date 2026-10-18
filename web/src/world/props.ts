import * as THREE from 'three';
import type { KnockRec } from './knockable';
import { registerLights } from './night_lights';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { CAR_GEO, carMaterial, carPick } from './cars';
import { parkedCars } from './parkedcars';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { glowMaterialPatch } from '../engine/daytime';
import { nightUniform } from '../engine/materials';
import { mopedGeo } from './mopeds';
import { catalogFountainNear } from './catalog';


/**
 * Per-tile props. Street furniture of a tile is merged into ONE vertex-coloured mesh (1 draw call);
 * cars are instanced per model; trees per class. Rows are local metres [x, y, z, heading, ...].
 */
export interface PropMeta {
  trees: number[][]; cars: number[][]; lamps: number[][]; masts: number[][]; benches: number[][];
  fountains: number[][]; bins: number[][]; bikes: number[][]; racks?: number[][]; wires: number[][][];
}

const C = (h: number) => new THREE.Color(h);
const COL = { metal: C(0x6d7377), pole: C(0x4f585c), glow: C(0xfff3c8), stone: C(0x9a968c), water: C(0x3f6f8a),
  wood: C(0x8a5a32), bin: C(0x2f5a3a), dark: C(0x1d2226), cable: C(0x2a2a2a) };

function part(g: THREE.BufferGeometry, c: THREE.Color): THREE.BufferGeometry {
  g = g.index ? g.toNonIndexed() : g;
  for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal') g.deleteAttribute(k);
  const n = g.getAttribute('position').count, a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) a.set([c.r, c.g, c.b], i * 3);
  g.setAttribute('color', new THREE.BufferAttribute(a, 3));
  return g;
}
const box = (w: number, h: number, d: number, x: number, y: number, z: number, c: THREE.Color) => part(new THREE.BoxGeometry(w, h, d).translate(x, y, z), c);
const cyl = (r0: number, r1: number, h: number, x: number, y: number, z: number, c: THREE.Color, n = 8) => part(new THREE.CylinderGeometry(r0, r1, h, n).translate(x, y, z), c);
const merge = (g: THREE.BufferGeometry[]) => mergeGeometries(g)!;

const T: Record<string, THREE.BufferGeometry> = {
  lamp: merge([box(0.7, 0.18, 0.45, 0, 7.4, 0, COL.metal), box(0.5, 0.04, 0.3, 0, 7.3, 0, COL.glow)]),
  cable: box(1, 0.025, 0.025, 0, 7.6, 0, COL.cable),
  mast: merge([cyl(0.07, 0.1, 7, 0, 3.5, 0, COL.pole), box(0.06, 0.06, 1.4, 0, 6.95, -0.7, COL.pole),
    box(0.35, 0.12, 0.6, 0, 6.9, -1.4, COL.pole), box(0.28, 0.03, 0.5, 0, 6.83, -1.4, COL.glow)]),
  bench: merge([box(1.8, 0.06, 0.45, 0, 0.45, 0, COL.wood), box(1.8, 0.4, 0.06, 0, 0.72, 0.22, COL.wood),
    box(0.06, 0.45, 0.4, -0.8, 0.22, 0, COL.dark), box(0.06, 0.45, 0.4, 0.8, 0.22, 0, COL.dark)]),
  fountain: merge([box(2.2, 0.75, 1.0, 0, 0.375, 0, COL.stone), cyl(0.18, 0.22, 1.7, 0, 0.85, 0.65, COL.stone),
    box(0.08, 0.08, 0.35, 0, 1.4, 0.45, COL.metal), box(2.0, 0.02, 0.8, 0, 0.68, 0, COL.water)]),
  // Zürich Anlehnbügel (galvanised inverted U), oriented across the bike row
  rack: merge([cyl(0.025, 0.025, 0.8, -0.35, 0.4, 0, C(0xb8bcc0), 6), cyl(0.025, 0.025, 0.8, 0.35, 0.4, 0, C(0xb8bcc0), 6),
    part(new THREE.BoxGeometry(0.75, 0.05, 0.05).translate(0, 0.8, 0), C(0xb8bcc0))]),
  // bistro set: round table + 4 chairs (Zürich café terrace)
  terrace: merge([cyl(0.36, 0.36, 0.03, 0, 0.74, 0, C(0xd9d6cf), 14), cyl(0.03, 0.03, 0.72, 0, 0.36, 0, C(0x3a3d40), 6),
    ...[[0.65, 0], [-0.65, 0], [0, 0.65], [0, -0.65]].flatMap(([x, z]) => [box(0.42, 0.04, 0.42, x, 0.46, z, C(0x2f3336)),
      box(0.42, 0.42, 0.04, x * 1.3, 0.7, z * 1.3 + (x === 0 ? 0 : 0), C(0x2f3336)), box(0.04, 0.46, 0.04, x, 0.23, z, C(0x2f3336))])]),
  parasol: merge([cyl(0.025, 0.025, 2.3, 0, 1.15, 0, C(0xd8d8d8), 6), part(new THREE.ConeGeometry(1.4, 0.45, 8).translate(0, 2.35, 0), C(0xf0ece2))]),
  bin: merge([cyl(0.22, 0.2, 0.85, 0, 0.6, 0, COL.bin, 10), cyl(0.04, 0.04, 0.6, 0, 0.3, 0, COL.dark)]),
};

/** Blender-built Zürich furniture (pipeline/furniture); replaces the box placeholders above when loaded. */
export async function loadFurniture(base = '/models/furniture') {
  const list = (await (await fetch(`${base}/manifest.json`)).json()) as { name: string; file: string }[];
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const F: Record<string, THREE.BufferGeometry> = {};
  await Promise.all(list.map(async (e) => {
    const g = await loader.loadAsync(`${base}/${e.file}`);
    g.scene.updateMatrixWorld(true);
    g.scene.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      let geo = m.geometry.clone().applyMatrix4(m.matrixWorld);
      geo = geo.index ? geo.toNonIndexed() : geo;
      const n = geo.getAttribute('position').count, src = geo.getAttribute('color'), lin = new Float32Array(n * 3), c = new THREE.Color();
      for (let i = 0; i < n; i++) { // vertex colours were exported as sRGB bytes
        c.setRGB(src ? src.getX(i) : 1, src ? src.getY(i) : 1, src ? src.getZ(i) : 1, THREE.SRGBColorSpace);
        lin.set([c.r, c.g, c.b], i * 3);
      }
      const out = new THREE.BufferGeometry();
      out.setAttribute('position', new THREE.Float32BufferAttribute(Array.from(geo.getAttribute('position').array as ArrayLike<number>), 3));
      out.setAttribute('normal', new THREE.Float32BufferAttribute(Array.from(geo.getAttribute('normal').array as ArrayLike<number>), 3));
      out.setAttribute('color', new THREE.BufferAttribute(lin, 3));
      F[e.name] = out;
    });
  }));
  // cable lamps hang from the span wire (origin = suspension point, model hangs down)
  if (F.lamp_cable) T.lamp = F.lamp_cable.clone().translate(0, 7.6, 0);
  if (F.lamp_mast) T.mast = F.lamp_mast;
  if (F.bench_slat) T.bench = F.bench_slat;
  if (F.bench_metal) T.bench2 = F.bench_metal;
  if (F.bin) T.bin = F.bin;
  for (const k of ['bin_ash', 'bin_hai', 'bin_robidog', 'bench_cast', 'bench_flat', 'bench_table']) if (F[k]) T[k] = F[k];
  if (F.fountain_trough) T.fountain = F.fountain_trough;
  if (F.fountain_round) T.fountain2 = F.fountain_round;
  if (F.fountain_drink) T.fountain3 = F.fountain_drink;
  if (F.hydrant) T.hydrant = F.hydrant;
  if (F.pingpong) T.pingpong = F.pingpong;
  if (F.bollard) T.bollard = F.bollard;
}

const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), s = new THREE.Vector3(), Y = new THREE.Vector3(0, 1, 0);
// light pools under street lamps: additive radial quads, only visible at night (nightUniform)
const poolTex = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d')!, r = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  r.addColorStop(0, 'rgba(255,214,150,1)'); r.addColorStop(0.45, 'rgba(255,190,120,0.45)'); r.addColorStop(1, 'rgba(255,170,100,0)');
  g.fillStyle = r; g.fillRect(0, 0, 128, 128);
  return new THREE.CanvasTexture(c);
})();
const poolMat = new THREE.MeshBasicMaterial({ map: poolTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: true,
  polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 });
poolMat.onBeforeCompile = (sh) => {
  sh.uniforms.night = nightUniform;
  sh.fragmentShader = sh.fragmentShader.replace('void main() {', 'uniform float night;\nvoid main() {')
    .replace('#include <map_fragment>', '#include <map_fragment>\ndiffuseColor.rgb *= 0.75 * night;');
};
const poolGeo = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);

const furnitureMat = new THREE.MeshLambertMaterial({ vertexColors: true });
glowMaterialPatch(furnitureMat); // lamps glow at night

export function buildProps(meta: PropMeta, shadows: boolean): THREE.Object3D[] {
  const out: THREE.Object3D[] = [];
  const { cars = [], lamps = [], masts = [], benches = [], fountains = [], bins = [], wires = [] } = meta;

  // street furniture -> one merged mesh
  const parts: THREE.BufferGeometry[] = [];
  const place = (tpl: THREE.BufferGeometry, x: number, y: number, z: number, rot: number, sx = 1) =>
    parts.push(tpl.clone().applyMatrix4(m4.compose(p.set(x, z, -y), q.setFromAxisAngle(Y, rot), s.set(sx, 1, 1))));
  for (const r of lamps) { place(T.lamp, r[0], r[1], r[2], -r[3]); place(T.cable, r[0], r[1], r[2], -r[3], r[4]); }
  for (const r of masts) place(T.mast, r[0], r[1], r[2], -r[3]);
  // bench type from Sitzbankkataster (r[4]): 0 back-rest, 1 none, 2 table-bench, 3 "046" modern, 4 table, 5 other; old tiles: no r[4]
  for (const r of benches) {
    const t = r[4], h = Math.abs(r[0] * 13 + r[1]) % 3 < 1;
    const tpl = t === 1 ? T.bench_flat : t === 2 || t === 4 ? T.bench_table : t === 3 ? T.bench : t === 0 ? (h ? T.bench_cast : T.bench2) : undefined;
    place(tpl || (h && T.bench2) || T.bench, r[0], r[1], r[2], -r[3] + Math.PI / 2);
  }
  for (const r of fountains) { if (catalogFountainNear(r[0], r[1])) continue; const k = Math.floor(Math.abs(r[0] * 7 + r[1] * 3)) % 4; place((k === 1 && T.fountain2) || (k === 2 && T.fountain3) || T.fountain, r[0], r[1], r[2], -r[3]); }
  // bin type (r[4] = type*2 + ashtray): 0 Zueri-Kuebel, 1 Abfallhai, 2 Robidog, 3 other
  const knocks: { part: number; rec: KnockRec }[] = [];   // knock-over objects: part index in `parts` -> record (vertex ranges are filled after the merge)
  const knockable = (r: number[], rad: number, kind: 1 | 2, type: KnockRec['type']) => knocks.push({ part: parts.length, rec: { x: r[0], y: r[1], z: r[2], r: rad, kind, type, ranges: [] } });
  for (const r of bins) {
    const t = r[4] === undefined ? 0 : r[4] >> 1, ash = (r[4] ?? 0) & 1;
    knockable(r, 0.3, 1, 'bin');
    place((t === 1 && T.bin_hai) || (t === 2 && T.bin_robidog) || (ash && T.bin_ash) || T.bin, r[0], r[1], r[2], -r[3] + Math.PI);
  }
  for (const r of meta.racks ?? []) { knockable(r, 0.35, 2, 'flat'); place(T.rack, r[0], r[1], r[2], -r[3] + Math.PI / 2); }
  for (const r of (meta as unknown as { mopeds?: number[][] }).mopeds ?? []) place(mopedGeo(r[4]), r[0], r[1], r[2], -r[3]);
  for (const r of (meta as unknown as { terraces?: number[][] }).terraces ?? []) {
    place(T.terrace, r[0], r[1], r[2], -r[3]);
    if (r[4]) place(T.parasol, r[0], r[1], r[2], 0);
  }
  const extra = meta as unknown as { hydrants?: number[][]; bollards?: number[][]; pingpong?: number[][] };
  for (const [key, tpl] of [['hydrants', 'hydrant'], ['bollards', 'bollard'], ['pingpong', 'pingpong']] as const)
    if (T[tpl]) for (const r of extra[key] ?? []) { if (key === 'bollards') knockable(r, 0.15, 2, 'pole'); place(T[tpl], r[0], r[1], r[2], r[3]); }
  const lampPts: number[] = [];
  for (const r of lamps) lampPts.push(r[0], r[2] + 7.0, -r[1], 17, 1.7, 1.05, 0.5);
  for (const r of masts) lampPts.push(r[0] - Math.sin(r[3]) * 1.4, r[2] + 7.0, -(r[1] - Math.cos(r[3]) * 1.4), 17, 1.7, 1.05, 0.5);
  if (lampPts.length) { const owner = new THREE.Object3D(); registerLights(owner, lampPts); out.push(owner); }
  const pools = [...lamps.map((r) => [r[0], r[1], r[2] - 0.1, 11]), ...masts.map((r) => [r[0] - Math.sin(r[3]) * 1.4, r[1] - Math.cos(r[3]) * 1.4, r[2], 9])];
  if (pools.length) {
    const im = new THREE.InstancedMesh(poolGeo, poolMat, pools.length);
    pools.forEach(([x, y, z, size], i) => im.setMatrixAt(i, m4.compose(p.set(x, z + 0.03, -y), q.identity(), s.set(size, 1, size))));
    im.computeBoundingSphere();
    im.renderOrder = 2;
    out.push(im);
  }
  if (parts.length) {
    const mesh = new THREE.Mesh(merge(parts), furnitureMat);
    mesh.castShadow = shadows;
    if (knocks.length) { // vertex / index offset of every part inside the merged geometry
      const v: number[] = [], ix: number[] = []; let a = 0, b = 0;
      for (const g of parts) { v.push(a); ix.push(b); a += g.getAttribute('position').count; b += g.index?.count ?? 0; }
      mesh.userData.knock = knocks.map(({ part, rec }) => {
        const g = parts[part];
        rec.ranges.push({ v0: v[part], vn: g.getAttribute('position').count, i0: g.index ? ix[part] : undefined, in: g.index?.count, mesh });
        return rec;
      });
    }
    out.push(mesh);
  }

  // parked cars: one InstancedMesh per model + a box stand-in for distant tiles (Tiles.cull swaps them)
  const byType = new Map<string, number[][]>();
  for (const r of cars) { const t = carPick(r[4]).type; if (CAR_GEO[t]) (byType.get(t) ?? byType.set(t, []).get(t)!).push(r); }
  for (const [t, rows] of byType) {
    const im = new THREE.InstancedMesh(CAR_GEO[t], carMaterial, rows.length);
    rows.forEach((r, i) => {
      im.setMatrixAt(i, m4.compose(p.set(r[0], r[2], -r[1]), q.setFromAxisAngle(Y, -r[3]), s.set(1, 1, 1)));
      im.setColorAt(i, carPick(r[4]).color);
      parkedCars.add({ mesh: im, i, x: r[0], y: r[1], z: r[2], h: r[3], type: t, color: carPick(r[4]).color, taken: false });
    });
    im.castShadow = shadows;
    im.computeBoundingSphere();
    const lo = new THREE.InstancedMesh(carLo(t), carMaterial, rows.length);
    lo.instanceMatrix = im.instanceMatrix; lo.instanceColor = im.instanceColor;
    lo.computeBoundingSphere();
    lo.visible = false;
    im.userData.lo = lo;
    out.push(im, lo);
  }

  if (wires.length) {
    const pos: number[] = [];
    for (const w of wires) for (let i = 0; i + 1 < w.length; i++) pos.push(w[i][0], w[i][2], -w[i][1], w[i + 1][0], w[i + 1][2], -w[i + 1][1]);
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    out.push(new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x222222 })));
  }
  return out;
}

/** ~60-triangle car: painted body, dark glass cabin, black wheels; sized from the detailed model's bounds. */
const CAR_LO: Record<string, THREE.BufferGeometry> = {};
function carLo(t: string): THREE.BufferGeometry {
  if (CAR_LO[t]) return CAR_LO[t];
  const ref = CAR_GEO[t];
  ref.computeBoundingBox();
  const bb = ref.boundingBox!, c = new THREE.Vector3();
  bb.getCenter(c);
  const alongX = bb.max.x - bb.min.x >= bb.max.z - bb.min.z;
  const L = alongX ? bb.max.x - bb.min.x : bb.max.z - bb.min.z, W = alongX ? bb.max.z - bb.min.z : bb.max.x - bb.min.x;
  const H = bb.max.y - bb.min.y, y0 = bb.min.y;
  const tag = (g: THREE.BufferGeometry, col: number, paint: number) => {
    g = g.toNonIndexed();
    for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal') g.deleteAttribute(k);
    const n = g.getAttribute('position').count, cc = new THREE.Color(col);
    g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(n * 3).map((_, i) => [cc.r, cc.g, cc.b][i % 3]), 3));
    g.setAttribute('_paint', new THREE.BufferAttribute(new Float32Array(n).fill(paint), 1));
    return g;
  };
  const box = (l: number, h: number, w: number, x: number, y: number, z: number, col: number, paint: number) => {
    const g = new THREE.BoxGeometry(l, h, w); g.translate(x, y, z); return tag(g, col, paint);
  };
  const r = Math.min(0.34, H * 0.24), body = H * 0.5;
  const parts = [
    box(L, body - r * 0.6, W, 0, y0 + r * 0.6 + (body - r * 0.6) / 2, 0, 0xffffff, 1),
    box(L * 0.52, H - body, W * 0.86, -L * 0.04, y0 + body + (H - body) / 2, 0, 0x22262c, 0),
  ];
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) parts.push(box(r * 1.9, r * 1.9, 0.22, sx * (L / 2 - r * 1.7), y0 + r, sz * (W / 2 - 0.1), 0x111111, 0));
  let g = mergeGeometries(parts)!;
  if (!alongX) g = g.rotateY(Math.PI / 2);
  g.translate(c.x, 0, c.z);
  return (CAR_LO[t] = g);
}
