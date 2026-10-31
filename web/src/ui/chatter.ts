/**
 * Speech-bubble lines for passers-by, picked by place, time and what the player is riding. Züritüütsch (spoken
 * Zürich dialect) with Swisscore / Züricore satire: affectionate mockery of Zürich clichés, never of real people,
 * parties or shops (docs/CONTENT_GUIDELINES.md). Sources, spelling notes and rejected lines: research/chatter_mundart.md.
 * UI text elsewhere stays Hochdeutsch; the bubbles are what people on the street actually say.
 */
export type ChatMode = 'foot' | 'run' | 'bike' | 'scooter' | 'car' | 'transit';
export interface ChatCtx { place: string; min: number; day: number; night: boolean; mode: ChatMode }

const ANY_DAY = [
  'Grüezi.', 'Hoi zäme!', 'Sali!', 'So en Lappe!', 'Sone Galööri.', 'Würd mi.', 'Nöd so deep.', 'Das isch ja peak.',
  'Chunnt s dänn öppe?', 'Exgüsi, dörf i schnäll verbii?', 'Bisch au nöd vo da, gäll?', 'Bisch scho imne Verein?',
  'Alles tuet mer weh.', 'Muesch gschpüüre!', 'Ehrewort nöd!',
];
/** Zürich clichés and types (Bünzli, Seefeld, Kreis-5-Startup, Expat); the English ones are the expats. */
const CLICHE = [
  'Punkt Zähni gaht s Fänschter uf.', 'Abfallsack ohni Marke? Das wird tüür.', 'Robidog isch dete, nöd uf em Rase.',
  'Goldküschte oder Pfnüselküschte?', 'Brocki billig? Nöd i Züri.', 'Polo, On-Schueh, Garmin. Hoi Reto.',
  'Im Seefeld hät s meh Porsche als Parkplätz.', 'Startup im Chreis 5: Pitch, Pingpong, kei Umsatz.',
  'Disruptsch au öppis oder trinksch nur Kafi?', 'Hochdütsch reicht nöd, sorry.', 'Zürcher arrogant? Säg das no eimal.',
  'Bisch Migros- oder Coop-Chind?', 'Chasch nöd de Füfer und s Weggli ha.', 'S het solang s het.', 'Hochnäbel. Wider.',
  'Hudlet s? Dänn Badi zue.', 'Fondue im Auguscht? Bisch Tourischt.', 'Am Obere Lette: alli tättowiert, niemert schwümmt.',
  'Hey, I just moved here from California, can I join your inner circle?', 'Three balconies, walk-in closet and lake view, please.',
  "I'm not an immigrant, I'm an expat.", 'Do you speak High German? – Nei.',
];
const MORNING = ['Guete Morge!', 'Zerscht en Kafi, dänn redsch mit mir.', 'S Tram isch scho wider z spaat.', 'Zwei Gipfeli und d Zytig, bitte.', 'Znüni isch heilig.', 'Z spaat? Nöd i Züri.', 'Scho gschafft oder erscht Yoga gha?', 'Schaffsch uf de Gmeind, gäll?'];
const NOON = ['Zmittag! Chunsch mit?', 'Ich hol mer schnäll öppis z ässe.', 'Hüt git s Kebab, oder?', 'Znüni-Weggli isch scho wider weg.'];
const EVENING = ['Schöne Fiirabig!', 'Chunsch no uf es Bier mit?', 'Wämmer eis go ziie?', 'Ich muess no i d Wöschchuchi.', 'Wo bliibt s Tram?'];
const NIGHT = ['Schöne Abig no!', 'Hesch Füür?', 'No eis, und dänn gang i hei.', 'Scho so spaat? Ich muess morn früeh use.', 'Guet Nacht, bis morn!', 'Punkt Zähni rüeft öpper d Polizei.', 'Abeleere!', 'Hesch en Lumpe im Gsicht.', 'Mach de Fisch, bevor d Tschugger chömed.'];
const WEEKEND = ['Chunsch nach em Flohmi uf en Kafi?', 'Hüt isch ändlich frei.', 'Hesch scho öppis vor am Wuchenänd?', 'Uetliberg, Brunch, susch nüt.'];
const SUNDAY = ['Sunntig isch Ruehtag. Au für dich.', 'Glas in Container am Sunntig? Bisch verruckt?', 'Rasemäie am Sunntig, de Nachber luegt scho.', 'Nach Zähni nüme spüele, gäll.'];
/** What people shout at you depending on how you move; `foot` has no extra lines. */
const BY_MODE: Record<ChatMode, string[]> = {
  foot: [],
  run: ['Hopp de Bäse!', 'Rännsch vor de Stüüre devo?', 'Jogge ohni Garmin zellt nöd.', 'Sone Stürmi, immer am Pressiere.', 'De Schneller isch de Gschwinder.'],
  bike: ['Rotliecht gilt au für Velos, gäll.', 'Trottoir isch für Füess, nöd für Velo!', 'Ohni Helm? Mega mutig.', 'Chlingle hilft. Schreie au.', 'Lastevelo? Du wohnsch sicher im Chreis 4.', 'Isch das Velo vom Brocki oder gstole?', 'Velokurier oder eifach z spaat dra?'],
  scooter: ['Hesch Termin?', 'Hesch Termin?', 'Z Fuess wärsch scho dete.', 'Stell s Trotti nöd mitts ufs Trottoir!', 'Trotti plus Bier isch Statistik.', 'Mit em Trotti s Gipfeli hole. Sportlich.', 'Fahr uf de Strass, nöd uf min Fuess!'],
  car: ['Voll wüests Auto.', 'Sone Chlapf.', 'Isch das dis Auto oder grad gfunde?', 'Mit em Auto i d Stadt? Hesch z viel Ziit?', 'Blaui Zone, nöd Trottoir, du Tubel.', 'Düüse chasch uf de Autobahn, nöd i de 30er.', 'Gleast oder bisch bi de Bank?'],
  transit: ['Türe freigäh, s Tram wartet uf niemert.', 'Rucksack ab im Tram, du Tubel.', 'Nöd so luut telefoniere, mer sind im Tram.', 'Isch das no Fahrplan oder scho Kunscht?'],
};
const BY_PLACE: [RegExp, string[]][] = [
  [/langstrasse/i, ['Da isch immer öppis los.', 'Ein Falafel bitte, scharf.', 'D Miete da sind komplett verruckt.', 'Soja-Chai-Latte a de Langstrass. Voll Gentrifizierig.', 'Langstrass am Samschtig? Viel Glück.']],
  [/helvetiaplatz|kanzlei/i, ['De Märt hät hüt schöns Gmües.', 'Träffe mer eus bim Volkshuus?', 'Im Xenix lauft hüt en guete Film.']],
  [/limmatplatz|escher|hardbrücke|hardplatz/i, ['De Zug fahrt grad, ich muess renne!', 'Da isch alles Bauschtell.', 'Vo de Hardbrugg gsehsch s ganz Quartier.']],
  [/stauffacher|werd/i, ['Ich nimm s Tram bis Bahnhofstrass.', 'Träffpunkt isch bim Stauffacher.']],
  [/bahnhof|hb\b/i, ['Weles Gleis isch es scho wider?', 'Min Zug hät wider Verspötig.', 'Ich muess de Aschluss verwütsche!']],
  [/bäckeranlage|josefwiese|park|wiese/i, ['D Chind sind scho wider im Planschbecki.', 'Da isch de Hund immer glücklich.', 'Robidog isch dete, nöd uf em Rase.']],
];

export function chatLine(c: ChatCtx): string {
  const pick = (a: string[]) => a[Math.floor(Math.random() * a.length)];
  const pool: string[] = [...ANY_DAY, ...CLICHE];
  for (const [re, lines] of BY_PLACE) if (re.test(c.place)) pool.push(...lines, ...lines);
  const mode = BY_MODE[c.mode] ?? [];
  pool.push(...mode, ...mode, ...mode);   // what you ride is the first thing people comment on
  const h = c.min / 60;
  if (c.night) pool.push(...NIGHT, ...NIGHT);
  else if (h < 10) pool.push(...MORNING, ...MORNING);
  else if (h >= 11.5 && h < 14) pool.push(...NOON, ...NOON);
  else if (h >= 16.5) pool.push(...EVENING, ...EVENING);
  if (c.day >= 5 && !c.night) pool.push(...WEEKEND);
  if (c.day === 6 && !c.night) pool.push(...SUNDAY, ...SUNDAY);
  return pick(pool);
}
