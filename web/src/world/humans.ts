import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js';

/** Realistic MakeHuman/MPFB characters (CC0), exported by pipeline/blender. Animations (CMU mocap, retargeted): idle, walk, run, walk_slow, stand_phone. */
interface Entry { id: string; file: string; role: 'player' | 'npc'; sex: string; age: string; height?: number; props?: string[]; clip_speed?: ClipSpeed }
export interface Model { scene: THREE.Object3D; clips: THREE.AnimationClip[]; age: string; height: number; props: string[]; speeds?: ClipSpeed }
interface Accessory { name: string; obj: THREE.Object3D; bone: string | null; offset: number[]; rotation: number[]; clips: THREE.AnimationClip[] }

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
      const m: Model = { scene: g.scene, clips: g.animations, age: e.age ?? 'young', height: e.height ?? 1.75, props: e.props ?? [], speeds: e.clip_speed };
      if (e.role === 'player') this.player = m; else this.npcs.push(m);
    }));
  }

  instance(m: Model): Human { return new Human(SkeletonUtils.clone(m.scene), m.clips, m.speeds); }
}

/** Measured ground speed (m/s) of the in-place mocap loops (manifest `clip_speed`); playback rate = v / clip speed keeps feet from sliding. */
export interface ClipSpeed { walk: number; run: number; walk_slow?: number }
const DEFAULT_SPEED: ClipSpeed = { walk: 1.3, run: 3.6, walk_slow: 0.8 };
const smooth = (a: number, b: number, v: number) => { const t = Math.min(1, Math.max(0, (v - a) / (b - a))); return t * t * (3 - 2 * t); };

/**
 * One animated character. Standing: idle / stand_phone via play(). Moving: setSpeed(v) blends idle -> (walk_slow ->) walk -> run by
 * weight (gait clips phase-locked so feet never cross over), each clip played at v / clip_speed.
 */
export class Human {
  readonly mixer: THREE.AnimationMixer;
  readonly actions: Record<string, THREE.AnimationAction> = {};
  private target: Record<string, number> = {};
  private weight: Record<string, number> = {};
  private gait = false;

  constructor(readonly root: THREE.Object3D, clips: THREE.AnimationClip[], private speeds: ClipSpeed = DEFAULT_SPEED) {
    this.mixer = new THREE.AnimationMixer(root);
    for (const c of clips) { this.actions[c.name] = this.mixer.clipAction(c); this.weight[c.name] = 0; this.target[c.name] = 0; }
    for (const a of Object.values(this.actions)) { a.play(); a.setEffectiveWeight(0); }
    const upd = this.mixer.update.bind(this.mixer);
    this.mixer.update = (dt: number) => { this.blend(dt); return upd(dt); };
    this.play('idle', 0);
  }

  /** Use the slow walk (older people) when walking. */
  slow = false;

  /** Switch to a single clip (idle, stand_phone, ...). */
  play(name: string, fade = 0.25, offset = 0) {
    if (!this.actions[name]) return;
    if (!this.gait && this.target[name] === 1) return;
    this.gait = false;
    for (const n in this.target) this.target[n] = n === name ? 1 : 0;
    for (const a of Object.values(this.actions)) a.timeScale = 1;
    this.actions[name].time = offset;
    if (fade <= 0) this.blend(1e3);
  }

  /** Choose clip weights and playback rates from ground speed (m/s). */
  setSpeed(v: number) {
    const A = this.actions, sp = this.speeds;
    if (!A.walk) return;
    if (!Number.isFinite(v)) v = 0;
    const ladder: [string, number][] = [];
    if (this.slow && A.walk_slow) ladder.push(['walk_slow', sp.walk_slow ?? DEFAULT_SPEED.walk_slow!]);
    ladder.push(['walk', sp.walk]); if (A.run) ladder.push(['run', sp.run]);
    this.gait = true;
    const move = smooth(0.12, 0.55, v);                         // idle -> moving
    const w: Record<string, number> = {};
    for (const n in this.target) w[n] = 0;
    w.idle = 1 - move;
    let i = 0;                                                  // lower clip of the pair that contains v
    while (i < ladder.length - 2 && v > ladder[i + 1][1] * 0.9) i++;
    const [lo, clo] = ladder[i];
    if (ladder.length > i + 1) {
      const [hi, chi] = ladder[i + 1];
      const t0 = clo * 1.3, t1 = Math.max(t0 + 0.4, chi * 0.8), up = smooth(t0, t1, v);
      w[lo] = move * (1 - up); w[hi] = move * up;
      A[lo].timeScale = Math.min(2.4, Math.max(0.35, v / clo)); A[hi].timeScale = Math.min(2.4, Math.max(0.35, v / chi));
    } else { w[lo] = move; A[lo].timeScale = Math.min(2.4, Math.max(0.35, v / clo)); }
    for (const n in w) this.target[n] = w[n];
    if (A.idle) A.idle.timeScale = 1;
  }

  private blend(dt: number) {
    const k = dt > 0 ? 1 - Math.exp(-dt * 9) : 0;
    let master: THREE.AnimationAction | null = null, mw = -1;
    const gaitNames = ['walk_slow', 'walk', 'run'];
    for (const n in this.actions) {
      const w = (this.weight[n] += (this.target[n] - this.weight[n]) * k);
      this.actions[n].setEffectiveWeight(w < 0.002 ? 0 : w);
      if (gaitNames.includes(n) && w > mw) { mw = w; master = this.actions[n]; }
    }
    if (this.gait && master) {                                  // phase-lock the other gait clips to the dominant one
      const ph = (master.time / master.getClip().duration) % 1;
      for (const n of gaitNames) { const a = this.actions[n]; if (a && a !== master && this.weight[n] > 0.002) a.time = ph * a.getClip().duration; }
    }
  }
}
