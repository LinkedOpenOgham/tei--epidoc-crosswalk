# EpiDoc elements crosswalked to CIDOC CRM (current mapping)

> **Generated** by `python py/main.py`. Describes the crosswalk for the EpiDoc elements currently handled, based on the 506 input EpiDoc files in `../data\origin/`. For every element in the corpus (including the ones not yet mapped) see `all-epidoc-elements.md`; for the full documentation see `../out/README.md`.

| EpiDoc element | in stones | Linked Open Ogham class | CIDOC CRM / CRMtex | property |
|---|---|---|---|---|
| `<support> (msDesc)` | 505/506 | `ogham:OghamStone` | `crm:E22_Human-Made_Object` | `(root node)` |
| `<idno type=CIIC\|CISP\|TM\|SMR\|Trove>` | 505/506 | `—` | `crm:E42_Identifier` | `P1_is_identified_by (+ P2_has_type)` |
| `<objectType>` | 505/506 | `—` | `crm:E55_Type` | `P2_has_type` |
| `<material>` | 505/506 | `ogham:Material` | `crm:E57_Material` | `P45_consists_of` |
| `inscribed surface / <layout>` | 504/506 | `—` | `crm:E25_Human-Made_Feature` | `P56_bears_feature` |
| `<div type=edition>` | 505/506 | `ogham:Inscription` | `crmtex:TX1_Written_Text` | `P128_carries` |
| `<div type=edition> / <rdg>` | 92/506 | `—` | `ogham:Reading` | `ogham:identifiedAs (⊑ TXP4) + prov:wasAttributedTo` |
| `<origPlace> + <geo>` | 505/506 | `ogham:Place` | `crm:E53_Place` | `P53_has_former_or_current_location` |
| `<placeName type=townland\|parish\|county\|…>` | 505/506 | `ogham:Place` | `crm:E53_Place` | `P89_falls_within (chained)` |
| `<ref target=logainm\|rcahmw\|coflein>` | 505/506 | `ogham:Place` | `crm:E53_Place` | `skos:closeMatch (weighted)` |
| `<origDate> (when present)` | 500/506 | `—` | `crm:E52_Time-Span` | `P4_has_time-span` |
| `<name nymRef> / <persName>` | 505/506 | `ogham:Person` | `crm:E21_Person` | `P67_refers_to` |

Selected terms (materials, object types, editors) are additionally anchored to **Wikidata** via weighted `skos:closeMatch`. The reconciliation cache and the curated allowlists live in `../reconciliation/` (`wikidata-links.csv`, `material-allowlist.csv`, `editor-allowlist.csv`, `objecttype-allowlist.csv`).

