import type * as THREE from 'three';

/** Seated, pedalling pose applied on top of the idle clip (after mixer.update). Bone axes differ per bone. */
const NAMES = ['thigh_l', 'thigh_r', 'calf_l', 'calf_r', 'upperarm_l', 'upperarm_r', 'spine_01'] as const;
export type RideBones = Partial<Record<(typeof NAMES)[number], THREE.Object3D>>;

export function rideBones(root: THREE.Object3D): RideBones {
  const b: RideBones = {};
  for (const n of NAMES) b[n] = root.getObjectByName(n);
  return b;
}

export function ridePose(b: RideBones, pedal: number) {
  const p = Math.sin(pedal);
  b.spine_01?.rotateX(0.35);
  b.thigh_l?.rotateX(-1.2 - 0.35 * p); b.calf_l?.rotateX(-1.1 + 0.4 * p);
  b.thigh_r?.rotateX(-1.2 + 0.35 * p); b.calf_r?.rotateX(-1.1 - 0.4 * p);
  b.upperarm_l?.rotateX(0.8); b.upperarm_r?.rotateX(0.8);
}
