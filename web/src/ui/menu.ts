import { bindSettingsPage, settings } from './settings';
import { bindReportPage, type ReportInfo } from './report';
import { typing } from '../input/keyboard';

const CONTACT = 'daniel@gnaegi.me';

/** Pause menu (Esc / P / ☰): continue, map, settings (sound, camera, joystick), contact (mail), report a bug (GitHub issue), credits, imprint. */
export class Menu {
  open = false;
  private el = document.getElementById('menu')!;
  onMap: () => void = () => {};
  onMute: (m: boolean) => void = () => {};
  onMusic: (on: boolean, vol: number) => void = () => {};
  /** Snapshot for «Fehler melden»; main.ts sets it once the game runs. */
  onReport: () => ReportInfo | null = () => null;

  constructor() {
    const $ = (id: string) => document.getElementById(id)!;
    $('btn-menu').addEventListener('click', () => this.toggle(true));
    $('m-continue').addEventListener('click', () => this.toggle(false));
    $('m-map').addEventListener('click', () => { this.toggle(false); this.onMap(); });
    bindSettingsPage(this.el.querySelector<HTMLElement>('[data-page="settings"]')!, { onMute: (m) => this.onMute(m), onMusic: () => this.onMusic(settings.music, settings.musicVol) });
    $('m-settings').addEventListener('click', () => this.page('settings'));
    $('m-contact').addEventListener('click', () => { location.href = `mailto:${CONTACT}`; });
    const report = bindReportPage(this.el.querySelector<HTMLElement>('[data-page="report"]')!, { contact: CONTACT, info: () => this.onReport() });
    $('m-report').addEventListener('click', () => { this.page('report'); report.refresh(); });
    for (const id of ['m-credits', 'm-imprint']) $(id).addEventListener('click', () => this.page(id === 'm-credits' ? 'credits' : 'imprint'));
    for (const b of document.querySelectorAll('.m-back')) b.addEventListener('click', () => this.page('main'));
    window.addEventListener('keydown', (e) => {
      if (typing(e)) { if (e.code === 'Escape') (e.target as HTMLElement).blur(); return; }   // writing a bug report: P does nothing, Escape leaves the box first
      if (e.code === 'KeyP' || (e.code === 'Escape' && !document.getElementById('bigmap')!.style.display.includes('block'))) this.toggle(!this.open);
    });
  }

  toggle(on: boolean) {
    this.open = on;
    this.el.style.display = on ? 'grid' : 'none';
    this.page('main');
    if (on) document.exitPointerLock?.();
  }

  private page(name: string) {
    for (const p of this.el.querySelectorAll<HTMLElement>('.m-page')) p.style.display = p.dataset.page === name ? 'block' : 'none';
  }
}
