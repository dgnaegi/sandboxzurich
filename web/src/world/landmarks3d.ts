import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { nightUniform } from '../engine/materials';

/** Detailed landmark models (pipeline/landmarks/*.py -> /models/landmarks/*.glb), streamed by distance.
 *  Manifest /data/landmarks.json: {landmarks:[{name, model, x, y, z, heading, hide}]} in local metres
 *  (x east, y north, z = ground height of the model origin). Local -> Three: (x, z, -y). */
interface Entry { name: string; model: string; x: number; y: number; z: number; heading: number }

const LOAD_R = 600, DROP_R = 700, SHADOW_R = 220; // shadows only near the player (shadow pass is the expensive part)

export class Landmarks3D {
  private entries: Entry[] = [];
  private live = new Map<string, THREE.Group | null>();   // null = loading
  private lit: THREE.MeshLambertMaterial[] = [];
  private casting = new Map<string, boolean>();
  private loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);

  constructor(private scene: THREE.Scene) {}

  async load(): Promise<void> {
    try {
      const r = await fetch('/data/landmarks.json');
      if (r.ok) this.entries = (await r.json()).landmarks ?? [];
    } catch { /* no manifest: nothing to show */ }
  }

  /** Call per frame (cheap) with the player's local position. */
  update(px: number, py: number): void {
    for (const e of this.entries) {
      const d = Math.hypot(e.x - px, e.y - py), g = this.live.get(e.name);
      if (g === undefined && d < LOAD_R) { this.live.set(e.name, null); void this.spawn(e); }
      else if (g) {
        g.visible = d < DROP_R;
        const near = d < SHADOW_R;
        if (this.casting.get(e.name) !== near) { this.casting.set(e.name, near); g.traverse((o) => { if ((o as THREE.Mesh).isMesh) o.castShadow = near; }); }
      }
    }
    const n = nightUniform.value;
    for (const m of this.lit) m.emissiveIntensity = n * 0.9;
  }

  private async spawn(e: Entry): Promise<void> {
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
