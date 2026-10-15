import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js';

/** Realistic MakeHuman/MPFB characters (CC0), exported by pipeline/blender. Animations: idle, walk, run. */
interface Entry { id: string; file: string; role: 'player' | 'npc'; sex: string; age: string; height?: number; props?: string[] }
export interface Model { scene: THREE.Object3D; clips: THREE.AnimationClip[]; age: string; height: number; props: string[] }
interface Accessory { name: string; obj: THREE.Object3D; bone: string | null; offset: number[]; rotation: number[]; clips: THREE.AnimationClip[] }

export const WALK_SPEED = 1.4; // m/s the walk clip was authored for
export const RUN_SPEED = 4.0;

export class HumanLib {
  player!: Model;
  npcs: Model[] = [];

  /** Loads the player and the first `first` NPC models; the rest stream in afterwards (download budget). */
  accessories = new Map<string, Accessory>();
  /** Adult NPC models only (police, crowds, scenes must never use children). */
  get adults(): Model[] { const a = this.npcs.filter((m) => m.age !== 'child'); return a.length ? a : this.npcs; }

  /** Loads the player and the first `first` NPC models; up to `max` more stream in afterwards (download budget). */
  static async load(base = '/models/humans', first = 4, max = 40): Promise<HumanLib> {
    const lib = new HumanLib();
    const list = (await (await fetch(`${base}/manifest.json`)).json()) as Entry[];
    const player = list.filter((e) => e.role === 'player');
    // interleave ages so every subset is mixed
    const npcs = list.filter((e) => e.role !== 'player').sort((a, b) => (a.id < b.id ? -1 : 1));
    const order = [...npcs.filter((_, i) => i % 3 === 0), ...npcs.filter((_, i) => i % 3 === 1), ...npcs.filter((_, i) => i % 3 === 2)].slice(0, max);
    await lib.fetch(base, [...player, ...order.slice(0, first)]);
    void lib.fetch(base, order.slice(first)).then(() => lib.loadAccessories());
    return lib;
  }

  async loadAccessories(base = '/models/accessories') {
    const man = (await (await fetch(`${base}/manifest.json`)).json()) as { items: { name: string; file: string; bone: string | null; offset: number[]; rotation: number[]; tint?: string }[] };
    const loader = new GLTFLoader();
    await Promise.all(man.items.map(async (it) => {
      const g = await loader.loadAsync(`${base}/${it.file}`);
      if (it.tint) g.scene.traverse((o) => { const m = o as THREE.Mesh; if (m.isMesh) { m.material = (m.material as THREE.MeshStandardMaterial).clone(); (m.material as THREE.MeshStandardMaterial).color.set(it.tint!); } });
      this.accessories.set(it.name, { name: it.name, obj: g.scene, bone: it.bone, offset: it.offset, rotation: it.rotation, clips: g.animations });
    }));
  }

  /** Attach an accessory clone to a character (bone-local per manifest); returns the object or null. */
  attach(h: Human, name: string, scale = 1): THREE.Object3D | null {
    const a = this.accessories.get(name);
    if (!a) return null;
    const o = SkeletonUtils.clone(a.obj);
    const parent = a.bone ? h.root.getObjectByName(a.bone) : h.root;
    if (!parent) return null;
    o.position.fromArray(a.offset); o.rotation.fromArray(a.rotation as [number, number, number]); o.scale.setScalar(scale);
    parent.add(o);
    return o;
  }

  /** A free-standing accessory (dog) with its own mixer. */
  spawnFree(name: string): { obj: THREE.Object3D; mixer: THREE.AnimationMixer } | null {
    const a = this.accessories.get(name);
    if (!a) return null;
    const obj = SkeletonUtils.clone(a.obj), mixer = new THREE.AnimationMixer(obj);
    const walk = a.clips.find((c) => c.name === 'walk') ?? a.clips[0];
    if (walk) mixer.clipAction(walk).play();
    return { obj, mixer };
  }

  private async fetch(base: string, list: Entry[]) {
    const loader = new GLTFLoader();
    await Promise.all(list.map(async (e) => {
      const g = await loader.loadAsync(`${base}/${e.file}`);
      g.scene.traverse((o) => { if ((o as THREE.Mesh).isMesh) { o.castShadow = true; o.frustumCulled = false; } });
      const m: Model = { scene: g.scene, clips: g.animations, age: e.age ?? 'young', height: e.height ?? 1.75, props: e.props ?? [] };
      if (e.role === 'player') this.player = m; else this.npcs.push(m);
    }));
  }

  instance(m: Model): Human { return new Human(SkeletonUtils.clone(m.scene), m.clips); }
}

/** One animated character with cross-faded idle/walk/run. */
export class Human {
  readonly mixer: THREE.AnimationMixer;
  private actions: Record<string, THREE.AnimationAction> = {};
  private current = '';

  constructor(readonly root: THREE.Object3D, clips: THREE.AnimationClip[]) {
    this.mixer = new THREE.AnimationMixer(root);
    for (const c of clips) this.actions[c.name] = this.mixer.clipAction(c);
    this.play('idle', 0);
  }

  /** Use the slow walk (older people) when walking. */
  slow = false;

  play(name: string, fade = 0.25, offset = 0) {
    if (name === this.current || !this.actions[name]) return;
    const next = this.actions[name].reset().play();
    next.time = offset;
    if (this.current) this.actions[this.current].crossFadeTo(next, fade, false);
    this.current = name;
  }

  /** Choose the clip and playback rate from ground speed (m/s). */
  setSpeed(v: number) {
    if (v < 0.3) { this.play('idle'); this.mixer.timeScale = 1; }
    else if (v < 3.2) { const sl = this.slow && this.actions.walk_slow; this.play(sl ? 'walk_slow' : 'walk'); this.mixer.timeScale = v / (sl ? 1.0 : WALK_SPEED); }
    else { this.play('run'); this.mixer.timeScale = v / RUN_SPEED; }
  }
}
