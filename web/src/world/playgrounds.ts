import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
/** Playground equipment (pipeline/playgrounds.py). Rows [x, y, z, heading, type]; one merged vertex-coloured mesh per tile.
 *  Local (x east, y north, z up) -> Three (x, z, -y). Equipment is built along local +x, rotated by heading. */
export type PlaygroundRow = [number, number, number, number, string];

const WOOD = 0x9a6b3f, STEEL = 0x8c9399, RED = 0xd8322a, YEL = 0xf2c230, BLUE = 0x2f7fd0, GREEN = 0x3fa34d, SAND = 0xd9c79a, BLACK = 0x222222;
const COLS = [RED, YEL, BLUE, GREEN];

function col(g: THREE.BufferGeometry, c: number): THREE.BufferGeometry {
  g = g.index ? g.toNonIndexed() : g;
  const n = g.getAttribute('position').count, cc = new THREE.Color(c);
  g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(n * 3).map((_, i) => [cc.r, cc.g, cc.b][i % 3]), 3));
  for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal' && k !== 'color') g.deleteAttribute(k);
  return g;
}
const box = (w: number, h: number, d: number, x: number, y: number, z: number, c: number, rx = 0, rz = 0) => {
  const g = new THREE.BoxGeometry(w, h, d);
  if (rx) g.rotateX(rx);
  if (rz) g.rotateZ(rz);
  g.translate(x, y, z);
  return col(g, c);
};
const post = (x: number, z: number, h: number, c = WOOD, r = 0.06, tilt = 0) => {
  const g = new THREE.CylinderGeometry(r, r, h, 6);
  g.translate(0, h / 2, 0);
  if (tilt) g.rotateZ(tilt);
  g.translate(x, 0, z);
  return col(g, c);
};

/** Templates in Three axes (y up), centred on the origin, long side along x. */
const T: Record<string, (k: number) => THREE.BufferGeometry[]> = {
  swing: (k) => {
    const p: THREE.BufferGeometry[] = [];
    for (const sx of [-1.6, 1.6]) for (const sz of [-0.7, 0.7]) p.push(post(sx, sz * 0.2, 2.5, WOOD, 0.07, -sx * 0.06 * Math.sign(sz) * 0));
    p.push(box(3.4, 0.14, 0.14, 0, 2.45, 0, WOOD));
    for (const sx of [-0.7, 0.7]) {
      for (const dz of [-0.2, 0.2]) p.push(box(0.02, 1.9, 0.02, sx, 1.45, dz, STEEL));
      p.push(box(0.45, 0.04, 0.18, sx, 0.5, 0, COLS[k % 4]));
    }
    p.push(box(3.2, 0.03, 1.6, 0, 0.02, 0, SAND));
    return p;
  },
  basketswing: (k) => {
    const p = [post(-1.5, 0, 2.6, STEEL), post(1.5, 0, 2.6, STEEL), box(3.2, 0.1, 0.1, 0, 2.6, 0, STEEL)];
    const nest = new THREE.TorusGeometry(0.55, 0.07, 5, 12);
    nest.rotateX(Math.PI / 2); nest.translate(0, 0.6, 0);
    p.push(col(nest, COLS[(k + 1) % 4]));
    for (const a of [0, 2.1, 4.2]) p.push(box(0.02, 2.0, 0.02, Math.cos(a) * 0.3, 1.6, Math.sin(a) * 0.3, BLACK));
    return p;
  },
  slide: (k) => [
    box(1.0, 0.08, 1.0, -1.2, 1.4, 0, WOOD), ...[[-1.65, -0.45], [-0.75, -0.45], [-1.65, 0.45], [-0.75, 0.45]].map(([x, z]) => post(x, z, 1.9)),
    box(0.9, 0.5, 0.06, -1.2, 1.7, -0.48, COLS[k % 4]), box(0.9, 0.5, 0.06, -1.2, 1.7, 0.48, COLS[k % 4]),
    box(2.5, 0.06, 0.55, 0.35, 0.78, 0, COLS[(k + 2) % 4], 0, -0.55),
    box(2.5, 0.25, 0.05, 0.35, 0.9, -0.28, COLS[(k + 2) % 4], 0, -0.55), box(2.5, 0.25, 0.05, 0.35, 0.9, 0.28, COLS[(k + 2) % 4], 0, -0.55),
    ...[0.35, 0.75, 1.15].map((y) => box(0.06, 0.05, 0.6, -2.0 + y * 0.12, y, 0, WOOD)),
  ],
  sandpit: () => [box(3.2, 0.3, 3.2, 0, 0.15, 0, WOOD), box(2.95, 0.31, 2.95, 0, 0.16, 0, SAND), box(0.5, 0.2, 0.3, 0.6, 0.38, 0.4, RED), box(0.25, 0.25, 0.25, -0.7, 0.4, -0.5, YEL)],
  climb: (k) => {
    const p: THREE.BufferGeometry[] = [];
    for (const x of [-1.8, -0.6, 0.6, 1.8]) p.push(post(x, -0.9, 2.3, STEEL, 0.05), post(x, 0.9, 2.3, STEEL, 0.05));
    for (const y of [0.6, 1.2, 1.8, 2.3]) p.push(box(3.6, 0.05, 0.05, 0, y, -0.9, STEEL), box(3.6, 0.05, 0.05, 0, y, 0.9, STEEL));
    for (const x of [-1.2, 0, 1.2]) p.push(box(0.05, 0.05, 1.8, x, 2.3, 0, COLS[k % 4]));
    p.push(box(1.2, 0.06, 1.8, 0.6, 1.2, 0, WOOD));
    return p;
  },
  seesaw: (k) => [box(0.25, 0.5, 0.25, 0, 0.25, 0, STEEL), box(3.2, 0.08, 0.28, 0, 0.55, 0, COLS[k % 4], 0, 0.12),
    box(0.06, 0.3, 0.4, -1.3, 0.55, 0, BLACK, 0, 0.12), box(0.06, 0.3, 0.4, 1.3, 0.85, 0, BLACK, 0, 0.12)],
  springy: (k) => {
    const s = new THREE.CylinderGeometry(0.12, 0.12, 0.45, 8); s.translate(0, 0.22, 0);
    const b = new THREE.SphereGeometry(0.28, 8, 6); b.scale(1.5, 0.8, 0.7); b.translate(0, 0.65, 0);
    return [col(s, STEEL), col(b, COLS[k % 4]), box(0.06, 0.25, 0.35, 0.25, 0.9, 0, BLACK)];
  },
  roundabout: (k) => {
    const d = new THREE.CylinderGeometry(1.2, 1.2, 0.1, 14); d.translate(0, 0.3, 0);
    return [col(d, COLS[k % 4]), post(0, 0, 1.0, STEEL, 0.05), box(2.2, 0.05, 0.05, 0, 0.95, 0, STEEL), box(0.05, 0.05, 2.2, 0, 0.95, 0, STEEL)];
  },
  tower: (k) => {
    const p = [...[[-1, -1], [1, -1], [-1, 1], [1, 1]].map(([x, z]) => post(x, z, 3.2, WOOD, 0.08)), box(2.2, 0.08, 2.2, 0, 1.5, 0, WOOD)];
    const roof = new THREE.ConeGeometry(1.6, 1.0, 4); roof.rotateY(Math.PI / 4); roof.translate(0, 3.6, 0);
    p.push(col(roof, COLS[k % 4]), box(2.0, 0.06, 0.6, 2.0, 0.8, 0, COLS[(k + 1) % 4], 0, -0.6), box(0.06, 0.6, 2.1, -1.05, 1.85, 0, WOOD));
    return p;
  },
  playhouse: (k) => {
    const roof = new THREE.ConeGeometry(1.3, 0.8, 4); roof.rotateY(Math.PI / 4); roof.translate(0, 1.75, 0);
    return [box(1.8, 1.35, 1.6, 0, 0.68, 0, WOOD), box(0.5, 0.9, 0.05, 0, 0.45, 0.81, BLACK), col(roof, COLS[k % 4])];
  },
};

let mat: THREE.MeshLambertMaterial | undefined;
export function buildPlaygrounds(rows: PlaygroundRow[]): THREE.Object3D[] {
  if (!rows.length) return [];
  const parts: THREE.BufferGeometry[] = [];
  rows.forEach(([x, y, z, h, type], i) => {
    const f = T[type];
    if (!f) return;
    for (const g of f(i + Math.floor(Math.abs(x * 7 + y * 3)))) {
      g.rotateY(h);
      g.translate(x, z, -y);
      parts.push(g);
    }
  });
  if (!parts.length) return [];
  const geo = mergeGeometries(parts)!;
  parts.forEach((p) => p.dispose());
  const m = new THREE.Mesh(geo, (mat ??= new THREE.MeshLambertMaterial({ vertexColors: true })));
  m.castShadow = true;
  m.receiveShadow = true;
  return [m];
}
