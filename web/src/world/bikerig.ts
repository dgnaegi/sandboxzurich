import * as THREE from 'three';
import { bikeGeo, bikeModelMaterial, BIKE_RIG } from './bikes';

/**
 * The ridden bike: the static model split by position into frame, two spinning wheels and the crank set
 * (axle positions from pipeline/bikes manifest `rig`), plus the riding dynamics (power-limited acceleration,
 * smoothed steering, lean into curves from yaw rate and speed, freewheeling while coasting).
 */
const G = 9.81;
const BIKE_ACC = 3.2, BIKE_BRAKE = 7;

type Rig = { rear: [number, number]; front: [number, number]; bb: [number, number] };

/** Copy the triangles whose three vertices satisfy `pred` (and the rest) into two non-indexed geometries. */
function split(g: THREE.BufferGeometry, pred: (x: number, y: number, z: number) => boolean) {
  const src = g.index ? g.toNonIndexed() : g, pos = src.getAttribute('position');
  const take: number[] = [], rest: number[] = [];
  for (let t = 0; t < pos.count; t += 3) {
    let all = true;
    for (let k = 0; k < 3 && all; k++) all = pred(pos.getX(t + k), pos.getY(t + k), pos.getZ(t + k));
    (all ? take : rest).push(t);
  }
  const build = (tris: number[]) => {
    const out = new THREE.BufferGeometry();
    for (const [name, a] of Object.entries(src.attributes)) {
      const arr = new Float32Array(tris.length * 3 * a.itemSize);
      tris.forEach((t, i) => { for (let k = 0; k < 3; k++) for (let c = 0; c < a.itemSize; c++) arr[(i * 3 + k) * a.itemSize + c] = a.getComponent(t + k, c); });
      out.setAttribute(name, new THREE.BufferAttribute(arr, a.itemSize));
    }
    return out;
  };
  return [build(take), build(rest)] as const;
}

const cache = new Map<string, { frame: THREE.BufferGeometry; rear: THREE.BufferGeometry; front: THREE.BufferGeometry; crank: THREE.BufferGeometry; rig: Rig }>();
function parts(type: string) {
  let c = cache.get(type);
  if (c) return c;
  const base = bikeGeo(type), rig = BIKE_RIG[type] as Rig | undefined;
  if (!rig) return null;
  const wheel = ([R, z]: [number, number]) => (x: number, y: number, zz: number) => Math.abs(x) < 0.03 && Math.hypot(y - R, zz - z) <= R + 0.002;
  const [rear, r1] = split(base, wheel(rig.rear));
  const [front, r2] = split(r1, wheel(rig.front));
  const [crank, frame] = split(r2, (x, y, z) => Math.abs(x) > 0.052 && Math.hypot(y - rig.bb[0], z - rig.bb[1]) <= 0.23);
  rear.translate(0, -rig.rear[0], -rig.rear[1]); front.translate(0, -rig.front[0], -rig.front[1]); crank.translate(0, -rig.bb[0], -rig.bb[1]);
  c = { frame, rear, front, crank, rig };
  cache.set(type, c);
  return c;
}

export class BikeRig {
  readonly group = new THREE.Group();
  geo: { bars: [number, number, number]; saddle: [number, number]; bb: [number, number]; crankR: number } | null = null;
  steer = 0; lean = 0; wheel = 0; crank = 0;
  private leanV = 0;
  private meshes: THREE.InstancedMesh[] = [];
  private pivots: THREE.Object3D[] = [];

  constructor() { this.group.visible = false; }

  set(type: string, color: THREE.Color) {
    this.group.clear();
    this.meshes = []; this.pivots = [];
    const p = parts(type.replace('_lean', ''));
    const rg = p?.rig as (Rig & { saddle?: [number, number] }) | undefined;
    this.geo = rg && rg.saddle ? { bars: [0, 0, 0], saddle: rg.saddle, bb: rg.bb, crankR: 0.17 } : null;
    const mk = (g: THREE.BufferGeometry) => {
      const m = new THREE.InstancedMesh(g, bikeModelMaterial, 1);
      m.setMatrixAt(0, new THREE.Matrix4()); m.setColorAt(0, color);
      m.castShadow = true; m.frustumCulled = false;
      this.meshes.push(m); return m;
    };
    if (!p) { this.group.add(mk(bikeGeo(type.replace('_lean', '')))); return; }
    this.group.add(mk(p.frame));
    for (const [g, yz] of [[p.rear, [p.rig.rear[0], p.rig.rear[1]]], [p.front, [p.rig.front[0], p.rig.front[1]]], [p.crank, p.rig.bb]] as const) {
      const pv = new THREE.Group(); pv.position.set(0, yz[0], yz[1]); pv.add(mk(g)); this.group.add(pv); this.pivots.push(pv);
    }
    this.steer = this.lean = this.leanV = 0;
    this.group.visible = true;
  }

  hide() { this.group.visible = false; }

  /** One step of riding physics: new speed and heading change. `my` = throttle/brake (-1..1), `mx` = steering input. */
  dynamics(dt: number, speed: number, mx: number, my: number, max: number): { speed: number; turn: number } {
    const f = Math.min(1, Math.max(0, speed) / Math.max(max, 1));
    if (my > 0.1) {
      const acc = BIKE_ACC * (0.5 + 0.5 * Math.min(1, speed / 2)) * (1 - 0.55 * f);  // soft start from standstill, less push when fast
      speed = Math.min(max * my, speed + acc * dt);
      if (speed > max * my) speed = Math.max(max * my, speed - 2 * dt);
    } else if (my < -0.1) speed = Math.max(-1.5, speed - BIKE_BRAKE * dt * (speed > 0 ? 1 : 0.4));
    else speed = Math.max(0, speed - (0.45 + 0.04 * speed + 0.012 * speed * speed) * dt); // coasting: rolling + air resistance
    this.steer += (mx - this.steer) * Math.min(1, dt * 7);
    const v = Math.abs(speed);
    let w = this.steer * (2.1 - Math.min(v, 8) * 0.11) * Math.min(1, v / 1.8);
    w = Math.max(-6.5 / Math.max(v, 1), Math.min(6.5 / Math.max(v, 1), w)); // lateral grip limit
    const turn = w * dt * Math.sign(speed || 1);
    // lean: centripetal acceleration v*w over g, spring-smoothed (positive rotation.z = leaning left)
    const target = -Math.atan((speed * w) / G) * 0.85;
    this.leanV += (90 * (target - this.lean) - 13 * this.leanV) * dt;
    this.lean += this.leanV * dt;
    return { speed, turn };
  }

  /** Wheels follow the ground speed; cranks turn with the rider's cadence (stop while freewheeling). */
  animate(dt: number, speed: number, pedalling: boolean) {
    const R = this.pivots[0] ? (this.pivots[0].position.y || 0.34) : 0.34;
    this.wheel -= (speed / R) * dt;
    if (pedalling && speed > 0.3) this.crank += (4.5 + 3.6 * Math.min(1, speed / 9)) * dt;
    if (this.pivots.length >= 3) {
      this.pivots[0].rotation.x = this.wheel; this.pivots[1].rotation.x = this.wheel; this.pivots[2].rotation.x = -this.crank;
    }
  }
}
