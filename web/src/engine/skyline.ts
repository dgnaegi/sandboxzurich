import * as THREE from 'three';
import { HORIZON, ZENITH } from './sky';
import { gradeUniforms } from './grading';

/**
 * Cheap far view: terrain ridges (Uetliberg, Zuerichberg, from swissALTI3D via pipeline/skyline.py) as curtains on a dome
 * around the camera, in hazy layers, plus tower silhouettes beyond the tile radius. Depth-tested (no depth write) at renderOrder 0 so real geometry always covers it
 * (negative renderOrders did not draw in this pipeline). Phones: ONE ridge layer, no tower strips, no per-frame work beyond ~170 vertices.
 */
interface SkyData { near: number[][]; far: number[][]; all: number[][]; towers: { n: string; x: number; y: number; g: number; h: number; w: number }[] }
const R = 385, BOTTOM = -0.06;

function hazeMaterial(amount: number): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({
    depthTest: true, depthWrite: false, fog: false, side: THREE.DoubleSide,
    uniforms: { horizon: { value: HORIZON }, tint: { value: ZENITH }, amount: { value: amount }, ...gradeUniforms() },
    vertexShader: 'attribute float g; varying float vG; void main(){ vG = g; gl_Position = projectionMatrix * viewMatrix * vec4(position, 1.0); }',
    fragmentShader: `uniform vec3 horizon; uniform vec3 tint; uniform float amount; varying float vG;
      void main(){
        vec3 dark = mix(tint * 0.75, vec3(0.16, 0.2, 0.3) * (0.25 + dot(horizon, vec3(0.33))), 0.5);
        vec3 c = mix(horizon, dark, amount * (0.3 + 0.7 * vG));
        gl_FragColor = vec4(c, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
}

class Ring {
  readonly mesh: THREE.Mesh;
  private pos: Float32Array;
  constructor(private pts: number[][], amount: number, order: number) {
    const n = pts.length;
    this.pos = new Float32Array(n * 2 * 3);
    const g = new Float32Array(n * 2);
    for (let i = 0; i < n; i++) { g[i * 2] = 1; g[i * 2 + 1] = 0; }
    const idx: number[] = [];
    for (let i = 0; i < n; i++) { const a = i * 2, b = ((i + 1) % n) * 2; idx.push(a, a + 1, b, b, a + 1, b + 1); }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(this.pos, 3));
    geo.setAttribute('g', new THREE.BufferAttribute(g, 1));
    geo.setIndex(idx);
    this.mesh = new THREE.Mesh(geo, hazeMaterial(amount));
    this.mesh.frustumCulled = false; this.mesh.renderOrder = 0; void order;
  }
  update(cx: number, cy: number, cz: number): void {
    const p = this.pos;
    for (let i = 0; i < this.pts.length; i++) {
      const [x, y, h] = this.pts[i];                      // local metres (east, north), height above z0
      const dx = x - cx, dz = -y - cz, d = Math.max(200, Math.hypot(dx, dz));
      const ang = Math.atan2(h - cy, d), k = R / d;
      const ux = dx * k * Math.cos(ang) , uz = dz * k * Math.cos(ang);
      p[i * 6] = cx + ux; p[i * 6 + 1] = cy + R * Math.sin(ang) ; p[i * 6 + 2] = cz + uz;
      p[i * 6 + 3] = cx + ux; p[i * 6 + 4] = cy + R * Math.sin(BOTTOM); p[i * 6 + 5] = cz + uz;
    }
    (this.mesh.geometry.attributes.position as THREE.BufferAttribute).needsUpdate = true;
  }
}

class Towers {
  readonly mesh: THREE.Mesh;
  private pos: Float32Array;
  constructor(private list: SkyData['towers']) {
    const n = list.length;
    this.pos = new Float32Array(n * 4 * 3);
    const g = new Float32Array(n * 4);
    const idx: number[] = [];
    for (let i = 0; i < n; i++) { g.set([0.2, 0.2, 1, 1], i * 4); const o = i * 4; idx.push(o, o + 1, o + 2, o + 2, o + 1, o + 3); }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(this.pos, 3));
    geo.setAttribute('g', new THREE.BufferAttribute(g, 1));
    geo.setIndex(idx);
    this.mesh = new THREE.Mesh(geo, hazeMaterial(0.55));
    this.mesh.frustumCulled = false; this.mesh.renderOrder = 0;
  }
  update(cx: number, cy: number, cz: number): void {
    const p = this.pos;
    this.list.forEach((t, i) => {
      const dx = t.x - cx, dz = -t.y - cz, d = Math.hypot(dx, dz);
      const o = i * 12;
      if (d < 460) { p.fill(0, o, o + 12); return; }   // near: the real model/tiles are there
      const az = Math.atan2(dz, dx), hw = (t.w / 2) / d;
      const bot = Math.atan2(t.g - cy, d), top = Math.atan2(t.g + t.h - cy, d);
      for (let s = 0; s < 2; s++) {
        const a = az + (s ? hw : -hw);
        const cxz = Math.cos(a), czz = Math.sin(a);
        const put = (j: number, ang: number) => { p[o + j * 3] = cx + cxz * R * Math.cos(ang); p[o + j * 3 + 1] = cy + R * Math.sin(ang); p[o + j * 3 + 2] = cz + czz * R * Math.cos(ang); };
        put(s, bot); put(2 + s, top);
      }
    });
    (this.mesh.geometry.attributes.position as THREE.BufferAttribute).needsUpdate = true;
  }
}
export class Skyline {
  private rings: Ring[] = [];
  private towers: Towers | null = null;
  private lx = 1e9; private lz = 1e9; private lf = 0;
  constructor(private scene: THREE.Scene, private mobile: boolean) {}

  async load(): Promise<void> {
    const d: SkyData = await (await fetch('/data/skyline.json')).json();
    if (this.mobile) this.rings.push(new Ring(d.all, 0.6, -0.5));
    else {
      this.rings.push(new Ring(d.far, 0.38, -0.6), new Ring(d.near, 0.62, -0.5));
      this.towers = new Towers(d.towers);
    }
    for (const r of this.rings) this.scene.add(r.mesh);
    if (this.towers) this.scene.add(this.towers.mesh);
    this.lx = 1e9;
  }

  /** Call every frame with the camera position (cheap: only recomputes after ~6 m of movement). */
  update(c: THREE.Vector3): void {
    if (!this.rings.length) return;
    if (Math.abs(c.x - this.lx) + Math.abs(c.z - this.lz) < 6 && (this.lf++ & 31) !== 0) return;
    this.lx = c.x; this.lz = c.z;
    for (const r of this.rings) r.update(c.x, c.y, c.z);
    this.towers?.update(c.x, c.y, c.z);
  }
}
