import * as THREE from 'three';
import { CLASSES, atlas, models } from './trees';

/** Far LOD: every class model is rendered once (own geometry, fixed light) into a 4x4 tile sheet; far trees are camera-facing quads. */
const TILE = 128;
export const IMP_W = 1.3, IMP_H = 1.1, IMP_Y0 = -0.04; // frame in model units: width, height, bottom

export function bakeImpostors(renderer: THREE.WebGLRenderer): THREE.Texture {
  const rt = new THREE.WebGLRenderTarget(TILE * 4, TILE * 4, { generateMipmaps: true, minFilter: THREE.LinearMipmapLinearFilter });
  const scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight(0xdfe8ff, 0x6a6a50, 1.5));
  const sun = new THREE.DirectionalLight(0xfff0d8, 2.0); sun.position.set(.5, 1, .8); scene.add(sun);
  const cam = new THREE.OrthographicCamera(-IMP_W / 2, IMP_W / 2, IMP_Y0 + IMP_H, IMP_Y0, 0.1, 10);
  cam.position.set(0, 0, 4);
  const prev = { rt: renderer.getRenderTarget(), vp: new THREE.Vector4(), sc: new THREE.Vector4(), ca: new THREE.Color(), al: renderer.getClearAlpha(), st: renderer.getScissorTest(), shadow: renderer.shadowMap.enabled };
  renderer.getViewport(prev.vp); renderer.getScissor(prev.sc); renderer.getClearColor(prev.ca);
  renderer.shadowMap.enabled = false;
  renderer.setRenderTarget(rt);
  renderer.setClearColor(0x4a6a30, 0); renderer.setScissorTest(false); renderer.clear();
  renderer.setScissorTest(true);
  const mat = new THREE.MeshLambertMaterial({ map: atlas, vertexColors: true, alphaTest: .5, side: THREE.DoubleSide });
  CLASSES.forEach((_, i) => {
    const m = models[i].lod1 ?? models[i].lod0[0];
    if (!m) return;
    const mesh = new THREE.Mesh(m.geo, mat);
    scene.add(mesh);
    const x = (i % 4) * TILE, y = Math.floor(i / 4) * TILE;
    renderer.setViewport(x, y, TILE, TILE); renderer.setScissor(x, y, TILE, TILE);
    renderer.render(scene, cam);
    scene.remove(mesh);
  });
  renderer.setRenderTarget(prev.rt);
  renderer.setViewport(prev.vp); renderer.setScissor(prev.sc); renderer.setScissorTest(prev.st);
  renderer.setClearColor(prev.ca, prev.al);
  renderer.shadowMap.enabled = prev.shadow;
  return rt.texture;
}
