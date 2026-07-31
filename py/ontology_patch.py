#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ontology_patch.py -- correct and extend ogham.owl, reproducibly.

``ontologies/upstream/ogham.owl`` is the file as published and is never edited.
This module reads it, applies a declared list of corrections and additions, and
writes ``ontologies/ogham.owl`` together with ``ontologies/CHANGES.md``, which says
what changed and why. Re-running regenerates both, so a new upstream release can be
dropped into ``upstream/`` and the patch replayed.

Why patch rather than hand-edit: every other artefact in this repository is
generated from a stated input, and an ontology edited in place would be the one
place where a change had no record. The generated file also stays honest about
which axioms are ours -- they carry ``rdfs:isDefinedBy`` pointing at this
repository.

**The corrections are a CRMtex version migration, not typo-fixing.** The upstream
file embeds its own copy of CRMtex under
``http://www.cidoc-crm.org/cidoc-crm/crmtex/`` -- a namespace CRMtex has never used
-- and the copy is **CRMtex 1.0**, where TX5 was *Reading* and TX6 was
*Transcription*. CRMtex 2.0 keeps the numbers and renames them: TX5 is *Text
Recognition*, TX6 is *Transliteration*, and a new TX14 is *Reading*. Anything built
against the old names points at classes that no longer exist under names that were
never resolvable.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, XSD

OG = Namespace("http://ontology.ogham.link/")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
TEX = Namespace("http://www.cidoc-crm.org/extensions/crmtex/")
WRONG_TEX = "http://www.cidoc-crm.org/cidoc-crm/crmtex/"
REPO = URIRef("https://github.com/LinkedOpenOgham/tei--epidoc-crosswalk")

# CRMtex 1.0 numbers kept their identifiers in 2.0 but not their names.
TEX_RENAME = {
    "TX5_Reading": "TX5_Text_Recognition",
    "TX6_Transcription": "TX6_Transliteration",
}

# Axioms that invert the reference ontologies. Both put a CRM or CRMtex class
# underneath an ogham one, which is why ogham:Person came out with TX1_Written_Text
# among its ancestors.
DROP = [
    (CRM["E36_Visual_Item"], RDFS.subClassOf, URIRef(WRONG_TEX + "TX7_Written_Text_Segment"),
     "E36_Visual_Item is a core CIDOC CRM class; it cannot be a subclass of a "
     "CRMtex segment. CRMtex has TX7 under TX1_Written_Text."),
    (URIRef(WRONG_TEX + "TX7_Written_Text_Segment"), RDFS.subClassOf, OG["Inscription"],
     "The same inversion the other way round: CRMtex declares "
     "TX7 \u2291 TX1_Written_Text, and ogham:Inscription is itself a TX1."),
]

# Properties the crosswalk needs and the ontology does not yet carry.
# (name, kind, domain, range, label, comment)
ADDITIONS = [
    ("geoStatus", OWL.DatatypeProperty, OG["Place"], XSD.string,
     "findspot coordinate status",
     "How the coordinate of a findspot stands in the edition: asserted (a plain "
     "pair), qualified (hedged with @cert or a phrase such as \u201capproximate\u201d), "
     "textual_only (prose instead of numbers), supplied (empty in the edition and "
     "filled from an outside source), or missing."),
    ("geoCertainty", OWL.DatatypeProperty, OG["Place"], XSD.string,
     "editorial certainty on the coordinate",
     "The value of @cert on the TEI <geo> element, kept verbatim."),
    ("coordinateSource", OWL.DatatypeProperty, OG["Place"], XSD.string,
     "source of a supplied coordinate",
     "Where a coordinate came from when the edition gives none: a CISP grid "
     "reference, a national monuments record, a Wikidata item."),
    # any place with a coordinate, including a museum, which is an E53 but not
    # an ogham:Place (that one is a Pleiades place)
    ("geocodedFrom", OWL.DatatypeProperty, CRM["E53_Place"], XSD.string,
     "how a place was geocoded",
     "Which service or identifier produced a coordinate for a named place: "
     "wikidata, wikidata-qid, osm, osm-id, or manual."),
    ("corpusCommit", OWL.DatatypeProperty, None, XSD.string,
     "upstream corpus commit",
     "The commit of the EpiDoc corpus a derived graph was built from. The corpus "
     "is a living repository, so a graph that does not name its commit cannot be "
     "reproduced."),
    ("corpusCommitDate", OWL.DatatypeProperty, None, XSD.string,
     "date of the upstream commit", "Date of the commit named by ogham:corpusCommit."),
    ("corpusEditionCount", OWL.DatatypeProperty, None, XSD.integer,
     "editions in that corpus state",
     "How many EpiDoc editions the corpus held at that commit."),
    ("matchedVariant", OWL.DatatypeProperty, OG["Word"], XSD.string,
     "spelling that matched",
     "The spelling of a formulaic word that was actually found, where the word has "
     "several: MAQQI, MAC and MACCI all match MAQI."),
    ("matchMode", OWL.DatatypeProperty, OG["Word"], XSD.string,
     "how the word was matched",
     "Whether a word was matched as a whole token (formula words, compound names) "
     "or as a substring (name elements). The two carry different confidence and "
     "should not be read alike."),
    ("matchSource", OWL.AnnotationProperty, None, XSD.string,
     "gazetteer a close match points into",
     "Which authority a weighted skos:closeMatch was drawn from, e.g. Logainm or "
     "the RCAHMW Historic Place Names of Wales."),
    ("matchConfidence", OWL.AnnotationProperty, None, XSD.decimal,
     "reconciliation confidence",
     "Confidence in a reconciliation link, in [0,1]. Carried on the reified "
     "statement alongside amt:weight."),
    ("matchStatus", OWL.AnnotationProperty, None, XSD.string,
     "reconciliation status",
     "Whether a link was found automatically (auto), asserted by the source "
     "(source-asserted), or checked by a person (verified)."),
    ("matchTypeCheck", OWL.AnnotationProperty, None, XSD.string,
     "type check on a Wikidata match",
     "Result of checking a candidate's P31/P279 against what was expected: ok, "
     "mismatch, or unknown."),
    ("nymReference", OWL.DatatypeProperty, (OG["Person"], OG["OghamTribe"]), XSD.string,
     "normalised name form from the edition",
     "The value of @nymRef on a TEI <name>: the editors' normalised form of an "
     "inscribed name, carried by a person or by the kin group named after one. "
     "These are reconstructed nominatives; CISP indexes the inscribed genitive, so "
     "the two do not match on the string, and where they differ OG(H)AM is the "
     "authority and CISP is supplementary."),
    ("anonymousInEdition", OWL.DatatypeProperty, OG["Person"], XSD.boolean,
     "the edition does not name this person",
     "True where @nymRef is '#?'. Each such slot is its own person: the inscription "
     "asserts that someone stood in that relation, not that all of them were one."),
    ("relatedTo", OWL.ObjectProperty, OG["Person"], None,
     "related to, as the inscription says",
     "A relation one inscription asserts between two named slots. The kind is on the "
     "reified statement as ogham:relationLemma, because the formula word is what "
     "carries it; where that is a direct parent relation, crm:P152_has_parent is "
     "emitted as well."),
    ("relationLemma", OWL.AnnotationProperty, None, XSD.string,
     "formula word carrying the relation",
     "The lemma of the formula word, e.g. maqqas, or maqqas+muccoviias where two "
     "formula words stand together and assert one thing."),
    ("wordClass", OWL.AnnotationProperty, OG["Word"], XSD.string,
     "class of formulaic word",
     "Label for the kind of word, mirroring the ogham:FormulaWord and "
     "ogham:NomenclatureWord subclasses."),
]

# ogham:Reading needs a parent that exists. See CHANGES.md for the reasoning.
READING_PARENT = TEX["TX7_Written_Text_Segment"]


def _renamespace(term):
    if isinstance(term, URIRef) and str(term).startswith(WRONG_TEX):
        local = str(term)[len(WRONG_TEX):]
        return TEX[TEX_RENAME.get(local, local)]
    return term


def patch(upstream: Path, out: Path, changes_path: Path) -> dict:
    g = Graph()
    g.parse(str(upstream))
    before = len(g)

    log = {"renamespaced": [], "dropped": [], "retyped": [], "added": [], "inlined": 0}

    # 1. drop the inverted axioms, by URI, before anything is rewritten
    for s, p, o, why in DROP:
        if (s, p, o) in g:
            g.remove((s, p, o))
            log["dropped"].append((f"{s.n3(g.namespace_manager)} "
                                   f"{p.n3(g.namespace_manager)} "
                                   f"{o.n3(g.namespace_manager)}", why))

    # 2. the inlined CRMtex 1.0 copy: remove its own class definitions, then move
    #    every remaining reference to the real namespace and the 2.0 names
    for s in list({s for s in g.subjects() if isinstance(s, URIRef)
                   and str(s).startswith(WRONG_TEX)}):
        for p, o in list(g.predicate_objects(s)):
            g.remove((s, p, o))
            log["inlined"] += 1
    for s, p, o in list(g):
        ns, no = _renamespace(s), _renamespace(o)
        if (ns, no) != (s, o):
            g.remove((s, p, o))
            g.add((ns, p, no))
            for old, new in ((s, ns), (o, no)):
                if old is not new:
                    log["renamespaced"].append((str(old), str(new)))

    # 3. ogham:Reading lost its parent with TX6_Transcription; give it one that exists
    for o in list(g.objects(OG["Reading"], RDFS.subClassOf)):
        g.remove((OG["Reading"], RDFS.subClassOf, o))
    g.add((OG["Reading"], RDFS.subClassOf, READING_PARENT))
    g.add((OG["Reading"], RDFS.isDefinedBy, REPO))
    log["retyped"].append(("ogham:Reading", "crmtex:TX7_Written_Text_Segment"))

    # 4. ogham:shows declares its range twice, which in RDFS is an intersection no
    #    instance can satisfy. Make it the union that was meant.
    ranges = sorted(g.objects(OG["shows"], RDFS.range), key=str)
    if len(ranges) > 1:
        for r in ranges:
            g.remove((OG["shows"], RDFS.range, r))
        union = BNode()
        members = BNode()
        Collection(g, members, list(ranges))
        g.add((union, RDF.type, OWL.Class))
        g.add((union, OWL.unionOf, members))
        g.add((OG["shows"], RDFS.range, union))
        g.add((OG["shows"], RDFS.isDefinedBy, REPO))
        log["retyped"].append(("ogham:shows range",
                               "owl:unionOf (" + ", ".join(
                                   r.n3(g.namespace_manager) for r in ranges) + ")"))

    # 5. the properties the crosswalk mints
    for name, kind, domain, rng, label, comment in ADDITIONS:
        u = OG[name]
        if (u, RDF.type, None) in g:
            continue
        g.add((u, RDF.type, kind))
        g.add((u, RDFS.label, Literal(label)))
        g.add((u, RDFS.comment, Literal(comment)))
        if isinstance(domain, tuple):
            # a kin group carries a normalised name form just as a person does
            union, members = BNode(), BNode()
            Collection(g, members, list(domain))
            g.add((union, RDF.type, OWL.Class))
            g.add((union, OWL.unionOf, members))
            g.add((u, RDFS.domain, union))
        elif domain is not None:
            g.add((u, RDFS.domain, domain))
        if rng is not None:
            g.add((u, RDFS.range, rng))
        g.add((u, RDFS.isDefinedBy, REPO))
        log["added"].append((name, label))

    g.bind("crmtex", TEX)
    g.bind("ogham", OG)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Turtle, not RDF/XML: the serialiser drops assertions on the blank node that
    # carries owl:unionOf, and a union that loses its type is not a union.
    g.serialize(destination=str(out), format="turtle")
    log["before"], log["after"] = before, len(g)
    _write_changes(changes_path, log, upstream, out)
    return log


def _write_changes(path: Path, log: dict, upstream: Path, out: Path) -> None:
    root = path.parent.parent
    rel = lambda q: q.relative_to(root).as_posix() if q.is_relative_to(root) else q.name
    L = []
    add = L.append
    add("# What this repository changes in `ogham.owl`\n")
    add(f"> **Generated** by `py/ontology_patch.py` on {dt.date.today().isoformat()}. "
        f"`{rel(upstream)}` is the published file and is never edited; "
        f"`{rel(out)}` is the corrected and extended version the pipeline "
        f"validates against. Re-running regenerates both this file and that one.\n")
    add(f"{log['before']} triples in, {log['after']} out.\n")

    add("## Corrections\n")
    add("### The embedded CRMtex was version 1.0, under a namespace CRMtex never used\n")
    add("The published file carries its own copy of CRMtex classes under "
        "`http://www.cidoc-crm.org/cidoc-crm/crmtex/`. CRMtex is published at "
        "`http://www.cidoc-crm.org/extensions/crmtex/`, so every one of those URIs "
        "resolved to nothing. The copy is also **CRMtex 1.0**, and 2.0 kept the "
        "numbers while changing the names:\n")
    add("| CRMtex 1.0 | CRMtex 2.0 |")
    add("|---|---|")
    add("| `TX5_Reading` | `TX5_Text_Recognition` |")
    add("| `TX6_Transcription` | `TX6_Transliteration` |")
    add("")
    add("2.0 also adds `TX14_Reading`, which is *not* the old TX5: it is the whole "
        "interpretive act, and it sits under `crminf:I1_Argumentation` — which is "
        "where a reading meets axis 2's belief model.\n")
    add(f"{log['inlined']} triples of the inlined 1.0 copy were removed, and "
        f"{len(set(log['renamespaced']))} references moved to the real namespace. "
        "The classes are not re-stated here: `ontologies/CRMtex_v2.0.rdf` is the "
        "definition.\n")

    if log["dropped"]:
        add("### Axioms that inverted the reference ontologies\n")
        for triple, why in log["dropped"]:
            add(f"- **Removed** `{triple}`  \n  {why}")
        add("")
        add("Together these two put CRM and CRMtex classes *underneath* ogham ones, "
            "which is why `ogham:Person` came out with `TX1_Written_Text` and "
            "`TX7_Written_Text_Segment` among its ancestors.\n")

    add("### `ogham:Reading` needed a parent that exists\n")
    add("It was declared under `TX6_Transcription`. Under CRMtex 2.0 that identifier "
        "is `TX6_Transliteration`, an `E65_Creation` — an *activity*. A reading "
        "**text** is not an activity, and `ogham:Reading` is used as one: it is the "
        "range of `ogham:identifiedAs`.\n")
    add("It is now `⊑ crmtex:TX7_Written_Text_Segment`, whose definition is *\"portions "
        "of text considered to be of particular significance by scholars\"* — which is "
        "what a competing reading is. **This is the one substantive modelling choice "
        "made here**, and the alternative is worth weighing: model the *act* of "
        "reading as `TX14_Reading` and attach the text to it. That is richer, it is "
        "the natural bridge to CRMinf, and it would change the shape of the graph.\n")
    add("### `ogham:shows` had two ranges\n")
    add("`rdfs:range` twice means an intersection: an instance would have to be both "
        "a `Person` and a `Word`. It is now `owl:unionOf`.\n")

    add(f"## Additions — {len(log['added'])} properties\n")
    add("The crosswalk records uncertainty and provenance, which the published "
        "ontology does not yet model. Rather than list them in a log on every run, "
        "they are declared here, each with a domain, a range and a comment, and each "
        "carrying `rdfs:isDefinedBy` pointing at this repository so their origin "
        "stays visible.\n")
    add("| property | what it says |")
    add("|---|---|")
    for name, label in log["added"]:
        add(f"| `ogham:{name}` | {label} |")
    add("")
    add("## Two things deliberately left alone\n")
    add("Both are places where the crosswalk and the ontology say different things "
        "and **both readings are defensible**, so neither side was quietly changed.\n")
    add("### `ogham:Material`\n")
    add("The ontology puts it under `crm:E55_Type`; the crosswalk emits materials as "
        "`crm:E57_Material`. Neither is wrong, because they are about different "
        "things: `crm:P45_consists_of` *requires* an `E57_Material` for its range, "
        "while a controlled vocabulary of Granite and Sandstone is naturally a set of "
        "types. Granite is honestly both. The choice is whether the instance carries "
        "both types, or whether the vocabulary and the material are separate nodes.\n")
    add("### `ogham:Person`\n")
    add("The ontology puts it under `foaf:Person`; the crosswalk emits `crm:E21_Person`. "
        "The names on an ogham stone are attested people, so `E21` is apt, and "
        "`foaf:Person` is the web-of-data anchor. Declaring `ogham:Person` under both "
        "would settle it, and costs nothing.\n")
    add("## How to fold this upstream\n")
    add("The generated file is a drop-in replacement, but the interesting part is "
        "smaller than that. The corrections are worth taking as they stand; the "
        "additions are a proposal. `py/validate.py` reports any term the crosswalk "
        "emits that is in neither file, so a term that is renamed upstream surfaces "
        "on the next run rather than drifting.\n")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
