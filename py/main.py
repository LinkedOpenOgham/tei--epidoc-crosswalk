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

Companion of ``tei--epidoc-amt`` (axis 2). Axis 1 is the **structural** crosswalk:
it models the inscription and every competing reading in CRMtex (who read what).
Axis 2 adds the ``amt:weight`` belief layer on top of the same readings.

Modelling follows the ``ogham.link`` ontology (whose classes are rdfs:subClassOf
the CRM classes), so the domain ontology *is* the crosswalk.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from lxml import etree
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD

# --- repo-root-relative paths -------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "out"

STONES = [
    ("S-ARL-001.xml", "gigha1"),
    ("I-COR-001.xml", "coomleagh-east"),
    ("I-COR-030.xml", "garranes"),
    ("I-KER-020.xml", "ballinrannig6"),
]

ID_SYSTEMS = ["CIIC", "CISP", "TM", "SMR", "Trove"]
EDITOR_PREFIXES = {"RHY": "Rhys", "MAC": "Macalister", "DIA": "Diack",
                   "JAC": "Jackson", "FOR": "Forsyth"}

# --- namespaces (aligned with the ogham.link ontology) ------------------------
TEI = "http://www.tei-c.org/ns/1.0"
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
CRMTEX = Namespace("http://www.cidoc-crm.org/cidoc-crm/crmtex/")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
PROV = Namespace("http://www.w3.org/ns/prov#")
OGHAM = Namespace("http://ontology.ogham.link/")
DATA_NS = Namespace("http://data.ogham.link/crm/")

# The core crosswalk. Drives emission AND the generated documentation.
MAPPING = [
    ("<support> (msDesc)",          "the stone",           "crm:E22_Human-Made_Object",  "(root node)"),
    ("<idno type=CIIC|CISP|TM|SMR|Trove>", "identifiers",  "crm:E42_Identifier",         "P1_is_identified_by (+ P2_has_type)"),
    ("<objectType>",                "object type",         "crm:E55_Type",               "P2_has_type"),
    ("<material>",                  "material",            "crm:E57_Material",           "P45_consists_of"),
    ("inscribed surface / <layout>","inscribed face",      "crm:E25_Human-Made_Feature", "P56_bears_feature"),
    ("<div type=edition>",          "inscription text",    "crmtex:TX1_Written_Text",    "P128_carries"),
    ("<div type=edition> / <rdg>",  "readings",            "crmtex:TX6_Transcription",   "TXP4_has_segment (from TX1) + prov:wasAttributedTo"),
    ("<origPlace> + <geo>",         "place of origin",     "crm:E53_Place",              "P53_has_former_or_current_location (+ geo:asWKT)"),
    ("<name nymRef> / <persName>",  "referenced name",     "crm:E21_Person",             "P67_refers_to (from TX1)"),
]


def _text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text or "").strip("_") or "x"


def editor_label(source_id: str) -> str:
    m = re.match(r"([A-Za-z]+)(\d{4})", source_id or "")
    if not m:
        return source_id or "OGHAM edition"
    return f"{EDITOR_PREFIXES.get(m.group(1).upper(), m.group(1).title())} {m.group(2)}"


def parse(tree) -> dict:
    """Extract the core elements that the crosswalk maps."""
    d: dict = {}
    idnos = {i.get("type"): (i.text or "").strip() for i in tree.findall(f".//{{{TEI}}}idno[@type]")}
    d["ids"] = {k: v for k, v in idnos.items() if k in ID_SYSTEMS and v}
    d["ciic"] = idnos.get("CIIC", idnos.get("filename", "x"))
    d["title"] = _text(tree.find(f".//{{{TEI}}}title"))
    d["material"] = _text(tree.find(f".//{{{TEI}}}material")) or None
    d["objectType"] = _text(tree.find(f".//{{{TEI}}}objectType")) or None

    # edition transliteration + competing readings ------------------------------
    div = tree.find(f".//{{{TEI}}}div[@type='edition'][@subtype='transliteration']")
    if div is None:
        div = tree.find(f".//{{{TEI}}}div[@type='edition']")
    readings = []
    edition_text = ""
    if div is not None:
        ab = div.findall(f".//{{{TEI}}}ab")
        edition_text = _text(ab[-1]) if ab else _text(div)
        if edition_text:
            resp = (div.get("resp") or "").lstrip("#") or "OGHAM"
            readings.append({"id": f"OGHAM_{resp}", "editor": f"OG(H)AM edition ({resp})",
                             "text": edition_text, "edition": True})
    for rdg in tree.findall(f".//{{{TEI}}}rdg"):
        src = (rdg.get("source") or rdg.get("resp") or "").lstrip("#")
        txt = _text(rdg)
        if txt:
            readings.append({"id": src, "editor": editor_label(src), "text": txt, "edition": False})
    d["edition"] = edition_text
    d["readings"] = readings

    # place of origin -----------------------------------------------------------
    placeName = tree.find(f".//{{{TEI}}}origPlace//{{{TEI}}}placeName")
    if placeName is not None:
        d["place"] = _text(placeName)
    else:
        op = _text(tree.find(f".//{{{TEI}}}origPlace"))
        d["place"] = re.split(r"\d", op)[0].strip(" ,") if op else None
    geo = _text(tree.find(f".//{{{TEI}}}geo"))
    m = re.findall(r"-?\d+\.\d+", geo)
    d["latlon"] = (float(m[0]), float(m[1])) if len(m) >= 2 else None

    # referenced names (Latin transliteration, de-duplicated) -------------------
    names, seen = [], set()
    for n in tree.findall(f".//{{{TEI}}}name[@nymRef]"):
        t = _text(n)
        if t and re.fullmatch(r"[A-Za-z ]+", t) and t.upper() not in seen:
            seen.add(t.upper())
            names.append(t)
    d["names"] = names
    return d


def build_graph(d: dict):
    g = Graph()
    for pfx, ns in (("crm", CRM), ("crmtex", CRMTEX), ("geo", GEO), ("prov", PROV),
                    ("ogham", OGHAM), ("data", DATA_NS), ("rdfs", RDFS), ("xsd", XSD)):
        g.bind(pfx, ns)

    ciic = d["ciic"]
    sid = _slug(ciic)
    records: list[tuple] = []

    stone = DATA_NS[f"stone_{sid}"]
    g.add((stone, RDF.type, CRM["E22_Human-Made_Object"]))
    g.add((stone, RDF.type, OGHAM.OghamStone))
    g.add((stone, RDFS.label, Literal(f"{d['title'] or 'Ogham stone'} (CIIC {ciic})")))
    records.append(("<support>", d["title"], "E22_Human-Made_Object", f"data:stone_{sid}"))

    for system, value in d["ids"].items():
        idn = DATA_NS[f"id_{sid}_{system}"]
        g.add((idn, RDF.type, CRM["E42_Identifier"]))
        g.add((idn, RDFS.label, Literal(value)))
        g.add((idn, CRM["P2_has_type"], Literal(system)))
        g.add((stone, CRM["P1_is_identified_by"], idn))
        records.append((f"<idno type={system}>", value, "E42_Identifier", f"data:id_{sid}_{system}"))

    if d["objectType"]:
        typ = DATA_NS[f"type_{_slug(d['objectType'])}"]
        g.add((typ, RDF.type, CRM["E55_Type"]))
        g.add((typ, RDFS.label, Literal(d["objectType"])))
        g.add((stone, CRM["P2_has_type"], typ))
        records.append(("<objectType>", d["objectType"], "E55_Type", f"data:type_{_slug(d['objectType'])}"))

    if d["material"]:
        mat = DATA_NS[f"material_{_slug(d['material'])}"]
        g.add((mat, RDF.type, CRM["E57_Material"]))
        g.add((mat, RDFS.label, Literal(d["material"])))
        g.add((stone, CRM["P45_consists_of"], mat))
        records.append(("<material>", d["material"], "E57_Material", f"data:material_{_slug(d['material'])}"))

    surface = DATA_NS[f"surface_{sid}"]
    g.add((surface, RDF.type, CRM["E25_Human-Made_Feature"]))
    g.add((surface, RDFS.label, Literal("inscribed surface")))
    g.add((stone, CRM["P56_bears_feature"], surface))
    records.append(("inscribed surface", "inscribed face", "E25_Human-Made_Feature", f"data:surface_{sid}"))

    # inscription text (TX1) carried by the stone -------------------------------
    inscr = DATA_NS[f"inscription_{sid}"]
    g.add((inscr, RDF.type, CRMTEX["TX1_Written_Text"]))
    g.add((inscr, RDF.type, OGHAM.Inscription))
    if d["edition"]:
        g.add((inscr, RDFS.label, Literal(d["edition"])))
    g.add((stone, CRM["P128_carries"], inscr))
    records.append(("<div type=edition>", d["edition"], "crmtex:TX1_Written_Text", f"data:inscription_{sid}"))

    # competing readings (TX6 Transcription), segments of the TX1, per editor ----
    # (structural only -- the amt:weight belief layer is added in tei--epidoc-amt)
    for r in d["readings"]:
        rd = DATA_NS[f"reading_{sid}_{_slug(r['id'] or r['text'])}"]
        g.add((rd, RDF.type, CRMTEX["TX6_Transcription"]))
        g.add((rd, RDF.type, OGHAM.Reading))
        g.add((rd, RDFS.label, Literal(r["text"])))
        g.add((inscr, CRMTEX["TXP4_has_segment"], rd))     # ontology: ogham:identifiedAs
        agent = DATA_NS[f"agent_{_slug(r['id'])}"]
        g.add((agent, RDF.type, PROV.Agent))
        g.add((agent, RDFS.label, Literal(r["editor"])))
        g.add((rd, PROV.wasAttributedTo, agent))
        kind = "edition" if r["edition"] else "historical"
        records.append((f"<rdg> ({kind})", f"{r['editor']}: {r['text']}",
                        "crmtex:TX6_Transcription", f"data:reading_{sid}_{_slug(r['id'] or r['text'])}"))

    # place of origin (E53 + GeoSPARQL) -----------------------------------------
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

    # referenced names (E21 Person) ---------------------------------------------
    for name in d["names"]:
        person = DATA_NS[f"person_{sid}_{_slug(name)}"]
        g.add((person, RDF.type, CRM["E21_Person"]))
        g.add((person, RDFS.label, Literal(name)))
        g.add((inscr, CRM["P67_refers_to"], person))
        records.append(("<name nymRef>", name, "E21_Person", f"data:person_{sid}_{_slug(name)}"))

    return g, records


def write_out_readme(results: list[tuple]) -> None:
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
        "crosswalk. The inscription and every competing reading are modelled here "
        "(structurally, in CRMtex); the `amt:weight` belief over the readings is added in "
        "`tei--epidoc-amt` (axis 2).\n")

    add("## 2. The crosswalk (EpiDoc element → CIDOC CRM / CRMtex)\n")
    add("| EpiDoc element | role | CRM/CRMtex class | CRM property |")
    add("|---|---|---|---|")
    for el, role, klass, prop in MAPPING:
        add(f"| `{esc(el)}` | {esc(role)} | `{esc(klass)}` | `{esc(prop)}` |")
    add("")
    add("Namespaces: `crm: http://www.cidoc-crm.org/cidoc-crm/`, "
        "`crmtex: …/cidoc-crm/crmtex/`, `geo: http://www.opengis.net/ont/geosparql#`, "
        "`prov: http://www.w3.org/ns/prov#`, `ogham: http://ontology.ogham.link/`.\n")

    add("## 3. Resolved modelling decisions\n")
    add("- **Material → `E57_Material` via `P45_consists_of`.** `E57_Material` is the CRM "
        "class for the substance an object is made of and is itself `rdfs:subClassOf E55_Type`; "
        "the ontology's `Material ⊑ E55` should be tightened to `⊑ E57` so `P45` is "
        "type-consistent.")
    add("- **Readings → `crmtex:TX6_Transcription`, `TXP4_has_segment` from the `TX1`, "
        "`prov:wasAttributedTo` the editor.** This follows the ontology "
        "(`Reading ⊑ TX6`, `identifiedAs ⊑ TXP4_has_segment`); weights stay in axis 2.")
    add("- **Place → `P53_has_former_or_current_location`** (the recorded `<geo>` is the "
        "site/findspot), matching the ontology's `disclosedAt ⊑ P53`; a reconstructed origin "
        "would use `E12_Production` / `P7_took_place_at` instead.\n")

    add("## 4. Per stone — how each element ends up in CIDOC CRM\n")
    for title, ciic, out, records in results:
        add(f"### {title} (CIIC {ciic})\n")
        add(f"`{out}` — {len(records)} mapped elements.\n")
        add("| EpiDoc element | extracted value | → CRM class | node |")
        add("|---|---|---|---|")
        for el, val, klass, node in records:
            v = (val or "").strip()
            v = v if len(v) <= 44 else v[:41] + "…"
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
        print(f"  {el:24} -> {klass:26} {(val or '')[:40]}")
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
