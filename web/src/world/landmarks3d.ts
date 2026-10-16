import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { nightUniform } from '../engine/materials';

/** Detailed landmark models (pipeline/landmarks/*.py -> /models/landmarks/*.glb), streamed by distance.
 *  Manifest /data/landmarks.json: {landmarks:[{name, model, x, y, z, heading, hide}]} in local metres
 *  (x east, y north, z = ground height of the model origin). Local -> Three: (x, z, -y). */
interface Entry { name: string; model: string; x: number; y: number; z: number; heading: number; load_r?: number }  // load_r: near-only parts (interiors) load closer and are disposed again when far

const LOAD_R = 600, DROP_R = 700, SHADOW_R = 220; // shadows only near the player (shadow pass is the expensive part)

export class Landmarks3D {
  private entries: Entry[] = [];
  private live = new Map<string, THREE.Group | null>();   // null = loading
  private lit: THREE.MeshLambertMaterial[] = [];
  private casting = new Map<string, boolean>();
  private pending = new Map<string, Promise<void>>();
  private loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);

  constructor(private scene: THREE.Scene) {}

  async load(): Promise<void> {
    try {
      const r = await fetch('/data/landmarks.json');
      if (r.ok) this.entries = (await r.json()).landmarks ?? [];
    } catch { /* no manifest: nothing to show */ }
  }

  /** Load (and await) every landmark model within `r` metres of (x, y): needed before solidAt() is meaningful. */
  async prepare(x: number, y: number, r = 120): Promise<void> {
    const jobs: Promise<void>[] = [];
    for (const e of this.entries) {
      if (Math.hypot(e.x - x, e.y - y) >= r + 80) continue;
      const pend = this.pending.get(e.name);
      if (pend) { jobs.push(pend); continue; }
      if (this.live.get(e.name) === undefined) { this.live.set(e.name, null); jobs.push(this.spawn(e)); }
    }
    await Promise.all(jobs);
  }

  /** Is the standing point (x, y, z=feet) inside landmark geometry (walls around it, or a low ceiling above)? */
  solidAt(x: number, y: number, z: number): boolean {
    const groups: THREE.Object3D[] = [];
    for (const e of this.entries) { const g = this.live.get(e.name); if (g && Math.hypot(e.x - x, e.y - y) < 150) groups.push(g); }
    if (!groups.length) return false;
    const meshes: THREE.Mesh[] = [];
    for (const g of groups) { g.updateMatrixWorld(true); g.traverse((o) => { if ((o as THREE.Mesh).isMesh) meshes.push(o as THREE.Mesh); }); }
    const sides = meshes.map((m) => (m.material as THREE.Material).side);
    meshes.forEach((m) => { (m.material as THREE.Material).side = THREE.DoubleSide; });
    const rc = new THREE.Raycaster(), o = new THREE.Vector3(x, z + 1.0, -y), d = new THREE.Vector3();
    let walls = 0, solid = false;
    rc.set(o, d.set(0, 1, 0)); rc.far = 4.5;
    if (rc.intersectObjects(meshes, false).length) solid = true;       // low ceiling right above: stair undersides, platforms
    for (let k = 0; k < 8 && !solid; k++) {
      const a = (k / 8) * Math.PI * 2;
      rc.set(o, d.set(Math.cos(a), 0, Math.sin(a))); rc.far = 0.7;
      if (rc.intersectObjects(meshes, false).length) walls++;
    }
    meshes.forEach((m, i) => { (m.material as THREE.Material).side = sides[i]; });
    return solid || walls >= 3;
  }

  /** Call per frame (cheap) with the player's local position. */
  update(px: number, py: number): void {
    for (const e of this.entries) {
      const d = Math.hypot(e.x - px, e.y - py), g = this.live.get(e.name), lr = e.load_r ?? LOAD_R, dr = e.load_r ? lr + 40 : DROP_R;
      if (g === undefined && d < lr) { this.live.set(e.name, null); void this.spawn(e); }
      else if (g && e.load_r && d > lr + 120) this.dispose(e, g);
      else if (g) {
        g.visible = d < dr;
        const near = d < SHADOW_R;
        if (this.casting.get(e.name) !== near) { this.casting.set(e.name, near); g.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = near; }); }
      }
    }
    const n = nightUniform.value;
    for (const m of this.lit) m.emissiveIntensity = n * 0.9;
  }

  /** Near-only models (interiors): free GPU memory once the player is far away; they reload on return. */
  private dispose(e: Entry, g: THREE.Group): void {
    this.scene.remove(g);
    g.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      m.geometry.dispose();
      const mat = m.material as THREE.MeshLambertMaterial;
      this.lit = this.lit.filter((l) => l !== mat);
      mat.map?.dispose(); mat.emissiveMap?.dispose(); mat.dispose();
    });
    this.live.delete(e.name); this.casting.delete(e.name);
  }

  private spawn(e: Entry): Promise<void> {
    const p = this.spawnNow(e).finally(() => this.pending.delete(e.name));
    this.pending.set(e.name, p);
    return p;
  }

  private async spawnNow(e: Entry): Promise<void> {
    try {
      const gltf = await this.loader.loadAsync(e.model);
      const g = gltf.scene;
      g.position.set(e.x, e.z, -e.y);
      g.rotation.y = e.heading;
      g.name = 'landmark:' + e.name;
      g.traverse((o) => {
        const m = o as THREE.Mesh;
        if (!m.isMesh) return;
        m.castShadow = false; m.receiveShadow = true; // castShadow toggled by distance in update()
        const s = m.material as THREE.MeshStandardMaterial;
        const l = new THREE.MeshLambertMaterial({ map: s.map, vertexColors: !!m.geometry.attributes.color, name: s.name });
        if (s.emissiveMap) { l.emissiveMap = s.emissiveMap; l.emissive = new THREE.Color(0xffffff); l.emissiveIntensity = 0; this.lit.push(l); }
        for (const t of [l.map, l.emissiveMap]) if (t) t.anisotropy = 4;
        m.material = l;
      });
      this.scene.add(g);
      this.live.set(e.name, g);
    } catch (err) {
      console.warn('landmark failed', e.name, err);
      this.live.set(e.name, null);
    }
  }
}
