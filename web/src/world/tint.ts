import * as THREE from 'three';
import type { Human, Model, Role } from './humans';

/**
 * Runtime clothing recolour for the baked MakeHuman atlases (no extra textures): every vertex gets a zone mask from its bone weights and
 * rest height (shirt/jacket = torso + arms, trousers = pelvis + legs, shoes = feet), the fragment shader replaces the texel colour by
 * tint x (texel luma / zone mean luma), so folds, seams and stripes survive. Skin on bare forearms is spared (arm vertices with warm texels).
 * Material is cloned per person (uniforms differ); geometry and texture stay shared.
 */
const AUTUMN_TOPS = [0x1f2b45, 0x15171a, 0x4a5a2e, 0x9a7b4f, 0x7a2430, 0xb8862b, 0x6b7077, 0x1d4a36, 0xa5522a, 0xd8cdb6, 0x2c6a73, 0x8a2f2f, 0x3a3f66, 0xc9c4bb, 0x5a3b2a, 0xd9a2b0, 0x4f6f9a];
const TROUSERS = [0x2d4568, 0x1b1d22, 0x4b4f58, 0xb8aa8a, 0x55583a, 0x4a3828, 0x6a7fa3, 0x23262d, 0x7d6b50];
const SHOES = [0xf0f0ec, 0x16171a, 0x4a3426, 0x6d7074, 0x1f2a44, 0xb5482c, 0xd9d4c4];

/** Natural hair colours (dark -> light); `HAIR_DARK` for dark skin, `HAIR_OLD` for grey/white. A little dyed colour (Kreis 4/5). */
const HAIR_DARK = [0x14100e, 0x1c130d, 0x2a1a10, 0x34200f];
const HAIR_NAT = [0x14100e, 0x2a1a10, 0x3a2414, 0x4a3020, 0x6b4126, 0x8a6a45, 0xb99a62, 0xc9ae78, 0x8a3f1c];
const HAIR_OLD = [0x8d8d8a, 0xa6a6a2, 0xc9c8c2, 0x6e6c68, 0xdad8d0];
const HAIR_DYED = [0x7a2236, 0x3b2a6a, 0x1f5a5a, 0xa04b6e];
/** Baked-in hats (npc_17 ...): their hat mesh is part of the head, so the hair tint must stay off. */
const BAKED_HAT = new Set(['npc_17', 'npc_23', 'npc_25', 'npc_32', 'npc_35', 'npc_39']);

interface Uniforms {
  uT0: THREE.IUniform<THREE.Color>; uT1: THREE.IUniform<THREE.Color>; uT2: THREE.IUniform<THREE.Color>; uAvg: THREE.IUniform<THREE.Vector3>; uAmt: THREE.IUniform<THREE.Vector3>;
  uHair: THREE.IUniform<THREE.Color>; uHairAvg: THREE.IUniform<number>; uHairAmt: THREE.IUniform<number>; uSkinFix: THREE.IUniform<THREE.Vector3>; uSkinRef: THREE.IUniform<THREE.Vector3>; uSkinTone: THREE.IUniform<THREE.Vector3>;
}
interface TintState { u: Uniforms }
/** Per-model data computed once from the atlas + skin weights. */
interface Prep { skinRef: THREE.Vector3; avg: THREE.Vector3; hairAvg: number; hasHair: boolean; skinFix: THREE.Vector3; dark: boolean }
const state = new WeakMap<Human, TintState>();
const prepared = new WeakMap<Model, Prep>();
/** What a person was dressed in (read by HumanLib to match hood, beard, ...). */
export interface Look { top: number; hair: number | null; dark: boolean }

const lin = (c: number) => Math.pow(c / 255, 2.2);

/** Zone attribute + zone mean luma, once per model (shared geometry). Returns false when the model has no skinned mesh. */
export function prepareTint(m: Model): boolean {
  if (prepared.has(m)) return true;
  let mesh: THREE.SkinnedMesh | null = null;
  m.scene.traverse((o) => { if ((o as THREE.SkinnedMesh).isSkinnedMesh && !mesh) mesh = o as THREE.SkinnedMesh; });
  const sm = mesh as THREE.SkinnedMesh | null;
  if (!sm) return false;
  m.scene.updateMatrixWorld(true);
  const g = sm.geometry, pos = g.attributes.position, si = g.attributes.skinIndex, sw = g.attributes.skinWeight, uv = g.attributes.uv;
  const role = sm.skeleton.bones.map((b) => {
    const n = b.name;
    if (/^(spine_0|clavicle|upperarm|lowerarm)/.test(n)) return /arm/.test(n) && !/^clavicle/.test(n) ? 4 : 1;     // 4 = arm (skin check), 1 = shirt
    if (/^(pelvis|thigh|calf)/.test(n)) return 2;
    if (/^(foot|ball)/.test(n)) return 3;
    return 0;                                                                                                     // head, neck, hands, fingers
  });
  const kind = sm.skeleton.bones.map((b) => (/^(hand|thumb|index|middle|ring|pinky)/.test(b.name) ? 'hand' : b.name === 'head' ? 'head' : b.name === 'neck_01' ? 'neck' : ''));
  // connected components of the triangle mesh: loose hair meshes sit on the head bone and are not welded to the body
  const par = new Int32Array(pos.count).map((_, i) => i), find = (a: number): number => { while (par[a] !== a) { par[a] = par[par[a]]; a = par[a]; } return a; };
  const ix = g.index, seen = new Map<string, number>();   // glTF duplicates vertices along UV seams: weld by position first
  for (let i = 0; i < pos.count; i++) { const k = `${Math.round(pos.getX(i) * 4000)},${Math.round(pos.getY(i) * 4000)},${Math.round(pos.getZ(i) * 4000)}`, f = seen.get(k); if (f === undefined) seen.set(k, i); else par[i] = f; }
  if (ix) for (let i = 0; i < ix.count; i += 3) { const a = find(ix.getX(i)), b = find(ix.getX(i + 1)), c = find(ix.getX(i + 2)); par[b] = a; par[find(c)] = a; }
  const comp = new Map<number, { n: number; head: number; y1: number; lo: number[]; hi: number[] }>(), zone2 = new Float32Array(pos.count * 4);
  const zone = new Float32Array(pos.count * 4), v = new THREE.Vector3(), h = m.height;
  for (let i = 0; i < pos.count; i++) {
    let hw = 0; for (let k = 0; k < 4; k++) if (kind[si.getComponent(i, k)] === 'head') hw += sw.getComponent(i, k);
    v.fromBufferAttribute(pos, i).applyMatrix4(sm.matrixWorld);
    const r = find(i), c = comp.get(r) ?? { n: 0, head: 0, y1: -9, lo: [9, 9, 9], hi: [-9, -9, -9] };
    c.n++; c.head += hw; c.y1 = Math.max(c.y1, v.y); for (let k = 0; k < 3; k++) { const q = v.getComponent(k); c.lo[k] = Math.min(c.lo[k], q); c.hi[k] = Math.max(c.hi[k], q); } comp.set(r, c);
  }
  let big = 0, headMass = 0; for (const c of comp.values()) { big = Math.max(big, c.n); headMass += c.head; }
  const hairRoot = new Set<number>();
  if (!BAKED_HAT.has(m.id)) for (const [r, c] of comp) if (c.n < big && c.head < 0.4 * headMass && c.head / c.n > 0.45 && c.y1 > 0.8 * h && Math.max(c.hi[0] - c.lo[0], c.hi[1] - c.lo[1], c.hi[2] - c.lo[2]) > 0.045) hairRoot.add(r);
  for (let i = 0; i < pos.count; i++) {
    let sh = 0, tr = 0, fo = 0, arm = 0;
    for (let k = 0; k < 4; k++) {
      const w = sw.getComponent(i, k), r = role[si.getComponent(i, k)];
      if (r === 1) sh += w; else if (r === 4) { sh += w; arm += w; } else if (r === 2) tr += w; else if (r === 3) fo += w;
    }
    v.fromBufferAttribute(pos, i).applyMatrix4(sm.matrixWorld);
    const y = v.y / h;                                                                                            // 0 = sole, 1 = top of head
    const shoe = fo * (1 - Math.min(1, Math.max(0, (y - 0.045) / 0.03)));                                        // only the lowest ~7 cm count as shoe
    zone[i * 4] = Math.min(1, sh); zone[i * 4 + 1] = Math.min(1, tr + fo - shoe); zone[i * 4 + 2] = shoe; zone[i * 4 + 3] = arm;
    let hd = 0; for (let k = 0; k < 4; k++) if (kind[si.getComponent(i, k)] === 'hand') hd += sw.getComponent(i, k);
    zone2[i * 4] = Math.min(1, hd); zone2[i * 4 + 1] = hairRoot.has(find(i)) ? 1 : 0;
  }
  g.setAttribute('aZone', new THREE.BufferAttribute(zone, 4)); g.setAttribute('aZone2', new THREE.BufferAttribute(zone2, 4));
  // zone mean luma from the atlas texels under the zone's vertices
  const avg = new THREE.Vector3(0.3, 0.3, 0.3), skinFix = new THREE.Vector3(1, 1, 1), skinRef = new THREE.Vector3(0.46, 0.32, 0.22);
  let hairAvg = 0.1, dark = false;
  const img = (sm.material as THREE.MeshStandardMaterial).map?.image as CanvasImageSource | undefined;
  try {
    if (img && uv) {
      const S = 256, c = document.createElement('canvas'); c.width = c.height = S;
      const cx = c.getContext('2d', { willReadFrequently: true })!; cx.drawImage(img, 0, 0, S, S);
      const d = cx.getImageData(0, 0, S, S).data, sum = [0, 0, 0], cnt = [0, 0, 0];
      for (let i = 0; i < pos.count; i++) {
        const px = Math.min(S - 1, Math.max(0, Math.floor(uv.getX(i) * S))), py = Math.min(S - 1, Math.max(0, Math.floor(uv.getY(i) * S))), o = (py * S + px) * 4;
        const L = 0.299 * lin(d[o]) + 0.587 * lin(d[o + 1]) + 0.114 * lin(d[o + 2]);
        for (let z = 0; z < 3; z++) if (zone[i * 4 + z] > 0.9 && (z > 0 || zone[i * 4 + 3] < 0.1)) { sum[z] += L; cnt[z]++; }
      }
      for (let z = 0; z < 3; z++) if (cnt[z] > 8) avg.setComponent(z, Math.max(0.02, sum[z] / cnt[z]));
      // hair mean luma; hand skin -> face skin colour ratio (median, robust against lips/eyes): the baked hands come out paler or darker than the face
      const hand: number[][] = [[], [], []], face: number[][] = [[], [], []]; let hs = 0, hc = 0;
      for (let i = 0; i < pos.count; i++) {
        const px = Math.min(S - 1, Math.max(0, Math.floor(uv.getX(i) * S))), py = Math.min(S - 1, Math.max(0, Math.floor(uv.getY(i) * S))), o = (py * S + px) * 4;
        const r = lin(d[o]), gg = lin(d[o + 1]), b = lin(d[o + 2]);
        if (zone2[i * 4 + 1] > 0.5) { hs += 0.299 * r + 0.587 * gg + 0.114 * b; hc++; }
        if (zone2[i * 4] > 0.9) { hand[0].push(r); hand[1].push(gg); hand[2].push(b); }
        let hw = 0; for (let k = 0; k < 4; k++) if (kind[si.getComponent(i, k)] === 'head') hw += sw.getComponent(i, k);
        if (hw > 0.9 && zone2[i * 4 + 1] < 0.5) { face[0].push(r); face[1].push(gg); face[2].push(b); }
      }
      const med = (a: number[]) => (a.sort((x, y) => x - y), a[a.length >> 1]);
      if (hc > 20) hairAvg = Math.max(0.01, hs / hc);
      if (face[0].length > 30) { const f = [med(face[0]), med(face[1]), med(face[2])]; dark = 0.299 * f[0] + 0.587 * f[1] + 0.114 * f[2] < 0.1;
        if (hand[0].length > 20) { const hm = [med(hand[0]), med(hand[1]), med(hand[2])], t = hm[0] + hm[1] + hm[2] + 1e-4; skinRef.set(hm[0] / t, hm[1] / t, hm[2] / t); }
        if (hand[0].length > 20) for (let k = 0; k < 3; k++) skinFix.setComponent(k, Math.min(1.35, Math.max(0.75, f[k] / (med(hand[k]) + 1e-4)))); }
    }
  } catch { /* tainted/unsupported image: keep defaults */ }
  if (typeof location !== "undefined" && location.search.includes("dbgtint")) console.log("TINT", m.id, "fix", skinFix.toArray().map((x) => +x.toFixed(2)), "dark", dark, "hair", hairRoot.size, hairAvg.toFixed(3), "comps", comp.size, big);
  prepared.set(m, { skinRef, avg, hairAvg, hasHair: hairRoot.size > 0, skinFix, dark });
  return true;
}

function attach(h: Human, m: Model): TintState | null {
  const pr = prepared.get(m);
  if (!pr) return null;
  let st = state.get(h);
  if (st) return st;
  const u: Uniforms = { uT0: { value: new THREE.Color() }, uT1: { value: new THREE.Color() }, uT2: { value: new THREE.Color() }, uAvg: { value: pr.avg.clone() }, uAmt: { value: new THREE.Vector3() },
    uHair: { value: new THREE.Color() }, uHairAvg: { value: pr.hairAvg }, uHairAmt: { value: 0 }, uSkinFix: { value: pr.skinFix.clone() }, uSkinRef: { value: pr.skinRef.clone() }, uSkinTone: { value: new THREE.Vector3(1, 1, 1) } };
  h.root.traverse((o) => {
    const sm = o as THREE.SkinnedMesh;
    if (!sm.isSkinnedMesh) return;
    const mat = (sm.material as THREE.MeshStandardMaterial).clone();
    mat.onBeforeCompile = (sh) => {
      Object.assign(sh.uniforms, u);
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute vec4 aZone; attribute vec4 aZone2; varying vec4 vZone; varying vec4 vZone2;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvZone = aZone; vZone2 = aZone2;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec4 vZone; varying vec4 vZone2; uniform vec3 uT0, uT1, uT2, uAvg, uAmt, uHair, uSkinFix, uSkinRef, uSkinTone; uniform float uHairAvg, uHairAmt; float gRough = 0.85;')
        .replace('#include <map_fragment>', `#include <map_fragment>
        {
          float L = dot(diffuseColor.rgb, vec3(0.299, 0.587, 0.114));
          float Ls = mix(L, dot(texture2D(map, vMapUv, 3.0).rgb, vec3(0.299, 0.587, 0.114)), 0.55);   // blurred luma: folds stay, pinstripes soften
          vec3 chrom = diffuseColor.rgb / (diffuseColor.r + diffuseColor.g + diffuseColor.b + 1e-4);
          float bare = vZone.w * (1.0 - smoothstep(0.035, 0.08, distance(chrom, uSkinRef))) * smoothstep(0.02, 0.06, L);   // bare forearm skin = texels near the hand colour
          vec3 zn = smoothstep(0.47, 0.53, vZone.xyz);                      // hard edge jacket / trousers / shoes
          float hr = step(0.5, vZone2.y), hd = step(0.5, vZone2.x);
          float fw = fwidth(vMapUv.x) + fwidth(vMapUv.y), fine = 1.0 - smoothstep(0.003, 0.010, fw);   // micro detail only when texels are big on screen
          float cloth = max(zn.x * (1.0 - bare), zn.y);
          float skin = 1.0 - clamp(cloth + zn.z + hr, 0.0, 1.0);
          vec3 c = diffuseColor.rgb;
          c *= mix(vec3(1.0), uSkinFix, max(hd, bare)) * mix(vec3(1.0), uSkinTone, skin);
          float weave = 1.0 + fine * 0.055 * sin(vMapUv.x * 1900.0) * sin(vMapUv.y * 1900.0);
          c = mix(c, uT0 * clamp(Ls / uAvg.x, 0.3, 2.2) * weave, zn.x * uAmt.x * (1.0 - bare));
          c = mix(c, uT1 * clamp(Ls / uAvg.y, 0.3, 2.2) * weave, zn.y * uAmt.y);
          c = mix(c, uT2 * clamp(L / uAvg.z, 0.3, 2.2), zn.z * uAmt.z);
          float strand = 1.0 + fine * 0.14 * sin(vMapUv.x * 1300.0 + 5.0 * sin(vMapUv.y * 160.0));
          c = mix(c, uHair * clamp(Ls / uHairAvg, 0.4, 2.2) * strand, hr * uHairAmt);
          diffuseColor.rgb = c;
          gRough = mix(mix(0.62, 0.52, hr), 0.95, cloth);
          gRough = mix(gRough, 0.55, zn.z);
        }`)
        .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n roughnessFactor = gRough;');
    };
    mat.customProgramCacheKey = () => 'humanTint';
    sm.material = mat;
  });
  st = { u }; state.set(h, st);
  return st;
}

const pick = <T,>(a: T[], r: number) => a[Math.floor(r * a.length) % a.length];

/**
 * Random autumn outfit colours, hair colour and skin tone for a person (null look = child / no skinned mesh). `m` = the figure's model.
 * Cheap: only uniforms change. Returns what was chosen so the caller can match accessories (hood colour, beard).
 */
export function dress(h: Human, m: Model, keep = 0.25, role: Role = 'any'): Look | null {
  if (!prepareTint(m)) return null;
  const st = attach(h, m), pr = prepared.get(m);
  if (!st || !pr) return null;
  const r = Math.random, u = st.u;
  u.uSkinTone.value.set(1 + (r() - 0.5) * 0.12, 1 + (r() - 0.5) * 0.1, 1 + (r() - 0.5) * 0.14);
  const top = pick(AUTUMN_TOPS, r());
  if (m.age === 'child') { u.uAmt.value.set(0, 0, 0); u.uHairAmt.value = 0; return { top: 0, hair: null, dark: pr.dark }; }
  u.uAmt.value.set(r() < keep ? 0 : 1, r() < keep + 0.1 ? 0 : 1, r() < 0.35 ? 0 : 1);
  let tr = pick(TROUSERS, r()), sh = pick(SHOES, r()), tp = top;
  if (role === 'builder') { tr = pick([0x23262d, 0x2d4568, 0x4b4f58, 0x55583a], r()); sh = pick([0x4a3426, 0x16171a], r()); tp = pick([0x4b4f58, 0x1f2b45, 0x15171a, 0x6b7077], r()); u.uAmt.value.set(1, 1, 1); }
  else if (role === 'office') { tr = pick([0x23262d, 0x1b1d22, 0x2d4568, 0x4b4f58], r()); sh = pick([0x16171a, 0x4a3426, 0x16171a], r()); tp = pick([0x1f2b45, 0xc9c4bb, 0x4f6f9a, 0x15171a, 0x6b7077, 0xd9d4c4], r()); u.uAmt.value.set(1, 1, 1); }
  else if (role === 'courier') { tr = pick([0x1b1d22, 0x23262d, 0x4b4f58], r()); sh = pick([0x16171a, 0xf0f0ec], r()); u.uAmt.value.set(1, 1, 1); }
  u.uT0.value.set(tp); u.uT1.value.set(tr); u.uT2.value.set(sh);
  let hair: number | null = null;
  if (pr.hasHair && r() < 0.75) {
    hair = pr.dark ? pick(HAIR_DARK, r()) : m.age === 'old' ? pick(HAIR_OLD, r()) : r() < 0.04 ? pick(HAIR_DYED, r()) : m.age === 'mid' && r() < 0.3 ? pick(HAIR_OLD, r()) : pick(HAIR_NAT, r());
    u.uHair.value.set(hair);
  }
  u.uHairAmt.value = hair === null ? 0 : 1;
  return { top: tp, hair, dark: pr.dark };
}

/** Force the shirt colour of a dressed person (hoodie colour = hood colour). */
export function setTop(h: Human, hex: number) {
  const st = state.get(h);
  if (!st) return;
  st.u.uT0.value.set(hex); st.u.uAmt.value.x = 1;
}
