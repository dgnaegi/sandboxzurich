import * as THREE from 'three';
import type { Human, HumanLib } from './humans';

/**
 * Standing / sitting people at fixed spots taken from the tile meta: benches (sitting), fountains (standing at the rim),
 * bars at night (smokers in front of the door), cafés/kiosks (looking at the phone) and construction workers
 * (hard hat + hi-vis vest, from pipeline/sites.py). Only the spots nearest to the player are populated, from a pool,
 * and the number of people is capped by the budget the crowd hands in (quality.peds based).
 */
type Kind = 'sit' | 'fount' | 'smoke' | 'cafe' | 'work';
/** ry = three rotation.y of the person (model faces local -z); (ax, ay) = unit axis in world for side-by-side offsets */
interface Spot { x: number; y: number; z: number; ry: number; ax: number; ay: number; kind: Kind; k: number; people: Human[]; gear: THREE.Object3D[][] }
const face = (fx: number, fy: number) => Math.atan2(-fx, fy);

const BARS = new Set(['bar', 'pub', 'nightclub', 'biergarten', 'club', 'cocktail']);
const CAFES = new Set(['cafe', 'kiosk', 'bakery', 'ice_cream', 'fast_food', 'confectionery']);
const hash = (x: number, y: number) => Math.abs(Math.floor(x * 73.13 + y * 19.7 + x * y * 0.011)) % 1000;
const hatMat = new THREE.MeshLambertMaterial({ color: 0xf0c020 });
const vestMat = new THREE.MeshLambertMaterial({ color: 0xff7a10 });
const stripeMat = new THREE.MeshLambertMaterial({ color: 0xe8e8d0 });

export class PedSpots {
  private spots: Spot[] = [];
  private pool: Human[] = [];
  private live: Spot[] = [];
  private n = 0;
  private frame = 0;
  hour = 12;
  weekday = 0;
  visRadius = 75;
  /** hard cap for people on spots (set by the crowd every frame) */
  budget = 8;

  constructor(private lib: HumanLib, private parent: THREE.Group) {}

  add(meta: { benches?: number[][]; fountains?: number[][]; signs?: { x: number; y: number; z: number; tx: number; ty: number; kind: string }[]; workers?: number[][] }) {
    const mk = (x: number, y: number, z: number, ry: number, ax: number, ay: number, kind: Kind, k: number) => this.spots.push({ x, y, z, ry, ax, ay, kind, k, people: [], gear: [] });
    for (const [x, y, z, h] of meta.benches ?? []) { const k = hash(x, y), ry = -h + Math.PI / 2; if (k % 100 < 60) mk(x, y, z, ry, Math.cos(ry), Math.sin(ry), 'sit', k); }
    for (const [x, y, z] of meta.fountains ?? []) {
      const k = hash(x, y), a = (k % 628) / 100;
      if (k % 100 < 55) mk(x + Math.cos(a) * 1.4, y + Math.sin(a) * 1.4, z, face(-Math.cos(a), -Math.sin(a)), 1, 0, 'fount', k);
    }
    for (const s of meta.signs ?? []) {
      const k = hash(s.x, s.y), nx = s.ty, ny = -s.tx; // outward facade normal
      if (BARS.has(s.kind)) mk(s.x + nx * 1.4, s.y + ny * 1.4, s.z, face(s.tx, s.ty), s.tx, s.ty, 'smoke', k);
      else if (CAFES.has(s.kind) && k % 100 < 40) mk(s.x + nx * 1.1, s.y + ny * 1.1, s.z, face(-nx, -ny), 1, 0, 'cafe', k);
    }
    for (const [x, y, z, yaw] of meta.workers ?? []) mk(x, y, z, face(Math.cos(yaw), Math.sin(yaw)), 1, 0, 'work', hash(x, y));
  }

  private active(s: Spot): boolean {
    const h = this.hour, night = h >= 22 || h < 6, p = s.k % 100;
    switch (s.kind) {
      case 'sit': return night ? p < 12 : h >= 8 && p < 60;
      case 'fount': return h >= 9 && h < 22;
      case 'cafe': return h >= 7 && h < 20;
      case 'smoke': return h >= 18 || h < 3 ? p < (this.weekday >= 4 && this.weekday <= 5 ? 90 : 55) : false;
      case 'work': return this.weekday <= 4 && ((h >= 7 && h < 12) || (h >= 13 && h < 17));
    }
  }

  private take(): Human {
    return this.pool.pop() ?? this.lib.instance(this.lib.adults[(this.n++ * 7) % this.lib.adults.length]);
  }

  private bones(h: Human, names: string[]) { return names.map((n) => h.root.getObjectByName(n)); }

  private sitPose(h: Human) {
    h.mixer.setTime(0.2);
    const [tl, tr, cl, cr] = this.bones(h, ['thigh_l', 'thigh_r', 'calf_l', 'calf_r']);
    const a = 1.45, b = 1.5;
    tl?.rotateX(a); tr?.rotateX(a); cl?.rotateX(-b); cr?.rotateX(-b);
  }

  private gear(h: Human): THREE.Object3D[] {
    const head = h.root.getObjectByName('head'), chest = h.root.getObjectByName('spine_03') ?? h.root.getObjectByName('spine_02');
    const out: THREE.Object3D[] = [];
    if (head) {
      const hat = new THREE.Mesh(new THREE.SphereGeometry(0.125, 8, 5, 0, Math.PI * 2, 0, Math.PI / 2), hatMat);
      hat.position.set(0, 0.1, 0.01); head.add(hat); out.push(hat);
    }
    if (chest) {
      const vest = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.19, 0.34, 10, 1, true), vestMat);
      vest.material = vestMat; (vest.material as THREE.Material).side = THREE.DoubleSide;
      vest.position.set(0, 0.08, 0.02); chest.add(vest); out.push(vest);
      const st = new THREE.Mesh(new THREE.CylinderGeometry(0.202, 0.192, 0.05, 10, 1, true), stripeMat);
      st.material = stripeMat; stripeMat.side = THREE.DoubleSide; st.position.set(0, 0.04, 0.02); chest.add(st); out.push(st);
    }
    return out;
  }

  private place(h: Human, x: number, y: number, z: number, ry: number) {
    h.root.position.set(x, z, -y);
    h.root.rotation.set(0, ry, 0);
    this.parent.add(h.root);
  }

  private populate(s: Spot) {
    const person = (off: number, ry: number, anim = 'idle') => {
      const h = this.take();
      h.play(anim, 0); h.mixer.setTime((s.k % 7) * 0.4);
      s.people.push(h);
      this.place(h, s.x + s.ax * off, s.y + s.ay * off, s.z, ry);
      return h;
    };
    if (s.kind === 'sit') {
      const n = 1 + (s.k % 3 === 0 ? 1 : 0);
      for (let i = 0; i < n; i++) {
        const off = (i - (n - 1) / 2) * 0.9 + (n === 1 ? ((s.k % 5) - 2) * 0.12 : 0), h = person(off, s.ry, (s.k + i) % 2 ? 'stand_phone' : 'idle');
        this.sitPose(h);
        h.root.position.y -= 0.45;
      }
    } else if (s.kind === 'smoke') { person(-0.5, s.ry); person(0.5, s.ry + Math.PI); }
    else if (s.kind === 'work') s.gear.push(this.gear(person(0, s.ry + (s.k % 5) * 0.15, s.k % 4 === 0 ? 'stand_phone' : 'idle')));
    else person(0, s.ry, s.kind === 'cafe' || s.k % 2 ? 'stand_phone' : 'idle');
  }

  private clear(s: Spot) {
    for (const g of s.gear) for (const o of g) o.removeFromParent();
    s.gear = [];
    for (const h of s.people) { h.root.removeFromParent(); h.root.rotation.set(0, 0, 0); this.pool.push(h); }
    s.people = [];
  }

  get count() { return this.live.reduce((n, s) => n + s.people.length, 0); }

  update(dt: number, px: number, py: number) {
    this.frame++;
    if (this.frame % 20 === 1) {
      const cost = (s: Spot) => (s.kind === 'sit' ? 1 + (s.k % 3 === 0 ? 1 : 0) : s.kind === 'smoke' ? 2 : 1);
      const near = this.spots.filter((s) => Math.abs(s.x - px) < this.visRadius && Math.abs(s.y - py) < this.visRadius && this.active(s))
        .map((s) => ({ s, d: Math.hypot(s.x - px, s.y - py) })).filter((e) => e.d < this.visRadius).sort((a, b) => a.d - b.d);
      let left = this.budget;
      const keep = new Set<Spot>();
      for (const { s } of near) { const c = cost(s); if (left < c) continue; left -= c; keep.add(s); }
      for (const s of this.live) if (!keep.has(s)) this.clear(s);
      let built = 0;
      for (const s of keep) if (!s.people.length && built++ < 2) this.populate(s);
      this.live = [...keep].filter((s) => s.people.length);
    }
    for (const s of this.live) {
      if (s.kind === 'sit' || Math.hypot(s.x - px, s.y - py) > 35) continue; // seated: frozen pose; far: frozen
      for (const h of s.people) h.mixer.update(dt);
    }
  }
}
