import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import type { Human, Model, Role } from './humans';

/**
 * Procedural clothing / head kit for pedestrians (no download): glasses, beard, beanie, cap, helmet, headphones, hood, quilted gilet, hi-vis vest.
 * Everything a person wears on the head is ONE merged mesh on the head bone, everything on the torso ONE mesh on spine_02 (2 draw calls at most),
 * geometry is cached per recipe and shared. Authoring frame = root-aligned axes (y up, front = -z) with the origin at the bone's rest position;
 * `anchor` maps that frame into the (mirrored) bone frame and scales it to the figure.
 */
export interface Kit { head?: string[]; torso?: string; hex?: Record<string, number> }
interface Dims { hw: number; top: number; front: number; q: THREE.Quaternion; qs: THREE.Quaternion; tw: number; td: number; ty: number; tcz: number; headP: THREE.Vector3; s2P: THREE.Vector3 }

const dims = new WeakMap<Model, Dims>();
const geoCache = new Map<string, THREE.BufferGeometry>();
(globalThis as { __kitCache?: unknown }).__kitCache = geoCache;
let material: THREE.MeshStandardMaterial | undefined;
const STD = { hw: 0.088, top: 0.15, front: 0.118 };       // standard head (relative to the head joint) the recipes are authored for

/** Rest-pose measurements of a model (head size, torso width), once. */
export function measure(m: Model): Dims | null {
  const hit = dims.get(m);
  if (hit) return hit;
  m.scene.updateMatrixWorld(true);
  const head = m.scene.getObjectByName('head'), s2 = m.scene.getObjectByName('spine_02'), neck = m.scene.getObjectByName('neck_01');
  let sm: THREE.SkinnedMesh | undefined;
  m.scene.traverse((o) => { if ((o as THREE.SkinnedMesh).isSkinnedMesh && !sm) sm = o as THREE.SkinnedMesh; });
  if (!head || !s2 || !neck || !sm) return null;
  const hp = new THREE.Vector3().setFromMatrixPosition(head.matrixWorld), sp = new THREE.Vector3().setFromMatrixPosition(s2.matrixWorld), np = new THREE.Vector3().setFromMatrixPosition(neck.matrixWorld);
  const q = new THREE.Quaternion(), qs = new THREE.Quaternion(); head.matrixWorld.decompose(new THREE.Vector3(), q, new THREE.Vector3()); q.invert(); s2.matrixWorld.decompose(new THREE.Vector3(), qs, new THREE.Vector3()); qs.invert();
  const g = sm.geometry, pos = g.attributes.position, si = g.attributes.skinIndex, sw = g.attributes.skinWeight, names = sm.skeleton.bones.map((b) => b.name), v = new THREE.Vector3();
  sm.skeleton.update();
  let top = -9, front = 9, hw = 0, tw = 0, tz0 = 9, tz1 = -9;
  for (let i = 0; i < pos.count; i++) {
    let wh = 0, wt = 0;
    for (let k = 0; k < 4; k++) { const n = names[si.getComponent(i, k)], w = sw.getComponent(i, k); if (n === 'head') wh += w; else if (n === 'spine_02' || n === 'spine_03') wt += w; }
    if (wh < 0.9 && wt < 0.9) continue;
    sm.applyBoneTransform(i, v.fromBufferAttribute(pos, i)); v.applyMatrix4(sm.matrixWorld);   // skinned rest position as rendered
    if (wh >= 0.9) { top = Math.max(top, v.y); front = Math.min(front, v.z); hw = Math.max(hw, Math.abs(v.x)); }
    else if (v.y > sp.y - 0.05) { tw = Math.max(tw, Math.abs(v.x)); tz0 = Math.min(tz0, v.z); tz1 = Math.max(tz1, v.z); }
  }
  const d: Dims = { hw: hw || STD.hw, top: top - hp.y, front: hp.z - front, q, qs, tw: tw || 0.17, td: tz1 - tz0 > 0.1 ? tz1 - tz0 : 0.25, ty: (np.y - sp.y) / 0.4, tcz: (tz0 + tz1) / 2 - sp.z, headP: hp, s2P: sp };
  dims.set(m, d);
  return d;
}

// ---------------------------------------------------------------- geometry helpers
function paint(g: THREE.BufferGeometry, hex: number, shade = 1): THREE.BufferGeometry {
  const c = new THREE.Color(hex).multiplyScalar(shade), n = g.attributes.position.count, a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { a[i * 3] = c.r; a[i * 3 + 1] = c.g; a[i * 3 + 2] = c.b; }
  g.setAttribute('color', new THREE.BufferAttribute(a, 3)); g.deleteAttribute('uv');
  return g;
}
const box = (w: number, h: number, d: number, x: number, y: number, z: number, hex: number, rot: [number, number, number] = [0, 0, 0]) => {
  const g = new THREE.BoxGeometry(w, h, d); g.rotateX(rot[0]); g.rotateY(rot[1]); g.rotateZ(rot[2]); g.translate(x, y, z); return paint(g, hex);
};
interface Ring { y: number; rx: number; rz: number; cz: number; shade?: number }
/** Elliptic shell through `rings` (angle 0 = front = -z). `skip(x,y,z)` drops quads (armholes, mouth); `arc` limits the angle range (radians, +-). */
function shell(rings: Ring[], seg: number, hex: number, arc = Math.PI, skip?: (x: number, y: number, z: number) => boolean, bandHex?: (y: number) => number | null): THREE.BufferGeometry {
  const pos: number[] = [], col: number[] = [], idx: number[] = [], c = new THREE.Color(), cols = seg + 1;
  rings.forEach((r) => {
    for (let j = 0; j <= seg; j++) {
      const t = -arc + (2 * arc * j) / seg, x = r.rx * Math.sin(t), z = r.cz - r.rz * Math.cos(t);
      pos.push(x, r.y, z); c.set(bandHex?.(r.y) ?? hex).multiplyScalar(r.shade ?? 1); col.push(c.r, c.g, c.b);
    }
  });
  for (let i = 0; i < rings.length - 1; i++) for (let j = 0; j < seg; j++) {
    const a = i * cols + j, b = a + 1, d = a + cols, e = d + 1;
    const mx = (pos[a * 3] + pos[e * 3]) / 2, my = (pos[a * 3 + 1] + pos[e * 3 + 1]) / 2, mz = (pos[a * 3 + 2] + pos[e * 3 + 2]) / 2;
    if (skip?.(mx, my, mz)) continue;
    idx.push(a, d, b, b, d, e);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); g.setIndex(idx); g.computeVertexNormals();
  return g;
}
/** Cranium ellipsoid (centre y .03, radii .093 x .12 x .108) as rings from the rim (tilted down at the back) to the crown. */
function dome(off: number, rimDeg: number, n: number, hex: number, cuff = 0): THREE.BufferGeometry {
  const rings: Ring[] = [];
  for (let i = 0; i < n; i++) {
    const phi = ((rimDeg + (88 - rimDeg) * (i / (n - 1))) * Math.PI) / 180, s = Math.sin(phi), co = Math.cos(phi), w = Math.pow(1 - i / (n - 1), 2) * 0.034;
    rings.push({ y: 0.03 + (0.12 + off) * s - w, rx: (0.093 + off + (i < 2 ? cuff : 0)) * co, rz: (0.108 + off + (i < 2 ? cuff : 0)) * co, cz: -0.008 + w * 0.2, shade: i < 2 && cuff ? 0.82 : 1 });
  }
  return shell(rings, 18, hex);
}
function tube(pts: [number, number, number][], r: number, hex: number, segs = 14, radial = 5): THREE.BufferGeometry {
  const g = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts.map((p) => new THREE.Vector3(...p))), segs, r, radial, false); return paint(g, hex);
}

// ---------------------------------------------------------------- recipes
const GLASS_COL = [0x15161a, 0x15161a, 0x3a2a1c, 0x8a1f2c, 0x2b3a5a, 0xc9c4b8];
function glasses(variant: number, sun: boolean): THREE.BufferGeometry[] {
  const f = GLASS_COL[variant % GLASS_COL.length], y = 0.03, z = -0.11, lw = 0.05, lh = 0.034, t = 0.0045, o: THREE.BufferGeometry[] = [];
  for (const sx of [-1, 1]) {
    const cx = sx * 0.034;
    o.push(box(lw, t, 0.006, cx, y + lh / 2, z, f), box(lw, t, 0.006, cx, y - lh / 2, z, f), box(t, lh, 0.006, cx - lw / 2, y, z, f), box(t, lh, 0.006, cx + lw / 2, y, z, f));
    if (sun) o.push(box(lw, lh, 0.003, cx, y, z + 0.001, 0x101114));
    o.push(box(0.003, 0.003, 0.1, sx * (0.034 + lw / 2 + 0.002), y + 0.012, z + 0.05, f));
  }
  o.push(box(0.014, t, 0.006, 0, y + 0.01, z, f));
  return o;
}
function headphones(hex: number): THREE.BufferGeometry[] {
  const o = [tube([[-0.097, 0.02, 0.0], [-0.094, 0.09, 0.0], [-0.052, 0.16, 0.0], [0, 0.178, 0.0], [0.052, 0.16, 0.0], [0.094, 0.09, 0.0], [0.097, 0.02, 0.0]], 0.0065, hex, 16, 5)];
  for (const sx of [-1, 1]) { const g = new THREE.CylinderGeometry(0.036, 0.036, 0.026, 10); g.rotateZ(Math.PI / 2); g.translate(sx * 0.1, 0.018, 0.002); o.push(paint(g, hex, 0.9)); }
  return o;
}
function beard(hex: number): THREE.BufferGeometry {
  const Y = [-0.004, -0.02, -0.04, -0.058, -0.074, -0.086, -0.093], RX = [0.079, 0.077, 0.07, 0.062, 0.05, 0.032, 0.012], RZ = [0.112, 0.11, 0.104, 0.096, 0.086, 0.07, 0.04], CZ = [-0.004, -0.004, -0.003, 0, 0, 0.002, 0.01];
  const rings: Ring[] = Y.map((y, i) => ({ y, rx: RX[i], rz: RZ[i], cz: CZ[i], shade: 1 - 0.06 * i }));
  return shell(rings, 18, hex, (110 * Math.PI) / 180, (x, y, z) => Math.abs(x) < 0.024 && y < -0.008 && y > -0.034 && z < -0.08);
}
function hood(hex: number): THREE.BufferGeometry {
  const p: [number, number, number][] = [];
  for (let i = 0; i <= 8; i++) { const a = (-105 + (210 * i) / 8) * (Math.PI / 180); p.push([0.112 * Math.sin(a), -0.105 - 0.035 * Math.cos(a), 0.015 + 0.105 * Math.cos(a)]); }
  return tube(p, 0.036, hex, 18, 6);
}
function hat(kind: string, hex: number): THREE.BufferGeometry[] {
  if (kind === 'beanie') { const g = dome(0.012, 8, 8, hex, 0.006); return [g]; }
  const g = dome(kind === 'helmet' ? 0.016 : 0.01, 14, 8, hex);
  if (kind === 'helmet') { const r = new THREE.CylinderGeometry(0.128, 0.128, 0.008, 18); r.scale(1, 1, 1.12); r.translate(0, 0.056, -0.008); return [g, paint(r, hex, 0.92)]; }
  const brim: THREE.BufferGeometry[] = [], n = 6;
  const pts: number[] = [], idx: number[] = [];
  for (let u = 0; u <= n; u++) for (let v = 0; v <= 2; v++) { const a = ((u / n) * 2 - 1) * 0.95, r = 0.118 + v * 0.045; pts.push(r * 0.78 * Math.sin(a), 0.07 - v * 0.012 - 0.012 * Math.abs(a), -0.008 - r * Math.cos(a)); }
  for (let u = 0; u < n; u++) for (let v = 0; v < 2; v++) { const a = u * 3 + v, b = a + 1, d = a + 3, e = d + 1; idx.push(a, d, b, b, d, e); }
  const bg = new THREE.BufferGeometry(); bg.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3)); bg.setIndex(idx); bg.computeVertexNormals(); brim.push(paint(bg, hex, 0.9));
  return [g, ...brim];
}

/** Flat ribbon along a path (width along x), double sided by the material. */
function ribbon(path: [number, number, number][], hw: number, hex: number, shade = 1): THREE.BufferGeometry {
  const pos: number[] = [], idx: number[] = [];
  path.forEach((p, i) => { pos.push(p[0] - hw, p[1], p[2], p[0] + hw, p[1], p[2]); if (i) { const a = (i - 1) * 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); } });
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals(); return paint(g, hex, shade);
}
/** Torso garment in the spine_02 frame: y -0.13 (waist) ... +0.38 (neck base). Sleeveless: a ring up to the armpit plus two shoulder straps. */
function torso(kind: string, hex: number): THREE.BufferGeometry[] {
  const hv = kind === 'hivis', n = hv ? 7 : 12, rings: Ring[] = [], y0 = -0.13, y1 = 0.14;
  for (let i = 0; i < n; i++) {
    const u = i / (n - 1), y = y0 + u * (y1 - y0), q = 0.5 + 0.5 * Math.cos((y * Math.PI * 2) / 0.078), bulge = hv ? 0 : 0.011 * q, sh = hv ? 0.01 : 0.02;
    rings.push({ y, rx: 0.152 + 0.026 * Math.sin(u * Math.PI / 2) + sh + bulge, rz: 0.118 + sh + bulge, cz: -0.047, shade: hv ? 1 : 0.9 + 0.1 * q });
  }
  const band = hv ? (y: number) => (Math.abs(y - 0.0) < 0.02 || Math.abs(y - 0.105) < 0.02 ? 0xb9bcc2 : null) : undefined;
  const o = [shell(rings, 22, hex, Math.PI, undefined, band)];
  const zf = -(0.165 + (hv ? 0.01 : 0.02) + 0.014), zb = 0.071 + (hv ? 0.01 : 0.02) + 0.014;
  for (const sx of [-1, 1]) {   // strap over the shoulder: front chest -> neck base -> back
    const x = sx * 0.1, p: [number, number, number][] = [[x, 0.12, zf], [x, 0.24, zf + 0.006], [x * 0.95, 0.34, zf + 0.04], [x * 0.85, 0.39, -0.047], [x * 0.95, 0.355, zb - 0.045], [x, 0.24, zb - 0.014], [x, 0.12, zb]];
    o.push(ribbon(p, 0.034, hex, 0.95));
  }
  o.push(ribbon([[0, 0.12, zf], [0, 0.22, zf + 0.004], [0, 0.29, zf + 0.026]], 0.085, hex, 0.93), ribbon([[0, 0.12, zb], [0, 0.22, zb - 0.004], [0, 0.3, zb - 0.026]], 0.085, hex, 0.93));
  return o;
}

// ---------------------------------------------------------------- assembly
function recipe(items: string[], hex: Record<string, number>): THREE.BufferGeometry | null {
  const list: THREE.BufferGeometry[] = [];
  for (const it of items) {
    const [k, v = '0'] = it.split(':'), c = hex[k] ?? 0x222222;
    if (k === 'glasses' || k === 'sunglasses') list.push(...glasses(+v, k === 'sunglasses'));
    else if (k === 'headphones') list.push(...headphones(c));
    else if (k === 'beard') list.push(beard(c));
    else if (k === 'hood') list.push(hood(c));
    else if (k === 'beanie' || k === 'cap' || k === 'helmet') list.push(...hat(k, c));
    else if (k === 'gilet' || k === 'hivis') list.push(...torso(k, c));
  }
  return list.length ? mergeGeometries(list, false) : null;
}

/** Dress `h` with a kit; clears whatever was on it before. Returns false when the model cannot be measured. */
export function applyKit(h: Human, m: Model, kit: Kit): boolean {
  const slots = h.kit ??= {};
  const set = (slot: 'head' | 'torso', items: string[] | null) => {
    const old = slots[slot];
    if (!items || !items.length) { if (old) old.visible = false; return; }
    const d = measure(m), bone = h.root.getObjectByName(slot === 'head' ? 'head' : 'spine_02');
    if (!d || !bone) return;
    const key = items.map((i) => `${i}#${(kit.hex?.[i.split(':')[0]] ?? 0).toString(16)}`).join('|');
    let g = geoCache.get(key);
    if (!g) { g = recipe(items, kit.hex ?? {}) ?? undefined; if (!g) return; geoCache.set(key, g); }
    material ??= new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.82, metalness: 0, side: THREE.DoubleSide });
    let o = old;
    if (!o) { o = slots[slot] = new THREE.Mesh(g, material); o.matrixAutoUpdate = false; o.castShadow = false; o.frustumCulled = false; }
    if (o.parent !== bone) bone.add(o);
    o.geometry = g; o.visible = true;
    const q = slot === 'head' ? d.q : d.qs;
    if (slot === 'head') {
      const k = d.hw / STD.hw, off = new THREE.Vector3(0, d.top - k * STD.top, -(d.front - k * STD.front)).applyQuaternion(q);
      o.matrix.compose(off, q, new THREE.Vector3(k, k, k));
    } else {
      const kx = d.tw / 0.17, kz = d.td / 0.248, off = new THREE.Vector3(0, 0, d.tcz + 0.047 * kz).applyQuaternion(q), s = new THREE.Vector3(kx, d.ty, kz);
      o.matrix.copy(new THREE.Matrix4().compose(off, q, new THREE.Vector3(1, 1, 1))).multiply(new THREE.Matrix4().makeScale(s.x, s.y, s.z));
    }
    o.matrixWorldNeedsUpdate = true;
  };
  set('head', kit.head ?? null);
  set('torso', kit.torso ? [kit.torso] : null);
  return true;
}

const pick = <T,>(a: readonly T[]) => a[Math.floor(Math.random() * a.length)];
const HAT_COL = [0x15171a, 0x1f2b45, 0x7a2430, 0x4a5a2e, 0x6b7077, 0xb8862b, 0x1d4a36, 0xd8cdb6];
const GILET_COL = [0x15171a, 0x1f2b45, 0x4a5a2e, 0x7a2430, 0x6b7077, 0xb8862b, 0x1d4a36, 0x3a3f66, 0xa5522a];
const HOOD_COL = [0x15171a, 0x3a3f66, 0x4a5a2e, 0x6b7077, 0x7a2430, 0x1f2b45, 0xb8862b, 0x8a8a86];
const HEAD_BAKED = new Set(['npc_17', 'npc_23', 'npc_25', 'npc_32', 'npc_35', 'npc_39']);

/** Random everyday kit for an adult (autumn Zuerich): ~35 % wear something on the head, ~15 % a gilet / vest, ~8 % a hood. `top` = shirt colour (hood matches it). */
export function rollKit(m: Model, _top: number, hair: number | null, male: boolean, role: Role = 'any'): Kit {
  const r = Math.random, head: string[] = [], hex: Record<string, number> = {}, baked = HEAD_BAKED.has(m.id), child = m.age === 'child';
  let torso: string | undefined;
  if (role === 'builder') { torso = 'hivis'; hex.hivis = r() < 0.7 ? 0xff7a00 : 0xcfe000; if (!baked && r() < 0.75) { head.push('helmet'); hex.helmet = pick([0xf2c200, 0xf0f0ec, 0xf2c200, 0xd85a1a]); } }
  else {
    const hat = role === 'courier' ? 0.7 : role === 'student' ? 0.3 : role === 'office' ? 0.03 : child ? 0.2 : 0.17;
    if (!baked && r() < hat) { const k = pick(['beanie', 'beanie', 'cap', 'cap'] as const); head.push(k); hex[k] = pick(HAT_COL); }
    else if (!baked && !child && r() < (role === 'student' ? 0.25 : 0.06)) { head.push('headphones'); hex.headphones = pick([0x15171a, 0x15171a, 0xd8d4c4, 0x7a2430]); }
    if (!child && r() < (role === 'office' ? 0.3 : 0.15)) { const sun = r() < 0.12; head.push(`${sun ? 'sunglasses' : 'glasses'}:${Math.floor(r() * 6)}`); }
    if (!child && male && !baked && r() < 0.15) { head.push('beard'); hex.beard = hair ?? pick([0x2a1a10, 0x3a2414, 0x14100e, 0x6b4126]); }
    if (!child && role !== 'office' && r() < (role === 'courier' ? 0.5 : 0.17)) { torso = 'gilet'; hex.gilet = pick(GILET_COL); }
    if (!child && !torso && role !== 'office' && r() < (role === 'student' ? 0.4 : 0.1)) { head.push('hood'); hex.hood = pick(HOOD_COL); }
  }
  return { head, torso, hex };
}

const TROLLEY_COL = [0x7a2430, 0x1f2b45, 0x1d4a36, 0x15171a, 0x6b7077, 0xa5522a];
/** Shopping trolley (Einkaufstrolley) pulled beside the right leg; origin = ground below the bag, handle reaches the right hand. One draw call. */
export function trolleyFor(h: Human): THREE.Mesh {
  const c = TROLLEY_COL[Math.floor(Math.random() * TROLLEY_COL.length)], key = `trolley#${c.toString(16)}`;
  let g = geoCache.get(key);
  if (!g) {
    const hl = Math.hypot(0.34, 0.23), ang = Math.atan2(0.34, 0.23);
    g = mergeGeometries([box(0.3, 0.46, 0.2, 0, 0.36, 0, c), box(0.31, 0.05, 0.21, 0, 0.6, 0, c, [0, 0, 0]), box(0.22, 0.18, 0.012, 0, 0.3, -0.106, c),
      box(0.012, hl, 0.012, 0.09, 0.62 + 0.115, -0.17, 0x9a9da3, [-(Math.PI / 2 - ang), 0, 0]), box(0.012, hl, 0.012, -0.09, 0.62 + 0.115, -0.17, 0x9a9da3, [-(Math.PI / 2 - ang), 0, 0]),
      box(0.2, 0.014, 0.014, 0, 0.85, -0.34, 0x15171a), box(0.05, 0.05, 0.02, 0.1, 0.05, 0.1, 0x15171a), box(0.05, 0.05, 0.02, -0.1, 0.05, 0.1, 0x15171a)], false)!;
    geoCache.set(key, g);
  }
  material ??= new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.82, metalness: 0, side: THREE.DoubleSide });
  const o = new THREE.Mesh(g, material); o.position.set(0.31, 0, 0.3); o.castShadow = false; o.frustumCulled = false; h.root.add(o);
  return o;
}
