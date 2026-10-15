import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { N8AOPass } from 'n8ao';
import { bloom, gradeUniforms, setGradeResolution } from './grading';

/**
 * Post-processing for the high tier (PC): screen-space ambient occlusion (N8AO, half resolution)
 * on an MSAA target, then tone mapping/colour space via OutputPass. Phones render directly.
 */
export function createPost(renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.PerspectiveCamera) {
  const size = renderer.getDrawingBufferSize(new THREE.Vector2());
  const target = new THREE.WebGLRenderTarget(size.x, size.y, { type: THREE.HalfFloatType, samples: 4 });
  const composer = new EffectComposer(renderer, target);
  composer.addPass(new RenderPass(scene, camera));
  const ao = new N8AOPass(scene, camera, size.x, size.y);
  ao.configuration.aoRadius = 2.2;
  ao.configuration.distanceFalloff = 1.0;
  ao.configuration.intensity = 2.4;
  ao.configuration.halfRes = true;
  ao.configuration.depthAwareUpsampling = true;
  ao.configuration.gammaCorrection = false;
  ao.setQualityMode('Medium');
  composer.addPass(ao);
  // bloom on the HDR buffer (internally half resolution): only emissive/very bright parts exceed the threshold
  const bl = new UnrealBloomPass(new THREE.Vector2(size.x, size.y), bloom.strength, bloom.radius, bloom.threshold);
  composer.addPass(bl);
  const out = new OutputPass();   // custom tone mapper (ACES + grade) comes from the renderer setting
  Object.assign(out.uniforms, gradeUniforms());
  composer.addPass(out);
  const resize = () => {
    const s = renderer.getDrawingBufferSize(new THREE.Vector2());
    composer.setSize(s.x / renderer.getPixelRatio(), s.y / renderer.getPixelRatio());
    setGradeResolution(renderer);
  };
  window.addEventListener('resize', resize);
  return {
    render: () => {
      bl.strength = bloom.strength; bl.threshold = bloom.threshold; bl.radius = bloom.radius;
      composer.render();
    },
  };
}
