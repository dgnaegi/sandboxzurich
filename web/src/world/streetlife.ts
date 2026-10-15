import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/**
 * Small street-life details: chalkboard A-frames in front of cafés/bakeries/kiosks, and blue Züri-Säcke
 * (official rubbish bags) at house entrances on collection mornings.
 */
let chalkTex: THREE.Texture | null = null;
const MENUS = [['TAGESMENÜ', 'Curry 19.50', 'Suppe 8.–'], ['KAFI', 'Espresso 4.20', 'Cappuccino 5.50'], ['HEUTE', 'frische Gipfeli', 'Zopf 6.80'],
  ['HAPPY HOUR', '17–19 Uhr', 'Bier 6.–'], ['LOTTO', 'Euromillions', 'Jackpot 120 Mio']];

function chalk(): THREE.Texture {
  const c = document.createElement('canvas'); c.width = 640; c.height = 256;
  const g = c.getContext('2d')!;
  MENUS.forEach((m, i) => {
    const x = i * 128;
    g.fillStyle = '#1f2a24'; g.fillRect(x, 0, 128, 256);
    g.strokeStyle = '#8a6a44'; g.lineWidth = 8; g.strokeRect(x + 4, 4, 120, 248);
    g.fillStyle = '#f2efe6'; g.textAlign = 'center';
    g.font = '22px Anton, sans-serif'; g.fillText(m[0], x + 64, 50);
    g.font = '15px "Barlow Condensed", sans-serif'; g.fillText(m[1], x + 64, 110); g.fillText(m[2], x + 64, 140);
    g.strokeStyle = '#e8a0b8'; g.lineWidth = 2; g.beginPath(); g.moveTo(x + 24, 175); g.lineTo(x + 104, 175); g.stroke();
  });
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** rows: signs of the tile ({x, y, tx, ty, kind}); returns A-frames for cafés, bakeries, kiosks, bars. */
export function buildAFrames(signs: { x: number; y: number; z: number; tx: number; ty: number; kind: string; name: string }[]): THREE.Object3D[] {
  const want = signs.filter((s) => ['cafe', 'bakery', 'kiosk', 'restaurant', 'bar', 'pub', 'convenience', 'ice_cream'].includes(s.kind));
  if (!want.length) return [];
  chalkTex ??= chalk();
  const pos: number[] = [], uv: number[] = [], nrm: number[] = [], idx: number[] = [];
  for (const s of want) {
    let hsh = 0; for (const ch of s.name) hsh = (hsh * 31 + ch.charCodeAt(0)) >>> 0;
    if (hsh % 3 === 0) continue;
    const ox = s.ty, oy = -s.tx, side = ((hsh >> 3) % 3 - 1) * 1.2;
    const bx = s.x + ox * 1.1 + s.tx * side, by = s.y + oy * 1.1 + s.ty * side;
    const m = MENUS.indexOf(MENUS[hsh % MENUS.length]);
    // two boards leaning together (A-frame), each 0.55 x 0.9 m
    for (const f of [1, -1]) {
      const b = pos.length / 3, nx = ox * f, ny = oy * f;
      const base = [bx + nx * 0.22, by + ny * 0.22], top = [bx + nx * 0.02, by + ny * 0.02];
      for (const [u, v] of [[-0.28, 0], [0.28, 0], [0.28, 1], [-0.28, 1]]) {
        const p = v ? top : base;
        pos.push(p[0] + s.tx * u, s.z - 3.45 + (v ? 0.92 : 0), -(p[1] + s.ty * u)); nrm.push(nx, 0.2, -ny); // sign z = ground + 3.45
      }
      uv.push(m / 5, 0, (m + 1) / 5, 0, (m + 1) / 5, 1, m / 5, 1);
      idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
    }
  }
  if (!idx.length) return [];
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  return [new THREE.Mesh(g, new THREE.MeshLambertMaterial({ map: chalkTex, side: THREE.DoubleSide }))];
}

/** Züri-Säcke at entrances (rows = house numbers [x, y, zNumber, tx, ty, text]); visible on collection mornings. */
export const sackGroups = new Set<THREE.Object3D>();
const sackGeo = (() => {
  const bag = (x: number, z: number, s: number) => new THREE.SphereGeometry(0.28 * s, 7, 5).scale(1, 1.25, 0.9).translate(x, 0.33 * s, z).toNonIndexed();
  const knot = (x: number, z: number, s: number) => new THREE.ConeGeometry(0.07, 0.14, 5).translate(x, 0.72 * s, z).toNonIndexed();
  const parts = [bag(0, 0, 1), bag(0.45, 0.1, 0.9), bag(0.2, 0.45, 0.85), knot(0, 0, 1), knot(0.45, 0.1, 0.9), knot(0.2, 0.45, 0.85)];
  for (const p of parts) p.deleteAttribute('uv');
  return mergeGeometries(parts)!;
})();
const sackMat = new THREE.MeshLambertMaterial({ color: 0x2f63c9 });

export function buildSacks(rows: (number | string)[][]): THREE.Object3D[] {
  const pick = rows.filter((r) => Math.abs(Math.floor((r[0] as number) * 17 + (r[1] as number) * 5)) % 5 < 2);
  if (!pick.length) return [];
  const im = new THREE.InstancedMesh(sackGeo, sackMat, pick.length);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), s = new THREE.Vector3(1, 1, 1);
  pick.forEach((r, i) => {
    const [x, y, zn, tx, ty] = r as number[];
    const ox = ty, oy = -tx;
    m.compose(p.set(x + ox * 0.6 + tx * 1.0, zn - 2.2, -(y + oy * 0.6 + ty * 1.0)), q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), x), s);
    im.setMatrixAt(i, m);
  });
  im.computeBoundingSphere();
  im.visible = false;
  sackGroups.add(im);
  return [im];
}

/** Collection mornings (assumption for Kreis 4: Tue and Fri, bags out 06:00–10:30). */
export function updateSacks(weekday: number, minute: number) {
  const on = (weekday === 1 || weekday === 4) && minute >= 360 && minute < 630;
  for (const g of sackGroups) g.visible = on;
}
