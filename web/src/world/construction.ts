import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/**
 * Construction sites (rows [x, y, z, tx, ty, width, height]): facade scaffolding with green debris net,
 * site fence with banner, skip, and a «Baustelle» sign. Plus shared e-scooters ([x, y, z, heading, colour]).
 */
const C = (h: number) => new THREE.Color(h);
function part(g: THREE.BufferGeometry, c: THREE.Color) {
  g = g.index ? g.toNonIndexed() : g;
  g.deleteAttribute('uv');
  const n = g.getAttribute('position').count;
  g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(n * 3).map((_, i) => [c.r, c.g, c.b][i % 3]), 3));
  return g;
}
const mat = new THREE.MeshLambertMaterial({ vertexColors: true });
const netMat = new THREE.MeshLambertMaterial({ color: 0x2f7a3a, transparent: true, opacity: 0.55, side: THREE.DoubleSide, depthWrite: false });
let bannerTex: THREE.Texture | null = null;
function banner() {
  const c = document.createElement('canvas'); c.width = 512; c.height = 96;
  const g = c.getContext('2d')!;
  g.fillStyle = '#f2f2ee'; g.fillRect(0, 0, 512, 96);
  g.fillStyle = '#d0202a'; g.font = '56px Anton, sans-serif'; g.textAlign = 'center'; g.fillText('BAUSTELLE', 256, 70);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export function buildConstruction(rows: number[][]): THREE.Object3D[] {
  if (!rows.length) return [];
  bannerTex ??= banner();
  const parts: THREE.BufferGeometry[] = [], nets: THREE.BufferGeometry[] = [], banners: THREE.BufferGeometry[] = [];
  const steel = C(0x9aa0a4), plank = C(0x8a6a44), red = C(0xc8202a), white = C(0xf0f0ea), skip = C(0x4a6a8a);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1);
  for (const [x, y, z, tx, ty, w, h] of rows) {
    const ox = ty, oy = -tx, yaw = Math.atan2(tx, ty) - Math.PI / 2; // local +x along the facade, +z away from it
    m.compose(p.set(x, z, -y), q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), -yaw), one);
    const local: THREE.BufferGeometry[] = [];
    const bays = Math.max(2, Math.round(w / 2.5));
    for (let i = 0; i <= bays; i++) {
      const u = -w / 2 + (w * i) / bays;
      for (const d of [0.25, 1.15]) local.push(part(new THREE.CylinderGeometry(0.025, 0.025, h, 5).translate(u, h / 2, d), steel));
    }
    for (let lv = 2; lv < h; lv += 2) {
      for (const d of [0.25, 1.15]) local.push(part(new THREE.BoxGeometry(w, 0.05, 0.05).translate(0, lv, d), steel));
      local.push(part(new THREE.BoxGeometry(w, 0.04, 0.8).translate(0, lv - 0.05, 0.7), plank));
    }
    // site fence 2.5 m in front, banner, skip and sign
    for (let i = 0; i < Math.ceil(w / 3.5); i++) local.push(part(new THREE.BoxGeometry(3.4, 2.0, 0.04).translate(-w / 2 + 1.75 + i * 3.5, 1.0, 3.2), C(0xb0b6ba)));
    local.push(part(new THREE.BoxGeometry(3.4, 1.2, 1.8).translate(w / 2 - 2, 0.6, 5.2), skip));
    local.push(part(new THREE.CylinderGeometry(0.03, 0.03, 1.6, 5).translate(-w / 2 - 0.5, 0.8, 3.6), steel));
    local.push(part(new THREE.CircleGeometry(0.32, 3).rotateZ(Math.PI / 2).translate(-w / 2 - 0.5, 1.75, 3.62), red));
    local.push(part(new THREE.CircleGeometry(0.24, 3).rotateZ(Math.PI / 2).translate(-w / 2 - 0.5, 1.75, 3.63), white));
    for (const g of local) parts.push(g.applyMatrix4(m));
    nets.push(new THREE.PlaneGeometry(w, h).translate(0, h / 2, 1.3).applyMatrix4(m));
    banners.push(new THREE.PlaneGeometry(3.0, 0.56).translate(-w / 2 + 1.75, 1.5, 3.23).applyMatrix4(m));
    void ox; void oy;
  }
  return [new THREE.Mesh(mergeGeometries(parts)!, mat), new THREE.Mesh(mergeGeometries(nets)!, netMat),
    new THREE.Mesh(mergeGeometries(banners)!, new THREE.MeshLambertMaterial({ map: bannerTex }))];
}

const scooterGeo = mergeGeometries([
  part(new THREE.BoxGeometry(0.16, 0.05, 0.85).translate(0, 0.1, 0), C(0x222426)),
  part(new THREE.CylinderGeometry(0.02, 0.02, 1.05, 5).translate(0, 0.62, -0.4), C(0x2a2c2e)),
  part(new THREE.BoxGeometry(0.45, 0.03, 0.03).translate(0, 1.14, -0.4), C(0x2a2c2e)),
  part(new THREE.CylinderGeometry(0.1, 0.1, 0.05, 10).rotateZ(Math.PI / 2).translate(0, 0.1, -0.45), C(0x111111)),
  part(new THREE.CylinderGeometry(0.1, 0.1, 0.05, 10).rotateZ(Math.PI / 2).translate(0, 0.1, 0.42), C(0x111111)),
])!;
const SCOOTER_COLS = [0x1fae5a, 0x2f6fd6, 0xe8e8e2].map((c) => new THREE.Color(c));
const scooterMat = new THREE.MeshLambertMaterial({ vertexColors: true });

export function buildScooters(rows: number[][]): THREE.Object3D[] {
  if (!rows.length) return [];
  const im = new THREE.InstancedMesh(scooterGeo, scooterMat, rows.length);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), s = new THREE.Vector3(1, 1, 1);
  const lean = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), 0.18); // on the kickstand
  rows.forEach(([x, y, z, h, c], i) => {
    q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), -h).multiply(lean);
    im.setMatrixAt(i, m.compose(p.set(x, z, -y), q, s));
    im.setColorAt(i, SCOOTER_COLS[c % SCOOTER_COLS.length]);
  });
  im.computeBoundingSphere();
  return [im];
}

/** Construction fence closing the playable map: panels along polylines [[x, y, z], ...] with banners and blinkers. */
let fenceBanner: THREE.Texture | null = null;
export function buildFence(lines: number[][][]): THREE.Object3D[] {
  if (!lines.length) return [];
  fenceBanner ??= (() => {
    const c = document.createElement('canvas'); c.width = 512; c.height = 128;
    const g = c.getContext('2d')!;
    g.fillStyle = '#f4f2ea'; g.fillRect(0, 0, 512, 128);
    for (let x = -128; x < 512; x += 64) { g.fillStyle = '#d0202a'; g.beginPath(); g.moveTo(x, 128); g.lineTo(x + 32, 128); g.lineTo(x + 96, 64); g.lineTo(x + 64, 64); g.fill(); }
    g.fillStyle = '#111'; g.font = '40px Anton, sans-serif'; g.textAlign = 'center'; g.fillText('BAUSTELLE – DURCHGANG GESPERRT', 256, 46);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
  })();
  const panels: THREE.BufferGeometry[] = [], banners: THREE.BufferGeometry[] = [];
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1), Y = new THREE.Vector3(0, 1, 0);
  for (const line of lines) for (let i = 0; i + 1 < line.length; i++) {
    const [ax, ay, az] = line[i], [bx, by, bz] = line[i + 1], len = Math.hypot(bx - ax, by - ay);
    if (len < 0.3) continue;
    m.compose(p.set((ax + bx) / 2, (az + bz) / 2, -(ay + by) / 2), q.setFromAxisAngle(Y, Math.atan2(by - ay, bx - ax)), one);
    panels.push(part(new THREE.BoxGeometry(len, 2.0, 0.05).translate(0, 1.0, 0), C(0xaeb4b8)).applyMatrix4(m));
    panels.push(part(new THREE.BoxGeometry(0.6, 0.15, 0.25).translate(-len / 2, 0.08, 0), C(0x3a3d40)).applyMatrix4(m)); // concrete foot
    if (i % 3 === 0) banners.push(new THREE.PlaneGeometry(Math.min(len, 3.2), 0.8).translate(0, 1.3, 0.04).applyMatrix4(m),
      new THREE.PlaneGeometry(Math.min(len, 3.2), 0.8).rotateY(Math.PI).translate(0, 1.3, -0.04).applyMatrix4(m));
    if (i % 4 === 0) panels.push(part(new THREE.CylinderGeometry(0.09, 0.09, 0.12, 8).translate(-len / 2, 2.1, 0), C(0xffb000)).applyMatrix4(m)); // warning light
  }
  const out: THREE.Object3D[] = [new THREE.Mesh(mergeGeometries(panels)!, mat)];
  if (banners.length) out.push(new THREE.Mesh(mergeGeometries(banners)!, new THREE.MeshLambertMaterial({ map: fenceBanner })));
  return out;
}
