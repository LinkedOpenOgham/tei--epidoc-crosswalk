# All EpiDoc elements in the corpus — crosswalk status & candidates

> **Generated** by `python py/main.py`. Every EpiDoc element tag found across the 4 input files, with its crosswalk status: **✅ mapped** (emitted now), **🔧 candidate** (a sensible CIDOC CRM target we could add next), **② axis 2** (doubt signal, handled in `tei--epidoc-amt`), or **▫ structural** (TEI wrapper / record metadata).

Summary: ② axis 2 (AMT) 5 · ▫ structural 38 · ✅ mapped 13 · 🔧 candidate 33.

| element | count | status | CIDOC CRM target / note |
|---|---|---|---|
| `change` | 64 | ▫ structural | — (TEI structure / record metadata) |
| `idno` | 26 | ✅ mapped | crm:E42_Identifier |
| `language` | 25 | 🔧 candidate | crm:E56_Language / crmtex:TX3_Writing_System |
| `name` | 24 | ✅ mapped | crm:E21_Person |
| `div` | 23 | ✅ mapped | crmtex:TX1_Written_Text |
| `persName` | 23 | ✅ mapped | crm:E21_Person (via <name>) |
| `bibl` | 20 | 🔧 candidate | crm:E31_Document (P70_documents) |
| `ptr` | 20 | ▫ structural | — (TEI structure / record metadata) |
| `citedRange` | 19 | 🔧 candidate | crm:E31_Document (cited range) |
| `orgName` | 18 | 🔧 candidate | crm:E74_Group / E40_Legal_Body |
| `p` | 17 | ▫ structural | — (TEI structure / record metadata) |
| `q` | 17 | 🔧 candidate | crm:E33_Linguistic_Object (quotation) |
| `resp` | 17 | 🔧 candidate | crm:E39_Actor (editorial responsibility) |
| `respStmt` | 17 | 🔧 candidate | crm:E39_Actor (PROV) |
| `ref` | 15 | ▫ structural | — (TEI structure / record metadata) |
| `date` | 14 | 🔧 candidate | crm:E52_Time-Span (P4_has_time-span) |
| `distinct` | 14 | ▫ structural | — (TEI structure / record metadata) |
| `placeName` | 14 | 🔧 candidate | crm:E53_Place (place hierarchy) |
| `supplied` | 12 | ② axis 2 (AMT) | → amt:weight (axis 2) |
| `note` | 11 | 🔧 candidate | crm:E62_String (P3_has_note) |
| `ab` | 10 | ✅ mapped | crmtex:TX1_Written_Text (display line, feeds the edition text) |
| `desc` | 10 | ▫ structural | — (TEI structure / record metadata) |
| `editor` | 9 | 🔧 candidate | crm:E39_Actor (P14_carried_out_by) |
| `lb` | 9 | 🔧 candidate | crmtex:TX7_Written_Text_Segment |
| `funder` | 8 | ▫ structural | — (TEI structure / record metadata) |
| `gap` | 8 | ② axis 2 (AMT) | → amt:weight (axis 2) |
| `graphic` | 8 | 🔧 candidate | crmdig:D1_Digital_Object (image) |
| `height` | 8 | 🔧 candidate | crm:E54_Dimension (P90/P91) |
| `provenance` | 8 | 🔧 candidate | crm:E5_Event / E9_Move (object biography) |
| `app` | 7 | ② axis 2 (AMT) | apparatus → axis 2 |
| `w` | 7 | 🔧 candidate | crm:E36_Visual_Item / ogham:Word |
| `unclear` | 6 | ② axis 2 (AMT) | → amt:weight (axis 2) |
| `rdg` | 5 | ✅ mapped | crmtex:TX6_Transcription |
| `TEI` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `authority` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `availability` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `body` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `calendar` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `calendarDesc` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `condition` | 4 | 🔧 candidate | crm:E3_Condition_State (P44_has_condition) |
| `country` | 4 | 🔧 candidate | crm:E53_Place (place hierarchy) |
| `dimensions` | 4 | 🔧 candidate | crm:E54_Dimension (P43_has_dimension) |
| `encodingDesc` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `facsimile` | 4 | 🔧 candidate | crmdig:D1_Digital_Object |
| `fileDesc` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `geo` | 4 | ✅ mapped | crm:E53_Place (via <origPlace>) |
| `handDesc` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `handNote` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `history` | 4 | 🔧 candidate | crm:E5_Event (object-biography wrapper) |
| `include` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `keywords` | 4 | 🔧 candidate | crm:E55_Type (classification) |
| `langUsage` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `layout` | 4 | ✅ mapped | crm:E25_Human-Made_Feature |
| `layoutDesc` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `licence` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `listBibl` | 4 | 🔧 candidate | crm:E31_Document |
| `listChange` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `material` | 4 | ✅ mapped | crm:E57_Material |
| `msContents` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `msDesc` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `msIdentifier` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `msItem` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `objectDesc` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `objectType` | 4 | ✅ mapped | crm:E55_Type |
| `origDate` | 4 | ✅ mapped | crm:E52_Time-Span |
| `origPlace` | 4 | ✅ mapped | crm:E53_Place |
| `origin` | 4 | 🔧 candidate | crm:E12_Production (P108_has_produced) |
| `physDesc` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `profileDesc` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `publicationStmt` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `repository` | 4 | 🔧 candidate | crm:E40_Legal_Body / E39_Actor (P50_has_current_keeper) |
| `revisionDesc` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `sourceDesc` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `support` | 4 | ✅ mapped | crm:E22_Human-Made_Object |
| `supportDesc` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `teiHeader` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `term` | 4 | 🔧 candidate | crm:E55_Type (e.g. type_of_inscription) |
| `text` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `textClass` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `textLang` | 4 | 🔧 candidate | crm:E56_Language / crmtex:TX3_Writing_System |
| `title` | 4 | 🔧 candidate | crm:E35_Title (P102_has_title) |
| `titleStmt` | 4 | ▫ structural | — (TEI structure / record metadata) |
| `depth` | 3 | 🔧 candidate | crm:E54_Dimension |
| `listApp` | 3 | ② axis 2 (AMT) | apparatus → axis 2 |
| `width` | 3 | 🔧 candidate | crm:E54_Dimension |
| `altIdentifier` | 2 | ▫ structural | — (TEI structure / record metadata) |
| `media` | 2 | 🔧 candidate | crmdig:D1_Digital_Object (3D/photo) |
| `rs` | 2 | 🔧 candidate | crm:E55_Type (e.g. execution technique) |
| `dim` | 1 | 🔧 candidate | crm:E54_Dimension |

