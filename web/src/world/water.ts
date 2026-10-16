import * as THREE from 'three';
import { HORIZON, ZENITH } from '../engine/sky';
import { gradeUniforms } from '../engine/grading';
import { nightUniform } from '../engine/materials';
import { nlPos, nlCol, NL_POINTS } from './night_lights';

/** Per-tile shader data from pipeline/water.py: RGBA8 grid (res m): R distance to bank, GB flow xy, A pier proximity. */
export interface WaterMeta { x0: number; y0: number; n: number; res: number; dmax: number; level: number; rgba: string }

const VERT = /* glsl */ `
varying vec3 vWorld;
#include <fog_pars_vertex>
void main() {
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWorld = wp.xyz;
  vec4 mvPosition = viewMatrix * wp;
  gl_Position = projectionMatrix * mvPosition;
  #include <fog_vertex>
}`;

const FRAG = /* glsl */ `
uniform sampler2D data;
uniform vec4 tile;           // x0, y0, n, res
uniform float dmax;
uniform float time;
uniform vec3 sunDir;
uniform vec3 sunCol;
uniform vec3 horizon;
uniform vec3 zenith;
uniform float night;
uniform vec4 nlPos[NLP];
uniform vec3 nlCol[NLP];
varying vec3 vWorld;
#include <fog_pars_fragment>
float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p) {
  vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(h21(i), h21(i + vec2(1.0, 0.0)), f.x), mix(h21(i + vec2(0.0, 1.0)), h21(i + vec2(1.0, 1.0)), f.x), f.y);
}
float fbm(vec2 p) {
  float a = 0.5, s = 0.0;
  for (int i = 0; i < OCT; i++) { s += a * vn(p); p = p * 2.03 + 17.0; a *= 0.5; }
  return s;
}
// wave height gradient in the flow frame (x along the flow, stretched), finite differences
vec2 grad(vec2 p) {
  const float e = 0.1;
  float h0 = fbm(p);
  return vec2(fbm(p + vec2(e, 0.0)) - h0, fbm(p + vec2(0.0, e)) - h0) / e;
}
void main() {
  vec2 tuv = (vec2(vWorld.x - tile.x, -vWorld.z - tile.y) / tile.w + 0.5) / tile.z;
  vec4 d = texture2D(data, tuv);
  float dist = d.r * dmax;
  vec2 f = (d.gb - 128.0 / 255.0) * (255.0 / 127.0);          // flow xy (local, y = north) * strength
  float fl = length(f);
  vec2 fdir = fl > 0.04 ? vec2(f.x, -f.y) / fl : vec2(1.0, 0.0);   // to world xz
  vec2 perp = vec2(-fdir.y, fdir.x);
  float speed = (0.25 + 1.6 * smoothstep(0.1, 0.8, fl)) * (0.35 + 0.65 * smoothstep(0.0, 4.0, dist));
  vec2 xz = vWorld.xz;
  vec2 q = vec2(dot(xz, fdir) * 0.45, dot(xz, perp) * 1.15);
  // two crossfaded phases advected along the flow (flow-map technique)
  const float T = 2.2;
  float p0 = fract(time / T), p1 = fract(time / T + 0.5);
  float w0 = 1.0 - abs(2.0 * p0 - 1.0);
  vec2 drift = vec2(speed * 0.45, 0.0) * T;
  vec2 g0 = grad(q - drift * p0);
  vec2 g1 = grad(q * 1.07 + 3.7 - drift * p1);
  vec2 g = g0 * w0 + g1 * (1.0 - w0);
  float steep = 0.55 + 0.9 * smoothstep(0.1, 0.8, fl);
  vec3 gw = vec3(fdir.x * g.x * 0.45 + perp.x * g.y * 1.15, 0.0, fdir.y * g.x * 0.45 + perp.y * g.y * 1.15);
  vec3 N = normalize(vec3(-gw.x * steep * 0.5, 1.0, -gw.z * steep * 0.5));
  vec3 V = normalize(cameraPosition - vWorld);
  float ndv = clamp(dot(N, V), 0.0, 1.0);
  float fres = 0.025 + 0.975 * pow(1.0 - ndv, 5.0);
  vec3 R = reflect(-V, N); R.y = abs(R.y);
  vec3 sky = mix(horizon, zenith, pow(clamp(R.y, 0.0, 1.0), 0.5));
  sky = mix(horizon * 0.35 + vec3(0.015), sky, smoothstep(0.04, 0.4, R.y));   // houses along the bank darken the low reflection
  float sd = max(dot(R, sunDir), 0.0);
  vec3 spec = sunCol * (pow(sd, 700.0) * 12.0 + pow(sd, 60.0) * 0.5);
  // body: shallow (bed visible, light) near the bank, deep green-turquoise (Limmat/Sihl) in the channel
  float lum = (1.0 - 0.85 * night) * (0.55 + 0.45 * clamp(sunDir.y * 2.0, 0.0, 1.0));
  vec3 shallow = vec3(0.075, 0.2, 0.15), deep = vec3(0.012, 0.075, 0.07);
  vec3 body = mix(shallow, deep, smoothstep(0.2, 5.5, dist)) * lum;
  body += vec3(0.01, 0.04, 0.03) * (vn(q * 0.9 + time * 0.1) - 0.5) * lum;      // slight turbidity patches
  vec3 col = mix(body, sky, clamp(fres * 1.15 + 0.04, 0.0, 0.9)) + spec * clamp(fres + 0.25, 0.0, 1.0);
  // foam: ragged band at the banks, around piers, on fast water
  float nz = fbm(q * 2.4 - vec2(speed * time * 0.6, 0.0));
  float edge = 1.0 - smoothstep(0.05, 0.9 + 0.7 * nz, dist + (nz - 0.5) * 0.5);
  float pier = d.a * smoothstep(0.35, 0.8, nz + d.a * 0.45);
  float foam = clamp(edge * (0.25 + 0.55 * fl) + pier * 0.85, 0.0, 0.9);
  col = mix(col, vec3(0.62, 0.66, 0.66) * (0.35 + 0.65 * lum), foam);
  // night: lamp lights mirrored in the surface (stretched by the ripples)
  if (night > 0.05) {
    vec3 lights = vec3(0.0);
    for (int i = 0; i < NLP; i++) {
      vec3 L = nlPos[i].xyz - vWorld; float r2 = dot(L, L); float Rr = nlPos[i].w * 3.0;
      float a = max(1.0 - r2 / (Rr * Rr), 0.0);
      if (a <= 0.0) continue;
      vec3 l = L * inversesqrt(r2 + 1e-3);
      lights += nlCol[i] * a * (pow(max(dot(R, l), 0.0), 90.0) * 2.2 + pow(max(dot(R, l), 0.0), 12.0) * 0.12);
    }
    col += lights * night * (0.35 + fres);
  }
  gl_FragColor = vec4(col, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
  #include <fog_fragment>
}`;

let sun: THREE.DirectionalLight | null = null;
const uSunDir = { value: new THREE.Vector3(0.3, 0.8, 0.3) };
const uSunCol = { value: new THREE.Color(1, 1, 1) };
const uTime = { value: 0 };

/** One shared shader, one material per tile (own data texture); sky colours and lamp arrays are shared uniforms. */
export function waterMaterial(m: WaterMeta, pc: boolean): THREE.ShaderMaterial {
  const bytes = Uint8Array.from(atob(m.rgba), (c) => c.charCodeAt(0));
  const tex = new THREE.DataTexture(bytes, m.n, m.n, THREE.RGBAFormat);
  tex.magFilter = tex.minFilter = THREE.LinearFilter;
  tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
  tex.needsUpdate = true;
  const mat = new THREE.ShaderMaterial({
    vertexShader: VERT,
    fragmentShader: FRAG,
    fog: true,
    defines: { OCT: pc ? 3 : 2, NLP: NL_POINTS },
    uniforms: THREE.UniformsUtils.merge([THREE.UniformsLib.fog, {
      data: { value: tex }, tile: { value: new THREE.Vector4(m.x0, m.y0, m.n, m.res) }, dmax: { value: m.dmax },
      time: uTime, sunDir: uSunDir, sunCol: uSunCol, horizon: { value: HORIZON }, zenith: { value: ZENITH },
      night: nightUniform, nlPos, nlCol,
    }, gradeUniforms()]),
  });
  mat.userData.tex = tex;
  mat.onBeforeRender = (_r, scene) => {
    uTime.value = (performance.now() / 1000) % 3600;
    if (!sun) sun = scene.children.find((o): o is THREE.DirectionalLight => (o as THREE.DirectionalLight).isDirectionalLight) ?? null;
    if (sun) {
      uSunDir.value.copy(sun.position).sub(sun.target.position).normalize();
      uSunCol.value.copy(sun.color).multiplyScalar(Math.min(1, sun.intensity / 3));
    }
  };
  return mat;
}

export function disposeWater(mat: THREE.Material | THREE.Material[]): void {
  for (const m of Array.isArray(mat) ? mat : [mat]) { (m.userData.tex as THREE.Texture | undefined)?.dispose(); m.dispose(); }
}
