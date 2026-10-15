import * as THREE from 'three';

/** Shared night factor (0 = day .. 1 = night) for all patched materials (windows, shopfronts, lamps). */
export const nightUniform = { value: 0 };
export function setNight(v: number): void { nightUniform.value = v; }

/**
 * One shared material for all tile geometry: a texture array (facades, shopfronts, roofs, ground)
 * selected per vertex (uv1.x), UVs in repeats (uv), vertex colour = tint applied where the mask (alpha) is set.
 */
export async function loadWorldMaterial(base: string, anisotropy: number): Promise<THREE.Material> {
  const meta = await (await fetch(`${base}/layers.json`)).json() as { size: number; cols: number; count: number; facades: number; shops_end: number; normals: number };
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
  const nn = meta.normals, nd = new Uint8Array(L * L * 4 * nn), np_ = pix(nimg);
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
      .replace('#include <common>', '#include <common>\nuniform highp sampler2DArray atlas;\nuniform highp sampler2DArray normalAtlas;\nuniform float night;\nvarying vec2 vTex;\nvarying float vLayer;\nvarying vec3 vWorld;\nvarying vec3 vWN;\n' + nightFn(F, S))
      .replace('#include <color_fragment>',
        'vec4 tx = texture(atlas, vec3(vTex, floor(vLayer + 0.5)));\n' +
        'diffuseColor.rgb *= tx.rgb * mix(vec3(1.0), vColor.rgb, tx.a);')
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>\n' + normalPatch(N))
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += nightEmissive(tx, floor(vLayer + 0.5), vWorld);');
  };
  return mat;
}

/** Wall normal map: tangent frame from the (vertical) wall normal and world up, so no tangent attribute is needed.
 *  T = up x N (texture u), B = up (texture v up); skipped for ground/roofs and non-vertical faces. */
const normalPatch = (N: string) => `
{
  float nl = floor(vLayer + 0.5);
  if (nl < ${N} && abs(vWN.y) < 0.5) {
    vec3 wn = normalize(vWN);
    vec3 T = normalize(cross(vec3(0.0, 1.0, 0.0), wn));
    vec2 xy = (texture(normalAtlas, vec3(vTex, nl)).rg * 2.0 - 1.0) * 0.9;
    vec3 pw = T * xy.x + vec3(0.0, 1.0, 0.0) * xy.y + wn * sqrt(max(1.0 - dot(xy, xy), 0.05));
    normal = normalize((viewMatrix * vec4(pw, 0.0)).xyz) * faceDirection;
  }
}`;

/** Layers: facades [0,F), shopfronts [F,S), then brandmauer, roofs, ground. Windows light up per cell (world hash). */
const nightFn = (F: string, S: string) => `
float hash31(vec3 p){ p = fract(p * vec3(0.1031, 0.1030, 0.0973)); p += dot(p, p.yxz + 33.33); return fract((p.x + p.y) * p.z); }
vec3 nightEmissive(vec4 tx, float ly, vec3 wp){
  if (night < 0.01 || ly > ${S} - 0.5) return vec3(0.0);
  if (ly > ${F} - 0.5) {                                                // shopfronts: only the dark glass glows warm
    float g = 1.0 - smoothstep(0.25, 0.45, dot(tx.rgb, vec3(0.299, 0.587, 0.114)));
    return (tx.rgb * 0.03 + vec3(1.0, 0.75, 0.45) * g * 0.2) * night;
  }
  vec3 cell = vec3(floor(wp.x / 2.8), floor(wp.y / 3.1), floor(wp.z / 2.8));
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
