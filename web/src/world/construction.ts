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


/* ---------- real sites (pipeline/sites.py): rows [type, x, y, z, yaw, a, b] ---------- */
const box = (w: number, h: number, d: number, x: number, y: number, z: number, c: THREE.Color) => part(new THREE.BoxGeometry(w, h, d).translate(x, y, z), c);
const merged = (l: THREE.BufferGeometry[]) => mergeGeometries(l)!;
const ORANGE = C(0xff6a10), WHITE = C(0xf0f0ea), RED = C(0xc8202a), DARK = C(0x2a2c2e), GREY = C(0xaeb4b8), YEL = C(0xe8b020);
const CONTAINERS = [C(0x3a6a9a), C(0x8a8f94), C(0x5a7a4a), C(0xc8c8c0)];
const TPL: (THREE.BufferGeometry | ((a: number, b: number) => THREE.BufferGeometry))[] = [
  /* 0 cone */ merged([part(new THREE.ConeGeometry(0.11, 0.55, 5, 1, true).translate(0, 0.3, 0), ORANGE), box(0.32, 0.03, 0.32, 0, 0.015, 0, DARK)]),
  /* 1 barrier */ merged([box(0.05, 1.0, 0.4, -0.85, 0.5, 0, GREY), box(0.05, 1.0, 0.4, 0.85, 0.5, 0, GREY), box(1.0, 0.2, 0.04, -0.5, 0.9, 0, RED), box(1.0, 0.2, 0.04, 0.5, 0.9, 0, WHITE)]),
  /* 2 excavator */ merged([box(3.0, 0.5, 0.7, 0, 0.25, -0.85, DARK), box(3.0, 0.5, 0.7, 0, 0.25, 0.85, DARK), box(2.2, 0.9, 2.2, 0, 0.95, 0, YEL), box(1.0, 1.1, 1.2, -0.5, 1.95, -0.2, C(0x3a4650)), box(1.0, 0.15, 1.2, -0.5, 2.55, -0.2, YEL),
    part(new THREE.BoxGeometry(3.4, 0.28, 0.3).rotateZ(0.5).translate(2.4, 2.1, 0), YEL), part(new THREE.BoxGeometry(2.2, 0.22, 0.25).rotateZ(-0.9).translate(4.7, 2.2, 0), YEL), box(0.7, 0.5, 0.8, 5.6, 1.2, 0, DARK)]),
  /* 3 container */ (a, b) => merged([box(6.0, 2.4, 2.4, 0, 1.2, 0, CONTAINERS[(Math.abs(Math.floor(a * 7 + b)) + 1) % 4]), box(6.1, 0.08, 2.5, 0, 2.43, 0, DARK), box(0.5, 1.4, 0.05, 2.0, 1.1, 1.22, DARK)]),
  /* 4 fence */ merged([box(3.0, 1.9, 0.04, 0, 1.0, 0, GREY), box(0.5, 0.12, 0.5, -1.4, 0.06, 0, DARK), box(0.5, 0.12, 0.5, 1.4, 0.06, 0, DARK)]),
  /* 5 sign */ merged([box(0.05, 2.1, 0.05, 0, 1.05, 0, GREY), part(new THREE.CircleGeometry(0.4, 3).rotateZ(Math.PI / 2).translate(0, 2.0, 0.04), RED), part(new THREE.CircleGeometry(0.3, 3).rotateZ(Math.PI / 2).translate(0, 1.99, 0.05), WHITE),
    part(new THREE.CircleGeometry(0.4, 3).rotateZ(Math.PI / 2).rotateY(Math.PI).translate(0, 2.0, -0.04), RED), box(0.7, 0.2, 0.03, 0, 1.45, 0.04, YEL)]),
  /* 6 blinker */ merged([box(0.04, 1.3, 0.04, 0, 0.65, 0, GREY), box(0.2, 0.2, 0.2, 0, 1.4, 0, C(0xffb000))]),
  /* 7 trench */ (a, b) => merged([box(a, 0.06, b, 0, 0.1, 0, C(0x3b3028)), box(a * 0.45, 0.04, b * 0.9, -a * 0.2, 0.13, 0, C(0x7a8086)), box(a * 0.3, 0.05, b * 0.9, a * 0.28, 0.13, 0, C(0x5a4a3a))]),
  /* 8 pile */ (a) => part(new THREE.ConeGeometry(1.4 * a, 1.2 * a, 7).translate(0, 0.6 * a, 0), C(0x8a7a62)),
  /* 9 toilet */ merged([box(1.1, 2.3, 1.1, 0, 1.15, 0, C(0x2a6a9a)), box(1.15, 0.08, 1.15, 0, 2.32, 0, WHITE)]),
  /* 10 pallet */ merged([box(1.2, 0.15, 0.8, 0, 0.08, 0, C(0x8a6a44)), box(1.1, 0.9, 0.7, 0, 0.6, 0, C(0xa4503a))]),
];
let atlasTex: THREE.Texture | null = null;
const BANNERS = [['BAUSTELLE', ''], ['HIER ENTSTEHT: LUXUS-WOHNEN', 'ab CHF 6\'800.– pro Monat'], ['ZUTRITT VERBOTEN', 'Eltern haften nicht für ihre Kinder. Wir auch nicht.'],
  ['WIR BAUEN FÜR SIE*', '*Renditeobjekt, Besichtigung nur mit Anwalt'], ['TOTALSANIERUNG', 'Wir danken für Ihr Verständnis. Kündigungen sind verschickt.']];
function atlas() {
  const c = document.createElement('canvas'); c.width = 512; c.height = 128 * BANNERS.length;
  const g = c.getContext('2d')!;
  BANNERS.forEach(([t, s], i) => {
    const y = i * 128;
    g.fillStyle = i === 0 ? '#f2f2ee' : ['#f2f2ee', '#1f3a52', '#e8c820', '#2a2a2a', '#f2f2ee'][i]; g.fillRect(0, y, 512, 128);
    const dark = i === 1 || i === 3;
    g.fillStyle = i === 0 ? '#d0202a' : dark ? '#f4f4ee' : '#111'; g.font = `${t.length > 16 ? 40 : 60}px Anton, sans-serif`; g.textAlign = 'center';
    g.fillText(t, 256, y + (s ? 58 : 84), 490);
    g.font = '24px sans-serif'; g.fillText(s, 256, y + 100, 490);
  });
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const glowMat = new THREE.MeshBasicMaterial({ color: 0xffa000 });

export function buildSites(rows: number[][]): THREE.Object3D[] {
  if (!rows.length) return [];
  const parts: THREE.BufferGeometry[] = [], banners: THREE.BufferGeometry[] = [], glow: THREE.BufferGeometry[] = [];
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1), Y = new THREE.Vector3(0, 1, 0);
  const cache: (THREE.BufferGeometry | null)[] = [];
  for (const [t, x, y, z, yaw, a, b] of rows) {
    m.compose(p.set(x, z, -y), q.setFromAxisAngle(Y, yaw), one);
    const tp = TPL[t];
    const g = (typeof tp === 'function' ? tp(t === 3 ? x : a, t === 3 ? y : b) : (cache[t] ??= tp)).clone().applyMatrix4(m);
    if (t === 6) { glow.push(new THREE.BoxGeometry(0.22, 0.22, 0.22).translate(0, 1.4, 0).applyMatrix4(m)); continue; }
    parts.push(g);
    if (t === 4 && a >= 0) {
      const v0 = 1 - (a + 1) / BANNERS.length, v1 = 1 - a / BANNERS.length;
      for (const s of [1, -1]) {
        const pl = new THREE.PlaneGeometry(2.8, 0.7);
        const uv = pl.getAttribute('uv'); for (let i = 0; i < uv.count; i++) uv.setY(i, v0 + uv.getY(i) * (v1 - v0));
        banners.push(pl.rotateY(s > 0 ? 0 : Math.PI).translate(0, 1.35, s * 0.03).applyMatrix4(m));
      }
    }
  }
  atlasTex ??= atlas();
  const out: THREE.Object3D[] = [];
  const o = new THREE.Mesh(merged(parts), mat); out.push(o);
  if (banners.length) out.push(new THREE.Mesh(merged(banners), new THREE.MeshLambertMaterial({ map: atlasTex })));
  if (glow.length) out.push(new THREE.Mesh(merged(glow), glowMat));
  return out;
}

/* ---------- tower cranes: rows [x, y, z, yaw, height, jib] ---------- */
let trussTex: THREE.Texture | null = null;
const truss = () => {
  const c = document.createElement('canvas'); c.width = 64; c.height = 64;
  const g = c.getContext('2d')!; g.strokeStyle = '#e8b81c'; g.lineWidth = 7;
  g.beginPath(); g.moveTo(0, 0); g.lineTo(64, 64); g.moveTo(64, 0); g.lineTo(0, 64); g.moveTo(0, 3); g.lineTo(64, 3); g.moveTo(0, 61); g.lineTo(64, 61); g.stroke();
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; return t;
};
export function buildCranes(rows: number[][]): THREE.Object3D[] {
  if (!rows.length) return [];
  trussTex ??= truss();
  const solid: THREE.BufferGeometry[] = [], lattice: THREE.BufferGeometry[] = [], glow: THREE.BufferGeometry[] = [];
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1), Y = new THREE.Vector3(0, 1, 0);
  const yel = C(0xe5b21a), cw = C(0x8a8e92), cab = C(0xf0f0ea);
  const plane = (w: number, h: number, tile: number) => {
    const g = new THREE.PlaneGeometry(w, h), uv = g.getAttribute('uv');
    for (let i = 0; i < uv.count; i++) { uv.setX(i, uv.getX(i) * (w / tile)); uv.setY(i, uv.getY(i) * (h / tile)); }
    return g;
  };
  for (const [x, y, z, yaw, h, jib] of rows) {
    m.compose(p.set(x, z, -y), q.setFromAxisAngle(Y, yaw), one);
    const L: THREE.BufferGeometry[] = [], T: THREE.BufferGeometry[] = [];
    for (const [dx, dz] of [[-0.8, -0.8], [0.8, -0.8], [0.8, 0.8], [-0.8, 0.8]]) L.push(box(0.22, h, 0.22, dx, h / 2, dz, yel));
    for (let k = 0; k < 4; k++) T.push(plane(1.6, h, 1.6).rotateY((k * Math.PI) / 2).translate(Math.sin((k * Math.PI) / 2) * 0.8, h / 2, Math.cos((k * Math.PI) / 2) * 0.8));
    L.push(box(2.4, 0.5, 2.4, 0, h + 0.25, 0, cab), box(1.4, 1.6, 1.6, 1.2, h + 1.3, 0, cab), box(1.0, 1.0, 1.2, 1.9, h + 1.2, 1.1, C(0x3a4650)));
    L.push(box(0.2, 6, 0.2, 0, h + 3.5, 0, yel));
    const top = h + 1.0;
    L.push(box(jib + 12, 0.16, 0.16, (jib - 12) / 2, top + 1.5, 0, yel), box(jib + 12, 0.14, 0.14, (jib - 12) / 2, top, 0, yel));
    T.push(plane(jib + 12, 1.5, 1.5).translate((jib - 12) / 2, top + 0.75, 0));
    L.push(box(2.2, 1.4, 1.6, -10.5, top + 0.4, 0, cw), box(2.2, 1.4, 1.6, -8.2, top + 0.4, 0, cw));
    const tr = jib * 0.62;
    L.push(box(0.9, 0.35, 0.5, tr, top - 0.3, 0, DARK), box(0.03, h * 0.7, 0.03, tr, top - 0.3 - (h * 0.7) / 2, 0, DARK), box(0.5, 0.4, 0.4, tr, top - 0.3 - h * 0.7 - 0.1, 0, RED));
    L.push(box(0.5, 0.5, 0.5, 0, h + 6.7, 0, DARK));
    for (const g of L) solid.push(g.applyMatrix4(m));
    for (const g of T) lattice.push(g.applyMatrix4(m));
    glow.push(new THREE.BoxGeometry(0.5, 0.5, 0.5).translate(0, h + 7.1, 0).applyMatrix4(m));
  }
  const out: THREE.Object3D[] = [new THREE.Mesh(merged(solid), mat)];
  const lat = new THREE.Mesh(merged(lattice.map((g) => { g.deleteAttribute('normal'); return g; }).map((g) => (g.index ? g.toNonIndexed() : g))), new THREE.MeshBasicMaterial({ map: trussTex, alphaTest: 0.5, side: THREE.DoubleSide, color: 0xe8e0c8 }));
  out.push(lat, new THREE.Mesh(merged(glow), new THREE.MeshBasicMaterial({ color: 0xff2a1a })));
  return out;
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
