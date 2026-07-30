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
element-by-element result for every stone. The per-element documentation (mapped elements + full inventory of all EpiDoc tags) is generated into `element-docs/`.

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
| `<placeName type="townland\|parish\|county\|…">` | `crm:E53_Place` + `crm:E55_Type` | `P89_falls_within` (chained) |
| `<ref target="logainm\|rcahmw\|coflein">` | gazetteer anchor | weighted `skos:closeMatch` |
| `<name nymRef>` / `<persName>` | `crm:E21_Person` | `P67_refers_to` |

Instances also carry the matching `ogham.link` class (e.g. `ogham:OghamStone`),
which is `rdfs:subClassOf` the CRM class — so the domain ontology *is* the
crosswalk. Namespaces are aligned with the `ogham.link` ontology
(`crm: http://www.cidoc-crm.org/cidoc-crm/`, `crmtex: …/cidoc-crm/crmtex/`,
`geo: http://www.opengis.net/ont/geosparql#`).

## The place layer (whole corpus)

`main.py` crosswalks a few stones in full. The **place layer** (`py/places.py`) does
the complementary thing: it applies the same CIDOC CRM modelling to *one aspect* —
the geography — across **every EpiDoc file it is pointed at**.

The editions live in a separate repository,
[`lguariento/og-h-am`](https://github.com/lguariento/og-h-am) (504 editions). Fetch
them once and everything after that needs no flags:

```
python py/main.py --fetch-corpus   # XML into data/origin/ (gitignored), then runs
python py/main.py                  # finds data/origin/ on its own from here on
```

**Only the XML is fetched.** That repository is about **1.6 GB** because of its
images and 3D derivatives, and nothing here reads them — so the fetch is a
*blobless, sparse, shallow* clone of the `XML/` directory alone: **~8 MB, about two
seconds**. Where git is too old for partial clones (< 2.25), it falls back to the
GitHub API.

### The corpus is a living repository

Re-running `--fetch-corpus` fast-forwards the checkout rather than refetching, and
then reports what actually moved:

```
updating data/origin
  504 editions, 7.1 MB, commit bb62ccd (2026-07-02)
  changes since 2026-06-01:
    added      1  I-ARM-001
    changed    2  E-DEV-002, E-DEV-X01
    removed    1  I-KER-999
```

That comparison runs off **`data/corpus-manifest.yaml`**, which is *committed* even
though `data/origin/` is not — it is the only record of which upstream state
produced `out/` and `docs/`:

```yaml
source: https://github.com/lguariento/og-h-am.git
subdirectory: XML
fetched: '2026-07-30T14:23:11+00:00'
commit: bb62ccd146cc34e75c1304e60204744e742e3109
commit_date: '2026-07-02T12:07:30+01:00'
commit_subject: Update I-KER-048.xml
file_count: 508
edition_count: 504
files:
  XML/E-CON/E-CON-001.xml: e47aed0907abea513ea80144b9e272a05382befb
  …
```

The per-file values are **git blob hashes**, so they are directly comparable with
GitHub's tree listing — which is how the API fallback also downloads only the files
that changed, and how a locally edited edition shows up as drift.

Provenance is read from **the checkout that was actually used**, not from the
manifest — stamping the manifest's commit onto a graph built from some other
directory would be a false claim, worse than none. Point `--corpus` at an untracked
directory and the run says so and emits no commit at all.

The same commit is carried into the outputs rather than living only in the manifest:
`out/places.crm.ttl` records it as PROV-O on `data:places-graph`
(`prov:wasDerivedFrom` the upstream tree, plus `ogham:corpusCommit`), the generated
`out/README.md` states it, and the published map footer links to it. A graph built
from a moving corpus without naming the commit is not reproducible.

**`data/origin/` is the only place looked in.** Not a sibling `../og-h-am/`, not
anything else on the machine: an unrelated checkout of unknown vintage would
silently produce a graph that looks complete and is not. `--corpus PATH` and
`$OGHAM_CORPUS` still override, explicitly. If `data/origin/` is empty the editions
are fetched automatically on first run — 8 MB is a better default than quietly
mapping four stones. Use `--no-fetch`, or `--offline`, to suppress that; then the
place layer falls back to the samples in `data/` and says so loudly.

`data/origin/` is skipped when `data/` itself is scanned, so the sample stones are
never counted twice.

Malformed editions do not stop a run. The corpus occasionally carries a duplicate
`xml:id`, which lxml rejects even though the document is well-formed; such files are
re-parsed in recovery mode, kept, and listed in the run log rather than dropped.

It writes three files from a single parse, so table, map layer and graph cannot
drift apart:

| file | what |
|---|---|
| `out/places.crm.ttl` | CIDOC CRM place graph — `E53_Place`, `P89_falls_within`, `geo:asWKT` |
| `out/places.csv` | one row per inscription, all `<placeName>` levels as columns |
| `out/places.geojson` | WGS84 point layer; each feature carries its `data:findspot_*` URI |
| `docs/index.html` | browsable Leaflet map of the findspots (GitHub Pages) |
| `docs/words.html` | the formulaic vocabulary, filterable by word |
| `docs/places.geojson` | the same point layer, published beside the map |

Over the full corpus: **504 stones, 395 distinct places** across 12 administrative
levels, 146 gazetteer links, ~10 000 triples. The stone URIs are the same ones the
per-stone graphs mint, so `out/*.crm.ttl` and `out/places.crm.ttl` merge directly.

### The map (GitHub Pages)

`py/webmap.py` publishes the same records as a self-contained Leaflet map in
`docs/` — filterable by country and by free text (name, CIIC, CISP, TM, SMR),
with hedged findspots drawn as dashed rings and each popup showing the
`data:findspot_*` node the point corresponds to. Nothing in it re-parses the XML,
so map, table and graph cannot drift apart.

To publish: **Settings → Pages → Source: Deploy from a branch → `main` / `/docs`**.
A `.nojekyll` file is written alongside so Pages serves the directory as-is. The
page also opens straight from disk (`open docs/index.html`); only the basemap
tiles and the two Leaflet libraries come off the network.

## The formulaic vocabulary (`docs/words.html`)

A second page picks up the DHd 2020 poster
[`o3d-epidoc-extractor`](https://github.com/LinkedOpenOgham/o3d-epidoc-extractor)
(Homburg & Thiery, *Linked Ogham Stones*). That extractor matched McManus's
formulaic vocabulary against the *Ogham in 3D* database and mapped the hits; this
one runs the same vocabulary against the TEI/EpiDoc editions of **OG(H)AM**, the
successor project — and against **every reading, not just the current one**.

That is the part the earlier version could not do. Its source held one reading per
stone; EpiDoc holds the current edition *and* the historical `<rdg>`s, so a word is
no longer a property of a stone but of a reading:

- 104 words, of which **78 are attested** in the corpus
- **286 stones** carry at least one match, **663 occurrences** across all readings
- **22 stone/word pairs occur only in a historical reading** — six of them MAQI,
  four MUCOI. On seven stones the entire formulaic reading belongs to an editor
  who has since been superseded.

The map draws that distinction directly: a filled dot means the word is in the
current OG(H)AM edition, a dashed ring means only an older editor read it there.
Popups show each reading with the matched token highlighted.

| file | what |
|---|---|
| `out/words.csv` | one row per (stone, reading, word) with variant, token, gloss, QID |
| `out/words.crm.ttl` | occurrences as `crmtex:TX7_Written_Text_Segment` of the `TX6` reading |
| `docs/words.html` | the filter map |

In RDF each occurrence is a segment of the reading that carries it
(`TXP4_has_segment`), typed by an `E55_Type` for the word, which carries the
McManus reference, the variants as `skos:altLabel` and the Wikidata QID as a
weighted `skos:closeMatch` — the same AMT-conformant shape the rest of the
repository uses. Because the reading is `prov:wasAttributedTo` its editor, "who
read MUCOI here" is a single SPARQL query.

**Matching modes.** Formula words (`ANM`, `MAQI`, `MUCOI`, …) and compound names
match whole tokens; name elements (`CUNA`, `ERC`, `LUG`, …) match as substrings,
which is the earlier project's semantics and is deliberately kept — but it is not
precise, and short elements such as `CON` or `VIR` also fire inside unrelated
names. Every hit records its mode so the two kinds of claim stay distinguishable.

The word list lives at `data/words.csv`, taken unchanged from the earlier
repository (MIT, © Timo Homburg and Florian Thiery) and fetched automatically if
absent.

### Coordinate status — the hand-over to axis 2

`<geo>` is not a strictly typed field. Beside plain `lat, lon` pairs the corpus
holds hedges (`(approximate)`, `(possible original location)`), `@cert="low"`, and
in a few records prose instead of numbers. Nothing is discarded: every findspot
carries `ogham:geoStatus`, and the editors' own wording is kept verbatim in a
`P3_has_note`.

| `ogham:geoStatus` | n | meaning |
|---|---|---|
| `asserted` | 475 | bare coordinate pair, no hedge |
| `qualified` | 6 | coordinates plus `@cert` or a textual hedge |
| `textual_only` | 3 | prose in `<geo>`, no numbers |
| `missing` | 20 | empty `<geo/>` |

Axis 1 records **that** the editors hedged and **how**; turning that into an
`amt:weight`-bearing statement over `geo:asWKT`, bridged to `crminf:I2_Belief`, is
axis 2's job in `tei--epidoc-amt`.

## Crosswalk ontology & SHACL validation

Two kinds of RDF are produced. The per-stone `*.crm.ttl` files are **instances**
(A-Box). The crosswalk itself is emitted as an **OWL ontology** `out/crosswalk.ttl`
(T-Box): every TEI/EpiDoc application class (`teiapp:Support`, `teiapp:Idno`,
`teiapp:Reading`, … — derived from the tags) is `rdfs:subClassOf` its Linked Open
Ogham class, which is `rdfs:subClassOf` the CIDOC CRM class, up to
`crm:E1_CRM_Entity rdfs:subClassOf owl:Thing`; every CRM class carries an
`ogham:nfdiCoreMatch` to a NFDI Core / schema.org term.

`shapes/crosswalk-shapes.ttl` (SHACL) then validates every application class on two
constraints: (1) it must reach `crm:E1_CRM_Entity` (has a CIDOC CRM superclass),
and (2) it or a superclass must carry `ogham:nfdiCoreMatch` (is linked to the NFDI
Core profile). `python py/main.py` runs the check — the current crosswalk is
SHACL-valid.

## Repository structure

```
tei--epidoc-crosswalk/
├── data/                      # inputs only (EpiDoc XML)
│   ├── origin/                # OG(H)AM editions, fetched on demand (gitignored)
│   ├── corpus-manifest.yaml   # which upstream state that is (generated, committed)
│   ├── words.csv              # McManus vocabulary, from o3d-epidoc-extractor
│   ├── S-ARL-001.xml          # Gigha 1 (CIIC 506)
│   ├── I-COR-001.xml          # Coomleagh East (CIIC 55)
│   ├── I-COR-030.xml          # Garranes (CIIC 81)
│   └── I-KER-020.xml          # Ballinrannig 6 (CIIC 153)
├── out/                       # generated outputs
│   ├── README.md              # documentation (generated)
│   ├── *.crm.ttl              # one CIDOC CRM instance graph per stone (generated)
│   ├── places.crm.ttl         # corpus-wide place graph (generated)
│   ├── places.csv             # one row per inscription (generated)
│   ├── places.geojson         # WGS84 point layer (generated)
│   └── crosswalk.ttl          # the crosswalk as an OWL class hierarchy (generated)
├── reconciliation/            # Wikidata cache + curated allowlists (committed)
│   ├── wikidata-links.csv     # reconciliation cache (human-verifiable)
│   ├── material-allowlist.csv     # curated material QIDs (override)
│   ├── editor-allowlist.csv       # curated editor QIDs (override)
│   └── objecttype-allowlist.csv   # curated object-type QIDs (override)
├── element-docs/              # generated element documentation
│   ├── README.md              # crosswalk of the mapped elements (generated)
│   └── all-epidoc-elements.md # full element inventory + candidates (generated)
├── shapes/                    # committed SHACL validation rules (not generated)
│   └── crosswalk-shapes.ttl   # every TEI class → CRM superclass + NFDI link
├── docs/                      # generated GitHub Pages site
│   ├── index.html             # Leaflet map of the findspots (generated)
│   ├── words.html             # formulaic-word filter map (generated)
│   ├── places.geojson         # point layer beside the map (generated)
│   └── .nojekyll
├── py/
│   ├── main.py                # single entry point:  python py/main.py
│   ├── corpus.py              # fetch/update the editions + provenance manifest
│   ├── places.py              # corpus-wide place layer (E53 + GeoSPARQL)
│   ├── words.py               # formulaic vocabulary across all readings
│   ├── webmap.py              # docs/ map builder
│   └── wikidata.py             # Wikidata reconciliation module
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Installation

```
pip install -r requirements.txt
```

`rdflib` builds the graph, `lxml` parses the EpiDoc XML, `PyYAML` reads and writes
the corpus manifest.

## Usage

Run from the repository root:

```
python py/main.py
```

This processes all four stones and writes one `out/<stone>.crm.ttl` per stone,
plus `out/README.md`. Single-file mode:

```
python py/main.py --input data/S-ARL-001.xml --output out/gigha1.crm.ttl
python py/main.py --offline   # skip live Wikidata calls (cache only)
```

Place layer:

```
python py/main.py --corpus ../og-h-am        # place layer over the whole corpus
python py/main.py --places-only               # place layer + map only
python py/main.py --corpus /path/to/og-h-am   # explicit corpus location
python py/main.py --no-places                # per-stone crosswalk only
python py/main.py --no-map                   # skip the docs/ pages
python py/main.py --no-words                # skip the formulaic-word layer
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
- **The findspot is its own `E53_Place`, not the townland it lies in.** Stones in
  one townland do not always carry the same coordinates — 21 townlands in the corpus
  disagree with themselves — so the geometry sits on a per-stone `data:findspot_*`
  node which `P89_falls_within` the shared townland node. Putting it on the townland
  would invent a consensus the editions do not assert.
- **Stone URIs are built on the OG(H)AM edition id (`I-COR-001`), not the CIIC
  number.** CIIC is a bibliographic numbering that is neither complete nor unique:
  two Kilgobnet stones share CIIC 214 and many stones have no CIIC at all, so
  CIIC-based URIs would silently merge distinct stones. CIIC remains in the graph as
  an `E42_Identifier`, which is where a bibliographic number belongs.

See `out/README.md` for the per-stone detail.

## Wikidata reconciliation (term anchoring)

Selected terms — **materials, object types, editors** — are anchored to Wikidata
QIDs and written straight into the `*.crm.ttl` as weighted `skos:closeMatch`, each
with an `ogham:matchConfidence` and `ogham:matchStatus` (reconciliation is itself
uncertain, so links are weighted, not hard `owl:sameAs`). Each candidate's type is
verified against Wikidata **P31/P279** (editor → human; material → rock/stone;
object type → monument/standing stone …): the best type-fitting candidate is kept, otherwise the top hit is kept with **halved confidence** and flagged
`matchTypeCheck = mismatch` — this catches e.g. *Pillar → column (architectural)* or
*Rhys → the given name*. Use `--no-verify` to skip the type check. The committed cache
`reconciliation/wikidata-links.csv` makes runs deterministic and lets you verify machine
suggestions: `verified` entries are trusted; `auto` entries are refreshed from the
live API and should be checked; `pending` entries are resolved on the next online
run. Use `--offline` to skip the live API entirely.

Where the search is unreliable, **committed curated allowlists** in `reconciliation/` pin a fixed QID per term: `material-allowlist.csv`, `editor-allowlist.csv`, `objecttype-allowlist.csv`. A filled entry **overrides** the search entirely and is marked `matchStatus verified`, `matchTypeCheck curated`. This is the fix for e.g. *Pillar → column* (architectural): put the standing-stone / ogham-stone QID in `objecttype-allowlist.csv`. The allowlists ship with the relevant terms present but QIDs empty — fill the ones you confirm.

## Author & licence

Florian Thiery. Code licensed under the **MIT License** (see `LICENSE`).

## AI assistance

Parts of this repository were drafted with the assistance of Claude (Anthropic)
and reviewed by Florian Thiery.

## TODO (to fill before publishing)

- Zenodo DOI and `CITATION.cff`
- Data licence / attribution for the EpiDoc input (OG(H)AM project)
- ORCID / affiliation
- Dimensions (`<dimensions>`) → `E54_Dimension`
- `<repository>` → `E40_Legal_Body` / `P50_has_current_keeper` (current location, as
  opposed to the findspot the place layer models)
- Reconcile the 395 places against Wikidata / GeoNames via the existing Logainm and
  RCAHMW anchors
