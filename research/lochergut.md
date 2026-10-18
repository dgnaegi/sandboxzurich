# Lochergut: Quellen, Befunde, Lizenzen (v4, Coop und Platz)

Auftrag: Coop, Ladenzeile im Sockel, Vorplatz und Kreuzung Badenerstrasse/Sihlfeldstrasse realistischer. Kontaktbogen `preview/ref_lochergut_1..5.jpg` (Nummern = Zeile unten), Vergleich `preview/lochergut_cmp.jpg`.
Fotos liegen lokal in `data/raw/photos/{v3,places_k45,streetscape}/lochergut*` und `data/raw/photos/lochergut/` (nicht im Repo). Nur zum Ansehen und Messen, keine Textur- oder Modellübernahme. SWISSIMAGE: swisstopo OGD (Quelle swisstopo).

## Befunde (aus Fotos und SWISSIMAGE)
- Sockel (Zentrum Lochergut): ca. 106 x 25 m, drei Teilstrecken leicht geknickt (SW-Ecke 30/-926, SE-Ecke 128/-959). Erdgeschoss voll verglast, Obergeschoss helle gerippte Metallverkleidung, darüber weisse Leuchtschrift «ZENTRUM LOCHERGUT» (nachts rosa-weiss, Foto 75).
- Dach des Sockels (SWISSIMAGE 10 cm): begrünte Kreisflächen (Ø ca. 3.5 m) mit Oberlichtern im versetzten Raster, hellgrauer Randstreifen.
- Coop (OSM 58/-927) mit Fassadenband weiss, Schrift orange (Foto 70); daneben Apotheke, Grand Café, Blumen Haab, Bank Cler. Im Spiel nur die Namen als freie Schrift, keine Logos.
- Scheiben: Enden cremegelb/beige (#cdbb8c), Längsfassaden helle Betonbänder mit dunklen Fensterbändern und Sonnenstoren; Seebahnstrasse-Seite dunkler braungrau (Fotos 30-43).
- Platz: breiter Gehweg unter dem Vordach, Baumstreifen mit Velobügeln, zwei Tramperrons (Lochergut, Tram 2/3/8/9/14), Mast mit Haltestellenschild, Wartehäuschen mit Sitzbank.
- Hof nördlich: Sandsteinbrunnen mit Bronzeplastik, Kopfsteinpflaster (Fotos 13, 72); Zahlenzug (Steinquader mit Jahreszahlen) an der Seebahnstrasse bei 140/-957 (Fotos 25-27, Commons-Koordinate der Kamera 152/-955).
- Strassenschild Bertastrasse bei 18/-954 (Commons-Koordinate).

## Im Spiel umgesetzt
- `pipeline/landmarks/lochergut_v2.py` (ersetzt `k45_lochergut.py` als Generator; gleiche GLB `lochergut.glb`): Ladenschilder an OSM-Positionen, Gründach mit Oberlichtern, Rippen am Fassadenband, Farben der Scheiben.
- `pipeline/overrides/places_detail_lochergut.json`: Gehweg-Band vor dem Sockel, Brunnen im Hof, Zahlenzug-Quader, Strassenschild, Blumenstand, Einkaufswagen-Unterstand.

## Referenzfotos (83)

| # | Datei | Quelle / Lizenz |
|---|---|---|
| 0 | `places_k45/lochergut/01.jpg` | Commons File:Zuerich Hochhaus Lochergut Helikopter.jpg, CC BY-SA 3.0, Ikiwaner, https://commons.wikimedia.org/wiki/File:Zuerich_Hochhaus_Lochergut_Helikopter.jpg |
| 1 | `places_k45/lochergut/02.jpg` | Commons File:Lochergut Einkaufszentrum Zürich (pm., dvdb).jpg, CC BY-SA 3.0, Dodo von den Bergen, https://commons.wikimedia.org/wiki/File:Lochergut_Einkaufszentrum_Z%C3%BCrich_(pm.,_dvdb).jpg |
| 2 | `places_k45/lochergut/03.jpg` | Commons File:Lochergut Zürich.JPG, CC BY-SA 3.0, Tschubby, https://commons.wikimedia.org/wiki/File:Lochergut_Z%C3%BCrich.JPG |
| 3 | `places_k45/lochergut/04.jpg` | Commons File:Impression - Statistisches Quartier Hard - Zürich - Bild 8.JPG, CC BY-SA 4.0, Martin E. Walder, https://commons.wikimedia.org/wiki/File:Impression_-_Statistisches_Quartier_Hard_-_Z%C3%BCrich_-_Bild_8.JPG |
| 4 | `places_k45/lochergut/05.jpg` | Commons File:Lochergut 2020.JPG, CC BY-SA 3.0, Tschubby, https://commons.wikimedia.org/wiki/File:Lochergut_2020.JPG |
| 5 | `places_k45/lochergut/06.jpg` | Commons File:Lochergut - panoramio.jpg, CC BY-SA 3.0, gertrudis2010, https://commons.wikimedia.org/wiki/File:Lochergut_-_panoramio.jpg |
| 6 | `places_k45/lochergut/07.jpg` | Commons File:Ghostbike Lochergut.jpg, CC BY-SA 4.0, Captaininler, https://commons.wikimedia.org/wiki/File:Ghostbike_Lochergut.jpg |
| 7 | `places_k45/lochergut/08.jpg` | Commons File:2013-05-05 Zuriko (Foto Dietrich Michael Weidmann) 101.JPG, CC BY-SA 3.0, Dietrich Michael Weidmann, https://commons.wikimedia.org/wiki/File:2013-05-05_Zuriko_(Foto_Dietrich_Michael_Weidmann)_101.JPG |
| 8 | `places_k45/lochergut/09.jpg` | Commons File:Lochergut, Zurich - panoramio.jpg, CC BY-SA 3.0, gertrudis2010, https://commons.wikimedia.org/wiki/File:Lochergut,_Zurich_-_panoramio.jpg |
| 9 | `places_k45/lochergut/10.jpg` | Commons File:Lochergut (24617550841).jpg, CC BY 2.0, Thomas8047, https://commons.wikimedia.org/wiki/File:Lochergut_(24617550841).jpg |
| 10 | `v3/lochergut/cm_2013_05_05_Zuriko_Foto_Dietrich_Michael_Weidmann_101_JPG.jpg` | commons, CC BY-SA 3.0, Dietrich Michael Weidmann https://commons.wikimedia.org/wiki/File:2013-05-05_Zuriko_(Foto_Dietrich_Michael_Weidmann)_101.JPG |
| 11 | `v3/lochergut/cm_Aussersihl_2015_HAL_011715_jpg.jpg` | commons, CC BY-SA 4.0, Juliet Haller https://commons.wikimedia.org/wiki/File:Aussersihl_2015_HAL_011715.jpg |
| 12 | `v3/lochergut/cm_December_afternoon_15877764370_jpg.jpg` | commons, CC BY 2.0, Thomas8047 https://commons.wikimedia.org/wiki/File:December_afternoon_(15877764370).jpg |
| 13 | `v3/lochergut/cm_Fountain_Lochergut_jpg.jpg` | commons, CC BY-SA 4.0, Katja Hottingen https://commons.wikimedia.org/wiki/File:Fountain_Lochergut.jpg |
| 14 | `v3/lochergut/cm_Ghostbike_Lochergut_jpg.jpg` | commons, CC BY-SA 4.0, Captaininler https://commons.wikimedia.org/wiki/File:Ghostbike_Lochergut.jpg |
| 15 | `v3/lochergut/cm_Impression_Statistisches_Quartier_Hard_Z_rich_Bild_8_JPG.jpg` | commons, CC BY-SA 4.0, Martin E. Walder https://commons.wikimedia.org/wiki/File:Impression_-_Statistisches_Quartier_Hard_-_Z%C3%BCrich_-_Bild_8.JPG |
| 16 | `v3/lochergut/cm_Kindergarten_Lochergut_2019_JPG.jpg` | commons, CC BY-SA 3.0, Tschubby https://commons.wikimedia.org/wiki/File:Kindergarten_Lochergut_2019.JPG |
| 17 | `v3/lochergut/cm_Lochergut_2020_JPG.jpg` | commons, CC BY-SA 3.0, Tschubby https://commons.wikimedia.org/wiki/File:Lochergut_2020.JPG |
| 18 | `v3/lochergut/cm_Lochergut_24617550841_jpg.jpg` | commons, CC BY 2.0, Thomas8047 https://commons.wikimedia.org/wiki/File:Lochergut_(24617550841).jpg |
| 19 | `v3/lochergut/cm_Lochergut_Einkaufszentrum_Z_rich_pm_dvdb_jpg.jpg` | commons, CC BY-SA 3.0, Dodo von den Bergen https://commons.wikimedia.org/wiki/File:Lochergut_Einkaufszentrum_Z%C3%BCrich_(pm.,_dvdb).jpg |
| 20 | `v3/lochergut/cm_Lochergut_Z_rich_JPG.jpg` | commons, CC BY-SA 3.0, Tschubby https://commons.wikimedia.org/wiki/File:Lochergut_Z%C3%BCrich.JPG |
| 21 | `v3/lochergut/cm_Lochergut_panoramio_jpg.jpg` | commons, CC BY-SA 3.0, gertrudis2010 https://commons.wikimedia.org/wiki/File:Lochergut_-_panoramio.jpg |
| 22 | `v3/lochergut/cm_Strassenschild_Bertastrasse_jpg.jpg` | commons, CC BY-SA 4.0, Captaininler https://commons.wikimedia.org/wiki/File:Strassenschild_Bertastrasse.jpg |
| 23 | `v3/lochergut/cm_Wohnsiedlung_Erismannhof_HAL_011715_cropped_jpg.jpg` | commons, CC BY-SA 4.0, Juliet Haller https://commons.wikimedia.org/wiki/File:Wohnsiedlung_Erismannhof_HAL_011715_(cropped).jpg |
| 24 | `v3/lochergut/cm_Z_risch_2015_HAL_011784_jpg.jpg` | commons, CC BY-SA 4.0, Juliet  Haller https://commons.wikimedia.org/wiki/File:Z%C3%BCrisch_2015_-_HAL_011784.jpg |
| 25 | `v3/lochergut/cm_Zahlenzug_frontal_jpg.jpg` | commons, CC BY-SA 4.0, Captaininler https://commons.wikimedia.org/wiki/File:Zahlenzug_frontal.jpg |
| 26 | `v3/lochergut/cm_Zahlenzug_oben_jpg.jpg` | commons, CC BY-SA 4.0, Captaininler https://commons.wikimedia.org/wiki/File:Zahlenzug_oben.jpg |
| 27 | `v3/lochergut/cm_Zahlenzug_unten_jpg.jpg` | commons, CC BY-SA 4.0, Captaininler https://commons.wikimedia.org/wiki/File:Zahlenzug_unten.jpg |
| 28 | `v3/lochergut/ml_1035270424697985.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=1035270424697985 |
| 29 | `v3/lochergut/ml_1134240140970652.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=1134240140970652 |
| 30 | `v3/lochergut/ml_1140313250652160.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=1140313250652160 |
| 31 | `v3/lochergut/ml_1197680381369073.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=1197680381369073 |
| 32 | `v3/lochergut/ml_1219462132412496.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=1219462132412496 |
| 33 | `v3/lochergut/ml_1270034073929617.jpg` | mapillary, CC BY-SA 4.0, lto https://www.mapillary.com/app/?pKey=1270034073929617 |
| 34 | `v3/lochergut/ml_1420360902301795.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=1420360902301795 |
| 35 | `v3/lochergut/ml_1973177566472783.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=1973177566472783 |
| 36 | `v3/lochergut/ml_321232900650843.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=321232900650843 |
| 37 | `v3/lochergut/ml_3628217567432557.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=3628217567432557 |
| 38 | `v3/lochergut/ml_402350025988414.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=402350025988414 |
| 39 | `v3/lochergut/ml_432932986297708.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=432932986297708 |
| 40 | `v3/lochergut/ml_657044993121673.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=657044993121673 |
| 41 | `v3/lochergut/ml_850457193637856.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=850457193637856 |
| 42 | `v3/lochergut/ml_919589745807108.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=919589745807108 |
| 43 | `v3/lochergut/ml_971315311184796.jpg` | mapillary, CC BY-SA 4.0, Yha1 https://www.mapillary.com/app/?pKey=971315311184796 |
| 44 | `v3/lochergut/px_fe1ca208-c6f.jpg` | panoramax, CC-BY-SA-4.0, stillhart https://api.panoramax.xyz/#focus=pic&pic=fe1ca208-c6f8-4db4-8237-b45513e9be87 |
| 45 | `streetscape/Lochergut/059_Ghostbike_Lochergut_jpg.jpg` | Commons (streetscape-Sammlung, Datei = Commons-Titel) |
| 46 | `streetscape/Lochergut/104_Lochergut_2020_JPG.jpg` | Commons (streetscape-Sammlung, Datei = Commons-Titel) |
| 47 | `streetscape/Lochergut/105_Lochergut_Zürich_JPG.jpg` | Commons (streetscape-Sammlung, Datei = Commons-Titel) |
| 48 | `lochergut/c00.jpg` | Commons File:Ghostbike Lochergut.jpg, CC BY-SA 4.0, Captaininler, https://commons.wikimedia.org/wiki/File:Ghostbike_Lochergut.jpg |
| 49 | `lochergut/c01.jpg` | Commons File:Impression - Statistisches Quartier Hard - Zürich - Bild 8.JPG, CC BY-SA 4.0, Martin E. Walder, https://commons.wikimedia.org/wiki/File:Impression_-_Statistisches_Quartier_Hard_-_Z%C3%BCrich_-_Bild_8.JPG |
| 50 | `lochergut/c02.jpg` | Commons File:Lochergut - panoramio.jpg, CC BY-SA 3.0, gertrudis2010, https://commons.wikimedia.org/wiki/File:Lochergut_-_panoramio.jpg |
| 51 | `lochergut/c03.jpg` | Commons File:Lochergut 2020.JPG, CC BY-SA 3.0, Tschubby, https://commons.wikimedia.org/wiki/File:Lochergut_2020.JPG |
| 52 | `lochergut/c04.jpg` | Commons File:Lochergut Einkaufszentrum Zürich (pm., dvdb).jpg, CC BY-SA 3.0, Dodo von den Bergen, https://commons.wikimedia.org/wiki/File:Lochergut_Einkaufszentrum_Z%C3%BCrich_(pm.,_dvdb).jpg |
| 53 | `lochergut/c05.jpg` | Commons File:Lochergut Zürich.JPG, CC BY-SA 3.0, Tschubby, https://commons.wikimedia.org/wiki/File:Lochergut_Z%C3%BCrich.JPG |
| 54 | `lochergut/c06.jpg` | Commons File:Lochergut-Überbauung Zürich.jpg, CC BY-SA 3.0, www.mikkostamm.com (Mikkostamm at de.wikipedia), https://commons.wikimedia.org/wiki/File:Lochergut-%C3%9Cberbauung_Z%C3%BCrich.jpg |
| 55 | `lochergut/c07.jpg` | Commons File:Lochergut.jpg, Public domain, René Nyffenegger at de.wikipedia, https://commons.wikimedia.org/wiki/File:Lochergut.jpg |
| 56 | `lochergut/c08.jpg` | Commons File:Zuerich Hochhaus Lochergut Helikopter.jpg, CC BY-SA 3.0, Ikiwaner, https://commons.wikimedia.org/wiki/File:Zuerich_Hochhaus_Lochergut_Helikopter.jpg |
| 57 | `lochergut/c10.jpg` | Commons File:Aussersihl Badenerstr49.JPG, CC BY-SA 3.0, Paebi, https://commons.wikimedia.org/wiki/File:Aussersihl_Badenerstr49.JPG |
| 58 | `lochergut/c11.jpg` | Commons File:Aussersihl Badenerstr67.JPG, CC BY-SA 3.0, Paebi, https://commons.wikimedia.org/wiki/File:Aussersihl_Badenerstr67.JPG |
| 59 | `lochergut/c16.jpg` | Commons File:Badenerstrasse 75 in Zürich.jpg, CC BY 4.0, Balise42, https://commons.wikimedia.org/wiki/File:Badenerstrasse_75_in_Z%C3%BCrich.jpg |
| 60 | `lochergut/c17.jpg` | Commons File:Brunnen Badenerstrasse Ecke Kalkbreitestrasse, Zürich 2019.jpg, CC BY-SA 4.0, SophiaHenke, https://commons.wikimedia.org/wiki/File:Brunnen_Badenerstrasse_Ecke_Kalkbreitestrasse,_Z%C3%BCrich_2019.jpg |
| 61 | `lochergut/c18.jpg` | Commons File:Brunnen Sihlfeldstrasse Ecke Bertastrasse und Badenerstrasse, Zürich 2019.jpg, CC BY-SA 4.0, Katja Hottingen, https://commons.wikimedia.org/wiki/File:Brunnen_Sihlfeldstrasse_Ecke_Bertastrasse_und_Badenerstrasse,_Z%C3%BCrich_2019.jpg |
| 62 | `lochergut/c19.jpg` | Commons File:Lochergut, Zurich - panoramio.jpg, CC BY-SA 3.0, gertrudis2010, https://commons.wikimedia.org/wiki/File:Lochergut,_Zurich_-_panoramio.jpg |
| 63 | `lochergut/c20.jpg` | Commons File:Mapillary Zürich 1640896079862130 (u3iVcplwqT9IFZXPjQEbyA by fcignat – 2025-03-10 05H39M21S366) (cropped).jpg, CC BY-SA 4.0, fcignat , https://commons.wikimedia.org/wiki/File:Mapillary_Z%C3%BCrich_1640896079862130_(u3iVcplwqT9IFZXPjQEbyA_by_fcignat_%E2%80%93_2025-03-10_05H39M21S366)_(cropped).jpg |
| 64 | `lochergut/c21.jpg` | Commons File:Mapillary Zürich 1640896079862130 (u3iVcplwqT9IFZXPjQEbyA by fcignat – 2025-03-10 05H39M21S366).jpg, CC BY-SA 4.0, fcignat , https://commons.wikimedia.org/wiki/File:Mapillary_Z%C3%BCrich_1640896079862130_(u3iVcplwqT9IFZXPjQEbyA_by_fcignat_%E2%80%93_2025-03-10_05H39M21S366).jpg |
| 65 | `lochergut/c23.jpg` | Commons File:VBZ Be 4-6 1664 Lochergut 230509.jpg, CC BY-SA 3.0, NAC, https://commons.wikimedia.org/wiki/File:VBZ_Be_4-6_1664_Lochergut_230509.jpg |
| 66 | `lochergut/c26.jpg` | Commons File:Zuerich-vbz-tram-14-be-663566.jpg, Attribution, Kurt Rasmussen, https://commons.wikimedia.org/wiki/File:Zuerich-vbz-tram-14-be-663566.jpg |
| 67 | `lochergut/c27.jpg` | Commons File:Zuerich-vbz-tram-2-be-632731.jpg, Attribution, Kurt Rasmussen, https://commons.wikimedia.org/wiki/File:Zuerich-vbz-tram-2-be-632731.jpg |
| 68 | `lochergut/c28.jpg` | Commons File:Zuerich-vbz-tram-2-be-672057.jpg, Attribution, Kurt Rasmussen, https://commons.wikimedia.org/wiki/File:Zuerich-vbz-tram-2-be-672057.jpg |
| 69 | `lochergut/c29.jpg` | Commons File:Zuerich-vbz-tram-2-be-672063.jpg, Attribution, Kurt Rasmussen, https://commons.wikimedia.org/wiki/File:Zuerich-vbz-tram-2-be-672063.jpg |
| 70 | `lochergut/c30.jpg` | Commons File:Zuerich-vbz-tram-2-bombardieralstom-884940.jpg, Attribution, Kurt Rasmussen, https://commons.wikimedia.org/wiki/File:Zuerich-vbz-tram-2-bombardieralstom-884940.jpg |
| 71 | `lochergut/c31.jpg` | Commons File:Aussersihl 2015 HAL 011715.jpg, CC BY-SA 4.0, Juliet Haller, https://commons.wikimedia.org/wiki/File:Aussersihl_2015_HAL_011715.jpg |
| 72 | `lochergut/c32.jpg` | Commons File:Fountain Lochergut.jpg, CC BY-SA 4.0, Katja Hottingen, https://commons.wikimedia.org/wiki/File:Fountain_Lochergut.jpg |
| 73 | `lochergut/c33.jpg` | Commons File:Kindergarten Lochergut 2019.JPG, CC BY-SA 3.0, Tschubby, https://commons.wikimedia.org/wiki/File:Kindergarten_Lochergut_2019.JPG |
| 74 | `lochergut/c34.jpg` | Commons File:Lochergut (24617550841).jpg, CC BY 2.0, Thomas8047, https://commons.wikimedia.org/wiki/File:Lochergut_(24617550841).jpg |
| 75 | `lochergut/c35.jpg` | Commons File:Lochergut - panoramio - gertrudis2010.jpg, CC BY-SA 3.0, gertrudis2010, https://commons.wikimedia.org/wiki/File:Lochergut_-_panoramio_-_gertrudis2010.jpg |
| 76 | `lochergut/c42.jpg` | Commons File:Hard Sihlfeld Turnhalle.JPG, CC BY-SA 3.0, Paebi, https://commons.wikimedia.org/wiki/File:Hard_Sihlfeld_Turnhalle.JPG |
| 77 | `lochergut/c43.jpg` | Commons File:Sihlfeldstrasse - panoramio.jpg, CC BY-SA 3.0, gertrudis2010, https://commons.wikimedia.org/wiki/File:Sihlfeldstrasse_-_panoramio.jpg |
| 78 | `lochergut/c44.jpg` | Commons File:Sihlfeldstrasse.jpg, CC BY-SA 3.0, UCaetano, https://commons.wikimedia.org/wiki/File:Sihlfeldstrasse.jpg |
| 79 | `lochergut/c46.jpg` | Commons File:Seebahnstrasse 85.JPG, CC BY-SA 3.0, Tschubby, https://commons.wikimedia.org/wiki/File:Seebahnstrasse_85.JPG |
| 80 | `lochergut/c47.jpg` | Commons File:Zahlenzug frontal.jpg, CC BY-SA 4.0, Captaininler, https://commons.wikimedia.org/wiki/File:Zahlenzug_frontal.jpg |
| 81 | `lochergut/c48.jpg` | Commons File:Zahlenzug oben.jpg, CC BY-SA 4.0, Captaininler, https://commons.wikimedia.org/wiki/File:Zahlenzug_oben.jpg |
| 82 | `lochergut/c49.jpg` | Commons File:Zahlenzug unten.jpg, CC BY-SA 4.0, Captaininler, https://commons.wikimedia.org/wiki/File:Zahlenzug_unten.jpg |

## Passerelle entfernt (User-Rückmeldung)
Ursache: OSM-Fusswege `bridge=yes` (Way 284686661 bei 194/-994, 547047231 bei 201/-1015) neben der Badenerstrasse-Brücke über das SBB-Gleisfeld wurden als eigenes erhöhtes Deck ohne Anschluss gezeichnet (`pipeline/bridges.py`). Fix: Ausschluss in `pipeline/overrides/lochergut_excl.json` (Hook `# lochergut` in `bridge_ways`); Kacheln 0_-5 und 1_-5 neu gebaut. Die Strassenbrücke selbst bleibt.

## Leuchtschrift «LOCHERGUT»
- Befund aus Fotos (Nr. 52 Tag, Nr. 75 Nacht): Leuchtkasten mit Blockbuchstaben «LOCHERGUT» auf dem Dach des Sockels, ca. 16 x 2.5 m, auf Stützen ca. 1 m über dem Dach, tagsüber weiss, nachts magenta/rosa leuchtend (linkes Ende rötlich). Kleine Beschriftung «ZENTRUM LOCHERGUT» an der Fassade unten links.
- Webrecherche (Stadt Zürich Siedlungsdokumentation, world-architects, Suchanfragen) fand nichts zu Farbfolge oder Takt. Die Farbfolge ist deshalb eine Annahme: langsamer Verlauf Violett, Magenta, Rosa, Rot-Rosa, Periode 36 s.
- Umsetzung: eigenes Mesh mit Material `lochergut_neon` in `lochergut.glb` (`lochergut_v2.py`, `neon_tex`), Animation per Hook `// lochergut-neon` in `web/src/world/landmarks3d.ts` (emissive Farbe über `nightUniform`, tagsüber schwach, keine Allokation pro Frame). Nachtprüfung `preview/lochergut_neon.jpg`.
