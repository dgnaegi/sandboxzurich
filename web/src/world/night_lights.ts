import * as THREE from 'three';

/**
 * Cheap fake night lighting without real lights: the world material evaluates the nearest street lamps / shop windows
 * (point terms) and car headlights (cone terms) from uniform arrays. Tiles register their sources, the player-near
 * subset is picked every few frames. Phones use fewer sources.
 */
const MOBILE = /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent) || (navigator.maxTouchPoints > 1 && Math.min(screen.width, screen.height) < 820);
export const NL_POINTS = MOBILE ? 10 : 20;
export const NL_CARS = MOBILE ? 4 : 8;

export const nlPos = { value: Array.from({ length: NL_POINTS }, () => new THREE.Vector4(0, -1e4, 0, 1)) };
export const nlCol = { value: Array.from({ length: NL_POINTS }, () => new THREE.Vector3()) };
export const nlCar = { value: Array.from({ length: NL_CARS }, () => new THREE.Vector4(0, -1e4, 0, 0)) };
export const nlDir = { value: Array.from({ length: NL_CARS }, () => new THREE.Vector3(1, 0, 0)) };
/** 0..1 wet-road sheen (PC only, set by Daytime). */
export const nlWet = { value: 0 };

export const NIGHT_LIGHT_GLSL = /* glsl */ `
uniform vec4 nlPos[${NL_POINTS}]; uniform vec3 nlCol[${NL_POINTS}];
uniform vec4 nlCar[${NL_CARS}]; uniform vec3 nlDir[${NL_CARS}];
uniform float nlWet;
vec3 nightLight(vec3 wp, vec3 n){
  vec3 acc = vec3(0.0);
  vec3 V = normalize(cameraPosition - wp);
  float up = step(0.5, n.y);
  for (int i = 0; i < ${NL_POINTS}; i++) {
    vec3 d = nlPos[i].xyz - wp; float r2 = dot(d, d); float R = nlPos[i].w;
    float a = max(1.0 - r2 / (R * R), 0.0); a *= a;
    if (a <= 0.0) continue;
    vec3 l = d * inversesqrt(r2 + 1e-3);
    float lit = max(dot(n, l), 0.0) * a;
    acc += nlCol[i] * lit;
    if (nlWet > 0.01 && up > 0.5) {   // wet asphalt: stretched highlight of the lamp
      vec3 rv = reflect(-V, n);
      acc += nlCol[i] * a * nlWet * pow(max(dot(rv, l), 0.0), 40.0) * 2.5;
    }
  }
  for (int j = 0; j < ${NL_CARS}; j++) {
    vec4 P = nlCar[j]; if (P.w <= 0.0) continue;
    vec3 d = wp - P.xyz; float len = length(d) + 1e-3;
    float along = dot(d, nlDir[j]) / len;
    vec3 l = normalize(P.xyz - wp + vec3(0.0, 2.5, 0.0));
    float ndl = max(dot(n, l), 0.0);
    float cone = smoothstep(0.82, 0.96, along) * pow(max(1.0 - len / 30.0, 0.0), 1.5);
    float tail = pow(max(1.0 - len / 4.5, 0.0), 2.0) * smoothstep(0.1, -0.5, along);
    acc += (vec3(1.0, 0.88, 0.62) * cone * 1.6 + vec3(1.0, 0.1, 0.05) * tail * 0.5) * ndl * P.w;
  }
  return acc * 0.6;   // tuned: pools at full strength burned the sidewalks to white (Hohlstrasse)
}`;

interface Src { owner: THREE.Object3D; born: number; pts: Float32Array }   // pts: x,y,z (three), radius, r,g,b
const srcs: Src[] = [];
let frame = 0;

/** Register light points of a tile. `owner` must end up in the scene graph (it is dropped once detached). */
export function registerLights(owner: THREE.Object3D, pts: number[]): void {
  if (pts.length) srcs.push({ owner, born: frame, pts: new Float32Array(pts) });
}

/** Forget light sources of tiles that were removed from the scene (called on tile unload). */
export function purgeLights(): void {
  for (let k = srcs.length - 1; k >= 0; k--) if (srcs[k].owner.parent && !attached(srcs[k].owner)) srcs.splice(k, 1);
}

const attached = (o: THREE.Object3D) => { let p: THREE.Object3D | null = o; while (p) { if ((p as THREE.Scene).isScene) return true; p = p.parent; } return false; };
const best = new Float32Array(NL_POINTS * 8);

/** Pick the nearest points around (x,z) into the uniforms. */
export function refreshLights(x: number, z: number, night: number): void {
  frame++;
  for (let k = srcs.length - 1; k >= 0; k--) if (frame - srcs[k].born > 600 && !attached(srcs[k].owner)) srcs.splice(k, 1);
  let n = 0;
  const R2 = 75 * 75;
  for (const s of srcs) {
    const a = s.pts;
    for (let i = 0; i < a.length; i += 7) {
      const dx = a[i] - x, dz = a[i + 2] - z, d2 = dx * dx + dz * dz;
      if (d2 > R2) continue;
      const score = d2 / (a[i + 3] * a[i + 3]);   // small radii (shop windows) only count when close
      let pos = n < NL_POINTS ? n++ : -1;
      if (pos < 0) {   // replace the worst entry if better
        let w = 0; for (let j = 1; j < NL_POINTS; j++) if (best[j * 8] > best[w * 8]) w = j;
        if (best[w * 8] <= score) continue;
        pos = w;
      }
      best[pos * 8] = score; for (let j = 0; j < 7; j++) best[pos * 8 + 1 + j] = a[i + j];
    }
  }
  const on = night > 0.05;
  for (let j = 0; j < NL_POINTS; j++) {
    const p = nlPos.value[j], c = nlCol.value[j];
    if (j < n && on) { p.set(best[j * 8 + 1], best[j * 8 + 2], best[j * 8 + 3], best[j * 8 + 4]); c.set(best[j * 8 + 5], best[j * 8 + 6], best[j * 8 + 7]); }
    else { p.set(0, -1e4, 0, 1); c.set(0, 0, 0); }
  }
}

let nCars = 0;
/** Headlight cones for cars (three coords of the front lamps, unit direction in xz, strength 0..1). Call per frame, reset with beginCars(). */
export function beginCars(): void { nCars = 0; }
export function addCar(x: number, y: number, z: number, dx: number, dz: number, w = 1): void {
  if (nCars >= NL_CARS) return;
  nlCar.value[nCars].set(x, y, z, w); nlDir.value[nCars].set(dx, 0, dz); nCars++;
}
export function endCars(): void { for (let j = nCars; j < NL_CARS; j++) nlCar.value[j].set(0, -1e4, 0, 0); }
export const carSlots = () => NL_CARS;
