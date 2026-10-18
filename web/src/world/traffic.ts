import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/**
 * Moving cars and cyclists on the real OSM road graph (public/data/roads.json, pipeline/roadgraph.py).
 * Local metres: x east, y north. Three position = (x, ground-0.12, -y). Heading = atan2(dy, dx) in local metres.
 * All agents are instances (1 InstancedMesh per car type, 3 meshes for bikes: body + 2 legs), no per-agent objects.
 */
interface Agent {
  kind: 'car' | 'bike'; e: number; s: number; v: number; nxt: number; x: number; y: number; h: number; ex: number; ey: number;
  seg: number; vmul: number; len: number; type: string; color: THREE.Color; wait: number; free: boolean; phase: number;
  id: number; alive: boolean; yielding: boolean; acc: number; turn: number; dz: number;
  /** move2: cached distance to a pole/sign/bollard in the lane, edge on which such obstacles are ignored (waited too long) */
  sd?: number; sIgn?: number;
}
interface Edge {
  a: number; b: number; p: Float32Array; cum: Float32Array; len: number; v: number; w: number;
  d0x: number; d0y: number; d1x: number; d1y: number; list: Agent[];
  /** bridge deck height per vertex, NaN = terrain (pipeline/decktrack.py); undefined = no deck on this edge */
  z?: Float32Array;
}
interface Graph { edges: Edge[]; outs: number[][]; ins: number[][]; wcum: Float64Array; total: number }

const B = 4.5, TAU = 0.7, MINGAP = 2, CAP = 64;
const safe = (gap: number, vl: number) => -B * TAU + Math.sqrt((B * TAU) ** 2 + vl * vl + 2 * B * Math.max(0, gap - MINGAP));

function buildGraph(raw: { a: number; b: number; p: number[]; v: number; w: number; z?: (number | null)[] }[], nn: number): Graph {
  const edges: Edge[] = [];
  for (const r of raw) {
    const n = r.p.length / 2;
    if (n < 2) continue;
    const p = Float32Array.from(r.p), cum = new Float32Array(n);
    for (let i = 1; i < n; i++) cum[i] = cum[i - 1] + Math.hypot(p[2 * i] - p[2 * i - 2], p[2 * i + 1] - p[2 * i - 1]);
    const len = cum[n - 1];
    if (len < 1) continue;
    const dir = (i: number) => { const dx = p[2 * i + 2] - p[2 * i], dy = p[2 * i + 3] - p[2 * i + 1], l = Math.hypot(dx, dy) || 1; return [dx / l, dy / l]; };
    const [d0x, d0y] = dir(0), [d1x, d1y] = dir(n - 2);
    edges.push({ a: r.a, b: r.b, p, cum, len, v: r.v, w: r.w, d0x, d0y, d1x, d1y, list: [], z: r.z ? Float32Array.from(r.z, (v) => v ?? NaN) : undefined });
  }
  const outs: number[][] = Array.from({ length: nn }, () => []), ins: number[][] = Array.from({ length: nn }, () => []);
  const wcum = new Float64Array(edges.length);
  let t = 0;
  edges.forEach((e, i) => { outs[e.a].push(i); ins[e.b].push(i); t += e.len; wcum[i] = t; });
  return { edges, outs, ins, wcum, total: t };
}

/** Low-poly cyclist (front -Z, origin = ground below the middle of the bike). Legs are separate so they can pedal. */
export function bikeGeometries() {
  const parts: THREE.BufferGeometry[] = [];
  const add = (g: THREE.BufferGeometry, col: number, paint = 0) => {
    const ng = g.index ? g.toNonIndexed() : g;
    ng.deleteAttribute('uv');
    const n = ng.attributes.position.count, c = new THREE.Color(col), arr = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) { arr[3 * i] = c.r; arr[3 * i + 1] = c.g; arr[3 * i + 2] = c.b; }
    ng.setAttribute('color', new THREE.BufferAttribute(arr, 3));
    ng.setAttribute('_paint', new THREE.BufferAttribute(new Float32Array(n).fill(paint), 1));
    parts.push(ng);
  };
  const bar = (a: number[], b: number[], th: number, col: number, paint = 0) => {
    const va = new THREE.Vector3(...a), vb = new THREE.Vector3(...b), len = va.distanceTo(vb);
    const g = new THREE.BoxGeometry(th, th, len);
    const o = new THREE.Object3D();
    o.position.copy(va).add(vb).multiplyScalar(0.5); o.lookAt(vb); o.updateMatrix();
    g.applyMatrix4(o.matrix);
    add(g, col, paint);
  };
  for (const z of [-0.55, 0.55]) add(new THREE.TorusGeometry(0.31, 0.035, 4, 10).rotateY(Math.PI / 2).translate(0, 0.34, z), 0x1d1d1f);
  const F = 0x3a4048;
  bar([0, 0.3, 0.1], [0, 0.95, 0.2], 0.04, F); bar([0, 0.95, 0.2], [0, 0.97, -0.42], 0.04, F); bar([0, 0.3, 0.1], [0, 0.97, -0.42], 0.04, F);
  bar([0, 0.34, -0.55], [0, 1.0, -0.43], 0.035, F); bar([0, 0.34, 0.55], [0, 0.3, 0.1], 0.035, F); bar([0, 0.34, 0.55], [0, 0.95, 0.2], 0.035, F);
  bar([-0.25, 1.03, -0.44], [0.25, 1.03, -0.44], 0.03, 0x15161a);
  add(new THREE.BoxGeometry(0.1, 0.05, 0.22).translate(0, 0.99, 0.22), 0x15161a);
  bar([0, 1.02, 0.22], [0, 1.5, -0.1], 0.3, 0xffffff, 1); // torso
  add(new THREE.IcosahedronGeometry(0.12, 0).translate(0, 1.7, -0.2), 0xd9a98a);
  add(new THREE.BoxGeometry(0.27, 0.08, 0.3).translate(0, 1.79, -0.19), 0x2a2e36); // helmet-ish cap
  for (const sx of [-1, 1]) bar([sx * 0.19, 1.45, -0.1], [sx * 0.24, 1.03, -0.44], 0.07, 0xffffff, 1);
  const body = mergeGeometries(parts)!;
  const leg = new THREE.BoxGeometry(0.12, 0.82, 0.13).translate(0, -0.41, 0).toNonIndexed();
  leg.deleteAttribute('uv');
  const n = leg.attributes.position.count, c = new THREE.Color(0x2b3140), arr = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { arr[3 * i] = c.r; arr[3 * i + 1] = c.g; arr[3 * i + 2] = c.b; }
  leg.setAttribute('color', new THREE.BufferAttribute(arr, 3));
  leg.setAttribute('_paint', new THREE.BufferAttribute(new Float32Array(n), 1));
  return { body, leg };
}

export const JACKETS = [0xd32f2f, 0xf57c00, 0xfbc02d, 0x00897b, 0x1976d2, 0x388e3c, 0x212121, 0xeeeeee, 0x7b1fa2, 0xe91e63].map((c) => new THREE.Color(c));

export function bikeMaterial() {
  const m = new THREE.MeshLambertMaterial({ vertexColors: true });
  m.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float _paint;')
      .replace('#include <color_vertex>', 'vColor = vec4(1.0);\nvColor.rgb *= color.rgb;\n#ifdef USE_INSTANCING_COLOR\nvColor.rgb *= mix(vec3(1.0), instanceColor.rgb, _paint);\n#endif');
  };
  return m;
}

export class Traffic {
  private cars: Graph | null = null;
  private bikes: Graph | null = null;
  private carMesh: Record<string, THREE.InstancedMesh> = {};
  private carLen: Record<string, number> = {};
  private bikeMesh!: THREE.InstancedMesh;
  private legL!: THREE.InstancedMesh;
  private legR!: THREE.InstancedMesh;
  private agents: Agent[] = [];
  private nCars = 0;
  private nBikes = 0;
  private _maxCars = 20;
  private _maxBikes = 8;
  private nextId = 1;
  private spawnT = 0;
  private out: { x: number; y: number; heading: number; kind: 'car' | 'bike'; len: number; v: number; id: number; brake: boolean; turn: number; type: string; edge: number }[] = [];
  private readonly group = new THREE.Group();
  private tmpA = new THREE.Matrix4();
  private tmpB = new THREE.Matrix4();

  constructor(scene: THREE.Scene, private ground: (x: number, y: number) => number,
    private carGeo: Record<string, THREE.BufferGeometry>, private carMaterial: THREE.Material,
    private pick: (key: number) => { type: string; color: THREE.Color }) {
    scene.add(this.group);
  }

  get maxCars() { return this._maxCars; }
  set maxCars(n: number) { this._maxCars = Math.max(0, Math.min(CAP * 2, Math.floor(n))); }
  get maxBikes() { return this._maxBikes; }
  set maxBikes(n: number) { this._maxBikes = Math.max(0, Math.min(CAP, Math.floor(n))); }

  async load(url = '/data/roads.json') {
    const j = await (await fetch(url)).json();
    const nn = j.nodes.length;
    this.cars = buildGraph(j.cars, nn);
    this.bikes = buildGraph(j.bikes, nn);
    for (const [type, g] of Object.entries(this.carGeo)) {
      g.computeBoundingBox();
      this.carLen[type] = g.boundingBox!.max.z - g.boundingBox!.min.z;
      const m = new THREE.InstancedMesh(g, this.carMaterial, CAP);
      m.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(CAP * 3), 3);
      m.frustumCulled = false; m.count = 0;
      this.carMesh[type] = m; this.group.add(m);
    }
    const bg = bikeGeometries(), mat = bikeMaterial();
    this.bikeMesh = new THREE.InstancedMesh(bg.body, mat, CAP);
    this.bikeMesh.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(CAP * 3), 3);
    this.legL = new THREE.InstancedMesh(bg.leg, mat, CAP);
    this.legR = new THREE.InstancedMesh(bg.leg, mat, CAP);
    for (const m of [this.bikeMesh, this.legL, this.legR]) { m.frustumCulled = false; m.count = 0; this.group.add(m); }
  }

  positions() { return this.out; }

  /**
   * Closest car whose body is within `r` metres of (x, y); with `take` it leaves the traffic (the driver gets out)
   * and its state is returned: compass heading (0 = north, clockwise) and speed along the road.
   */
  findCar(x: number, y: number, r: number, take = false): { d: number; type: string; color: THREE.Color; x: number; y: number; h: number; v: number; len: number } | null {
    let best: Agent | null = null, bd = r;
    for (const a of this.agents) {
      if (a.kind !== 'car' || !a.alive) continue;
      const c = Math.cos(a.h), s = Math.sin(a.h), dx = x - a.x, dy = y - a.y;
      const al = Math.max(-a.len / 2, Math.min(a.len / 2, dx * c + dy * s)), ac = Math.max(-0.9, Math.min(0.9, -dx * s + dy * c));
      const d = Math.hypot(dx * c + dy * s - al, -dx * s + dy * c - ac);
      if (d < bd) { bd = d; best = a; }
    }
    if (!best) return null;
    const out = { d: bd, type: best.type, color: best.color, x: best.x, y: best.y, h: Math.PI / 2 - best.h, v: best.v, len: best.len };
    if (take) {
      best.alive = false;
      this.graph(best).edges[best.e].list = this.graph(best).edges[best.e].list.filter((c) => c !== best);
      this.agents = this.agents.filter((a) => a.alive);
      this.nCars = this.agents.filter((a) => a.kind === 'car').length;
    }
    return out;
  }

  // ---------- helpers ----------
  private graph(a: Agent) { return (a.kind === 'car' ? this.cars : this.bikes)!; }

  private chooseNext(g: Graph, e: Edge): number {
    const outs = g.outs[e.b];
    let tot = 0;
    const w: number[] = [];
    for (const o of outs) {
      const oe = g.edges[o];
      const back = oe.b === e.a && oe.a === e.b;
      const dot = e.d1x * oe.d0x + e.d1y * oe.d0y;
      const wt = back ? 0 : dot > 0.9 ? 2.5 : dot < -0.5 ? 0.05 : 1;
      w.push(wt); tot += wt;
    }
    if (tot <= 0) return outs.length ? outs[0] : -1; // dead end: turn around if possible
    let r = Math.random() * tot;
    for (let i = 0; i < outs.length; i++) { r -= w[i]; if (r <= 0) return outs[i]; }
    return outs[outs.length - 1];
  }

  private place(a: Agent, e: Edge): [number, number] {
    const p = e.p, cum = e.cum, n = cum.length;
    let i = Math.min(a.seg, n - 2);
    while (i > 0 && cum[i] > a.s) i--;
    while (i < n - 2 && cum[i + 1] < a.s) i++;
    a.seg = i;
    const l = cum[i + 1] - cum[i] || 1, t = Math.min(1, Math.max(0, (a.s - cum[i]) / l));
    const x0 = p[2 * i], y0 = p[2 * i + 1], x1 = p[2 * i + 2], y1 = p[2 * i + 3];
    this._hx = (x1 - x0) / l; this._hy = (y1 - y0) / l;
    if (e.z) {
      const z0 = e.z[i], z1 = e.z[i + 1], n0 = Number.isNaN(z0), n1 = Number.isNaN(z1);
      this._z = n0 && n1 ? NaN : n0 ? z1 : n1 ? z0 : z0 + (z1 - z0) * t;
    } else this._z = NaN;
    return [x0 + (x1 - x0) * t, y0 + (y1 - y0) * t];
  }
  private _z = NaN;
  private _hx = 1; private _hy = 0;

  private turnOf(e: Edge, ne: Edge | null) {
    if (!ne) return 0;
    const dot = e.d1x * ne.d0x + e.d1y * ne.d0y, cr = e.d1x * ne.d0y - e.d1y * ne.d0x;
    if (dot > 0.9) return 0;
    return dot < -0.5 || cr > 0 ? 1 : -1; // 1 left/u-turn, -1 right
  }

  /** Simple priority: major road, right-hand rule, oncoming traffic when turning left. */
  private shouldYield(a: Agent, e: Edge, g: Graph): boolean {
    const me = a.nxt >= 0 ? g.edges[a.nxt] : null;
    const myTurn = this.turnOf(e, me);
    const myD = e.len - a.s;
    for (const ie of g.ins[e.b]) {
      if (ie === a.e) continue;
      const E2 = g.edges[ie];
      for (const c of E2.list) {
        const d = E2.len - c.s;
        if (d > 25) continue;
        const cn = c.nxt >= 0 ? g.edges[c.nxt] : null, cTurn = this.turnOf(E2, cn);
        const dot = e.d1x * E2.d1x + e.d1y * E2.d1y;
        let conflict: boolean, prio: boolean;
        if (a.nxt >= 0 && c.nxt === a.nxt) { conflict = true; prio = E2.w > e.w + 1.5 || (Math.abs(E2.w - e.w) <= 1.5 && (d < myD || (d === myD && c.id < a.id))); }
        else if (dot < -0.8) { conflict = myTurn === 1 && cTurn !== 1; prio = true; }
        else if (myTurn === -1) { conflict = false; prio = false; }
        else {
          conflict = true;
          const dw = E2.w - e.w;
          prio = dw > 1.5 ? true : dw < -1.5 ? false : (e.d1x * E2.d1y - e.d1y * E2.d1x) > 0;
        }
        if (!conflict) continue;
        if (d < 4 && c.v > 1) return true; // already crossing
        if (prio && (c.v > 0.3 || d < 10)) return true;
      }
    }
    if (myTurn !== -1) {
      for (const oi of g.outs[e.b]) {
        if (oi === a.nxt) continue;
        const E3 = g.edges[oi];
        if (E3.b === e.a || Math.abs(E3.d0x * e.d1x + E3.d0y * e.d1y) > 0.9) continue;
        for (const c of E3.list) if (c.s < 7 && c.v > 0.5) return true;
      }
    }
    return false;
  }

  private step(a: Agent, g: Graph, dt: number, avoid: { x: number; y: number; r: number }[], px: number, py: number) {
    const e = g.edges[a.e], dEnd = e.len - a.s;
    let vt = (e.v / 3.6) * a.vmul;
    // leader on same edge / next edge
    let gap = Infinity, vl = 0, boxBlock = false;
    for (const c of e.list) {
      if (c === a || c.s <= a.s) continue;
      const gg = c.s - a.s - (a.len + c.len) / 2;
      if (gg < gap) { gap = gg; vl = c.v; }
    }
    const ne = a.nxt >= 0 ? g.edges[a.nxt] : null;
    if (gap === Infinity && ne && dEnd < 50) {
      for (const c of ne.list) {
        if (c === a) continue;
        const gg = dEnd + c.s - (a.len + c.len) / 2;
        if (gg < gap) { gap = gg; vl = c.v; }
        if (c.s < 8 + a.len) boxBlock = true;
      }
    }
    if (gap < Infinity) vt = Math.min(vt, safe(gap, vl));
    // approach junction
    const stopOff = Math.min(e.w / 2, 5) + 0.5;
    const dStop = dEnd - a.len / 2 - stopOff;
    if (ne) {
      const tn = this.turnOf(e, ne);
      const vNode = tn === 0 ? vt : tn > 0 ? 5 : 4;
      vt = Math.min(vt, Math.sqrt(vNode * vNode + 2 * B * Math.max(0, dEnd - a.len / 2 - 1)));
    }
    a.yielding = false;
    if (a.kind === 'car' && ne && !a.free && dStop < 25 && dStop > -1.5) {
      if (boxBlock || this.shouldYield(a, e, g)) { a.yielding = true; vt = Math.min(vt, safe(dStop, 0)); }
    } else if (boxBlock && dStop > -1.5) { vt = Math.min(vt, safe(dStop, 0)); }
    // avoid circles (player, pedestrians)
    const hx = Math.cos(a.h), hy = Math.sin(a.h);
    for (const c of avoid) {
      const dx = c.x - a.x, dy = c.y - a.y;
      if (dx * dx + dy * dy > 900) continue;
      const f = dx * hx + dy * hy, l = -dx * hy + dy * hx;
      if (f > -a.len / 2 && f < 12 + a.v * 1.5 && Math.abs(l) < c.r + (a.kind === 'car' ? 1.1 : 0.6)) {
        vt = Math.min(vt, safe(f - c.r - a.len / 2, 0));
      }
    }
    // move2: posts, signs and bollards sticking into the lane (static circle colliders): brake before them; after 3 s of waiting drive on (never a permanent jam)
    if (this.solidAhead && a.sIgn !== a.e) {
      if ((this.tick + a.id) % 5 === 0) {
        const d = this.solidAhead(a.x, a.y, hx, hy, 14 + a.v * 1.2, (a.kind === 'car' ? 1.0 : 0.45));
        a.sd = d === Infinity ? undefined : d - a.len / 2 - 0.3;
      }
      if (a.sd !== undefined) {
        a.sd -= a.v * dt;
        vt = Math.min(vt, safe(Math.max(0, a.sd), 0));
        if (a.v < 0.2) { a.wait += dt; if (a.wait > 3) { a.sIgn = a.e; a.sd = undefined; } }
      }
    }
    if (a.yielding && a.v < 0.3) { a.wait += dt; if (a.wait > 5) a.free = true; } else if (a.v > 2) a.wait = 0;
    vt = Math.max(0, vt);
    // soft pull-away and braking: target acceleration eases in (jerk-limited) instead of switching on/off
    const want = vt > a.v ? Math.min(a.kind === 'car' ? 2.6 : 1.2, (vt - a.v) * 1.4) : Math.max(-9, (vt - a.v) * 3.5);
    a.acc += (want - a.acc) * Math.min(1, dt * (want < a.acc ? 6 : 2.5));
    a.v = Math.max(0, a.v + a.acc * dt);
    if (vt === 0 && a.v < 0.15) { a.v = 0; a.acc = 0; }
    a.turn = ne && dEnd < 30 ? this.turnOf(e, ne) : 0;
    a.s += a.v * dt;
    let changed = false;
    while (a.s >= g.edges[a.e].len) {
      const cur = g.edges[a.e];
      if (a.nxt < 0) { a.alive = false; return; }
      a.s -= cur.len; a.e = a.nxt; a.seg = 0; a.free = false; a.wait = 0; changed = true;
      a.nxt = this.chooseNext(g, g.edges[a.e]);
    }
    const ce = g.edges[a.e];
    const [rx, ry] = this.place(a, ce);
    a.dz = this._z;
    if (changed) { a.ex = a.x - rx; a.ey = a.y - ry; }
    const k = Math.exp(-dt * 3);
    a.ex *= k; a.ey *= k;
    a.x = rx + a.ex; a.y = ry + a.ey;
    const th = Math.atan2(this._hy, this._hx);
    let dh = th - a.h;
    dh = Math.atan2(Math.sin(dh), Math.cos(dh));
    a.h += dh * (1 - Math.exp(-dt * 9));
    if (a.kind === 'bike') a.phase += a.v * 1.8 * dt;
    // despawn far away
    const dd = (a.x - px) ** 2 + (a.y - py) ** 2;
    if (dd > 280 * 280) a.alive = false;
  }

  private trySpawn(kind: 'car' | 'bike', px: number, py: number) {
    const g = kind === 'car' ? this.cars : this.bikes;
    if (!g || !g.total) return false;
    for (let tries = 0; tries < 10; tries++) {
      const r = Math.random() * g.total;
      let lo = 0, hi = g.wcum.length - 1;
      while (lo < hi) { const m = (lo + hi) >> 1; if (g.wcum[m] < r) lo = m + 1; else hi = m; }
      const e = g.edges[lo];
      if (e.len < 12) continue;
      const a: Agent = { kind, e: lo, s: 5 + Math.random() * (e.len - 10), v: 0, nxt: -1, x: 0, y: 0, h: 0, ex: 0, ey: 0, seg: 0, vmul: 1,
        len: 4.4, type: '', color: JACKETS[0], wait: 0, free: false, phase: Math.random() * 6.28, id: this.nextId++, alive: true, yielding: false, acc: 0, turn: 0, dz: NaN };
      const [x, y] = this.place(a, e);
      a.dz = this._z;
      const d = Math.hypot(x - px, y - py);
      if (d < 120 || d > 250) continue;
      let ok = true;
      for (const c of e.list) if (Math.abs(c.s - a.s) < 10) { ok = false; break; }
      if (!ok) continue;
      a.x = x; a.y = y; a.h = Math.atan2(this._hy, this._hx);
      if (kind === 'car') {
        const key = (Math.random() * 1e9) | 0, p = this.pick(key);
        if (!this.carMesh[p.type]) continue;
        a.type = p.type; a.color = p.color; a.len = this.carLen[p.type] || 4.4; a.vmul = 0.8 + Math.random() * 0.25;
      } else {
        a.color = JACKETS[Math.floor(Math.random() * JACKETS.length)]; a.len = 1.8; a.vmul = 0.9 + Math.random() * 0.4;
      }
      a.v = Math.min((e.v / 3.6) * a.vmul, 6);
      a.nxt = this.chooseNext(g, e);
      e.list.push(a);
      this.agents.push(a);
      if (kind === 'car') this.nCars++; else this.nBikes++;
      return true;
    }
    return false;
  }

  /** move2: set by main (tiles.colliders.circleAhead). */
  solidAhead: ((x: number, y: number, hx: number, hy: number, maxD: number, hw: number) => number) | null = null;
  private tick = 0;

  update(dt: number, px: number, py: number, avoid: { x: number; y: number; r: number }[]) {
    if (!this.cars || !this.bikes) return;
    this.tick++;
    dt = Math.min(dt, 0.05);
    for (const g of [this.cars, this.bikes]) for (const e of g.edges) e.list.length = 0;
    for (const a of this.agents) this.graph(a).edges[a.e].list.push(a);
    for (const a of this.agents) if (a.alive) this.step(a, this.graph(a), dt, avoid, px, py);
    // cull dead / over limit
    for (const kind of ['car', 'bike'] as const) {
      const max = kind === 'car' ? this._maxCars : this._maxBikes;
      let n = this.agents.filter((a) => a.kind === kind && a.alive).length;
      while (n > max) {
        let far: Agent | null = null, fd = -1;
        for (const a of this.agents) if (a.kind === kind && a.alive) { const d = (a.x - px) ** 2 + (a.y - py) ** 2; if (d > fd) { fd = d; far = a; } }
        if (!far) break;
        far.alive = false; n--;
      }
    }
    this.agents = this.agents.filter((a) => a.alive);
    this.nCars = this.agents.filter((a) => a.kind === 'car').length;
    this.nBikes = this.agents.length - this.nCars;
    // spawn
    this.spawnT -= dt;
    if (this.spawnT <= 0) {
      const hungry = this.nCars < this._maxCars * 0.6 || this.nBikes < this._maxBikes * 0.6;
      this.spawnT = hungry ? 0.02 : 0.3;
      const burst = hungry ? 4 : 1;
      for (let i = 0; i < burst; i++) {
        if (this.nCars < this._maxCars && this.trySpawn('car', px, py)) continue;
        if (this.nBikes < this._maxBikes) this.trySpawn('bike', px, py);
      }
    }
    this.render();
  }

  private render() {
    const cursor: Record<string, number> = {};
    let nb = 0;
    this.out = [];
    const M = this.tmpA, L = this.tmpB;
    for (const a of this.agents) {
      const y = Number.isNaN(a.dz) ? this.ground(a.x, a.y) - 0.12 : a.dz, th = a.h - Math.PI / 2, c = Math.cos(th), s = Math.sin(th);
      this.out.push({ x: a.x, y: a.y, heading: a.h, kind: a.kind, len: a.len, v: a.v, id: a.id, brake: a.acc < -1.3 || (a.yielding && a.v < 0.6), turn: a.turn, type: a.type, edge: a.e });
      if (a.kind === 'car') {
        const m = this.carMesh[a.type], i = cursor[a.type] ?? 0;
        if (!m || i >= CAP) continue;
        cursor[a.type] = i + 1;
        const arr = m.instanceMatrix.array as Float32Array, o = i * 16;
        arr[o] = c; arr[o + 1] = 0; arr[o + 2] = -s; arr[o + 3] = 0; arr[o + 4] = 0; arr[o + 5] = 1; arr[o + 6] = 0; arr[o + 7] = 0;
        arr[o + 8] = s; arr[o + 9] = 0; arr[o + 10] = c; arr[o + 11] = 0; arr[o + 12] = a.x; arr[o + 13] = y; arr[o + 14] = -a.y; arr[o + 15] = 1;
        m.setColorAt(i, a.color);
      } else if (nb < CAP) {
        M.makeRotationY(th).setPosition(a.x, y, -a.y);
        this.bikeMesh.setMatrixAt(nb, M);
        this.bikeMesh.setColorAt(nb, a.color);
        const ph = Math.sin(a.phase) * 0.5, base = M;
        L.makeRotationX(0.35 + ph).setPosition(-0.12, 1.0, 0.22);
        this.legL.setMatrixAt(nb, this.tmpC.copy(base).multiply(L));
        L.makeRotationX(0.35 - ph).setPosition(0.12, 1.0, 0.22);
        this.legR.setMatrixAt(nb, this.tmpC.copy(base).multiply(L));
        nb++;
      }
    }
    for (const [t, m] of Object.entries(this.carMesh)) {
      m.count = cursor[t] ?? 0;
      m.instanceMatrix.needsUpdate = true;
      if (m.instanceColor) m.instanceColor.needsUpdate = true;
    }
    for (const m of [this.bikeMesh, this.legL, this.legR]) { m.count = nb; m.instanceMatrix.needsUpdate = true; }
    if (this.bikeMesh.instanceColor) this.bikeMesh.instanceColor.needsUpdate = true;
  }
  private tmpC = new THREE.Matrix4();
}
