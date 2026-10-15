import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/** Low-poly vehicle geometries (GTA3 style). Origin on the ground, front = -z. */
const box = (w: number, h: number, d: number, x = 0, y = 0, z = 0) => new THREE.BoxGeometry(w, h, d).translate(x, y, z);
const cyl = (r: number, w: number, x: number, y: number, z: number, seg = 8) =>
  new THREE.CylinderGeometry(r, r, w, seg).rotateZ(Math.PI / 2).translate(x, y, z);
const merge = (g: THREE.BufferGeometry[]) => mergeGeometries(g.map((x) => x.toNonIndexed()))!;

export const CAR_COLORS = [0xb8202a, 0x1f4e8c, 0xe8e6e0, 0x2b2b2e, 0x8a9096, 0x2f6b3a, 0xd9a020, 0x5a2c6e, 0xc8c2b0,
  0x13294b, 0x9c1c1c, 0x707a80].map((c) => new THREE.Color(c));

/** Car: paint (body+roof, instance colour), dark (glass, wheels, bumpers), lights. */
export const car = {
  paint: merge([box(1.76, 0.62, 4.3, 0, 0.55, 0), box(1.5, 0.08, 2.1, 0, 1.36, 0.25)]),
  dark: merge([
    box(1.56, 0.5, 2.2, 0, 1.1, 0.25),
    box(1.82, 0.22, 0.12, 0, 0.36, -2.15), box(1.82, 0.22, 0.12, 0, 0.36, 2.15),
    cyl(0.33, 0.24, -0.82, 0.33, -1.35), cyl(0.33, 0.24, 0.82, 0.33, -1.35),
    cyl(0.33, 0.24, -0.82, 0.33, 1.35), cyl(0.33, 0.24, 0.82, 0.33, 1.35),
  ]),
  lights: merge([box(0.34, 0.12, 0.05, -0.6, 0.68, -2.16), box(0.34, 0.12, 0.05, 0.6, 0.68, -2.16)]),
  rear: merge([box(0.34, 0.12, 0.05, -0.6, 0.68, 2.16), box(0.34, 0.12, 0.05, 0.6, 0.68, 2.16)]),
};

/** Zürich tram (Cobra-ish), 3 segments ≈ 36 m, white/blue. */
export const tram = (() => {
  const body: THREE.BufferGeometry[] = [], blue: THREE.BufferGeometry[] = [], dark: THREE.BufferGeometry[] = [];
  for (let s = 0; s < 3; s++) {
    const z = (s - 1) * 12.2;
    body.push(box(2.4, 2.1, 11.6, 0, 1.75, z), box(2.2, 0.25, 11.2, 0, 2.9, z));
    blue.push(box(2.42, 0.5, 11.62, 0, 0.75, z));
    dark.push(box(2.44, 1.0, 10.2, 0, 2.05, z));
  }
  body.push(box(2.3, 1.5, 1.2, 0, 2.0, -18.6), box(2.3, 1.5, 1.2, 0, 2.0, 18.6));
  dark.push(box(2.0, 0.9, 0.2, 0, 2.3, -19.25), box(2.0, 0.9, 0.2, 0, 2.3, 19.25), box(0.05, 0.8, 30, 0, 3.4, 0));
  return { body: merge(body), blue: merge(blue), dark: merge(dark) };
})();

/** Bicycle: frame (instance colour) and black parts. Origin between wheels, front = -z. */
export const bike = {
  frame: merge([
    box(0.05, 0.05, 0.62, 0, 0.62, 0).rotateX(0.0), box(0.05, 0.5, 0.05, 0, 0.55, 0.08),
    box(0.05, 0.05, 0.5, 0, 0.42, 0.25).rotateX(-0.6).translate(0, 0.14, 0.05), box(0.05, 0.55, 0.05, 0, 0.6, -0.36),
  ]),
  black: merge([
    new THREE.TorusGeometry(0.34, 0.035, 4, 14).rotateY(Math.PI / 2).translate(0, 0.35, -0.55),
    new THREE.TorusGeometry(0.34, 0.035, 4, 14).rotateY(Math.PI / 2).translate(0, 0.35, 0.55),
    box(0.12, 0.05, 0.24, 0, 0.88, 0.12), box(0.56, 0.04, 0.04, 0, 0.98, -0.42),
  ]),
};
