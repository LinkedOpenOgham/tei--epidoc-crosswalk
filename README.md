# tei--epidoc-crosswalk

Crosswalk TEI/EpiDoc editions of ogham stones to **CIDOC CRM 7.1.3** and its text
extension **CRMtex**, producing FAIR RDF per stone.

This is **axis 1 (structural interoperability)** of the Linked Open Ogham
crosswalk and the companion of
[`tei--epidoc-amt`](https://github.com/LinkedOpenOgham/tei--epidoc-amt) (axis 2,
vagueness modelling). It supports the DHd 2027 poster *"Mind the Gap zwischen
Stein und Graph"*.

See **`out/README.md`** (generated) for: the three-layer crosswalk
(EpiDoc → Linked Open Ogham class → CIDOC CRM), the supporting vocabularies
(GeoSPARQL, PROV-O, OWL-Time, RDFS), the upward alignment of CIDOC CRM to the
NFDI reference (OCMDP / NFDI Core → schema.org, DCAT, DataCite), and the
element-by-element result for every stone.

## What it does

For each stone the core EpiDoc elements are mapped to CIDOC CRM / CRMtex and
serialised as Turtle (`out/<stone>.crm.ttl`):

| EpiDoc element | CIDOC CRM / CRMtex | property |
|---|---|---|
| `<support>` (the stone) | `crm:E22_Human-Made_Object` | root node |
| `<idno>` (CIIC, CISP, TM, SMR, Trove) | `crm:E42_Identifier` | `P1_is_identified_by` |
| `<objectType>` | `crm:E55_Type` | `P2_has_type` |
| `<material>` | `crm:E57_Material` | `P45_consists_of` |
| inscribed surface | `crm:E25_Human-Made_Feature` | `P56_bears_feature` |
| `<div type="edition">` | `crmtex:TX1_Written_Text` | `P128_carries` |
| `<div type="edition">` / `<rdg>` (readings) | `crmtex:TX6_Transcription` | `TXP4_has_segment` + `prov:wasAttributedTo` |
| `<origPlace>` + `<geo>` | `crm:E53_Place` (+ `geo:asWKT`) | `P53_has_former_or_current_location` |
| `<name nymRef>` / `<persName>` | `crm:E21_Person` | `P67_refers_to` |

Instances also carry the matching `ogham.link` class (e.g. `ogham:OghamStone`),
which is `rdfs:subClassOf` the CRM class — so the domain ontology *is* the
crosswalk. Namespaces are aligned with the `ogham.link` ontology
(`crm: http://www.cidoc-crm.org/cidoc-crm/`, `crmtex: …/cidoc-crm/crmtex/`,
`geo: http://www.opengis.net/ont/geosparql#`).

## Repository structure

```
tei--epidoc-crosswalk/
├── data/                      # inputs (EpiDoc XML)
│   ├── S-ARL-001.xml          # Gigha 1 (CIIC 506)
│   ├── I-COR-001.xml          # Coomleagh East (CIIC 55)
│   ├── I-COR-030.xml          # Garranes (CIIC 81)
│   └── I-KER-020.xml          # Ballinrannig 6 (CIIC 153)
├── out/                       # generated outputs
│   ├── README.md              # element-by-element CRM result (generated)
│   └── *.crm.ttl              # one CIDOC CRM graph per stone (generated)
├── py/
│   └── main.py                # single entry point:  python py/main.py
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Installation

```
pip install -r requirements.txt
```

`rdflib` builds the graph, `lxml` parses the EpiDoc XML.

## Usage

Run from the repository root:

```
python py/main.py
```

This processes all four stones and writes one `out/<stone>.crm.ttl` per stone,
plus `out/README.md`. Single-file mode:

```
python py/main.py --input data/S-ARL-001.xml --output out/gigha1.crm.ttl
```

## Resolved modelling decisions

- **Material** → `E57_Material` via `P45_consists_of`. `E57_Material` is the CRM class for
  the substance an object is made of and is `rdfs:subClassOf E55_Type`; the ontology's
  `Material ⊑ E55` should be tightened to `⊑ E57` so `P45` is type-consistent.
- **Readings** → `crmtex:TX6_Transcription`, `TXP4_has_segment` from the `TX1`,
  `prov:wasAttributedTo` the editor — following the ontology (`Reading ⊑ TX6`,
  `identifiedAs ⊑ TXP4_has_segment`). The `amt:weight` belief stays in axis 2.
- **Place** → `P53_has_former_or_current_location` (the recorded `<geo>` is the
  findspot), matching the ontology's `disclosedAt ⊑ P53`; a reconstructed origin
  would use `E12_Production` / `P7_took_place_at`.

See `out/README.md` for the per-stone detail.

## Author & licence

Florian Thiery. Code licensed under the **MIT License** (see `LICENSE`).

## AI assistance

Parts of this repository were drafted with the assistance of Claude (Anthropic)
and reviewed by Florian Thiery.

## TODO (to fill before publishing)

- Zenodo DOI and `CITATION.cff`
- Data licence / attribution for the EpiDoc input (OG(H)AM project)
- ORCID / affiliation
- Dimensions (`<dimensions>`) → `E54_Dimension`; richer place/production model
