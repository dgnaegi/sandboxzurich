import { GfxMode, bindSettingsPage } from './settings';

/** Pause menu (Esc / P / ☰): continue, map, settings (graphics, sound, camera, joystick), credits, imprint. */
export class Menu {
  open = false;
  private el = document.getElementById('menu')!;
  onMap: () => void = () => {};
  onQuality: (q: GfxMode) => void = () => {};
  onMute: (m: boolean) => void = () => {};

  constructor() {
    const $ = (id: string) => document.getElementById(id)!;
    $('btn-menu').addEventListener('click', () => this.toggle(true));
    $('m-continue').addEventListener('click', () => this.toggle(false));
    $('m-map').addEventListener('click', () => { this.toggle(false); this.onMap(); });
    bindSettingsPage(this.el.querySelector<HTMLElement>('[data-page="settings"]')!, { onGfx: (g) => this.onQuality(g), onMute: (m) => this.onMute(m) });
    $('m-settings').addEventListener('click', () => this.page('settings'));
    for (const id of ['m-credits', 'm-imprint']) $(id).addEventListener('click', () => this.page(id === 'm-credits' ? 'credits' : 'imprint'));
    for (const b of document.querySelectorAll('.m-back')) b.addEventListener('click', () => this.page('main'));
    window.addEventListener('keydown', (e) => {
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
