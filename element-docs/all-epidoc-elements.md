# All EpiDoc elements in the corpus — crosswalk status & candidates

> **Generated** by `python py/main.py`. Every EpiDoc element tag found across the 508 input files in `../data\origin/`, with its crosswalk status: **✅ mapped** (emitted now), **🔧 candidate** (a sensible CIDOC CRM target we could add next), **② axis 2** (doubt signal, handled in `tei--epidoc-amt`), or **▫ structural** (TEI wrapper / record metadata).

Summary: ② axis 2 (AMT) 15 · ▫ structural 42 · ✅ mapped 17 · 🔧 candidate 40.

| element | count | status | CIDOC CRM target / note |
|---|---|---|---|
| `change` | 4117 | ▫ structural | — (TEI structure / record metadata) |
| `idno` | 3424 | ✅ mapped | crm:E42_Identifier |
| `div` | 3145 | ✅ mapped | crmtex:TX1_Written_Text |
| `language` | 3069 | 🔧 candidate | crm:E56_Language / crmtex:TX3_Writing_System |
| `name` | 2843 | ✅ mapped | crm:E21_Person |
| `p` | 2288 | ▫ structural | — (TEI structure / record metadata) |
| `persName` | 2114 | ✅ mapped | crm:E21_Person (via <name>) |
| `orgName` | 1964 | 🔧 candidate | crm:E74_Group / E40_Legal_Body |
| `resp` | 1874 | 🔧 candidate | crm:E39_Actor (editorial responsibility) |
| `respStmt` | 1874 | 🔧 candidate | crm:E39_Actor (PROV) |
| `ref` | 1761 | ✅ mapped | crm:E53_Place — gazetteer targets inside <origPlace> only; other <ref> are record metadata |
| `placeName` | 1659 | ✅ mapped | crm:E53_Place |
| `bibl` | 1431 | 🔧 candidate | crm:E31_Document (P70_documents) |
| `ptr` | 1431 | ▫ structural | — (TEI structure / record metadata) |
| `citedRange` | 1377 | 🔧 candidate | crm:E31_Document (cited range) |
| `lb` | 1355 | 🔧 candidate | crmtex:TX7_Written_Text_Segment |
| `ab` | 1235 | ✅ mapped | crmtex:TX1_Written_Text (display line, feeds the edition text) |
| `q` | 1234 | 🔧 candidate | crm:E33_Linguistic_Object (quotation) |
| `distinct` | 1044 | ✅ mapped | rdfs:label on the E53_Place (vernacular name form, language-tagged) |
| `note` | 1038 | 🔧 candidate | crm:E62_String (P3_has_note) |
| `provenance` | 1020 | 🔧 candidate | crm:E5_Event / E9_Move (object biography) |
| `funder` | 1014 | ▫ structural | — (TEI structure / record metadata) |
| `editor` | 943 | 🔧 candidate | crm:E39_Actor (P14_carried_out_by) |
| `desc` | 851 | ▫ structural | — (TEI structure / record metadata) |
| `unclear` | 845 | ② axis 2 (AMT) | → amt:weight (axis 2) |
| `height` | 801 | 🔧 candidate | crm:E54_Dimension (P90/P91) |
| `w` | 777 | 🔧 candidate | crm:E36_Visual_Item / ogham:Word |
| `graphic` | 721 | 🔧 candidate | crmdig:D1_Digital_Object (image) |
| `gap` | 583 | ② axis 2 (AMT) | → amt:weight (axis 2) |
| `textLang` | 571 | 🔧 candidate | crm:E56_Language / crmtex:TX3_Writing_System |
| `title` | 520 | 🔧 candidate | crm:E35_Title (P102_has_title) |
| `term` | 516 | 🔧 candidate | crm:E55_Type (e.g. type_of_inscription) |
| `handNote` | 510 | ▫ structural | — (TEI structure / record metadata) |
| `layout` | 508 | ✅ mapped | crm:E25_Human-Made_Feature |
| `TEI` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `authority` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `availability` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `body` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `calendar` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `calendarDesc` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `condition` | 507 | 🔧 candidate | crm:E3_Condition_State (P44_has_condition) |
| `country` | 507 | ✅ mapped | crm:E53_Place (place hierarchy, P89_falls_within) |
| `encodingDesc` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `fileDesc` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `geo` | 507 | ✅ mapped | crm:E53_Place (geo:asWKT on the findspot) |
| `history` | 507 | 🔧 candidate | crm:E5_Event (object-biography wrapper) |
| `langUsage` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `licence` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `listChange` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `material` | 507 | ✅ mapped | crm:E57_Material |
| `msDesc` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `msIdentifier` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `objectDesc` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `objectType` | 507 | ✅ mapped | crm:E55_Type |
| `origPlace` | 507 | ✅ mapped | crm:E53_Place |
| `origin` | 507 | 🔧 candidate | crm:E12_Production (P108_has_produced) |
| `physDesc` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `profileDesc` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `publicationStmt` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `revisionDesc` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `sourceDesc` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `support` | 507 | ✅ mapped | crm:E22_Human-Made_Object |
| `supportDesc` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `teiHeader` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `text` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `titleStmt` | 507 | ▫ structural | — (TEI structure / record metadata) |
| `include` | 506 | ▫ structural | — (TEI structure / record metadata) |
| `layoutDesc` | 506 | ▫ structural | — (TEI structure / record metadata) |
| `msContents` | 506 | ▫ structural | — (TEI structure / record metadata) |
| `repository` | 506 | 🔧 candidate | crm:E74_Group / E39_Actor (P50_has_current_keeper) |
| `textClass` | 504 | ▫ structural | — (TEI structure / record metadata) |
| `dimensions` | 502 | 🔧 candidate | crm:E54_Dimension (P43_has_dimension) |
| `listBibl` | 502 | 🔧 candidate | crm:E31_Document |
| `msItem` | 502 | ▫ structural | — (TEI structure / record metadata) |
| `origDate` | 502 | ✅ mapped | crm:E52_Time-Span |
| `facsimile` | 499 | 🔧 candidate | crmdig:D1_Digital_Object |
| `handDesc` | 496 | ▫ structural | — (TEI structure / record metadata) |
| `supplied` | 493 | ② axis 2 (AMT) | → amt:weight (axis 2) |
| `keywords` | 492 | 🔧 candidate | crm:E55_Type (classification) |
| `g` | 489 | 🔧 candidate | crmtex:TX7_Written_Text_Segment (ogham glyph; resolves via <charDecl>/<glyph>) |
| `app` | 437 | ② axis 2 (AMT) | apparatus → axis 2 |
| `rs` | 429 | 🔧 candidate | crm:E55_Type (e.g. execution technique) |
| `date` | 426 | 🔧 candidate | crm:E52_Time-Span (P4_has_time-span) |
| `width` | 364 | 🔧 candidate | crm:E54_Dimension |
| `depth` | 340 | 🔧 candidate | crm:E54_Dimension |
| `altIdentifier` | 333 | ▫ structural | — (TEI structure / record metadata) |
| `listApp` | 249 | ② axis 2 (AMT) | apparatus → axis 2 |
| `dim` | 195 | 🔧 candidate | crm:E54_Dimension |
| `rdg` | 156 | ✅ mapped | ogham:Reading |
| `media` | 104 | 🔧 candidate | crmdig:D1_Digital_Object (3D/photo) |
| `hi` | 99 | ▫ structural | — (TEI structure / record metadata) |
| `choice` | 93 | ② axis 2 (AMT) | editorial alternative → axis 2 |
| `creation` | 67 | 🔧 candidate | crm:E65_Creation (origin of the text) |
| `space` | 38 | 🔧 candidate | crmtex:TX7_Written_Text_Segment (vacat) |
| `damage` | 35 | ② axis 2 (AMT) | damage-induced doubt → axis 2 |
| `corr` | 32 | ② axis 2 (AMT) | editorial correction → axis 2 |
| `sic` | 32 | ② axis 2 (AMT) | editorial correction → axis 2 |
| `roleName` | 15 | 🔧 candidate | crm:E55_Type (role of the named person) |
| `del` | 10 | 🔧 candidate | crm:E13_Attribute_Assignment (carved deletion) |
| `add` | 7 | 🔧 candidate | crm:E13_Attribute_Assignment (carved addition) |
| `surname` | 7 | 🔧 candidate | crm:E41_Appellation (P1_is_identified_by on E21_Person) |
| `handShift` | 6 | 🔧 candidate | crm:E55_Type (change of hand / carver) |
| `item` | 6 | ▫ structural | — (TEI structure / record metadata) |
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

