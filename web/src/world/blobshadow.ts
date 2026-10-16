import * as THREE from 'three';

/**
 * Soft contact shadows for people, cars and bikes where real shadow maps are off (phones / battery saver).
 * One InstancedMesh, one draw call, ~70 flat quads with a radial alpha texture.
 */
const CAP = 72;

function blobTexture(): THREE.Texture {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d')!;
  const gr = g.createRadialGradient(32, 32, 2, 32, 32, 31);
  gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(0.55, 'rgba(0,0,0,0.55)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.NoColorSpace;
  return t;
}

export interface BlobSource {
  crowd: THREE.Object3D;
  cars: () => { x: number; y: number; heading: number; len: number; kind: string }[];
  player: THREE.Object3D;
  ground: (x: number, y: number) => number;
  sunDir: THREE.Vector3;
}

export class BlobShadows {
  readonly mesh: THREE.InstancedMesh;
  private m = new THREE.Matrix4();
  private q = new THREE.Quaternion();
  private e = new THREE.Euler();
  private p = new THREE.Vector3();
  private s = new THREE.Vector3();
  private frame = 0;
  private mat: THREE.MeshBasicMaterial;
  constructor(scene: THREE.Scene, private src: BlobSource) {
    const geo = new THREE.PlaneGeometry(1, 1); geo.rotateX(-Math.PI / 2);
    this.mat = new THREE.MeshBasicMaterial({ map: blobTexture(), color: 0x10131c, transparent: true, opacity: 0.4, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
    this.mesh = new THREE.InstancedMesh(geo, this.mat, CAP);
    this.mesh.frustumCulled = false; this.mesh.renderOrder = 2; this.mesh.count = 0;
    scene.add(this.mesh);
  }

  private put(i: number, x: number, y: number, z: number, rot: number, sx: number, sz: number, sh: THREE.Vector3): void {
    this.e.set(0, rot, 0); this.q.setFromEuler(this.e);
    this.p.set(x - sh.x * 0.5, y + 0.07, z - sh.z * 0.5); this.s.set(sx, 1, sz);
    this.m.compose(this.p, this.q, this.s); this.mesh.setMatrixAt(i, this.m);
  }

  /** enabled = real shadows are off; sunUp = sin(sun elevation). Updates every 2nd frame. */
  update(enabled: boolean, sunUp: number, cam: THREE.Vector3): void {
    this.mesh.visible = enabled && sunUp > 0.02;
    if (!this.mesh.visible || (this.frame++ & 1)) return;
    this.mat.opacity = 0.42 * Math.min(1, sunUp * 5);
    const { crowd, player, ground, sunDir } = this.src, cars = this.src.cars();
    const sh = new THREE.Vector3(-sunDir.x, 0, -sunDir.z);   // shadow falls away from the sun
    sh.multiplyScalar(-1);
    let n = 0;
    this.put(n++, player.position.x, player.position.y, player.position.z, 0, 0.95, 0.95, sh);
    const R2 = 65 * 65;
    for (const c of crowd.children) {
      if (n >= CAP - 28 || !c.visible) continue;
      const w = c.position;
      const dx = w.x - cam.x, dz = w.z - cam.z;
      if (dx * dx + dz * dz > R2) continue;
      this.put(n++, w.x, w.y, w.z, 0, 0.8, 0.8, sh);
    }
    for (const a of cars) {
      if (n >= CAP) break;
      const dx = a.x - cam.x, dz = -a.y - cam.z;
      if (dx * dx + dz * dz > R2 * 1.5) continue;
      const bike = a.kind === 'bike';
      this.put(n++, a.x, ground(a.x, a.y) + 0.02, -a.y, a.heading - Math.PI / 2, bike ? a.len * 0.6 : a.len * 1.1, bike ? 0.7 : a.len * 0.5, sh);
    }
    this.mesh.count = n;
    this.mesh.instanceMatrix.needsUpdate = true;
  }
}
