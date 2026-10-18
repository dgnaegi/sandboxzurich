// look3: cheap hedge foliage. Vertex wobble (world-position noise, so box faces stay watertight) + leaf-clump shading in the
// fragment shader. No texture, no extra draw call. Works for instanced unit boxes ('inst') and merged geometry with a `fol`
// attribute ('attr': 1 = hedge vertex above the ground, 0 = anything else).
import * as THREE from 'three';

const HASH = /* glsl */ `
float fh(vec3 p){ p = fract(p * 0.1031); p += dot(p, p.yzx + 33.33); return fract((p.x + p.y) * p.z); }
float fn(vec3 p){ vec3 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
  return mix(mix(mix(fh(i), fh(i + vec3(1,0,0)), f.x), mix(fh(i + vec3(0,1,0)), fh(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(fh(i + vec3(0,0,1)), fh(i + vec3(1,0,1)), f.x), mix(fh(i + vec3(0,1,1)), fh(i + vec3(1,1,1)), f.x), f.y), f.z); }
`;

export function foliagePatch(mat: THREE.Material, mode: 'inst' | 'attr', lite: boolean) {
  mat.customProgramCacheKey = () => `foliage-${mode}-${lite}`;
  mat.onBeforeCompile = (sh) => {
    sh.vertexShader = (mode === 'attr' ? 'attribute float fol;\n' : '') + 'varying vec3 vFW; varying float vFF;\n' + HASH + sh.vertexShader
      .replace('#include <project_vertex>', /* glsl */ `
      vec4 fp = vec4(transformed, 1.0);
      #ifdef USE_INSTANCING
        fp = instanceMatrix * fp;
      #endif
      float fk = ${mode === 'attr' ? 'fol' : 'step(-0.49, position.y)'};
      vec4 fw = modelMatrix * fp;
      float hb = ${mode === 'attr' ? '1.0' : 'smoothstep(-0.49, -0.2, position.y)'};
      vec3 q = fw.xyz;
      vec3 dv = vec3(fn(q * 1.7) - .5, (fn(q * 2.3 + 7.) - .5) * 1.3, fn(q * 1.9 + 3.) - .5);
      ${lite ? '' : 'dv += (vec3(fn(q * 5.1 + 1.), fn(q * 5.7 + 4.), fn(q * 4.9 + 9.)) - .5) * .5;'}
      fw.xyz += dv * 0.26 * fk * hb;
      vFW = fw.xyz; vFF = fk;
      vec4 mvPosition = viewMatrix * fw;
      gl_Position = projectionMatrix * mvPosition;`);
    sh.fragmentShader = 'varying vec3 vFW; varying float vFF;\n' + HASH + sh.fragmentShader.replace('#include <color_fragment>', /* glsl */ `
      #include <color_fragment>
      if (vFF > 0.5) {
        float big = fn(vFW * 0.35), mid = fn(vFW * 3.2), cl = fn(vFW * 9.0);
        ${lite ? 'float leaf = mid;' : 'float leaf = mid * .6 + cl * .4;'}
        vec3 tint = mix(vec3(.62, .78, .55), vec3(.95, .9, .6), smoothstep(.55, .85, big)); // dark leaf green -> beech/yellow patches
        diffuseColor.rgb *= tint * (0.38 + 0.95 * leaf * leaf * 1.6 + 0.1) * 0.9;
      }`);
  };
}
