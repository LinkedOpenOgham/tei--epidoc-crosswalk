#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""persons.py -- the people named on the stones, and how they are related.

The relationship does not have to be guessed from word order: the corpus marks it.

    <persName>
      <name nymRef="#cassittas">CASSITTAS</name>
      <w type="formula" lemma="maqqas">MAQI</w>
      <w type="formula" lemma="muccoviias">MUCOI</w>
      <name nymRef="#calliti">CALLITI</name>
    </persName>

``<persName>`` wraps the whole person phrase, ``<name nymRef>`` gives the normalised
name, and ``<w type="formula" lemma="…">`` gives the relation, lemmatised. Two
formula words in a row are **one** relation, not two: *MAQI MUCOI X* is "son of the
kin of X", and splitting it would assert both that CASSITTAS is the son of CALLITI
and that he is of CALLITI's kin, where the inscription says one thing.

Three distinctions the extractor keeps, because collapsing any of them would invent
a network the stones do not carry:

**Asserted against hypothetical.** Within one inscription an edge is what the text
says. *Across* inscriptions, two occurrences of a name are the same string, not
demonstrably the same person -- and often demonstrably not: ``maqqas_treni`` is
"son of Trenus", a patronymic, on stones in Cork and in Pembrokeshire. Those links
are kept apart and drawn apart.

**Anonymous ends stay separate.** 144 name slots read ``nymRef="#?"``. "Someone, son
of Vobarracas" is a real statement, but every ``?`` is a *different* unknown person,
so each occurrence gets its own node rather than all of them merging into one
very well-connected stranger.

**Kin groups are not people.** The object of ``muccoviias`` is a *túath*, so it
becomes an ``ogham:OghamTribe``, not an ``ogham:Person``.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

from lxml import etree
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

TEI = "http://www.tei-c.org/ns/1.0"
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
OGHAM = Namespace("http://ontology.ogham.link/")
DATA_NS = Namespace("http://data.ogham.link/crm/")
LOD = Namespace("http://lod.ogham.link/data/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
AMT = Namespace("http://academic-meta-tool.xyz/vocab#")

ANON = {"?", "", "...", "…"}

# What each lemma asserts. `parent` maps onto crm:P152_has_parent; `kin` makes the
# object a tribe rather than a person.
RELATIONS = {
    "maqqas": ("son of", "parent"),
    "filius": ("son of (Latin)", "parent"),
    "avias": ("grandson or descendant of", "descent"),
    "muccoviias": ("of the kin of", "kin"),
    "celi": ("client or follower of", "social"),
    "celias": ("client or follower of", "social"),
    "c\u0113lias": ("client or follower of", "social"),
    "koi": ("here (lies)", "marker"),
    "anmen": ("name of", "marker"),
    "anm": ("name of", "marker"),
    "netta": ("nephew or sister's son of", "descent"),
    "inigena": ("daughter of", "parent"),
}


def _local(el) -> str:
    return etree.QName(el).localname


def _text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def normalise_nym(value: str) -> str:
    """`#maqqas-treni` and `#maqqas_treni` are the same name written two ways."""
    return value.lstrip("#").strip().replace("-", "_")


def parse_stone(tree, ogham_id: str) -> dict:
    """Person slots and relations from one edition.

    Only the transliteration division: the ogham-script division repeats the same
    <persName> elements, and counting both would double every edge.
    """
    slots, edges = [], []
    div = tree.find(f".//{{{TEI}}}div[@type='edition'][@subtype='transliteration']")
    if div is None:
        return {"slots": slots, "edges": edges}

    for phrase_i, phrase in enumerate(div.findall(f".//{{{TEI}}}persName")):
        seq = []
        for el in phrase.iter():
            if not isinstance(el.tag, str):
                continue
            tag = _local(el)
            if tag == "name" and el.get("nymRef") is not None:
                raw = normalise_nym(el.get("nymRef"))
                anon = raw in ANON or raw.strip("?") == ""
                slot = {
                    "id": (f"{ogham_id}/anon{phrase_i}_{len(seq)}" if anon
                           else f"name/{raw}"),
                    "nym": "" if anon else raw,
                    "surface": _text(el),
                    "anonymous": anon,
                    "uncertain": raw.endswith("?"),
                    "stone": ogham_id,
                }
                seq.append(("name", slot))
                slots.append(slot)
            elif tag == "w" and (el.get("type") or "") == "formula":
                lemma = (el.get("lemma") or "").strip("#").strip()
                if lemma:
                    seq.append(("rel", {"lemma": lemma.rstrip("?"),
                                        "surface": _text(el),
                                        "uncertain": lemma.endswith("?")}))

        # consecutive formula words are one compound relation
        merged, i = [], 0
        while i < len(seq):
            kind, item = seq[i]
            if kind != "rel":
                merged.append((kind, item))
                i += 1
                continue
            run = [item]
            while i + 1 < len(seq) and seq[i + 1][0] == "rel":
                run.append(seq[i + 1][1])
                i += 1
            merged.append(("rel", {
                "lemma": "+".join(r["lemma"] for r in run),
                "surface": " ".join(r["surface"] for r in run),
                "uncertain": any(r["uncertain"] for r in run),
                "parts": [r["lemma"] for r in run],
            }))
            i += 1

        for j, (kind, item) in enumerate(merged):
            if kind != "rel":
                continue
            before = [x for k, x in merged[:j] if k == "name"]
            after = [x for k, x in merged[j + 1:] if k == "name"]
            if not (before and after):
                continue
            parts = item.get("parts", [item["lemma"]])
            kinds = {RELATIONS.get(p, ("", "other"))[1] for p in parts}
            edges.append({
                "stone": ogham_id,
                "from": before[-1]["id"],
                "to": after[0]["id"],
                "lemma": item["lemma"],
                "surface": item["surface"],
                "uncertain": item["uncertain"],
                "gloss": " and ".join(RELATIONS.get(p, (p, ""))[0] for p in parts),
                "kinds": sorted(kinds),
                "object_is_kin": "kin" in kinds,
            })
    return {"slots": slots, "edges": edges}


def scan(files, parse_xml, is_edition) -> dict:
    slots, edges = [], []
    for path in files:
        tree = parse_xml(path)
        if tree is None:
            continue
        idno = tree.find(f".//{{{TEI}}}idno[@type='filename']")
        ogham_id = (idno.text or "").strip() if idno is not None else path.stem
        if not is_edition({"ogham_id": ogham_id}):
            continue
        found = parse_stone(tree, ogham_id)
        slots.extend(found["slots"])
        edges.extend(found["edges"])

    # a name attested on more than one stone: a hypothesis, not a fact
    stones_by_name = defaultdict(set)
    for s in slots:
        if s["nym"]:
            stones_by_name[s["nym"]].add(s["stone"])
    shared = {n: sorted(v) for n, v in stones_by_name.items() if len(v) > 1}

    return {"slots": slots, "edges": edges, "shared_names": shared,
            "stones_by_name": {k: sorted(v) for k, v in stones_by_name.items()}}


def components(slots: list[dict], edges: list[dict]) -> list[dict]:
    """Groups joined by asserted relations only."""
    parent: dict[str, str] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in edges:
        a, b = find(e["from"]), find(e["to"])
        if a != b:
            parent[a] = b

    groups = defaultdict(lambda: {"nodes": set(), "edges": [], "stones": set()})
    for e in edges:
        g = groups[find(e["from"])]
        g["nodes"].update({e["from"], e["to"]})
        g["edges"].append(e)
        g["stones"].add(e["stone"])
    out = []
    for key, g in groups.items():
        out.append({"key": key, "nodes": sorted(g["nodes"]),
                    "edges": g["edges"], "stones": sorted(g["stones"])})
    out.sort(key=lambda c: (-len(c["stones"]), -len(c["nodes"]), c["key"]))
    return out


def reconcile(slots: list[dict], published: Path | None) -> dict[str, str]:
    """Link a name to the published person vocabulary at lod.ogham.link where the
    label matches. Only 26 of 224 do: the published list comes from Ogham in 3D and
    the EpiDoc editions use their own normalised forms, so most names here are new."""
    if not published or not published.exists():
        return {}
    g = Graph()
    g.parse(str(published), format="turtle")
    labels: dict[str, str] = {}
    for s in g.subjects(RDF.type, OGHAM.Person):
        for lab in g.objects(s, RDFS.label):
            labels.setdefault(str(lab).strip().lower(), str(s))
    out = {}
    for s in slots:
        if not s["nym"]:
            continue
        for key in (s["nym"], s["nym"].rstrip("?"), s["nym"].replace("_", "-")):
            if key.lower() in labels:
                out[s["nym"]] = labels[key.lower()]
                break
    return out


CSV_FIELDS = ["stone", "from_name", "relation_lemma", "relation_surface", "relation_gloss",
              "to_name", "object_is_kin_group", "uncertain", "from_anonymous",
              "to_anonymous"]


def write_csv(slots: list[dict], edges: list[dict], path: Path) -> int:
    by_id = {s["id"]: s for s in slots}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        for e in edges:
            a, b = by_id.get(e["from"], {}), by_id.get(e["to"], {})
            w.writerow({
                "stone": e["stone"],
                "from_name": a.get("surface", ""), "to_name": b.get("surface", ""),
                "relation_lemma": e["lemma"], "relation_surface": e["surface"],
                "relation_gloss": e["gloss"],
                "object_is_kin_group": "yes" if e["object_is_kin"] else "no",
                "uncertain": "yes" if e["uncertain"] else "no",
                "from_anonymous": "yes" if a.get("anonymous") else "no",
                "to_anonymous": "yes" if b.get("anonymous") else "no",
            })
    return len(edges)


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text or "").strip("_") or "x"


def build_graph(slots: list[dict], edges: list[dict], links: dict[str, str],
                stone_key) -> tuple[Graph, dict]:
    g = Graph()
    for pfx, ns in (("crm", CRM), ("ogham", OGHAM), ("data", DATA_NS), ("lod", LOD),
                    ("skos", SKOS), ("amt", AMT), ("rdfs", RDFS), ("xsd", XSD)):
        g.bind(pfx, ns)

    # A kin group is not the ancestor it is named after, and the same name can be a
    # person on one stone and a tuath on another. So the group gets its own node
    # rather than the person node changing type -- which had made a name a tribe
    # everywhere as soon as it was one anywhere.
    kin_objects = {e["to"] for e in edges if e["object_is_kin"]}

    def node_for(slot_id: str, as_kin: bool = False):
        return DATA_NS[("tribe_" if as_kin else "person_") + _slug(slot_id)]

    seen = set()
    for s in slots:
        if s["id"] in seen:
            continue
        seen.add(s["id"])
        node = node_for(s["id"])
        label = Literal(s["surface"] or s["nym"] or "unnamed")
        g.add((node, RDF.type, CRM["E21_Person"]))
        g.add((node, RDF.type, OGHAM.Person))
        g.add((node, RDFS.label, label))
        if s["nym"]:
            g.add((node, OGHAM.nymReference, Literal(s["nym"])))
        if s["anonymous"]:
            g.add((node, OGHAM.anonymousInEdition, Literal(True, datatype=XSD.boolean)))
        g.add((DATA_NS[f"stone_{_slug(s['stone'])}"], OGHAM.shows, node))
        target = links.get(s["nym"])
        if target:
            g.add((node, SKOS.closeMatch, URIRef(target)))
        if s["id"] in kin_objects:
            kin = node_for(s["id"], True)
            g.add((kin, RDF.type, OGHAM.OghamTribe))
            g.add((kin, RDFS.label, Literal(f"kin of {s['surface'] or s['nym']}")))
            # named after the person, not identical with them
            g.add((kin, OGHAM.nymReference, Literal(s["nym"] or "")))

    for i, e in enumerate(edges):
        src = node_for(e["from"])
        dst = node_for(e["to"], e["object_is_kin"])
        if "parent" in e["kinds"] and not e["object_is_kin"]:
            g.add((src, CRM["P152_has_parent"], dst))
        if not e["object_is_kin"]:
            g.add((src, OGHAM.relatedTo, dst))
        st = DATA_NS[f"relation_{_slug(e['stone'])}_{i}"]
        g.add((st, RDF.type, RDF.Statement))
        g.add((st, RDF.subject, src))
        g.add((st, RDF.predicate, OGHAM.relatedTo))
        g.add((st, RDF.object, dst))
        g.add((st, OGHAM.relationLemma, Literal(e["lemma"])))
        g.add((st, RDFS.label, Literal(e["gloss"])))
        g.add((st, RDFS.comment, Literal(e["surface"])))
        # asserted by one inscription: the weight is the editors', not ours
        g.add((st, AMT.weight, Literal("0.90" if e["uncertain"] else "1.00",
                                       datatype=XSD.decimal)))

    return g, {"persons": len(seen), "tribes": len(kin_objects),
               "relations": len(edges), "linked": len(set(links.values()))}
