import { actions } from './actions';
import { settings } from '../ui/settings';

/** True while a key event targets a form field (bug-report box, sliders): the game must not read it as input. */
export const typing = (e: Event) => e.target instanceof HTMLElement && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName);

/** Keyboard (WASD/arrows, Shift) and mouse drag / pointer lock for the camera. */
export function initKeyboardMouse(canvas: HTMLCanvasElement) {
  const down = new Set<string>();
  const sync = () => {
    const f = +(down.has('KeyW') || down.has('ArrowUp')) - +(down.has('KeyS') || down.has('ArrowDown'));
    const r = +(down.has('KeyD') || down.has('ArrowRight')) - +(down.has('KeyA') || down.has('ArrowLeft'));
    const l = Math.hypot(f, r) || 1;
    actions.move.x = r / l;
    actions.move.y = f / l;
    actions.kb.x = r; actions.kb.y = f;
    actions.run = down.has('ShiftLeft') || down.has('ShiftRight');
  };
  window.addEventListener('keydown', (e) => {
    if (typing(e)) return;
    if ((e.code === 'KeyE' || e.code === 'KeyF') && !e.repeat) actions.use = true;
    if (e.code === 'KeyH' && !e.repeat) actions.bell = true;
    down.add(e.code); sync();
  });
  window.addEventListener('keyup', (e) => { down.delete(e.code); sync(); });
  window.addEventListener('blur', () => { down.clear(); sync(); });

  let dragging = false;
  canvas.addEventListener('mousedown', () => { dragging = true; });
  window.addEventListener('mouseup', () => { dragging = false; });
  canvas.addEventListener('dblclick', () => canvas.requestPointerLock?.());
  window.addEventListener('mousemove', (e) => {
    if (!dragging && document.pointerLockElement !== canvas) return;
    actions.look.yaw += e.movementX * 0.004 * settings.sens;
    actions.look.pitch += e.movementY * 0.003 * settings.sens;
  });
}
