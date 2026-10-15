import * as THREE from 'three';
import type { Tiles } from '../engine/tiles';
import type { Rig } from './vehicle_model';

/**
 * Arcade-realistic car physics. Local metres (x east, y north), heading = compass angle (0 = north, clockwise,
 * forward = (sin h, cos h)). Longitudinal engine/brake model, steering limited by grip (turning circle grows with
 * speed), lateral slip that decays, sprung body (pitch/roll from acceleration and ground), 3 collision circles
 * against buildings and oriented boxes for traffic/trams/parked cars. Stars/police can read `speed` and `onImpact`.
 */
export interface DriveInput { throttle: number; steer: number; turbo: boolean }
/** Oriented box obstacle: centre, unit forward vector, half length/width. */
export interface Obb { x: number; y: number; fx: number; fy: number; hl: number; hw: number }

const ACC = 5.6, TURBO_ACC = 8.5, VMAX = 25, TURBO_VMAX = 33, VREV = 6, BRAKE = 10.5, ALAT = 9.5, GRIP = 9;
const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));

export class DriveCar {
  x: number; y: number; h: number; z = 0;
  vx = 0; vy = 0;
  /** signed speed along the car (m/s), lateral slip speed, front wheel angle (rad, + = right) */
  speed = 0; slip = 0; steer = 0; yawRate = 0;
  pitch = 0; roll = 0;
  private pitchV = 0; private rollV = 0; private zV = 0;
  wheelAngle = 0;
  braking = false; reversing = false;
  /** Brake light on while braking and while coasting down (no throttle, still rolling); held briefly so it does not flicker. */
  private brakeHold = 0;
  /** Smoothed engine state for audio/lights. */
  rpm = 0; gear = 1; throttle = 0;
  /** Latched indicator side (-1 left, 1 right) and its phase. */
  blink: -1 | 0 | 1 = 0;
  private blinkHold = 0; private blinkAge = 0; blinkPhase = 0;
  impact = 0; // strength of the last hit (decays), for camera shake
  onImpact: ((strength: number) => void) | null = null;
  readonly half: { l: number; w: number };
  private circles: number[] = [];
  readonly radius: number;
  private oldAcc = 0;

  constructor(private tiles: Tiles, readonly rig: Rig, readonly type: string, readonly color: THREE.Color,
    x: number, y: number, h: number, speed = 0) {
    this.x = x; this.y = y; this.h = h;
    this.z = tiles.groundAt(x, y, tiles.ground(x, y));
    this.speed = speed; this.vx = Math.sin(h) * speed; this.vy = Math.cos(h) * speed;
    this.half = { l: rig.length / 2, w: rig.width / 2 };
    this.radius = Math.min(0.95, this.half.w * 0.52);
    const r = this.radius, n = Math.max(3, Math.round(rig.length / (r * 1.7))), span = this.half.l - r;
    for (let i = 0; i < n; i++) this.circles.push(-span + (2 * span * i) / (n - 1));
  }

  /** Collision circles in world coordinates (also fed to Traffic so other cars brake for us). */
  circlesWorld(): { x: number; y: number; r: number }[] {
    const fx = Math.sin(this.h), fy = Math.cos(this.h);
    return this.circles.map((o) => ({ x: this.x + fx * o, y: this.y + fy * o, r: this.radius + 0.1 }));
  }

  /** Front-wheel angle limit: tight at walking pace, grip-limited when fast (turning circle grows with speed). */
  maxSteer(v: number) {
    const wb = this.rig.wheelbase, av = Math.abs(v);
    return Math.min(0.62, Math.atan((wb * ALAT) / Math.max(av * av, 1e-3)));
  }

  update(dt: number, inp: DriveInput, obstacles: Obb[] | null, nearParked: (x: number, y: number, r: number) => Obb[]) {
    const steps = Math.ceil(dt / 0.017);
    for (let i = 0; i < steps; i++) this.step(dt / steps, inp, obstacles, nearParked);
    this.impact *= Math.exp(-dt * 5);
    this.applyVisual(dt, inp);
  }

  private step(dt: number, inp: DriveInput, obstacles: Obb[] | null, nearParked: (x: number, y: number, r: number) => Obb[]) {
    const fx = Math.sin(this.h), fy = Math.cos(this.h);
    let vl = this.vx * fx + this.vy * fy;
    const vmax = inp.turbo ? TURBO_VMAX : VMAX, acc = inp.turbo ? TURBO_ACC : ACC;
    const t = inp.throttle;
    this.braking = false; this.reversing = false;
    let a = 0;
    if (t > 0.05) {
      if (vl < -0.4) { a = BRAKE * t; this.braking = true; }
      else a = acc * t * Math.max(0, 1 - Math.pow(Math.max(0, vl) / vmax, 1.6)) + (vl < 2 ? 0.8 * t : 0); // a bit of launch torque
    } else if (t < -0.05) {
      if (vl > 0.4) { a = -BRAKE * -t; this.braking = true; }
      else { a = -3.0 * -t * Math.max(0, 1 - Math.abs(vl) / VREV); this.reversing = true; }
    } else a = -Math.sign(vl) * Math.min(Math.abs(vl) / dt, 0.35 + 0.0015 * vl * vl); // engine braking + rolling resistance
    if (Math.abs(a) < 1e-6 && Math.abs(vl) < 0.05) vl = 0;
    // drag also above vmax (turbo ended)
    if (vl > vmax) a -= (vl - vmax) * 0.8;
    const vlNew = vl + a * dt;
    // coming to a stop from braking: do not flip sign through zero
    vl = (vl > 0 && vlNew < 0 && t <= 0.05 || vl < 0 && vlNew > 0 && t >= -0.05) ? 0 : vlNew;
    this.oldAcc += ((vlNew - this.speed) / dt - this.oldAcc) * Math.min(1, dt * 8);

    // steering: wheel angle follows the input at a finite rate (slower the faster we go)
    const lim = this.maxSteer(vl), target = clamp(inp.steer, -1, 1) * lim;
    const rate = (Math.abs(target) > Math.abs(this.steer) ? 3.4 : 5.2) / (1 + Math.abs(vl) * 0.04);
    this.steer += clamp(target - this.steer, -rate * dt, rate * dt);
    if (Math.abs(this.steer) > lim) this.steer = Math.sign(this.steer) * lim;
    const omega = (vl / this.rig.wheelbase) * Math.tan(this.steer);
    this.yawRate = omega;
    this.h += omega * dt;

    // keep the world velocity, split in the new frame; lateral part decays (grip), rest follows the car
    const nfx = Math.sin(this.h), nfy = Math.cos(this.h), rx = nfy, ry = -nfx;
    const along = this.vx * nfx + this.vy * nfy + (vl - (this.vx * fx + this.vy * fy));
    let lat = this.vx * rx + this.vy * ry;
    lat *= Math.exp(-(inp.turbo ? GRIP * 0.7 : GRIP) * dt);
    this.vx = nfx * along + rx * lat; this.vy = nfy * along + ry * lat;
    this.slip = lat;
    this.speed = along;

    const ox = this.x, oy = this.y;
    this.x += this.vx * dt; this.y += this.vy * dt;
    this.collide(obstacles, nearParked);
    if (!this.tiles.inPlay(this.x, this.y)) { this.x = ox; this.y = oy; this.vx *= -0.3; this.vy *= -0.3; this.speed *= -0.3; }

    // engine model for sound and lights: simple 5-speed gearbox
    const sp = Math.abs(this.speed), tops = [6, 11, 16, 22, 40];
    let g = 0; while (g < 4 && sp > tops[g]) g++;
    const lo = g ? tops[g - 1] * 0.72 : 0, rpmT = clamp(0.18 + 0.82 * (sp - lo) / (tops[g] - lo), 0.15, 1);
    this.gear = g + 1; this.rpm += (rpmT + Math.abs(t) * 0.12 - this.rpm) * Math.min(1, dt * 7);
    this.throttle = t;
    if (this.reversing) this.gear = 0;
  }

  private collide(obstacles: Obb[] | null, nearParked: (x: number, y: number, r: number) => Obb[]) {
    const r = this.radius;
    let hit = 0;
    for (let iter = 0; iter < 2; iter++) {
      let px = 0, py = 0, nx = 0, ny = 0;
      const fx = Math.sin(this.h), fy = Math.cos(this.h);
      for (const o of this.circles) {
        const cx = this.x + fx * o, cy = this.y + fy * o;
        const [qx, qy] = this.tiles.colliders.resolve(cx, cy, r);
        px += qx - cx; py += qy - cy;
      }
      const boxes = [...(obstacles ?? []), ...nearParked(this.x, this.y, this.half.l + 4)];
      for (const b of boxes) {
        for (const o of this.circles) {
          const cx = this.x + fx * o, cy = this.y + fy * o, dx = cx - b.x, dy = cy - b.y;
          const al = dx * b.fx + dy * b.fy, ac = -dx * b.fy + dy * b.fx;
          const qa = clamp(al, -b.hl, b.hl), qc = clamp(ac, -b.hw, b.hw);
          let ex = al - qa, ec = ac - qc, d = Math.hypot(ex, ec);
          if (d >= r) continue;
          if (d < 1e-4) { // centre inside the box: leave through the nearest face
            const dl = b.hl - Math.abs(al), dw = b.hw - Math.abs(ac);
            if (dl < dw) { ex = Math.sign(al || 1); ec = 0; d = -dl; } else { ex = 0; ec = Math.sign(ac || 1); d = -dw; }
          } else { ex /= d; ec /= d; }
          const push = r - d;
          px += (b.fx * ex - b.fy * ec) * push; py += (b.fy * ex + b.fx * ec) * push;
        }
      }
      const m = Math.hypot(px, py);
      if (m < 1e-4) break;
      const lim = Math.min(m, 1.2), k = lim / m;
      this.x += px * k; this.y += py * k;
      nx = px / m; ny = py / m;
      const vn = this.vx * nx + this.vy * ny;
      if (vn < 0) {
        hit = Math.max(hit, -vn);
        this.vx -= nx * vn * 1.18; this.vy -= ny * vn * 1.18; // small bounce
        this.vx *= 0.985; this.vy *= 0.985;
        // glancing blow nudges the heading away from the obstacle
        const rxx = Math.cos(this.h), ryy = -Math.sin(this.h), side = nx * rxx + ny * ryy;
        this.h += clamp(side * Math.min(-vn, 8) * 0.01, -0.03, 0.03) * Math.sign(this.speed || 1);
      }
    }
    if (hit > 0.3) {
      this.speed = this.vx * Math.sin(this.h) + this.vy * Math.cos(this.h);
      if (hit > 2) { this.impact = Math.max(this.impact, Math.min(1, hit / 12)); this.onImpact?.(hit); }
    }
  }

  private applyVisual(dt: number, inp: DriveInput) {
    const { wheelbase: wb, width } = this.rig, hw = width * 0.42;
    const fx = Math.sin(this.h), fy = Math.cos(this.h), rx = fy, ry = -fx;
    const gz = (lf: number, lr: number) => this.tiles.groundAt(this.x + fx * lf + rx * lr, this.y + fy * lf + ry * lr, this.z);
    const zfl = gz(wb / 2, -hw), zfr = gz(wb / 2, hw), zrl = gz(-wb / 2, -hw), zrr = gz(-wb / 2, hw);
    const zt = (zfl + zfr + zrl + zrr) / 4;
    const slopeP = Math.atan2((zfl + zfr - zrl - zrr) / 2, wb), slopeR = Math.atan2((zfr + zrr - zfl - zrl) / 2, hw * 2);
    // spring-damper body: ground height, pitch and roll (plus load transfer from acceleration and cornering)
    const aLat = this.speed * this.yawRate;
    const pT = slopeP + clamp(this.oldAcc * 0.0105, -0.07, 0.07), rT = slopeR + clamp(aLat * 0.0125, -0.09, 0.09);
    const spring = (x: number, v: number, tgt: number, k: number, c: number) => { v += (k * (tgt - x) - c * v) * dt; return [x + v * dt, v]; };
    [this.z, this.zV] = spring(this.z, this.zV, zt, 220, 22);
    if (Math.abs(this.z - zt) > 1.2) { this.z = zt; this.zV = 0; } // teleport/bridge safety
    [this.pitch, this.pitchV] = spring(this.pitch, this.pitchV, pT, 70, 8.5);
    [this.roll, this.rollV] = spring(this.roll, this.rollV, rT, 70, 8.5);
    this.wheelAngle -= (this.speed / this.rig.wheelR) * dt;
    // indicators: latched by a sustained strong steering input, cancelled when the wheel straightens
    const s = inp.steer;
    this.blinkAge += dt;
    if (this.blink === 0) {
      this.blinkHold = Math.abs(s) > 0.6 && Math.abs(this.speed) > 0.5 ? this.blinkHold + dt : 0;
      if (this.blinkHold > 0.5) { this.blink = s < 0 ? -1 : 1; this.blinkAge = 0; this.blinkHold = 0; }
    } else if (this.blinkAge > 1.5 && Math.abs(s) < 0.12) this.blink = 0;
    this.blinkPhase += dt;
    const coast = Math.abs(this.throttle) <= 0.05 && Math.abs(this.speed) > 0.3;
    this.brakeHold = this.braking || coast ? 0.3 : Math.max(0, this.brakeHold - dt);
    const g = this.rig.group;
    g.position.set(this.x, this.z, -this.y);
    g.rotation.set(this.pitch, -this.h, this.roll, 'YXZ');
    this.rig.setWheels(this.wheelAngle, -this.steer);
  }

  /** Update the lights (needs the day/night value). */
  lights(night: number) {
    this.rig.setLights({ brake: this.brakeHold > 0, reverse: this.reversing, night, blink: this.blink, blinkOn: Math.floor(this.blinkPhase * 3) % 2 === 0 });
  }
}
