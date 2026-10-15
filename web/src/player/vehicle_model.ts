import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { CAR_GEO } from '../world/cars';

/**
 * Visual rig of a driven car from `<type>_drive.glb` (pipeline/cars/build_car.py ... drive): body without wheels,
 * four wheel nodes, head/tail light meshes. Clear-coat paint with reflections, glossy glass, spinning/steering wheels,
 * head/tail/brake/reverse lights and indicators. Falls back to the static model without wheels if the file is missing.
 */
export interface Rig {
  group: THREE.Group;       // origin on the ground, front = -z
  length: number; width: number; wheelR: number; wheelbase: number;
  /** speed (m/s, signed), steer (rad), then lights. */
  setWheels(spin: number, steer: number): void;
  setLights(o: { brake: boolean; reverse: boolean; night: number; blink: -1 | 0 | 1; blinkOn: boolean }): void;
  dispose(): void;
}

const cache = new Map<string, Promise<THREE.Object3D | null>>();
let envMap: THREE.Texture | null = null;

/** Small procedural environment (sky gradient + warm sun spot + street) for car reflections; built once. */
export function initCarEnvironment(renderer: THREE.WebGLRenderer) {
  if (envMap) return;
  const sc = new THREE.Scene();
  const g = new THREE.SphereGeometry(50, 24, 12), pos = g.getAttribute('position'), col = new Float32Array(pos.count * 3);
  const top = new THREE.Color(0x6f9ad8), hor = new THREE.Color(0xe8ddd0), gnd = new THREE.Color(0x58524a), c = new THREE.Color();
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i) / 50;
    if (y > 0) c.copy(hor).lerp(top, Math.pow(y, 0.6)); else c.copy(hor).lerp(gnd, Math.min(1, -y * 3));
    col.set([c.r, c.g, c.b], i * 3);
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  sc.add(new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide })));
  const sun = new THREE.Mesh(new THREE.SphereGeometry(7, 8, 6), new THREE.MeshBasicMaterial({ color: new THREE.Color(6, 5, 3.6) }));
  sun.position.set(-26, 22, 18); sc.add(sun);
  const pm = new THREE.PMREMGenerator(renderer);
  envMap = pm.fromScene(sc, 0.02).texture;
  pm.dispose();
}

function loadModel(type: string): Promise<THREE.Object3D | null> {
  let p = cache.get(type);
  if (!p) {
    p = new GLTFLoader().loadAsync(`/models/cars/${type}_drive.glb`).then((g) => g.scene, () => null);
    cache.set(type, p);
  }
  return p;
}

const GLASS_LIN = { r: 0.011, b: 0.033 };
/** Split a body geometry into paint (colour baked in) and glass triangles. */
function splitBody(src: THREE.BufferGeometry, paint: THREE.Color): { body: THREE.BufferGeometry; glass: THREE.BufferGeometry } {
  const g = src.index ? src.toNonIndexed() : src.clone();
  const n = g.getAttribute('position').count, col = g.getAttribute('color'), pa = g.getAttribute('_paint');
  const isGlass = (v: number) => col && col.getZ(v) - col.getX(v) > 0.015 && Math.abs(col.getX(v) - GLASS_LIN.r) < 0.012 && Math.abs(col.getZ(v) - GLASS_LIN.b) < 0.02;
  const take = (glass: boolean) => {
    const pos: number[] = [], nor: number[] = [], cl: number[] = [];
    const P = g.getAttribute('position'), N = g.getAttribute('normal');
    for (let t = 0; t < n; t += 3) {
      if (isGlass(t) !== glass) continue;
      for (let k = 0; k < 3; k++) {
        const v = t + k;
        pos.push(P.getX(v), P.getY(v), P.getZ(v)); nor.push(N.getX(v), N.getY(v), N.getZ(v));
        const f = pa && pa.getX(v) > 0.5;
        cl.push(f ? paint.r : col?.getX(v) ?? 1, f ? paint.g : col?.getY(v) ?? 1, f ? paint.b : col?.getZ(v) ?? 1);
      }
    }
    const o = new THREE.BufferGeometry();
    o.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    o.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
    o.setAttribute('color', new THREE.Float32BufferAttribute(cl, 3));
    return o;
  };
  return { body: take(false), glass: take(true) };
}

export async function buildRig(type: string, paint: THREE.Color): Promise<Rig> {
  const src = await loadModel(type);
  const group = new THREE.Group();
  const geos: THREE.BufferGeometry[] = [];
  const paintMat = new THREE.MeshPhysicalMaterial({ vertexColors: true, roughness: 0.42, metalness: 0.35, clearcoat: 1, clearcoatRoughness: 0.06, envMap, envMapIntensity: 0.9 });
  const glassMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.06, metalness: 0.9, envMap, envMapIntensity: 1.1 });
  const tyreMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.75, metalness: 0.1, envMap, envMapIntensity: 0.3 });
  const mats: THREE.Material[] = [paintMat, glassMat, tyreMat];
  const wheels: { spin: THREE.Object3D; pivot: THREE.Object3D; front: boolean }[] = [];
  let length = 4.4, width = 1.8, wheelR = 0.31, wheelbase = 2.65;
  const headMat = new THREE.MeshBasicMaterial({ color: 0xcfc8b0, toneMapped: false });
  const tailMat = new THREE.MeshBasicMaterial({ color: 0x5a0a10, toneMapped: false });
  const revMat = new THREE.MeshBasicMaterial({ color: 0x444444, toneMapped: false });
  const blinkMat = new THREE.MeshBasicMaterial({ color: 0x4a3000, toneMapped: false });
  mats.push(headMat, tailMat, revMat, blinkMat);
  const blink: Record<'-1' | '1', THREE.Mesh[]> = { '-1': [], '1': [] };

  if (src) {
    src.updateMatrixWorld(true);
    const parts: Record<string, THREE.Mesh> = {};
    src.traverse((o) => { if ((o as THREE.Mesh).isMesh) parts[o.name] = o as THREE.Mesh; });
    const body = Object.entries(parts).find(([k]) => !/^(head|tail|wheel_)/.test(k))?.[1];
    if (body) {
      const { body: b, glass } = splitBody(body.geometry, paint);
      geos.push(b, glass);
      const mb = new THREE.Mesh(b, paintMat), mg = new THREE.Mesh(glass, glassMat);
      mb.castShadow = mg.castShadow = true;
      group.add(mb, mg);
      b.computeBoundingBox();
      const bb = b.boundingBox!;
      length = bb.max.z - bb.min.z; width = bb.max.x - bb.min.x;
    }
    for (const k of ['fl', 'fr', 'rl', 'rr']) {
      const w = parts[`wheel_${k}`];
      if (!w) continue;
      w.geometry.computeBoundingBox();
      wheelR = w.geometry.boundingBox!.max.y;
      const pivot = new THREE.Group(), spin = new THREE.Mesh(w.geometry, tyreMat);
      spin.castShadow = true;
      pivot.position.copy(w.position); pivot.add(spin); group.add(pivot);
      wheels.push({ spin, pivot, front: k[0] === 'f' });
    }
    const fz = wheels.filter((w) => w.front)[0]?.pivot.position.z, rz = wheels.filter((w) => !w.front)[0]?.pivot.position.z;
    if (fz !== undefined && rz !== undefined) wheelbase = rz - fz;
    if (parts.head) { const m = new THREE.Mesh(parts.head.geometry, headMat); group.add(m); }
    if (parts.tail) { const m = new THREE.Mesh(parts.tail.geometry, tailMat); group.add(m); }
  } else if (CAR_GEO[type]) { // missing drive model: the static one (wheels do not turn)
    const m = new THREE.Mesh(CAR_GEO[type], new THREE.MeshLambertMaterial({ vertexColors: true }));
    group.add(m);
  }
  // indicators (amber) at the four corners, reversing lights (white) in the middle of the tail
  const hl = length / 2, hw = width / 2 - 0.16, bz = 0.58;
  const box = (mat: THREE.Material, w: number, h: number, d: number, x: number, y: number, z: number) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); geos.push(m.geometry); group.add(m); return m;
  };
  for (const sx of [-1, 1] as const) {
    blink[String(sx) as '-1' | '1'].push(box(blinkMat, 0.16, 0.07, 0.05, sx * hw, bz, -hl + 0.02), box(blinkMat, 0.16, 0.07, 0.05, sx * hw, bz + 0.04, hl - 0.02));
  }
  box(revMat, 0.2, 0.06, 0.05, 0, bz - 0.04, hl - 0.015);

  const col = new THREE.Color();
  return {
    group, length, width, wheelR, wheelbase,
    setWheels(spin, steer) {
      for (const w of wheels) { w.spin.rotation.x = spin; if (w.front) w.pivot.rotation.y = steer; }
    },
    setLights({ brake, reverse, night, blink: b, blinkOn }) {
      headMat.color.setHex(night > 0.35 ? 0xfff6d8 : 0xa09c8a).multiplyScalar(night > 0.35 ? 2.2 : 1);
      tailMat.color.set(brake ? col.setRGB(3.2, 0.1, 0.1) : night > 0.35 ? col.setRGB(1.0, 0.04, 0.05) : col.setRGB(0.35, 0.03, 0.04));
      revMat.color.set(reverse ? col.setRGB(2.5, 2.5, 2.4) : col.setRGB(0.25, 0.25, 0.25));
      blinkMat.color.set(b !== 0 && blinkOn ? col.setRGB(3, 1.6, 0) : col.setRGB(0.2, 0.12, 0));
      const active = b === 0 ? [] : b < 0 ? blink['-1'] : blink['1'];
      for (const m of [...blink['-1'], ...blink['1']]) m.material = active.includes(m) ? blinkMat : offMat;
    },
    dispose() { for (const g of geos) g.dispose(); for (const m of mats) m.dispose(); },
  };
}

const offMat = new THREE.MeshBasicMaterial({ color: 0x3a2800, toneMapped: false });
