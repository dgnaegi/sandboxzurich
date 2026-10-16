/** Player settings, persisted in localStorage (every access guarded: private mode / blocked storage). */
export type GfxMode = 'auto' | 'sparen' | 'hoch';
export interface Settings { gfx: GfxMode; muted: boolean; sens: number; stickRight: boolean }

const KEY = 'sbz-settings';
export const settings: Settings = { gfx: 'auto', muted: false, sens: 1, stickRight: false };

try {
  const raw = JSON.parse(localStorage.getItem(KEY) ?? '{}') as Partial<Settings>;
  if (raw.gfx === 'auto' || raw.gfx === 'sparen' || raw.gfx === 'hoch') settings.gfx = raw.gfx;
  if (typeof raw.muted === 'boolean') settings.muted = raw.muted;
  if (typeof raw.sens === 'number' && raw.sens >= 0.4 && raw.sens <= 2.5) settings.sens = raw.sens;
  if (typeof raw.stickRight === 'boolean') settings.stickRight = raw.stickRight;
} catch { /* defaults */ }

export function saveSettings() {
  try { localStorage.setItem(KEY, JSON.stringify(settings)); } catch { /* ignore */ }
  document.body.classList.toggle('stick-right', settings.stickRight);
}

const GFX_LABEL: Record<GfxMode, string> = { auto: 'Automatisch', sparen: 'Akku sparen', hoch: 'Hoch' };
const GFX_HINT: Record<GfxMode, string> = {
  auto: 'Passt sich der Geschwindigkeit deines Geräts an.',
  sparen: 'Weniger Auflösung, Schatten und Sichtweite.',
  hoch: 'Volle Auflösung, Schatten und Sichtweite.',
};

/** Fills the settings page of the menu and reports changes. */
export function bindSettingsPage(page: HTMLElement, cb: { onGfx: (g: GfxMode) => void; onMute: (m: boolean) => void }) {
  const q = <T extends HTMLElement>(s: string) => page.querySelector<T>(s)!;
  const gfxBtns = Array.from(page.querySelectorAll<HTMLButtonElement>('[data-gfx]'));
  const sound = q<HTMLButtonElement>('#s-sound'), sens = q<HTMLInputElement>('#s-sens');
  const stick = q<HTMLButtonElement>('#s-stick'), hint = q('#s-gfx-hint');
  const refresh = () => {
    for (const b of gfxBtns) { b.classList.toggle('on', b.dataset.gfx === settings.gfx); b.textContent = GFX_LABEL[b.dataset.gfx as GfxMode]; }
    hint.textContent = GFX_HINT[settings.gfx];
    sound.textContent = `Ton: ${settings.muted ? 'aus' : 'an'}`;
    stick.textContent = `Joystick: ${settings.stickRight ? 'rechts' : 'links'}`;
    sens.value = String(settings.sens);
  };
  for (const b of gfxBtns) b.addEventListener('click', () => { settings.gfx = b.dataset.gfx as GfxMode; saveSettings(); refresh(); cb.onGfx(settings.gfx); });
  sound.addEventListener('click', () => { settings.muted = !settings.muted; saveSettings(); refresh(); cb.onMute(settings.muted); });
  stick.addEventListener('click', () => { settings.stickRight = !settings.stickRight; saveSettings(); refresh(); });
  sens.addEventListener('input', () => { settings.sens = Number(sens.value); saveSettings(); });
  saveSettings();
  refresh();
}
