import * as THREE from 'three';
import { scooterMat, scooterParts, BAR_HALF, BAR_Y, DECK_Y, FORK_Z, STEM_Z, WHEEL_R, WHEEL_Z } from './scooters';
import { aim, ik, posIn, type RideBones } from './ridepose';

/** Swiss limit for e-scooters (Kleinmotorfahrzeug): 20 km/h. */
export const SCOOTER_MAX = 5.6;
const ACC = 4.2, BRAKE = 6.5, G = 9.81;

/** The ridden scooter: frame, steering assembly (stem, bar, front wheel turns with the bar) and two spinning wheels; plus the riding dynamics. */
export class ScooterRig {
  readonly group = new THREE.Group();
  steer = 0; lean = 0; wheel = 0;
  private leanV = 0;
  private front = new THREE.Group();
  private spin: THREE.Object3D[] = [];
  constructor() {
    const P = scooterParts();
    const mk = (g: THREE.BufferGeometry) => { const m = new THREE.InstancedMesh(g, scooterMat, 1); m.setMatrixAt(0, new THREE.Matrix4()); m.castShadow = true; m.frustumCulled = false; this.meshes.push(m); return m; };
    this.group.add(mk(P.frame));
    this.front.position.set(0, 0, STEM_Z);
    const steer = mk(P.steer); steer.position.set(0, 0, -STEM_Z);
    const fw = new THREE.Group(); fw.position.set(0, WHEEL_R, FORK_Z - STEM_Z); fw.add(mk(P.wheel)); this.spin.push(fw);
    this.front.add(steer, fw);
    const rw = new THREE.Group(); rw.position.set(0, WHEEL_R, WHEEL_Z); rw.add(mk(P.wheel)); this.spin.push(rw);
    this.group.add(this.front, rw);
    this.group.visible = false;
  }
  private meshes: THREE.InstancedMesh[] = [];

  set(color: THREE.Color) {
    for (const m of this.meshes) m.setColorAt(0, color);
    for (const m of this.meshes) if (m.instanceColor) m.instanceColor.needsUpdate = true;
    this.steer = this.lean = this.leanV = 0;
    this.group.visible = true;
  }
  hide() { this.group.visible = false; }

  /** One physics step: quick electric acceleration up to `max`, braking, coasting, smoothed steering and lean. */
  dynamics(dt: number, speed: number, mx: number, my: number, max = SCOOTER_MAX): { speed: number; turn: number } {
    if (my > 0.1) speed = Math.min(max * my, speed + ACC * dt * (1 - 0.35 * Math.max(0, speed) / max));
    else if (my < -0.1) speed = Math.max(-1.0, speed - BRAKE * dt * (speed > 0 ? 1 : 0.4));
    else speed = Math.max(0, speed - (0.6 + 0.05 * speed) * dt);
    if (speed > max) speed = Math.max(max, speed - 3 * dt);
    this.steer += (mx - this.steer) * Math.min(1, dt * 8);
    const v = Math.abs(speed);
    let w = this.steer * (2.4 - Math.min(v, 6) * 0.15) * Math.min(1, v / 1.5);
    w = Math.max(-5.5 / Math.max(v, 1), Math.min(5.5 / Math.max(v, 1), w));
    const turn = w * dt * Math.sign(speed || 1);
    const target = -Math.atan((speed * w) / G) * 0.9;
    this.leanV += (90 * (target - this.lean) - 13 * this.leanV) * dt;
    this.lean += this.leanV * dt;
    return { speed, turn };
  }

  animate(dt: number, speed: number) {
    this.wheel -= (speed / WHEEL_R) * dt;
    for (const w of this.spin) w.rotation.x = this.wheel;
    this.front.rotation.y = -this.steer * 0.35;
  }

  /** Standing pose on the deck (after mixer.update): feet on the deck, slightly bent knees, hands on the grips. */
  pose(b: RideBones, root: THREE.Object3D) {
    if (!b.pelvis || !b.thigh_l || !b.thigh_r || !b.calf_l || !b.calf_r || !b.foot_l || !b.foot_r || !b.spine_01) return;
    root.rotation.set(0, 0, 0); root.updateMatrixWorld(true);
    const lean = (deg: number) => new THREE.Vector3(0, Math.cos(THREE.MathUtils.degToRad(deg)), -Math.sin(THREE.MathUtils.degToRad(deg)));
    aim(root, b.pelvis, lean(6));
    for (const n of ['spine_01', 'spine_02', 'spine_03'] as const) if (b[n]) aim(root, b[n]!, lean(9));
    if (b.neck_01) aim(root, b.neck_01, lean(0));
    const pel = posIn(root, b.pelvis, new THREE.Vector3());
    const top = DECK_Y + 0.085;
    root.position.set(-pel.x, top + 0.8 - pel.y, 0.2 - pel.z);   // pelvis ~0.8 m above the soles: knees slightly bent
    root.updateMatrixWorld(true);
    const toRoot = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z).sub(root.position);
    for (const side of [1, -1]) {   // right foot behind, left foot in front
      const s = side > 0 ? 'r' : 'l', z = side > 0 ? 0.3 : 0.02;
      ik(root, b[`thigh_${s}`]!, b[`calf_${s}`]!, b[`foot_${s}`]!, toRoot(side * 0.07, top, z), new THREE.Vector3(side * 0.1, 0.2, -1));
      aim(root, b[`foot_${s}`]!, new THREE.Vector3(0, -0.2, -1));
    }
    if (b.upperarm_l && b.upperarm_r && b.lowerarm_l && b.lowerarm_r && b.hand_l && b.hand_r) {
      const a = -this.steer * 0.35, ca = Math.cos(a), sa = Math.sin(a);
      for (const side of [1, -1]) {
        const s = side > 0 ? 'r' : 'l', gx = side * (BAR_HALF - 0.04);
        ik(root, b[`upperarm_${s}`]!, b[`lowerarm_${s}`]!, b[`hand_${s}`]!, toRoot(gx * ca, BAR_Y, STEM_Z - gx * sa), new THREE.Vector3(side * 0.6, -0.5, 0.35));
      }
    }
  }
}
