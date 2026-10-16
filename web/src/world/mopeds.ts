import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/** Parked scooters / small motorcycles (Zweiradparkierung "Motorrad"): simple vertex-coloured model, 6 body colours. Length 1.75 m along +x. */
const BODY = [0x2b2f33, 0x9a9da0, 0x3b4f6b, 0x8a2b2b, 0xd8d6cf, 0x2f5a3a];
const cache: THREE.BufferGeometry[] = [];

function box(w: number, h: number, d: number, x: number, y: number, z: number, c: number, rz = 0): THREE.BufferGeometry {
  const g = new THREE.BoxGeometry(w, h, d).toNonIndexed();
  g.rotateZ(rz).translate(x, y, z);
  return paint(g, c);
}
function wheel(x: number): THREE.BufferGeometry {
  const g = new THREE.CylinderGeometry(0.22, 0.22, 0.12, 12).toNonIndexed();
  g.rotateX(Math.PI / 2).translate(x, 0.22, 0);
  return paint(g, 0x1b1b1d);
}
function paint(g: THREE.BufferGeometry, hex: number): THREE.BufferGeometry {
  for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal') g.deleteAttribute(k);
  const c = new THREE.Color(hex), n = g.getAttribute('position').count, a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) a.set([c.r, c.g, c.b], i * 3);
  g.setAttribute('color', new THREE.BufferAttribute(a, 3));
  return g;
}

export function mopedGeo(k: number): THREE.BufferGeometry {
  const i = Math.abs(k) % BODY.length;
  if (!cache[i]) {
    const c = BODY[i];
    cache[i] = mergeGeometries([
      wheel(0.7), wheel(-0.65),
      box(0.95, 0.16, 0.3, -0.05, 0.38, 0, c),          // floorboard / body
      box(0.5, 0.35, 0.34, -0.5, 0.52, 0, c),           // rear cowl
      box(0.5, 0.1, 0.26, -0.25, 0.74, 0, 0x1e1e20),    // seat
      box(0.14, 0.62, 0.3, 0.5, 0.62, 0, c, -0.25),     // front shield
      box(0.08, 0.08, 0.6, 0.52, 0.98, 0, 0x2a2a2c),    // handlebar
      box(0.1, 0.2, 0.14, 0.62, 1.04, 0, 0x888c90),     // mirror/instrument
    ])!;
  }
  return cache[i];
}
