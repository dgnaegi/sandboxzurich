/** Speech-bubble lines for passers-by, picked by place and time. Hochdeutsch, Schweizer Schreibweise (no Mundart without sign-off). */
export interface ChatCtx { place: string; min: number; day: number; night: boolean }

const ANY_DAY = ['Hallo!', 'Guten Tag!', 'Schönen Tag noch!', 'Na, auch unterwegs?', 'Entschuldigung, darf ich kurz vorbei?'];
const MORNING = ['Guten Morgen!', 'Ich brauche zuerst einen Kaffee.', 'Das Tram ist schon wieder zu spät.', 'Zwei Gipfeli, bitte, und eine Zeitung.'];
const NOON = ['Mittagspause! Kommst du mit?', 'Ich hole mir schnell etwas zu essen.', 'Heute gibt es Kebab, oder?'];
const EVENING = ['Schönen Feierabend!', 'Kommst du noch auf ein Bier mit?', 'Ich muss noch zur Waschküche.', 'Wo bleibt das Tram?'];
const NIGHT = ['Schönen Abend noch!', 'Hast du Feuer?', 'Noch ein Bier, und dann gehe ich heim.', 'Schon so spät? Ich muss morgen früh raus.', 'Gute Nacht, bis morgen!'];
const WEEKEND = ['Kommst du nach dem Flohmarkt zum Kaffee?', 'Heute ist endlich frei.', 'Hast du schon was vor am Wochenende?'];
const BY_PLACE: [RegExp, string[]][] = [
  [/langstrasse/i, ['Hier ist immer etwas los.', 'Ein Falafel bitte, mit scharf.', 'Die Mieten hier sind verrückt geworden.']],
  [/helvetiaplatz|kanzlei/i, ['Der Markt hat heute schönes Gemüse.', 'Treffen wir uns beim Volkshaus?', 'Im Xenix läuft heute ein guter Film.']],
  [/limmatplatz|escher|hardbrücke|hardplatz/i, ['Der Zug fährt gleich, ich muss rennen!', 'Hier ist alles Baustelle.', 'Von der Hardbrücke sieht man das ganze Quartier.']],
  [/stauffacher|werd/i, ['Ich nehme das Tram bis Bahnhofstrasse.', 'Treffpunkt ist beim Stauffacher.']],
  [/bahnhof|hb\b/i, ['Welches Gleis war es noch mal?', 'Mein Zug hat wieder Verspätung.', 'Ich muss den Anschluss erwischen!']],
  [/bäckeranlage|josefwiese|park|wiese/i, ['Die Kinder sind schon wieder im Planschbecken.', 'Hier ist der Hund immer glücklich.']],
];

export function chatLine(c: ChatCtx): string {
  const pick = (a: string[]) => a[Math.floor(Math.random() * a.length)];
  const pool: string[] = [...ANY_DAY];
  for (const [re, lines] of BY_PLACE) if (re.test(c.place)) pool.push(...lines, ...lines);
  const h = c.min / 60;
  if (c.night) pool.push(...NIGHT, ...NIGHT);
  else if (h < 10) pool.push(...MORNING, ...MORNING);
  else if (h >= 11.5 && h < 14) pool.push(...NOON, ...NOON);
  else if (h >= 16.5) pool.push(...EVENING, ...EVENING);
  if (c.day >= 5 && !c.night) pool.push(...WEEKEND);
  return pick(pool);
}
