# `out/` — TEI/EpiDoc → CIDOC CRM crosswalk

> **Generated file** — produced by `python py/main.py`. Do not edit by hand; it adapts to the EpiDoc inputs and to the `MAPPING` in `py/main.py`.

## 1. What the crosswalk does

For each ogham stone the core EpiDoc elements are mapped to **CIDOC CRM 7.1.3** and its text extension **CRMtex**, and serialised as RDF/Turtle (`out/<stone>.crm.ttl`). Instances also carry the matching `ogham.link` class, which is `rdfs:subClassOf` the CRM class — so the domain ontology *is* the crosswalk. The competing-reading weights are modelled separately in `tei--epidoc-amt` (axis 2).

## 2. The crosswalk (EpiDoc element → CIDOC CRM / CRMtex)

| EpiDoc element | role | CRM/CRMtex class | CRM property |
|---|---|---|---|
| `<support> (msDesc)` | the stone | `crm:E22_Human-Made_Object` | `(root node)` |
| `<idno type=CIIC\|CISP\|TM\|SMR\|Trove>` | identifiers | `crm:E42_Identifier` | `P1_is_identified_by (+ P2_has_type)` |
| `<objectType>` | object type | `crm:E55_Type` | `P2_has_type` |
| `<material>` | material | `crm:E57_Material` | `P45_consists_of` |
| `inscribed surface / <layout>` | inscribed face | `crm:E25_Human-Made_Feature` | `P56_bears_feature` |
| `<div type=edition>` | inscription text | `crmtex:TX1_Written_Text` | `P128_carries` |
| `<origPlace> + <geo>` | place of origin | `crm:E53_Place` | `P53_has_former_or_current_location (+ geo:asWKT)` |
| `<name nymRef> / <persName>` | referenced name | `crm:E21_Person` | `P67_refers_to (from TX1)` |

Namespaces: `crm: http://www.cidoc-crm.org/cidoc-crm/`, `crmtex: …/cidoc-crm/crmtex/`, `geo: http://www.opengis.net/ont/geosparql#`, `ogham: http://ontology.ogham.link/`.

Open modelling decisions (documented): material as `E57_Material` (CRM-conformant) vs. the ontology's `Material ⊑ E55`; place of origin via `P53` vs. a richer `E12_Production` / `E9_Move` event; readings as `crmtex:TX5/TX6` handled in axis 2.

## 3. Per stone — how each element ends up in CIDOC CRM

### Gigha 1 (CIIC 506)

`gigha1.crm.ttl` — 9 mapped elements.

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
| `<origPlace> + <geo>` | Gigha and Cara · POINT(-5.750278 55.6… | `E53_Place` | `data:place_506` |

### An Com Liath Thoir | Coomleagh East (CIIC 55)

`coomleagh-east.crm.ttl` — 12 mapped elements.

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
| `<origPlace> + <geo>` | Coomleagh East (An Com Liath Thoir) ·… | `E53_Place` | `data:place_55` |
| `<name nymRef>` | SAINA | `E21_Person` | `data:person_55_SAINA` |
| `<name nymRef>` | OGALA | `E21_Person` | `data:person_55_OGALA` |
| `<name nymRef>` | TEMOCA | `E21_Person` | `data:person_55_TEMOCA` |

### An Garrán | Garranes (CIIC 81)

`garranes.crm.ttl` — 11 mapped elements.

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
| `<origPlace> + <geo>` | Garranes (An Garrán) · POINT(-8.76547… | `E53_Place` | `data:place_81` |
| `<name nymRef>` | CASSITTAS | `E21_Person` | `data:person_81_CASSITTAS` |
| `<name nymRef>` | CALLITI | `E21_Person` | `data:person_81_CALLITI` |

### Baile an Reannaigh | Ballinrannig 6 (CIIC 153)

`ballinrannig6.crm.ttl` — 10 mapped elements.

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
| `<origPlace> + <geo>` | Ballinrannig (Baile an Reannaigh) · P… | `E53_Place` | `data:place_153` |

