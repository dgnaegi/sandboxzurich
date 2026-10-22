import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import type { BikeSlot } from './bikes';

/**
 * Shared e-scooters (colours only, no logos): slim dark deck, coloured stem/fenders, bar with grips, two small wheels, kickstand.
 * Model space like the bikes: origin on the ground between the wheels, front = -z. One InstancedMesh per tile; ridden ones use the
 * split parts (frame / steering assembly / wheel) from `scooterParts()` (see scooterrig.ts).
 */
export const SCOOTER_COLS = [0x2bd45c, 0x2f6fd6, 0xe8e8e2].map((c) => new THREE.Color(c));
export const WHEEL_R = 0.1, WHEEL_Z = 0.47, FORK_Z = -0.46, STEM_Z = -0.43, BAR_Y = 1.06, BAR_HALF = 0.25, DECK_Y = 0.15;
const DARK = 0x2a2d30, TYRE = 0x141414, HUB = 0x9a9ea2, GRIP = 0x0e0e0e, LIGHT = 0xff3b30;

function tag(g: THREE.BufferGeometry, hex: number, paint: number): THREE.BufferGeometry {
  g = g.index ? g.toNonIndexed() : g;
  for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal') g.deleteAttribute(k);
  const c = new THREE.Color(hex), n = g.getAttribute('position').count, col = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b; }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  g.setAttribute('_paint', new THREE.BufferAttribute(new Float32Array(n).fill(paint), 1));
  return g;
}
const box = (w: number, h: number, d: number, x: number, y: number, z: number) => new THREE.BoxGeometry(w, h, d).translate(x, y, z);
const cyl = (r: number, len: number, seg = 6) => new THREE.CylinderGeometry(r, r, len, seg);
/** Wheel with its centre at the origin, axle along x. */
const wheel = () => mergeGeometries([tag(cyl(WHEEL_R, 0.05, 10).rotateZ(Math.PI / 2), TYRE, 0), tag(cyl(0.05, 0.06, 6).rotateZ(Math.PI / 2), HUB, 0)])!;

let cache: { frame: THREE.BufferGeometry; steer: THREE.BufferGeometry; wheel: THREE.BufferGeometry; all: THREE.BufferGeometry } | null = null;
export function scooterParts() {
  if (cache) return cache;
  const stand = tag(cyl(0.01, 0.2, 4).rotateZ(-1.2).translate(-0.09, 0.07, 0.2), DARK, 0);
  const frame = mergeGeometries([
    tag(box(0.2, 0.04, 0.64, 0, DECK_Y - 0.02, 0.1), DARK, 0),                    // deck
    tag(box(0.19, 0.012, 0.6, 0, DECK_Y + 0.006, 0.1), 0x3a3e42, 0),              // grip tape
    tag(box(0.12, 0.025, 0.2, 0, 0.225, WHEEL_Z), 0xffffff, 1),                    // rear fender
    tag(box(0.04, 0.025, 0.03, 0, 0.215, WHEEL_Z + 0.11), LIGHT, 0),               // tail light
    tag(box(0.1, 0.07, 0.1, 0, 0.1, 0.38), DARK, 0),                               // motor/battery bulge over the rear axle
    tag(box(0.035, 0.1, 0.12, 0.09, 0.1, WHEEL_Z), DARK, 0), tag(box(0.035, 0.1, 0.12, -0.09, 0.1, WHEEL_Z), DARK, 0), // rear fork
    stand,
  ])!;
  const steer = mergeGeometries([
    tag(cyl(0.024, 0.95, 7).translate(0, DECK_Y + 0.475, STEM_Z), 0xffffff, 1),   // stem
    tag(box(0.1, 0.22, 0.09, 0, DECK_Y + 0.11, STEM_Z + 0.01), 0xffffff, 1),      // lower neck
    tag(cyl(0.015, BAR_HALF * 2 - 0.1, 5).rotateZ(Math.PI / 2).translate(0, BAR_Y, STEM_Z), DARK, 0), // bar
    tag(cyl(0.02, 0.12, 6).rotateZ(Math.PI / 2).translate(BAR_HALF - 0.04, BAR_Y, STEM_Z), GRIP, 0),   // grips
    tag(cyl(0.02, 0.12, 6).rotateZ(Math.PI / 2).translate(-(BAR_HALF - 0.04), BAR_Y, STEM_Z), GRIP, 0),
    tag(box(0.1, 0.035, 0.06, 0, BAR_Y + 0.03, STEM_Z), DARK, 0),                  // display
    tag(box(0.03, 0.1, 0.03, 0.04, WHEEL_R + 0.05, FORK_Z + 0.02), DARK, 0), tag(box(0.03, 0.1, 0.03, -0.04, WHEEL_R + 0.05, FORK_Z + 0.02), DARK, 0), // fork
    tag(box(0.12, 0.02, 0.18, 0, 0.235, FORK_Z), 0xffffff, 1),                     // front fender
  ])!;
  const w = wheel();
  const all = mergeGeometries([frame.clone(), steer.clone(), w.clone().translate(0, WHEEL_R, FORK_Z), w.clone().translate(0, WHEEL_R, WHEEL_Z)])!;
  cache = { frame, steer, wheel: w, all };
  return cache;
}

/** Instance material: vertex colours, body parts (`_paint` = 1) take the instance colour, the rest stays neutral. */
export const scooterMat = (() => {
  const m = new THREE.MeshLambertMaterial({ vertexColors: true });
  m.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float _paint;')
      .replace('#include <color_vertex>', 'vColor = vec4(1.0);\nvColor.rgb *= color.rgb;\n#ifdef USE_INSTANCING_COLOR\nvColor.rgb *= mix(vec3(1.0), instanceColor.rgb, step(0.5, _paint));\n#endif');
  };
  return m;
})();

const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1), zero = new THREE.Vector3(0, 0, 0);
const Y = new THREE.Vector3(0, 1, 0), LEAN = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), 0.18); // resting on the kickstand
const place = (mesh: THREE.InstancedMesh, i: number, x: number, y: number, z: number, h: number) =>
  mesh.setMatrixAt(i, m4.compose(p.set(x, z, -y), q.setFromAxisAngle(Y, -h).multiply(LEAN), one));

/** Slots of all loaded tiles (a tile's mesh vanishes from the scene on unload; stale slots are dropped lazily). */
let slots: BikeSlot[] = [];
const inScene = (o: THREE.Object3D) => { while (o.parent) o = o.parent; return (o as THREE.Scene).isScene === true; };

export function buildScooters(rows: number[][]): THREE.Object3D[] {
  if (!rows.length) return [];
  const im = new THREE.InstancedMesh(scooterParts().all, scooterMat, rows.length);
  rows.forEach(([x, y, z, h, c], i) => {
    place(im, i, x, y, z, h);
    const color = SCOOTER_COLS[c % SCOOTER_COLS.length];
    im.setColorAt(i, color);
    slots.push({ mesh: im, i, x, y, z, h, color, taken: false, type: 'scooter' });
  });
  im.computeBoundingSphere();
  return [im];
}

export class Scooters {
  readonly dropped: THREE.InstancedMesh;
  private count = 0;
  constructor(scene: THREE.Scene) {
    this.dropped = new THREE.InstancedMesh(scooterParts().all, scooterMat, 32);
    this.dropped.count = 0; this.dropped.frustumCulled = false;
    scene.add(this.dropped);
  }
  all() { return slots; }
  nearest(x: number, y: number, r = 2.0): BikeSlot | null {
    let best: BikeSlot | null = null, bd = r;
    for (const s of slots) {
      if (s.taken) continue;
      const d = Math.hypot(s.x - x, s.y - y);
      if (d < bd && (s.mesh === this.dropped || inScene(s.mesh))) { bd = d; best = s; }
    }
    return best;
  }
  /** Drop slots of unloaded tiles (cheap, call now and then). */
  prune() { slots = slots.filter((s) => s.mesh === this.dropped || inScene(s.mesh)); }
  take(s: BikeSlot) {
    s.taken = true;
    s.mesh.setMatrixAt(s.i, m4.compose(p.set(0, -100, 0), q.identity(), zero));
    s.mesh.instanceMatrix.needsUpdate = true;
  }
  /** Leave a scooter standing on its kickstand where the rider got off. */
  drop(x: number, y: number, z: number, h: number, color: THREE.Color) {
    const i = this.count++ % 32;
    place(this.dropped, i, x, y, z, h);
    this.dropped.setColorAt(i, color);
    this.dropped.count = Math.min(32, this.count);
    this.dropped.instanceMatrix.needsUpdate = true;
    if (this.dropped.instanceColor) this.dropped.instanceColor.needsUpdate = true;
    slots = slots.filter((s) => !(s.mesh === this.dropped && s.i === i));
    slots.push({ mesh: this.dropped, i, x, y, z, h, color, taken: false, type: 'scooter' });
  }
}
