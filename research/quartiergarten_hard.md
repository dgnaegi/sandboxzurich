# Quartiergarten Hard (Aussenansicht)

**Lage:** Bullingerstrasse 90, 8004 Zürich (Quartier Hard, Kreis 4; Fuss der Hardau-Hochhäuser, zwischen Familiengartenareal Hard/Gartenareal Aussersihl im NW, Sporthalle/Schulhaus Hardau im SE, VBZ-Depot Hardau jenseits der Bullingerstrasse). Verein Quartiergarten Hard, seit 2013, keine privaten Beete, Gäste täglich 8-20 Uhr willkommen, «kein öffentlicher Park». Im Spielgebiet: lokal ca. x -674..-576, y -192..-78, Ankerpunkt (-640, -130). Quelle Adresse/Regeln: quartiergarten-hard.ch (Website nur angesehen), Blick-Parkliste. Nicht in Kreis 5, sondern Kreis 4 (Auftrag sagte Kreis 5/Hardturm; die «Stadionbrache Hardturm» ist ein anderes Projekt).

## Fotos
85 Referenzfotos (nur Referenz, nie Textur): `data/raw/photos/qgh/` (nicht im Repo), Metadaten `research/quartiergarten_hard_photos.json`, Kontaktbogen `preview/ref_qgh.jpg` (32 Auswahl). Mapillary (CC BY-SA 4.0, Autoren Lezurex/Yha1/bjoernwider/sunflower/ramap/fifi u. a.; 360-Aufnahmen als perspektivische Ausschnitte), Panoramax (CC BY-SA 4.0, 2025, Velo-Kamera in der Bullingerstrasse), Commons (Umgebung: Letzigrund, VBZ-Busse; CC BY/BY-SA). Der Garten ist nur von der Strasse sichtbar (kein Bild aus dem Inneren auf Mapillary/Panoramax/Commons), daher «von aussen».

## Beobachtungen (Panoramax 2025, Frühling)
- Strassenseite: Rundholz-Schranke (Pfosten ~16 cm, 2 Querbalken ~0.45/0.85 m), dahinter Wildwiese mit Brennnessel/Beinwell-Streifen; Baumreihe mit Baumscheiben auf dem Trottoir.
- Weisse Grossbuchstaben «QUARTIERGARTEN» auf einem Brett am Zaun neben dem Holzhaus (Text frei, kein Logo; Foto #65, #69, #74).
- Dunkelbraunes Holzhaus (Chalet, Satteldach, Solarpanel) an der Strassenecke (swissBUILDINGS3D-Gebäude ID_8D055786, im Spiel ersetzt).
- Kies-/Schotterplatz mit Drahtgitterzaun und Schranke am SE-Ende (Foto #83).
- NW-Grenze: Maschendrahtzaun zu den Familiengärten, bewachsen.
- SWISSIMAGE (Ortho): Beetreihen in der Mitte, Kiesweg in Kurve, ein grosses Geräte-/Lagerhaus, Folien-Gewächshaus, offener Unterstand mit Feuerstelle, Wassertanks (IBC), Planen/Mulchhaufen, Sandspielfläche, wilde Ecke NE, Rondell mit Baum.

## Annahmen (nicht per Foto belegt)
Hochbeete beim Eingang, Komposter aus Paletten, Sitzgelegenheiten, Schilder-Texte, genaue Zaunhöhen: übliche Elemente von Zürcher Gemeinschaftsgärten; Texte frei erfunden und neutral (kein Logo).

## Umsetzung
`pipeline/landmarks/qgh.py` (+ `qgh_plants.py` Alpha-Karten-Atlas 512x512, Layout in Ortho-Pixeln), Override `pipeline/overrides/landmarks_qgh.json` (Modell `qgh.glb`, Chalet-Gebäude versteckt, Collider für Hütten/Tanks/Zäune), `yards_excl_qgh.json` (keine generischen Familiengarten-Hütten/Hecken/Sträucher im Garten, Filter `_apply_excl` in `pipeline/yards.py`), `tree_excl_qgh.json`. Referenzvergleich `preview/qgh_cmp.jpg`.

## Lizenzliste
| # | Quelle | Lizenz | Autor | URL |
|---|---|---|---|---|
| 0 | mapillary | CC BY-SA 4.0 | bjoernwider | https://www.mapillary.com/app/?pKey=309507827462658 |
| 1 | mapillary | CC BY-SA 4.0 | Yha1 | https://www.mapillary.com/app/?pKey=1075661403924348 |
| 2 | mapillary | CC BY-SA 4.0 | sunflower | https://www.mapillary.com/app/?pKey=173357884668571 |
| 3 | mapillary | CC BY-SA 4.0 | fifi | https://www.mapillary.com/app/?pKey=736047570405514 |
| 4 | mapillary | CC BY-SA 4.0 | Yha1 | https://www.mapillary.com/app/?pKey=1028306175713368 |
| 5 | mapillary | CC BY-SA 4.0 | Yha1 | https://www.mapillary.com/app/?pKey=2264974067184852 |
| 6 | mapillary | CC BY-SA 4.0 | ramap | https://www.mapillary.com/app/?pKey=758765134794491 |
| 7 | commons | CC BY-SA 4.0 | Captaininler | https://commons.wikimedia.org/wiki/File:Wand_Ding.jpg |
| 8 | commons | CC BY-SA 4.0 | Captaininler | https://commons.wikimedia.org/wiki/File:Beschreibung_Wand_Ding.jpg |
| 9 | commons | CC BY 4.0 | hrs51 | https://commons.wikimedia.org/wiki/File:Z%C3%BCrcher_Verkehrsbetriebe_gestern_und_heute._Mercedes_Citaro_(Baujahr_2008)_und_FBW_(_Baujahr_1954).jpg |
| 10 | commons | CC BY 2.0 | hrs51 | https://commons.wikimedia.org/wiki/File:Tram_Museum_Z%C3%BCrich_-_Tag_der_historischen_Busse_-_Saurer_4_ZP_(20._August_2017).jpg |
| 11 | commons | CC BY-SA 3.0 | Tschubby | https://commons.wikimedia.org/wiki/File:Kindergarten_Herdern.jpg |
| 12 | commons | CC BY-SA 3.0 | Port(u*o)s | https://commons.wikimedia.org/wiki/File:Restaurant_Schlachthof.JPG |
| 13 | commons | CC BY-SA 3.0 | Port(u*o)s | https://commons.wikimedia.org/wiki/File:Widderbrunnen.JPG |
| 14 | commons | CC BY 2.0 | hrs51 | https://commons.wikimedia.org/wiki/File:Tram_Museum_Z%C3%BCrich_-_Tag_der_historischen_Busse_-_Saurer_V_45_(20._August_2017).jpg |
| 15 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=966346119529015 |
| 16 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=970816362441791 |
| 17 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=1763098687992141 |
| 18 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=1014851497892286 |
| 19 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=2056700761726077 |
| 20 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=1343123081052413 |
| 21 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=1692783878724325 |
| 22 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=955471220701279 |
| 23 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=995050093205069 |
| 24 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=1696555345020060 |
| 25 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=900220269697057 |
| 26 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=997934496260587 |
| 27 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=952708817588892 |
| 28 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=27116173871348160 |
| 29 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=1726309701704737 |
| 30 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=1510097053801013 |
| 31 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=1335638061801238 |
| 32 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=867643572320857 |
| 33 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=941848815325260 |
| 34 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=1509684337610477 |
| 35 | mapillary | CC BY-SA 4.0 | Yha1 | https://www.mapillary.com/app/?pKey=929852538978005 |
| 36 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=1489771722823334 |
| 37 | mapillary | CC BY-SA 4.0 | bjoernwider | https://www.mapillary.com/app/?pKey=505210020610410 |
| 38 | mapillary | CC BY-SA 4.0 | ramap | https://www.mapillary.com/app/?pKey=142691777840245 |
| 39 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=1026281039743894 |
| 40 | mapillary | CC BY-SA 4.0 | bjoernwider | https://www.mapillary.com/app/?pKey=185814686638922 |
| 41 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=3229456340775165 |
| 42 | mapillary | CC BY-SA 4.0 | Yha1 | https://www.mapillary.com/app/?pKey=836527121985116 |
| 43 | mapillary | CC BY-SA 4.0 | sunflower | https://www.mapillary.com/app/?pKey=903264750245254 |
| 44 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=1996967464243816 |
| 45 | mapillary | CC BY-SA 4.0 | bjoernwider | https://www.mapillary.com/app/?pKey=437687153977408 |
| 46 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=2433686610390461 |
| 47 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=2442767876242746 |
| 48 | mapillary | CC BY-SA 4.0 | sp8962de | https://www.mapillary.com/app/?pKey=324045325754437 |
| 49 | mapillary | CC BY-SA 4.0 | kashifmukh | https://www.mapillary.com/app/?pKey=251376680070982 |
| 50 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=1932559734092702 |
| 51 | mapillary | CC BY-SA 4.0 | sunflower | https://www.mapillary.com/app/?pKey=493989245281389 |
| 52 | mapillary | CC BY-SA 4.0 | bjoernwider | https://www.mapillary.com/app/?pKey=920986985365352 |
| 53 | mapillary | CC BY-SA 4.0 | Yha1 | https://www.mapillary.com/app/?pKey=1055107316323545 |
| 54 | mapillary-360crop | CC BY-SA 4.0 | Lezurex | https://www.mapillary.com/app/?pKey=962320316430159 |
| 55 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=56851877-617e-42d7-9670-a1b6c1c112a2 |
| 56 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=6c136d79-308c-4eb3-8913-285495c8312b |
| 57 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=8625071b-9c7f-434b-8c83-94333d65f82c |
| 58 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=358af94f-ec08-4c3d-a055-01bd515f9925 |
| 59 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=80a6f719-133a-4253-a5af-84218a5ba9ba |
| 60 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=56011d76-19b0-4668-aa6f-4681aaad5b3d |
| 61 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=e6cf1c10-aaf0-4e5b-9eb9-d521598f18ca |
| 62 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=9feae0b6-79b2-40f5-bc7c-a5859c23a4aa |
| 63 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=92670e1e-14b2-47dc-9a6b-64f62be8c7d3 |
| 64 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=eb2c1ef2-36e4-4a75-96f5-fc7f495d6eb8 |
| 65 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=fcd5c21b-7f6b-4eae-99ec-b60c1e0044c3 |
| 66 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=781b23a4-f91a-462c-aee4-037fca2dcce8 |
| 67 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=e4d2fdc2-db7c-4561-a5f9-4088363f6544 |
| 68 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=5b09adb8-99b1-471a-8a7b-8df5d64da2ee |
| 69 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=2138c6f7-aaad-440f-a910-819e3e0fb4cd |
| 70 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=45a40f78-0b18-4b0b-a4a1-68baceec35df |
| 71 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=a9dbbd80-f1fb-4f2f-bb92-724a788ffe69 |
| 72 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=4b78df9d-a8a6-47ef-b172-bd37da6ee824 |
| 73 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=c2c5aca6-f040-4063-9fee-2c7e30fa56d6 |
| 74 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=c1f804ca-a8d6-465b-98d0-8fb654086a48 |
| 75 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=ca6af0ff-842f-4ba1-9c10-2961aea8be10 |
| 76 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=4b9bdb59-cfad-4f32-9569-ce3a64a97957 |
| 77 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=e1828a4e-216a-429b-97a4-49b5337ca270 |
| 78 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=2f7349ed-330d-42e5-b6f6-8f8e7f1603b5 |
| 79 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=bb276bae-3593-408e-875a-2e4eba7b3bf5 |
| 80 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=01e5bb69-6786-433a-a481-2b1d59517772 |
| 81 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=99f56ec6-a9d9-477c-ba38-a4c41cf60c82 |
| 82 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=abdc547b-9f59-4285-bdd6-caeb26d386da |
| 83 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=6eac0240-b315-4de2-9202-71783c47386a |
| 84 | panoramax | CC-BY-SA-4.0 | unknown | https://api.panoramax.xyz/#focus=pic&pic=fe1f336c-b772-4ec7-96a9-160d3c52a2f4 |
