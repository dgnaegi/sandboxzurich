import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
/** Prominent free-standing square signs (pipeline/overrides/landmark_signs.json).
 *  Row: [x, y, zGround, heading, name, plaque, flowers]. Double-sided enamel panel on two posts, plaque below,
 *  optional red carnations at the foot. Local (x east, y north, z up) -> Three (x, z, -y). */
export type LandmarkRow = [number, number, number, number, string, string, number];
const BLUE = '#0f3f8c';
const PW = 3.4, PH = 0.85, TOP = 3.4; // panel size (m) and panel centre height

function panelTexture(name: string, plaque: string): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = 1024; c.height = 512;
  const g = c.getContext('2d')!;
  // top half: name panel (1024x256), bottom half: plaque (1024x256)
  g.fillStyle = '#f4f4f0'; g.fillRect(0, 0, 1024, 256);
  g.fillStyle = BLUE; g.fillRect(8, 8, 1008, 240);
  g.strokeStyle = '#eef2f8'; g.lineWidth = 5; g.strokeRect(22, 22, 980, 212);
  g.fillStyle = '#fff'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.font = '600 150px "Barlow Condensed", "Arial Narrow", sans-serif';
  g.fillText(name, 512, 134, 940);
  g.fillStyle = BLUE; g.fillRect(0, 256, 1024, 256);
  g.fillStyle = '#f6f6f2'; g.fillRect(8, 264, 1008, 240);
  g.fillStyle = BLUE;
  const lines = plaque.split('\n').slice(0, 4);
  lines.forEach((ln, i) => {
    g.font = i === 0 ? '600 58px "Barlow Condensed", sans-serif' : '500 44px "Barlow Condensed", sans-serif';
    g.fillText(ln, 512, 384 + (i - (lines.length - 1) / 2) * 56, 960);
  });
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

function quad(w: number, h: number, v0: number, v1: number): THREE.BufferGeometry {
  const q = new THREE.PlaneGeometry(w, h);
  const uv = q.attributes.uv as THREE.BufferAttribute;
  for (let i = 0; i < uv.count; i++) uv.setY(i, uv.getY(i) > 0.5 ? v1 : v0);
  return q;
}

export function buildLandmarks(rows: LandmarkRow[]): THREE.Object3D[] {
  const out: THREE.Object3D[] = [];
  for (const [x, y, z, h, name, plaque, flowers] of rows) {
    const grp = new THREE.Group();
    grp.position.set(x, z, -y);
    grp.rotation.y = h; // panel tangent (cos h, sin h) in local -> Three x axis rotated by h
    const tex = panelTexture(name, plaque);
    const mat = new THREE.MeshLambertMaterial({ map: tex, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 0.25 });
    const faces: THREE.BufferGeometry[] = [];
    for (const side of [1, -1]) {
      const n = quad(PW, PH, 0.5, 1); n.translate(0, TOP, 0.03);
      const p = quad(PW * 0.62, PH * 0.62, 0, 0.5); p.translate(0, TOP - PH / 2 - 0.12 - PH * 0.31, 0.03);
      for (const f of [n, p]) { if (side < 0) f.rotateY(Math.PI); faces.push(f); }
    }
    grp.add(new THREE.Mesh(mergeGeometries(faces), mat));
    faces.forEach((f) => f.dispose());
    // posts + backing frame
    const steel: THREE.BufferGeometry[] = [];
    for (const px of [-PW / 2 + 0.25, PW / 2 - 0.25]) {
      const c = new THREE.CylinderGeometry(0.05, 0.055, TOP + PH / 2 + 0.1, 10);
      c.translate(px, (TOP + PH / 2 + 0.1) / 2, 0);
      steel.push(c);
    }
    const back = new THREE.BoxGeometry(PW + 0.04, PH + 0.04, 0.05); back.translate(0, TOP, 0); steel.push(back);
    const bp = new THREE.BoxGeometry(PW * 0.62 + 0.03, PH * 0.62 + 0.03, 0.05); bp.translate(0, TOP - PH / 2 - 0.12 - PH * 0.31, 0); steel.push(bp);
    grp.add(new THREE.Mesh(mergeGeometries(steel), new THREE.MeshLambertMaterial({ color: 0x6f757b })));
    steel.forEach((f) => f.dispose());
    if (flowers) grp.add(carnations());
    grp.traverse((o) => { o.castShadow = true; });
    out.push(grp);
  }
  return out;
}

/** A few red carnations and a candle glass at the foot of the left post. */
function carnations(): THREE.Object3D {
  const g = new THREE.Group();
  const stems: THREE.BufferGeometry[] = [], heads: THREE.BufferGeometry[] = [];
  let s = 7;
  const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  for (let i = 0; i < 9; i++) {
    const a = rnd() * 0.9 - 0.45, l = 0.42 + rnd() * 0.12, ox = -PW / 2 + 0.25 + Math.sin(a) * 0.12, oz = 0.12 + rnd() * 0.1;
    const st = new THREE.CylinderGeometry(0.004, 0.004, l, 3);
    st.rotateZ(Math.PI / 2 - 0.25 - rnd() * 0.3); st.rotateY(a); st.translate(ox + 0.2, 0.03, oz);
    stems.push(st);
    const hd = new THREE.IcosahedronGeometry(0.03, 0);
    hd.translate(ox + 0.2 + Math.cos(a) * l / 2, 0.04, oz - Math.sin(a) * l / 2);
    heads.push(hd);
  }
  g.add(new THREE.Mesh(mergeGeometries(stems), new THREE.MeshLambertMaterial({ color: 0x3f6b2a })));
  g.add(new THREE.Mesh(mergeGeometries(heads), new THREE.MeshLambertMaterial({ color: 0xc8102e, emissive: 0x400008 })));
  const glass = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.1, 8), new THREE.MeshLambertMaterial({ color: 0xd02030, emissive: 0xff5020, emissiveIntensity: 0.6, transparent: true, opacity: 0.85 }));
  glass.position.set(-PW / 2 + 0.6, 0.05, 0.08);
  g.add(glass);
  [...stems, ...heads].forEach((f) => f.dispose());
  return g;
}
