import * as THREE from 'three';

/**
 * Seated cycling pose on top of the idle clip (call after mixer.update). Absolute, not additive: bones are aimed
 * in world-of-the-character space (their Y axis runs along the bone), so it works for whatever rest/idle pose the
 * skeleton has. Pelvis sits on the saddle, spine leans forward, hands go to the bars and the legs follow the real
 * pedal positions of the crank (two-bone IK, knees point forward). Character space: x right, y up, front = -z.
 */
const NAMES = ['pelvis', 'spine_01', 'spine_02', 'spine_03', 'neck_01', 'thigh_l', 'thigh_r', 'calf_l', 'calf_r', 'foot_l', 'foot_r',
  'upperarm_l', 'upperarm_r', 'lowerarm_l', 'lowerarm_r', 'hand_l', 'hand_r'] as const;
export type RideBones = Partial<Record<(typeof NAMES)[number], THREE.Object3D>>;

export function rideBones(root: THREE.Object3D): RideBones {
  const b: RideBones = {};
  for (const n of NAMES) b[n] = root.getObjectByName(n);
  return b;
}

/** Per bike type: handlebar grip position (u forward, h height, half width), saddle seat point (h, z in bike space) and crank axis. */
export interface RideGeo { bars: [number, number, number]; saddle: [number, number]; bb: [number, number]; crankR: number }
export const BARS: Record<string, [number, number, number]> = {
  city: [0.31, 0.97, 0.29], kidseat: [0.31, 0.97, 0.29], rental: [0.28, 0.96, 0.27], trekking: [0.36, 0.95, 0.30], ebike: [0.35, 0.96, 0.30],
  road: [0.45, 0.82, 0.20], mtb: [0.37, 0.91, 0.34], cargo: [-0.30, 1.0, 0.31],
};

const sp = new THREE.Vector3(), ss = new THREE.Vector3(), UP = new THREE.Vector3(0, 1, 0), v1 = new THREE.Vector3(), v2 = new THREE.Vector3();
const q1 = new THREE.Quaternion(), q2 = new THREE.Quaternion(), q3 = new THREE.Quaternion(), qs = new THREE.Quaternion(), inv = new THREE.Matrix4();

/** Position / orientation of a bone relative to the character root. */
export function posIn(root: THREE.Object3D, o: THREE.Object3D, out: THREE.Vector3) { return out.setFromMatrixPosition(o.matrixWorld).applyMatrix4(inv.copy(root.matrixWorld).invert()); }
function quatIn(root: THREE.Object3D, o: THREE.Object3D, out: THREE.Quaternion) {
  o.matrixWorld.decompose(sp, out, ss); root.matrixWorld.decompose(sp, qs, ss);
  return out.premultiply(qs.invert());
}

/** Rotate `bone` (swing only) so that its Y axis points along `dir` (root space). */
export function aim(root: THREE.Object3D, bone: THREE.Object3D, dir: THREE.Vector3) {
  const cur = quatIn(root, bone, q1), axis = v1.set(0, 1, 0).applyQuaternion(cur);
  const swing = q2.setFromUnitVectors(axis, v2.copy(dir).normalize());
  const want = swing.multiply(cur);                       // new root-space orientation
  const par = quatIn(root, bone.parent!, q3);
  bone.quaternion.copy(par.invert().multiply(want));
  bone.updateMatrixWorld(true);
}

/** Two-bone IK: root bone `a` (upper), `b` (lower), end `c`; end reaches `target`, middle joint bends toward `pole`. */
export function ik(root: THREE.Object3D, a: THREE.Object3D, b: THREE.Object3D, c: THREE.Object3D, target: THREE.Vector3, pole: THREE.Vector3) {
  const A = posIn(root, a, new THREE.Vector3()), B = posIn(root, b, new THREE.Vector3()), C = posIn(root, c, new THREE.Vector3());
  const l1 = A.distanceTo(B), l2 = B.distanceTo(C);
  const T = target.clone().sub(A), d = Math.min(Math.max(T.length(), Math.abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3);
  const dir = T.normalize(), x = (d * d + l1 * l1 - l2 * l2) / (2 * d), h = Math.sqrt(Math.max(0, l1 * l1 - x * x));
  const pp = pole.clone().addScaledVector(dir, -pole.dot(dir)).normalize();
  const elbow = A.clone().addScaledVector(dir, x).addScaledVector(pp, h);
  aim(root, a, elbow.clone().sub(A));
  const end = A.clone().addScaledVector(dir, d);
  aim(root, b, end.sub(elbow));
}

/**
 * crank: crank angle (rad, as BikeRig.crank), type: bike type. `geo` from the bike manifest (saddle, bb).
 */
export function ridePose(b: RideBones, root: THREE.Object3D | number, crank = 0, type = 'city', geo: RideGeo | null = null) {
  if (typeof root === 'number') { crank = root; root = b.pelvis?.parent?.parent ?? b.pelvis!; } // legacy call ridePose(bones, pedal) (police patrol)
  if (!b.pelvis || !b.thigh_l || !b.thigh_r || !b.calf_l || !b.calf_r || !b.foot_l || !b.foot_r || !b.spine_01) return;
  const bars = BARS[type.replace('_lean', '')] ?? BARS.city;
  const saddle = geo?.saddle ?? [0.95, 0.15], bb = geo?.bb ?? [0.3, 0.06];
  root.rotation.set(0, 0, 0);
  root.updateMatrixWorld(true);
  // 1) torso: lean forward (pelvis a little, spine more)
  const lean = (deg: number) => new THREE.Vector3(0, Math.cos(THREE.MathUtils.degToRad(deg)), -Math.sin(THREE.MathUtils.degToRad(deg)));
  const leanDeg = type.startsWith('road') || type.startsWith('mtb') ? 38 : type.startsWith('city') || type.startsWith('kidseat') || type.startsWith('cargo') ? 14 : 24;
  aim(root, b.pelvis, lean(leanDeg * 0.5));
  for (const n of ['spine_01', 'spine_02', 'spine_03'] as const) if (b[n]) aim(root, b[n]!, lean(leanDeg));
  if (b.neck_01) aim(root, b.neck_01, lean(Math.max(0, leanDeg - 20)));
  // 2) put the pelvis on the saddle (root offset in the player's local frame; bike origin = player origin)
  const pel = posIn(root, b.pelvis, new THREE.Vector3());
  root.position.set(-pel.x, saddle[0] + 0.07 - pel.y, saddle[1] + 0.02 - pel.z);
  root.updateMatrixWorld(true);
  const toRoot = (x: number, y: number, z: number) => v1.set(x, y, z).sub(root.position).clone();
  // 3) legs follow the pedals; crank mesh turns by -crank about x, right pedal starts forward/down of the axis
  const L = 0.17, a0 = THREE.MathUtils.degToRad(-25), r = -crank;
  for (const side of [1, -1]) {
    const py = L * Math.sin(a0), pz = -L * Math.cos(a0);
    const cy = py * Math.cos(r) - pz * Math.sin(r), cz = py * Math.sin(r) + pz * Math.cos(r);
    const pedal = toRoot(side * 0.12, bb[0] + side * cy, bb[1] + side * cz);
    const ankle = pedal.add(new THREE.Vector3(0, 0.085, 0.09));
    const s = side > 0 ? 'r' : 'l';
    ik(root, b[`thigh_${s}`]!, b[`calf_${s}`]!, b[`foot_${s}`]!, ankle, new THREE.Vector3(side * 0.12, 0.25, -1));
    aim(root, b[`foot_${s}`]!, new THREE.Vector3(0, -0.22, -1));
  }
  // 4) arms to the grips
  if (b.upperarm_l && b.upperarm_r && b.lowerarm_l && b.lowerarm_r && b.hand_l && b.hand_r) {
    for (const side of [1, -1]) {
      const s = side > 0 ? 'r' : 'l';
      ik(root, b[`upperarm_${s}`]!, b[`lowerarm_${s}`]!, b[`hand_${s}`]!, toRoot(side * bars[2], bars[1] - 0.01, -bars[0]), new THREE.Vector3(side * 0.6, -0.5, 0.35));
    }
  }
  void UP;
}
