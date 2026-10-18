import * as THREE from 'three';
import { foliagePatch } from './foliage';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/**
 * Street details from OSM tags (pipeline/details_osm.py): advertising columns, phone booths, post boxes, recycling points,
 * guideposts, clocks, info boards, chargers, kiosks, gates, drinking fountains, hedges, fences and autumn leaves.
 * One merged vertex-coloured mesh per tile (1 draw call, no textures). Sources: research/details.md.
 * Rows [type, x, y, z, heading_rad(CCW from east), a, b, c]; lines {t, h, w, pts[[x,y,z]]}; leaves [x, y, z, rot_deg, colour].
 * Object space: +x along heading, +y up, +z = local south. Local -> Three: (x, z, -y).
 */
export type DetailRow = [string, number, number, number, number, number, number, number];
export interface DetailLine { t: string; h: number; w: number; pts: number[][] }
export interface DetailMeta { objs?: DetailRow[]; lines?: DetailLine[]; leaves?: number[][] }

function paint(g: THREE.BufferGeometry, c: number): THREE.BufferGeometry {
  g = g.index ? g.toNonIndexed() : g;
  for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal') g.deleteAttribute(k);
  const n = g.getAttribute('position').count, cc = new THREE.Color(c), a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) a.set([cc.r, cc.g, cc.b], i * 3);
  g.setAttribute('color', new THREE.BufferAttribute(a, 3));
  g.setAttribute('fol', new THREE.BufferAttribute(new Float32Array(n), 1)); // look3: 1 = hedge foliage vertex (see foliage.ts)
  return g;
}
type G = THREE.BufferGeometry;
const B = (w: number, h: number, d: number, x: number, y: number, z: number, c: number, ry = 0): G => {
  const g = new THREE.BoxGeometry(w, h, d); if (ry) g.rotateY(ry); return paint(g.translate(x, y + h / 2, z), c); }; // y = bottom
const Y = (r0: number, r1: number, h: number, x: number, y: number, z: number, c: number, n = 8): G =>
  paint(new THREE.CylinderGeometry(r1, r0, h, n).translate(x, y + h / 2, z), c);
const S = (r: number, x: number, y: number, z: number, c: number, sy = 1): G => paint(new THREE.IcosahedronGeometry(r, 0).scale(1, sy, 1).translate(x, y, z), c);
const rnd = (x: number, y: number, s = 0) => { const v = Math.sin(x * 127.1 + y * 311.7 + s * 74.7) * 43758.5453; return v - Math.floor(v); };

const POSTER = [0xc9b79a, 0x6f8fa8, 0xd8c35a, 0xb85a4a, 0x8a9f7a, 0xe8e4da, 0x3f4f6a, 0xcf8a4a];
const FIN = 0x4a5256;

const T: Record<string, (a: number, b: number, c: number, x: number, y: number) => G[]> = {
  // Litfasssäule (Allgemeine Plakatgesellschaft): dark base, four poster sectors, domed cap; a = poster palette offset, b = lit
  column: (a, b, _c, x, y) => {
    const p: G[] = [Y(0.66, 0.66, 0.35, 0, 0, 0, 0x2f4a3c, 12)];
    for (let i = 0; i < 4; i++) {
      const g = new THREE.CylinderGeometry(0.62, 0.62, 2.2, 6, 1, false, (i * Math.PI) / 2, Math.PI / 2).translate(0, 0.35 + 1.1, 0);
      p.push(paint(g, POSTER[Math.floor(rnd(x, y, i + a) * POSTER.length)]));
    }
    p.push(Y(0.7, 0.7, 0.1, 0, 2.55, 0, 0x2f4a3c, 12), paint(new THREE.ConeGeometry(0.7, 0.45, 12).translate(0, 2.65 + 0.22, 0), 0x3a4a42), S(0.08, 0, 3.15, 0, 0x6d7377));
    if (b) p.push(Y(0.63, 0.63, 0.04, 0, 2.5, 0, 0xfff3c8, 12));
    return p;
  },
  // phone booth: grey frame, glass sides, roof sign
  phone: () => [B(0.9, 0.08, 0.9, 0, 0, 0, 0x6b7074), B(0.9, 0.12, 0.9, 0, 2.25, 0, 0x4a5256), B(0.86, 2.2, 0.03, 0, 0.08, 0.43, 0x9db8c4), B(0.86, 2.2, 0.03, 0, 0.08, -0.43, 0x9db8c4),
    B(0.03, 2.2, 0.8, -0.43, 0.08, 0, 0x9db8c4), B(0.05, 1.2, 0.05, 0.43, 0.08, 0.38, FIN), B(0.05, 1.2, 0.05, 0.43, 0.08, -0.38, FIN), B(0.3, 0.55, 0.1, -0.38, 1.0, 0, 0x2a2d30)],
  // Swiss Post letter box (yellow); a=1 on a lamp-style post
  postbox: (a) => a ? [Y(0.05, 0.05, 1.55, 0, 0, 0, FIN, 6), B(0.46, 0.55, 0.3, 0, 1.05, 0, 0xf2c200), B(0.34, 0.05, 0.02, 0, 1.45, 0.16, 0x1d1d1d), B(0.12, 0.12, 0.02, 0, 1.2, 0.16, 0x1d1d1d)]
    : [B(0.2, 0.25, 0.3, 0, 0, 0, FIN), B(0.55, 0.85, 0.4, 0, 0.25, 0, 0xf2c200), B(0.4, 0.05, 0.02, 0, 0.95, 0.21, 0x1d1d1d), B(0.15, 0.15, 0.02, 0, 0.6, 0.21, 0x1d1d1d)],
  // recycling point: three collection posts; flags a: 1 glass, 2 cans, 4 clothes
  recycling: (a) => {
    const set = a & 1 ? [0x2f7a45, 0x7a4a2a, 0xe8e6de] : a & 4 ? [0xb23a30, 0x8f949a, 0xb23a30] : a & 2 ? [0xa9aeb2, 0x2f6fb0, 0xa9aeb2] : [0x7d8286, 0x7d8286, 0x7d8286];
    const p: G[] = [];
    set.forEach((c, i) => { const x = (i - 1) * 1.0; p.push(Y(0.42, 0.42, 1.25, x, 0, 0, c, 10), Y(0.46, 0.46, 0.08, x, 1.25, 0, 0x3a3d40, 10), B(0.18, 0.12, 0.05, x, 0.95, 0.4, 0x1d2226)); });
    return p;
  },
  // Zürcher Trinkbrunnen: stone column with brass spout and shallow trough; a=1 steel
  dwater: (a) => [B(1.5, 0.35, 0.7, 0, 0, 0, a ? 0x9aa0a4 : 0x8d8a82), B(1.3, 0.04, 0.5, 0, 0.35, 0, 0x4f7f95), Y(0.18, 0.15, 1.15, -0.45, 0, -0.18, a ? 0xa7adb2 : 0x9a968c, 8), B(0.04, 0.04, 0.22, -0.45, 1.0, -0.06, 0xb59a52)],
  // Wegweiser: pole with plates; a=1 Velo (white with red frame), else Wanderweg (yellow); b = number of plates
  guidepost: (a, b) => {
    const p: G[] = [Y(0.05, 0.05, 2.7, 0, 0, 0, 0x6d7377, 6)];
    for (let i = 0; i < Math.max(1, b); i++) {
      const y = 2.35 - i * 0.3, ry = i * 0.6 - 0.2;
      if (a) p.push(B(0.9, 0.22, 0.03, 0.4, y, 0, 0xf4f2ec, ry), B(0.9, 0.03, 0.035, 0.4, y + 0.19, 0, 0xc8202a, ry), B(0.9, 0.03, 0.035, 0.4, y, 0, 0xc8202a, ry), B(0.1, 0.1, 0.04, 0.1, y + 0.06, 0, 0xc8202a, ry));
      else p.push(B(0.85, 0.2, 0.03, 0.38, y, 0, 0xf2c230, ry), B(0.08, 0.12, 0.035, 0.75, y + 0.04, 0, 0x1d1d1d, ry));
    }
    return p;
  },
  infoboard: (a) => [B(0.08, 2.1, 0.08, -0.7, 0, 0, FIN), B(0.08, 2.1, 0.08, 0.7, 0, 0, FIN), B(1.6, 1.0, 0.06, 0, 0.95, 0, a ? 0xd8dccb : 0x35505a), B(1.5, 0.9, 0.02, 0, 1.0, 0.04, a ? 0xb9c8a0 : 0xe6e2d6)],
  // street clock on a pole (two-sided dial)
  clock: () => {
    const d = (z: number) => [paint(new THREE.CylinderGeometry(0.36, 0.36, 0.08, 20).rotateX(Math.PI / 2).translate(0, 3.5, z), 0xf4f2ec), paint(new THREE.TorusGeometry(0.36, 0.035, 5, 20).translate(0, 3.5, z), 0x2a2d30)];
    return [Y(0.07, 0.06, 3.5, 0, 0, 0, 0x2f3438, 8), ...d(0.06), ...d(-0.06), B(0.03, 0.26, 0.02, 0, 3.5, 0.11, 0x1d1d1d), B(0.2, 0.03, 0.02, 0.1, 3.5, 0.11, 0x1d1d1d)];
  },
  // cellar light-well grating lying flat (a Lichtschacht at the foot of an Altbau)
  cellar: () => [B(1.0, 0.03, 0.6, 0, 0, 0, 0x3a3d40), ...[-0.36, -0.18, 0, 0.18, 0.36].map((x) => B(0.03, 0.035, 0.56, x, 0, 0, 0x7a7e82))],
  // satellite dish on the wall: a = height above the ground
  dish: (a) => [B(0.08, 0.08, 0.3, 0, a, 0.05, 0x6d7377), paint(new THREE.SphereGeometry(0.32, 8, 4, 0, Math.PI * 2, 0, Math.PI / 2).rotateX(-Math.PI / 2).scale(1, 1, 0.45).translate(0, a + 0.1, 0.38), 0xd8d8d2)],
  charger: () => [B(0.4, 1.5, 0.28, 0, 0, 0, 0x3a4a4f), B(0.22, 0.12, 0.02, 0, 1.2, 0.15, 0x56d26a), B(0.3, 0.4, 0.02, 0, 0.6, 0.15, 0x1d2226)],
  // freestanding kiosk: a=1 K-Kiosk red, else grey-green; sales window towards +z
  kiosk: (a) => {
    const w = a ? 0xb0282c : 0x8b9a8a;
    return [B(3.2, 2.5, 2.4, 0, 0, 0, w), B(3.8, 0.16, 3.0, 0, 2.5, 0, 0x3a3f44), B(2.4, 0.9, 0.05, 0, 1.0, 1.22, 0x1d2226), B(2.4, 0.06, 0.5, 0, 0.95, 1.4, 0x8a8d90), B(2.4, 0.4, 0.05, 0, 2.0, 1.25, a ? 0xf4f2ec : 0xe8e0c8)];
  },
  // gate across the line: a = width (m), b=1 wood; two leaves
  gate: (a, b) => {
    const W = a || 3, col = b ? 0x7a5636 : 0x3d4a42, p: G[] = [B(0.14, 1.9, 0.14, -W / 2, 0, 0, FIN), B(0.14, 1.9, 0.14, W / 2, 0, 0, FIN)];
    if (W > 1.6) p.push(B(W / 2 - 0.08, 1.5, 0.05, -W / 4, 0.2, 0, col), B(W / 2 - 0.08, 1.5, 0.05, W / 4, 0.2, 0, col));
    else p.push(B(W - 0.14, 1.3, 0.05, 0, 0.2, 0, col));
    return p;
  },
};

const HEDGE = [0x3a5a2c, 0x45622e, 0x2f4a26, 0x5a6230, 0x7a5a2a]; // look3: Liguster / Thuja / Buche
// segmented hedge box; fol = 1 above the ground so the vertex shader may roughen the top and sides
function hedgeBox(len: number, h: number, w: number, c: number): G {
  const g = new THREE.BoxGeometry(len, h, w, Math.max(1, Math.ceil(len / 0.6)), 3, 2).translate(0, h / 2, 0);
  const pg = paint(g.toNonIndexed(), c), pos = pg.getAttribute('position'), f = pg.getAttribute('fol') as THREE.BufferAttribute;
  for (let i = 0; i < pos.count; i++) f.setX(i, pos.getY(i) > 0.01 ? 1 : 0);
  return pg;
}
function line(l: DetailLine, out: G[]) {
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), s1 = new THREE.Vector3(1, 1, 1), up = new THREE.Vector3(0, 1, 0);
  const put = (gs: G[], x: number, y: number, z: number, yaw: number) => {
    m.compose(p.set(x, z, -y), q.setFromAxisAngle(up, yaw), s1);
    for (const g of gs) out.push(g.applyMatrix4(m));
  };
  for (let i = 0; i + 1 < l.pts.length; i++) {
    const a = l.pts[i], b = l.pts[i + 1], len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (len < 0.05) continue;
    const yaw = Math.atan2(b[1] - a[1], b[0] - a[0]), mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, mz = Math.min(a[2], b[2]), h = l.h;
    const r = rnd(mx, my);
    if (l.t === 'hedge') {
      put([hedgeBox(len + 0.1, h * (0.85 + 0.3 * r), l.w, HEDGE[Math.floor(r * 4.99) % (r > 0.9 ? 5 : 3)])], mx, my, mz, yaw);
    } else if (l.t === 'wood') {
      put([B(len, h, 0.04, 0, 0, 0, 0x8f6a42), B(0.1, h + 0.1, 0.1, -len / 2, 0, 0, 0x6f5232)], mx, my, mz, yaw);
    } else if (l.t === 'mesh') {
      const gs: G[] = [B(0.06, h, 0.06, -len / 2, 0, 0, 0x6d7377)];
      for (const f of [0.1, 0.4, 0.7, 1.0]) gs.push(B(len, 0.02, 0.02, 0, f * (h - 0.05), 0, 0x8a9094));
      put(gs, mx, my, mz, yaw);
    } else { // rail: dark metal fence, post + top and mid rail + bars thinned to a lower rail
      put([B(0.06, h, 0.06, -len / 2, 0, 0, 0x2e3235), B(len, 0.05, 0.04, 0, h - 0.05, 0, 0x2e3235), B(len, 0.04, 0.03, 0, 0.12, 0, 0x2e3235), B(len, 0.03, 0.03, 0, h * 0.5, 0, 0x2e3235)], mx, my, mz, yaw);
    }
  }
}

const LEAF = [0x9a6a2a, 0xc2a038, 0xb4532a];
function leaves(rows: number[][]): G {
  const n = rows.length * 3, pos = new Float32Array(n * 6 * 3), col = new Float32Array(n * 6 * 3), nor = new Float32Array(n * 6 * 3);
  const c = new THREE.Color();
  let o = 0;
  rows.forEach(([x, y, z, rot, ci], r) => {
    const R = (rot * Math.PI) / 180;
    for (let k = 0; k < 3; k++) {
      const ang = R + k * 1.3, dx = Math.cos(k * 2.1 + r) * 0.35, dy = Math.sin(k * 2.1 + r) * 0.35, w = 0.14, d = 0.09;
      const cs = Math.cos(ang), sn = Math.sin(ang);
      const P = (u: number, v: number) => [x + dx + u * cs - v * sn, z + 0.0 + k * 0.004, -(y + dy + u * sn + v * cs)];
      c.setHex(LEAF[(ci + (k === 2 ? 1 : 0)) % 3]).offsetHSL(0, 0, (rnd(x, y, k) - 0.5) * 0.12);
      for (const v of [P(-w, -d), P(w, -d), P(w, d), P(-w, -d), P(w, d), P(-w, d)]) {
        pos.set(v, o); col.set([c.r, c.g, c.b], o); nor.set([0, 1, 0], o); o += 3;
      }
    }
  });
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3)); g.setAttribute('fol', new THREE.BufferAttribute(new Float32Array(n * 6), 1));
  return g;
}

let mat: THREE.MeshLambertMaterial | undefined;
let detailsLite = false; export function setDetailsLite(v: boolean) { detailsLite = v; } // look3
const mkMat = () => { const m = new THREE.MeshLambertMaterial({ vertexColors: true }); foliagePatch(m, 'attr', detailsLite); return m; };
export function buildDetails(meta: DetailMeta | undefined, shadows: boolean): THREE.Object3D[] {
  if (!meta || (!meta.objs?.length && !meta.lines?.length && !meta.leaves?.length)) return [];
  const parts: G[] = [];
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), s = new THREE.Vector3(1, 1, 1), up = new THREE.Vector3(0, 1, 0);
  for (const [t, x, y, z, h, a, b, c] of meta.objs ?? []) {
    const f = T[t];
    if (!f) { console.warn('details: unknown type', t); continue; }
    m.compose(p.set(x, z, -y), q.setFromAxisAngle(up, h), s);
    for (const g of f(a, b, c, x, y)) parts.push(g.applyMatrix4(m));
  }
  for (const l of meta.lines ?? []) line(l, parts);
  const out: THREE.Object3D[] = [];
  if (parts.length) {
    const mesh = new THREE.Mesh(mergeGeometries(parts)!, (mat ??= mkMat()));
    parts.forEach((g) => g.dispose());
    mesh.castShadow = shadows; mesh.receiveShadow = shadows; out.push(mesh);
  }
  if (meta.leaves?.length) { // flat litter on the ground: no shadows
    const lm = new THREE.Mesh(leaves(meta.leaves), (mat ??= mkMat()));
    lm.receiveShadow = shadows; out.push(lm);
  }
  return out;
}
