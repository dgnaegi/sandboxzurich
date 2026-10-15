import * as THREE from 'three';

/**
 * Image-based lighting from the live sky (PC tier). The sky shader is rendered into a tiny cube map (64 px, ENV define =
 * dark ground bounce) and prefiltered with PMREM. Re-rendered only when the clock has moved a few game minutes, so the
 * per-frame cost is zero. scene.environment feeds every MeshStandardMaterial (world tiles, glass).
 */
export class SkyProbe {
  private pmrem: THREE.PMREMGenerator;
  private scene = new THREE.Scene();
  private rt: THREE.WebGLRenderTarget | null = null;
  private last = -1e9;

  constructor(renderer: THREE.WebGLRenderer, private target: THREE.Scene, sky: THREE.ShaderMaterial) {
    this.pmrem = new THREE.PMREMGenerator(renderer);
    const m = new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false, depthTest: false, fog: false, defines: { ENV: 1 },
      uniforms: sky.uniforms, vertexShader: sky.vertexShader, fragmentShader: sky.fragmentShader,
    });
    const mesh = new THREE.Mesh(new THREE.SphereGeometry(50, 16, 8), m);
    mesh.frustumCulled = false;
    this.scene.add(mesh);
  }

  /** Re-render the probe when the time moved >= 12 game minutes (or `force`). */
  update(minutes: number, force = false): void {
    const d = Math.abs(((minutes - this.last + 720) % 1440) - 720);
    if (!force && d < 12) return;
    this.last = minutes;
    const old = this.rt;
    this.rt = this.pmrem.fromScene(this.scene, 0, 0.1, 100, { size: 64 });
    this.target.environment = this.rt.texture;
    old?.dispose();
  }
}
