import * as THREE from 'three';
import type { Transit, Driven } from '../world/transit';
import type { DriveInput, Obb, Crash } from './drive';

/**
 * Tram driven by the player: runs on its line (rails), the player only controls speed. State = arc position `s`
 * of the front tip along the line and speed `v`. Quacks like DriveCar for camera, HUD, audio and traffic.
 * Max 14 m/s (50 km/h in town), accel 1.2, service brake 1.5, emergency brake (Shift) 2.8, reverse <= 3 m/s.
 */
const VMAX = 14, VREV = 3, ACC = 1.2, BRAKE = 1.5, EMERGENCY = 2.8, COAST = 0.15, LAT = 1.3;
const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));

export class TramCar {
  readonly isTram = true;
  readonly type = 'tram';
  readonly color = new THREE.Color(0xffffff);
  readonly rig = null;
  x = 0; y = 0; z = 0; h = 0; vx = 0; vy = 0;
  speed = 0; slip = 0; steer = 0; yawRate = 0; pitch = 0; roll = 0; wheelAngle = 0;
  braking = false; reversing = false; rpm = 0; gear = 1; throttle = 0;
  damage = 0; dead = false; impact = 0;
  onImpact: ((strength: number) => void) | null = null;
  onCrash: ((c: Crash) => void) | null = null;
  readonly half = { l: 5.5, w: 1.2 };
  cam = { dist: 15, h: 2.4 };
  /** Front-tip arc position, speed is `speed`. */
  s: number;
  doorsOpen = false;
  /** Stop the tram is at / approaching and the distance to its platform centre along the line (m). */
  stopName = ''; stopDist = 0;
  minS: number;
  private hitCool = 0;
  readonly vlen: number;
  private c0: number;
  private pose = [0, 0, 0, 0];
  private pool: { x: number; y: number; r: number }[] = [];
  private out: { x: number; y: number; r: number }[] = [];

  constructor(private transit: Transit, readonly li: number, readonly key: string, specName: string, s: number, v: number) {
    const spec = transit.spec(specName)!;
    this.vlen = spec.length; this.c0 = spec.sequence[0].z_center_from_front;
    this.s = s; this.speed = clamp(v, -VREV, VMAX);
    this.minS = Math.min(this.vlen, s);
    const n = Math.ceil(this.vlen / 3.5);
    for (let i = 0; i < n; i++) this.pool.push({ x: 0, y: 0, r: 1.45 });
    const d: Driven = { li, key, s, spec: specName, doors: false, active: true };
    transit.driven = d;
    this.place();
  }

  get driven(): Driven { return this.transit.driven!; }

  /** Pose of the front module (the player/camera follow it). */
  private place() {
    this.transit.poseAt(this.li, this.s - this.c0, this.pose);
    [this.x, this.y, this.z, this.h] = this.pose as [number, number, number, number];
    const d = this.transit.driven;
    if (d && d.key === this.key) d.s = this.s;
  }

  circlesWorld() {
    this.out.length = 0;
    for (let i = 0; i < this.pool.length; i++) {
      this.transit.poseAt(this.li, this.s - 1.5 - i * 3.5, this.pose);
      const c = this.pool[i]; c.x = this.pose[0]; c.y = this.pose[1];
      this.out.push(c);
    }
    return this.out;
  }

  lights(_night: number) { void _night; }

  /** Distance (m) from the tip of the tram (front when `fwd`, else tail) to the nearest obstacle in the rail corridor. */
  private gapAhead(fwd: boolean, obs: Obb[] | null, parked: (x: number, y: number, r: number) => Obb[]): number {
    const sRef = fwd ? this.s : this.s - this.vlen, p = this.pose;
    this.transit.poseAt(this.li, sRef, p);
    const px = p[0], py = p[1], dir = fwd ? 1 : -1, fx = Math.sin(p[3]) * dir, fy = Math.cos(p[3]) * dir;
    let gap = Infinity;
    const test = (b: Obb) => {
      const dx = b.x - px, dy = b.y - py, reach = b.hl + b.hw + 30;
      if (dx * dx + dy * dy > reach * reach) return;
      let amin = Infinity, amax = -Infinity, lmin = Infinity, lmax = -Infinity;
      for (let i = 0; i < 4; i++) {
        const sl = i & 1 ? 1 : -1, sw = i & 2 ? 1 : -1;
        const cx = dx + b.fx * b.hl * sl - b.fy * b.hw * sw, cy = dy + b.fy * b.hl * sl + b.fx * b.hw * sw;
        const a = cx * fx + cy * fy, l = -cx * fy + cy * fx;
        amin = Math.min(amin, a); amax = Math.max(amax, a); lmin = Math.min(lmin, l); lmax = Math.max(lmax, l);
      }
      if (lmax < -LAT || lmin > LAT || amax < -0.3) return;
      gap = Math.min(gap, Math.max(0, amin));
    };
    if (obs) for (const b of obs) test(b);
    for (const b of parked(px + fx * 6, py + fy * 6, 12)) test(b);
    return gap;
  }

  update(dt: number, inp: DriveInput, obstacles: Obb[] | null, parked: (x: number, y: number, r: number) => Obb[]) {
    const L = this.transit.line(this.li), t = inp.throttle;
    let v = this.speed, a = 0;
    this.braking = false; this.reversing = false;
    if (inp.turbo && Math.abs(v) > 0.05) { a = -Math.sign(v) * EMERGENCY; this.braking = true; }
    else if (t > 0.05) { if (v < -0.1) { a = BRAKE * 1.5 * t; this.braking = true; } else a = ACC * t * Math.max(0, 1 - (v / VMAX) ** 2) + (v < 1 ? 0.3 * t : 0); }
    else if (t < -0.05) {
      if (v > 0.1) { a = -BRAKE * -t; this.braking = true; } else { a = -0.9 * -t * Math.max(0, 1 - Math.abs(v) / VREV); this.reversing = true; }
    } else a = -Math.sign(v) * Math.min(Math.abs(v) / Math.max(dt, 1e-3), COAST);
    const vn = v + a * dt;
    v = (v > 0 && vn < 0 && !(t < -0.05)) || (v < 0 && vn > 0 && !(t > 0.05)) ? 0 : vn;
    v = clamp(v, -VREV, VMAX);
    // soft stop at the ends of the line (the speed allowed shrinks with the distance left)
    const room = v >= 0 ? L.len - this.s : this.s - this.minS, lim = Math.sqrt(2 * BRAKE * Math.max(0, room));
    if (Math.abs(v) > lim) v = Math.sign(v) * lim;
    // obstacles in the rail corridor: stop hard
    this.hitCool -= dt;
    let ds = v * dt;
    const moving = Math.abs(v) > 0.01, pushing = Math.abs(t) > 0.05;
    if (moving || pushing) {
      const gap = this.gapAhead(moving ? v > 0 : t > 0, obstacles, parked);
      if (gap < Math.abs(ds) + 0.35) {
        const sp = Math.abs(v);
        if (sp > 0.8 && this.hitCool <= 0) {
          this.hitCool = 0.5; this.impact = Math.max(this.impact, Math.min(1, sp / 10));
          this.onImpact?.(Math.min(14, sp * 1.1));
        }
        v = 0; ds = 0;
      }
    }
    this.speed = v; this.vx = Math.sin(this.h) * v; this.vy = Math.cos(this.h) * v;
    this.s = clamp(this.s + ds, this.minS, L.len);
    this.impact *= Math.exp(-dt * 5);
    this.throttle = t; this.slip = inp.turbo && Math.abs(v) > 2 ? 4 : 0; // emergency brake squeals
    this.rpm += (clamp(0.12 + 0.3 * Math.abs(v) / VMAX, 0, 1) - this.rpm) * Math.min(1, dt * 4);
    this.wheelAngle -= v * dt;
    this.place();
    this.updateStop(L);
    this.driven.doors = this.doorsOpen = Math.abs(v) < 0.3 && Math.abs(this.stopDist) < 15 && this.stopName !== '';
  }

  /** Nearest stop of the line (platform centre at the tram's centre) and signed distance (+ = still ahead). */
  private updateStop(L: ReturnType<Transit['line']>) {
    const mid = this.s - this.vlen / 2, fwd = this.speed >= 0;
    let best = Infinity, name = '';
    for (const st of L.stops) {
      const d = st.s - mid;
      if (fwd ? d > -15 && d < best : d < 15 && (best === Infinity || d > best)) { best = d; name = st.name; }
    }
    this.stopName = best === Infinity ? '' : name; this.stopDist = best === Infinity ? 0 : best;
  }
}
