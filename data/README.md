# `data/` — EpiDoc elements crosswalked to CIDOC CRM (current mapping)

> **Generated** by `python py/main.py`. Describes the crosswalk for the EpiDoc elements currently handled, based on the 4 input files in this folder. For every element in the corpus (including the ones not yet mapped) see `all-epidoc-elements.md`; for the full documentation see `../out/README.md`.

| EpiDoc element | in stones | Linked Open Ogham class | CIDOC CRM / CRMtex | property |
|---|---|---|---|---|
| `<support> (msDesc)` | 4/4 | `ogham:OghamStone` | `crm:E22_Human-Made_Object` | `(root node)` |
| `<idno type=CIIC\|CISP\|TM\|SMR\|Trove>` | 4/4 | `—` | `crm:E42_Identifier` | `P1_is_identified_by (+ P2_has_type)` |
| `<objectType>` | 4/4 | `—` | `crm:E55_Type` | `P2_has_type` |
| `<material>` | 4/4 | `ogham:Material` | `crm:E57_Material` | `P45_consists_of` |
| `inscribed surface / <layout>` | 4/4 | `—` | `crm:E25_Human-Made_Feature` | `P56_bears_feature` |
| `<div type=edition>` | 4/4 | `ogham:Inscription` | `crmtex:TX1_Written_Text` | `P128_carries` |
| `<div type=edition> / <rdg>` | 2/4 | `ogham:Reading` | `crmtex:TX6_Transcription` | `TXP4_has_segment + prov:wasAttributedTo` |
| `<origPlace> + <geo>` | 4/4 | `ogham:Place` | `crm:E53_Place` | `P53_has_former_or_current_location` |
| `<origDate> (when present)` | 4/4 | `—` | `crm:E52_Time-Span` | `P4_has_time-span` |
| `<name nymRef> / <persName>` | 4/4 | `ogham:Person` | `crm:E21_Person` | `P67_refers_to` |

Selected terms (materials, object types, editors) are additionally anchored to **Wikidata** via weighted `skos:closeMatch`. The reconciliation cache is `wikidata-links.csv` (committed): check and flip `status: auto` → `verified` once a QID is confirmed.

