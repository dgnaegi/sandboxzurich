/** Device-independent actions. Gameplay code reads only this, never keys or touches directly. */
export interface Actions {
  /** Move intent: x = right, y = forward, length 0..1. */
  move: { x: number; y: number };
  /** Accumulated camera look delta in radians since last frame (consumed by the camera). */
  look: { yaw: number; pitch: number };
  run: boolean;
  /** Raw (un-normalised) keyboard axes: full throttle while steering fully. 0,0 when no key / touch is used. */
  kb: { x: number; y: number };
  /** Edge-triggered action button (E / touch): get on/off bike, interact. */
  use: boolean;
}

export const actions: Actions = { move: { x: 0, y: 0 }, look: { yaw: 0, pitch: 0 }, run: false, use: false, kb: { x: 0, y: 0 } };

export function consumeUse() {
  const u = actions.use;
  actions.use = false;
  return u;
}

export function consumeLook() {
  const l = { ...actions.look };
  actions.look.yaw = actions.look.pitch = 0;
  return l;
}
