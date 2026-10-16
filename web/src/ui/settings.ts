/** Player settings, persisted in localStorage (every access guarded: private mode / blocked storage). */
export interface Settings { muted: boolean; sens: number; stickRight: boolean; music: boolean; musicVol: number }

const KEY = 'sbz-settings';
export const settings: Settings = { muted: false, sens: 1, stickRight: false, music: true, musicVol: 0.5 };

try {
  const raw = JSON.parse(localStorage.getItem(KEY) ?? '{}') as Partial<Settings>;
  if (typeof raw.muted === 'boolean') settings.muted = raw.muted;
  if (typeof raw.sens === 'number' && raw.sens >= 0.4 && raw.sens <= 2.5) settings.sens = raw.sens;
  if (typeof raw.stickRight === 'boolean') settings.stickRight = raw.stickRight;
  if (typeof raw.music === 'boolean') settings.music = raw.music;
  if (typeof raw.musicVol === 'number' && raw.musicVol >= 0 && raw.musicVol <= 1) settings.musicVol = raw.musicVol;
} catch { /* defaults */ }

export function saveSettings() {
  try { localStorage.setItem(KEY, JSON.stringify(settings)); } catch { /* ignore */ }
  document.body.classList.toggle('stick-right', settings.stickRight);
}

/** Fills the settings page of the menu and reports changes. */
export function bindSettingsPage(page: HTMLElement, cb: { onMute: (m: boolean) => void; onMusic: () => void }) {
  const q = <T extends HTMLElement>(s: string) => page.querySelector<T>(s)!;
  const sound = q<HTMLButtonElement>('#s-sound'), sens = q<HTMLInputElement>('#s-sens');
  const music = q<HTMLButtonElement>('#s-music'), mvol = q<HTMLInputElement>('#s-mvol');
  const stick = q<HTMLButtonElement>('#s-stick');
  const refresh = () => {
    sound.textContent = `Ton: ${settings.muted ? 'aus' : 'an'}`;
    music.textContent = `Musik: ${settings.music ? 'an' : 'aus'}`;
    mvol.value = String(settings.musicVol);
    stick.textContent = `Joystick: ${settings.stickRight ? 'rechts' : 'links'}`;
    sens.value = String(settings.sens);
  };
  sound.addEventListener('click', () => { settings.muted = !settings.muted; saveSettings(); refresh(); cb.onMute(settings.muted); });
  music.addEventListener('click', () => { settings.music = !settings.music; saveSettings(); refresh(); cb.onMusic(); });
  mvol.addEventListener('input', () => { settings.musicVol = Number(mvol.value); saveSettings(); cb.onMusic(); });
  stick.addEventListener('click', () => { settings.stickRight = !settings.stickRight; saveSettings(); refresh(); });
  sens.addEventListener('input', () => { settings.sens = Number(sens.value); saveSettings(); });
  saveSettings();
  refresh();
}
