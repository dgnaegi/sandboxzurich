import * as THREE from 'three';
import type { createRenderer } from './renderer';
import { HORIZON, ZENITH } from './sky';
import { nightUniform } from './materials';
import { gradeA, gradeB, gradeC, bloom } from './grading';

type Ctx = ReturnType<typeof createRenderer>;

/**
 * Art-directed keyframes in solar hours (Zurich, mid April: sunrise ~5:15, sunset ~18:45). 80s neon palette:
 * turquoise noon, long pink/orange golden hour, violet-blue nights.
 * g = [saturation, contrast, shadow tint rgb, highlight tint rgb, bloom strength, bloom threshold]
 */
type G = [number, number, number, number, number, number, number, number, number, number];
interface Key { h: number; zen: number; hor: number; sun: number; sunI: number; hs: number; hg: number; hI: number; cLo: number; cHi: number; exp: number; night: number; stars: number; g: G }
const GN: G = [1.12, 0.12, -0.02, 0.0, 0.07, 0.04, 0.0, -0.02, 0.85, 0.7];      // night: violet-blue shadows, strong bloom
const GD: G = [1.30, 0.26, -0.05, 0.0, 0.10, 0.07, 0.03, -0.06, 0.22, 1.8];        // day
const GG: G = [1.28, 0.18, 0.02, 0.0, 0.06, 0.12, 0.02, -0.08, 0.45, 1.1];        // golden/pink hour
const K: Key[] = [
  { h: 0,    zen: 0x0e0f3e, hor: 0x3a2a78, sun: 0x6f86c8, sunI: 0,   hs: 0x4a4aa0, hg: 0x20183a, hI: 1.35,  cLo: 0x2a2858, cHi: 0x4a3a7c, exp: 1.45, night: 1,   stars: 1, g: GN },
  { h: 4.5,  zen: 0x0e0f3e, hor: 0x3a2a78, sun: 0x6f86c8, sunI: 0,   hs: 0x4a4aa0, hg: 0x20183a, hI: 1.35,  cLo: 0x2a2858, cHi: 0x4a3a7c, exp: 1.45, night: 1,   stars: 1, g: GN },
  { h: 5.4,  zen: 0x3a3a8c, hor: 0xf08aa8, sun: 0xff9a80, sunI: 1.0, hs: 0x9a8ac8, hg: 0x4a3a58, hI: 1.0,  cLo: 0xf0a0b0, cHi: 0xffc8c8, exp: 1.15, night: 0.4, stars: 0.3, g: GG },
  { h: 6.5,  zen: 0x3a8ad0, hor: 0xffc08a, sun: 0xffc890, sunI: 2.6, hs: 0xd8e0f4, hg: 0x8a7458, hI: 1.3,  cLo: 0xffd0b8, cHi: 0xfff0e0, exp: 1.05, night: 0,   stars: 0, g: GG },
  { h: 8.5,  zen: 0x2a86d8, hor: 0x9fe2ea, sun: 0xfff0dc, sunI: 3.6, hs: 0xd0e8ff, hg: 0x807a68, hI: 1.6,  cLo: 0xeef6f8, cHi: 0xffffff, exp: 1.0,  night: 0,   stars: 0, g: GD },
  { h: 15.5, zen: 0x2a86d8, hor: 0xa4e0e8, sun: 0xfff0dc, sunI: 3.6, hs: 0xd0e8ff, hg: 0x807a68, hI: 1.6,  cLo: 0xeef6f8, cHi: 0xffffff, exp: 1.0,  night: 0,   stars: 0, g: GD },
  { h: 17.0, zen: 0x3a7ad0, hor: 0xffc08a, sun: 0xffd09a, sunI: 3.3, hs: 0xe0d0e8, hg: 0x8a7458, hI: 1.5,  cLo: 0xffd0b0, cHi: 0xfff0e0, exp: 1.05, night: 0,   stars: 0, g: GG },
  { h: 17.9, zen: 0x4a62c0, hor: 0xfa9078, sun: 0xffa060, sunI: 2.7, hs: 0xd0a8d0, hg: 0x7a5050, hI: 1.3,  cLo: 0xff9a8a, cHi: 0xffc8b0, exp: 1.1,  night: 0.05, stars: 0, g: GG },
  { h: 18.6, zen: 0x5a3aa0, hor: 0xff6a9a, sun: 0xff6a50, sunI: 1.8, hs: 0xb890d0, hg: 0x6a4058, hI: 1.4,  cLo: 0xff7a9a, cHi: 0xffb0b8, exp: 1.12, night: 0.25, stars: 0, g: GG },
  { h: 19.4, zen: 0x2a1a70, hor: 0xb04aa0, sun: 0xd0507a, sunI: 0.5, hs: 0x7a6ac0, hg: 0x2a2040, hI: 1.4,  cLo: 0x8a4a90, cHi: 0xd070a0, exp: 1.2,  night: 0.7, stars: 0.5, g: GG },
  { h: 20.5, zen: 0x0e0f3e, hor: 0x3a2a78, sun: 0x6f86c8, sunI: 0,   hs: 0x4a4aa0, hg: 0x20183a, hI: 1.35,  cLo: 0x2a2858, cHi: 0x4a3a7c, exp: 1.45, night: 1,   stars: 1, g: GN },
  { h: 24,   zen: 0x0e0f3e, hor: 0x3a2a78, sun: 0x6f86c8, sunI: 0,   hs: 0x4a4aa0, hg: 0x20183a, hI: 1.35,  cLo: 0x2a2858, cHi: 0x4a3a7c, exp: 1.45, night: 1,   stars: 1, g: GN },
];

const LAT = THREE.MathUtils.degToRad(47.37), DECL = THREE.MathUtils.degToRad(9.5);
const sstep = (a: number, b: number, x: number) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const c1 = new THREE.Color(), c2 = new THREE.Color();
const lerpCol = (out: THREE.Color, a: number, b: number, t: number) => out.setHex(a).lerp(c2.setHex(b), t);

/** Start time in game minutes: `?t=HH:MM` or `?t=18` (hours), default 17:36 (golden evening like the reel). */
export function startMinutes(): number {
  const t = new URLSearchParams(window.location.search).get('t');
  if (t) {
    const [h, m] = t.split(':');
    const v = (parseFloat(h) || 0) * 60 + (parseFloat(m) || 0);
    if (isFinite(v)) return ((v % 1440) + 1440) % 1440;
  }
  return 17 * 60 + 36;
}

export class Daytime {
  /** 0 = day .. 1 = night (also drives window/shop/lamp emission). */
  night = 0;
  /** Sun elevation as sin(angle). */
  sunUp = 1;
  private lamps: THREE.PointLight[] = [];
  private shadowFrames = 0;
  private moonDir = new THREE.Vector3();
  private sunV = new THREE.Vector3();
  private tmp = new THREE.Vector3();

  constructor(private ctx: Ctx) {
    if (!ctx.mobile) {   // PC only: 4 warm lights around the player (cheap stand-in for street lamps)
      for (let i = 0; i < 4; i++) {
        const l = new THREE.PointLight(0xffd9a0, 0, 24, 2);
        this.lamps.push(l);
        ctx.scene.add(l);
      }
    }
    this.set(startMinutes());
  }

  /** Place the lamp lights around the player (call once per frame next to followSun). */
  follow(p: THREE.Vector3): void {
    for (let i = 0; i < this.lamps.length; i++) {
      const a = (i / this.lamps.length) * Math.PI * 2 + 0.6;
      this.lamps[i].position.set(p.x + Math.cos(a) * 11, p.y + 6.5, p.z + Math.sin(a) * 11);
    }
  }

  set(minutes: number): void {
    const { sun, hemi, scene, renderer, skyMat, sunDir } = this.ctx;
    const hr = (((minutes / 60) % 24) + 24) % 24;

    // sun position (east, up, -north) from hour angle
    const ha = (hr - 12) * Math.PI / 12;
    const sinE = Math.sin(LAT) * Math.sin(DECL) + Math.cos(LAT) * Math.cos(DECL) * Math.cos(ha);
    const east = -Math.cos(DECL) * Math.sin(ha);
    const north = Math.sin(DECL) * Math.cos(LAT) - Math.cos(DECL) * Math.sin(LAT) * Math.cos(ha);
    sunDir.set(east, sinE, -north).normalize();
    this.sunUp = sinE;
    this.moonDir.copy(sunDir).negate();

    // keyframes
    let i = 0;
    while (i < K.length - 2 && hr >= K[i + 1].h) i++;
    const a = K[i], b = K[i + 1], t = (hr - a.h) / (b.h - a.h);
    const L = (x: number, y: number) => x + (y - x) * t;

    lerpCol(ZENITH, a.zen, b.zen, t);
    lerpCol(HORIZON, a.hor, b.hor, t);
    (skyMat.uniforms.cloudLo.value as THREE.Color).setHex(a.cLo).lerp(c1.setHex(b.cLo), t);
    (skyMat.uniforms.cloudHi.value as THREE.Color).setHex(a.cHi).lerp(c1.setHex(b.cHi), t);
    const sunCol = lerpCol(new THREE.Color(), a.sun, b.sun, t);
    (skyMat.uniforms.sunCol.value as THREE.Color).copy(sunCol);
    skyMat.uniforms.sun.value.copy(sunDir);
    skyMat.uniforms.moon.value.copy(this.moonDir);
    skyMat.uniforms.stars.value = L(a.stars, b.stars);
    (scene.fog as THREE.Fog).color.copy(HORIZON);

    hemi.color.setHex(a.hs).lerp(c1.setHex(b.hs), t);
    hemi.groundColor.setHex(a.hg).lerp(c1.setHex(b.hg), t);
    hemi.intensity = L(a.hI, b.hI);
    renderer.toneMappingExposure = L(a.exp, b.exp);
    const g = a.g.map((v, k) => v + (b.g[k] - v) * t);
    gradeA.set(g[0] - 1, g[1], 0.32, 0);
    gradeB.set(g[2], g[3], g[4], 0);
    gradeC.set(g[5], g[6], g[7], 0);
    bloom.strength = g[8]; bloom.threshold = g[9];
    this.night = L(a.night, b.night);
    nightUniform.value = this.night;

    // one directional light: sun by day, bluish moon at night (blended by weight)
    const sunW = L(a.sunI, b.sunI) * sstep(-0.04, 0.1, sinE);
    const moonW = 0.5 * this.night * sstep(0.0, 0.2, -sinE);
    const w = sunW + moonW;
    sun.color.copy(sunCol).multiplyScalar(sunW).add(c1.setHex(0x7f93d0).multiplyScalar(moonW)).multiplyScalar(w > 0 ? 1 / w : 0);
    sun.intensity = w;
    this.sunV.copy(sunDir).multiplyScalar(sunW).addScaledVector(this.moonDir, moonW);
    if (this.sunV.lengthSq() > 1e-6) {
      this.tmp.copy(this.sunV).normalize();
      this.tmp.y = Math.max(this.tmp.y, 0.08);   // never light from below the horizon
      sunDir.copy(this.tmp.normalize());         // shadow/light direction used by followSun
    }
    // shadows only while the sun is up; the map is frozen (and faded out) at night
    const shadowOn = sunW > 0.15;
    // render the map at least once, otherwise samplers point at an unallocated depth texture (GL error)
    renderer.shadowMap.autoUpdate = shadowOn || this.shadowFrames++ < 5;
    (sun.shadow as THREE.LightShadow & { intensity: number }).intensity = Math.min(0.85, sunW / 1.4);   // lighter, softer shadows
    skyMat.uniforms.sun.value.set(east, sinE, -north).normalize();

    for (const l of this.lamps) l.intensity = 9 * sstep(0.35, 0.9, this.night);
  }
}

const GLOW = new THREE.Color(0xfff3c8);

/** Makes vertex colours near 0xfff3c8 (lamp lenses in props.ts) glow at night. */
export function glowMaterialPatch(mat: THREE.MeshLambertMaterial): void {
  const prev = mat.onBeforeCompile;
  mat.onBeforeCompile = (sh, r) => {
    prev?.call(mat, sh, r);
    sh.uniforms.night = nightUniform;
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>\nuniform float night;`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        if (night > 0.01 && distance(vColor.rgb, vec3(${GLOW.r.toFixed(4)}, ${GLOW.g.toFixed(4)}, ${GLOW.b.toFixed(4)})) < 0.06)
          totalEmissiveRadiance += vec3(1.0, 0.85, 0.55) * 2.2 * night;`);
  };
  mat.customProgramCacheKey = () => 'glow';
  mat.needsUpdate = true;
}
