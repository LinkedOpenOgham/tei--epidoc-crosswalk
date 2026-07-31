#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate.py -- check what the crosswalk emits against the ontologies it claims.

Until this existed, a run reported ``crosswalk SHACL: VALID`` and meant that twelve
class declarations in ``crosswalk.ttl`` were well formed. The twenty thousand
triples in ``out/*.crm.ttl`` -- the actual graph -- were never checked against
anything. A property used with the wrong kind of subject, or a class name that does
not exist in CIDOC CRM at all, passed silently.

Three checks, in order of how badly they bite:

1. **Does the term exist?** Every class and property in a CRM, CRMtex, ogham or AMT
   namespace is looked up in the local copy under ``ontologies/``. This is what
   catches ``crmtex:TX6_Transcription``, a class the crosswalk used from the start
   and which CRMtex does not define under that name.

2. **Domain and range.** For every property with a declared domain or range, the
   subject and object are checked against it, following ``rdfs:subClassOf``. This
   is what catches a ``TXP4_has_segment`` whose object is not a
   ``TX7_Written_Text_Segment``.

3. **Subclass claims.** Where the crosswalk asserts that one of its own classes
   sits under a CRM class, that claim is compared with what the ogham ontology
   actually says -- ``ogham:Place`` is a Pleiades place, not a ``crm:E53_Place``,
   and a crosswalk that assumes otherwise is quietly wrong.

Nothing here is fixed automatically. A domain violation is usually a modelling
decision, and those belong to the person who owns the ontology.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from rdflib import BNode, Graph, RDF, RDFS, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL

WATCHED = {
    "http://www.cidoc-crm.org/cidoc-crm/": "crm",
    "http://www.cidoc-crm.org/extensions/crmtex/": "crmtex",
    "http://www.cidoc-crm.org/cidoc-crm/crmtex/": "crmtex(wrong ns)",
    "http://ontology.ogham.link/": "ogham",
    "http://academic-meta-tool.xyz/vocab#": "amt",
}

# Terms the crosswalk defines for itself. Legitimately absent from the reference
# ontologies; listed so they are reported as "new" rather than as "unknown".
LOCAL_NS = "http://ontology.ogham.link/"


def short(uri: str) -> str:
    for ns, pfx in WATCHED.items():
        if uri.startswith(ns):
            return f"{pfx}:{uri[len(ns):]}"
    return uri


def load_reference(directory: Path) -> Graph:
    g = Graph()
    for name in ("ogham.ttl", "CIDOC_CRM_v7.1.3.rdf", "CRMtex_v2.0.rdf", "amt.ttl"):
        path = directory / name
        if path.exists():
            g.parse(str(path))
    return g


def _closure(g: Graph, start: URIRef, predicate) -> set:
    """Everything reachable from ``start`` along ``predicate``, plus start."""
    seen, stack = {start}, [start]
    while stack:
        node = stack.pop()
        for parent in g.objects(node, predicate):
            if isinstance(parent, URIRef) and parent not in seen:
                seen.add(parent)
                stack.append(parent)
    return seen


class Reference:
    def __init__(self, g: Graph):
        self.g = g
        self.known = {str(s) for s in g.subjects() if isinstance(s, URIRef)}
        self.domain = {str(s): self._expand(o) for s, o in g.subject_objects(RDFS.domain)}
        self.range = {str(s): self._expand(o) for s, o in g.subject_objects(RDFS.range)}
        self._super = {}

    def _expand(self, node) -> tuple[str, ...]:
        """A class, or the members of an owl:unionOf. A union range is satisfied by
        any one member; treating the blank node itself as the expected class is how
        a perfectly good union came out as a violation 626 times."""
        if isinstance(node, BNode):
            for lst in self.g.objects(node, OWL.unionOf):
                return tuple(str(m) for m in Collection(self.g, lst))
            return ()
        return (str(node),)

    def supers(self, cls: str) -> set:
        if cls not in self._super:
            self._super[cls] = {str(x) for x in _closure(self.g, URIRef(cls), RDFS.subClassOf)}
        return self._super[cls]

    def is_a(self, types: set[str], expected) -> bool:
        options = expected if isinstance(expected, tuple) else (expected,)
        return any(opt in self.supers(t) for t in types for opt in options)


def check(data: Graph, ref: Reference) -> dict:
    """Unknown terms, domain and range violations, in the emitted graph."""
    unknown_terms = defaultdict(int)
    new_local = defaultdict(int)
    violations = defaultdict(list)

    types = defaultdict(set)
    for s, o in data.subject_objects(RDF.type):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            types[str(s)].add(str(o))

    for s, p, o in data:
        for term, position in ((p, "property"), (o if p == RDF.type else None, "class")):
            if not isinstance(term, URIRef):
                continue
            uri = str(term)
            if not any(uri.startswith(ns) for ns in WATCHED):
                continue
            if uri in ref.known:
                continue
            (new_local if uri.startswith(LOCAL_NS) else unknown_terms)[
                f"{short(uri)} ({position})"] += 1

        pu = str(p)
        if not any(pu.startswith(ns) for ns in WATCHED) or pu not in ref.known:
            continue
        expected_dom = ref.domain.get(pu)
        if expected_dom and isinstance(s, URIRef):
            have = types.get(str(s), set())
            if have and not ref.is_a(have, expected_dom):
                violations[f"{short(pu)} domain should be "
                           f"{' or '.join(short(x) for x in expected_dom)}"].append(
                    f"{short(str(s))} is {', '.join(sorted(short(t) for t in have))}")
        expected_rng = ref.range.get(pu)
        if expected_rng and isinstance(o, URIRef):
            have = types.get(str(o), set())
            if have and not ref.is_a(have, expected_rng):
                violations[f"{short(pu)} range should be "
                           f"{' or '.join(short(x) for x in expected_rng)}"].append(
                    f"{short(str(o))} is {', '.join(sorted(short(t) for t in have))}")

    return {"unknown": dict(unknown_terms), "new_local": dict(new_local),
            "violations": {k: v for k, v in violations.items()}}


def subclass_claims(crosswalk: Graph, ref: Reference) -> list[str]:
    """Where the crosswalk says one of its classes is under a CRM class, does the
    ogham ontology agree?"""
    out = []
    for s, o in crosswalk.subject_objects(RDFS.subClassOf):
        if not (isinstance(s, URIRef) and isinstance(o, URIRef)):
            continue
        if not str(s).startswith(LOCAL_NS):
            continue
        if str(s) not in ref.known:
            continue
        if str(o) in ref.supers(str(s)) - {str(s)}:
            continue
        # the direct parents are what a reader needs; the transitive closure of a
        # CRM class runs to twenty lines and buries the point
        direct = sorted(str(x) for x in ref.g.objects(URIRef(str(s)), RDFS.subClassOf)
                        if isinstance(x, URIRef))
        claimed_name = str(o).rsplit("/", 1)[-1]
        same_name = [a for a in direct if a.rsplit("/", 1)[-1] == claimed_name]
        if same_name:
            out.append(f"{short(str(s))}: both say {claimed_name}, but the ontology "
                       f"writes it as {same_name[0]} -- a namespace that defines nothing")
        else:
            declared = ", ".join(short(a) for a in direct) or "nothing"
            out.append(f"{short(str(s))}: crosswalk says {short(str(o))}, "
                       f"ontology says {declared}")
    return out


def run(out_dir: Path, ontologies: Path, root: Path | None = None) -> dict:
    ref_graph = load_reference(ontologies)
    if not len(ref_graph):
        print("  ! no reference ontologies under ontologies/; skipping validation")
        return {}
    ref = Reference(ref_graph)

    data = Graph()
    files = sorted(out_dir.glob("*.crm.ttl"))
    for path in files:
        data.parse(str(path), format="turtle")
    crosswalk = Graph()
    if (out_dir / "crosswalk.ttl").exists():
        crosswalk.parse(str(out_dir / "crosswalk.ttl"), format="turtle")

    result = check(data, ref)
    result["subclass"] = subclass_claims(crosswalk, ref)
    result["triples"] = len(data)
    result["files"] = len(files)

    rel = (lambda p: p.relative_to(root)) if root else (lambda p: p)
    print(f"\nA-box validation -- {len(data)} triples from {len(files)} graphs "
          f"against {len(ref_graph)} reference triples")

    if result["unknown"]:
        print(f"  {len(result['unknown'])} term(s) not defined in any reference ontology:")
        for term, n in sorted(result["unknown"].items(), key=lambda x: -x[1]):
            print(f"    {term:52} {n} use(s)")
    if result["violations"]:
        total = sum(len(v) for v in result["violations"].values())
        print(f"  {len(result['violations'])} domain/range rule(s) broken, {total} times:")
        for rule, cases in sorted(result["violations"].items(),
                                  key=lambda x: -len(x[1])):
            print(f"    {rule}  ({len(cases)}x)")
            print(f"      e.g. {cases[0]}")
    if result["subclass"]:
        print(f"  {len(result['subclass'])} subclass claim(s) the ontology does not support:")
        for line in result["subclass"]:
            print(f"    {line}")
    if result["new_local"]:
        # These should now be empty: py/ontology_patch.py declares them. If one
        # appears, a property was added to the crosswalk and not to the ontology.
        print(f"  ! {len(result['new_local'])} term(s) emitted but declared nowhere -- "
              f"add them to ADDITIONS in py/ontology_patch.py:")
        for term, n in sorted(result["new_local"].items()):
            print(f"    {term:52} {n} use(s)")
    if not (result["unknown"] or result["violations"] or result["subclass"]):
        print("  no unknown terms, no domain or range violations")
    return result
