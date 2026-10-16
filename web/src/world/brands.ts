import type { Look, ShopSign } from './storefront_style';

/** Colours for recognisable shops and institutions. Names and house colours are facts; no logos or marks are drawn. */
const BRANDS: [RegExp, string, string][] = [
  [/^migros/i, '#ee6a00', '#ffffff'],
  [/^coop/i, '#e8331f', '#ffffff'],
  [/^denner/i, '#d5141c', '#ffe100'],
  [/^aldi/i, '#12337a', '#ffffff'],
  [/^lidl/i, '#0b4fa8', '#ffe600'],
  [/^volg/i, '#0d7a3e', '#ffffff'],
  [/^spar\b/i, '#c8102e', '#ffffff'],
  [/^(k kiosk|avec|valora)/i, '#d0202c', '#ffffff'],
];
const SCHOOL = new Set(['school', 'kindergarten', 'childcare', 'college', 'university']);
const CIVIC = new Set(['community_centre', 'library', 'townhall', 'post_office', 'hospital', 'clinic', 'police', 'fire_station']);

/** Look override for brands (house colours) and institutions (school / church / civic plaques); null = keep the generic look. */
export function applyBrand(look: Look, s: ShopSign): Look {
  for (const [re, bg, fg] of BRANDS) if (re.test(s.name)) return { ...look, bg, fg, st: 'box', font: '"Barlow Condensed"', hf: 1, neon: null };
  if (s.kind === 'galaxus') return { ...look, bg: '#0f1217', fg: '#ffffff', st: 'box', font: '"Barlow Condensed"', hf: 0.5, neon: null };
  if (SCHOOL.has(s.kind)) return { ...look, bg: '#ece6d6', fg: '#27415f', st: 'plain', font: '"Barlow Condensed"', hf: 0.75, neon: null };
  if (s.kind === 'place_of_worship') return { ...look, bg: '#cfc9bb', fg: '#2b2926', st: 'plain', font: '"Barlow Condensed"', hf: 0.75, neon: null };
  if (CIVIC.has(s.kind)) return { ...look, bg: '#255f86', fg: '#ffffff', st: 'plain', font: '"Barlow Condensed"', hf: 0.75, neon: null };
  return look;
}
