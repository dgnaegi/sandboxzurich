import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js';
import { dress } from './tint';

/**
 * Realistic MakeHuman/MPFB characters (CC0), exported by pipeline/blender. Per-figure clips (CMU mocap, retargeted): idle, walk, run, walk_slow.
 * Shared library clips (anims_<class>.glb, class = A|B x young|old, pelvis track scaled to the figure): shift, look, stand2, wait, talk, listen,
 * talk2, argue, call, text, crossed, crossed2, pockets, pockets2, sit, sit_talk, sit_chat (see research/humans.md R7).
 */
interface Entry { id: string; file: string; role: 'player' | 'npc'; sex: string; age: string; height?: number; props?: string[]; clip_speed?: ClipSpeed }
export interface Model { scene: THREE.Object3D; clips: THREE.AnimationClip[]; age: string; height: number; props: string[]; speeds?: ClipSpeed; cls: string }

/** Reference figure height (m) of each library class (the figure the clips were retargeted on). */
const LIB_REF: Record<string, number> = { A_young: 1.757, B_young: 1.467, A_old: 1.767, B_old: 1.491 };
/** Standing / seated clip families; `pick` chooses one per person so neighbours differ. */
export const FAMILY = {
  idle: ['idle', 'shift', 'stand2', 'listen', 'look', 'crossed', 'pockets', 'crossed2', 'pockets2'],
  wait: ['wait', 'shift', 'crossed', 'pockets', 'look', 'stand2', 'idle'],
  phone: ['text'], call: ['call'], talk: ['talk', 'talk2', 'listen', 'listen', 'talk2', 'listen'], listen: ['listen', 'stand2', 'crossed', 'shift'],
  sit: ['sit', 'sit+text'], sitTalk: ['sit_talk', 'sit_chat'],
} as const;
/** Phone placement per clip (bone-local, measured with pipeline/blender/check/anim_sheet.mjs). */
const PHONE_FIT: Record<string, { bone: string; offset: number[]; rotation: number[] }> = {
  text: { bone: 'hand_r', offset: [-0.0072, 0.0603, -0.0133], rotation: [3.0106, -0.6798, -2.9191] },
  call: { bone: 'hand_r', offset: [0.0428, 0.0603, -0.0133], rotation: [3.0106, -0.6798, -2.9191] },
};
/** Old name kept for scenes: stand_phone = texting. */
const ALIAS: Record<string, string> = { stand_phone: 'text' };
let scarfGeo: THREE.BufferGeometry | undefined;
const SCARF_COLORS = [0x7a2430, 0xb8862b, 0x1d4a36, 0x3a3f66, 0xd8cdb6, 0xa5522a, 0x6b7077, 0xd9a2b0, 0x15171a];
const LEG_NODES = /^(pelvis|spine_0\d|thigh_|calf_|foot_|ball_)/;
interface Accessory { name: string; obj: THREE.Object3D; bone: string | null; offset: number[]; rotation: number[]; clips: THREE.AnimationClip[] }

export class HumanLib {
  player!: Model;
  npcs: Model[] = [];
  private libs = new Map<string, THREE.AnimationClip[]>();
  private libCache = new Map<string, THREE.AnimationClip[]>();

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
    await lib.loadLibs(base);
    await lib.fetch(base, [...player, ...order.slice(0, first)]);
    // the other figures only add variety: load them after the start so they do not compete with the first tiles
    setTimeout(() => void lib.fetch(base, order.slice(first)).then(() => lib.loadAccessories()), 8000);
    return lib;
  }

  /** Shared animation libraries (about 0.4 MB each); a failed file only means fewer clips. */
  private async loadLibs(base: string) {
    const loader = new GLTFLoader();
    await Promise.all(Object.keys(LIB_REF).map(async (c) => {
      try { this.libs.set(c, (await loader.loadAsync(`${base}/anims_${c}.glb`)).animations); } catch { /* optional */ }
    }));
  }

  /** Library clips for a figure: rotation tracks shared, pelvis translation scaled by height / reference height. */
  private libClips(cls: string, height: number): THREE.AnimationClip[] {
    const src = this.libs.get(cls);
    if (!src) return [];
    const k = Math.round((height / LIB_REF[cls]) * 50) / 50, key = `${cls}:${k}`;
    let out = this.libCache.get(key);
    if (!out) {
      out = src.map((c) => new THREE.AnimationClip(c.name, c.duration, c.tracks.map((t) => {
        if (!t.name.endsWith('.position')) return t;
        const v = t.values.slice(); for (let i = 0; i < v.length; i++) v[i] *= k;
        return new THREE.VectorKeyframeTrack(t.name, t.times, v);
      })));
      this.libCache.set(key, out);
    }
    return out;
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
      const age = e.age ?? 'young', height = e.height ?? 1.75, cls = `${e.sex === 'm' ? 'A' : 'B'}_${age === 'old' ? 'old' : 'young'}`;
      const own = g.animations.filter((c) => c.name !== 'stand_phone');
      const m: Model = { scene: g.scene, clips: e.role === 'player' ? own : [...own, ...this.libClips(cls, height)], age, height, props: e.props ?? [], speeds: e.clip_speed, cls };
      if (e.role === 'player') this.player = m; else this.npcs.push(m);
    }));
  }

  instance(m: Model): Human { const h = new Human(SkeletonUtils.clone(m.scene), m.clips, m.speeds); h.lib = this; h.model = m; return h; }

  /** New random autumn outfit colours (jacket, trousers, shoes) for a pooled person; the player keeps her own. */
  dress(h: Human) {
    if (!h.model) return;
    dress(h, h.model);
    this.scarf(h, h.model.age !== 'child' && Math.random() < 0.22);
  }

  /** Wool scarf (snood) around the neck: one shared torus, colour from the autumn palette. */
  private scarf(h: Human, on: boolean) {
    let s = h.scarfObj;
    if (!on) { if (s) s.visible = false; return; }
    const neck = h.root.getObjectByName('neck_01');
    if (!neck) return;
    if (!s) {
      scarfGeo ??= new THREE.TorusGeometry(0.068, 0.03, 6, 14).rotateX(Math.PI / 2).translate(0, 0.02, 0);
      s = h.scarfObj = new THREE.Mesh(scarfGeo, new THREE.MeshLambertMaterial());
      neck.add(s);
    }
    (s.material as THREE.MeshLambertMaterial).color.set(SCARF_COLORS[Math.floor(Math.random() * SCARF_COLORS.length)]);
    s.visible = true;
  }

  /** Show the phone in the hand while a phone clip plays (created on first use, hidden otherwise). */
  phoneFor(h: Human, clip: string) {
    const fit = PHONE_FIT[clip];
    if (!fit) { if (h.phone) h.phone.visible = false; return; }
    if (!h.phone) {
      const a = this.accessories.get('phone');
      if (!a) return;
      h.phone = SkeletonUtils.clone(a.obj); h.phone.userData.bone = '';
    }
    const bone = h.root.getObjectByName(fit.bone);
    if (!bone) return;
    if (h.phone.parent !== bone) bone.add(h.phone);
    h.phone.position.fromArray(fit.offset); h.phone.rotation.fromArray(fit.rotation as [number, number, number]); h.phone.visible = true;
  }
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
  /** Created lazily (a mixer binding per clip per person would be wasted on the ~25 clips nobody plays). */
  readonly actions: Record<string, THREE.AnimationAction> = {};
  private target: Record<string, number> = {};
  private weight: Record<string, number> = {};
  private gait = false;
  private clips = new Map<string, THREE.AnimationClip>();
  /** set by HumanLib.instance(); drives the phone prop for phone clips */
  lib?: HumanLib;
  phone?: THREE.Object3D;
  model?: Model;
  scarfObj?: THREE.Mesh;
  current = 'idle';

  constructor(readonly root: THREE.Object3D, clips: THREE.AnimationClip[], private speeds: ClipSpeed = DEFAULT_SPEED) {
    this.mixer = new THREE.AnimationMixer(root);
    for (const c of clips) this.clips.set(c.name, c);
    for (const n of ['idle', 'walk', 'run', 'walk_slow']) this.ensure(n);
    const upd = this.mixer.update.bind(this.mixer);
    this.mixer.update = (dt: number) => { this.blend(dt); return upd(dt); };
    this.play('idle', 0);
  }

  /** Use the slow walk (older people) when walking. */
  slow = false;

  /** A clip exists (own or library). `a+b` = legs/pelvis/spine of a with arms, neck and head of b. */
  has(name: string): boolean { name = ALIAS[name] ?? name; return name.includes('+') ? name.split('+').every((n) => this.clips.has(n)) : this.clips.has(name); }

  /** One clip of the family chosen by `r` in [0,1); skips clips this figure lacks. */
  pick(family: keyof typeof FAMILY, r: number): string {
    const l = FAMILY[family].filter((n) => this.has(n));
    return l.length ? l[Math.floor(r * l.length) % l.length] : 'idle';
  }

  private ensure(name: string): THREE.AnimationAction | null {
    if (this.actions[name]) return this.actions[name];
    let clip = this.clips.get(name);
    if (!clip && name.includes('+')) {                          // mixed clip, built once per figure
      const [a, b] = name.split('+').map((n) => this.clips.get(n));
      if (a && b) clip = new THREE.AnimationClip(name, a.duration, [...a.tracks.filter((t) => LEG_NODES.test(t.name)), ...b.tracks.filter((t) => !LEG_NODES.test(t.name))]);
    }
    if (!clip) return null;
    const act = this.actions[name] = this.mixer.clipAction(clip);
    this.weight[name] = 0; this.target[name] = 0; act.play(); act.setEffectiveWeight(0);
    return act;
  }

  /** Switch to a single clip (idle, wait, talk, sit, ...); offset = start time in s (default: random, so neighbours are out of phase). */
  play(name: string, fade = 0.25, offset?: number) {
    name = ALIAS[name] ?? name;
    const act = this.ensure(name);
    if (!act) return;
    if (!this.gait && this.target[name] === 1) return;
    this.gait = false; this.current = name;
    for (const n in this.target) this.target[n] = n === name ? 1 : 0;
    for (const a of Object.values(this.actions)) a.timeScale = 1;
    act.time = offset ?? Math.random() * act.getClip().duration;
    if (fade <= 0) this.blend(1e3);
    this.lib?.phoneFor(this, name);
  }

  /** Choose clip weights and playback rates from ground speed (m/s). */
  setSpeed(v: number) {
    const A = this.actions, sp = this.speeds;
    if (!A.walk) return;
    if (this.phone?.visible) this.phone.visible = false;
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
