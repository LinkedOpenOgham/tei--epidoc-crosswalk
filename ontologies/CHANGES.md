# What this repository changes in `ogham.owl`

> **Generated** by `py/ontology_patch.py` on 2026-07-31. `ontologies/upstream/ogham.owl` is the published file and is never edited; `ontologies/ogham.ttl` is the corrected and extended version the pipeline validates against. Re-running regenerates both this file and that one.

817 triples in, 901 out.

## Corrections

### The embedded CRMtex was version 1.0, under a namespace CRMtex never used

The published file carries its own copy of CRMtex classes under `http://www.cidoc-crm.org/cidoc-crm/crmtex/`. CRMtex is published at `http://www.cidoc-crm.org/extensions/crmtex/`, so every one of those URIs resolved to nothing. The copy is also **CRMtex 1.0**, and 2.0 kept the numbers while changing the names:

| CRMtex 1.0 | CRMtex 2.0 |
|---|---|
| `TX5_Reading` | `TX5_Text_Recognition` |
| `TX6_Transcription` | `TX6_Transliteration` |

2.0 also adds `TX14_Reading`, which is *not* the old TX5: it is the whole interpretive act, and it sits under `crminf:I1_Argumentation` — which is where a reading meets axis 2's belief model.

26 triples of the inlined 1.0 copy were removed, and 4 references moved to the real namespace. The classes are not re-stated here: `ontologies/CRMtex_v2.0.rdf` is the definition.

### Axioms that inverted the reference ontologies

- **Removed** `crm:E36_Visual_Item rdfs:subClassOf crmtex:TX7_Written_Text_Segment`  
  E36_Visual_Item is a core CIDOC CRM class; it cannot be a subclass of a CRMtex segment. CRMtex has TX7 under TX1_Written_Text.
- **Removed** `crmtex:TX7_Written_Text_Segment rdfs:subClassOf ontology:Inscription`  
  The same inversion the other way round: CRMtex declares TX7 ⊑ TX1_Written_Text, and ogham:Inscription is itself a TX1.

Together these two put CRM and CRMtex classes *underneath* ogham ones, which is why `ogham:Person` came out with `TX1_Written_Text` and `TX7_Written_Text_Segment` among its ancestors.

### `ogham:Reading` needed a parent that exists

It was declared under `TX6_Transcription`. Under CRMtex 2.0 that identifier is `TX6_Transliteration`, an `E65_Creation` — an *activity*. A reading **text** is not an activity, and `ogham:Reading` is used as one: it is the range of `ogham:identifiedAs`.

It is now `⊑ crmtex:TX7_Written_Text_Segment`, whose definition is *"portions of text considered to be of particular significance by scholars"* — which is what a competing reading is. **This is the one substantive modelling choice made here**, and the alternative is worth weighing: model the *act* of reading as `TX14_Reading` and attach the text to it. That is richer, it is the natural bridge to CRMinf, and it would change the shape of the graph.

### `ogham:shows` had two ranges

`rdfs:range` twice means an intersection: an instance would have to be both a `Person` and a `Word`. It is now `owl:unionOf`.

## Additions — 18 properties

The crosswalk records uncertainty and provenance, which the published ontology does not yet model. Rather than list them in a log on every run, they are declared here, each with a domain, a range and a comment, and each carrying `rdfs:isDefinedBy` pointing at this repository so their origin stays visible.

| property | what it says |
|---|---|
| `ogham:geoStatus` | findspot coordinate status |
| `ogham:geoCertainty` | editorial certainty on the coordinate |
| `ogham:coordinateSource` | source of a supplied coordinate |
| `ogham:geocodedFrom` | how a place was geocoded |
| `ogham:corpusCommit` | upstream corpus commit |
| `ogham:corpusCommitDate` | date of the upstream commit |
| `ogham:corpusEditionCount` | editions in that corpus state |
| `ogham:matchedVariant` | spelling that matched |
| `ogham:matchMode` | how the word was matched |
| `ogham:matchSource` | gazetteer a close match points into |
| `ogham:matchConfidence` | reconciliation confidence |
| `ogham:matchStatus` | reconciliation status |
| `ogham:matchTypeCheck` | type check on a Wikidata match |
| `ogham:nymReference` | normalised name form from the edition |
| `ogham:anonymousInEdition` | the edition does not name this person |
| `ogham:relatedTo` | related to, as the inscription says |
| `ogham:relationLemma` | formula word carrying the relation |
| `ogham:wordClass` | class of formulaic word |

## Two things deliberately left alone

Both are places where the crosswalk and the ontology say different things and **both readings are defensible**, so neither side was quietly changed.

### `ogham:Material`

The ontology puts it under `crm:E55_Type`; the crosswalk emits materials as `crm:E57_Material`. Neither is wrong, because they are about different things: `crm:P45_consists_of` *requires* an `E57_Material` for its range, while a controlled vocabulary of Granite and Sandstone is naturally a set of types. Granite is honestly both. The choice is whether the instance carries both types, or whether the vocabulary and the material are separate nodes.

### `ogham:Person`

The ontology puts it under `foaf:Person`; the crosswalk emits `crm:E21_Person`. The names on an ogham stone are attested people, so `E21` is apt, and `foaf:Person` is the web-of-data anchor. Declaring `ogham:Person` under both would settle it, and costs nothing.

## How to fold this upstream

The generated file is a drop-in replacement, but the interesting part is smaller than that. The corrections are worth taking as they stand; the additions are a proposal. `py/validate.py` reports any term the crosswalk emits that is in neither file, so a term that is renamed upstream surfaces on the next run rather than drifting.

