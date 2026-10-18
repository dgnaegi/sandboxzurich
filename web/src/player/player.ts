import * as THREE from 'three';
import { actions, consumeLook } from '../input/actions';
import type { Tiles } from '../engine/tiles';
import type { Human } from '../world/humans';
import type { BikeSlot } from '../world/bikes';
import { BikeRig } from '../world/bikerig';
import { rideBones, ridePose, type RideBones } from '../world/ridepose';
import { driveStep, type DriveState } from './vehicle_player';
import type { DriveCar } from './drive';

// Mocap clips run at ~1.35 / 3.7 m/s (manifest clip_speed); Human.setSpeed scales playback by v / clip speed, so these stay slide-free.
const WALK = 1.55, RUN = 4.5, RADIUS = 0.35, ACCEL = 7, DECEL = 11;
const TURN_WALK = 9, TURN_RUN = 6; // max turn rate (rad/s) of the body while walking / running
const BIKE_MAX = 7.5, BIKE_SPRINT = 10.5; // top speeds; acceleration/steering/lean live in world/bikerig.ts

/** Third-person player: walks, or rides a bike. Movement relative to camera when walking, steering on the bike. */
export class Player {
  x: number; y: number;
  yaw = 0; // camera yaw, 0 = looking north
  pitch = 0.22;
  heading = 0;
  speed = 0;
  riding: BikeSlot | null = null;
  /** Seconds left of a fall after a hard bike crash (figure lies on the ground, no control); `onBikeCrash` leaves the bike behind. */
  fallT = 0;
  onBikeCrash: ((speed: number) => void) | null = null;
  /** Car the player is driving (see vehicle_player.ts); the player position follows the car. */
  driving: DriveCar | null = null;
  drive: DriveState = { stopPending: false, camDist: 9, shake: 0, fov: 60, hooks: null };
  /** Speed factor on the bike (e.g. 1.2 on cycle lanes). */
  boost = 1;
  readonly mesh = new THREE.Group();
  private camDist = 5.5;
  z = 0;
  /** The ridden bike (spinning wheels, cranks, lean); see world/bikerig.ts. */
  readonly rig = new BikeRig();
  lastLook = 0;
  /** Smoothed walking velocity (m/s, world x/y). */
  private vx = 0; private vy = 0;
  private lean = 0;
  private slideSide = 1;
  private bones: RideBones;

  constructor(x: number, y: number, readonly tiles: Tiles, readonly body: Human) {
    this.x = x; this.y = y;
    this.z = tiles.ground(x, y);
    this.mesh.add(body.root);
    this.mesh.add(this.rig.group);
    this.bones = rideBones(body.root);
  }

  teleport(x: number, y: number, yaw: number) {
    this.x = x; this.y = y; this.yaw = yaw; this.heading = yaw; this.speed = 0; this.vx = this.vy = 0;
    this.z = this.tiles.groundAt(x, y, this.z);
  }

  mount(slot: BikeSlot) {
    this.riding = slot;
    this.x = slot.x; this.y = slot.y; this.heading = slot.h; this.speed = 0; this.vx = this.vy = 0;
    this.rig.set(slot.type, slot.color);
  }

  /** Get off; returns where the bike was left. */
  dismount(): { x: number; y: number; z: number; h: number; color: THREE.Color } | null {
    if (!this.riding) return null;
    const left = { x: this.x, y: this.y, z: this.z, h: this.heading, color: this.riding.color };
    this.riding = null;
    this.rig.hide();
    // step off to the right
    const nx = this.x + Math.cos(this.heading) * 0.8, ny = this.y - Math.sin(this.heading) * 0.8;
    if (!this.tiles.colliders.inside(nx, ny)) { this.x = nx; this.y = ny; }
    this.speed = 0;
    return left;
  }

  update(dt: number, camera: THREE.PerspectiveCamera) {
    const look = consumeLook();
    if (look.yaw || look.pitch) this.lastLook = 0; else this.lastLook += dt;
    this.yaw += look.yaw;
    this.pitch = Math.min(1.2, Math.max(-0.25, this.pitch + look.pitch));
    const { x: mx, y: my } = actions.move;
    const ox = this.x, oy = this.y;
    if (this.driving) { driveStep(this, dt, camera, look); return; }
    if (this.fallT > 0) { // lying after a fall: no control for a moment
      this.fallT -= dt;
      const k = Math.min(1, this.fallT / 1.8), lie = k > 0.12 ? Math.min(1, (1.8 - this.fallT) * 6) : Math.max(0, k / 0.12);
      this.body.root.rotation.x = -1.45 * lie; this.body.root.position.set(0, 0.18 * lie, 0);
      this.body.setSpeed(0); this.body.mixer.update(dt);
      this.vx = this.vy = 0; this.speed = 0;
      const wob = this.fallT > 1.5 ? (Math.random() - 0.5) * 0.12 * (this.fallT - 1.5) / 0.3 : 0;
      this.mesh.position.set(this.x, this.z, -this.y); this.mesh.rotation.z = wob;
      camera.lookAt(this.x, this.z + 1, -this.y);
      return;
    }

    if (this.riding) {
      const max = (actions.run ? BIKE_SPRINT : BIKE_MAX) * this.boost;
      const r = this.rig.dynamics(dt, this.speed, mx, my, max);  // power-limited, soft start, smoothed steering, lean
      this.speed = r.speed;
      if (Math.abs(this.speed) > 0.3) this.heading += r.turn;
      const nx = this.x + Math.sin(this.heading) * this.speed * dt, ny = this.y + Math.cos(this.heading) * this.speed * dt;
      [this.x, this.y] = this.tiles.resolveSolid(nx, ny, 0.45, this.z);
      const hitSolid = Math.hypot(this.x - nx, this.y - ny) > 0.02;
      const [rx, ry] = this.tiles.bridges.railPush(this.x, this.y, this.z, 0.45);   // deck railing: slides along it, no fall
      if (rx !== this.x || ry !== this.y) { this.x = rx; this.y = ry; this.speed *= 0.97; }
      if (hitSolid) { // bumped into something: head-on hard hit = fall off; glancing (move2) = slide along it, steer away a little
        const px = this.x - nx, py = this.y - ny, pl = Math.hypot(px, py) || 1;
        const vn = Math.max(0, -(px / pl * Math.sin(this.heading) + py / pl * Math.cos(this.heading))) * Math.abs(this.speed);   // speed into the obstacle
        if (vn > 4.5 && this.speed > 5.5) { const sp = this.speed; this.fallT = 1.8; this.onBikeCrash?.(sp); this.speed = 0; }
        else {
          const [qx, qy] = this.tiles.colliders.resolveCircles(nx, ny, 0.45), thin = Math.hypot(qx - nx, qy - ny) > 1e-3;   // pole/sign (not a wall)?
          const frac = vn / Math.max(1, Math.abs(this.speed));
          this.speed *= thin ? 1 - Math.min(0.12, frac * 0.15 + 0.004) : 1 - Math.min(0.5, frac * 0.5 + 0.004);
          const side = Math.sin(this.heading) * py - Math.cos(this.heading) * px;   // which side the push came from
          this.heading -= Math.sign(side || 1) * (thin ? 2.4 * Math.max(frac, 0.25) : Math.min(0.4, vn * 0.05) * Math.min(1, dt * 20)) * (thin ? dt : 1);   // steer round the post
        }
      }
      // camera swings behind the bike unless the player is looking around
      if (this.lastLook > 1.2) { let d = this.heading - this.yaw; d = Math.atan2(Math.sin(d), Math.cos(d)); this.yaw += d * Math.min(1, dt * 2.5); }
    } else {
      const amount = Math.min(1, Math.hypot(mx, my));
      let tx = 0, ty = 0, turnRate = 0;
      if (amount > 0.05) {
        const s = Math.sin(this.yaw), c = Math.cos(this.yaw);
        const dx = my * s + mx * c, dy = my * c - mx * s, l = Math.hypot(dx, dy);
        let v = (actions.run ? RUN : WALK) * amount;
        tx = (dx / l) * v; ty = (dy / l) * v;
        let d = Math.atan2(dx, dy) - this.heading;
        d = Math.atan2(Math.sin(d), Math.cos(d));
        const maxTurn = (TURN_WALK + (TURN_RUN - TURN_WALK) * Math.min(1, this.speed / RUN)) * dt;   // limited angular speed, no snapping
        const step = Math.max(-maxTurn, Math.min(maxTurn, d * Math.min(1, dt * 12)));
        this.heading += step;
        turnRate = dt > 0 ? step / dt : 0;
        // move2: sharp turns cost speed (a runner cannot turn on a coin at full pace)
        const cut = Math.max(0.35, Math.cos(Math.min(Math.abs(d), 1.4)));
        tx *= cut; ty *= cut;
      }
      // ease into and out of steps instead of jumping to full speed
      const k = Math.min(1, dt * (tx || ty ? ACCEL : DECEL));
      this.vx += (tx - this.vx) * k; this.vy += (ty - this.vy) * k;
      if (Math.hypot(this.vx, this.vy) > 0.01) {
        const n = Math.max(1, Math.ceil(Math.hypot(this.vx, this.vy) * dt / 0.25));   // move2: substeps, no tunnelling/jerks on frame spikes
        for (let i = 0; i < n; i++) {
          const wx = this.x + (this.vx * dt) / n, wy = this.y + (this.vy * dt) / n;
          [this.x, this.y] = this.tiles.resolveSolid(wx, wy, RADIUS, this.z);
          // move2: walking straight into a pole/sign: glide round it (tangent to the contact, on the side we are already leaning to) instead of standing still
          const [cx, cy] = this.tiles.colliders.resolveCircles(wx, wy, RADIUS), pd = Math.hypot(cx - wx, cy - wy);
          if (pd > 1e-4) {
            const nx = (cx - wx) / pd, ny = (cy - wy) / pd, sp = Math.hypot(this.vx, this.vy);
            if (-(this.vx * nx + this.vy * ny) > 0.6 * sp) {
              const tdot = -ny * this.vx + nx * this.vy, sg = tdot !== 0 ? Math.sign(tdot) : (this.slideSide ||= 1);
              this.slideSide = sg;
              [this.x, this.y] = this.tiles.resolveSolid(this.x - ny * sg * sp * 0.9 * dt / n, this.y + nx * sg * sp * 0.9 * dt / n, RADIUS, this.z);
            }
          }
          [this.x, this.y] = this.tiles.bridges.railPush(this.x, this.y, this.z, RADIUS);
        }
        const mvx = dt > 0 ? (this.x - ox) / dt : this.vx, mvy = dt > 0 ? (this.y - oy) / dt : this.vy; // keep only what walls allowed
        this.vx = mvx; this.vy = mvy;
      }
      const v = dt > 0 ? Math.hypot(this.x - ox, this.y - oy) / dt : this.speed;
      this.speed += (v - this.speed) * Math.min(1, dt * 10);
      // lean into curves when running (rolls the body about its forward axis)
      const wantLean = -Math.max(-0.22, Math.min(0.22, turnRate * Math.max(0, this.speed - 2) * 0.03));
      this.lean += (wantLean - this.lean) * Math.min(1, dt * 8);
    }
    if (!this.tiles.inPlay(this.x, this.y)) { this.x = ox; this.y = oy; this.speed *= 0.3; } // fence: end of the playable map

    // animation: walking/running, or pedalling (walk clip, raised onto the saddle)
    if (this.riding) {
      this.body.setSpeed(0); // idle base pose, legs/arms overridden below
      this.body.root.position.set(0, 0.12, 0.1);
      this.body.root.rotation.x = 0;
    } else {
      this.body.setSpeed(this.speed);
      this.body.root.position.set(0, 0, 0);
      this.body.root.rotation.x = 0;
    }
    this.body.mixer.update(dt);
    if (this.riding) { this.rig.animate(dt, this.speed, my > 0.1); ridePose(this.bones, this.body.root, this.rig.crank, this.riding.type, this.rig.geo); }
    this.z += (this.tiles.groundAt(this.x, this.y, this.z) - this.z) * Math.min(1, dt * 15);
    this.mesh.position.set(this.x, this.z, -this.y);
    this.mesh.rotation.y = -this.heading;
    this.mesh.rotation.z = this.riding ? this.rig.lean : this.lean;

    // camera: behind, pulled in front of walls
    const want = this.riding ? 6.5 : 5.5, cp0 = Math.cos(this.pitch) * want;
    // sweep a ~0.5 m wide corridor (centre + both sides) instead of a single ray, then keep a wall margin at the end point
    const bx = this.x - Math.sin(this.yaw) * cp0, by = this.y - Math.cos(this.yaw) * cp0, sx = Math.cos(this.yaw) * 0.5, sy = -Math.sin(this.yaw) * 0.5;
    const col = this.tiles.colliders;
    const free = Math.min(col.freeFraction(this.x, this.y, bx, by), col.freeFraction(this.x + sx, this.y + sy, bx + sx, by + sy), col.freeFraction(this.x - sx, this.y - sy, bx - sx, by - sy));
    this.camDist += (Math.max(1.0, want * free - 0.5) - this.camDist) * Math.min(1, dt * (free < 1 ? 20 : 4));
    const target = new THREE.Vector3(this.x, this.z + 1.55, -this.y);
    const cp = Math.cos(this.pitch);
    camera.position.set(target.x - Math.sin(this.yaw) * cp * this.camDist, target.y + Math.sin(this.pitch) * this.camDist,
      target.z + Math.cos(this.yaw) * cp * this.camDist);
    const [cx, cy] = col.resolve(camera.position.x, -camera.position.z, 0.55); // camera sphere vs footprints: never inside, >= 0.55 m from walls
    camera.position.x = cx; camera.position.z = -cy;
    // hb3: below the terrain (underground deck) the camera stays between that floor and the ceiling instead of being lifted above the terrain
    if (this.z < this.tiles.ground(this.x, this.y) - 1.0) camera.position.y = Math.min(Math.max(camera.position.y, this.z + 0.7), this.z + 2.9);
    else camera.position.y = Math.max(camera.position.y, this.tiles.ground(camera.position.x, -camera.position.z) + 0.4);
    camera.lookAt(target);
  }
}
