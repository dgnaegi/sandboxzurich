import * as THREE from 'three';
import type { createRenderer } from './renderer';
import { HORIZON, ZENITH } from './sky';
import { nightUniform, hemiK } from './materials';
import { SkyProbe } from './env';
import { gradeA, gradeB, gradeC, bloom } from './grading';

type Ctx = ReturnType<typeof createRenderer>;

/**
 * Keyframes in clock hours (Zurich, mid October: sunrise ~8:00, sunset ~18:45). Natural palette: hazy blue day,
 * warm orange golden hour, blue-grey night with warm lamp highlights.
 * g = [saturation, contrast, shadow tint rgb, highlight tint rgb, bloom strength, bloom threshold]
 */
type G = [number, number, number, number, number, number, number, number, number, number];
interface Key { h: number; zen: number; hor: number; sun: number; sunI: number; hs: number; hg: number; hI: number; cLo: number; cHi: number; exp: number; night: number; stars: number; g: G }
const GN: G = [1.0, 0.10, -0.01, 0.0, 0.03, 0.05, 0.02, -0.04, 0.5, 0.9];       // night: cool shadows, warm lamp highlights
const GD: G = [1.12, 0.14, -0.01, 0.0, 0.02, 0.02, 0.01, -0.01, 0.15, 1.9];        // day: natural
const GG: G = [1.12, 0.12, 0.0, 0.0, 0.0, 0.07, 0.03, -0.05, 0.28, 1.4];          // golden hour: warm highlights
const NIGHT = { zen: 0x070a1c, hor: 0x1e2842, sun: 0x6f86c8, sunI: 0, hs: 0x5468a0, hg: 0x1c1e2c, hI: 1.25, cLo: 0x1c2442, cHi: 0x2c385c, exp: 1.5, night: 1, stars: 1, g: GN };
const DAY = { zen: 0x4a84c6, hor: 0xc6d9e6, sun: 0xfff4e6, sunI: 3.4, hs: 0xbcd2ee, hg: 0x7a7668, hI: 1.45, cLo: 0xdfe5ec, cHi: 0xffffff, exp: 1.0, night: 0, stars: 0, g: GD };
const K: Key[] = [
  { h: 0, ...NIGHT },
  { h: 6.6, ...NIGHT },
  { h: 7.5, zen: 0x2e3e78, hor: 0xd09a8e, sun: 0xff9a68, sunI: 0.9, hs: 0x8a98c0, hg: 0x4a4650, hI: 1.0, cLo: 0xc09aa0, cHi: 0xf0c8b8, exp: 1.2, night: 0.4, stars: 0.2, g: GG },
  { h: 8.3, zen: 0x4a70b4, hor: 0xf0c4a0, sun: 0xffc08a, sunI: 2.2, hs: 0xb4c4e0, hg: 0x706458, hI: 1.25, cLo: 0xf0c8b0, cHi: 0xfff0e4, exp: 1.08, night: 0, stars: 0, g: GG },
  { h: 10.0, ...DAY },
  { h: 15.5, ...DAY },
  { h: 17.2, zen: 0x4a7cc0, hor: 0xe8d0b8, sun: 0xffe0b8, sunI: 3.0, hs: 0xc4d0e4, hg: 0x7c6e58, hI: 1.4, cLo: 0xf0dccc, cHi: 0xfff4ea, exp: 1.04, night: 0, stars: 0, g: GG },
  { h: 18.1, zen: 0x4064aa, hor: 0xf4b078, sun: 0xffa660, sunI: 2.4, hs: 0xb8bcd8, hg: 0x7a5c4c, hI: 1.3, cLo: 0xf4b090, cHi: 0xffd8b8, exp: 1.1, night: 0.05, stars: 0, g: GG },
  { h: 18.8, zen: 0x303e80, hor: 0xe87c50, sun: 0xff7030, sunI: 1.4, hs: 0x9aa0cc, hg: 0x5c4448, hI: 1.25, cLo: 0xe08870, cHi: 0xf4b090, exp: 1.16, night: 0.25, stars: 0, g: GG },
  { h: 19.5, zen: 0x1a2458, hor: 0x8c5c78, sun: 0xc05a50, sunI: 0.35, hs: 0x6c78b0, hg: 0x2a2434, hI: 1.25, cLo: 0x70507a, cHi: 0xa06c88, exp: 1.3, night: 0.7, stars: 0.4, g: GG },
  { h: 20.4, ...NIGHT },
  { h: 24, ...NIGHT },
];

const LAT = THREE.MathUtils.degToRad(47.37), DECL = THREE.MathUtils.degToRad(-8.5)   // mid October;
const sstep = (a: number, b: number, x: number) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const ctx_env = (scene: THREE.Scene, v: number) => { scene.environmentIntensity = v; };
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
  private probe: SkyProbe | null = null;

  constructor(private ctx: Ctx) {
    if (!ctx.mobile) {   // PC only: 4 warm lights around the player (cheap stand-in for street lamps)
      for (let i = 0; i < 4; i++) {
        const l = new THREE.PointLight(0xffd9a0, 0, 24, 2);
        this.lamps.push(l);
        ctx.scene.add(l);
      }
    }
    this.set(startMinutes());
    if (!ctx.mobile) {   // IBL from the sky: desktop tier only (phones keep the hemisphere light + Lambert)
      this.probe = new SkyProbe(ctx.renderer, ctx.scene, ctx.skyMat);
      this.set(startMinutes(), true);
    }
  }

  /** Place the lamp lights around the player (call once per frame next to followSun). */
  follow(p: THREE.Vector3): void {
    for (let i = 0; i < this.lamps.length; i++) {
      const a = (i / this.lamps.length) * Math.PI * 2 + 0.6;
      this.lamps[i].position.set(p.x + Math.cos(a) * 11, p.y + 6.5, p.z + Math.sin(a) * 11);
    }
  }

  set(minutes: number, forceProbe = false): void {
    const { sun, hemi, scene, renderer, skyMat, sunDir } = this.ctx;
    const hr = (((minutes / 60) % 24) + 24) % 24;

    // sun position (east, up, -north) from hour angle
    const ha = (hr - 13.4) * Math.PI / 12;   // clock hour (CEST) -> solar hour angle, Zurich
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
    gradeA.set(g[0] - 1, g[1], 0.2, 0);
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

    // image-based light: day = full sky, night = a little cool ambience; the hemisphere light only fills what IBL does not reach
    if (this.probe) {
      this.probe.update(minutes, forceProbe);
      ctx_env(this.ctx.scene, 0.35 + 0.75 * (1 - this.night));
      hemiK.value = 0.3;
    }
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
