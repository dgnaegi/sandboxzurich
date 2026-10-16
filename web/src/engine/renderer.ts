import * as THREE from 'three';
import { createSky, HORIZON } from './sky';
import { installGrading, setGradeResolution } from './grading';

/** Renderer, scene, sky and lights (warm late afternoon). Quality tier caps the pixel ratio. */
export function createRenderer(canvas: HTMLCanvasElement, mobile: boolean) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: !mobile, powerPreference: 'high-performance', stencil: true });   // stencil: hb3 stair-well mask
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, mobile ? 1.25 : 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  installGrading(renderer);   // custom tone mapper = ACES + 80s neon grade (see grading.ts)
  renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = !mobile;
  renderer.shadowMap.type = THREE.PCFShadowMap;

  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(HORIZON, 55, mobile ? 400 : 560)   // aerial perspective: distant blocks fade into the haze;

  // far plane just beyond the fog: nothing invisible gets drawn
  const camera = new THREE.PerspectiveCamera(60, 1, 0.3, (mobile ? 420 : 600) + 40);

  const sunDir = new THREE.Vector3(-0.55, 0.42, 0.35).normalize();
  const sky = createSky(sunDir);
  const skyMat = sky.material as THREE.ShaderMaterial;
  scene.add(sky);
  const hemi = new THREE.HemisphereLight(0xcfe0ff, 0x8a7458, 1.5);
  scene.add(hemi);
  const sun = new THREE.DirectionalLight(0xffd9a8, 3.2);
  sun.castShadow = !mobile;
  sun.shadow.mapSize.set(2048, 2048);
  const s = sun.shadow.camera;
  s.left = s.bottom = -80; s.right = s.top = 80; s.near = 10; s.far = 500;
  sun.shadow.radius = 4;   // softer shadow edges
    sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.04;
  scene.add(sun, sun.target);

  const resize = () => {
    const w = window.innerWidth, h = window.innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.fov = w < h ? 75 : 60;
    camera.updateProjectionMatrix();
    setGradeResolution(renderer);
  };
  window.addEventListener('resize', resize);
  resize();

  /** Keep the shadow frustum centred on the player. */
  const sr = new THREE.Vector3(), su = new THREE.Vector3(), sp = new THREE.Vector3();
  const texel = (s.right - s.left) / sun.shadow.mapSize.x;
  const followSun = (p: THREE.Vector3) => {
    // snap the focus point to shadow-map texels in light space: no edge shimmer while walking
    sr.set(0, 1, 0).cross(sunDir).normalize(); su.copy(sunDir).cross(sr).normalize();
    const a = Math.round(p.dot(sr) / texel) * texel, b = Math.round(p.dot(su) / texel) * texel;
    sp.copy(p).addScaledVector(sr, a - p.dot(sr)).addScaledVector(su, b - p.dot(su));
    sun.position.copy(sp).addScaledVector(sunDir, 200);
    sun.target.position.copy(sp);
  };
  return { renderer, scene, camera, followSun, sun, hemi, sky, skyMat, sunDir, mobile };
}
