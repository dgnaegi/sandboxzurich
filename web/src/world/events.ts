import * as THREE from 'three';
import { mergeStatic } from './mergestatic';
import type { Human, HumanLib } from './humans';
import { bikeGeometries, bikeMaterial, JACKETS } from './traffic';

/**
 * Calendar events (public/data/events.json): flea market on the Kanzleiareal (Sat), Critical Mass (Fri evening),
 * a housing demo (Sat). Each event exists only during its time window and near the player.
 */
interface Ev { id: string; type: 'market' | 'bikes' | 'demo'; title: string; weekday: number[]; from: number; to: number;
  x?: number; y?: number; w?: number; h?: number; dir?: number; stalls?: number; people?: number; riders?: number;
  path?: number[][]; banners?: string[]; zones?: { x: number; y: number; w: number; h: number; dir?: number; cols: number; rows: number }[] }

export const WEEKDAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
const TARP = [0xd84a3a, 0x2f6b9a, 0xe0b040, 0x3a8a5a, 0xf0f0e8, 0x8a4aa0].map((c) => new THREE.MeshLambertMaterial({ color: c }));
const TABLE = new THREE.MeshLambertMaterial({ color: 0x9a7a52 });
const PANTS = new THREE.MeshLambertMaterial({ color: 0x2f3440 });
const SKIN = new THREE.MeshLambertMaterial({ color: 0xd8a888 });
const GOODS = [0xc84030, 0x3060a0, 0xe8d8b0, 0x404040, 0x7a5a3a, 0x60a060].map((c) => new THREE.MeshLambertMaterial({ color: c }));

function along(path: number[][], s: number): [number, number, number] {
  for (let i = 0; i + 1 < path.length; i++) {
    const [ax, ay] = path[i], [bx, by] = path[i + 1], L = Math.hypot(bx - ax, by - ay);
    if (s <= L || i + 2 === path.length) { const t = Math.min(1, Math.max(0, s / L)); return [ax + (bx - ax) * t, ay + (by - ay) * t, Math.atan2(bx - ax, by - ay)]; }
    s -= L;
  }
  return [path[0][0], path[0][1], 0];
}
const pathLen = (p: number[][]) => p.slice(1).reduce((a, q, i) => a + Math.hypot(q[0] - p[i][0], q[1] - p[i][1]), 0);

function banner(text: string): THREE.Object3D {
  const c = document.createElement('canvas'); c.width = 512; c.height = 128;
  const g = c.getContext('2d')!;
  g.fillStyle = '#f4f1ea'; g.fillRect(0, 0, 512, 128);
  g.fillStyle = '#e8267a'; g.font = '64px Anton, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText(text, 256, 68);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
  const o = new THREE.Group();
  const cloth = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 0.65), new THREE.MeshLambertMaterial({ map: tex, side: THREE.DoubleSide }));
  cloth.position.y = 2.1;
  const pole = new THREE.CylinderGeometry(0.02, 0.02, 2.4, 5);
  const p1 = new THREE.Mesh(pole, TABLE), p2 = new THREE.Mesh(pole, TABLE);
  p1.position.set(-1.3, 1.2, 0); p2.position.set(1.3, 1.2, 0);
  o.add(cloth, p1, p2);
  return o;
}

export class Events {
  readonly group = new THREE.Group();
  private list: Ev[] = [];
  private live = new Map<string, { obj: THREE.Group; people: Human[]; tick?: (dt: number, min: number) => void }>();
  private pool: Human[] = [];
  private k = 0;
  private wait = new Map<string, number>();
  onStart: (title: string) => void = () => {};

  constructor(private lib: HumanLib, private ground: (x: number, y: number) => number, private mobile: boolean) {}

  async load(url = '/data/events.json') { this.list = ((await (await fetch(url)).json()) as { events: Ev[] }).events; }

  private human(): Human { return this.pool.pop() ?? this.lib.instance(this.lib.adults[(this.k++ * 5) % this.lib.adults.length]); }

  /** Events active at (weekday, minute) – for the HUD/map. */
  active(weekday: number, minute: number) { return this.list.filter((e) => e.weekday.includes(weekday) && minute >= e.from && minute < e.to); }

  update(dt: number, weekday: number, minute: number, px: number, py: number) {
    const now = new Set(this.active(weekday, minute).map((e) => e.id));
    for (const [id, l] of this.live) if (!now.has(id)) this.stop(id, l);
    for (const e of this.list) {
      if (!now.has(e.id) || this.live.has(e.id)) continue;
      if (e.type === 'market') {
        // static stalls are merged at the ground height of the moment: build them only once the player is near (exact tile heights loaded)
        const near = Math.hypot(e.x! - px, e.y! - py) < 170;
        this.wait.set(e.id, near ? (this.wait.get(e.id) ?? 0) + dt : 0);
        if ((this.wait.get(e.id) ?? 0) < 1.2) continue;
      }
      this.start(e);
    }
    for (const [id, l] of this.live) {
      const e = this.list.find((q) => q.id === id)!;
      if (e.type === 'market' && Math.hypot(e.x! - px, e.y! - py) > 420) { this.stop(id, l); this.wait.set(id, 0); }
    }
    for (const l of this.live.values()) {
      l.tick?.(dt, minute);
      for (const h of l.people) {
        const p = h.root.getWorldPosition(_v);
        if (Math.hypot(p.x - px, -p.z - py) < 70) h.mixer.update(dt);
      }
    }
  }

  private stop(id: string, l: { obj: THREE.Group; people: Human[] }) {
    for (const h of l.people) { h.root.removeFromParent(); this.pool.push(h); }
    this.group.remove(l.obj);
    this.live.delete(id);
  }

  /** one market stall: table, tarp/parasol, goods, every 3rd with a clothes rail, every 4th with crates / furniture */
  private stall(obj: THREE.Group, x: number, y: number, d: number, i: number) {
    const stall = new THREE.Group();
    const top = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.06, 1.0), TABLE); top.position.y = 0.78;
    const roof = new THREE.Mesh(new THREE.BoxGeometry(2.8, 0.05, 2.0), TARP[i % TARP.length]); roof.position.y = i % 5 === 0 ? 2.5 : 2.2; roof.rotation.x = (i % 3 - 1) * 0.08;
    stall.add(top, roof);
    for (const lx of [-1.3, 1.3]) for (const lz of [-0.9, 0.9]) {
      const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 2.2, 5), TABLE); leg.position.set(lx, 1.1, lz); stall.add(leg);
    }
    for (let g = 0; g < 6; g++) {
      const b = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.2 + (g % 3) * 0.1, 0.3), GOODS[(i + g) % GOODS.length]);
      b.position.set(-0.9 + g * 0.36, 0.9, (g % 2) * 0.2 - 0.1); stall.add(b);
    }
    if (i % 3 === 0) { // clothes rail behind the table
      const bar = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.03, 0.03), TABLE); bar.position.set(0, 1.6, -1.3); stall.add(bar);
      for (let g = 0; g < 14; g++) { const cl = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.7 + (g % 3) * 0.1, 0.35), GOODS[(i + g * 2) % GOODS.length]); cl.position.set(-1.0 + g * 0.15, 1.2, -1.3); stall.add(cl); }
    } else if (i % 4 === 1) { // crates / small furniture on the ground in front
      for (let g = 0; g < 3; g++) { const cr = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.35 + (g % 2) * 0.5, 0.45), GOODS[(i + g) % GOODS.length]); cr.position.set(-0.8 + g * 0.8, 0.2 + (g % 2) * 0.25, 1.5); stall.add(cr); }
    }
    stall.position.set(x, this.ground(x, y), -y); stall.rotation.y = -d;
    obj.add(stall);
  }

  /** static customer silhouette (legs, jacket, head) */
  private person(obj: THREE.Group, x: number, y: number, i: number) {
    const z = this.ground(x, y), jc = GOODS[(i * 3) % GOODS.length], g = new THREE.Group();
    const legs = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.85, 0.2), PANTS); legs.position.y = 0.43;
    const body = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.6, 0.24), jc); body.position.y = 1.15;
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.11, 6, 5), SKIN); head.position.y = 1.58;
    g.add(legs, body, head); g.position.set(x, z, -y); g.rotation.y = i * 1.7; g.scale.setScalar(0.92 + (i % 4) * 0.05);
    obj.add(g);
  }

  private start(e: Ev) {
    const obj = new THREE.Group(), people: Human[] = [];
    let tick: ((dt: number, min: number) => void) | undefined;
    if (e.type === 'market') {
      const cx = e.x!, cy = e.y!;
      // zones: stalls in rows over the whole area (Kanzleiareal flea market is huge); legacy: one grid from x/y/w/h/stalls
      const zones = e.zones ?? [{ x: cx, y: cy, w: e.w!, h: e.h!, dir: e.dir ?? 0, cols: 4, rows: Math.ceil(e.stalls! / 4) }];
      const keep = this.mobile ? 0.55 : 1;
      let si = 0;
      const aisles: number[][] = [];
      for (const z of zones) {
        const d = z.dir ?? 0, c = Math.cos(d), s = Math.sin(d), cols = z.cols, rows = z.rows;
        for (let r = 0; r < rows; r++) for (let q = 0; q < cols; q++, si++) {
          const hsh = ((si * 2654435761) >>> 0) / 4294967296;
          if (hsh > keep || ((si * 7919) % 17 === 0)) continue;
          const u = (q - (cols - 1) / 2) * (z.w / cols), v = (r - (rows - 1) / 2) * (z.h / rows);
          const x = z.x + c * u + s * v, y = z.y - s * u + c * v;
          this.stall(obj, x, y, d, si);
          aisles.push([x + s * 2.4, y + c * 2.4, d]);
        }
      }
      const crowd = this.mobile ? 55 : 150;
      for (let i = 0; i < crowd; i++) { // static customers standing in the aisles (merged, one draw call per colour)
        const a = aisles[(i * 7) % aisles.length], off = ((i * 13) % 7) * 0.45 - 1.3;
        this.person(obj, a[0] + Math.cos(a[2]) * off, a[1] - Math.sin(a[2]) * off, i);
      }
      const np = this.mobile ? Math.ceil(e.people! * 0.5) : e.people!;
      for (let i = 0; i < np; i++) {
        const h = this.human(), a = aisles.length ? aisles[(i * 11) % aisles.length] : [cx, cy, 0];
        const x = a[0] + Math.sin(i) * 1.2, y = a[1] + Math.cos(i * 1.7) * 1.2;
        h.root.position.set(x, this.ground(x, y), -y); h.root.rotation.set(0, i * 2.39, 0);
        h.play('idle', 0, i * 0.4);
        obj.add(h.root); people.push(h);
      }
    } else if (e.type === 'bikes') {
      const { body, leg } = bikeGeometries(), mat = bikeMaterial(), n = this.mobile ? Math.ceil(e.riders! * 0.5) : e.riders!;
      const bodies = new THREE.InstancedMesh(body, mat, n), legs = new THREE.InstancedMesh(leg, mat, n * 2);
      for (let i = 0; i < n; i++) { bodies.setColorAt(i, JACKETS[i % JACKETS.length]); legs.setColorAt(2 * i, JACKETS[0]); legs.setColorAt(2 * i + 1, JACKETS[0]); }
      bodies.frustumCulled = legs.frustumCulled = false;
      obj.add(bodies, legs);
      const L = pathLen(e.path!), m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1), Y = new THREE.Vector3(0, 1, 0), X = new THREE.Vector3(1, 0, 0);
      const hip = new THREE.Matrix4(), rot = new THREE.Matrix4();
      tick = (_dt, min) => {
        const head = (min - e.from) * 60 * 4.2; // 4.2 m/s; the mass keeps circling the route during the window
        for (let i = 0; i < n; i++) {
          const sAlong = (((head - Math.floor(i / 4) * 2.4) % L) + L) % L;
          const lane = ((i % 4) - 1.5) * 1.1;
          const [x0, y0, h] = along(e.path!, Math.max(0, Math.min(L, sAlong)));
          const x = x0 + Math.cos(h) * lane, y = y0 - Math.sin(h) * lane;
          const z = this.ground(x, y) - 0.12, vis = 1;
          m.compose(p.set(x, z, -y), q.setFromAxisAngle(Y, -h), one.setScalar(vis));
          bodies.setMatrixAt(i, m);
          for (const side of [0, 1]) {
            const ph = min * 60 * 5 + i + side * Math.PI;
            hip.makeTranslation(side ? 0.11 : -0.11, 1.0, 0.18);
            rot.makeRotationAxis(X, Math.sin(ph) * 0.6 - 0.3);
            legs.setMatrixAt(2 * i + side, m.clone().multiply(hip).multiply(rot));
          }
        }
        bodies.instanceMatrix.needsUpdate = legs.instanceMatrix.needsUpdate = true;
      };
    } else if (e.type === 'demo') {
      const n = this.mobile ? Math.ceil(e.people! * 0.6) : e.people!, L = pathLen(e.path!);
      const flags = (e.banners ?? []).map((t) => { const b = banner(t); obj.add(b); return b; });
      for (let i = 0; i < n; i++) { const h = this.human(); h.setSpeed(1.1); obj.add(h.root); people.push(h); }
      tick = (_dt, min) => {
        const head = (min - e.from) * 60 * 1.1;
        people.forEach((h, i) => {
          const s = (((head - Math.floor(i / 4) * 1.4) % L) + L) % L, lane = ((i % 4) - 1.5) * 0.9;
          const [x0, y0, hd] = along(e.path!, Math.max(0, s));
          const x = x0 + Math.cos(hd) * lane, y = y0 - Math.sin(hd) * lane;
          h.root.position.set(x, this.ground(x, y) - 0.12, -y); h.root.rotation.y = -hd;
        });
        flags.forEach((b, j) => {
          const [x, y, hd] = along(e.path!, (((head - 1 - j * 6) % L) + L) % L);
          b.position.set(x, this.ground(x, y) - 0.12, -y); b.rotation.y = -hd;
        });
      };
    }
    mergeStatic(obj); // stalls, tables, banners: one draw call per material
    this.group.add(obj);
    this.live.set(e.id, { obj, people, tick });
    this.onStart(e.title);
  }
}
const _v = new THREE.Vector3();
