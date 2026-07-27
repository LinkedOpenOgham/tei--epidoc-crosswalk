# `out/` — TEI/EpiDoc → CIDOC CRM crosswalk

> **Generated file** — produced by `python py/main.py`. Do not edit by hand; it adapts to the EpiDoc inputs and to the `MAPPING` in `py/main.py`.

## 1. What the crosswalk does

For each ogham stone the core EpiDoc elements are mapped to **CIDOC CRM 7.1.3** and its text extension **CRMtex**, and serialised as RDF/Turtle (`out/<stone>.crm.ttl`). Instances also carry the matching `ogham.link` class, which is `rdfs:subClassOf` the CRM class — so the domain ontology *is* the crosswalk. The inscription and every competing reading are modelled here (structurally, in CRMtex); the `amt:weight` belief over the readings is added in `tei--epidoc-amt` (axis 2).

## 2. The crosswalk (EpiDoc element → CIDOC CRM / CRMtex)

| EpiDoc element | role | CRM/CRMtex class | CRM property |
|---|---|---|---|
| `<support> (msDesc)` | the stone | `crm:E22_Human-Made_Object` | `(root node)` |
| `<idno type=CIIC\|CISP\|TM\|SMR\|Trove>` | identifiers | `crm:E42_Identifier` | `P1_is_identified_by (+ P2_has_type)` |
| `<objectType>` | object type | `crm:E55_Type` | `P2_has_type` |
| `<material>` | material | `crm:E57_Material` | `P45_consists_of` |
| `inscribed surface / <layout>` | inscribed face | `crm:E25_Human-Made_Feature` | `P56_bears_feature` |
| `<div type=edition>` | inscription text | `crmtex:TX1_Written_Text` | `P128_carries` |
| `<div type=edition> / <rdg>` | readings | `crmtex:TX6_Transcription` | `TXP4_has_segment (from TX1) + prov:wasAttributedTo` |
| `<origPlace> + <geo>` | place of origin | `crm:E53_Place` | `P53_has_former_or_current_location (+ geo:asWKT)` |
| `<name nymRef> / <persName>` | referenced name | `crm:E21_Person` | `P67_refers_to (from TX1)` |

Namespaces: `crm: http://www.cidoc-crm.org/cidoc-crm/`, `crmtex: …/cidoc-crm/crmtex/`, `geo: http://www.opengis.net/ont/geosparql#`, `prov: http://www.w3.org/ns/prov#`, `ogham: http://ontology.ogham.link/`.

## 3. Resolved modelling decisions

- **Material → `E57_Material` via `P45_consists_of`.** `E57_Material` is the CRM class for the substance an object is made of and is itself `rdfs:subClassOf E55_Type`; the ontology's `Material ⊑ E55` should be tightened to `⊑ E57` so `P45` is type-consistent.
- **Readings → `crmtex:TX6_Transcription`, `TXP4_has_segment` from the `TX1`, `prov:wasAttributedTo` the editor.** This follows the ontology (`Reading ⊑ TX6`, `identifiedAs ⊑ TXP4_has_segment`); weights stay in axis 2.
- **Place → `P53_has_former_or_current_location`** (the recorded `<geo>` is the site/findspot), matching the ontology's `disclosedAt ⊑ P53`; a reconstructed origin would use `E12_Production` / `P7_took_place_at` instead.

## 4. Per stone — how each element ends up in CIDOC CRM

### Gigha 1 (CIIC 506)

`gigha1.crm.ttl` — 14 mapped elements.

| EpiDoc element | extracted value | → CRM class | node |
|---|---|---|---|
| `<support>` | Gigha 1 | `E22_Human-Made_Object` | `data:stone_506` |
| `<idno type=CIIC>` | 506 | `E42_Identifier` | `data:id_506_CIIC` |
| `<idno type=CISP>` | GIGHA/1 | `E42_Identifier` | `data:id_506_CISP` |
| `<idno type=Trove>` | 38529 | `E42_Identifier` | `data:id_506_Trove` |
| `<objectType>` | Pillar | `E55_Type` | `data:type_Pillar` |
| `<material>` | Granite | `E57_Material` | `data:material_Granite` |
| `inscribed surface` | inscribed face | `E25_Human-Made_Feature` | `data:surface_506` |
| `<div type=edition>` | [---]MAQ[---]COGIN[---] | `crmtex:TX1_Written_Text` | `data:inscription_506` |
| `<rdg> (edition)` | OG(H)AM edition (KF): [---]MAQ[---]COGIN[… | `crmtex:TX6_Transcription` | `data:reading_506_OGHAM_KF` |
| `<rdg> (historical)` | Rhys 1899: MAQICAGILEB | `crmtex:TX6_Transcription` | `data:reading_506_RHY1899` |
| `<rdg> (historical)` | Rhys 1901: OGMA MAQI TIGERNI | `crmtex:TX6_Transcription` | `data:reading_506_RHY1901` |
| `<rdg> (historical)` | Macalister 1902: VICULA MAQ COMGINI | `crmtex:TX6_Transcription` | `data:reading_506_MAC1902` |
| `<rdg> (historical)` | Macalister 1945: VICULA MAQ CUGINI | `crmtex:TX6_Transcription` | `data:reading_506_MAC1945` |
| `<origPlace> + <geo>` | Gigha and Cara · POINT(-5.750278 55.669722) | `E53_Place` | `data:place_506` |

### An Com Liath Thoir | Coomleagh East (CIIC 55)

`coomleagh-east.crm.ttl` — 14 mapped elements.

| EpiDoc element | extracted value | → CRM class | node |
|---|---|---|---|
| `<support>` | An Com Liath Thoir \| Coomleagh East | `E22_Human-Made_Object` | `data:stone_55` |
| `<idno type=CIIC>` | 55 | `E42_Identifier` | `data:id_55_CIIC` |
| `<idno type=CISP>` | COOME/1 | `E42_Identifier` | `data:id_55_CISP` |
| `<idno type=TM>` | 172523 | `E42_Identifier` | `data:id_55_TM` |
| `<idno type=SMR>` | CO106-064---- | `E42_Identifier` | `data:id_55_SMR` |
| `<objectType>` | Pillar | `E55_Type` | `data:type_Pillar` |
| `inscribed surface` | inscribed face | `E25_Human-Made_Feature` | `data:surface_55` |
| `<div type=edition>` | .. ? ..TETA | `crmtex:TX1_Written_Text` | `data:inscription_55` |
| `<rdg> (edition)` | OG(H)AM edition (NW): .. ? ..TETA | `crmtex:TX6_Transcription` | `data:reading_55_OGHAM_NW` |
| `<rdg> (historical)` | Macalister 1945: ANM SAINA MAQ OGALA MUCO… | `crmtex:TX6_Transcription` | `data:reading_55_MAC1945` |
| `<origPlace> + <geo>` | Coomleagh East (An Com Liath Thoir) · POI… | `E53_Place` | `data:place_55` |
| `<name nymRef>` | SAINA | `E21_Person` | `data:person_55_SAINA` |
| `<name nymRef>` | OGALA | `E21_Person` | `data:person_55_OGALA` |
| `<name nymRef>` | TEMOCA | `E21_Person` | `data:person_55_TEMOCA` |

### An Garrán | Garranes (CIIC 81)

`garranes.crm.ttl` — 12 mapped elements.

| EpiDoc element | extracted value | → CRM class | node |
|---|---|---|---|
| `<support>` | An Garrán \| Garranes | `E22_Human-Made_Object` | `data:stone_81` |
| `<idno type=CIIC>` | 81 | `E42_Identifier` | `data:id_81_CIIC` |
| `<idno type=CISP>` | GARES/1 | `E42_Identifier` | `data:id_81_CISP` |
| `<idno type=SMR>` | CO084-090002- | `E42_Identifier` | `data:id_81_SMR` |
| `<objectType>` | Pillar | `E55_Type` | `data:type_Pillar` |
| `<material>` | Sandstone | `E57_Material` | `data:material_Sandstone` |
| `inscribed surface` | inscribed face | `E25_Human-Made_Feature` | `data:surface_81` |
| `<div type=edition>` | CASSITTAS MAQI MUCOI CALLITI | `crmtex:TX1_Written_Text` | `data:inscription_81` |
| `<rdg> (edition)` | OG(H)AM edition (NW): CASSITTAS MAQI MUCO… | `crmtex:TX6_Transcription` | `data:reading_81_OGHAM_NW` |
| `<origPlace> + <geo>` | Garranes (An Garrán) · POINT(-8.765479 51… | `E53_Place` | `data:place_81` |
| `<name nymRef>` | CASSITTAS | `E21_Person` | `data:person_81_CASSITTAS` |
| `<name nymRef>` | CALLITI | `E21_Person` | `data:person_81_CALLITI` |

### Baile an Reannaigh | Ballinrannig 6 (CIIC 153)

`ballinrannig6.crm.ttl` — 11 mapped elements.

| EpiDoc element | extracted value | → CRM class | node |
|---|---|---|---|
| `<support>` | Baile an Reannaigh \| Ballinrannig 6 | `E22_Human-Made_Object` | `data:stone_153` |
| `<idno type=CIIC>` | 153 | `E42_Identifier` | `data:id_153_CIIC` |
| `<idno type=CISP>` | BALIG/6 | `E42_Identifier` | `data:id_153_CISP` |
| `<idno type=TM>` | www.trismegistos.org/text/172983 | `E42_Identifier` | `data:id_153_TM` |
| `<idno type=SMR>` | KE042-057011- | `E42_Identifier` | `data:id_153_SMR` |
| `<objectType>` | Pillar | `E55_Type` | `data:type_Pillar` |
| `<material>` | Sandstone | `E57_Material` | `data:material_Sandstone` |
| `inscribed surface` | inscribed face | `E25_Human-Made_Feature` | `data:surface_153` |
| `<div type=edition>` | CCICAMINIvac. MAQQ[/I] C[A]TTINI | `crmtex:TX1_Written_Text` | `data:inscription_153` |
| `<rdg> (edition)` | OG(H)AM edition (NW): CCICAMINIvac. MAQQ[… | `crmtex:TX6_Transcription` | `data:reading_153_OGHAM_NW` |
| `<origPlace> + <geo>` | Ballinrannig (Baile an Reannaigh) · POINT… | `E53_Place` | `data:place_153` |

