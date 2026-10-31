/**
 * Speech-bubble lines for passers-by, picked by place, time and what the player is riding. Züritüütsch (spoken
 * Zürich dialect) with Swisscore / Züricore satire: affectionate mockery of Zürich clichés, never of real people,
 * parties or shops (docs/CONTENT_GUIDELINES.md). Sources, spelling notes and rejected lines: research/chatter_mundart.md.
 * UI text elsewhere stays Hochdeutsch; the bubbles are what people on the street actually say.
 *
 * Vetting state (2026-10-31): ACTIVE are only the lines the fork owner named (OWNER, the Swisscore insiders testers
 * should meet first) and the maintainer's original Hochdeutsch lines in dialect. Everything researched or composed
 * beyond that sits in RESERVE, which chatLine() never reads, until testers have vetted it; to activate a line, move
 * it from RESERVE into the matching pool.
 */
export type ChatMode = 'foot' | 'run' | 'bike' | 'scooter' | 'car' | 'transit';
export interface ChatCtx { place: string; min: number; day: number; night: boolean; mode: ChatMode }

// --- active -------------------------------------------------------------------------------------------------
/** Named by the fork owner (spelling as given). Weighted double in every context. */
const OWNER = [
  'So en Lappe!', 'Bisch scho imne Verein?', 'Angst und Geld hani kei.', 'Hey, gömmer Bulle go schlah?', 'Multipli hundert.', 'Chatsy.',
  'Hey, I just moved here from California, can I join your inner circle?',
];
/** The maintainer's original lines (Hochdeutsch until now), translated one to one. */
const ANY_DAY = ['Hoi!', 'Grüezi.', 'Schöne Tag no!', 'Au underwägs?', 'Exgüsi, dörf i schnäll verbii?'];
const MORNING = ['Guete Morge!', 'Ich bruuche zerscht en Kafi.', 'S Tram isch scho wider z spaat.', 'Zwei Gipfeli, bitte, und e Zytig.'];
const NOON = ['Zmittag! Chunsch mit?', 'Ich hol mer schnäll öppis z ässe.', 'Hüt git s Kebab, oder?'];
const EVENING = ['Schöne Fiirabig!', 'Chunsch no uf es Bier mit?', 'Ich muess no i d Wöschchuchi.', 'Wo bliibt s Tram?'];
const NIGHT = ['Schöne Abig no!', 'Hesch Füür?', 'No eis, und dänn gang i hei.', 'Scho so spaat? Ich muess morn früeh use.', 'Guet Nacht, bis morn!'];
const WEEKEND = ['Chunsch nach em Flohmi uf en Kafi?', 'Hüt isch ändlich frei.', 'Hesch scho öppis vor am Wuchenänd?'];
/** What people shout at you depending on how you move (owner lines only so far; more in RESERVE.mode). */
const BY_MODE: Record<ChatMode, string[]> = { foot: [], run: [], bike: [], scooter: ['Hesch Termin?'], car: ['Voll wüests Auto.'], transit: [] };
const BY_PLACE: [RegExp, string[]][] = [
  [/langstrasse/i, ['Da isch immer öppis los.', 'Ein Falafel bitte, scharf.', 'D Miete da sind komplett verruckt.']],
  [/helvetiaplatz|kanzlei/i, ['De Märt hät hüt schöns Gmües.', 'Träffe mer eus bim Volkshuus?', 'Im Xenix lauft hüt en guete Film.']],
  [/limmatplatz|escher|hardbrücke|hardplatz/i, ['De Zug fahrt grad, ich muess renne!', 'Da isch alles Bauschtell.', 'Vo de Hardbrugg gsehsch s ganz Quartier.']],
  [/stauffacher|werd/i, ['Ich nimm s Tram bis Bahnhofstrass.', 'Träffpunkt isch bim Stauffacher.']],
  [/bahnhof|hb\b/i, ['Weles Gleis isch es scho wider?', 'Min Zug hät wider Verspötig.', 'Ich muess de Aschluss verwütsche!']],
  [/bäckeranlage|josefwiese|park|wiese/i, ['D Chind sind scho wider im Planschbecki.', 'Da isch de Hund immer glücklich.']],
];

export function chatLine(c: ChatCtx): string {
  const pick = (a: string[]) => a[Math.floor(Math.random() * a.length)];
  const pool: string[] = [...OWNER, ...OWNER, ...ANY_DAY];
  for (const [re, lines] of BY_PLACE) if (re.test(c.place)) pool.push(...lines, ...lines);
  const mode = BY_MODE[c.mode] ?? [];
  pool.push(...mode, ...mode, ...mode);   // what you ride is the first thing people comment on
  const h = c.min / 60;
  if (c.night) pool.push(...NIGHT, ...NIGHT);
  else if (h < 10) pool.push(...MORNING, ...MORNING);
  else if (h >= 11.5 && h < 14) pool.push(...NOON, ...NOON);
  else if (h >= 16.5) pool.push(...EVENING, ...EVENING);
  if (c.day >= 5 && !c.night) pool.push(...WEEKEND);
  return pick(pool);
}

// --- reserve: researched / composed, NOT in use until vetted (research/chatter_mundart.md lists the sources) --------
export const RESERVE = {
  generic: ['Hoi zäme!', 'Sali!', 'Sone Galööri.', 'Würd mi.', 'Nöd so deep.', 'Das isch ja peak.', 'Chunnt s dänn öppe?', 'Bisch au nöd vo da, gäll?', 'Alles tuet mer weh.', 'Muesch gschpüüre!', 'Ehrewort nöd!'],
  /** Zürich clichés and types (Bünzli, Seefeld, Kreis-5-Startup, Expat); the English ones are the expats. */
  cliche: [
    'Punkt Zähni gaht s Fänschter uf.', 'Abfallsack ohni Marke? Das wird tüür.', 'Robidog isch dete, nöd uf em Rase.',
    'Goldküschte oder Pfnüselküschte?', 'Brocki billig? Nöd i Züri.', 'Polo, On-Schueh, Garmin. Hoi Reto.',
    'Im Seefeld hät s meh Porsche als Parkplätz.', 'Startup im Chreis 5: Pitch, Pingpong, kei Umsatz.',
    'Disruptsch au öppis oder trinksch nur Kafi?', 'Hochdütsch reicht nöd, sorry.', 'Zürcher arrogant? Säg das no eimal.',
    'Bisch Migros- oder Coop-Chind?', 'Chasch nöd de Füfer und s Weggli ha.', 'S het solang s het.', 'Hochnäbel. Wider.',
    'Hudlet s? Dänn Badi zue.', 'Fondue im Auguscht? Bisch Tourischt.', 'Am Obere Lette: alli tättowiert, niemert schwümmt.',
    'Three balconies, walk-in closet and lake view, please.', "I'm not an immigrant, I'm an expat.", 'Do you speak High German? – Nei.',
  ],
  morning: ['Zerscht en Kafi, dänn redsch mit mir.', 'Znüni isch heilig.', 'Z spaat? Nöd i Züri.', 'Scho gschafft oder erscht Yoga gha?', 'Schaffsch uf de Gmeind, gäll?'],
  noon: ['Znüni-Weggli isch scho wider weg.'],
  evening: ['Wämmer eis go ziie?'],
  night: ['Punkt Zähni rüeft öpper d Polizei.', 'Abeleere!', 'Hesch en Lumpe im Gsicht.', 'Mach de Fisch, bevor d Tschugger chömed.'],
  weekend: ['Uetliberg, Brunch, susch nüt.'],
  sunday: ['Sunntig isch Ruehtag. Au für dich.', 'Glas in Container am Sunntig? Bisch verruckt?', 'Rasemäie am Sunntig, de Nachber luegt scho.', 'Nach Zähni nüme spüele, gäll.'],
  mode: {
    run: ['Hopp de Bäse!', 'Rännsch vor de Stüüre devo?', 'Jogge ohni Garmin zellt nöd.', 'Sone Stürmi, immer am Pressiere.', 'De Schneller isch de Gschwinder.'],
    bike: ['Rotliecht gilt au für Velos, gäll.', 'Trottoir isch für Füess, nöd für Velo!', 'Ohni Helm? Mega mutig.', 'Chlingle hilft. Schreie au.', 'Lastevelo? Du wohnsch sicher im Chreis 4.', 'Isch das Velo vom Brocki oder gstole?', 'Velokurier oder eifach z spaat dra?'],
    scooter: ['Z Fuess wärsch scho dete.', 'Stell s Trotti nöd mitts ufs Trottoir!', 'Trotti plus Bier isch Statistik.', 'Mit em Trotti s Gipfeli hole. Sportlich.', 'Fahr uf de Strass, nöd uf min Fuess!'],
    car: ['Sone Chlapf.', 'Isch das dis Auto oder grad gfunde?', 'Mit em Auto i d Stadt? Hesch z viel Ziit?', 'Blaui Zone, nöd Trottoir, du Tubel.', 'Düüse chasch uf de Autobahn, nöd i de 30er.', 'Gleast oder bisch bi de Bank?'],
    transit: ['Türe freigäh, s Tram wartet uf niemert.', 'Rucksack ab im Tram, du Tubel.', 'Nöd so luut telefoniere, mer sind im Tram.', 'Isch das no Fahrplan oder scho Kunscht?'],
  },
  place: {
    langstrasse: ['Soja-Chai-Latte a de Langstrass. Voll Gentrifizierig.', 'Langstrass am Samschtig? Viel Glück.'],
    park: ['Robidog isch dete, nöd uf em Rase.'],
  },
};
