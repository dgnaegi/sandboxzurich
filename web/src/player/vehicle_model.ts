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

/** Surface classes encoded in `_paint` by pipeline/cars/build_car.py: 1 lacquer, 0.3 glass, 0.15 chrome/alloy, 0 matte. */
type Surf = 'paint' | 'glass' | 'chrome' | 'matte';
const surfOf = (v: number): Surf => (v > 0.5 ? 'paint' : v > 0.22 ? 'glass' : v > 0.08 ? 'chrome' : 'matte');
/** Split a geometry by surface class (non-indexed copies); lacquer vertices get the paint colour baked in. */
function splitSurf(src: THREE.BufferGeometry, paint: THREE.Color | null): Record<Surf, THREE.BufferGeometry | null> {
  const g = src.index ? src.toNonIndexed() : src.clone();
  const n = g.getAttribute('position').count, col = g.getAttribute('color'), pa = g.getAttribute('_paint');
  const P = g.getAttribute('position'), N = g.getAttribute('normal');
  const acc: Record<Surf, { pos: number[]; nor: number[]; cl: number[] }> = { paint: { pos: [], nor: [], cl: [] }, glass: { pos: [], nor: [], cl: [] }, chrome: { pos: [], nor: [], cl: [] }, matte: { pos: [], nor: [], cl: [] } };
  for (let t = 0; t < n; t += 3) {
    const k = surfOf(pa ? pa.getX(t) : 0), o = acc[k];
    for (let j = 0; j < 3; j++) {
      const v = t + j;
      o.pos.push(P.getX(v), P.getY(v), P.getZ(v)); o.nor.push(N.getX(v), N.getY(v), N.getZ(v));
      if (k === 'paint' && paint) o.cl.push(paint.r, paint.g, paint.b);
      else if (k === 'glass') o.cl.push(Math.min(1, (col?.getX(v) ?? 1) * 2.4), Math.min(1, (col?.getY(v) ?? 1) * 2.4), Math.min(1, (col?.getZ(v) ?? 1) * 2.4)); // tinted glass, lifted so it does not read black
      else o.cl.push(col?.getX(v) ?? 1, col?.getY(v) ?? 1, col?.getZ(v) ?? 1);
    }
  }
  const out = {} as Record<Surf, THREE.BufferGeometry | null>;
  for (const k of Object.keys(acc) as Surf[]) {
    const o = acc[k];
    if (!o.pos.length) { out[k] = null; continue; }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(o.pos, 3));
    geo.setAttribute('normal', new THREE.Float32BufferAttribute(o.nor, 3));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(o.cl, 3));
    out[k] = geo;
  }
  return out;
}

export async function buildRig(type: string, paint: THREE.Color): Promise<Rig> {
  const src = await loadModel(type);
  const group = new THREE.Group();
  const geos: THREE.BufferGeometry[] = [];
  // clear-coat lacquer, tinted reflective glass, polished chrome/alloy, matte plastic/rubber (only the driven car is Physical)
  const paintMat = new THREE.MeshPhysicalMaterial({ vertexColors: true, roughness: 0.4, metalness: 0.12, clearcoat: 1, clearcoatRoughness: 0.05, envMap, envMapIntensity: 0.5 });
  const glassMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.05, metalness: 0.35, envMap, envMapIntensity: 1.6 });
  const chromeMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.22, metalness: 0.9, envMap, envMapIntensity: 1.1 });
  const matteMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.78, metalness: 0.05, envMap, envMapIntensity: 0.25 });
  const mats: THREE.Material[] = [paintMat, glassMat, chromeMat, matteMat];
  const surfMat: Record<Surf, THREE.Material> = { paint: paintMat, glass: glassMat, chrome: chromeMat, matte: matteMat };
  const addSurf = (parent: THREE.Object3D, geo: THREE.BufferGeometry, pc: THREE.Color | null) => {
    const sp = splitSurf(geo, pc);
    for (const k of Object.keys(sp) as Surf[]) {
      const g = sp[k]; if (!g) continue;
      geos.push(g); const m = new THREE.Mesh(g, surfMat[k]); m.castShadow = true; parent.add(m);
    }
    return sp;
  };
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
      const sp = addSurf(group, body.geometry, paint);
      const ref = (sp.paint ?? sp.matte)!;
      ref.computeBoundingBox();
      const bb = ref.boundingBox!;
      length = bb.max.z - bb.min.z; width = bb.max.x - bb.min.x;
    }
    for (const k of ['fl', 'fr', 'rl', 'rr']) {
      const w = parts[`wheel_${k}`];
      if (!w) continue;
      w.geometry.computeBoundingBox();
      wheelR = w.geometry.boundingBox!.max.y;
      const pivot = new THREE.Group(), spin = new THREE.Group();
      addSurf(spin, w.geometry, null);
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
