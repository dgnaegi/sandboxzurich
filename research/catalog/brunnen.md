# Brunnen – Varianten (Kreis 3/4/5/9)

Quelle Anzahl: `data/raw/stadtzh/geo_brunnen__wvz_brunnen.geojson`, 334 Brunnen (stadtkreis 3/4/5/9; 281 öffentlich, 51 privat, 2 Notwasser nach Feld `art`). Regeln und Zahlen: `pipeline/catalog/variants.py` → `variant_counts.json`. Fotos: 94 Brunnen haben ein lokales Foto ≤ 25 m, nur 51 ≤ 12 m, und davon zeigen viele den Brunnen gar nicht (Strassenfoto). Die Zuordnung per Auge ist deshalb nur für die unten genannten IDs gesichert.

Masse: Richtwerte aus Fotos (Person ≈ 1.75 m). Farben: Richtwerte, nicht gemessen.

| Variante | Anzahl (Daten) | Zuordnungsmerkmal (Datenfeld → Variante) | Form, Masse (geschätzt) | Material / Farbe (Richtwert) | Beispiel-Foto-IDs (sicher) |
|---|---|---|---|---|---|
| **V1 Säulenbrunnen** (Zürcher Standard: Säule + Trog) | 45 | `material_trog` und `material_saeule` gesetzt, `material_figur` leer | Säule 1.0–1.6 m, Trog rund/oval Ø 0.8–1.2 m, Wasserstrahl aus Säule in Trog | Kalkstein/Sandstein/Granit, Säule oft dunkler (Muschelkalk, Holz selten) #bdb5a0 / #8f877a | BR-223 (Säule mit Schale, Datenfeld Säule fehlt → Fehler im Datensatz, siehe unten) |
| **V2 Trogbrunnen Stein** (rund/oval, ohne Säule; Unterform: Doppeltrog oval, Trog mit Relief) | 135 | `material_trog` in Stein-Familie (Granit, Gneis, Kalk, Sandstein, Porphyr, Findling), keine Säule, keine Figur | Trog rund Ø 1.5–2.5 m, Höhe 0.4–0.6 m; oval Doppeltrog ca. 2.5 × 1.2 m | Granit grau #7d7d78; Gneis dunkler #5e5e5a; Kalk hell #cfc4ad | BR-278 (rund, Relief-Band, Kindergarten Wiedikon), BR-609 (oval Doppeltrog, Feld School) |
| **V3 Bronzeguss-Trog** | 33 | `material_trog` = Bronzeguss / Bronze | Trog rund oder Schale auf Stiel, Ø 0.8–1.5 m | Patina dunkelbraun #4a3d2c, Glanzstellen #8a6d45 | nicht gesichert (Fotos zeigen Bronze nur am Rand) |
| **V4 Betontrog / Betonbassin** | 19 | `material_trog` = Beton | Bassin rund Ø 3–4 m, Rand 0.4 m (Plätze), Fontäne mittig | Beton hellgrau #9a9a96 | BR-41 (rundes Bassin mit Fontäne, Freibad-/Platzumfeld) |
| **V5 Kunststein-Trog** (flach, rund) | 15 | `material_trog` = Kunststein | flache Schale Ø 1.0–1.5 m, Rand 0.3 m, Auslauf am Rand | Kunststein hell-beige #b8b2a6 | BR-429 (flache runde Schale), BR-607 (Friedhof Sihlfeld, Auslauf) |
| **V6 Figurenbrunnen** | 34 | `material_figur` gesetzt (meist Bronze, auch Stein) | Figur 0.6–1.8 m auf Trog oder Sockel; Wandnische möglich | Bronze #4a3d2c, Stein wie Trog | BR-284 (Fröschen-Brunnen, Bronze-Figur in Wandnische, Altstetten) |
| **V7 Wandbrunnen (Nische)** | 0 (nicht aus Daten ableitbar) | keine Angabe; Nischenfassade am Schulhaus | Nische 2–3 m hoch, Muschel-/Bogenornament, Trog 0.4 m tief | Muschelkalk hell #bdb5a0 | BR-111 und BR-260 (Schulhaus Limmat Aussenseite, Muschel-Nische) |
| **V8 Notwasserbrunnen** | 2 (Feld `art`); 27 nach `brunnenart` | `art` = Notwasserbrunnen | Gusseisen/Bronze, Säule, offene Schale | Dunkelgrau #4f4f4f, Bronze | keine sicher gesehen. Achtung: `art` und `brunnenart` widersprechen sich |
| **V9 Holztrog** | 3 | `material_trog` = Holz | Holztrog Ø 1.0 m | Holz braun #7a5a3a | keine |
| **V10 ohne Materialangabe** | 48 | `material_trog` leer (und keine Säule) | unbekannt, Foto nötig | – | 8 Objekte mit Foto ≤ 25 m, nicht sicher bestimmt |

Summe: 334 (Kontrolle: 2 + 34 + 45 + 135 + 33 + 19 + 15 + 0 + 3 + 48).

## Befunde
- Die Datenregel ist grob. Wandbrunnen (BR-111, BR-260) tragen eine Säulenangabe und würden als V1 falsch laufen. BR-223 hat im Datensatz keine Säule, auf dem Foto steht aber eine Säule über der Schale. Die Regeln sind Startwerte, die Overrides in `assign_hints.json` korrigieren sie.
- Die Mehrzahl der Brunnen hat kein Foto, auf dem sie zu sehen ist. Für V3, V7, V9 und die 48 Objekte ohne Angabe fehlt ein Beleg. Das braucht gezielte Fotos (Commons/Mapillary, Lage-Suche) oder Stichproben vor Ort.
- Schalenbrunnen auf Stiel (Bronze/Granit, Hardplatz-Stil) gibt es vermutlich als eigene Form. Auf einem Foto (BR-401, Segheriagranit) ist eine Schale auf kurzem Stiel zu sehen. Das ist nicht sicher und wird nicht als Variante geführt; es fällt heute unter V2.
- Datensatz-Feld `historisches_baujahr` (Mehrheit 1925–1975) hilft nicht bei der Form.

## Assign-Hints (`research/catalog/assign_hints.json`, nur sicher)
BR-41 → V4, BR-429 → V5, BR-607 → V5, BR-609 → V2, BR-278 → V2, BR-284 → V6, BR-111 → V7, BR-260 → V7.
