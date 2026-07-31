# `out/` — TEI/EpiDoc → CIDOC CRM crosswalk

> **Generated file** — produced by `python py/main.py`. Do not edit by hand; it adapts to the EpiDoc inputs and to the `MAPPING` in `py/main.py`.

## 1. What the crosswalk does

For each ogham stone the core EpiDoc elements are mapped to **CIDOC CRM 7.1.3** and its text extension **CRMtex**, and serialised as RDF/Turtle (`out/<stone>.crm.ttl`). Instances also carry the matching `ogham.link` class, which is `rdfs:subClassOf` the CRM class — so the domain ontology *is* the crosswalk. The inscription and every competing reading are modelled here (structurally, in CRMtex); the `amt:weight` belief over the readings is added in `tei--epidoc-amt` (axis 2). Selected terms (materials, object types, editors) are also anchored to Wikidata via weighted `skos:closeMatch` (cache: `../reconciliation/wikidata-links.csv`).

## 2. The crosswalk: EpiDoc → Linked Open Ogham class → CIDOC CRM

The crosswalk runs through an **intermediate domain layer**: each EpiDoc element is mapped to a Linked Open Ogham ontology class, which is `rdfs:subClassOf` the target CIDOC CRM / CRMtex class. `—` means the mapping goes straight to CRM.

| EpiDoc element | Linked Open Ogham class | CIDOC CRM / CRMtex class | property | other vocab |
|---|---|---|---|---|
| `<support> (msDesc)` | `ogham:OghamStone` | `crm:E22_Human-Made_Object` | `(root node)` | — |
| `<idno type=CIIC\|CISP\|TM\|SMR\|Trove>` | `—` | `crm:E42_Identifier` | `P1_is_identified_by (+ P2_has_type)` | — |
| `<objectType>` | `—` | `crm:E55_Type` | `P2_has_type` | — |
| `<material>` | `ogham:Material` | `crm:E57_Material` | `P45_consists_of` | — |
| `inscribed surface / <layout>` | `—` | `crm:E25_Human-Made_Feature` | `P56_bears_feature` | — |
| `<div type=edition>` | `ogham:Inscription` | `crmtex:TX1_Written_Text` | `P128_carries` | CRMtex |
| `<div type=edition> / <rdg>` | `ogham:Reading` | `crmtex:TX6_Transcription` | `TXP4_has_segment + prov:wasAttributedTo` | CRMtex, PROV-O |
| `<origPlace> + <geo>` | `ogham:Place` | `crm:E53_Place` | `P53_has_former_or_current_location` | GeoSPARQL |
| `<placeName type=townland\|parish\|county\|…>` | `ogham:Place` | `crm:E53_Place` | `P89_falls_within (chained)` | — |
| `<ref target=logainm\|rcahmw\|coflein>` | `ogham:Place` | `crm:E53_Place` | `skos:closeMatch (weighted)` | SKOS, AMT |
| `<origDate> (when present)` | `—` | `crm:E52_Time-Span` | `P4_has_time-span` | OWL-Time |
| `<name nymRef> / <persName>` | `ogham:Person` | `crm:E21_Person` | `P67_refers_to` | — |

Namespaces: `crm: http://www.cidoc-crm.org/cidoc-crm/`, `crmtex: …/cidoc-crm/crmtex/`, `geo: http://www.opengis.net/ont/geosparql#`, `prov: http://www.w3.org/ns/prov#`, `time: http://www.w3.org/2006/time#`, `ogham: http://ontology.ogham.link/`.

## 3. Supporting vocabularies (used alongside CIDOC CRM)

Beyond CIDOC CRM / CRMtex, the crosswalk draws on established W3C/OGC vocabularies for the aspects CRM deliberately leaves to specialised standards:

| vocabulary | prefix | used for | in this graph |
|---|---|---|---|
| **CRMtex** (CIDOC CRM text extension) | `crmtex:` | the inscription and its readings | `TX1_Written_Text`, `TX6_Transcription`, `TXP4_has_segment` |
| **GeoSPARQL** (OGC) | `geo:` | geometry of places | `geo:asWKT` on `E53_Place` |
| **PROV-O** (W3C) | `prov:` | attribution of readings to editors | `prov:wasAttributedTo` on each `TX6` |
| **OWL-Time** (W3C) | `time:` | time-spans, aligned with `E52_Time-Span` | when `<origDate>` is present (none in this corpus yet) |
| **RDFS** (W3C) | `rdfs:` | human-readable labels | `rdfs:label` throughout |
| **SKOS + Wikidata** | `skos:` / `wd:` | anchoring terms to Wikidata QIDs | weighted `skos:closeMatch` (materials/types/editors) with `ogham:matchConfidence` + P31/P279 `ogham:matchTypeCheck` |
| **AMT** | `amt:` | making the match a weighted belief | each match is a reified `amt:weight` quadruple; `skos:closeMatch` is typed `amt:Role` (AMT-conformant, aligned with axis 2) |

## 4. Resolved modelling decisions

- **Material → `E57_Material` via `P45_consists_of`.** `E57_Material` is the CRM class for the substance an object is made of and is itself `rdfs:subClassOf E55_Type`; the ontology's `Material ⊑ E55` should be tightened to `⊑ E57` so `P45` is type-consistent.
- **Readings → `crmtex:TX6_Transcription`, `TXP4_has_segment` from the `TX1`, `prov:wasAttributedTo` the editor.** This follows the ontology (`Reading ⊑ TX6`, `identifiedAs ⊑ TXP4_has_segment`); weights stay in axis 2.
- **Place → `P53_has_former_or_current_location`** (the recorded `<geo>` is the site/findspot), matching the ontology's `disclosedAt ⊑ P53`; a reconstructed origin would use `E12_Production` / `P7_took_place_at` instead.

## 5. Where CIDOC CRM sits in the NFDI reference stack

CIDOC CRM is the **domain-rich, event-based** reference for cultural-heritage objects. For discovery-level interoperability across the NFDI, these classes align *upward* via the NFDI4Objects **Object Core Metadata Profile (OCMDP)**, whose super-elements crosswalk to the **NFDI Core Metadata Profile** — schema.org, DataCite, DCAT, NFDI Core / NFDIcore, CodeMeta — as well as DublinCore and Wikidata; on the class side, **MaCHeCO** provides the hierarchical crosswalk to CIDOC CRM (Thiery, Gerber & Fricke 2025). Indicative class-level alignment:

| CIDOC CRM | schema.org | DCAT / DCTERMS | DataCite |
|---|---|---|---|
| `E22_Human-Made_Object` | `schema:CreativeWork` / `Thing` | `dcat:Resource` | `resourceTypeGeneral=PhysicalObject` |
| `E42_Identifier` | `schema:identifier` | `dct:identifier` | `Identifier` |
| `E21_Person` | `schema:Person` / `creator` | `dct:creator` | `creator` / `contributor` |
| `E53_Place` (+ geo) | `schema:spatialCoverage` | `dct:spatial` | `geoLocation` |
| `E52_Time-Span` | `schema:temporalCoverage` | `dct:temporal` | `date` |
| `E55_Type` | `schema:additionalType` | `dcat:theme` | `subject` |
| `E57_Material` | `schema:material` | — | — |
| `crmtex:TX1_Written_Text` | `schema:text` | — | — |

*Indicative only.* The authoritative crosswalk is defined at the OCMDP super-element level (Thiery, F., Gerber, A. & Fricke, F. 2025, *Squirrel Papers* 7(4), https://doi.org/10.5281/zenodo.17159183; N4O TWG OCMDP/MaCHeCO, https://www.nfdi4objects.net/en/twgs/twg2024-1_omds_oo/).

## 6. The crosswalk as an OWL ontology (`crosswalk.ttl`) + SHACL

The crosswalk is also emitted as an **OWL ontology** (`out/crosswalk.ttl`) that models it as a class hierarchy: each TEI/EpiDoc application class (`teiapp:Support`, `teiapp:Idno`, `teiapp:Reading`, …, derived from the tags) is `rdfs:subClassOf` its Linked Open Ogham class, which is `rdfs:subClassOf` the CIDOC CRM class, up to `crm:E1_CRM_Entity rdfs:subClassOf owl:Thing`. Every CRM class also carries an `ogham:nfdiCoreMatch` to a NFDI Core / schema.org term.

A SHACL shapes file (`shapes/crosswalk-shapes.ttl`) then validates every application class (`sh:targetClass teiapp:TEIApplicationClass`) on two constraints:

1. it must reach `crm:E1_CRM_Entity` via `rdfs:subClassOf+` — it has a CIDOC CRM superclass;
2. it (or a superclass) must carry `ogham:nfdiCoreMatch` — it is linked to the NFDI Core profile.

`python py/main.py` runs this validation; the current crosswalk is **SHACL-valid**.

## 7. Per stone — how each element ends up in CIDOC CRM

### Gigha 1 (CIIC 506)

`gigha1.crm.ttl` — 14 mapped elements.

| EpiDoc element | extracted value | → CRM class | node |
|---|---|---|---|
| `<support>` | Gigha 1 | `E22_Human-Made_Object` | `data:stone_S_ARL_001` |
| `<idno type=CIIC>` | 506 | `E42_Identifier` | `data:id_S_ARL_001_CIIC` |
| `<idno type=CISP>` | GIGHA/1 | `E42_Identifier` | `data:id_S_ARL_001_CISP` |
| `<idno type=Trove>` | 38529 | `E42_Identifier` | `data:id_S_ARL_001_Trove` |
| `<objectType>` | Pillar | `E55_Type` | `data:type_Pillar` |
| `<material>` | Granite | `E57_Material` | `data:material_Granite` |
| `inscribed surface` | inscribed face | `E25_Human-Made_Feature` | `data:surface_S_ARL_001` |
| `<div type=edition>` | [---]MAQ[---]COGIN[---] | `crmtex:TX1_Written_Text` | `data:inscription_S_ARL_001` |
| `<rdg> (edition)` | OG(H)AM edition (KF): [---]MAQ[---]COGIN[… | `crmtex:TX6_Transcription` | `data:reading_S_ARL_001_OGHAM_KF` |
| `<rdg> (historical)` | Rhys 1899: MAQICAGILEB | `crmtex:TX6_Transcription` | `data:reading_S_ARL_001_RHY1899` |
| `<rdg> (historical)` | Rhys 1901: OGMA MAQI TIGERNI | `crmtex:TX6_Transcription` | `data:reading_S_ARL_001_RHY1901` |
| `<rdg> (historical)` | Macalister 1902: VICULA MAQ COMGINI | `crmtex:TX6_Transcription` | `data:reading_S_ARL_001_MAC1902` |
| `<rdg> (historical)` | Macalister 1945: VICULA MAQ CUGINI | `crmtex:TX6_Transcription` | `data:reading_S_ARL_001_MAC1945` |
| `<origPlace> + <geo>` | Gigha and Cara · POINT(-5.750278 55.669722) | `E53_Place` | `data:place_S_ARL_001` |

### An Com Liath Thoir | Coomleagh East (CIIC 55)

`coomleagh-east.crm.ttl` — 14 mapped elements.

| EpiDoc element | extracted value | → CRM class | node |
|---|---|---|---|
| `<support>` | An Com Liath Thoir \| Coomleagh East | `E22_Human-Made_Object` | `data:stone_I_COR_001` |
| `<idno type=CIIC>` | 55 | `E42_Identifier` | `data:id_I_COR_001_CIIC` |
| `<idno type=CISP>` | COOME/1 | `E42_Identifier` | `data:id_I_COR_001_CISP` |
| `<idno type=TM>` | 172523 | `E42_Identifier` | `data:id_I_COR_001_TM` |
| `<idno type=SMR>` | CO106-064---- | `E42_Identifier` | `data:id_I_COR_001_SMR` |
| `<objectType>` | Pillar | `E55_Type` | `data:type_Pillar` |
| `inscribed surface` | inscribed face | `E25_Human-Made_Feature` | `data:surface_I_COR_001` |
| `<div type=edition>` | .. ? ..TETA | `crmtex:TX1_Written_Text` | `data:inscription_I_COR_001` |
| `<rdg> (edition)` | OG(H)AM edition (NW): .. ? ..TETA | `crmtex:TX6_Transcription` | `data:reading_I_COR_001_OGHAM_NW` |
| `<rdg> (historical)` | Macalister 1945: ANM SAINA MAQ OGALA MUCO… | `crmtex:TX6_Transcription` | `data:reading_I_COR_001_MAC1945` |
| `<origPlace> + <geo>` | Coomleagh East (An Com Liath Thoir) · POI… | `E53_Place` | `data:place_I_COR_001` |
| `<name nymRef>` | SAINA | `E21_Person` | `data:person_I_COR_001_SAINA` |
| `<name nymRef>` | OGALA | `E21_Person` | `data:person_I_COR_001_OGALA` |
| `<name nymRef>` | TEMOCA | `E21_Person` | `data:person_I_COR_001_TEMOCA` |

### An Garrán | Garranes (CIIC 81)

`garranes.crm.ttl` — 12 mapped elements.

| EpiDoc element | extracted value | → CRM class | node |
|---|---|---|---|
| `<support>` | An Garrán \| Garranes | `E22_Human-Made_Object` | `data:stone_I_COR_030` |
| `<idno type=CIIC>` | 81 | `E42_Identifier` | `data:id_I_COR_030_CIIC` |
| `<idno type=CISP>` | GARES/1 | `E42_Identifier` | `data:id_I_COR_030_CISP` |
| `<idno type=SMR>` | CO084-090002- | `E42_Identifier` | `data:id_I_COR_030_SMR` |
| `<objectType>` | Pillar | `E55_Type` | `data:type_Pillar` |
| `<material>` | Sandstone | `E57_Material` | `data:material_Sandstone` |
| `inscribed surface` | inscribed face | `E25_Human-Made_Feature` | `data:surface_I_COR_030` |
| `<div type=edition>` | CASSITTAS MAQI MUCOI CALLITI | `crmtex:TX1_Written_Text` | `data:inscription_I_COR_030` |
| `<rdg> (edition)` | OG(H)AM edition (NW): CASSITTAS MAQI MUCO… | `crmtex:TX6_Transcription` | `data:reading_I_COR_030_OGHAM_NW` |
| `<origPlace> + <geo>` | Garranes (An Garrán) · POINT(-8.765479 51… | `E53_Place` | `data:place_I_COR_030` |
| `<name nymRef>` | CASSITTAS | `E21_Person` | `data:person_I_COR_030_CASSITTAS` |
| `<name nymRef>` | CALLITI | `E21_Person` | `data:person_I_COR_030_CALLITI` |

### Baile an Reannaigh | Ballinrannig 6 (CIIC 153)

`ballinrannig6.crm.ttl` — 11 mapped elements.

| EpiDoc element | extracted value | → CRM class | node |
|---|---|---|---|
| `<support>` | Baile an Reannaigh \| Ballinrannig 6 | `E22_Human-Made_Object` | `data:stone_I_KER_020` |
| `<idno type=CIIC>` | 153 | `E42_Identifier` | `data:id_I_KER_020_CIIC` |
| `<idno type=CISP>` | BALIG/6 | `E42_Identifier` | `data:id_I_KER_020_CISP` |
| `<idno type=TM>` | www.trismegistos.org/text/172983 | `E42_Identifier` | `data:id_I_KER_020_TM` |
| `<idno type=SMR>` | KE042-057011- | `E42_Identifier` | `data:id_I_KER_020_SMR` |
| `<objectType>` | Pillar | `E55_Type` | `data:type_Pillar` |
| `<material>` | Sandstone | `E57_Material` | `data:material_Sandstone` |
| `inscribed surface` | inscribed face | `E25_Human-Made_Feature` | `data:surface_I_KER_020` |
| `<div type=edition>` | CCICAMINIvac. MAQQ[/I] C[A]TTINI | `crmtex:TX1_Written_Text` | `data:inscription_I_KER_020` |
| `<rdg> (edition)` | OG(H)AM edition (NW): CCICAMINIvac. MAQQ[… | `crmtex:TX6_Transcription` | `data:reading_I_KER_020_OGHAM_NW` |
| `<origPlace> + <geo>` | Ballinrannig (Baile an Reannaigh) · POINT… | `E53_Place` | `data:place_I_KER_020` |

## 8. The place layer across the whole corpus (`places.crm.ttl`)

`main.py` crosswalks a few stones in full; the place layer crosswalks **one aspect across every EpiDoc file it is given** (`--corpus`, default `data/`). This run read **506 files** (504 editions, 2 template/test files skipped) and produced **391 distinct places** over 12 administrative levels, 146 gazetteer links and 10053 triples.

| EpiDoc | Linked Open Ogham class | CIDOC CRM | property |
|---|---|---|---|
| `<origPlace>` | `ogham:Place` | `crm:E53_Place` | `P53_has_former_or_current_location` from the stone |
| `<geo>` | — | (on the `E53`) | `geo:asWKT` |
| `<placeName type=…>` | `ogham:Place` | `crm:E53_Place` | `P89_falls_within` (chained) |
| `@type` of the `<placeName>` | — | `crm:E55_Type` | `P2_has_type` |
| `<distinct xml:lang=…>` | — | — | `rdfs:label` with that language tag |
| `<ref target="logainm…">` | — | — | weighted `skos:closeMatch` |

**The findspot is a place of its own, not the townland.** Stones in one townland do not always carry the same coordinates, so the geometry sits on a per-stone `data:findspot_*` node which `P89_falls_within` the shared townland node. Putting the geometry on the townland would invent a consensus the editions do not assert.

### Coordinate status

`<geo>` is not a strictly typed field. Beside plain `lat, lon` pairs it holds hedges (`(approximate)`, `(possible original location)`), `@cert="low"`, and in a few records prose instead of numbers. Every findspot therefore carries `ogham:geoStatus`, and the editors' own wording is kept verbatim in a `P3_has_note`:

| `ogham:geoStatus` | n | meaning |
|---|---|---|
| `asserted` | 475 | bare coordinate pair, no hedge |
| `qualified` | 6 | coordinates plus `@cert` or a textual hedge |
| `textual_only` | 3 | prose in `<geo>`, no numbers |
| `supplied` | 3 | empty in the edition, filled from an outside source |
| `missing` | 17 | empty `<geo/>` |

This is the **hand-over point to axis 2**: `tei--epidoc-amt` turns `geoStatus`/`geoCertainty` and the note into an `amt:weight`-bearing reified statement over `geo:asWKT`, bridged to `crminf:I2_Belief`. Axis 1 stays structural and only records that the editors hedged, and how.

### Side outputs

`places.csv` (504 rows) and `places.geojson` (484 points, WGS84) are written from the same parse, so the table, the map layer and the graph cannot drift apart. Each GeoJSON feature carries the URI of its `data:findspot_*` node, which is how a map click gets back into the graph.

### Which corpus state this is

The editions are a living repository, so the graph records what it was built from — in `../data/corpus-manifest.yaml` and, as PROV-O, in the graph itself on `data:places-graph`:

| | |
|---|---|
| upstream commit | `bb62ccd146cc` (2026-07-02) |
| fetched | 2026-07-30 |
| editions | 504 |
| tree | <https://github.com/lguariento/og-h-am/tree/bb62ccd146cc34e75c1304e60204744e742e3109/XML> |

`py/webmap.py` publishes the same records as a Leaflet map in `docs/` (484 points), which is what GitHub Pages serves. Nothing there re-parses the XML, so map, table and graph cannot disagree.

