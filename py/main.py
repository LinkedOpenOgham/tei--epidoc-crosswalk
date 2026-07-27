#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""main.py -- crosswalk OG(H)AM EpiDoc editions of ogham stones to CIDOC CRM / CRMtex.

Single entry point of the ``tei--epidoc-crosswalk`` repository (axis 1 of the
Linked Open Ogham crosswalk). Run from the repo root:

    python py/main.py            # process all stones in STONES, write out/README.md
    python py/main.py --input data/S-ARL-001.xml --output out/gigha1.crm.ttl

For each stone it maps the core EpiDoc elements to CIDOC CRM 7.1.3 and its text
extension CRMtex, emits Turtle, and documents the element-by-element result in a
generated ``out/README.md``.

Companion of ``tei--epidoc-amt`` (axis 2, vagueness modelling): axis 1 is the
structural crosswalk to the reference ontology; the competing-reading weights
live in axis 2.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from lxml import etree
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

# --- repo-root-relative paths -------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"          # inputs (EpiDoc XML)
OUT = ROOT / "out"            # generated outputs (TTL + README)

STONES = [
    ("S-ARL-001.xml", "gigha1"),
    ("I-COR-001.xml", "coomleagh-east"),
    ("I-COR-030.xml", "garranes"),
    ("I-KER-020.xml", "ballinrannig6"),
]

# identifier systems we crosswalk to E42 (external IDs / LOD hubs); others skipped
ID_SYSTEMS = ["CIIC", "CISP", "TM", "SMR", "Trove"]

# --- namespaces (aligned with the ogham.link ontology) ------------------------
TEI = "http://www.tei-c.org/ns/1.0"
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
CRMTEX = Namespace("http://www.cidoc-crm.org/cidoc-crm/crmtex/")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
OGHAM = Namespace("http://ontology.ogham.link/")
DATA_NS = Namespace("http://data.ogham.link/crm/")

# The core crosswalk (EpiDoc element -> CIDOC CRM / CRMtex). Drives emission AND
# the generated documentation, so both always agree.
MAPPING = [
    ("<support> (msDesc)",          "the stone",             "crm:E22_Human-Made_Object", "(root node)"),
    ("<idno type=CIIC|CISP|TM|SMR|Trove>", "identifiers",    "crm:E42_Identifier",        "P1_is_identified_by (+ P2_has_type)"),
    ("<objectType>",                "object type",           "crm:E55_Type",              "P2_has_type"),
    ("<material>",                  "material",              "crm:E57_Material",          "P45_consists_of"),
    ("inscribed surface / <layout>","inscribed face",        "crm:E25_Human-Made_Feature","P56_bears_feature"),
    ("<div type=edition>",          "inscription text",      "crmtex:TX1_Written_Text",   "P128_carries"),
    ("<origPlace> + <geo>",         "place of origin",       "crm:E53_Place",             "P53_has_former_or_current_location (+ geo:asWKT)"),
    ("<name nymRef> / <persName>",  "referenced name",       "crm:E21_Person",            "P67_refers_to (from TX1)"),
]


def _text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text or "").strip("_") or "x"


def parse(tree) -> dict:
    """Extract the core elements that the crosswalk maps."""
    d: dict = {}
    idnos = {i.get("type"): (i.text or "").strip() for i in tree.findall(f".//{{{TEI}}}idno[@type]")}
    d["ids"] = {k: v for k, v in idnos.items() if k in ID_SYSTEMS and v}
    d["ciic"] = idnos.get("CIIC", idnos.get("filename", "x"))
    d["title"] = _text(tree.find(f".//{{{TEI}}}title"))
    d["material"] = _text(tree.find(f".//{{{TEI}}}material")) or None
    d["objectType"] = _text(tree.find(f".//{{{TEI}}}objectType")) or None

    # edition transliteration (reader-facing <ab>)
    div = tree.find(f".//{{{TEI}}}div[@type='edition'][@subtype='transliteration']")
    if div is None:
        div = tree.find(f".//{{{TEI}}}div[@type='edition']")
    if div is not None:
        ab = div.findall(f".//{{{TEI}}}ab")
        d["edition"] = _text(ab[-1]) if ab else _text(div)
    else:
        d["edition"] = ""

    # place of origin: placeName + coordinates
    placeName = tree.find(f".//{{{TEI}}}origPlace//{{{TEI}}}placeName")
    if placeName is not None:
        d["place"] = _text(placeName)
    else:
        op = _text(tree.find(f".//{{{TEI}}}origPlace"))
        d["place"] = re.split(r"\d", op)[0].strip(" ,") if op else None
    geo = _text(tree.find(f".//{{{TEI}}}geo"))
    m = re.findall(r"-?\d+\.\d+", geo)
    d["latlon"] = (float(m[0]), float(m[1])) if len(m) >= 2 else None

    # referenced names (Latin transliteration, de-duplicated)
    names, seen = [], set()
    for n in tree.findall(f".//{{{TEI}}}name[@nymRef]"):
        t = _text(n)
        if t and re.fullmatch(r"[A-Za-z ]+", t) and t.upper() not in seen:
            seen.add(t.upper())
            names.append(t)
    d["names"] = names
    return d


def build_graph(d: dict):
    """Emit the CIDOC CRM / CRMtex triples; also return per-element records."""
    g = Graph()
    for pfx, ns in (("crm", CRM), ("crmtex", CRMTEX), ("geo", GEO),
                    ("ogham", OGHAM), ("data", DATA_NS), ("rdfs", RDFS), ("xsd", XSD)):
        g.bind(pfx, ns)

    ciic = d["ciic"]
    sid = _slug(ciic)
    records: list[tuple] = []   # (element, value, crm_class, node)

    # 1) the stone -> E22 (with the ogham.link domain type, which is rdfs:subClassOf E22)
    stone = DATA_NS[f"stone_{sid}"]
    g.add((stone, RDF.type, CRM["E22_Human-Made_Object"]))
    g.add((stone, RDF.type, OGHAM.OghamStone))
    g.add((stone, RDFS.label, Literal(f"{d['title'] or 'Ogham stone'} (CIIC {ciic})")))
    records.append(("<support>", d["title"], "E22_Human-Made_Object", f"data:stone_{sid}"))

    # 2) identifiers -> E42
    for system, value in d["ids"].items():
        idn = DATA_NS[f"id_{sid}_{system}"]
        g.add((idn, RDF.type, CRM["E42_Identifier"]))
        g.add((idn, RDFS.label, Literal(value)))
        g.add((idn, CRM["P2_has_type"], Literal(system)))
        g.add((stone, CRM["P1_is_identified_by"], idn))
        records.append((f"<idno type={system}>", value, "E42_Identifier", f"data:id_{sid}_{system}"))

    # 3) object type -> E55
    if d["objectType"]:
        typ = DATA_NS[f"type_{_slug(d['objectType'])}"]
        g.add((typ, RDF.type, CRM["E55_Type"]))
        g.add((typ, RDFS.label, Literal(d["objectType"])))
        g.add((stone, CRM["P2_has_type"], typ))
        records.append(("<objectType>", d["objectType"], "E55_Type", f"data:type_{_slug(d['objectType'])}"))

    # 4) material -> E57
    if d["material"]:
        mat = DATA_NS[f"material_{_slug(d['material'])}"]
        g.add((mat, RDF.type, CRM["E57_Material"]))
        g.add((mat, RDFS.label, Literal(d["material"])))
        g.add((stone, CRM["P45_consists_of"], mat))
        records.append(("<material>", d["material"], "E57_Material", f"data:material_{_slug(d['material'])}"))

    # 5) inscribed surface -> E25
    surface = DATA_NS[f"surface_{sid}"]
    g.add((surface, RDF.type, CRM["E25_Human-Made_Feature"]))
    g.add((surface, RDFS.label, Literal("inscribed surface")))
    g.add((stone, CRM["P56_bears_feature"], surface))
    records.append(("inscribed surface", "inscribed face", "E25_Human-Made_Feature", f"data:surface_{sid}"))

    # 6) inscription text -> crmtex:TX1, carried by the stone
    inscr = DATA_NS[f"inscription_{sid}"]
    g.add((inscr, RDF.type, CRMTEX["TX1_Written_Text"]))
    g.add((inscr, RDF.type, OGHAM.Inscription))
    if d["edition"]:
        g.add((inscr, RDFS.label, Literal(d["edition"])))
    g.add((stone, CRM["P128_carries"], inscr))
    records.append(("<div type=edition>", d["edition"], "crmtex:TX1_Written_Text", f"data:inscription_{sid}"))

    # 7) place of origin -> E53 (+ GeoSPARQL geometry)
    if d["place"] or d["latlon"]:
        place = DATA_NS[f"place_{sid}"]
        g.add((place, RDF.type, CRM["E53_Place"]))
        if d["place"]:
            g.add((place, RDFS.label, Literal(d["place"])))
        g.add((stone, CRM["P53_has_former_or_current_location"], place))
        wkt = ""
        if d["latlon"]:
            lat, lon = d["latlon"]
            wkt = f"POINT({lon} {lat})"
            g.add((place, GEO.asWKT, Literal(wkt, datatype=GEO.wktLiteral)))
        records.append(("<origPlace> + <geo>", (d["place"] or "") + (f" · {wkt}" if wkt else ""),
                        "E53_Place", f"data:place_{sid}"))

    # 8) referenced names -> E21 Person, referred to by the inscription
    for name in d["names"]:
        person = DATA_NS[f"person_{sid}_{_slug(name)}"]
        g.add((person, RDF.type, CRM["E21_Person"]))
        g.add((person, RDFS.label, Literal(name)))
        g.add((inscr, CRM["P67_refers_to"], person))
        records.append(("<name nymRef>", name, "E21_Person", f"data:person_{sid}_{_slug(name)}"))

    return g, records


# --- generated documentation --------------------------------------------------
def write_out_readme(results: list[tuple]) -> None:
    L, add = [], None
    L = []
    add = L.append
    esc = lambda s: str(s).replace("|", "\\|")
    add("# `out/` — TEI/EpiDoc → CIDOC CRM crosswalk\n")
    add("> **Generated file** — produced by `python py/main.py`. Do not edit by hand; "
        "it adapts to the EpiDoc inputs and to the `MAPPING` in `py/main.py`.\n")

    add("## 1. What the crosswalk does\n")
    add("For each ogham stone the core EpiDoc elements are mapped to **CIDOC CRM 7.1.3** "
        "and its text extension **CRMtex**, and serialised as RDF/Turtle "
        "(`out/<stone>.crm.ttl`). Instances also carry the matching `ogham.link` class, "
        "which is `rdfs:subClassOf` the CRM class — so the domain ontology *is* the "
        "crosswalk. The competing-reading weights are modelled separately in "
        "`tei--epidoc-amt` (axis 2).\n")

    add("## 2. The crosswalk (EpiDoc element → CIDOC CRM / CRMtex)\n")
    add("| EpiDoc element | role | CRM/CRMtex class | CRM property |")
    add("|---|---|---|---|")
    for el, role, klass, prop in MAPPING:
        add(f"| `{esc(el)}` | {esc(role)} | `{esc(klass)}` | `{esc(prop)}` |")
    add("")
    add("Namespaces: `crm: http://www.cidoc-crm.org/cidoc-crm/`, "
        "`crmtex: …/cidoc-crm/crmtex/`, `geo: http://www.opengis.net/ont/geosparql#`, "
        "`ogham: http://ontology.ogham.link/`.\n")
    add("Open modelling decisions (documented): material as `E57_Material` (CRM-conformant) "
        "vs. the ontology's `Material ⊑ E55`; place of origin via `P53` vs. a richer "
        "`E12_Production` / `E9_Move` event; readings as `crmtex:TX5/TX6` handled in axis 2.\n")

    add("## 3. Per stone — how each element ends up in CIDOC CRM\n")
    for title, ciic, out, records in results:
        add(f"### {title} (CIIC {ciic})\n")
        add(f"`{out}` — {len(records)} mapped elements.\n")
        add("| EpiDoc element | extracted value | → CRM class | node |")
        add("|---|---|---|---|")
        for el, val, klass, node in records:
            v = (val or "").strip()
            v = v if len(v) <= 40 else v[:37] + "…"
            add(f"| `{esc(el)}` | {esc(v) or '—'} | `{esc(klass)}` | `{esc(node)}` |")
        add("")

    (OUT / "README.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  -> wrote {(OUT / 'README.md').relative_to(ROOT)}")


def process(input_path: Path, output_path: Path):
    tree = etree.parse(str(input_path))
    d = parse(tree)
    g, records = build_graph(d)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(output_path), format="turtle")
    print(f"\n{d['title'] or '?'} (CIIC {d['ciic']}) -- {len(records)} elements -> "
          f"{output_path.relative_to(ROOT)} ({len(g)} triples)")
    for el, val, klass, node in records:
        v = (val or "")[:38]
        print(f"  {el:26} -> {klass:26} {v}")
    return d["title"] or "?", d["ciic"], output_path.name, records


def main() -> None:
    ap = argparse.ArgumentParser(description="EpiDoc -> CIDOC CRM (Linked Open Ogham, axis 1)")
    ap.add_argument("--input", type=Path, help="single EpiDoc file (default: all stones)")
    ap.add_argument("--output", type=Path, help="output Turtle file (single-file mode only)")
    args = ap.parse_args()

    if args.input:
        out = args.output or (OUT / (args.input.stem + ".crm.ttl"))
        process(args.input, out)
    else:
        results = [process(DATA / f, OUT / f"{b}.crm.ttl") for f, b in STONES]
        write_out_readme(results)


if __name__ == "__main__":
    main()
