import * as THREE from 'three';

/** Shared night factor (0 = day .. 1 = night) for all patched materials (windows, shopfronts, lamps). */
export const nightUniform = { value: 0 };
export function setNight(v: number): void { nightUniform.value = v; }

/**
 * One shared material for all tile geometry: a texture array (facades, shopfronts, roofs, ground)
 * selected per vertex (uv1.x), UVs in repeats (uv), vertex colour = tint applied where the mask (alpha) is set.
 */
export async function loadWorldMaterial(base: string, anisotropy: number): Promise<THREE.Material> {
  const meta = await (await fetch(`${base}/layers.json`)).json() as { size: number; cols: number; count: number; facades: number; shops_end: number; normals: number; normals3?: number; facades3?: [number, number]; layers?: string[]; shops2?: [number, number] };
  const [rgb, mask, nimg] = await Promise.all([loadImage(`${base}/atlas.webp`), loadImage(`${base}/atlas_mask.png`), loadImage(`${base}/atlas_n.webp`)]);
  const L = meta.size, n = meta.count;
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
  const nn = meta.normals + (meta.normals3 ?? 0), nd = new Uint8Array(L * L * 4 * nn), np_ = pix(nimg);
  for (let k = 0; k < nn; k++) {
    const ox = (k % meta.cols) * L, oy = Math.floor(k / meta.cols) * L;
    for (let y = 0; y < L; y++) {
      let src = ((oy + y) * nimg.width + ox) * 4, dst = (k * L * L + y * L) * 4;
      for (let x = 0; x < L; x++, src += 4, dst += 4) {
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
  const ntex = setup(new THREE.DataArrayTexture(nd, L, L, nn), false);
  const F = meta.facades.toFixed(1), S = meta.shops_end.toFixed(1), N = meta.normals.toFixed(1);
  const [A3, B3] = (meta.facades3 ?? [9999, 9999]).map((v) => v.toFixed(1));

  const mat = new THREE.MeshLambertMaterial({ vertexColors: true });
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.atlas = { value: tex };
    sh.uniforms.night = nightUniform;
    sh.uniforms.normalAtlas = { value: ntex };
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\n#ifndef USE_UV1\nattribute vec2 uv1;\n#endif\nvarying vec2 vTex;\nvarying float vLayer;\nvarying vec3 vWorld;\nvarying vec3 vWN;')
      .replace('#include <beginnormal_vertex>', '#include <beginnormal_vertex>\nvWN = normalize(mat3(modelMatrix) * objectNormal);')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvTex = uv;\nvLayer = uv1.x;\nvWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform highp sampler2DArray atlas;\nuniform highp sampler2DArray normalAtlas;\nuniform float night;\nvarying vec2 vTex;\nvarying float vLayer;\nvarying vec3 vWorld;\nvarying vec3 vWN;\n' + nightFn(F, S, shopHours(meta, F), (meta.shops2?.[0] ?? 9999).toFixed(1), (meta.shops2?.[1] ?? 9999).toFixed(1), A3, B3))
      .replace('#include <color_fragment>',
        'vec4 tx = texture(atlas, vec3(vTex, floor(vLayer + 0.5)));\n' +
        'float fl3 = step(' + A3 + ' - 0.5, vLayer) * step(vLayer, ' + B3 + ' - 0.5);\n' +
        'diffuseColor.rgb *= tx.rgb * mix(vec3(1.0), vColor.rgb * mix(1.0, 1.35, fl3), tx.a);')
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\n' + normalPatch(N, A3, B3))
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += nightEmissive(tx, floor(vLayer + 0.5), vWorld);');
  };
  return mat;
}

/** Wall normal map: tangent frame from the (vertical) wall normal and world up, so no tangent attribute is needed.
 *  T = up x N (texture u), B = up (texture v up); skipped for ground/roofs and non-vertical faces. */
const normalPatch = (N: string, A: string, B: string) => `
{
  float nl = floor(vLayer + 0.5);
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
  float on = step(h, 0.35 * night);                               // ~35 % of windows at full night
  float luma = dot(tx.rgb, vec3(0.299, 0.587, 0.114));
  float dark = 1.0 - smoothstep(0.18, 0.34, luma);
  dark *= 1.0 - tx.a;                              // unmasked + dark = glass
  vec3 warm = mix(vec3(1.0, 0.6, 0.28), vec3(1.0, 0.8, 0.5), h2);
  return warm * (dark * on * (0.16 + 0.12 * h2) * night);
}`;

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((ok, fail) => {
    const i = new Image();
    i.onload = () => ok(i);
    i.onerror = fail;
    i.src = url;
  });
}
