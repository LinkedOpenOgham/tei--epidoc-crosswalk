# PRIMER: tei--epidoc-crosswalk

Arbeitsplan für das Repository `LinkedOpenOgham/tei--epidoc-crosswalk` (Achse 1: strukturelle Interoperabilität). Wird zu Beginn jedes Chats hochgeladen und am Ende zurückgeschrieben. Alles Nach-außen-Sichtbare (Code, README, Ontologie, Docs) ist britisches Englisch, dieses Dokument ist deutsch.

Stand: 2026-11-01, Release 0.2.0. Das Repo wurde ohne PRIMER angelegt; dieser ist beim ersten Patch (S1 bis S6) entstanden.

---

# Teil A: Immer gültig

## A1 Ausgangslage

| Repo | Rolle | Stand |
|---|---|---|
| `LinkedOpenOgham/tei--epidoc-crosswalk` | dieses Repo: OG(H)AM-EpiDoc nach CIDOC CRM / CRMtex, Orts-, Halter-, Wort- und Lesungsschicht, Pages | 0.2.0 |
| `LinkedOpenOgham/tei--epidoc-amt` | Achse 2: gewichtete Aussagen mit AMT, hat eine eigene `STONES`-Liste | nicht angefasst |
| `lguariento/og-h-am` | die Editionen (Quelle), per `--fetch-corpus` nach `data/origin/` | hier gepinnt auf `bb62ccd` (2026-07-02), 504 Editionen; Upstream steht inzwischen bei `9a68afd` |
| `florianthiery/poster-kit` | Poster CAA UK 2026, nutzt die Zahlen dieses Repos | nur gelesen |

Nicht neu bauen: Ortsschicht, Halterschicht, Wortschicht, Lesungsansicht, Ontologie-Patch, SHACL-Prüfung. Sie liefen vor diesem Patch und sind unverändert.

**Befunde** (geprüft 2026-11-01):

- **Der Build ist in der Sandbox reproduzierbar, aber nicht uhrfrei.** Mit `--offline --no-fetch` gegen den Corpus-Stand `bb62ccd` stimmt die Ausgabe mit dem eingecheckten Stand überein, bis auf drei Stellen, an denen eine Uhr in der Ausgabe steht: `prov:generatedAtTime` in `out/places.crm.ttl`, der Satz „Generated <Datum>" in `docs/*.html`, und das Datum in `ontologies/CHANGES.md`. Ein zweiter Lauf ändert daher `out/places.crm.ttl`. Das war schon vorher so, siehe S9.
- **Die drei neuen Steine und das Poster.** Die Zählung (Transliteration plus Apparat) stimmt mit dem Poster überein: Dyke 12 `unclear`, 9 `gap`, 3 `choice`, 1 `app`; Blackwaterfoot 1: 2 `unclear`, 3 `gap`, 1 `choice`, 9 `app`, 6 `rdg`; Bishop Loch: 2 `gap`, 1 `app`; Garranes: 3 `supplied`. Geprüft mit `context/scripts/count_doubt.py` und mit `doubt_profile()`.
- **Bishop Loch hat zwei Koordinaten, aber nur einen Fundort.** `<geo>` im Provenienz-Teil (55.876389, -4.100278, Old Monkland, NS 68700 66800) ist der Fundort. `idno type="geo"` (55.946991, -3.1891831) liegt in Edinburgh und ist der Aufbewahrungsort (National Museums Scotland, Q1967502), den die Halterschicht ohnehin getrennt führt. Kein Konflikt, `geoStatus` ist `asserted`. Der einzige `app`-Eintrag ist eine Notiz zur Leserichtung, kein Zweifel am Befund.
- **Bishop Loch ist die Grenze der Methode.** Dass die Zeichen vielleicht kein Ogham sind, steht nur in Prosa („ogham-like markings", „the purported ogham inscription", „the alleged ogham inscription" in Provenienz, Zustand, Layout und Handnotiz). Das Markup kennt zwei Lücken. Das Zweifelsprofil liest sich daher als „wenig Zweifel" für den zweifelhaftesten Stein.
- **Fehler gefunden und behoben: erfundener Autor.** Ein `<rdg>` ohne `@source` bekam `prov:wasAttributedTo data:agent_x`, einen gemeinsamen Agenten, den es nicht gibt (der Slug von „" ist `x`). Betroffen war nur Blackwaterfoot 1 (drei Lesungen: Jackson 1973 steht dort nur in der Prosa der Notiz). Jetzt keine Attribution.
- **Noch offen: Blackwaterfoot 1 verliert Struktur.** Die Datei hat drei Inschriften (drei `transliteration`-Divisionen), das Einzelgraph-Modell nimmt die erste. Zwei `rdg` derselben Quelle (`FOR1996`: ADLEUV, BLUEDLA) landen auf **einem** Lesungsknoten mit zwei Labels. Und ein `<rdg>` im Apparat ist oft die Variante einer Buchstabengruppe, keine Lesung des ganzen Textes. Siehe D1.
- **`<origDate>` wird nicht ausgegeben**, obwohl `MAPPING` die Zeile führt und der generierte Text bis 0.1.0 behauptete, es gebe im Corpus keine. Stand `bb62ccd`: 502 `origDate`-Elemente in 502 Dateien, 134 davon mit Wert (Dyke: `cert="low"`, Blackwaterfoot 1: `precision="low"`). Siehe D2.
- **D9 (TX6/TX7) geklärt.** `MAPPING`, die Graphen und der Ontologie-Patch benutzen `ogham:Reading` (im gepatchten `ontologies/ogham.ttl` ⊑ `crmtex:TX7_Written_Text_Segment`, CRMtex 2.0 geprüft: es gibt `TX6_Transliteration` und `TX14_Reading`, aber keine `TX6_Transcription`). Veraltet war nur der Text: README (Mapping-Tabelle, SPARQL-Beispiel, Entscheidungsliste, Tabelle der Wort-Ausgabe), der generierte `out/README.md` und zwei Docstrings. Das veröffentlichte `ogham.owl` deklariert weiterhin `Reading ⊑ TX6_Transcription`; das ist Sache der Ontologie, nicht dieses Repos.
- **Das SPARQL-Beispiel der Lesungsansicht lief nie.** Es benutzte `crm:P128_carries` und `crmtex:TXP4_has_segment`, die der Graph nicht behauptet (er benutzt `ogham:carries` und `ogham:identifiedAs`, Unterrelationen ohne Inferenz nicht sichtbar), und einen Alias in `HAVING`. Jetzt gegen `out/` geprüft: Blackwaterfoot 1 (3 zugeschriebene Lesungen) und Gigha 1 (5).
- **Status der Fundstücke.** Corpus-weit: 456 `numbered`, 14 `lost`, 34 `doubtful` (stimmt mit der Poster-Zählung 34 X-Datensätze). Per Abfrage auf `places.crm.ttl`: England 5, Wales 12, Schottland 4, also 21 britische; Irland 12 statt 13, weil `I-FER-X01` in der Ortshierarchie kein Land trägt.

## A2 Zielbild

```
data/origin/ (OG(H)AM, gepinnt)    data/*.xml (sieben Beispielsteine)
   |                                  |
   | places / keepers / words /       | py/main.py: parse -> build_graph
   | dissent / persons / setting      |   recordStatus, Zweifelsprofil, Lesungen
   v                                  v
out/places.crm.ttl, words, ...     out/<stein>.crm.ttl     out/crosswalk.ttl
   \_______________ validate.py (A-Box gegen Ontologien) ______________/
                                   |
                       out/README.md, docs/ (Pages), element-docs/
```

Eigenschaften, die das Ergebnis haben muss:

1. Jeder Stein in `STONES` hat `data/<id>.xml`, `out/<name>.crm.ttl` und einen Abschnitt in `out/README.md`.
2. Jeder Stein-Knoten trägt `ogham:recordStatus`, jeder Einzelgraph zusätzlich die sechs Zählungen, und die Zählungen stimmen mit `count_doubt.py` überein.
3. Kein `<rdg>` ohne `@source` hat ein `prov:wasAttributedTo`.
4. Der A-Box-Check meldet keinen unbekannten Begriff (neue Terme sind in `py/ontology_patch.py` deklariert).
5. Zwei Läufe hintereinander ändern, abgesehen von den drei Uhr-Stellen (A1, S9), keine Datei.

## A3 Querschnittsregeln

- `data/` ist Eingabe, unverändert (die XMLs der Beispielsteine sind Kopien aus `data/origin`, gleicher Blob). Alles, was ein Skript daraus macht, liegt in `out/`, `docs/`, `element-docs/`.
- `out/`, `docs/`, `element-docs/` und `ontologies/CHANGES.md`/`ogham.ttl` sind generiert, werden eingecheckt, aber nie von Hand geändert und nicht im Patch-ZIP geliefert.
- Einziger Einstiegspunkt ist `python py/main.py` (Abweichung vom Familien-Skelett, das `main.py` im Wurzelverzeichnis hat; hier beschlossen, nicht umzubauen, siehe A4).
- Der Corpus wird nur im eigenen Schritt geholt (`--fetch-corpus`); `--offline --no-fetch` baut gegen das, was in `data/origin/` liegt. Der Stand steht im eingecheckten Manifest.
- Neue `ogham:`-Terme gehören nach `ADDITIONS` in `py/ontology_patch.py` (mit Domäne, Bereich, Kommentar) und sind als „Proposed term" zu kennzeichnen, solange die Ontologie sie nicht übernommen hat.
- Doppelte Edition: jede OG(H)AM-Datei trägt den Text zweimal (`subtype="ogham"`, `"transliteration"`) und den Apparat getrennt. Gezählt wird nur Transliteration plus Apparat.
- Keine Uhr in neuen Ausgaben. (Drei bestehende Stellen sind offen, S9.)
- Britisches Englisch außen, Deutsch hier. Befehle für Windows `cmd`, je eine Zeile.
- Änderungen kommen als Patch-ZIP (Skill `patch-zip-delivery`), nur Quellen, gegen eine frische Kopie des Originals geprüft.

## A4 Beschlusslage

| Frage | Beschluss | seit |
|---|---|---|
| Welche Steine kommen zusätzlich in `STONES`? | Dyke (`dyke`), Blackwaterfoot 1 (`blackwaterfoot-1`), Bishop Loch (`bishop-loch`); `tei--epidoc-amt` übernimmt dieselben Basisnamen | 2026-11-01 (Flo), Basisnamen Vorschlag |
| Status der Fundstücke abfragbar? | Ja, `ogham:recordStatus` ∈ {`numbered`, `lost`, `doubtful`}, aus der Serie der Kennung; in Einzelgraphen und `places.crm.ttl`; Name ist ein **Vorschlag**, mit dem Ontologie-Team abzustimmen | 2026-11-01 (Flo), Name Vorschlag |
| Zweifelsprofil im Graphen? | Sechs Zählungen am Stein-Knoten (`unclearCount`, `suppliedCount`, `gapCount`, `choiceCount`, `appCount`, `rdgCount`); Namen **Vorschlag** | Vorschlag 2026-11-01 |
| Grenze der Methode (Bishop Loch) | Wird im Repo-README und im generierten `out/README.md` ehrlich benannt; das Markup sieht Statuszweifel nicht | 2026-11-01 (Flo) |
| Lesungsklasse | `ogham:Reading`, im gepatchten Ontologie-Auszug ⊑ `crmtex:TX7_Written_Text_Segment`; kein `TX6_Transcription` | 2026-11-01 (Flo, D9 geklärt) |
| Lesung ohne `@source` | keine Attribution, kein erfundener Agent | Vorschlag 2026-11-01 |
| Bishop Loch: welche Koordinate? | `<geo>` im Provenienz-Teil ist der Fundort, `idno type="geo"` der Aufbewahrungsort | 2026-11-01 (aus den Daten) |
| Gewichte | keine in diesem Repo, `amt:weight` gehört nach `tei--epidoc-amt` | 2026-11-01 (Flo) |
| Corpus-Stand | bleibt `bb62ccd`; kein `--fetch-corpus` in diesem Patch, damit der Patch nur die eigenen Änderungen zeigt | 2026-11-01 |
| Skelett | `py/main.py` bleibt Einstiegspunkt, kein Umbau auf Familien-Skelett | Vorschlag 2026-11-01 |
| Versionsnummer | 0.2.0; 0.1.0 rückwirkend für den Stand davor | Vorschlag 2026-11-01 |

## A5 Was in welchem Chat hochgeladen wird

Das Bundle enthält Quellcode, Eingaben und die kleinen Ausgaben, nicht den Corpus-Klon und nicht die großen Tabellen:

```
robocopy . %TEMP%\crosswalk-bundle /E /XD .git .venv __pycache__ origin /XF *.csv *.geojson >nul & powershell -Command "Compress-Archive -Path $env:TEMP\crosswalk-bundle\* -DestinationPath crosswalk-bundle.zip -Force"
```

Nicht hochladen: `.venv/`, `.git/`, `data/origin/`, `docs/*.csv`, `out/*.csv`. Für Schritte am Ortslayer zusätzlich `out/places.csv`.

---

# Teil B: Schrittübersicht

| ID | Schritt | Repo | hängt ab von | Status |
|---|---|---|---|---|
| S0 | Festlegungen (Steine, Basisnamen, Termnamen) | crosswalk | | erledigt 2026-11-01 (teils Vorschlag) |
| S1 | PRIMER, CHANGELOG, CITATION | crosswalk | S0 | erledigt 2026-11-01 |
| S2 | Dyke, Blackwaterfoot 1, Bishop Loch aufnehmen | crosswalk | S0 | erledigt 2026-11-01 |
| S3 | `ogham:recordStatus` | crosswalk | S2 | erledigt 2026-11-01 |
| S4 | Zweifelsprofil am Stein | crosswalk | S2 | erledigt 2026-11-01 |
| S5 | D9: TX6 aus Text und Docstrings | crosswalk | | erledigt 2026-11-01 |
| S6 | Grenze der Methode dokumentieren | crosswalk | S4 | erledigt 2026-11-01 |
| S7 | Termnamen mit dem Ontologie-Team abstimmen | crosswalk / Ontologie | S3, S4 | offen |
| S8 | `<origDate>` abbilden (cert, precision) | crosswalk | S7 | offen |
| S9 | Uhr aus der Ausgabe nehmen | crosswalk | | offen |
| S10 | Übergabe an `tei--epidoc-amt` (Chat 3) | amt | S2 | offen |

S7, S8 und S9 sind voneinander unabhängig. S10 braucht nur S2 bis S4 und kann sofort beginnen.

---

# Teil C: Die Schritte

## S2 — Drei Steine aufnehmen

**Ziel:** Dyke, Blackwaterfoot 1 und Bishop Loch wie die vier Beispielsteine behandelt, mit Einzelgraph, Dokumentation und Pages.

**Abnahme:** `python py/main.py --offline --no-fetch` läuft ohne Fehler; `out/dyke.crm.ttl`, `out/blackwaterfoot-1.crm.ttl`, `out/bishop-loch.crm.ttl` existieren; `out/README.md` hat einen Abschnitt je Stein; die Einzelgraphen der vier alten Steine unterscheiden sich nur um die neuen Eigenschaften an der Stein-Knoten.

### Erledigt 2026-11-01

- Die XMLs sind Kopien aus `data/origin` (`cmp` gleich). 54, 72 und 41 Tripel (inklusive der sieben neuen Eigenschaften je Stein).
- Die vier alten Einzelgraphen: Differenz gegen `cff6341` sind nur die sieben neuen Zeilen je Graph (`recordStatus` und sechs Zählungen).
- Bishop Loch: Fundort Old Monkland, `POINT(-4.100278 55.876389)`, keine Lesungslücke im Graphen (`[---]` steht im Label).

## S3 — `ogham:recordStatus`

**Ziel:** „Wie viele X-Datensätze sind britisch" ist eine Abfrage.

**Abnahme:** Abfrage auf `out/places.crm.ttl` liefert England 5, Wales 12, Schottland 4.

### Erledigt 2026-11-01

Abfrage und Zahlen wie in A1. Der Wert kommt aus `worklist.series_of()`, also aus derselben Quelle wie die Arbeitsliste; Wortlaut der Werte wie dort (`numbered`, `lost`, `doubtful`). 456 + 14 + 34 = 504.

## S4 — Zweifelsprofil

**Ziel:** Achse 2 kann das Zweifelsprofil eines Steins aus dem Graphen lesen.

**Abnahme:** Die Zählungen stimmen für Dyke, Blackwaterfoot 1, Bishop Loch und Garranes mit `count_doubt.py` überein.

### Erledigt 2026-11-01

Übereinstimmung für alle vier (siehe A1). Die Tabelle steht im generierten `out/README.md`. Keine Zählung für `cert` und `precision`: das braucht D2.

## S5 und S6 — D9 und Grenze

**Abnahme:** `grep -rn "TX6_Transcription"` findet nur noch erklärende Stellen (`ontology_patch.py`, `validate.py`, `words.py`-Kommentar, README-Abschnitt über die Ontologie); der Absatz „Limit of the method" steht in `out/README.md` und README.

### Erledigt 2026-11-01

Umgesetzt wie in A1. Das SPARQL-Beispiel wurde dabei repariert und gegen die Ausgabe ausgeführt.

## S7 — Termnamen abstimmen

**Ziel:** Entscheidung, ob `ogham:recordStatus` und die sechs Zähl-Eigenschaften so heißen sollen, und ob sie in `ogham.owl` übernommen werden.

**Abnahme:** Beschluss in A4 ohne „Vorschlag"; bei Umbenennung: ein Lauf, `grep` findet den alten Namen nicht mehr.

## S8 — `<origDate>`

**Ziel:** Datierung mit `cert` und `precision` im Graphen, damit das Profil auch den Zweifel am Datum zeigt (Dyke `cert="low"`, Blackwaterfoot 1 `precision="low"`).

Zu klären: `P4_has_time-span` hat als Domäne `E2_Temporal_Entity`, die Zeile in `MAPPING` hängt es aber an den Stein. Nötig ist vermutlich eine `E12_Production` oder eine Erstellung der Inschrift dazwischen.

**Abnahme:** Dyke und Blackwaterfoot 1 haben einen `E52_Time-Span` mit `cert`/`precision`; der A-Box-Check meldet keine Domänen-Verletzung; „none in this corpus yet" kommt nirgends mehr vor.

## S9 — Uhr aus der Ausgabe

**Ziel:** Zwei Läufe hintereinander ändern keine Datei.

Drei Stellen: `prov:generatedAtTime` (`py/places.py`), „Generated <Datum>" (`py/webmap.py`), das Datum in `py/ontology_patch.py`. Das Datum soll aus dem Corpus-Manifest (`commit_date`) kommen, nicht aus der Uhr.

**Abnahme:** zwei Läufe, `git status` sauber.

## S10 — Übergabe an `tei--epidoc-amt` (Chat 3)

Was dieses Repo jetzt liefert:

- Sieben Steine in `STONES`, Dateien `S-ARL-001`, `I-COR-001`, `I-COR-030`, `I-KER-020`, `S-MOR-001`, `S-BUT-001`, `S-LKS-X01` in `data/`. **Basisnamen:** `gigha1`, `coomleagh-east`, `garranes`, `ballinrannig6`, `dyke`, `blackwaterfoot-1`, `bishop-loch`; die AMT-Seite soll dieselben nehmen.
- Am Stein-Knoten `data:stone_<ID>`: `ogham:recordStatus` und die sechs Zählungen. Gewichte gibt es hier nicht.
- Lesungen sind `ogham:Reading`, über `ogham:identifiedAs` von der Inschrift aus. Eine Lesung ohne `@source` hat keinen Autor. Dort muss die AMT-Seite entscheiden, was sie mit einem Gewicht ohne Quelle macht (Blackwaterfoot 1: drei Lesungen).
- Zwei Lesungen derselben Quelle auf demselben Stein teilen einen Knoten (`FOR1996` auf Blackwaterfoot 1). Vor Gewichten klären (D1).
- Bishop Loch trägt `recordStatus = doubtful` und sonst fast kein Markup: ein Gewicht, das nur auf `unclear`/`supplied` beruht, wäre dort 1,0.

---

# Teil D: Offene Punkte

- **D1 Modell der Lesungen.** Soll ein `<rdg>` mit `@source` auf demselben Stein mehrere Knoten bekommen (z. B. Index im Apparat), und soll ein Apparat-`rdg` als Variante einer Buchstabengruppe von einer Lesung des ganzen Textes unterschieden werden? Betrifft Blackwaterfoot 1 (`FOR1996`). Ist die Frage ein Schritt oder gehört sie zur AMT-Seite? Beim Wiederaufnehmen als Formular fragen.
- **D2 `<origDate>`** (S8): das Zeitspannen-Modell festlegen.
- **D3 Mehrere Inschriften in einer Datei.** Blackwaterfoot 1 hat drei; modelliert wird die erste. Reicht das, oder braucht jede Inschrift einen Knoten?
- **D4 `I-FER-X01`** trägt in der Ortshierarchie kein Land; Irland zählt 12 statt 13. Ist das ein Fehler der Edition oder der Hierarchie-Ableitung (`py/places.py`)?
- **D5 Versionsnummer.** Gab es für den Stand vor diesem Patch einen Tag? Wenn nein, den Eintrag 0.1.0 im CHANGELOG anpassen. ORCID in `CITATION.cff` fehlt (Flo).
- **D6 Adresse der Engine** für die README: nur falls das Repo darauf verweist (`n4o-rse/amt-engine` laut Abstract, `alpaca-fair-framework/amt-engine` laut AMT-README). Für dieses Repo ohne Belang.
- **D7 Corpus-Stand.** Der Upstream-Corpus ist bei `9a68afd`, hier gepinnt `bb62ccd`. Bei einem `--fetch-corpus` ändern sich viele Dateien in `out/` und `docs/`; das sollte ein eigener Schritt mit eigenem Commit sein.
