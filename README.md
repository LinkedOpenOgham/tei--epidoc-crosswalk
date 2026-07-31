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
| `docs/index.html` | the landing page: what exists, with live figures |
| `docs/findspots.html` | browsable Leaflet map of the findspots, points or hex density |
| `docs/words.html` | the formulaic vocabulary, filterable by word, points or hex density |
| `docs/readings.html` | stones with competing readings, by distance and editor |
| `docs/keepers.html` | findspot-to-museum arcs, filterable by institution |
| `docs/setting.html` | how each stone stands today, in the landscape or under a roof |
| `docs/persons.html` | who is named, how they are related, and where names recur |
| `docs/places.geojson` | the same point layer, published beside the map |

Over the full corpus: **504 stones, 395 distinct places** across 12 administrative
levels, 146 gazetteer links, ~10 000 triples. The stone URIs are the same ones the
per-stone graphs mint, so `out/*.crm.ttl` and `out/places.crm.ttl` merge directly.

### The map (GitHub Pages)

`py/webmap.py` publishes the same records as self-contained pages in `docs/`:
a landing page and, at the moment, two views — the findspot map (filterable by
country and by free text, with hedged findspots as dashed rings and the
`data:findspot_*` node in every popup) and the formulaic-word map. Nothing in them
re-parses the XML, so map, table and graph cannot drift apart.

## Who the stones name (`docs/persons.html`)

The relationship does not have to be inferred from word order — the corpus marks it:

```xml
<persName>
  <name nymRef="#cassittas">CASSITTAS</name>
  <w type="formula" lemma="maqqas">MAQI</w>
  <w type="formula" lemma="muccoviias">MUCOI</w>
  <name nymRef="#calliti">CALLITI</name>
</persName>
```

**360 people and 34 kin groups**, **116 relations** the inscriptions assert, in **97
groups** — of which 82 are a single pair, 11 a triple, and four have four members.
No force-directed layout: this is not a hairball, so each stone's kinship is drawn
as a small diagram in its popup instead.

### Three distinctions the extractor keeps

**Two formula words in a row are one relation.** *MAQI MUCOI X* is "son of the kin of
X". Splitting it would assert both that CASSITTAS is CALLITI's son and that he is of
CALLITI's kin, where the inscription says one thing.

**A shared name is a hypothesis, not a person.** Within one inscription an edge is
what the text says; across inscriptions, two occurrences of a name are the same
string. `maqqas_treni` is "son of Trenus" — a patronymic two unrelated men can carry,
and it appears in Cork and in Pembrokeshire. Those links are drawn as **dashed arcs**
and the popup names them as hypotheses. Twelve names bridge stones this way.

**Every `#?` is its own unknown person.** 144 name slots are anonymous. Merging them
would produce one extremely well-connected stranger who is an artefact of the
notation.

A kin group also gets its own node: a *túath* is named after an ancestor but is not
that ancestor. Getting this wrong was caught by the validator, which found a name
typed as a tribe everywhere because it was a tribe somewhere.

### OG(H)AM is the authority; CISP is supplementary

Stated as a principle because it settles more than one question. Where the two
disagree, OG(H)AM has brought Macalister's and CISP's readings up to current
scholarship, and OG(H)AM wins.

It explains a reconciliation that looks broken and is not. Only 37 of 217 `nymRef`
values match the CISP name index by string, and the reason is systematic rather than
noisy: **OG(H)AM normalises to the reconstructed nominative, CISP indexes the
inscribed genitive.**

| OG(H)AM | CISP |
|---|---|
| `caras` | `cari` |
| `olagnas?` | `olagni` |
| `dunaidu`, `marianus` | `dunaidonas`, `mariani` |
| `tebicatus` | `ebicato` |

On 75 stones the two sources name the same number of people, so a positional
alignment is available — and it is deliberately **not** shipped. A link at that
confidence would contradict the caution this page is built on: name identity is not
person identity. Doing it properly is a morphological correspondence, and worth
doing as its own task.

## Where the stones stand today (`docs/setting.html`)

`<repository>` answers one question: is it in an institution? For the 322 stones
where it is silent, the answer is not *unknown* — it is **not known to be in an
institution**, and `<provenance type="observed">` usually says a good deal more:

> *"In situ in pasture, on a gentle south facing slope"*
> *"Built into the wall of a summer house in the garden of Lancarffe House"*
> *"Still in place above the south window of the church at Knockboy"*
> *"Kept in a nearby modern enclosure with I-KER-118 and a boulder with rock art"*

So the reading runs on two axes. **Custody** is coarse and mostly reliable:

| | stones |
|---|---|
| out in the landscape | 213 |
| in an institution | 183 |
| indoors, but visitable | 58 |
| not described | 35 |
| lost or unlocated | 15 |

**Setting** is finer, and is a reading of free prose: *in situ or at the find site*
(86), *built into a structure* (54), *inside a church* (53), *in private or
institutional grounds* (29), *in a protective enclosure* (23), *in a churchyard*
(21), *visitor or heritage centre* (5), *in conservation* (1).

On the map a **circle** is out of doors and a **square** is under a roof, so the
coarse fact survives at a zoom where the colours run together.

### Every verdict shows its working

The rules were written against the corpus rather than guessed at, and each stone
carries the sentence it was judged on plus the phrase that decided it:

> **Lancarffe** · built into a structure
> *"Built into the wall of a summer house in the garden of Lancarffe House by Mr Dunn in 1928."*
> decided by: matched "Built into"

Of the 469 stones with an observed statement, **all 469 now classify**; the 35
`not described` are exactly those where the edition says nothing. That is not the
same as unknown — it still tells you the stone is not recorded as being in a museum.

Two things this shook out. A bare *"conservation"* appears in project credits, and
put the seven Knockboy lintels — stones built into a church wall — in a conservation
workshop; the rule now requires the real phrase, and only S-PER-004 is left, which
genuinely is with a conservator. And the ordering matters: *"Still in place above the
south window of the church"* is a stone in a fabric, not a stone in a churchyard, so
the specific rule has to win.

`reconciliation/setting-overrides.csv` replaces a machine verdict with a human one,
recorded as `set by hand`.

## From findspot to museum (`docs/keepers.html`)

**181 stones** name a present keeper in `<msIdentifier>/<repository>` *and* have a
findspot coordinate — 39 institutions in all, from the National Museum of Ireland
(64 stones) down to a parish church holding one. The corpus names them but gives no
coordinates, so the displacement cannot be drawn without geocoding.

`py/keepers.py` resolves each name against **Wikidata first** — an institution has a
QID, and the QID is what belongs in the graph — then falls back to **OSM Nominatim**
for the small local museums Wikidata does not carry. A candidate is only accepted if
one of its `P31` types reads like something that keeps objects (museum, library,
gallery, university, church…); without that check "Perth Museum" cheerfully resolves
to a town in Australia.

Results land in `reconciliation/keeper-coordinates.csv`, committed, in the same shape
as the Wikidata cache: machine suggestions are marked `auto` and are meant to be read
and either confirmed (`verified`) or corrected. **The file ships with every entry
`pending`** — geocodes are claims about the world and none has been made yet. One
online run fills it:

```
python py/main.py            # geocodes what is still pending, then rebuilds
```

Until then the page renders, says nothing is geocoded, and gives that command.

### What the first run produced, and what it got wrong

A run against the live services resolved **32 of 39 institutions**, covering 173 of
the 182 stones — 159 from Wikidata, 14 from OpenStreetMap. The type check did its
job: *Perth Museum* landed in Perth, Scotland, not in Australia. Every institution
fell inside the islands, and the QIDs correctly kept apart pairs that sit metres
from each other and are genuinely different bodies (Trinity College Dublin 498 m
from the National Museum of Ireland; University College Cork 367 m from Cork Public
Museum).

**One geocode was wrong, and it is instructive.** `St. Brynach's Church` resolved to
Llanfrynach near Brecon — but the stone, Nevern 1 (W-PEM-014), stands in St
Brynach's churchyard at *Nevern* in Pembrokeshire, 100 km away. There are five St
Brynach's in Wales and the search picked another. The stone had not moved at all.

That case is now caught automatically. A church, chapel, graveyard or abbey normally
holds a stone *in situ*, so a large distance means the wrong building of that
dedication was found, not that the stone travelled:

```
  1 geocode(s) worth checking:
    W-PEM-014   St. Brynach's Church   a church or chapel 99.9 km from the findspot
                                       is probably the wrong one of that dedication
```

Distance on its own is deliberately **not** a warning: Shetland to Edinburgh is
genuinely 460 km and Cork to the British Museum 600, and flagging those would bury
the one real error under eighteen false alarms.

**A second run found a second error of the same kind.** `Llansaint Chapel (All
Saints' Church)` resolved to a church in Ireland, 317 km from its Carmarthenshire
stone. The cause was the resolver's own fallback: having failed on the full string
and on `Llansaint Chapel`, it tried the parenthetical alone — and a bare dedication
matches anywhere. That variant is gone. The lookup now also **prefers** the country
the institution's stones come from, and asks Nominatim for that country directly.

A preference, not a filter: nine Irish stones really are in the British Museum and
three in the Pitt Rivers, and a hard country test would discard exactly the cases
this map exists to show. Each lookup therefore runs twice, in-country first, then
unrestricted.

`--regeocode` clears every non-verified coordinate and looks it up again, so a
resolver improvement can be applied without hand-editing the cache. Rows marked
`verified` are never touched.

### One file a human owns

`reconciliation/identifiers.yaml` holds every identifier and coordinate decided by
hand — QIDs, OSM object ids, coordinates typed from a source, and the aliases that
merge two names for one place. **The pipeline never writes it.**

That separation was missing at first, and it was a design error: hand decisions
lived inside `keeper-coordinates.csv`, which is a cache the run rewrites. They sat
one `--regeocode` away from being reformatted or lost, and nothing distinguished a
value someone had checked from one a search had guessed.

The flow is now one-way. Hand values are read from the YAML and applied over
whatever the lookup found, on every run. **Delete the cache and nothing is lost** —
the next run rebuilds it and re-applies them. Keys are what the corpus itself says,
so a mistyped repository string is caught rather than silently doing nothing:

```
  ! identifiers.yaml -- keepers: 'Manx Musuem' -- no such keeper in the corpus;
    check the spelling, this entry does nothing
```

```yaml
keepers:
  Live Borders Library HQ, Selkirk:
    qid: Q140775537
  Meffan Museum and Gallery, Forfar:
    osm_id: way/407744946
  National Museum of Scotland:
    alias_of: National Museums of Scotland
  St. Brynach's Church:
    lat: 52.025392
    lon: -4.795144
    note: Nevern, Pembrokeshire -- not Llanfrynach, which the search found.

findspots:
  I-COR-087:
    qid: Q85394128
    lat: 51.926111
    lon: -9.083889
    source: CISP MUSIC/1; Macalister 1945, 131
```

Precedence: **lat/lon > qid > osm_id > automatic lookup.**

### An identifier outlives a coordinate

Once an entry carries an identifier, the run stops searching and starts **refreshing**:
one call for that object's current coordinate, every run. The fixed file holds the
identifier, the cache holds today's coordinate, and if Wikidata or OSM moves the
point the next run picks it up. Only a *search* result is taken from the cache —
repeating a search is not a refresh, it is another chance to land somewhere else.

To make that easy to reach, every run writes
**`reconciliation/identifiers.suggested.yaml`**: the identifiers the lookup found
for itself, in the shape `identifiers.yaml` expects, with the coordinate in a
comment so it can be checked before promoting.

```yaml
keepers:
  # 51.519444, -0.126944 -- found by wikidata search
  British Museum:
    qid: Q6373
  # 52.059744, -9.06717 -- found by osm search
  Millstreet Museum:
    osm_id: way/…
```

It is a separate, generated file rather than a merge into `identifiers.yaml`,
because that file is the one thing here a person owns and a generator would take
away its comments and ordering. Paste an entry across and that institution is
settled for good.

Nominatim's search response names the object it matched; that id used to be thrown
away and is now kept, which is what lets an OSM-matched institution be promoted the
same way as a Wikidata one.

### A hand-set identifier beats a search

The cache takes two kinds of identifier, and either one closes the question a search
would re-open. Precedence: **a QID set by hand, then an OSM id set by hand, then a
search.** The QID wins where both are present, because it is what ends up in the
graph as the close match anyway.

```
repository                         qid            osm_id
Live Borders Library HQ, Selkirk   Q140775537
Meffan Museum and Gallery, Forfar                 way/407744946
```

A pinned QID is resolved **directly** — one `wbgetentities` call for that item's
`P625`, no searching. If the item carries no coordinate the row is left unset and
says so, rather than quietly falling back to a name search; an identifier is put
there to settle the matter, and a silent fallback would unsettle it again.

### An OSM id beats a search

The cache carries an **`osm_id`** column (`way/404085430`). Where one is present the
coordinate is taken from that object and the row is marked `verified` — the
identification was human, only the coordinate was fetched.

Two sources are tried, in order. **Nominatim's `/lookup` endpoint** — note *lookup*,
not *search*: `osm_ids` is not a search parameter, and sending it to `/search`
returns nothing at all rather than an error, which is exactly how this failed on its
first outing. Then the **OSM API** (`/api/0.6/way/{id}/full.json`), averaging the
object's node coordinates; Nominatim only knows what its indexer has picked up,
while the OSM API knows every object that exists, including one mapped last week.

If both fail the row is **left unset**. There is deliberately no fall-back to
searching: an id is usually present *because* the search got it wrong, so quietly
reinstating the search result would undo the correction and stamp it plausible.

**An id is not automatically right, either.** Four of the five supplied ids landed
where they should — Llansaint came out 0.0 km from its stone, which is what *in
situ* looks like. The fifth did not: `way/404085430` sits two metres from the
Wikidata hit it was meant to correct, because it is St Brynach's at **Llanfrynach**
near Brecon. *Llanfrynach* means "church of Brynach", so Wales has several, and both
the search and the manual lookup found the same wrong one. The in-situ check keeps
flagging it, and now says what the value probably is:

```
  W-PEM-014  St. Brynach's Church
     a church or chapel 99.9 km from the findspot is probably the wrong one of
     that dedication; if the stone is in situ the keeper coordinate is 52.0254, -4.7951
```

This is the argument for keeping the check even after a human has been round the
data: a human-supplied identifier is a better claim than a search result, not a
guaranteed one.

The row is now set by hand — `52.025392, -4.795144`, `source: manual`,
`status: verified` — and the rejected id is recorded in the note so nobody spends an
afternoon finding it again. The `osm_id` is cleared rather than left in place: it
names a real church, just not this one. After that the run reports **181 stones, 37
institutions, 12 across a border and no geocodes worth checking**.

An id is worth more than a typed coordinate: it names one object, it can be checked
by anyone, and it does not silently drift. It also **outranks an existing automatic
coordinate**, which is how a wrong `auto` row gets corrected — adding the id and
re-running is enough, no hand-editing of latitudes.

The six that needed human eyes now carry one:

| repository string | OSM object | what it fixes |
|---|---|---|
| `Museum nan Eilean in Steòrnabhagh \| Stornoway` | `way/382540720` | never resolved (pipe in the name) |
| `Live Borders Library HQ, Selkirk` | `way/1001969300` | never resolved — since remapped to Wikidata `Q140775537` |
| `Meffan Museum and Gallery, Forfar` | `way/407744946` | never resolved |
| `Mount Mellary Abbey Heritage Center` | `way/226430858` | corpus spells Melleray with an A |
| `St. Brynach's Church` | `way/404085430` | search found Llanfrynach, 100 km from Nevern |
| `Llansaint Chapel (All Saints' Church)` | `way/1060152504` | search found a church in Ireland, 317 km away |

### Two names, one place

The corpus names some institutions at two granularities — *National Museums of
Scotland* (the body) and *National Museum of Scotland* (the building on Chambers
Street); *National Museum Wales* and *National Museum Cardiff*. Wikidata rightly
gives each its own QID, but on a map of places they are one point. An `alias_of`
column in the cache merges them: 35 institutions become 33, and Scotland's count
goes from 23 + 2 to 25.

An alias row carries no coordinate of its own and is skipped when geocoding — two
API calls saved per run, and, more usefully, it is no longer counted as an
outstanding gap. A run that has resolved everything now says so:

```
  37/37 institutions located (2 merged into another by alias), 181 stones linked
```

Merging is a curatorial decision, so it lives in the reviewable CSV rather than in
code. Pairs that sit metres apart but are genuinely distinct — Trinity College Dublin
498 m from the National Museum of Ireland, University College Cork 367 m from Cork
Public Museum — are deliberately left alone.

The remaining names that did not resolve carry a qualifier the search chokes on —
`Carmarthen Museum, Abergwili`, `Armagh Robinson library (No 5 Vicars' Hill Museum)`,
`Museum nan Eilean in Steòrnabhagh | Stornoway`. The resolver retries with the name
progressively simplified — parenthetical dropped, then everything after a comma or
pipe — most specific first. That recovered three of the seven on the next run.

### When a count disagrees with the corpus

University College Cork holds **28** stones by the corpus's own reckoning, but only
27 arcs were drawn. The missing one is I-COR-087, *Mount Music*: it names a keeper
but its edition carries an **empty `<geo/>`**, so there is no findspot to draw from.

A sidebar count that quietly disagrees with the corpus is worse than a stated gap,
so the page now lists what it cannot draw, and the run says so:

```
  1 stone(s) name a keeper but have no findspot coordinate:
    I-COR-087   CIIC  135  University College Cork
```

### Supplying a findspot the edition lacks

Twenty editions carry an empty `<geo/>`. Where the findspot is known from elsewhere
it can be supplied through `reconciliation/findspot-overrides.csv` — committed,
provenanced, and applied only where the edition says nothing. An override that would
replace an existing coordinate is **refused and reported**, not applied.

For Mount Music the findspot comes from CISP (`MUSIC/1`), Macalister 1945, 131, and
Wikidata `Q85394128`, with the history that explains the displacement: Windele found
the stone prostrate in a field in 1845, set it up, later moved it to his own house,
and it was acquired from his representatives for the college. The coordinate is the
field, not the college — 40.7 km apart, which is now an arc rather than a silence.

A supplied coordinate must never pass for the edition's own claim, so it is legible
as different everywhere it appears: `ogham:geoStatus "supplied"` rather than
`asserted`, an `ogham:coordinateSource` and a `P3_has_note` recording where it came
from, a weighted `skos:closeMatch` to the QID, and a dashed ring on the map. The
sidebar filter is accordingly no longer "only hedged findspots" but **"only
findspots not plainly asserted"** — the editors' hedges and our supplements are
different things, but they share the property that the edition does not simply state
them.

### The modelling, and an ambiguity it resolves

```turtle
data:stone_I_KER_020  crm:P50_has_current_keeper    data:keeper_Kerry_County_Museum ;
                      crm:P55_has_current_location  data:place_keeper_Kerry_County_Museum .
data:keeper_Kerry_County_Museum a crm:E40_Legal_Body ;
    crm:P74_has_current_or_former_residence data:place_keeper_Kerry_County_Museum ;
    skos:closeMatch wd:Q6396857 .
```

The findspot keeps `P53_has_former_or_current_location`; the museum gets **`P55`**,
which is specifically the *current* location. Both were candidates for `P53`, which
would have made "where it was found" and "where it is" indistinguishable in a query.

Arcs are bowed rather than straight: sixty stones travelling from Cork to Dublin on
the same line would read as one, and a bow also reads as movement rather than as a
boundary. Stones that left their country are drawn in red — the check is a coarse
bounding box per country, since the corpus does not say where a museum is.

## What is still missing (`out/worklist.md`)

Every gap the pipeline can see, generated on each run so it shrinks as the corpus
and the override files grow. `out/worklist.csv` is the same thing to work through
offline.

The grouping matters more than the list, because OG(H)AM's identifiers carry a
distinction a naive gap report would flatten:

| series | example | meaning |
|---|---|---|
| numbered | `I-KER-042` | extant and catalogued |
| `L` | `I-KER-L02` | **lost** — *"broken up for building material, no record of its inscription was preserved"* (Macalister 1945) |
| `X` | `I-KER-X01` | **doubtful** — often *"findspot uncertain"* in the edition itself |

Supplying a coordinate for a numbered stone completes a record. Supplying one for
an `X` stone may assert a precision the evidence does not carry, which is the
opposite of the point. So the tiers run:

| tier | stones | |
|---|---|---|
| extant, no findspot | 0 | *cleared* — two supplied, three closed as not recoverable |
| coordinates the editors hedged | 6 | a better source may firm them up, or confirm the hedge |
| lost stones, no findspot | 7 | the stone is gone; the field may still be recorded |
| doubtful stones, no findspot | 10 | lowest priority, and sometimes the right answer is to leave it |
| no edition text at all | 38 | invisible to the word and disagreement layers |

Where the edition says the provenance is *unrecorded* — I-KER-043 does — the row is
marked **stated as not recoverable**, because that is a finding rather than an
omission and should not cost anyone an afternoon.

### Grid references, and one coordinate that was not one

CISP publishes a *Grid Ref* on the **Irish Grid** (`V 820 915`); the NMS Historic
Environment Viewer publishes **ITM** (`440544, 599247`). Neither is WGS84, and the
Irish Grid needs a datum shift as well as a projection inverse — skip it and you are
50 to 100 m out. `py/grid.py` does both and **checks itself on import** against a
point where the source publishes the answer as well as the input, so a silent
regression in the formulae cannot pass.

The check that mattered was independent, though. `V 820 915` for I-KER-083 converts
to `52.063851, -9.720612` — **140 m from I-KER-084**, the other stone of the same
Kilgobnet site, whose coordinate the corpus already carried. That is the separation
two stones at one site should have, and it is within the 100 m a six-figure grid
reference resolves to.

It also caught a bad datum. Three of the NMS extracts carried the same value,
`46.488181, -15.817314` — a viewer default lying **764 km out in the Atlantic**,
west of Biscay. Identical values repeated across unrelated records are the tell.

### A negative result is a result

Three of the five could not be recovered, and each for a different and documented
reason: Brandon Mountain went over a cliff in the landslide of 1849 and the NMS
record states outright that the location has not been identified; Burnham's edition
says the original provenance is unrecorded, so supplying one would assert exactly
what the editors marked unknown; the Dunraven stone had no recorded origin when it
entered the collection.

Those are recorded in `identifiers.yaml` with `status: not-recoverable` and the
reasoning attached, and the worklist retires them into their own section. Without
somewhere to put a negative result, the same five stones would be offered to the
next person and the afternoon that closed them would live nowhere.

**Tier 1 of the worklist is now empty.**

### A corpus fix that is not research

**200 of the CISP links in the corpus do not resolve.** CISP publishes a stone at
`.../stone/wvale_1.html`, but 160 `corresp` values carry the *identifier* form
`.../stone/TMINE/1.html`, and 40 are empty. The identifier form converts
mechanically — lowercase, `/` becomes `_` — so the worklist repairs its own links on
the way out; the corpus still has them wrong. The empty ones lack a CISP identifier
altogether, so they need one before a link can exist.

## Where the editors disagree (`docs/readings.html`)

The third view asks what the earlier two cannot: **which stones have been read more
than one way, and how far apart are those readings?**

- **90 stones** carry a competing reading, **138 comparisons** in all, **47 editors**
- by distance from the current edition: 35 far apart, 23 diverging, 25 close, 7 identical
- on **28 stones a formulaic word is what is at stake** — one editor read MAQI or
  MUCOI where the current edition does not, or the other way round

Coomleagh East (I-COR-001) is the case in miniature. The current edition reads
`TETA`; Macalister in 1945 read `ANM SAINA MAQ OGALA MUCOI TEMOCA`. Similarity 0.17,
and three formula words hang on which reading you take.

**This page adds no triples.** It is a view over structure the crosswalk already
carries — every reading is a `crmtex:TX6_Transcription` `prov:wasAttributedTo` its
editor — so the same question is one query away:

```sparql
SELECT ?stone (COUNT(DISTINCT ?reading) AS ?n) WHERE {
  ?stone crm:P128_carries ?inscription .
  ?inscription crmtex:TXP4_has_segment ?reading .
  ?reading a crmtex:TX6_Transcription ; prov:wasAttributedTo ?editor .
} GROUP BY ?stone HAVING (?n > 1)
```

What *is* computed is the degree of disagreement, and `out/readings.csv` labels it
as such: a character-level similarity between the current edition and each earlier
reading of the same script. It is an **ordering aid, not a verdict**. Two readings
can score 0.83 and still differ over everything that matters (`MAQI` against
`MAQI MUCOI`); another scores 0.5 only because one editor saw four more letters on a
broken stone. Readings are compared **within one script only** — on a bilingual
stone, measuring the ogham against the Roman-script reading would measure the
distance between two languages, not between two editors.

### Reading the apparatus correctly

Getting this right meant fixing how readings are extracted, which also corrected the
word layer:

- **305 of 434 `<app>` elements hold only a `<note>`** — an editorial remark, not a
  rival reading. Counting them as readings inflates the disagreement.
- **Only 53% of `<rdg>` elements carry `@source`.** For the rest the attribution is
  prose in the `<app>`'s note (*"Macalister (1945, 469) read:"*) and has to be parsed
  from there. Before this, 68 readings were silently labelled as the OG(H)AM edition;
  Macalister 1945 now accounts for 56 readings rather than 29.
- **`<rdg>` texts carry a script prefix** (`Ogham: LA[TI]NI`, `Roman: LATINI IC
  IACIT…`). Left in, the Roman-script readings normalised to an empty string and
  scored 0.00 against everything.

### Exporting a view

Both maps carry **Download SVG** and **Download JPG**, which write out the view as
it currently stands — filters, display mode, cell size and zoom included. The
filename records what it is: `ogham-words-mucoi-2026-07-30.svg`.

- **SVG** keeps the data layer as real vectors (circles for stones, paths for hex
  cells) over the basemap embedded as a single raster, so the figure opens
  correctly in Inkscape or Illustrator and the data can still be restyled.
- **JPG** is a flat composite at 2× the on-screen size.

Both carry the density legend (bottom right, where it sits on screen) and the
OpenStreetMap/CARTO/OG(H)AM attribution, so an exported figure stays properly
credited without anyone having to remember. The zoom and full-screen controls sit
top left and are never part of the export.

Two details worth knowing. **Points are always drawn individually**, even when the
screen shows clusters — a figure wants the distribution, not the bubbles. And the
basemap tiles are cross-origin, so they are re-fetched with CORS *at export time
only*: putting `crossOrigin` on the live tile layer would break the map outright if
the tile server ever stopped sending those headers. If the re-fetch fails the export
still succeeds, with the data layer over a plain background and the fact noted in
the file.

### Map controls

Zoom and full screen sit **top left**, which keeps the bottom-right corner free for
the density legend — and that is where the legend also lands in an exported figure.
Full screen uses the browser's own Fullscreen API on the map pane rather than a
Leaflet plugin: one dependency fewer, and the sidebar gets out of the way while
inspecting a cluster.

### Points or density

Both maps have two displays. **Points** is the clustered marker view. **Density**
bins whatever is currently filtered into a hexagonal grid, ported from the
[SPARQLing Archaeology OER](https://github.com/n4o-rse/oer-001-sparqling-archaeology)
holy-wells notebook: axial hex coordinates with cube rounding, latitude corrected
against the mean latitude of the points. The binning is bit-identical to that
notebook's Python — checked cell by cell — but runs in the browser, so it follows
the country filter, the search box and the selected word rather than being computed
once at build time.

Cell size is selectable (0.5° / 0.25° / 0.12°, giving 71 / 124 / 186 cells for the
481 findspots). So is the **colour scale**, and that needs a word:

| scale | palest band holds | why |
|---|---|---|
| `log` (default) | 68% of cells | equal-ratio bands |
| `linear` | 91% of cells | the notebook's scheme, equal-width bands |

The wells dataset was spread evenly enough for equal-width bands. This corpus is
not: the findspots pile up in Kerry and Cork, the median cell holds one or two
stones and the fullest holds 42, so linear bands push almost everything into the
palest step and the map goes flat. Log binning is therefore the default; linear is
kept one click away for comparison. Legend labels are integer count ranges, so a
band is never advertised that the data cannot fill.

The site is generated from a **page registry** in `py/webmap.py`:

```python
PAGES = [
    {"slug": "findspots.html", "nav": "Findspots", "title": "Findspot map", "blurb": "…"},
    {"slug": "words.html",     "nav": "Formulaic words", "title": "…", "blurb": "…"},
]
```

The navigation on every page and the cards on the landing page are both built from
that list, and the figures on each card are passed in from the run. Adding a third
view later means writing its builder and appending one entry — not editing three
templates and hoping the links stay in step.

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
| `out/readings.csv` | one row per competing reading, with its distance from the current edition |
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

## Checking the graph against the ontologies (`py/validate.py`)

`ontologies/` holds local copies of `ogham.owl`, CIDOC CRM 7.1.3, CRMtex 2.0 and the
AMT vocabulary, so the pipeline can check what it emits without a network call.

Until this existed, a run reported `crosswalk SHACL: VALID` and meant that twelve
class declarations were well formed. The **17 000 triples in `out/*.crm.ttl` — the
actual graph — were checked against nothing.** Three things it found immediately:

**The CRMtex namespace was wrong.** The crosswalk used
`http://www.cidoc-crm.org/cidoc-crm/crmtex/`; CRMtex 2.0 is published at
`http://www.cidoc-crm.org/extensions/crmtex/`. Every `TX` URI in the graph — 960 of
them — pointed at nothing that exists.

**`crm:E40_Legal_Body` was removed in CIDOC CRM 7.x.** Holding institutions were
typed with a class the declared version does not define, which also broke
`P50_has_current_keeper` and `P74`, both of which require an `E39_Actor`. They are
now `E74_Group`, which *is* an Actor.

**`crmtex:TX6_Transcription` does not exist.** CRMtex has `TX6_Transliteration` (an
`E65_Creation` activity) and `TX14_Reading` (an `I1_Argumentation`) — neither is a
text. This one is not the crosswalk's invention: **`ogham.owl` itself declares
`ogham:Reading ⊑ crm:crmtex/TX6_Transcription`**, a class that does not exist, under
a namespace that is not CRMtex's. The crosswalk was faithfully following it.

### The ontology had already made most of the decisions

Reading `ogham.owl` properly turned out to matter more than adding to it. Several
terms invented here already existed, and three subclass assumptions were wrong:

| the crosswalk assumed | the ontology says |
|---|---|
| `ogham:Material ⊑ crm:E57_Material` | `⊑ crm:E55_Type` |
| `ogham:Person ⊑ crm:E21_Person` | `⊑ foaf:Person` |
| `ogham:Place ⊑ crm:E53_Place` | `⊑ pleiades:Place` |

And there were purpose-built properties where generic CRM had been used:
`ogham:carries` (⊑ `P56_bears_feature`) for stone→inscription, **`ogham:identifiedAs`
(⊑ `TXP4_has_segment`, domain Inscription, range Reading)** for inscription→reading,
`ogham:shows` for what a stone displays, and `ogham:translation`, `ogham:context`,
`ogham:reference` for exactly the columns the word list carries. `ogham:FormulaWord`
and `ogham:NomenclatureWord` are the two classes the word matcher distinguishes, so
the match mode is now a class rather than a string.

Violations went from **969 to 5**, and unknown terms from 2 to none.

### Where the crosswalk and the ontology disagree

Four classes are declared differently on the two sides:

| class | the crosswalk says | `ogham.owl` says |
|---|---|---|
| `ogham:Material` | `⊑ crm:E57_Material` | `⊑ crm:E55_Type` |
| `ogham:Person` | `⊑ crm:E21_Person` | `⊑ foaf:Person` |
| `ogham:Inscription` | `⊑ crmtex:TX1_Written_Text` | the same class, under a namespace that defines nothing |

`ogham:Reading` is no longer among them. CRMtex has no class for a reading *text* —
`TX6` is Transliteration, an activity, and `TX14_Reading` is an argumentation — so
`ogham:Reading` is the anchor class in its own right and the ogham column has
nothing further to add. Filling both columns with it briefly made the class its own
superclass; a start-up check now refuses that, alongside one that catches a
duplicate key in `CROSSWALK_EXTRA` (a dict literal shadows silently, which is how
`ogham:Material` lost its entry).

The crosswalk keeps stating its own alignment rather than importing the ontology's,
for a concrete reason: the chain `teiapp:X ⊑ ogham:Y ⊑ crm:Z ⊑ E1_CRM_Entity` is what
the SHACL shape checks, and two of the ontology's parents do not reach `E1` at all —
they point into a namespace where nothing is defined. Importing them would trade a
reported disagreement for a broken graph.

So both sides say what they mean and `py/validate.py` reports the gap on every run.
Neither silently wins, and the four rows above are a decision for whoever owns the
ontology rather than something a script should settle.

### Correcting and extending the ontology

`ontologies/upstream/` holds the published files and is never edited.
`py/ontology_patch.py` reads `upstream/ogham.owl`, applies a declared list of
corrections and additions, and writes `ontologies/ogham.ttl` plus
`ontologies/CHANGES.md`. Both are regenerated on every run, so a new upstream
release can be dropped in and the patch replayed.

**The corrections are a CRMtex version migration.** The published file embeds its
own copy of CRMtex under `…/cidoc-crm/crmtex/` — a namespace CRMtex has never used —
and the copy is **version 1.0**, where `TX5` was *Reading* and `TX6` was
*Transcription*. CRMtex 2.0 keeps the numbers and renames them to *Text Recognition*
and *Transliteration*, and adds `TX14_Reading`, which sits under
`crminf:I1_Argumentation` — the natural bridge to axis 2. Twenty-six triples of the
stale copy were removed and the references moved to the real namespace.

Two axioms were dropped because they inverted the reference ontologies:
`crm:E36_Visual_Item ⊑ TX7_Written_Text_Segment` and
`TX7_Written_Text_Segment ⊑ ogham:Inscription`. Together they put CRM classes
*underneath* ogham ones, which is why `ogham:Person` came out with
`TX1_Written_Text` among its ancestors.

`ogham:shows` declared its range twice, which in RDFS is an intersection no instance
can satisfy; it is now `owl:unionOf`. And `ogham:Reading`, orphaned by the TX6
rename, is now `⊑ crmtex:TX7_Written_Text_Segment` — *"portions of text considered
to be of particular significance by scholars"*, which is what a competing reading is.
That is the one substantive modelling choice, and `CHANGES.md` sets out the
alternative: model the *act* of reading as `TX14_Reading` and hang the text off it.

**The fourteen properties are now declared, not logged.** Each carries a domain, a
range, a comment, and `rdfs:isDefinedBy` pointing at this repository so its origin
stays visible. The validator no longer lists them every run; if one ever appears
that is declared nowhere, *that* is reported, because it means a property was added
to the crosswalk and not to the ontology.

The patch immediately caught two faults in itself — the validator did not understand
a union range, and `geocodedFrom` had a domain too narrow for museum places, which
are `E53` but not `ogham:Place`. Which is the point of running it in the pipeline
rather than once by hand.

### What is left, and why it is left

Five uses of `ogham:shows` fail a range check because the ontology declares that
range **twice**, as `ogham:Person` *and* `ogham:Word`. In RDFS that is an
intersection no instance can satisfy; it wants `owl:unionOf`. That is a bug in
`ogham.owl`, so the validator reports it rather than the crosswalk working around it.

Two subclass divergences remain, and both sides are defensible, so neither was
quietly changed: `ogham:Material` (the ontology says `E55_Type`, the crosswalk emits
`E57_Material`, and `P45_consists_of` requires `E57` for its range) and
`ogham:Person` (`foaf:Person` against `crm:E21_Person`). `CHANGES.md` sets out both
and proposes declaring `ogham:Person` under both parents, which costs nothing.

**Domain and range violations: none.**

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
├── ontologies/                # local copies: ogham.owl, CIDOC CRM, CRMtex, AMT
├── docs/                      # generated GitHub Pages site
│   ├── index.html             # landing page (generated)
│   ├── findspots.html         # Leaflet map of the findspots (generated)
│   ├── words.html             # formulaic-word filter map (generated)
│   ├── readings.html          # editorial-disagreement map (generated)
│   ├── keepers.html           # findspot-to-museum map (generated)
│   ├── setting.html           # present-setting map (generated)
│   ├── persons.html           # person and kinship map (generated)
│   ├── places.geojson         # point layer beside the map (generated)
│   └── .nojekyll
├── py/
│   ├── main.py                # single entry point:  python py/main.py
│   ├── corpus.py              # fetch/update the editions + provenance manifest
│   ├── places.py              # corpus-wide place layer (E53 + GeoSPARQL)
│   ├── words.py               # formulaic vocabulary across all readings
│   ├── dissent.py             # comparison of competing readings
│   ├── grid.py                # Irish Grid and ITM to WGS84, self-checking
│   ├── ontology_patch.py      # corrects and extends ogham.owl, reproducibly
│   ├── validate.py            # A-box check against the reference ontologies
│   ├── worklist.py            # what is still missing, by priority
│   ├── keepers.py             # geocoding of the holding institutions
│   ├── setting.py             # present setting, read from the observed provenance
│   ├── persons.py             # people named on the stones and their relations
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
- Reconcile the 395 places against Wikidata / GeoNames via the existing Logainm and
  RCAHMW anchors
