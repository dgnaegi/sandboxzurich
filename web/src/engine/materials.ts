import * as THREE from 'three';
import { NIGHT_LIGHT_GLSL, nlPos, nlCol, nlCar, nlDir, nlWet } from '../world/night_lights';

/** Shared night factor (0 = day .. 1 = night) for all patched materials (windows, shopfronts, lamps). */
export const nightUniform = { value: 0 };
export function setNight(v: number): void { nightUniform.value = v; }

/**
 * One shared material for all tile geometry: a texture array (facades, shopfronts, roofs, ground)
 * selected per vertex (uv1.x), UVs in repeats (uv), vertex colour = tint applied where the mask (alpha) is set.
 */
/** Scale of the hemisphere light on the world material (IBL replaces most of it when an environment map is set). */
export const hemiK = { value: 1 };

export async function loadWorldMaterial(base: string, anisotropy: number, pbr = false): Promise<THREE.Material> {
  const meta = await (await fetch(`${base}/layers.json`)).json() as { size: number; cols: number; count: number; facades: number; shops_end: number; normals: number; normals3?: number; facades3?: [number, number]; layers?: string[]; shops2?: [number, number]; ground_n?: number[] };
    // phones (no pbr): half-resolution atlas + mask – the full one needs ~120 MB GPU + ~90 MB JS and crashed iOS Safari
  const half = pbr ? '' : '_half', fb = <T>(p: Promise<T>, f: () => Promise<T>) => p.catch(f);
  const [rgb, mask, nimg] = await Promise.all([fb(loadImage(`${base}/atlas${half}.webp`), () => loadImage(`${base}/atlas.webp`)), fb(loadImage(`${base}/atlas_mask${half}.png`), () => loadImage(`${base}/atlas_mask.png`)), loadImage(`${base}/atlas_n${pbr ? '' : '_half'}.webp`).catch(() => loadImage(`${base}/atlas_n.webp`))]);
  const L = Math.round(rgb.width / meta.cols), n = meta.count;   // layer size from the loaded image (512 PC, 256 phone)
  const pix = (img: HTMLImageElement) => {
    const c = document.createElement('canvas');
    c.width = img.width; c.height = img.height;
    const g = c.getContext('2d', { willReadFrequently: true })!;
    g.drawImage(img, 0, 0);
    return g.getImageData(0, 0, img.width, img.height).data;
  };
  const a = pix(rgb), m = pix(mask), W = rgb.width;
  const data = new Uint8Array(L * L * 4 * n);
  for (let k = 0; k < n; k++) {
    const ox = (k % meta.cols) * L, oy = Math.floor(k / meta.cols) * L;
    for (let y = 0; y < L; y++) {
      let src = ((oy + y) * W + ox) * 4, dst = (k * L * L + y * L) * 4;
      for (let x = 0; x < L; x++, src += 4, dst += 4) {
        data[dst] = a[src]; data[dst + 1] = a[src + 1]; data[dst + 2] = a[src + 2]; data[dst + 3] = m[src];
      }
    }
  }
  // normal array (R,G = normal xy, B = roughness, unused with Lambert): only the layers that have one
  const gN = meta.ground_n ?? [];   // ground layers with normal+roughness slots after the v3 facades
  const Ln = Math.round((L * nimg.width) / rgb.width);   // phones load a half-size normal atlas
  const nn = meta.normals + (meta.normals3 ?? 0) + gN.length, nd = new Uint8Array(Ln * Ln * 4 * nn), np_ = pix(nimg);
  for (let k = 0; k < nn; k++) {
    const ox = (k % meta.cols) * Ln, oy = Math.floor(k / meta.cols) * Ln;
    for (let y = 0; y < Ln; y++) {
      let src = ((oy + y) * nimg.width + ox) * 4, dst = (k * Ln * Ln + y * Ln) * 4;
      for (let x = 0; x < Ln; x++, src += 4, dst += 4) {
        nd[dst] = np_[src]; nd[dst + 1] = np_[src + 1]; nd[dst + 2] = np_[src + 2]; nd[dst + 3] = 255;
      }
    }
  }
  const setup = (t: THREE.DataArrayTexture, srgb: boolean) => {
    t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.magFilter = THREE.LinearFilter;
    t.minFilter = THREE.LinearMipmapLinearFilter;
    t.generateMipmaps = true;
    t.anisotropy = anisotropy;
    t.needsUpdate = true;
    return t;
  };
  const tex = setup(new THREE.DataArrayTexture(data, L, L, n), true);
  const ntex = setup(new THREE.DataArrayTexture(nd, Ln, Ln, nn), false);
  if (!pbr) for (const t of [tex, ntex]) t.onUpdate = () => { (t.image as { data: Uint8Array | null }).data = null; }; // phones: drop the JS copy once on the GPU
  const F = meta.facades.toFixed(1), S = meta.shops_end.toFixed(1), N = meta.normals.toFixed(1);
  const [A3, B3] = (meta.facades3 ?? [9999, 9999]).map((v) => v.toFixed(1));

  const mat: THREE.Material = pbr ? new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9, metalness: 0 }) : new THREE.MeshLambertMaterial({ vertexColors: true });
  const GB = (meta.normals + (meta.normals3 ?? 0)).toFixed(1);
  const li = (name: string) => (meta.layers?.indexOf(name) ?? -1).toFixed(1);
  const AS = li('asphalt'), G0 = li('sidewalk'), G1 = li('white');
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.atlas = { value: tex };
    sh.uniforms.night = nightUniform;
    sh.uniforms.hemiK = hemiK;
    sh.uniforms.nlPos = nlPos; sh.uniforms.nlCol = nlCol; sh.uniforms.nlCar = nlCar; sh.uniforms.nlDir = nlDir; sh.uniforms.nlWet = nlWet;
    sh.uniforms.normalAtlas = { value: ntex };
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\n#ifndef USE_UV1\nattribute vec2 uv1;\n#endif\nvarying vec2 vTex;\nvarying float vLayer;\nvarying vec3 vWorld;\nvarying vec3 vWN;')
      .replace('#include <beginnormal_vertex>', '#include <beginnormal_vertex>\nvWN = normalize(mat3(modelMatrix) * objectNormal);')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvTex = uv;\nvLayer = uv1.x;\nvWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform highp sampler2DArray atlas;\nuniform highp sampler2DArray normalAtlas;\nuniform float night;\nuniform float hemiK;\nvarying vec2 vTex;\nvarying float vLayer;\nvarying vec3 vWorld;\nvarying vec3 vWN;\n' + NIGHT_LIGHT_GLSL + groundSlotFn(gN, GB) + GROUND_FN + nightFn(F, S, shopHours(meta, F), (meta.shops2?.[0] ?? 9999).toFixed(1), (meta.shops2?.[1] ?? 9999).toFixed(1), A3, B3))
      .replace('#include <color_fragment>',
        'vec4 tx = texture(atlas, vec3(vTex, floor(vLayer + 0.5)));\n' +
        'float fl3 = step(' + A3 + ' - 0.5, vLayer) * step(vLayer, ' + B3 + ' - 0.5);\n' +
        'diffuseColor.rgb *= tx.rgb * mix(vec3(1.0), vColor.rgb * mix(1.0, 1.35, fl3), tx.a);\n' +
        'diffuseColor.rgb *= 1.0 - 0.3 * step(abs(vLayer - ' + AS + '), 0.5);     // asphalt darker\n' +
        // ground: world-space macro variation (breaks the 2.5-5 m texture repeat) + rotated low-frequency detail sample (PC)
        'if (groundSlot(floor(vLayer + 0.5)) > -0.5) {\n' +
        '  vec2 wp = vWorld.xz;\n' +
        '  float m = vn2(wp / 31.0) * 0.55 + vn2(wp / 8.5 + 3.7) * 0.3 + vn2(wp / 2.3 + 9.1) * 0.15;\n' +
        '  float h2 = vn2(wp / 47.0 + 21.0);\n' +
        '  diffuseColor.rgb *= (0.84 + 0.32 * m) * vec3(1.0 + 0.05 * (h2 - 0.5), 1.0, 1.0 - 0.05 * (h2 - 0.5));\n' +
        (pbr ? '  if (abs(vWN.y) > 0.5) {\n    vec3 t2 = vec3(mat2(0.8, 0.6, -0.6, 0.8) * vTex * 0.43 + 0.37, floor(vLayer + 0.5));\n    float dl = dot(textureLod(atlas, t2, 2.0).rgb - textureLod(atlas, t2, 9.0).rgb, vec3(0.333));\n    diffuseColor.rgb *= 1.0 + 0.9 * dl;\n  }\n' : '') +
        '}\n' +
        // glass = unmasked dark texels on wall faces of facade layers (same test as the night windows)
        'float glass = 0.0;\n' +
        'if (abs(vWN.y) < 0.5 && (vLayer < ' + F + ' - 0.5 || fl3 > 0.5)) glass = glassMask(tx);')
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\n' + (pbr ? 'roughnessFactor = mix(vLayer > ' + G0 + ' - 0.5 && vLayer < ' + G1 + ' + 0.5 ? 0.93 : 0.82, 0.16, glass);\n{ float gs = groundSlot(floor(vLayer + 0.5)); if (gs > -0.5) roughnessFactor = texture(normalAtlas, vec3(vTex, gs)).b; }\nroughnessFactor *= 1.0 - 0.55 * nlWet * step(abs(vLayer - ' + AS + '), 0.5);' : ''))
      .replace('#include <metalnessmap_fragment>', '#include <metalnessmap_fragment>\n' + (pbr ? 'metalnessFactor = glass * 0.4;' : ''))
      .replace('#include <lights_fragment_maps>', '#include <lights_fragment_maps>\n' + (pbr ? 'irradiance *= hemiK;' : ''))
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\n' + normalPatch(N, A3, B3, gN, pbr))
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += nightEmissive(tx, floor(vLayer + 0.5), vWorld);\nif (night > 0.12) totalEmissiveRadiance += diffuseColor.rgb * nightLight(vWorld, normalize(vWN)) * (night - 0.12) * 1.14;');
  };
  return mat;
}

/** Wall normal map: tangent frame from the (vertical) wall normal and world up, so no tangent attribute is needed.
 *  T = up x N (texture u), B = up (texture v up); skipped for ground/roofs and non-vertical faces. */
const groundSlotFn = (gN: number[], base: string) => `float groundSlot(float l){\n${gN.map((l, i) => `  if (abs(l - ${l}.0) < 0.5) return ${base} + ${i}.0;`).join('\n')}\n  return -1.0;\n}`;

const normalPatch = (N: string, A: string, B: string, gN: number[], pbr: boolean) => `
{
  float nl = floor(vLayer + 0.5);
  float gs = groundSlot(nl);
  if (gs > -0.5 && ${pbr ? 'true' : 'false'}) {   // procedural ground (asphalt, trottoir, Pflaster, curb): normal map, PC only
    vec2 xy = (texture(normalAtlas, vec3(vTex, gs)).rg * 2.0 - 1.0) * 0.9;
    vec3 wn = normalize(vWN);
    vec3 pw;
    if (abs(wn.y) > 0.5) pw = vec3(xy.x, sqrt(max(1.0 - dot(xy, xy), 0.05)) * sign(wn.y), -xy.y);   // u = world x, v = world north (-z)
    else { vec3 T = normalize(cross(vec3(0.0, 1.0, 0.0), wn)); pw = T * xy.x + vec3(0.0, 1.0, 0.0) * xy.y + wn * sqrt(max(1.0 - dot(xy, xy), 0.05)); }
    normal = normalize((viewMatrix * vec4(pw, 0.0)).xyz) * faceDirection;
  }
  float ni = nl < ${N} ? nl : (nl > ${A} - 0.5 && nl < ${B} - 0.5 ? ${N} + nl - ${A} : -1.0);
  if (ni > -0.5 && abs(vWN.y) < 0.5) {
    vec3 wn = normalize(vWN);
    vec3 T = normalize(cross(vec3(0.0, 1.0, 0.0), wn));
    vec2 xy = (texture(normalAtlas, vec3(vTex, ni)).rg * 2.0 - 1.0) * 0.9;
    vec3 pw = T * xy.x + vec3(0.0, 1.0, 0.0) * xy.y + wn * sqrt(max(1.0 - dot(xy, xy), 0.05));
    normal = normalize((viewMatrix * vec4(pw, 0.0)).xyz) * faceDirection;
  }
}`;

/** Share of shops of each type that are open at night (GLSL shopOpen(k): k = index among shop layers). */
const HOURS: [RegExp, number][] = [[/bar|club/, 1.0], [/kebab/, 0.95], [/spaeti|kiosk/, 0.8], [/restaurant/, 0.85], [/cafe/, 0.6],
  [/super/, 0.3], [/laden/, 0.3], [/coiffeur/, 0.15], [/velo|baeckerei|gemuese|apotheke|bank/, 0.08], [/buero/, 0.06], [/leer/, 0.0]];
function shopHours(meta: { facades: number; shops_end: number; layers?: string[]; shops2?: [number, number] }, F: string): string {
  // shop layers: [facades, shops_end) first (kept stable for old tiles), more appended at shops2 = [from, to)
  const names = [...(meta.layers?.slice(meta.facades, meta.shops_end) ?? []), ...(meta.shops2 ? meta.layers?.slice(...meta.shops2) ?? [] : [])];
  const rows = names.map((n, i) => `  if (k < ${i}.5) return ${(HOURS.find(([re]) => re.test(n))?.[1] ?? 0.3).toFixed(2)};`).join('\n');
  return `float shopOpen(float k){\n${rows}\n  return 0.3;\n}`;
}

/** Layers: facades [0,F), shopfronts [F,S), then brandmauer, roofs, ground. Windows light up per cell (world hash). */
const nightFn = (F: string, S: string, hours: string, E: string, E2: string, A3: string, B3: string) => `
${hours}
// glass = unmasked, dark and neutral/blue texels (a dark brown/red wall is not glass: that was the beige-block bug at night)
float glassMask(vec4 tx){
  float luma = dot(tx.rgb, vec3(0.299, 0.587, 0.114));
  float neutral = smoothstep(0.0, 0.06, tx.b - tx.r * 0.8 + 0.03) * (1.0 - smoothstep(0.25, 0.5, max(tx.r, max(tx.g, tx.b)) - min(tx.r, min(tx.g, tx.b)) + 0.0));
  return (1.0 - tx.a) * (1.0 - smoothstep(0.18, 0.34, luma)) * neutral;
}
float hash31(vec3 p){ p = fract(p * vec3(0.1031, 0.1030, 0.0973)); p += dot(p, p.yxz + 33.33); return fract((p.x + p.y) * p.z); }
vec3 nightEmissive(vec4 tx, float ly, vec3 wp){
  bool fac3 = ly > ${A3} - 0.5 && ly < ${B3} - 0.5;                              // v3 facades (appended after the roofs)
  bool shop2 = ly > ${E} - 0.5 && !fac3 && ly < ${E2} - 0.5;
  if (night < 0.01 || (ly > ${S} - 0.5 && !shop2 && !fac3)) return vec3(0.0);
  if ((ly > ${F} - 0.5 && !fac3) || shop2) {                                                // shopfronts: mask (alpha) = lit glass / neon, wall stays dark
    float k = shop2 ? ly - ${E} + (${S} - ${F}) : ly - ${F};
    // opening hours: per ~12 m cell of wall; bars/clubs always open, offices/vacant never, closed shops keep a faint window display
    float open = step(hash31(vec3(floor(wp.x / 12.0), floor(wp.z / 12.0), 5.0)), shopOpen(k));
    float lit = mix(0.12, 1.0, open) * tx.a;
    float sat = max(tx.r, max(tx.g, tx.b)) - min(tx.r, min(tx.g, tx.b));
    vec3 glow = pow(tx.rgb, vec3(1.5)) * (0.6 + 1.8 * sat * sat);   // painted interior colour (darks stay dark), neon tubes get extra punch
    return glow * lit * mix(1.0, 0.0, step(shopOpen(k), 0.001)) * night;
  }
  // one texture repeat = 4 bays x 4 storeys (pipeline/facade.py): switch whole windows, keyed per building block
  vec3 cell = vec3(floor(vTex * 4.0), floor(wp.x / 37.0) * 7.0 + floor(wp.z / 41.0) * 13.0);
  float h = hash31(cell), h2 = hash31(cell + 17.0);
  float on = step(h, 0.3 * night);                                // ~30 % of windows at full night
  float dark = glassMask(tx);
  vec3 warm = mix(vec3(1.0, 0.55, 0.22), vec3(1.0, 0.72, 0.4), h2);   // ~0xffd9a0 after tone mapping, stays orange instead of washing out to beige
  float cool = step(0.93, hash31(cell + 3.0));                       // the odd bluish TV window
  warm = mix(warm, vec3(0.45, 0.6, 1.0), cool);
  vec2 cu = fract(vTex * 4.0);
  dark *= smoothstep(0.1, 0.25, cu.x) * smoothstep(0.9, 0.75, cu.x) * smoothstep(0.12, 0.3, cu.y) * smoothstep(0.88, 0.7, cu.y);   // only the opening, not the whole bay
  float shade = 0.7 + 0.5 * cu.y;                       // brighter towards the sill: reads as a lit room, not a flat panel
  return warm * (dark * on * (0.045 + 0.04 * h2) * shade * night);
}`;

/** Cheap value noise for the world-space ground variation. */
const GROUND_FN = `
float vh2(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn2(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(vh2(i), vh2(i + vec2(1.0, 0.0)), f.x), mix(vh2(i + vec2(0.0, 1.0)), vh2(i + vec2(1.0, 1.0)), f.x), f.y); }
`;

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((ok, fail) => {
    const i = new Image();
    i.onload = () => ok(i);
    i.onerror = fail;
    i.src = url;
  });
}
