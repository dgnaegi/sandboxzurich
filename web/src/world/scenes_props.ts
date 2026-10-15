import * as THREE from 'three';

/**
 * Small procedural props for the ambient scenes (no external models). Local frame: front = -z, up = +y.
 * Materials and geometries are shared; scenes only add meshes, so disposing a scene needs no cleanup.
 */
const mats = new Map<number, THREE.MeshLambertMaterial>();
export const lam = (c: number) => { let m = mats.get(c); if (!m) { m = new THREE.MeshLambertMaterial({ color: c }); mats.set(c, m); } return m; };
const geos = new Map<string, THREE.BufferGeometry>();
const box = (w: number, h: number, d: number) => { const k = `b${w},${h},${d}`; let g = geos.get(k); if (!g) { g = new THREE.BoxGeometry(w, h, d); geos.set(k, g); } return g; };
const cyl = (r: number, h: number, n = 10) => { const k = `c${r},${h},${n}`; let g = geos.get(k); if (!g) { g = new THREE.CylinderGeometry(r, r, h, n); geos.set(k, g); } return g; };
const sph = (r: number) => { const k = `s${r}`; let g = geos.get(k); if (!g) { g = new THREE.SphereGeometry(r, 10, 8); geos.set(k, g); } return g; };
const mesh = (g: THREE.BufferGeometry, c: number, x = 0, y = 0, z = 0) => { const m = new THREE.Mesh(g, lam(c)); m.position.set(x, y, z); return m; };

function textTexture(lines: string[], opts: { bg: string; fg: string; w: number; h: number; font?: string; size?: number; rot?: number }) {
  const c = document.createElement('canvas');
  c.width = opts.w; c.height = opts.h;
  const g = c.getContext('2d')!;
  g.fillStyle = opts.bg; g.fillRect(0, 0, opts.w, opts.h);
  g.fillStyle = opts.fg; g.textAlign = 'center'; g.textBaseline = 'middle';
  const size = opts.size ?? 34;
  lines.forEach((t, i) => {
    g.font = `${i === 0 ? size : size * 0.75}px ${opts.font ?? 'Anton, sans-serif'}`;
    g.save(); g.translate(opts.w / 2, opts.h / 2 + (i - (lines.length - 1) / 2) * size * 1.35); g.rotate(opts.rot ?? 0);
    g.fillText(t, 0, 0); g.restore();
  });
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/** Free-standing board; the readable face looks towards -z. */
export function signBoard(lines: string[], w = 0.8, h = 1.0): THREE.Object3D {
  const board = new THREE.Group();
  const front = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshLambertMaterial({ map: textTexture(lines, { bg: '#111', fg: '#fff', w: 256, h: 320, size: 34 }) }));
  front.position.set(0, 0.6 + h / 2, -0.02);
  front.rotation.y = Math.PI;
  board.add(front, mesh(box(w, h, 0.03), 0x222222, 0, 0.6 + h / 2, 0), mesh(box(0.05, 0.6, 0.05), 0x333333, 0, 0.3, 0));
  return board;
}

/** Concrete wall slab with a spray-paint message (fictional, tongue in cheek). */
export function graffitiWall(lines: string[], paint = '#ff3d7f'): THREE.Object3D {
  const g = new THREE.Group();
  g.add(mesh(box(3.0, 1.9, 0.2), 0x9a9a94, 0, 0.95, 0), mesh(box(3.2, 0.1, 0.3), 0x7c7c76, 0, 1.92, 0));
  const tex = textTexture(lines, { bg: '#9a9a94', fg: paint, w: 512, h: 320, size: 62, font: 'Anton, Impact, sans-serif', rot: -0.06 });
  const f = new THREE.Mesh(new THREE.PlaneGeometry(2.9, 1.8), new THREE.MeshLambertMaterial({ map: tex }));
  f.position.set(0, 0.95, -0.105); f.rotation.y = Math.PI;
  g.add(f);
  return g;
}

export function bikeProp(color = 0x2a6fb0, bag = false): THREE.Object3D {
  const b = new THREE.Group(), tire = new THREE.TorusGeometry(0.34, 0.025, 6, 16);
  for (const z of [-0.5, 0.5]) { const w = new THREE.Mesh(tire, lam(0x111111)); w.rotation.y = Math.PI / 2; w.position.set(0, 0.36, z); b.add(w); }
  const bar = mesh(box(0.04, 0.04, 1.0), color, 0, 0.62, 0), seat = mesh(box(0.1, 0.03, 0.2), 0x111111, 0, 0.78, 0.3);
  const fork = mesh(box(0.04, 0.4, 0.04), color, 0, 0.55, -0.46); fork.rotation.x = 0.3;
  const hbar = mesh(box(0.5, 0.03, 0.03), 0x222222, 0, 0.82, -0.52);
  b.add(bar, seat, fork, hbar);
  if (bag) b.add(mesh(box(0.34, 0.3, 0.22), 0xe8742a, 0, 0.62, 0.6)); // courier bag on the rear rack
  b.rotation.z = 0.12; // leaning
  return b;
}

export function cargoBike(): THREE.Object3D {
  const b = new THREE.Group(), tire = new THREE.TorusGeometry(0.3, 0.025, 6, 16);
  for (const z of [-1.1, 0.55]) { const w = new THREE.Mesh(tire, lam(0x111111)); w.rotation.y = Math.PI / 2; w.position.set(0, 0.32, z); b.add(w); }
  b.add(mesh(box(0.04, 0.04, 1.7), 0x2f7a5a, 0, 0.55, -0.3), mesh(box(0.1, 0.03, 0.2), 0x111111, 0, 0.8, 0.35), mesh(box(0.5, 0.03, 0.03), 0x222222, 0, 0.85, 0.5));
  const cargo = new THREE.Group();
  cargo.add(mesh(box(0.7, 0.04, 0.9), 0x8a6a3a, 0, 0.3, 0), mesh(box(0.04, 0.35, 0.9), 0x8a6a3a, -0.33, 0.48, 0), mesh(box(0.04, 0.35, 0.9), 0x8a6a3a, 0.33, 0.48, 0),
    mesh(box(0.7, 0.35, 0.04), 0x8a6a3a, 0, 0.48, -0.43), mesh(box(0.7, 0.35, 0.04), 0x8a6a3a, 0, 0.48, 0.43));
  cargo.position.z = -0.7; b.add(cargo);
  return b;
}

export function pingpongTable(): THREE.Object3D {
  const t = new THREE.Group();
  t.add(mesh(box(1.5, 0.05, 2.7), 0x3d6b4f, 0, 0.76, 0), mesh(box(1.5, 0.06, 0.02), 0xdddddd, 0, 0.8, 0), mesh(box(0.02, 0.01, 2.7), 0xdddddd, 0, 0.79, 0));
  // concrete park table: slab + net of steel
  t.add(mesh(box(1.6, 0.16, 0.08), 0x888880, 0, 0.84, 0));
  for (const x of [-0.6, 0.6]) for (const z of [-1.1, 1.1]) t.add(mesh(box(0.1, 0.74, 0.1), 0x6e6e68, x, 0.37, z));
  return t;
}

export function towel(color: number, w = 0.9, d = 1.8): THREE.Object3D {
  const g = new THREE.Group();
  g.add(mesh(box(w, 0.015, d), color, 0, 0.01, 0), mesh(box(w, 0.016, 0.1), 0xffffff, 0, 0.012, d * 0.3), mesh(box(w, 0.016, 0.1), 0xffffff, 0, 0.012, d * 0.36));
  return g;
}

export function parasol(color = 0xe0b040): THREE.Object3D {
  const g = new THREE.Group();
  const top = new THREE.Mesh(new THREE.ConeGeometry(1.1, 0.4, 10), lam(color)); top.position.y = 2.1;
  g.add(mesh(cyl(0.02, 2.1, 6), 0xdddddd, 0, 1.05, 0), top);
  g.rotation.z = 0.12;
  return g;
}

export function flag(color: number): THREE.Object3D {
  const g = new THREE.Group();
  g.add(mesh(cyl(0.015, 2.2, 6), 0x555555, 0, 1.1, 0), mesh(box(0.5, 0.3, 0.01), color, 0.26, 2.0, 0));
  return g;
}

export function vinylStall(): THREE.Object3D {
  const g = new THREE.Group();
  g.add(mesh(box(2.0, 0.05, 0.8), 0x7a5a3a, 0, 0.85, 0), mesh(box(0.06, 0.85, 0.06), 0x5a4a3a, -0.95, 0.42, -0.35), mesh(box(0.06, 0.85, 0.06), 0x5a4a3a, 0.95, 0.42, -0.35),
    mesh(box(0.06, 0.85, 0.06), 0x5a4a3a, -0.95, 0.42, 0.35), mesh(box(0.06, 0.85, 0.06), 0x5a4a3a, 0.95, 0.42, 0.35));
  const cols = [0xc8443a, 0x2f6b9a, 0xe0b040, 0x3a8a5a, 0x8a4aa0, 0xf0f0e0];
  for (let i = 0; i < 2; i++) { // two crates with record sleeves
    const crate = new THREE.Group(); crate.add(mesh(box(0.7, 0.28, 0.4), 0x3a2e24, 0, 0.14, 0));
    for (let k = 0; k < 7; k++) { const s = mesh(box(0.02, 0.32, 0.31), cols[(k + i * 3) % 6], -0.3 + k * 0.1, 0.3, 0); s.rotation.z = (k % 2 ? 0.1 : -0.06); crate.add(s); }
    crate.position.set(-0.5 + i * 1.0, 0.875, 0); g.add(crate);
  }
  return g;
}

export function boule(color: number): THREE.Mesh { return mesh(sph(0.04), color, 0, 0.04, 0); }

export function duck(): THREE.Object3D {
  const d = new THREE.Group();
  d.add(mesh(sph(0.09), 0xffd21f, 0, 0.09, 0), mesh(sph(0.055), 0xffd21f, 0, 0.2, -0.07), mesh(box(0.05, 0.02, 0.05), 0xff8a1f, 0, 0.19, -0.13));
  return d;
}

export function pigeon(): THREE.Group {
  const p = new THREE.Group(), head = mesh(sph(0.035), 0x6c6f78, 0, 0.17, -0.1);
  p.add(mesh(sph(0.075), 0x8a8d96, 0, 0.1, 0), head, mesh(box(0.06, 0.02, 0.14), 0x6c6f78, 0, 0.1, 0.1), mesh(box(0.02, 0.06, 0.02), 0xc07070, 0, 0.03, 0));
  p.userData.head = head;
  return p;
}

export function movingBoxes(): THREE.Object3D {
  const g = new THREE.Group(), cols = [0xb08a58, 0xa07a48, 0xc09a68];
  [[0, 0, 0, 0.6, 0.45], [0.65, 0, 0.05, 0.5, 0.4], [0.2, 0.45, 0, 0.5, 0.4], [-0.7, 0, 0.1, 0.55, 0.5]].forEach(([x, y, z, w, h], i) => g.add(mesh(box(w, h, 0.5), cols[i % 3], x, y + h / 2, z)));
  const sofa = new THREE.Group(); // the sofa that does not fit through the stairwell
  sofa.add(mesh(box(1.9, 0.4, 0.8), 0x4a6a8a, 0, 0.3, 0), mesh(box(1.9, 0.45, 0.2), 0x405c78, 0, 0.62, 0.3), mesh(box(0.2, 0.3, 0.8), 0x405c78, -0.85, 0.5, 0), mesh(box(0.2, 0.3, 0.8), 0x405c78, 0.85, 0.5, 0));
  sofa.position.set(2.0, 0, 0.2); sofa.rotation.y = 0.3; g.add(sofa);
  return g;
}

export function foosball(): THREE.Object3D {
  const t = new THREE.Group();
  t.add(mesh(box(0.7, 0.14, 1.25), 0x2e6b3a, 0, 0.9, 0), mesh(box(0.74, 0.08, 1.3), 0x5a3a26, 0, 0.82, 0));
  for (const [x, z] of [[-0.33, -0.6], [0.33, -0.6], [-0.33, 0.6], [0.33, 0.6]]) t.add(mesh(box(0.06, 0.8, 0.06), 0x3a2a1c, x, 0.4, z));
  for (const z of [-0.4, -0.13, 0.13, 0.4]) t.add(mesh(cyl(0.01, 1.1, 5), 0xcccccc, 0, 1.0, z).rotateZ(Math.PI / 2));
  return t;
}

export function menuBoard(lines: string[]): THREE.Object3D {
  const g = new THREE.Group();
  const f = new THREE.Mesh(new THREE.PlaneGeometry(0.6, 0.85), new THREE.MeshLambertMaterial({ map: textTexture(lines, { bg: '#26332b', fg: '#f4efe0', w: 256, h: 360, size: 30, font: 'Georgia, serif' }) }));
  f.position.set(0, 0.55, -0.02); f.rotation.y = Math.PI;
  g.add(f, mesh(box(0.64, 0.9, 0.03), 0x7a5a3a, 0, 0.55, 0), mesh(box(0.05, 0.1, 0.05), 0x7a5a3a, -0.25, 0.05, 0.05), mesh(box(0.05, 0.1, 0.05), 0x7a5a3a, 0.25, 0.05, 0.05));
  return g;
}

export function miniBoegg(scale = 0.3): THREE.Object3D {
  const g = new THREE.Group(), white = lam(0xf4f4f0);
  for (const [r, yy] of [[0.55, 0.5], [0.42, 1.3], [0.3, 1.92]]) { const b = new THREE.Mesh(sph(r), white); b.position.y = yy; g.add(b); }
  g.add(mesh(cyl(0.22, 0.35, 12), 0x111111, 0, 2.32, 0));
  const nose = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.25, 8), lam(0xe0782a)); nose.rotation.x = -Math.PI / 2; nose.position.set(0, 1.95, -0.3); g.add(nose);
  g.scale.setScalar(scale);
  return g;
}

export function chocBox(): THREE.Object3D {
  const box1 = mesh(box(0.3, 0.12, 0.2), 0xf2a6c4, 0, 0.5, 0);
  box1.add(mesh(box(0.31, 0.02, 0.21), 0xffffff, 0, 0.07, 0));
  return box1;
}

export function barrier(): THREE.Object3D {
  const g = new THREE.Group();
  for (const x of [-0.6, 0.6]) g.add(mesh(cyl(0.025, 0.95, 6), 0x2a2a2a, x, 0.47, 0), mesh(cyl(0.12, 0.03, 10), 0x2a2a2a, x, 0.015, 0));
  const rope = mesh(box(1.2, 0.04, 0.04), 0x9a1f2a, 0, 0.85, 0); g.add(rope);
  return g;
}

export function glove(): THREE.Object3D {
  const g = new THREE.Group();
  g.add(mesh(box(0.1, 0.02, 0.14), 0xd04a4a, 0, 0.012, 0));
  for (let i = 0; i < 4; i++) g.add(mesh(box(0.02, 0.018, 0.07), 0xd04a4a, -0.04 + i * 0.027, 0.012, -0.1));
  return g;
}

export function planter(): THREE.Object3D {
  const g = new THREE.Group();
  g.add(mesh(cyl(0.3, 0.4, 10), 0x9a5a3a, 0, 0.2, 0), mesh(cyl(0.28, 0.04, 10), 0x4a3a2a, 0, 0.4, 0));
  for (let i = 0; i < 5; i++) g.add(mesh(sph(0.1), [0xe05a8a, 0xf0c030, 0xffffff][i % 3], Math.cos(i * 1.3) * 0.14, 0.6 + (i % 2) * 0.1, Math.sin(i * 1.3) * 0.14));
  return g;
}

export function plaque(lines: string[]): THREE.Object3D {
  const g = new THREE.Group();
  const f = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.32), new THREE.MeshLambertMaterial({ map: textTexture(lines, { bg: '#2d3a4a', fg: '#f2f2f2', w: 320, h: 200, size: 30, font: 'Arial, sans-serif' }) }));
  f.position.set(0, 0.9, -0.025); f.rotation.y = Math.PI;
  g.add(mesh(cyl(0.025, 0.75, 6), 0x555555, 0, 0.375, 0), mesh(box(0.54, 0.36, 0.04), 0x222a34, 0, 0.9, 0), f);
  return g;
}

/** Frees what a scene created itself (canvas textures, per-call geometries); shared cached geometries and materials stay. */
export function disposeObject(o: THREE.Object3D) {
  const shared = new Set<THREE.BufferGeometry>(geos.values());
  o.traverse((c) => {
    const m = c as THREE.Mesh;
    if (!m.isMesh) return;
    const mat = m.material as THREE.MeshLambertMaterial;
    if (mat.map) { mat.map.dispose(); mat.dispose(); }
    if (!shared.has(m.geometry)) m.geometry.dispose();
  });
}
