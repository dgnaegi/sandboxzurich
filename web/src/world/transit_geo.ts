import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/** Fallback box modules, vehicle type per trip and destination label textures for Transit. */
const WHITE = new THREE.Color(0xe9ecef), BLUE = new THREE.Color(0x1d4f9c), DARK = new THREE.Color(0x15191e);

export const box = (c: THREE.Color, w: number, h: number, d: number, x = 0, y = 0, z = 0) => {
  const g = new THREE.BoxGeometry(w, h, d).translate(x, y, z).toNonIndexed();
  const col = new Float32Array(g.attributes.position.count * 3);
  for (let i = 0; i < col.length; i += 3) { col[i] = c.r; col[i + 1] = c.g; col[i + 2] = c.b; }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  g.deleteAttribute('uv');
  return g;
};
export const merge = (g: THREE.BufferGeometry[]) => mergeGeometries(g)!;

/** Vehicle type per trip: Tram 2000 still runs on many lines (some in double traction), mixed with Cobra/Flexity. */
const T2000_LINES = new Set(['3', '4', '5', '6', '7', '9', '10', '11', '13', '14', '15']);
export function tramType(ref: string, k: number): string {
  const j = ((k % 6) + 6) % 6;
  if (T2000_LINES.has(ref) && j < 4) return j === 3 ? 'tram_2000_doppel' : 'tram_2000';
  return j % 2 ? 'tram_flexity' : 'tram_cobra';
}

/** Tram module (≈11.6 m long, front = -z). kind: 0 head, 1 mid, 2 tail. */
export function tramModule(kind: number): THREE.BufferGeometry {
  const g = [
    box(WHITE, 2.4, 2.1, 11.6, 0, 1.75), box(WHITE, 2.2, 0.25, 11.2, 0, 2.9), box(BLUE, 2.42, 0.5, 11.62, 0, 0.75),
    box(DARK, 2.44, 0.95, 10.0, 0, 2.05), box(DARK, 2.0, 0.5, 2.6, 0, 0.35, -3.6), box(DARK, 2.0, 0.5, 2.6, 0, 0.35, 3.6),
    box(DARK, 2.0, 2.0, 0.5, 0, 1.9, -5.9), box(DARK, 2.0, 2.0, 0.5, 0, 1.9, 5.9), // bellows
  ];
  if (kind === 0) g.push(box(WHITE, 2.3, 1.6, 1.3, 0, 1.9, -6.2), box(DARK, 2.0, 0.9, 0.1, 0, 2.3, -6.9), box(BLUE, 2.32, 0.5, 1.32, 0, 0.75, -6.2));
  if (kind === 2) g.push(box(WHITE, 2.3, 1.6, 1.3, 0, 1.9, 6.2), box(DARK, 2.0, 0.9, 0.1, 0, 2.3, 6.9), box(BLUE, 2.32, 0.5, 1.32, 0, 0.75, 6.2));
  if (kind === 1) g.push(box(DARK, 1.6, 0.12, 1.4, 0, 3.12, 0), box(DARK, 0.06, 0.5, 0.06, 0.5, 3.35, 0.4), box(DARK, 0.06, 0.5, 0.06, -0.5, 3.35, 0.4));
  return merge(g);
}

/** Articulated trolleybus module (9 m, front = -z). kind: 0 front, 1 rear. */
export function busModule(kind: number): THREE.BufferGeometry {
  const g = [
    box(WHITE, 2.55, 2.5, 8.8, 0, 1.75), box(BLUE, 2.57, 0.6, 8.82, 0, 0.8), box(DARK, 2.58, 0.95, 8.0, 0, 2.15),
    box(DARK, 0.3, 0.9, 0.9, 1.2, 0.45, -2.6), box(DARK, 0.3, 0.9, 0.9, -1.2, 0.45, -2.6),
    box(DARK, 0.3, 0.9, 0.9, 1.2, 0.45, 2.6), box(DARK, 0.3, 0.9, 0.9, -1.2, 0.45, 2.6),
  ];
  if (kind === 0) g.push(box(DARK, 2.3, 1.1, 0.1, 0, 2.2, -4.4), box(BLUE, 2.57, 0.45, 0.1, 0, 0.45, -4.4));
  else g.push(box(DARK, 0.04, 0.04, 6, 0.35, 3.15, 3).rotateX(-0.12), box(DARK, 0.04, 0.04, 6, -0.35, 3.15, 3).rotateX(-0.12),
    box(DARK, 2.0, 1.4, 0.6, 0, 1.9, 4.5));
  return merge(g);
}

const labelCache = new Map<string, THREE.Material>();
export function labelMat(ref: string, dest: string): THREE.Material {
  const key = `${ref}|${dest}`;
  let m = labelCache.get(key);
  if (m) return m;
  const c = document.createElement('canvas'); c.width = 256, c.height = 96;
  const x = c.getContext('2d')!;
  x.fillStyle = '#05070a'; x.fillRect(0, 0, 256, 96);
  x.fillStyle = '#ffb347'; x.textBaseline = 'middle'; x.textAlign = 'left';
  x.font = 'bold 54px monospace'; x.fillText(ref, 10, 32);   // LED orange: line number
  x.fillStyle = '#f4f4ee'; x.font = 'bold 26px monospace';   // white: destination, squeezed to fit
  const w = x.measureText(dest).width, fit = Math.min(1, 236 / Math.max(1, w));
  x.save(); x.translate(10, 76); x.scale(fit, 1); x.fillText(dest, 0, 0); x.restore();
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  m = new THREE.MeshBasicMaterial({ map: tex, side: THREE.FrontSide });
  labelCache.set(key, m);
  return m;
}

