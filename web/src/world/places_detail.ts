import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { glowMaterialPatch } from '../engine/daytime';

/**
 * Plaza / park detail (pipeline/places_detail.py, overrides/places_detail.json): furniture and landmarks of the
 * squares at their real spots. One merged vertex-coloured mesh per tile (1 draw call, no textures).
 * Rows [type, x, y, z, heading_rad(CCW from east), a, b, c, d, colour]; lines {t, h, col, pts[[x,y,z]..]}.
 * Object space: +x along the long side, +y up, +z = local south. Local -> Three: (x, z, -y).
 */
export type PlaceRow = [string, number, number, number, number, number, number, number, number, string];
export interface PlaceLine { t: string; h: number; col: string; pts: number[][] }
export interface PlaceSlab { pts: number[][]; holes: number[][][]; z: number; h: number; t: number; col: string }
export interface PlaceMeta { objs?: PlaceRow[]; lines?: PlaceLine[]; slabs?: PlaceSlab[] }

const GLOW = 0xfff3c8;
const NAMED: Record<string, number> = { steel: 0x8a9095, dark: 0x2a2d30, wood: 0x9a6b3f, stone: 0x9a968c, granite: 0x7d7b76, concrete: 0xb4b2aa,
  water: 0x3f6f8a, green: 0x2f6a3a, bush: 0x3d6b34, red: 0xc8202a, white: 0xf0eee6, yellow: 0xf2c230, blue: 0x2f6fb0, sand: 0xd9c79a, bin: 0x3a4a40 };
const colOf = (s: string | undefined, d: number): number => (!s ? d : s[0] === '#' ? parseInt(s.slice(1), 16) : NAMED[s] ?? d);

function paint(g: THREE.BufferGeometry, c: number): THREE.BufferGeometry {
  g = g.index ? g.toNonIndexed() : g;
  for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal') g.deleteAttribute(k);
  const n = g.getAttribute('position').count, cc = new THREE.Color(c), a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) a.set([cc.r, cc.g, cc.b], i * 3);
  g.setAttribute('color', new THREE.BufferAttribute(a, 3));
  return g;
}
const B = (w: number, h: number, d: number, x: number, y: number, z: number, c: number, ry = 0) => {
  const g = new THREE.BoxGeometry(w, h, d); if (ry) g.rotateY(ry); return paint(g.translate(x, y + h / 2, z), c); }; // y = bottom
const Y = (r0: number, r1: number, h: number, x: number, y: number, z: number, c: number, n = 8) =>
  paint(new THREE.CylinderGeometry(r1, r0, h, n).translate(x, y + h / 2, z), c); // r0 bottom, r1 top
const S = (r: number, x: number, y: number, z: number, c: number, sy = 1) => paint(new THREE.IcosahedronGeometry(r, 1).scale(1, sy, 1).translate(x, y, z), c);
/** tilted post from (x0,y0,z0) to (x1,y1,z1) */
function rod(a: number[], b: number[], r: number, c: number, n = 6) {
  const v = new THREE.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]), L = v.length();
  const g = new THREE.CylinderGeometry(r, r, L, n);
  g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), v.clone().normalize()));
  return paint(g.translate((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2), c);
}

type Fn = (a: number, b: number, c: number, d: number, col: number | undefined, hasCol: boolean) => THREE.BufferGeometry[];
const k = (v: number, d: number) => (v ? v : d);

const T: Record<string, Fn> = {
  generic_box: (a, b, c, _d, col) => [B(k(a, 1), k(c, 1), k(b, 1), 0, 0, 0, col ?? NAMED.concrete)],
  generic_cyl: (a, b, _c, _d, col) => [Y(k(a, 0.5), k(a, 0.5), k(b, 1), 0, 0, 0, col ?? NAMED.steel, 12)],
  // pole a=height (9), b=radius
  pole: (a, b, _c, _d, col) => [Y(k(b, 0.07), k(b, 0.07) * 0.7, k(a, 6), 0, 0, 0, col ?? NAMED.steel, 8)],
  // flag mast a=height, colour = flag type via d: 0 CH, 1 ZH, 2 city
  flag: (a, _b, _c, d) => {
    const H = k(a, 9), p: THREE.BufferGeometry[] = [Y(0.08, 0.04, H, 0, 0, 0, 0xb9bec2, 8), S(0.07, 0, H + 0.05, 0, 0xd8c070)];
    const W = 2.0, Hh = 1.3, y0 = H - Hh - 0.3, x0 = 0.05;
    if (d === 0) { p.push(B(W, Hh, 0.02, x0 + W / 2, y0, 0, 0xd0202a)); p.push(B(0.9, 0.3, 0.03, x0 + W / 2, y0 + Hh / 2 - 0.15, 0, 0xf4f4f0)); p.push(B(0.3, 0.9, 0.03, x0 + W / 2, y0 + Hh / 2 - 0.45, 0, 0xf4f4f0)); }
    else if (d === 1) { p.push(B(W, Hh, 0.02, x0 + W / 2, y0, 0, 0x2a5fb0)); p.push(B(W, Hh / 2, 0.03, x0 + W / 2, y0 + Hh / 2, 0, 0xf4f4f0)); }
    else { p.push(B(W, Hh, 0.02, x0 + W / 2, y0, 0, 0xf4f4f0)); p.push(B(W * 0.5, Hh, 0.03, x0 + W / 4, y0, 0, 0x2a5fb0)); }
    return p;
  },
  // bent steel arch mast a=height (8), b=max bend angle in degrees (70); curves toward +x; lamp head at the tip
  arch: (a, b, _c, _d, col) => {
    const H = k(a, 8), bend = (k(b, 70) * Math.PI) / 180, c = col ?? 0xa7adb2, p: THREE.BufferGeometry[] = [], N = 8, dl = H / N;
    let x = 0, y = 0, prev = [0, 0, 0];
    for (let i = 1; i <= N; i++) { const th = bend * Math.pow(i / N, 2.2); x += Math.sin(th) * dl; y += Math.cos(th) * dl; const cur = [x, y, 0]; p.push(rod(prev, cur, 0.065 - 0.03 * (i / N), c)); prev = cur; }
    p.push(Y(0.22, 0.2, 0.1, 0, 0, 0, 0x5a5f63, 10));
    p.push(B(0.7, 0.12, 0.3, prev[0], prev[1] - 0.2, 0, 0x6d7377), B(0.5, 0.03, 0.22, prev[0], prev[1] - 0.22, 0, GLOW));
    return p;
  },
  // street lamp pole a=height, b=arm length
  lamp: (a, b, _c, _d, col) => {
    const H = k(a, 6), L = k(b, 1.2), c = col ?? 0x4f585c;
    return [Y(0.1, 0.06, H, 0, 0, 0, c, 8), B(L, 0.06, 0.06, L / 2, H - 0.05, 0, c), B(0.6, 0.1, 0.28, L, H - 0.09, 0, 0x6d7377), B(0.45, 0.03, 0.2, L, H - 0.15, 0, GLOW)];
  },
  // mushroom lamp (Pilzleuchte): a=height 4, black disc shade
  pilz: (a) => [Y(0.07, 0.05, k(a, 4), 0, 0, 0, 0x26292c, 7), Y(0.6, 0.12, 0.22, 0, k(a, 4) - 0.1, 0, 0x26292c, 12), Y(0.4, 0.4, 0.03, 0, k(a, 4) - 0.12, 0, GLOW, 10)],
  // garden table set: round table (colour) with 4 chairs
  gtable: (_a, _b, _c, _d, col) => { const c = col ?? 0xc8302a, p: THREE.BufferGeometry[] = [Y(0.4, 0.4, 0.03, 0, 0.72, 0, c, 10), Y(0.03, 0.03, 0.72, 0, 0, 0, 0x3a3d40, 5)]; for (const [x, z] of [[0.62, 0], [-0.62, 0], [0, 0.62], [0, -0.62]]) p.push(B(0.4, 0.04, 0.4, x, 0.44, z, c), B(0.4 * (x ? 0.1 : 1), 0.4, 0.4 * (x ? 1 : 0.1), x * 1.3, 0.46, z * 1.3, c)); return p; },
  // Tisch-Bank-Kombi: table a=length (2.0) with two benches
  tbench: (a, b, _c, _d, col) => {
    const L = k(a, 2.0), W = k(b, 0.75), wood = col ?? 0x8f6a42, st = 0x4a5256;
    const p = [B(L, 0.05, W, 0, 0.74, 0, wood), B(L, 0.05, 0.28, 0, 0.44, W / 2 + 0.3, wood), B(L, 0.05, 0.28, 0, 0.44, -W / 2 - 0.3, wood)];
    for (const sx of [-L * 0.38, L * 0.38]) p.push(B(0.05, 0.74, W + 0.9, sx, 0, 0, st), B(0.5, 0.04, 0.04, sx, 0.74, 0, st));
    return p;
  },
  // park bench a=length: slatted wood on steel feet
  bench: (a, _b, _c, _d, col) => {
    const L = k(a, 1.8), wood = col ?? 0x8f6a42, st = 0x3a4043;
    return [B(L, 0.05, 0.42, 0, 0.44, 0, wood), B(L, 0.4, 0.04, 0, 0.62, -0.2, wood), B(0.05, 0.44, 0.4, -L * 0.42, 0, 0, st), B(0.05, 0.44, 0.4, L * 0.42, 0, 0, st)];
  },
  // Züri-Kübel: dark steel cylinder with ring and lid
  bin: () => [Y(0.2, 0.2, 0.8, 0, 0.05, 0, 0x3d4a42, 10), Y(0.22, 0.22, 0.05, 0, 0.85, 0, 0x2a3530, 10), Y(0.03, 0.03, 0.05, 0, 0, 0, 0x2a2d30, 6)],
  // drinking fountain: stone column a=height with brass spout and small basin
  dfount: (a) => [Y(0.22, 0.17, k(a, 1.0), 0, 0, 0, 0x8d8a82, 8), Y(0.3, 0.3, 0.1, 0, 0, 0, 0x7a776f, 8), B(0.35, 0.05, 0.3, 0.2, k(a, 1.0) - 0.15, 0, 0x4a4d50), B(0.03, 0.03, 0.2, 0.22, k(a, 1.0) - 0.08, 0, 0xb59a52)],
  // basin: a=length, b=width, c=coping height; stone rim 0.3, water inside
  basin: (a, b, c, _d, col) => {
    const L = k(a, 6), W = k(b, 2.5), H = k(c, 0.45), t = 0.32, st = col ?? NAMED.granite;
    return [B(L, H, t, 0, 0, -(W - t) / 2, st), B(L, H, t, 0, 0, (W - t) / 2, st), B(t, H, W - 2 * t, -(L - t) / 2, 0, 0, st), B(t, H, W - 2 * t, (L - t) / 2, 0, 0, st),
      B(L - 2 * t, 0.02, W - 2 * t, 0, H - 0.16, 0, NAMED.water), B(L - 2 * t, 0.1, W - 2 * t, 0, 0, 0, 0x55584f)];
  },
  // round fountain: a=radius, b=height, with centre column
  rfount: (a, b, _c, _d, col) => {
    const R = k(a, 1.6), H = k(b, 0.7), st = col ?? NAMED.stone;
    return [Y(R, R, H, 0, 0, 0, st, 20), Y(R - 0.3, R - 0.3, 0.03, 0, H, 0, NAMED.water, 20).translate(0, -0.05, 0), Y(0.25, 0.18, 1.3, 0, 0, 0, st, 10), Y(0.5, 0.5, 0.12, 0, 1.25, 0, st, 12)];
  },
  // kiosk / small pavilion a=length b=depth c=height, roof overhang; col = wall colour
  kiosk: (a, b, c, _d, col) => {
    const L = k(a, 4), D = k(b, 3), H = k(c, 2.6), w = col ?? 0xd8d4c6;
    return [B(L, H, D, 0, 0, 0, w), B(L + 0.8, 0.18, D + 0.8, 0, H, 0, 0x3a3f44), B(L * 0.7, 0.9, 0.05, 0, 1.0, D / 2 + 0.03, 0x1d2226), B(L * 0.7, 0.1, 0.7, 0, 1.95, D / 2 + 0.3, 0xc8202a),
      B(L * 0.7, 0.06, 0.4, 0, 0.95, D / 2 + 0.2, 0x8a8d90)];
  },
  // open pavilion on posts: a=length b=depth c=height; col = roof colour
  pavilion: (a, b, c, _d, col) => {
    const L = k(a, 8), D = k(b, 6), H = k(c, 3.2), p: THREE.BufferGeometry[] = [];
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) p.push(Y(0.14, 0.14, H, sx * (L / 2 - 0.3), 0, sz * (D / 2 - 0.3), 0xcfcac0, 8));
    p.push(B(L, 0.25, D, 0, H, 0, col ?? 0x6b6258), B(L + 1, 0.12, D + 1, 0, H + 0.2, 0, col ?? 0x6b6258));
    p.push(B(L - 0.6, 0.12, D - 0.6, 0, 0, 0, 0xb4b0a6)); // floor slab
    return p;
  },
  // market stall: a=length (3), b=depth (2), colour = awning; counter + clothes rail
  stall: (a, b, _c, _d, col) => {
    const L = k(a, 3), D = k(b, 2), c = col ?? 0xe9e4d8, p: THREE.BufferGeometry[] = [];
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) p.push(Y(0.03, 0.03, 2.3, sx * (L / 2 - 0.05), 0, sz * (D / 2 - 0.05), 0x9a9ea2, 6));
    p.push(B(L + 0.2, 0.05, D + 0.3, 0, 2.3, 0, c), B(L - 0.2, 0.06, 0.8, 0, 0.8, D / 2 - 0.5, 0x8a6a44), B(L - 0.3, 0.3, 0.7, 0, 0.82, D / 2 - 0.5, 0xb85a4a));
    return p;
  },
  // clothes rail with garments a=length
  rail: (a) => {
    const L = k(a, 2), p: THREE.BufferGeometry[] = [B(L, 0.03, 0.03, 0, 1.6, 0, 0xb8bcc0), B(0.03, 1.6, 0.03, -L / 2, 0, 0, 0xb8bcc0), B(0.03, 1.6, 0.03, L / 2, 0, 0, 0xb8bcc0)];
    const cols = [0xc85a5a, 0x4a6fa5, 0xe0c060, 0x6a9a6a, 0xd8d4c6, 0x8a5a9a, 0x2a2d30];
    for (let i = 0; i < L / 0.12; i++) p.push(B(0.07, 0.8 + (i % 3) * 0.1, 0.35, -L / 2 + 0.1 + i * 0.12, 0.75, 0, cols[i % cols.length]));
    return p;
  },
  // raised stone kerb / step strip a=length b=width c=height
  kerb: (a, b, c, _d, col) => [B(k(a, 4), k(c, 0.15), k(b, 0.4), 0, 0, 0, col ?? 0x9d9a92)],
  // stepped seating stairs a=length b=depth c=step h, 3 steps
  steps: (a, b, c, _d, col) => { const L = k(a, 6), D = k(b, 0.45), H = k(c, 0.16); return [0, 1, 2].map((i) => B(L, H * (i + 1), D, 0, 0, -i * D, col ?? 0x9d9a92)); },
  // planter / low wall a=length b=width c=height; d=1 adds a shrub
  planter: (a, b, c, d, col) => { const L = k(a, 3), W = k(b, 1), H = k(c, 0.5); const p = [B(L, H, W, 0, 0, 0, col ?? 0x8d8a82), B(L - 0.2, 0.05, W - 0.2, 0, H, 0, 0x4a3a2a)]; if (d) p.push(S(Math.min(L, W) * 0.5, 0, H + 0.3, 0, 0x3d6b34, 0.8)); return p; },
  bush: (a, b, _c, _d, col) => [S(k(a, 0.8), 0, k(b, 0.7), 0, col ?? 0x3d6b34, 0.85), Y(0.05, 0.05, 0.3, 0, 0, 0, 0x4a3a2a, 5)],
  hedge: (a, b, c, _d, col) => [B(k(a, 4), k(c, 1.1), k(b, 0.7), 0, 0, 0, col ?? 0x355f2a)],
  bollard: (a) => [Y(0.1, 0.1, k(a, 0.8), 0, 0, 0, 0x6a6e72, 8)],
  // sculpture variants via d: 0 stacked blocks, 1 sphere on plinth, 2 tall stele, 3 abstract arc
  sculpt: (a, _b, _c, d, col) => {
    const H = k(a, 2), c = col ?? 0x9a8f7a;
    if (d === 1) return [B(0.8, 0.5, 0.8, 0, 0, 0, 0x8d8a82), S(H * 0.35, 0, 0.5 + H * 0.35, 0, c)];
    if (d === 4) { // two rearing foals (bronze)
      const foal = (x: number, z: number, r: number) => [rod([x, 0.5, z], [x + 0.1 * r, 1.2, z], 0.17, c, 7), rod([x + 0.1 * r, 1.2, z], [x + 0.3 * r, 1.6, z], 0.07, c, 6), S(0.12, x + 0.35 * r, 1.65, z, c), rod([x, 0.5, z], [x - 0.15 * r, 0, z + 0.1], 0.06, c, 5), rod([x, 0.5, z], [x + 0.2, 0, z - 0.1], 0.06, c, 5)];
      return [B(2.2, 0.3, 1.2, 0, 0, 0, 0x9a9890), ...foal(-0.5, 0, 1), ...foal(0.5, 0.1, -1)];
    }
    if (d === 2) return [B(0.5, H, 0.5, 0, 0, 0, c), B(0.9, 0.2, 0.9, 0, 0, 0, 0x8d8a82)];
    if (d === 3) return [rod([0, 0, 0], [0.3, H, 0], 0.1, c), rod([0.3, H, 0], [1.4, H * 0.7, 0], 0.1, c), rod([1.4, H * 0.7, 0], [1.6, 0, 0], 0.1, c)];
    return [B(1.2, 0.5, 1.0, 0, 0, 0, c), B(0.9, 0.5, 0.8, 0.1, 0.5, 0, c), B(0.6, 0.5, 0.6, 0.2, 1.0, 0, c)];
  },
  // bronze monument group on a plinth: a=plinth height, b=figures (3)
  monument: (a, b, _c, _d, col) => {
    const H = k(a, 1.2), c = col ?? 0x5a6a58, p: THREE.BufferGeometry[] = [B(2.4, H, 1.4, 0, 0, 0, 0x9a9890), B(2.6, 0.12, 1.6, 0, H, 0, 0x8d8a82)];
    const fig = (x: number, z: number, h: number) => { p.push(Y(0.2, 0.14, h * 0.72, x, H + 0.12, z, c, 7), Y(0.16, 0.12, h * 0.1, x, H + 0.12 + h * 0.7, z, c, 7), S(0.11, x, H + 0.12 + h * 0.9, z, c)); };
    for (let i = 0; i < k(b, 3); i++) fig(-0.7 + i * 0.7, (i % 2) * 0.12, i === 1 ? 1.3 : 1.75);
    return p;
  },
  // round stone bench ring around a tree: a=radius (2.3)
  ringbench: (a, _b, _c, _d, col) => { const R = k(a, 2.3), p: THREE.BufferGeometry[] = []; for (let i = 0; i < 10; i++) { const th = (i / 10) * Math.PI * 2; p.push(B(1.4, 0.45, 0.5, Math.cos(th) * R, 0, Math.sin(th) * R, col ?? 0x9d9486, -th + Math.PI / 2)); } p.push(Y(R - 0.4, R - 0.4, 0.06, 0, 0, 0, 0x6b5a48, 16)); return p; },
  // Hundebrunnen (Albisriederplatz): granite block with seated bronze dog, conical granite bowl; slab = round paving plate
  hundebrunnen: () => [Y(1.9, 1.9, 0.05, 0, 0, 0, 0x8d8a82, 20), B(0.6, 1.2, 0.6, -0.5, 0.05, 0, 0x8a8a86), B(0.65, 0.05, 0.65, -0.5, 1.25, 0, 0x7a7a76),
    Y(0.35, 0.55, 0.5, 0.45, 0.05, 0, 0x8d8a82, 14), Y(0.5, 0.5, 0.03, 0.45, 0.5, 0, NAMED.water, 14),
    Y(0.17, 0.12, 0.45, -0.5, 1.3, 0, 0x5a7a6a, 7), S(0.12, -0.45, 1.85, 0, 0x5a7a6a), B(0.3, 0.06, 0.3, -0.5, 1.3, 0, 0x4a6a5a)],
  // concrete bollard a=height (0.7)
  cbollard: (a, b) => [Y(k(b, 0.2), k(b, 0.2), k(a, 0.7), 0, 0, 0, 0x9a9890, 10), Y(k(b, 0.2) + 0.01, k(b, 0.2) + 0.01, 0.06, 0, k(a, 0.7) - 0.06, 0, 0x7a7870, 10)],
  // round concrete stool / hocker a=radius b=height, striped band via d=1
  hocker: (a, b, _c, d) => [Y(k(a, 0.7), k(a, 0.7), k(b, 0.5), 0, 0, 0, 0xa6a39a, 14), ...(d ? [Y(k(a, 0.7) + 0.005, k(a, 0.7) + 0.005, 0.12, 0, k(b, 0.5) * 0.4, 0, 0x2a2a2a, 14)] : [])],
  // concrete flower-pot drinking fountain (Betonkübel) a=radius 0.4, height 0.75
  bucket: (a) => [Y(k(a, 0.4) * 0.8, k(a, 0.4), 0.75, 0, 0, 0, 0x8e8c86, 12), Y(k(a, 0.4) - 0.04, k(a, 0.4) - 0.04, 0.02, 0, 0.72, 0, NAMED.water, 12), B(0.03, 0.4, 0.03, 0.25, 0.75, 0, 0xb8bcc0)],
  // Kugelleuchte: concrete post with three white glass globes (a=height)
  kugel: (a) => { const H = k(a, 3.2); return [Y(0.16, 0.12, H, 0, 0, 0, 0x9a9890, 8), B(0.9, 0.05, 0.05, 0, H - 0.3, 0, 0x5a5f63), S(0.22, -0.45, H - 0.1, 0, GLOW), S(0.22, 0.45, H - 0.1, 0, GLOW), S(0.22, 0, H + 0.22, 0, GLOW)]; },
  // Tellerbrunnen: round shallow basin (a=radius) with low granite rim, central stem and shallow dish (b=radius)
  tellerbrunnen: (a, b) => { const R = k(a, 6), r = k(b, 2.5), st = 0xb4a58a; return [Y(R, R, 0.4, 0, 0, 0, 0x8d8a82, 32), Y(R - 0.45, R - 0.45, 0.02, 0, 0.3, 0, 0x4f7f95, 32), Y(0.5, 0.35, 0.9, 0, 0, 0, st, 10), Y(0.2, r, 0.35, 0, 0.8, 0, st, 20), Y(r - 0.2, r - 0.2, 0.02, 0, 1.16, 0, 0x4f7f95, 20)]; },
  // concrete planter bowl with perennials a=radius
  bowl: (a) => [Y(k(a, 0.5) * 0.8, k(a, 0.5), 0.45, 0, 0, 0, 0x9a968c, 10), S(k(a, 0.5) * 0.9, 0, 0.6, 0, 0x5a8a3a, 0.7)],
  // table tennis (concrete) a=length 2.74 → fixed
  pingpong: () => [B(2.74, 0.12, 1.52, 0, 0.7, 0, 0x7a8286), B(0.1, 0.7, 1.4, -1.0, 0, 0, 0x7a8286), B(0.1, 0.7, 1.4, 1.0, 0, 0, 0x7a8286), B(0.03, 0.15, 1.5, 0, 0.82, 0, 0xb8bcc0)],
  // petanque / boule court: gravel field with timber border a=length b=width
  boule: (a, b) => { const L = k(a, 12), W = k(b, 4); return [B(L, 0.12, 0.14, 0, 0, -W / 2, 0x8a6a44), B(L, 0.12, 0.14, 0, 0, W / 2, 0x8a6a44), B(0.14, 0.12, W, -L / 2, 0, 0, 0x8a6a44), B(0.14, 0.12, W, L / 2, 0, 0, 0x8a6a44)]; },
  sandbox: (a, b) => { const L = k(a, 4), W = k(b, 3); return [B(L, 0.3, 0.14, 0, 0, -W / 2, 0x8a6a44), B(L, 0.3, 0.14, 0, 0, W / 2, 0x8a6a44), B(0.14, 0.3, W, -L / 2, 0, 0, 0x8a6a44), B(0.14, 0.3, W, L / 2, 0, 0, 0x8a6a44), B(L - 0.2, 0.18, W - 0.2, 0, 0, 0, 0xd9c79a)]; },
  // bike stand row a=count
  bikerack: (a) => { const p: THREE.BufferGeometry[] = []; for (let i = 0; i < k(a, 5); i++) p.push(rod([i * 0.75, 0, 0], [i * 0.75, 0.8, 0], 0.025, 0xb8bcc0), rod([i * 0.75 + 0.7, 0, 0], [i * 0.75 + 0.7, 0.8, 0], 0.025, 0xb8bcc0), B(0.7, 0.04, 0.04, i * 0.75 + 0.35, 0.8, 0, 0xb8bcc0)); return p; },
  // yellow/white site container a=length
  container: (a, b, c, _d, col) => [B(k(a, 6), k(c, 2.5), k(b, 2.4), 0, 0, 0, col ?? 0xe6b422), B(k(a, 6) + 0.1, 0.08, k(b, 2.4) + 0.1, 0, k(c, 2.5), 0, 0x4a4d50)],
  // street cabinet / transformer hut
  cabinet: (a, b, c, _d, col) => [B(k(a, 1.2), k(c, 1.5), k(b, 0.6), 0, 0, 0, col ?? 0x7a8a7a)],
  // shelter roof on posts (tram/bus): a=length b=depth
  shelter: (a, b) => { const L = k(a, 6), D = k(b, 1.8), p: THREE.BufferGeometry[] = [B(L, 0.12, D, 0, 2.6, 0, 0x4a5056)]; for (const sx of [-1, 1]) p.push(B(0.08, 2.6, 0.08, sx * (L / 2 - 0.2), 0, -D / 2 + 0.2, 0x5a6066), B(0.08, 2.6, 0.08, sx * (L / 2 - 0.2), 0, D / 2 - 0.2, 0x5a6066)); p.push(B(L - 0.6, 0.05, 0.4, 0, 0.45, -D / 2 + 0.3, 0x8f6a42), B(L - 0.4, 1.6, 0.04, 0, 0.9, -D / 2 + 0.1, 0xa9c4cc)); return p; },
  // pergola a=length b=depth c=height
  pergola: (a, b, c) => { const L = k(a, 6), D = k(b, 3), H = k(c, 2.6), p: THREE.BufferGeometry[] = []; for (const sx of [-1, 1]) for (const sz of [-1, 1]) p.push(Y(0.08, 0.08, H, sx * L / 2, 0, sz * D / 2, 0x6b4a2a, 6)); for (let i = 0; i <= 8; i++) p.push(B(0.08, 0.1, D + 0.6, -L / 2 + (L * i) / 8, H, 0, 0x6b4a2a)); return p; },
  // lamp bollard / low light
  glow: (a) => [Y(0.08, 0.08, k(a, 0.9), 0, 0, 0, 0x4a4d50, 6), B(0.2, 0.2, 0.2, 0, k(a, 0.9), 0, GLOW)],
};

// polylines (a pole every ~2.5 m)
function line(l: PlaceLine): THREE.BufferGeometry[] {
  const out: THREE.BufferGeometry[] = [];
  const P = (p: number[]): number[] => [p[0], p[2], -p[1]];
  const c = l.col ? colOf(l.col, 0xcccccc) : undefined;
  for (let i = 0; i + 1 < l.pts.length; i++) {
    const a = l.pts[i], b = l.pts[i + 1], len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (len < 0.05) continue;
    const yaw = Math.atan2(b[1] - a[1], b[0] - a[0]);
    const n = Math.max(1, Math.round(len / (l.t === 'fence' ? 3.0 : 1)));
    for (let j = 0; j < n; j++) {
      const t0 = j / n, t1 = (j + 1) / n, mx = a[0] + (b[0] - a[0]) * (t0 + t1) / 2, my = a[1] + (b[1] - a[1]) * (t0 + t1) / 2, mz = a[2] + (b[2] - a[2]) * (t0 + t1) / 2;
      const seg = len / n;
      let g: THREE.BufferGeometry[] = [];
      if (l.t === 'fence') { // construction fence: panel with white/yellow face + concrete feet
        const H = l.h || 2.0, face = c ?? (j % 2 ? 0xf0efe8 : 0xe6b422);
        g = [B(seg - 0.05, H - 0.1, 0.04, 0, 0.1, 0, face), B(0.4, 0.12, 0.5, -seg / 2 + 0.2, 0, 0, 0x8d8a82), B(0.4, 0.12, 0.5, seg / 2 - 0.2, 0, 0, 0x8d8a82), B(seg - 0.05, 0.05, 0.05, 0, H, 0, 0x9aa0a4)];
      } else if (l.t === 'hedge') g = [B(seg + 0.02, l.h || 1.0, 0.7, 0, 0, 0, c ?? 0x355f2a)];
      else if (l.t === 'wall') g = [B(seg + 0.02, l.h || 0.5, 0.35, 0, 0, 0, c ?? 0x8d8a82)];
      else if (l.t === 'rail') g = [B(seg + 0.02, 0.04, 0.04, 0, l.h || 1.0, 0, c ?? 0x3a4043), B(0.04, l.h || 1.0, 0.04, -seg / 2, 0, 0, c ?? 0x3a4043)];
      else if (l.t === 'curb') g = [B(seg + 0.02, l.h || 0.15, 0.3, 0, 0, 0, c ?? 0x9d9a92)];
      else continue;
      const q = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
      const m = new THREE.Matrix4().compose(new THREE.Vector3(...P([mx, my, mz])), q, new THREE.Vector3(1, 1, 1));
      for (const x of g) out.push(x.applyMatrix4(m));
    }
  }
  return out;
}

let mat: THREE.MeshLambertMaterial | undefined;
export function buildPlaces(meta: PlaceMeta | undefined, shadows: boolean): THREE.Object3D[] {
  if (!meta || (!meta.objs?.length && !meta.lines?.length && !meta.slabs?.length)) return [];
  const parts: THREE.BufferGeometry[] = [];
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), s = new THREE.Vector3(1, 1, 1), up = new THREE.Vector3(0, 1, 0);
  for (const [t, x, y, z, h, a, b, c, d, col] of meta.objs ?? []) {
    const f = T[t];
    if (!f) { console.warn('places_detail: unknown type', t); continue; }
    m.compose(p.set(x, z, -y), q.setFromAxisAngle(up, h), s);
    for (const g of f(a, b, c, d, col ? colOf(col, 0) : undefined, !!col)) parts.push(g.applyMatrix4(m));
  }
  for (const l of meta.lines ?? []) parts.push(...line(l));
  for (const sl of meta.slabs ?? []) { // canopy roof: extruded polygon (tree holes), top at z + h
    const sh = new THREE.Shape(sl.pts.map(([x, y]) => new THREE.Vector2(x, y)));
    for (const h of sl.holes) sh.holes.push(new THREE.Path(h.map(([x, y]) => new THREE.Vector2(x, y))));
    const g = new THREE.ExtrudeGeometry(sh, { depth: sl.t, bevelEnabled: false });
    g.rotateX(-Math.PI / 2); g.translate(0, sl.z + sl.h, 0);
    parts.push(paint(g.index ? g.toNonIndexed() : g, colOf(sl.col, 0xb9b7af)));
  }
  if (!parts.length) return [];
  const mesh = new THREE.Mesh(mergeGeometries(parts)!, (mat ??= (() => { const x = new THREE.MeshLambertMaterial({ vertexColors: true }); glowMaterialPatch(x); return x; })()));
  parts.forEach((g) => g.dispose());
  mesh.castShadow = shadows;
  mesh.receiveShadow = shadows;
  return [mesh];
}
