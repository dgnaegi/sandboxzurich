import * as THREE from 'three';
import { HORIZON, ZENITH } from '../engine/sky';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/**
 * Low-poly cars (pipeline/cars, Blender), modelled after common Zürich cars without logos. Each model is one
 * mesh: vertex colours + a `_paint` attribute so the instance colour only tints the bodywork (1 draw call/type).
 */
// Swiss fleet (parked + traffic): SUVs and estates/hatchbacks dominate, few vans and sports cars (sedan model doubles as e-sedan)
export const CAR_MIX: [string, number][] = [['hatch', 17], ['wagon', 18], ['small', 9], ['sedan', 10], ['csuv', 14], ['suv', 22], ['van', 8], ['sport', 1]];
export const CAR_PAINT = [0x5d6268, 0x1a1c20, 0xe2e2df, 0x7d8288, 0x1b2c4e, 0x3a3f45, 0x8c1c22, 0x24402f, 0x2d4f7c, 0x4a4f55, 0x101214,
  0x6e2a1a, 0x9a9fa5, 0x14365c].map((c) => new THREE.Color(c));
/** Paint by share: white/black/grey/silver make up ~75 % of cars in Switzerland; blue, red, green, brown the rest. */
const PAINT_W: [number, number][] = [[0xe6e6e3, 20], [0x1a1c20, 19], [0x5d6268, 12], [0x3a3f45, 8], [0x9a9fa5, 10], [0xb9bdc1, 6], [0x1b2c4e, 7], [0x14365c, 3], [0x8c1c22, 5], [0x24402f, 3], [0x6e2a1a, 3], [0x2d4f7c, 3], [0xc8c1ae, 1]];
export const CH_PAINT = PAINT_W.flatMap(([c, w]) => Array.from({ length: w }, () => new THREE.Color(c)));
const VAN_PAINT = [0xf2f2ef, 0xf2f2ef, 0xf2f2ef, 0xf2f2ef, 0xd9dbdd, 0x9a9fa5, 0x1b2c4e, 0xb8201f].map((c) => new THREE.Color(c));
export const SPORT_PAINT = [0xf2c200, 0xc8102e, 0x2e7d32, 0xf5f5f0, 0x1565c0].map((c) => new THREE.Color(c));
export const CAR_GEO: Record<string, THREE.BufferGeometry> = {};

export async function loadCars(base = '/models/cars') {
  const list = (await (await fetch(`${base}/manifest.json`)).json()) as { type: string; file: string }[];
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  await Promise.all(list.map(async (e) => {
    const g = await loader.loadAsync(`${base}/${e.file}`);
    g.scene.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) CAR_GEO[e.type] = m.geometry.clone().applyMatrix4(m.matrixWorld);
    });
  }));
  if (CAR_GEO.wagon) CAR_GEO.police = policeCar(CAR_GEO.wagon);
  if (!CAR_GEO.taxi && CAR_GEO.sedan) CAR_GEO.taxi = taxi(CAR_GEO.sedan); // taxi.glb (own model with roof sign) preferred
}

/** Float32, non-indexed copy with only position/normal/color/_paint (so parts can be merged). */
function plain(g: THREE.BufferGeometry): THREE.BufferGeometry {
  const src = g.index ? g.toNonIndexed() : g, out = new THREE.BufferGeometry();
  for (const [name, size] of [['position', 3], ['normal', 3], ['color', 3], ['_paint', 1]] as const) {
    const a = src.getAttribute(name), n = src.getAttribute('position').count, arr = new Float32Array(n * size);
    for (let i = 0; i < n; i++) for (let c = 0; c < size; c++) arr[i * size + c] = a ? a.getComponent(i, c) : (name === 'color' ? 1 : 0);
    out.setAttribute(name, new THREE.BufferAttribute(arr, size));
  }
  return out;
}

/** Taxi: sedan with the yellow roof sign (Zürich taxis have no uniform colour). */
function taxi(sedan: THREE.BufferGeometry): THREE.BufferGeometry {
  const bb = new THREE.Box3().setFromBufferAttribute(sedan.getAttribute('position') as THREE.BufferAttribute);
  const g = new THREE.BoxGeometry(0.62, 0.17, 0.26).translate(0, bb.max.y + 0.09, 0.1).toNonIndexed();
  g.deleteAttribute('uv');
  const n = g.getAttribute('position').count, c = new THREE.Color(0xf6c400);
  g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(n * 3).map((_, i) => [c.r, c.g, c.b][i % 3]), 3));
  g.setAttribute('_paint', new THREE.BufferAttribute(new Float32Array(n), 1));
  return mergeGeometries([plain(sedan), g])!;
}

/** Zürich-style patrol car: white wagon with blue side stripe and light bar (no real logo). */
function policeCar(wagon: THREE.BufferGeometry): THREE.BufferGeometry {
  const box = (w: number, h: number, d: number, x: number, y: number, z: number, col: number) => {
    const g = new THREE.BoxGeometry(w, h, d).translate(x, y, z).toNonIndexed();
    g.deleteAttribute('uv');
    const n = g.getAttribute('position').count, c = new THREE.Color(col);
    g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(n * 3).map((_, i) => [c.r, c.g, c.b][i % 3]), 3));
    g.setAttribute('_paint', new THREE.BufferAttribute(new Float32Array(n), 1));
    return g;
  };
  const bb = new THREE.Box3().setFromBufferAttribute(wagon.getAttribute('position') as THREE.BufferAttribute);
  const w = bb.max.x - bb.min.x, top = bb.max.y, L = bb.max.z - bb.min.z;
  return mergeGeometries([plain(wagon),
    box(w + 0.03, 0.14, L * 0.82, 0, 0.72, 0, 0x1f4fd0),       // blue side stripe
    box(w + 0.03, 0.05, L * 0.82, 0, 0.82, 0, 0xf2c200),       // yellow pin stripe
    box(1.1, 0.12, 0.28, 0, top + 0.06, 0.1, 0x2a6bff),        // light bar
  ])!;
}

/** Day brightness for the reflection term (1 = day, 0.15 = night); set each frame by TrafficLights. */
export const carDay = { value: 1 };

/**
 * Lambert material where instanceColor only affects vertices with _paint > 0.5. `_paint` also encodes the surface:
 * 0.3 = glass, 0.15 = chrome/alloy, 1 = lacquer. Those get a cheap fake sky/ground reflection with a Fresnel boost
 * (no env map, no extra draw call), so windows read as glass and not as black holes.
 */
export const carMaterial = (() => {
  const m = new THREE.MeshLambertMaterial({ vertexColors: true });
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uCarDay = carDay;
    sh.uniforms.uSkyZ = { value: ZENITH };   // live sky colours (updated by Daytime): reflections follow the time of day
    sh.uniforms.uSkyH = { value: HORIZON };
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float _paint;\nvarying float vGloss;')
      .replace('#include <color_vertex>', 'vColor = vec4(1.0);\nvColor.rgb *= color.rgb;\nvGloss = _paint > 0.5 ? 0.10 : _paint;\n#ifdef USE_INSTANCING_COLOR\nvColor.rgb *= mix(vec3(1.0), instanceColor.rgb, step(0.5, _paint));\n#endif');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying float vGloss;\nuniform float uCarDay;\nuniform vec3 uSkyZ;\nuniform vec3 uSkyH;')
      .replace('#include <opaque_fragment>', `{
  vec3 vd = normalize(vViewPosition);
  float fr = pow(1.0 - clamp(dot(normal, vd), 0.0, 1.0), 3.0);
  vec3 rw = inverseTransformDirection(reflect(-vd, normal), viewMatrix);
  vec3 env = mix(uSkyH * vec3(0.3, 0.28, 0.25), mix(uSkyH, uSkyZ, smoothstep(0.0, 0.8, rw.y)) * 1.1, smoothstep(-0.05, 0.25, rw.y));
  outgoingLight += env * vGloss * (0.35 + 2.2 * fr) * uCarDay;
}
#include <opaque_fragment>`);
  };
  return m;
})();

/** Deterministic type and paint for a parked car from its key. */
export function carPick(key: number): { type: string; color: THREE.Color } {
  const total = CAR_MIX.reduce((a, [, w]) => a + w, 0);
  let k = (key * 2654435761 >>> 0) % total;
  for (const [type, w] of CAR_MIX) {
    if (k < w) return { type, color: type === 'sport' ? SPORT_PAINT[key % SPORT_PAINT.length] : type === 'van' ? VAN_PAINT[(key >> 3) % VAN_PAINT.length] : CH_PAINT[(key * 7919 >>> 3) % CH_PAINT.length] };
    k -= w;
  }
  return { type: 'hatch', color: CH_PAINT[0] };
}
