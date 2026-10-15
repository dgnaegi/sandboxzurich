import * as THREE from 'three';
import { gradeUniforms } from './grading';

/** Late-afternoon gradient sky dome (arcade-style), follows the camera. */
export const HORIZON = new THREE.Color(0xf4b98e);
export const ZENITH = new THREE.Color(0x3f74c4);

export function createSky(sunDir: THREE.Vector3): THREE.Mesh {
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    depthTest: false,
    fog: false,
    uniforms: {
      zenith: { value: ZENITH }, horizon: { value: HORIZON }, sun: { value: sunDir.clone().normalize() },
      moon: { value: sunDir.clone().negate() }, sunCol: { value: new THREE.Color(1, 0.8, 0.5) },
      cloudLo: { value: new THREE.Color(1.0, 0.86, 0.78) }, cloudHi: { value: new THREE.Color(1.0, 0.97, 0.94) },
      stars: { value: 0 }, ...gradeUniforms(),
    },
    vertexShader: 'varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * vec4(mat3(viewMatrix) * position, 1.0); }',
    fragmentShader: `uniform vec3 zenith; uniform vec3 horizon; uniform vec3 sun; uniform vec3 moon; uniform vec3 sunCol; uniform vec3 cloudLo; uniform vec3 cloudHi; uniform float stars; varying vec3 vDir;
      void main(){
        float h = max(vDir.y, 0.0);
        vec3 c = mix(horizon, zenith, pow(h, 0.55));
        c = mix(c, horizon * vec3(1.04, 0.98, 0.9), smoothstep(0.2, 0.0, h) * 0.5);   // low haze
        float s = max(dot(normalize(vDir), sun), 0.0);
        c += sunCol * (pow(s, 800.0) * 3.0 + pow(s, 14.0) * 0.18 + pow(s, 4.0) * 0.07 * (1.0 - h));   // disc + Mie halo + forward glow
        // soft procedural clouds (value-noise fbm on a plane above)
        vec2 q = vDir.xz / max(vDir.y, 0.04) * 0.9;
        float n = 0.0, a = 0.55;
        for (int i = 0; i < 5; i++) { vec2 f = fract(q), w = floor(q); f = f * f * (3.0 - 2.0 * f);
          float h00 = fract(sin(dot(w, vec2(127.1, 311.7))) * 43758.5), h10 = fract(sin(dot(w + vec2(1, 0), vec2(127.1, 311.7))) * 43758.5);
          float h01 = fract(sin(dot(w + vec2(0, 1), vec2(127.1, 311.7))) * 43758.5), h11 = fract(sin(dot(w + vec2(1, 1), vec2(127.1, 311.7))) * 43758.5);
          n += a * mix(mix(h00, h10, f.x), mix(h01, h11, f.x), f.y); q *= 2.1; a *= 0.5; }
        float cl = smoothstep(0.55, 0.85, n) * smoothstep(0.02, 0.25, vDir.y);
        vec3 cloudCol = mix(cloudLo, cloudHi, h) + sunCol * pow(s, 4.0) * 0.4;
        // stars + moon (behind clouds)
        if (stars > 0.01 && vDir.y > 0.0) {
          vec3 g = floor(normalize(vDir) * 160.0);
          float r = fract(sin(dot(g, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
          c += vec3(0.85, 0.9, 1.0) * step(0.9965, r) * (0.5 + 0.5 * fract(r * 91.7)) * stars * smoothstep(0.0, 0.25, vDir.y);
          float md = dot(normalize(vDir), moon);
          c = mix(c, vec3(0.92, 0.94, 1.0), smoothstep(0.99935, 0.99965, md) * stars);
          c += vec3(0.5, 0.6, 0.9) * pow(max(md, 0.0), 60.0) * 0.15 * stars;
        }
        c = mix(c, cloudCol, cl * 0.85);
        if (vDir.y < 0.0) c = horizon;
        gl_FragColor = vec4(c, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  const m = new THREE.Mesh(new THREE.SphereGeometry(380, 32, 16), mat);
  m.renderOrder = -1;
  m.frustumCulled = false;
  return m;
}
