import { actions } from './actions';
import { settings } from '../ui/settings';

/** Touch: floating joystick on the left half, camera swipe on the right half. */
export function initTouch(stick: HTMLElement, knob: HTMLElement) {
  const R = 50;
  let moveId: number | null = null, lookId: number | null = null;
  let ox = 0, oy = 0, lx = 0, ly = 0;

  // on-screen buttons handle their own touches; run is a toggle so the right thumb stays free for the camera
  const runBtn = document.getElementById('btn-run');
  const setRun = (on: boolean) => { actions.run = on; runBtn?.classList.toggle('on', on); };
  for (const [id, on] of [['btn-use', () => { actions.use = true; }], ['btn-run', () => setRun(!actions.run)]] as const) {
    const b = document.getElementById(id);
    b?.addEventListener('touchstart', (e) => { e.stopPropagation(); e.preventDefault(); on(); }, { passive: false });
  }
  const isUi = (t: EventTarget | null) => !!(t as HTMLElement | null)?.closest?.('button, #radar, #bigmap, #menu, #clock, #clockpanel, #helpcard');
  const start = (e: TouchEvent) => {
    document.body.classList.add('touch');
    if (Array.from(e.changedTouches).every((t) => isUi(t.target))) return; // let taps on UI become clicks
    for (const t of Array.from(e.changedTouches)) {
      if (isUi(t.target)) continue;
      const stickSide = settings.stickRight ? t.clientX >= window.innerWidth / 2 : t.clientX < window.innerWidth / 2;
      if (stickSide && moveId === null) {
        moveId = t.identifier; ox = t.clientX; oy = t.clientY;
        stick.style.left = `${ox}px`; stick.style.top = `${oy}px`; stick.style.display = 'block';
      } else if (lookId === null) {
        lookId = t.identifier; lx = t.clientX; ly = t.clientY;
      }
    }
    e.preventDefault();
  };
  const move = (e: TouchEvent) => {
    if (moveId === null && lookId === null) return;
    for (const t of Array.from(e.changedTouches)) {
      if (t.identifier === moveId) {
        let dx = t.clientX - ox, dy = t.clientY - oy;
        const d = Math.hypot(dx, dy);
        if (d > R) { dx *= R / d; dy *= R / d; }
        knob.style.transform = `translate(${dx}px, ${dy}px)`;
        actions.move.x = dx / R; actions.move.y = -dy / R;
      } else if (t.identifier === lookId) {
        actions.look.yaw += (t.clientX - lx) * 0.008 * settings.sens;
        actions.look.pitch += (t.clientY - ly) * 0.006 * settings.sens;
        lx = t.clientX; ly = t.clientY;
      }
    }
    e.preventDefault();
  };
  const end = (e: TouchEvent) => {
    for (const t of Array.from(e.changedTouches)) {
      if (t.identifier === moveId) {
        moveId = null; stick.style.display = 'none'; knob.style.transform = '';
        actions.move.x = actions.move.y = 0; setRun(false);
      } else if (t.identifier === lookId) lookId = null;
    }
  };
  window.addEventListener('touchstart', start, { passive: false });
  window.addEventListener('touchmove', move, { passive: false });
  window.addEventListener('touchend', end);
  window.addEventListener('touchcancel', end);
}
