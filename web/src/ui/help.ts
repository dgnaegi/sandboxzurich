/** One-time controls card on first start (dismissable) and fading of the permanent hint line. */
const KEY = 'sbz-help-seen';

const TOUCH = [
  ['Joystick', 'links auf dem Bildschirm ziehen = laufen'],
  ['Kamera', 'rechts wischen = umschauen'],
  ['⇧', 'Rennen an/aus'],
  ['E', 'Velo oder Auto nehmen / absteigen'],
  ['Radar', 'antippen = grosse Karte'],
  ['Uhr', 'antippen = Tageszeit'],
];
const PC = [
  ['W A S D', 'laufen (Pfeiltasten gehen auch)'],
  ['Maus', 'ziehen = umschauen (Doppelklick: Maus fangen)'],
  ['Shift', 'rennen'],
  ['E', 'Velo oder Auto nehmen / absteigen'],
  ['M', 'grosse Karte'],
  ['Uhr', 'anklicken = Tageszeit'],
];

function seen(): boolean { try { return localStorage.getItem(KEY) === '1'; } catch { return false; } }
function remember() { try { localStorage.setItem(KEY, '1'); } catch { /* ignore */ } }

export function initHelp(mobile: boolean) {
  const params = new URLSearchParams(location.search);
  if (mobile) document.body.classList.add('touch');
  // permanent hint line: PC only, fades after 3 minutes
  window.setTimeout(() => document.getElementById('help')?.classList.add('gone'), 180000);

  // automated browsers (Playwright) skip the card unless ?help is given
  if (params.has('nohelp') || (navigator.webdriver && !params.has('help')) || (seen() && !params.has('help'))) return;
  const rows = (mobile ? TOUCH : PC).map(([k, t]) => `<li><b>${k}</b><span>${t}</span></li>`).join('');
  const card = document.createElement('div');
  card.id = 'helpcard';
  card.innerHTML = `<div class="hc-box"><h2>So geht's</h2><ul>${rows}</ul><button type="button">Los geht's</button><small>${mobile ? 'Antippen zum Schliessen' : 'Klick oder Enter zum Schliessen'}</small></div>`;
  document.body.appendChild(card);
  const close = () => { remember(); card.classList.add('out'); window.setTimeout(() => card.remove(), 400); window.removeEventListener('keydown', onKey); };
  const onKey = (e: KeyboardEvent) => { if (e.code === 'Enter' || e.code === 'Space') { e.preventDefault(); close(); } };
  card.addEventListener('click', close);
  window.addEventListener('keydown', onKey);
}
