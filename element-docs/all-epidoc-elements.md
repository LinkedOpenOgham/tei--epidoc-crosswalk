# All EpiDoc elements in the corpus — crosswalk status & candidates

> **Generated** by `python py/main.py`. Every EpiDoc element tag found across the 506 input files in `../data\origin/`, with its crosswalk status: **✅ mapped** (emitted now), **🔧 candidate** (a sensible CIDOC CRM target we could add next), **② axis 2** (doubt signal, handled in `tei--epidoc-amt`), or **▫ structural** (TEI wrapper / record metadata).

Summary: ② axis 2 (AMT) 15 · ▫ structural 42 · ✅ mapped 17 · 🔧 candidate 40.

| element | count | status | CIDOC CRM target / note |
|---|---|---|---|
| `change` | 4099 | ▫ structural | — (TEI structure / record metadata) |
| `idno` | 3410 | ✅ mapped | crm:E42_Identifier |
| `div` | 3131 | ✅ mapped | crmtex:TX1_Written_Text |
| `language` | 3057 | 🔧 candidate | crm:E56_Language / crmtex:TX3_Writing_System |
| `name` | 2825 | ✅ mapped | crm:E21_Person |
| `p` | 2273 | ▫ structural | — (TEI structure / record metadata) |
| `persName` | 2096 | ✅ mapped | crm:E21_Person (via <name>) |
| `orgName` | 1958 | 🔧 candidate | crm:E74_Group / E40_Legal_Body |
| `resp` | 1868 | 🔧 candidate | crm:E39_Actor (editorial responsibility) |
| `respStmt` | 1868 | 🔧 candidate | crm:E39_Actor (PROV) |
| `ref` | 1750 | ✅ mapped | crm:E53_Place — gazetteer targets inside <origPlace> only; other <ref> are record metadata |
| `placeName` | 1653 | ✅ mapped | crm:E53_Place |
| `bibl` | 1417 | 🔧 candidate | crm:E31_Document (P70_documents) |
| `ptr` | 1417 | ▫ structural | — (TEI structure / record metadata) |
| `citedRange` | 1363 | 🔧 candidate | crm:E31_Document (cited range) |
| `lb` | 1347 | 🔧 candidate | crmtex:TX7_Written_Text_Segment |
| `ab` | 1231 | ✅ mapped | crmtex:TX1_Written_Text (display line, feeds the edition text) |
| `q` | 1228 | 🔧 candidate | crm:E33_Linguistic_Object (quotation) |
| `distinct` | 1033 | ✅ mapped | rdfs:label on the E53_Place (vernacular name form, language-tagged) |
| `note` | 1033 | 🔧 candidate | crm:E62_String (P3_has_note) |
| `provenance` | 1016 | 🔧 candidate | crm:E5_Event / E9_Move (object biography) |
| `funder` | 1010 | ▫ structural | — (TEI structure / record metadata) |
| `editor` | 941 | 🔧 candidate | crm:E39_Actor (P14_carried_out_by) |
| `desc` | 842 | ▫ structural | — (TEI structure / record metadata) |
| `unclear` | 837 | ② axis 2 (AMT) | → amt:weight (axis 2) |
| `height` | 797 | 🔧 candidate | crm:E54_Dimension (P90/P91) |
| `w` | 771 | 🔧 candidate | crm:E36_Visual_Item / ogham:Word |
| `graphic` | 712 | 🔧 candidate | crmdig:D1_Digital_Object (image) |
| `gap` | 585 | ② axis 2 (AMT) | → amt:weight (axis 2) |
| `textLang` | 569 | 🔧 candidate | crm:E56_Language / crmtex:TX3_Writing_System |
| `title` | 517 | 🔧 candidate | crm:E35_Title (P102_has_title) |
| `term` | 514 | 🔧 candidate | crm:E55_Type (e.g. type_of_inscription) |
| `handNote` | 508 | ▫ structural | — (TEI structure / record metadata) |
| `layout` | 506 | ✅ mapped | crm:E25_Human-Made_Feature |
| `TEI` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `authority` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `availability` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `body` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `calendar` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `calendarDesc` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `condition` | 505 | 🔧 candidate | crm:E3_Condition_State (P44_has_condition) |
| `country` | 505 | ✅ mapped | crm:E53_Place (place hierarchy, P89_falls_within) |
| `encodingDesc` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `fileDesc` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `geo` | 505 | ✅ mapped | crm:E53_Place (geo:asWKT on the findspot) |
| `history` | 505 | 🔧 candidate | crm:E5_Event (object-biography wrapper) |
| `langUsage` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `licence` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `listChange` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `material` | 505 | ✅ mapped | crm:E57_Material |
| `msDesc` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `msIdentifier` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `objectDesc` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `objectType` | 505 | ✅ mapped | crm:E55_Type |
| `origPlace` | 505 | ✅ mapped | crm:E53_Place |
| `origin` | 505 | 🔧 candidate | crm:E12_Production (P108_has_produced) |
| `physDesc` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `profileDesc` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `publicationStmt` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `revisionDesc` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `sourceDesc` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `support` | 505 | ✅ mapped | crm:E22_Human-Made_Object |
| `supportDesc` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `teiHeader` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `text` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `titleStmt` | 505 | ▫ structural | — (TEI structure / record metadata) |
| `include` | 504 | ▫ structural | — (TEI structure / record metadata) |
| `layoutDesc` | 504 | ▫ structural | — (TEI structure / record metadata) |
| `msContents` | 504 | ▫ structural | — (TEI structure / record metadata) |
| `repository` | 504 | 🔧 candidate | crm:E74_Group / E39_Actor (P50_has_current_keeper) |
| `textClass` | 502 | ▫ structural | — (TEI structure / record metadata) |
| `dimensions` | 500 | 🔧 candidate | crm:E54_Dimension (P43_has_dimension) |
| `listBibl` | 500 | 🔧 candidate | crm:E31_Document |
| `msItem` | 500 | ▫ structural | — (TEI structure / record metadata) |
| `origDate` | 500 | ✅ mapped | crm:E52_Time-Span |
| `facsimile` | 497 | 🔧 candidate | crmdig:D1_Digital_Object |
| `handDesc` | 494 | ▫ structural | — (TEI structure / record metadata) |
| `supplied` | 491 | ② axis 2 (AMT) | → amt:weight (axis 2) |
| `keywords` | 490 | 🔧 candidate | crm:E55_Type (classification) |
| `g` | 489 | 🔧 candidate | crmtex:TX7_Written_Text_Segment (ogham glyph; resolves via <charDecl>/<glyph>) |
| `app` | 434 | ② axis 2 (AMT) | apparatus → axis 2 |
| `rs` | 427 | 🔧 candidate | crm:E55_Type (e.g. execution technique) |
| `date` | 423 | 🔧 candidate | crm:E52_Time-Span (P4_has_time-span) |
| `width` | 362 | 🔧 candidate | crm:E54_Dimension |
| `depth` | 338 | 🔧 candidate | crm:E54_Dimension |
| `altIdentifier` | 331 | ▫ structural | — (TEI structure / record metadata) |
| `listApp` | 246 | ② axis 2 (AMT) | apparatus → axis 2 |
| `dim` | 195 | 🔧 candidate | crm:E54_Dimension |
| `rdg` | 156 | ✅ mapped | ogham:Reading |
| `media` | 104 | 🔧 candidate | crmdig:D1_Digital_Object (3D/photo) |
| `hi` | 99 | ▫ structural | — (TEI structure / record metadata) |
| `choice` | 93 | ② axis 2 (AMT) | editorial alternative → axis 2 |
| `creation` | 67 | 🔧 candidate | crm:E65_Creation (origin of the text) |
| `space` | 36 | 🔧 candidate | crmtex:TX7_Written_Text_Segment (vacat) |
| `damage` | 35 | ② axis 2 (AMT) | damage-induced doubt → axis 2 |
| `corr` | 32 | ② axis 2 (AMT) | editorial correction → axis 2 |
| `sic` | 32 | ② axis 2 (AMT) | editorial correction → axis 2 |
| `roleName` | 15 | 🔧 candidate | crm:E55_Type (role of the named person) |
| `del` | 10 | 🔧 candidate | crm:E13_Attribute_Assignment (carved deletion) |
| `add` | 7 | 🔧 candidate | crm:E13_Attribute_Assignment (carved addition) |
| `surname` | 7 | 🔧 candidate | crm:E41_Appellation (P1_is_identified_by on E21_Person) |
| `item` | 6 | ▫ structural | — (TEI structure / record metadata) |
| `handShift` | 4 | 🔧 candidate | crm:E55_Type (change of hand / carver) |
| `orig` | 4 | ② axis 2 (AMT) | editorial normalisation → axis 2 |
| `c` | 3 | 🔧 candidate | crmtex:TX7_Written_Text_Segment (single character) |
| `lem` | 3 | ② axis 2 (AMT) | apparatus lemma → axis 2 |
| `abbr` | 2 | ② axis 2 (AMT) | abbreviation/expansion → axis 2 |
| `emph` | 2 | ▫ structural | — (TEI structure / record metadata) |
| `list` | 2 | ▫ structural | — (TEI structure / record metadata) |
| `num` | 2 | ▫ structural | — (TEI structure / record metadata) |
| `surplus` | 2 | ② axis 2 (AMT) | editor judges characters surplus → axis 2 |
| `ex` | 1 | ② axis 2 (AMT) | editor-supplied expansion → axis 2 |
| `expan` | 1 | ② axis 2 (AMT) | abbreviation/expansion → axis 2 |
| `xml` | 1 | ▫ structural | — (TEI structure / record metadata) |

