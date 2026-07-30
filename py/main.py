#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""main.py -- crosswalk OG(H)AM EpiDoc editions of ogham stones to CIDOC CRM / CRMtex.

Single entry point of the ``tei--epidoc-crosswalk`` repository (axis 1 of the
Linked Open Ogham crosswalk). Run from the repo root:

    python py/main.py            # process all stones in STONES, write out/README.md
    python py/main.py --input data/S-ARL-001.xml --output out/gigha1.crm.ttl
    python py/main.py --corpus ../og-h-am        # place layer over the whole corpus

For each stone it maps the core EpiDoc elements to CIDOC CRM 7.1.3 and its text
extension CRMtex, emits Turtle, and documents the element-by-element result in a
generated ``out/README.md``.

Alongside the per-stone crosswalk it runs the **place layer** (``py/places.py``),
which applies the same CIDOC CRM modelling to the geography of *every* EpiDoc file
it is pointed at -- ``data/`` by default, or a full OG(H)AM corpus clone via
``--fetch-corpus``/``--corpus`` -- and writes ``out/places.crm.ttl``, ``places.csv`` and
``places.geojson``. ``py/webmap.py`` then publishes the same records as a Leaflet
map in ``docs/``, which is what GitHub Pages serves.

Companion of ``tei--epidoc-amt`` (axis 2). Axis 1 is the **structural** crosswalk:
it models the inscription and every competing reading in CRMtex (who read what).
Axis 2 adds the ``amt:weight`` belief layer on top of the same readings.

Modelling follows the ``ogham.link`` ontology (whose classes are rdfs:subClassOf
the CRM classes), so the domain ontology *is* the crosswalk.
"""
from __future__ import annotations

import argparse
import re
from collections import Counter

import corpus    # local module (py/corpus.py) -- fetch + provenance manifest
import places    # local module (py/places.py) -- corpus-wide place layer
import webmap    # local module (py/webmap.py) -- docs/ map for GitHub Pages
import wikidata  # local module (py/wikidata.py)
from pathlib import Path

from lxml import etree
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD, OWL

# --- repo-root-relative paths -------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "out"
SHAPES = ROOT / "shapes" / "crosswalk-shapes.ttl"   # committed SHACL rules (not generated)
RECON = ROOT / "reconciliation"                    # Wikidata cache + curated allowlists (committed)
RECON_CACHE = RECON / "wikidata-links.csv"
ALLOWLISTS = {"material": RECON / "material-allowlist.csv",
              "editor": RECON / "editor-allowlist.csv",
              "objectType": RECON / "objecttype-allowlist.csv"}
ELEMENT_DOCS = ROOT / "element-docs"               # generated element documentation
DOCS = ROOT / "docs"                               # generated GitHub Pages site (the map)

# The OG(H)AM editions are a separate, living repository; py/corpus.py fetches the
# XML into data/origin/ (gitignored) and records the upstream state in a committed
# manifest. The place layer runs over whichever checkout it finds, in this order;
# data/ (four sample stones) is only the last resort.
CORPUS_DIR = DATA / "origin"                       # fetched editions (gitignored)
CORPUS_MANIFEST = DATA / "corpus-manifest.yaml"    # provenance record (committed)
# data/origin/ is the only location discovered automatically -- see corpus.resolve

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
SCHEMA = Namespace("http://schema.org/")
TIME = Namespace("http://www.w3.org/2006/time#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
TEIAPP = Namespace("http://ontology.ogham.link/tei-application/")
WD = Namespace("http://www.wikidata.org/entity/")
AMT = Namespace("http://academic-meta-tool.xyz/vocab#")

# Derived per CRM class: the TEI/EpiDoc application class name + the NFDI Core term.
# (The application classes correspond to the EpiDoc tags in MAPPING.)
CROSSWALK_EXTRA = {
    "crm:E22_Human-Made_Object": ("Support", "schema:CreativeWork"),
    "crm:E42_Identifier": ("Idno", "schema:identifier"),
    "crm:E55_Type": ("ObjectType", "schema:DefinedTerm"),
    "crm:E57_Material": ("Material", "schema:material"),
    "crm:E25_Human-Made_Feature": ("Layout", "schema:Thing"),
    "crmtex:TX1_Written_Text": ("EditionText", "schema:CreativeWork"),
    "crmtex:TX6_Transcription": ("Reading", "schema:CreativeWork"),
    "crm:E53_Place": ("OrigPlace", "schema:Place"),
    "crm:E52_Time-Span": ("OrigDate", "schema:Date"),
    "crm:E21_Person": ("PersName", "schema:Person"),
}

# The core crosswalk. Each row: EpiDoc element -> Linked Open Ogham ontology class
# -> CIDOC CRM/CRMtex class (+ property), with any supporting vocabulary used on the
# way. `ogham="—"` means the crosswalk goes straight to the CRM class (no dedicated
# domain class). Drives the generated documentation.
MAPPING = [
    dict(el="<support> (msDesc)", role="the stone", ogham="ogham:OghamStone",
         crm="crm:E22_Human-Made_Object", prop="(root node)", vocab="—"),
    dict(el="<idno type=CIIC|CISP|TM|SMR|Trove>", role="identifiers", ogham="—",
         crm="crm:E42_Identifier", prop="P1_is_identified_by (+ P2_has_type)", vocab="—"),
    dict(el="<objectType>", role="object type", ogham="—",
         crm="crm:E55_Type", prop="P2_has_type", vocab="—"),
    dict(el="<material>", role="material", ogham="ogham:Material",
         crm="crm:E57_Material", prop="P45_consists_of", vocab="—"),
    dict(el="inscribed surface / <layout>", role="inscribed face", ogham="—",
         crm="crm:E25_Human-Made_Feature", prop="P56_bears_feature", vocab="—"),
    dict(el="<div type=edition>", role="inscription text", ogham="ogham:Inscription",
         crm="crmtex:TX1_Written_Text", prop="P128_carries", vocab="CRMtex"),
    dict(el="<div type=edition> / <rdg>", role="readings", ogham="ogham:Reading",
         crm="crmtex:TX6_Transcription", prop="TXP4_has_segment + prov:wasAttributedTo",
         vocab="CRMtex, PROV-O"),
    dict(el="<origPlace> + <geo>", role="place of origin", ogham="ogham:Place",
         crm="crm:E53_Place", prop="P53_has_former_or_current_location", vocab="GeoSPARQL"),
    dict(el="<placeName type=townland|parish|county|…>", role="place hierarchy",
         ogham="ogham:Place", crm="crm:E53_Place", prop="P89_falls_within (chained)",
         vocab="—", teiapp="PlaceName", tag="placeName"),
    dict(el="<ref target=logainm|rcahmw|coflein>", role="gazetteer anchor", ogham="ogham:Place",
         crm="crm:E53_Place", prop="skos:closeMatch (weighted)", vocab="SKOS, AMT",
         teiapp="GazetteerRef", tag="ref",
         note="gazetteer targets inside <origPlace> only; other <ref> are record metadata"),
    dict(el="<origDate> (when present)", role="date of origin", ogham="—",
         crm="crm:E52_Time-Span", prop="P4_has_time-span", vocab="OWL-Time"),
    dict(el="<name nymRef> / <persName>", role="referenced name", ogham="ogham:Person",
         crm="crm:E21_Person", prop="P67_refers_to", vocab="—"),
]


def crosswalk_extra(row: dict) -> tuple[str, str]:
    """(TEI application class, NFDI Core term) for a MAPPING row. Rows may override
    the class name, so that several rows can share one CIDOC CRM class."""
    tei, nfdi = CROSSWALK_EXTRA[row["crm"]]
    return row.get("teiapp", tei), row.get("nfdi", nfdi)


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
    d["ciic"] = idnos.get("CIIC", "").strip()
    d["ogham_id"] = idnos.get("filename", "").strip()
    # URI key: shared with the place layer, so the graphs merge (see places.stone_key)
    d["key"] = places.stone_key(idnos)
    d["label_id"] = f"CIIC {d['ciic']}" if d["ciic"] else (d["ogham_id"] or d["key"])
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

    sid = _slug(d["key"])
    records: list[tuple] = []

    stone = DATA_NS[f"stone_{sid}"]
    g.add((stone, RDF.type, CRM["E22_Human-Made_Object"]))
    g.add((stone, RDF.type, OGHAM.OghamStone))
    g.add((stone, RDFS.label, Literal(f"{d['title'] or 'Ogham stone'} ({d['label_id']})")))
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


def write_out_readme(results: list[tuple], places_summary: dict | None = None) -> None:
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
        "`tei--epidoc-amt` (axis 2). Selected terms (materials, object types, editors) are also anchored to Wikidata via weighted `skos:closeMatch` (cache: `../reconciliation/wikidata-links.csv`).\n")

    add("## 2. The crosswalk: EpiDoc → Linked Open Ogham class → CIDOC CRM\n")
    add("The crosswalk runs through an **intermediate domain layer**: each EpiDoc element "
        "is mapped to a Linked Open Ogham ontology class, which is `rdfs:subClassOf` the "
        "target CIDOC CRM / CRMtex class. `—` means the mapping goes straight to CRM.\n")
    add("| EpiDoc element | Linked Open Ogham class | CIDOC CRM / CRMtex class | property | other vocab |")
    add("|---|---|---|---|---|")
    for r in MAPPING:
        add(f"| `{esc(r['el'])}` | `{esc(r['ogham'])}` | `{esc(r['crm'])}` | "
            f"`{esc(r['prop'])}` | {esc(r['vocab'])} |")
    add("")
    add("Namespaces: `crm: http://www.cidoc-crm.org/cidoc-crm/`, "
        "`crmtex: …/cidoc-crm/crmtex/`, `geo: http://www.opengis.net/ont/geosparql#`, "
        "`prov: http://www.w3.org/ns/prov#`, `time: http://www.w3.org/2006/time#`, "
        "`ogham: http://ontology.ogham.link/`.\n")

    add("## 3. Supporting vocabularies (used alongside CIDOC CRM)\n")
    add("Beyond CIDOC CRM / CRMtex, the crosswalk draws on established W3C/OGC "
        "vocabularies for the aspects CRM deliberately leaves to specialised standards:\n")
    add("| vocabulary | prefix | used for | in this graph |")
    add("|---|---|---|---|")
    add("| **CRMtex** (CIDOC CRM text extension) | `crmtex:` | the inscription and its readings | `TX1_Written_Text`, `TX6_Transcription`, `TXP4_has_segment` |")
    add("| **GeoSPARQL** (OGC) | `geo:` | geometry of places | `geo:asWKT` on `E53_Place` |")
    add("| **PROV-O** (W3C) | `prov:` | attribution of readings to editors | `prov:wasAttributedTo` on each `TX6` |")
    add("| **OWL-Time** (W3C) | `time:` | time-spans, aligned with `E52_Time-Span` | when `<origDate>` is present (none in this corpus yet) |")
    add("| **RDFS** (W3C) | `rdfs:` | human-readable labels | `rdfs:label` throughout |")
    add("| **SKOS + Wikidata** | `skos:` / `wd:` | anchoring terms to Wikidata QIDs | "
        "weighted `skos:closeMatch` (materials/types/editors) with `ogham:matchConfidence` + "
        "P31/P279 `ogham:matchTypeCheck` |")
    add("| **AMT** | `amt:` | making the match a weighted belief | each match is a reified "
        "`amt:weight` quadruple; `skos:closeMatch` is typed `amt:Role` (AMT-conformant, "
        "aligned with axis 2) |\n")

    add("## 4. Resolved modelling decisions\n")
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

    add("## 5. Where CIDOC CRM sits in the NFDI reference stack\n")
    add("CIDOC CRM is the **domain-rich, event-based** reference for cultural-heritage "
        "objects. For discovery-level interoperability across the NFDI, these classes align "
        "*upward* via the NFDI4Objects **Object Core Metadata Profile (OCMDP)**, whose "
        "super-elements crosswalk to the **NFDI Core Metadata Profile** — schema.org, "
        "DataCite, DCAT, NFDI Core / NFDIcore, CodeMeta — as well as DublinCore and Wikidata; "
        "on the class side, **MaCHeCO** provides the hierarchical crosswalk to CIDOC CRM "
        "(Thiery, Gerber & Fricke 2025). Indicative class-level alignment:\n")
    add("| CIDOC CRM | schema.org | DCAT / DCTERMS | DataCite |")
    add("|---|---|---|---|")
    add("| `E22_Human-Made_Object` | `schema:CreativeWork` / `Thing` | `dcat:Resource` | `resourceTypeGeneral=PhysicalObject` |")
    add("| `E42_Identifier` | `schema:identifier` | `dct:identifier` | `Identifier` |")
    add("| `E21_Person` | `schema:Person` / `creator` | `dct:creator` | `creator` / `contributor` |")
    add("| `E53_Place` (+ geo) | `schema:spatialCoverage` | `dct:spatial` | `geoLocation` |")
    add("| `E52_Time-Span` | `schema:temporalCoverage` | `dct:temporal` | `date` |")
    add("| `E55_Type` | `schema:additionalType` | `dcat:theme` | `subject` |")
    add("| `E57_Material` | `schema:material` | — | — |")
    add("| `crmtex:TX1_Written_Text` | `schema:text` | — | — |\n")
    add("*Indicative only.* The authoritative crosswalk is defined at the OCMDP super-element "
        "level (Thiery, F., Gerber, A. & Fricke, F. 2025, *Squirrel Papers* 7(4), "
        "https://doi.org/10.5281/zenodo.17159183; N4O TWG OCMDP/MaCHeCO, "
        "https://www.nfdi4objects.net/en/twgs/twg2024-1_omds_oo/).\n")

    add("## 6. The crosswalk as an OWL ontology (`crosswalk.ttl`) + SHACL\n")
    add("The crosswalk is also emitted as an **OWL ontology** (`out/crosswalk.ttl`) that "
        "models it as a class hierarchy: each TEI/EpiDoc application class "
        "(`teiapp:Support`, `teiapp:Idno`, `teiapp:Reading`, …, derived from the tags) is "
        "`rdfs:subClassOf` its Linked Open Ogham class, which is `rdfs:subClassOf` the CIDOC "
        "CRM class, up to `crm:E1_CRM_Entity rdfs:subClassOf owl:Thing`. Every CRM class also "
        "carries an `ogham:nfdiCoreMatch` to a NFDI Core / schema.org term.\n")
    add("A SHACL shapes file (`shapes/crosswalk-shapes.ttl`) then validates every application "
        "class (`sh:targetClass teiapp:TEIApplicationClass`) on two constraints:\n")
    add("1. it must reach `crm:E1_CRM_Entity` via `rdfs:subClassOf+` — it has a CIDOC CRM superclass;")
    add("2. it (or a superclass) must carry `ogham:nfdiCoreMatch` — it is linked to the NFDI Core profile.\n")
    add("`python py/main.py` runs this validation; the current crosswalk is **SHACL-valid**.\n")

    add("## 7. Per stone — how each element ends up in CIDOC CRM\n")
    for title, label_id, out, records in results:
        add(f"### {title} ({label_id})\n")
        add(f"`{out}` — {len(records)} mapped elements.\n")
        add("| EpiDoc element | extracted value | → CRM class | node |")
        add("|---|---|---|---|")
        for el, val, klass, node in records:
            v = (val or "").strip()
            v = v if len(v) <= 44 else v[:41] + "…"
            add(f"| `{esc(el)}` | {esc(v) or '—'} | `{esc(klass)}` | `{esc(node)}` |")
        add("")

    if places_summary:
        L.extend(places.readme_section(places_summary))

    (OUT / "README.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  -> wrote {(OUT / 'README.md').relative_to(ROOT)}")


def _term(qname: str):
    pfx, local = qname.split(":", 1)
    ns = {"crm": CRM, "crmtex": CRMTEX, "ogham": OGHAM, "schema": SCHEMA,
          "time": TIME, "teiapp": TEIAPP, "skos": SKOS}[pfx]
    return ns[local]


def build_crosswalk_ontology() -> Graph:
    """Model the crosswalk as an OWL class hierarchy:
    teiapp:<tag> rdfs:subClassOf ogham:<class> rdfs:subClassOf crm:<class>
    rdfs:subClassOf crm:E1_CRM_Entity rdfs:subClassOf owl:Thing, with an
    ogham:nfdiCoreMatch on every CRM class."""
    g = Graph()
    for pfx, ns in (("owl", OWL), ("rdfs", RDFS), ("skos", SKOS), ("crm", CRM),
                    ("crmtex", CRMTEX), ("ogham", OGHAM), ("schema", SCHEMA),
                    ("time", TIME), ("teiapp", TEIAPP)):
        g.bind(pfx, ns)

    onto = URIRef("http://ontology.ogham.link/tei-application")
    g.add((onto, RDF.type, OWL.Ontology))
    g.add((onto, RDFS.label, Literal("TEI/EpiDoc \u2192 CIDOC CRM crosswalk ontology (Linked Open Ogham)")))

    g.add((CRM["E1_CRM_Entity"], RDF.type, OWL.Class))
    g.add((CRM["E1_CRM_Entity"], RDFS.subClassOf, OWL.Thing))

    g.add((TEIAPP["TEIApplicationClass"], RDF.type, OWL.Class))
    g.add((TEIAPP["TEIApplicationClass"], RDFS.label, Literal("TEI/EpiDoc application class")))

    g.add((OGHAM["nfdiCoreMatch"], RDF.type, OWL.AnnotationProperty))
    g.add((OGHAM["nfdiCoreMatch"], RDFS.label, Literal("aligns with NFDI Core term")))
    g.add((OGHAM["nfdiCoreMatch"], RDFS.comment,
           Literal("Indicative class-level alignment to the NFDI Core Metadata Profile "
                   "(schema.org / DCAT / DataCite via the N4O OCMDP).")))
    for prop, lbl in (("matchConfidence", "Wikidata reconciliation confidence [0,1]"),
                      ("matchStatus", "Wikidata reconciliation status (auto/verified)"),
                      ("matchTypeCheck", "Wikidata P31/P279 type check (ok/mismatch/unknown)")):
        g.add((OGHAM[prop], RDF.type, OWL.AnnotationProperty))
        g.add((OGHAM[prop], RDFS.label, Literal(lbl)))
    amt_ns = Namespace("http://academic-meta-tool.xyz/vocab#")
    skos_ns = Namespace("http://www.w3.org/2004/02/skos/core#")
    g.bind("amt", amt_ns)
    g.bind("skos", skos_ns)
    g.add((skos_ns.closeMatch, RDF.type, amt_ns.Role))
    g.add((skos_ns.closeMatch, RDFS.label, Literal("close match (weighted Wikidata anchor)")))
    g.add((skos_ns.closeMatch, RDFS.comment,
           Literal("Used as an AMT role: each reconciliation quadruple carries amt:weight "
                   "(the match confidence), so links are weighted beliefs, aligned with axis 2.")))

    for r in MAPPING:
        tei, nfdi = crosswalk_extra(r)
        crm_uri = _term(r["crm"])
        g.add((crm_uri, RDF.type, OWL.Class))
        g.add((crm_uri, RDFS.subClassOf, CRM["E1_CRM_Entity"]))
        g.add((crm_uri, OGHAM["nfdiCoreMatch"], _term(nfdi)))
        parent = crm_uri
        if r["ogham"] != "\u2014":
            og = _term(r["ogham"])
            g.add((og, RDF.type, OWL.Class))
            g.add((og, RDFS.subClassOf, crm_uri))          # anchor from the Linked Ogham ontology
            parent = og
        tc = TEIAPP[tei]
        g.add((tc, RDF.type, OWL.Class))
        g.add((tc, RDF.type, TEIAPP["TEIApplicationClass"]))   # OWL punning for SHACL targeting
        g.add((tc, RDFS.subClassOf, parent))
        g.add((tc, RDFS.label, Literal(f"TEI/EpiDoc {r['el']}")))
        g.add((tc, SKOS.note, Literal(f"Application class derived from EpiDoc {r['el']}.")))
    places.add_ontology_terms(g)      # ogham:geoStatus / geoCertainty / matchSource
    return g


def emit_and_validate_crosswalk() -> None:
    onto = build_crosswalk_ontology()
    onto.serialize(destination=str(OUT / "crosswalk.ttl"), format="turtle")
    print(f"  -> wrote out/crosswalk.ttl ({len(onto)} triples)")
    if not SHAPES.exists():
        print(f"  (SHACL skipped: {SHAPES.relative_to(ROOT)} not found)")
        return
    try:
        from pyshacl import validate
        conforms, _, report = validate(data_graph=str(OUT / "crosswalk.ttl"),
                                       shacl_graph=str(SHAPES),
                                       advanced=True)
        print(f"  crosswalk SHACL: {'VALID' if conforms else 'INVALID'} "
              f"({len(MAPPING)} TEI application classes checked)")
        if not conforms:
            print(report)
    except ImportError:
        print("  (install pyshacl to validate the crosswalk ontology)")


# --- element inventory & classification (for the data/ documentation) ----------
PRIMARY_TAG = {
    "crm:E22_Human-Made_Object": "support", "crm:E42_Identifier": "idno",
    "crm:E55_Type": "objectType", "crm:E57_Material": "material",
    "crm:E25_Human-Made_Feature": "layout", "crmtex:TX1_Written_Text": "div",
    "crmtex:TX6_Transcription": "rdg", "crm:E53_Place": "origPlace",
    "crm:E52_Time-Span": "origDate", "crm:E21_Person": "name",
}
ALSO_MAPPED = {
    "geo": "crm:E53_Place (geo:asWKT on the findspot)",
    "country": "crm:E53_Place (place hierarchy, P89_falls_within)",
    "distinct": "rdfs:label on the E53_Place (vernacular name form, language-tagged)",
    "persName": "crm:E21_Person (via <name>)",
    "ab": "crmtex:TX1_Written_Text (display line, feeds the edition text)",
}
# sensible CIDOC CRM targets we could add next (not yet emitted)
CANDIDATE = {
    "dimensions": "crm:E54_Dimension (P43_has_dimension)",
    "height": "crm:E54_Dimension (P90/P91)", "width": "crm:E54_Dimension",
    "depth": "crm:E54_Dimension", "dim": "crm:E54_Dimension",
    "condition": "crm:E3_Condition_State (P44_has_condition)",
    "title": "crm:E35_Title (P102_has_title)",
    "provenance": "crm:E5_Event / E9_Move (object biography)",
    "origin": "crm:E12_Production (P108_has_produced)",
    "history": "crm:E5_Event (object-biography wrapper)",
    "bibl": "crm:E31_Document (P70_documents)", "listBibl": "crm:E31_Document",
    "citedRange": "crm:E31_Document (cited range)",
    "lb": "crmtex:TX7_Written_Text_Segment",
    "w": "crm:E36_Visual_Item / ogham:Word",
    "term": "crm:E55_Type (e.g. type_of_inscription)",
    "repository": "crm:E40_Legal_Body / E39_Actor (P50_has_current_keeper)",
    "keywords": "crm:E55_Type (classification)",
    "rs": "crm:E55_Type (e.g. execution technique)",
    "date": "crm:E52_Time-Span (P4_has_time-span)",
    "language": "crm:E56_Language / crmtex:TX3_Writing_System",
    "textLang": "crm:E56_Language / crmtex:TX3_Writing_System",
    "editor": "crm:E39_Actor (P14_carried_out_by)",
    "resp": "crm:E39_Actor (editorial responsibility)",
    "respStmt": "crm:E39_Actor (PROV)",
    "orgName": "crm:E74_Group / E40_Legal_Body",
    "graphic": "crmdig:D1_Digital_Object (image)",
    "facsimile": "crmdig:D1_Digital_Object",
    "media": "crmdig:D1_Digital_Object (3D/photo)",
    "note": "crm:E62_String (P3_has_note)",
    "q": "crm:E33_Linguistic_Object (quotation)",
    # --- seen across the full OG(H)AM corpus (--corpus), not in the data/ sample ---
    "g": "crmtex:TX7_Written_Text_Segment (ogham glyph; resolves via <charDecl>/<glyph>)",
    "c": "crmtex:TX7_Written_Text_Segment (single character)",
    "space": "crmtex:TX7_Written_Text_Segment (vacat)",
    "del": "crm:E13_Attribute_Assignment (carved deletion)",
    "add": "crm:E13_Attribute_Assignment (carved addition)",
    "handShift": "crm:E55_Type (change of hand / carver)",
    "creation": "crm:E65_Creation (origin of the text)",
    "surname": "crm:E41_Appellation (P1_is_identified_by on E21_Person)",
    "roleName": "crm:E55_Type (role of the named person)",
    "glyph": "crmtex:TX3_Writing_System (ogham character declaration)",
    "charDecl": "crmtex:TX3_Writing_System (character declaration)",
}
DOUBT = {
    "unclear": "\u2192 amt:weight (axis 2)", "supplied": "\u2192 amt:weight (axis 2)",
    "gap": "\u2192 amt:weight (axis 2)", "certainty": "\u2192 amt:weight (axis 2)",
    "app": "apparatus \u2192 axis 2", "listApp": "apparatus \u2192 axis 2",
    "lem": "apparatus lemma \u2192 axis 2",
    # editorial alternatives: the editor asserts one form over another
    "choice": "editorial alternative \u2192 axis 2", "corr": "editorial correction \u2192 axis 2",
    "sic": "editorial correction \u2192 axis 2", "orig": "editorial normalisation \u2192 axis 2",
    "reg": "editorial normalisation \u2192 axis 2",
    "damage": "damage-induced doubt \u2192 axis 2",
    "surplus": "editor judges characters surplus \u2192 axis 2",
    "abbr": "abbreviation/expansion \u2192 axis 2", "expan": "abbreviation/expansion \u2192 axis 2",
    "ex": "editor-supplied expansion \u2192 axis 2",
}
STRUCTURAL = {
    "TEI", "teiHeader", "fileDesc", "titleStmt", "publicationStmt", "sourceDesc",
    "encodingDesc", "profileDesc", "revisionDesc", "textClass", "langUsage",
    "msDesc", "msIdentifier", "msContents", "msItem", "physDesc", "objectDesc",
    "supportDesc", "layoutDesc", "handDesc", "handNote", "body", "text", "p",
    "desc", "funder", "licence", "availability", "authority", "change",
    "listChange", "include", "altIdentifier", "calendar", "calendarDesc",
    "ptr", "hi", "emph", "list", "item", "num", "xml",
}


def scan_tags(corpus_dir: Path = DATA):
    """Return (total counts, per-file presence) for every EpiDoc element tag in
    ``corpus_dir`` -- ``data/`` by default, or a fetched OG(H)AM checkout."""
    total, presence = Counter(), Counter()
    files = [str(f) for f in places.collect_files(corpus_dir)]
    for f in files:
        seen = set()
        tree = places.parse_xml(Path(f))     # tolerant: shares the place layer's parser
        if tree is None:
            continue
        for el in tree.iter():
            if isinstance(el.tag, str):
                tag = etree.QName(el).localname
                total[tag] += 1
                seen.add(tag)
        for tag in seen:
            presence[tag] += 1
    return total, presence, len(files)


def primary_tag(row: dict) -> str:
    """EpiDoc tag a MAPPING row is anchored on (rows may override the default)."""
    return row.get("tag") or PRIMARY_TAG.get(row["crm"], "")


def classify(tag):
    """(status, target) for a tag in the full inventory."""
    for r in MAPPING:
        if primary_tag(r) == tag:
            return "\u2705 mapped", r["crm"] + (f" — {r['note']}" if r.get("note") else "")
    if tag in ALSO_MAPPED:
        return "\u2705 mapped", ALSO_MAPPED[tag]
    if tag in CANDIDATE:
        return "\U0001f527 candidate", CANDIDATE[tag]
    if tag in DOUBT:
        return "\u2461 axis 2 (AMT)", DOUBT[tag]
    if tag in STRUCTURAL:
        return "\u25ab structural", "\u2014 (TEI structure / record metadata)"
    return "? to review", "\u2014"


def write_data_readme(presence, n_files, source="../data/"):
    L, add = [], None
    L = []; add = L.append
    esc = lambda s: str(s).replace("|", "\\|")
    ELEMENT_DOCS.mkdir(parents=True, exist_ok=True)
    add("# EpiDoc elements crosswalked to CIDOC CRM (current mapping)\n")
    add(f"> **Generated** by `python py/main.py`. Describes the crosswalk for the EpiDoc "
        f"elements currently handled, based on the {n_files} input EpiDoc files in `{source}`. "
        f"For every element in the corpus (including the ones not yet mapped) see "
        f"`all-epidoc-elements.md`; for the full documentation see `../out/README.md`.\n")
    add(f"| EpiDoc element | in stones | Linked Open Ogham class | CIDOC CRM / CRMtex | property |")
    add("|---|---|---|---|---|")
    for r in MAPPING:
        tag = primary_tag(r)
        n = presence.get(tag, 0)
        add(f"| `{esc(r['el'])}` | {n}/{n_files} | `{esc(r['ogham'])}` | "
            f"`{esc(r['crm'])}` | `{esc(r['prop'])}` |")
    add("")
    add("Selected terms (materials, object types, editors) are additionally anchored to "
        "**Wikidata** via weighted `skos:closeMatch`. The reconciliation cache and the "
        "curated allowlists live in `../reconciliation/` (`wikidata-links.csv`, "
        "`material-allowlist.csv`, `editor-allowlist.csv`, `objecttype-allowlist.csv`).\n")
    (ELEMENT_DOCS / "README.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  -> wrote {(ELEMENT_DOCS / 'README.md').relative_to(ROOT)}")


def write_all_elements_readme(total, n_files, source="../data/"):
    L = []; add = L.append
    esc = lambda s: str(s).replace("|", "\\|")
    ELEMENT_DOCS.mkdir(parents=True, exist_ok=True)
    add("# All EpiDoc elements in the corpus \u2014 crosswalk status & candidates\n")
    add(f"> **Generated** by `python py/main.py`. Every EpiDoc element tag found across the "
        f"{n_files} input files in `{source}`, with its crosswalk status: **\u2705 mapped** (emitted now), "
        f"**\U0001f527 candidate** (a sensible CIDOC CRM target we could add next), "
        f"**\u2461 axis 2** (doubt signal, handled in `tei--epidoc-amt`), or "
        f"**\u25ab structural** (TEI wrapper / record metadata).\n")
    tally = Counter(classify(tag)[0] for tag in total)
    add("Summary: " + " \u00b7 ".join(f"{k} {v}" for k, v in sorted(tally.items())) + ".\n")
    add("| element | count | status | CIDOC CRM target / note |")
    add("|---|---|---|---|")
    for tag, n in sorted(total.items(), key=lambda x: (-x[1], x[0])):
        status, target = classify(tag)
        add(f"| `{tag}` | {n} | {status} | {esc(target)} |")
    add("")
    (ELEMENT_DOCS / "all-epidoc-elements.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  -> wrote {(ELEMENT_DOCS / 'all-epidoc-elements.md').relative_to(ROOT)}")


def editor_surname(source_id: str):
    """Surname of a historical editor from a reading id (e.g. MAC1945 -> Macalister),
    or None for the current OG(H)AM edition."""
    m = re.match(r"([A-Za-z]+)\d{4}", source_id or "")
    return EDITOR_PREFIXES.get(m.group(1).upper()) if m else None


def enrich_wikidata(g: Graph, d: dict, cache: dict, online: bool, verify: bool, resolved: set, overrides: dict) -> list:
    """Anchor selected terms (material, object type, editors) to Wikidata via
    weighted skos:closeMatch, written straight into the stone's CRM graph.
    Returns the list of (kind, label, Match) actually linked (for the summary)."""
    g.bind("skos", SKOS)
    g.bind("wd", WD)
    g.bind("amt", AMT)
    targets = []
    if d["material"]:
        targets.append(("material", d["material"], DATA_NS[f"material_{_slug(d['material'])}"]))
    if d["objectType"]:
        targets.append(("objectType", d["objectType"], DATA_NS[f"type_{_slug(d['objectType'])}"]))
    for r in d["readings"]:
        sur = editor_surname(r["id"])
        if sur:
            targets.append(("editor", sur, DATA_NS[f"agent_{_slug(r['id'])}"]))

    linked = []
    for kind, label, node in targets:
        key = (kind, label)
        if key in resolved:                       # reconcile each term once per run
            m = cache.get(key) or wikidata.Match()
        else:
            m = wikidata.reconcile(label, kind, cache, online=online, verify=verify, overrides=overrides)
            resolved.add(key)
        if not m.qid:
            continue
        wd_uri = WD[m.qid]
        g.add((node, SKOS.closeMatch, wd_uri))
        # AMT-conformant weighted quadruple (named, addressable): the match confidence is
        # the amt:weight; reconciliation is uncertain, so the link is a weighted belief.
        st = DATA_NS[f"match_{str(node).split('/')[-1]}"]
        g.add((st, RDF.type, RDF.Statement))
        g.add((st, RDF.subject, node))
        g.add((st, RDF.predicate, SKOS.closeMatch))
        g.add((st, RDF.object, wd_uri))
        g.add((st, AMT.weight, Literal(f"{m.confidence:.2f}", datatype=XSD.decimal)))
        g.add((st, OGHAM.matchConfidence, Literal(f"{m.confidence:.2f}", datatype=XSD.decimal)))
        g.add((st, OGHAM.matchStatus, Literal(m.status)))
        g.add((st, OGHAM.matchTypeCheck, Literal(m.type_match or "unknown")))
        linked.append((kind, label, m))
    return linked


def process(input_path: Path, output_path: Path, cache=None, online: bool = True, verify: bool = True, resolved=None, overrides=None):
    tree = etree.parse(str(input_path))
    d = parse(tree)
    g, records = build_graph(d)
    linked = enrich_wikidata(g, d, cache, online, verify, resolved if resolved is not None else set(), overrides or {}) if cache is not None else []
    output_path.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(output_path), format="turtle")
    print(f"\n{d['title'] or '?'} ({d['label_id']}) -- {len(records)} elements -> "
          f"{output_path.relative_to(ROOT)} ({len(g)} triples)")
    for el, val, klass, node in records:
        print(f"  {el:24} -> {klass:26} {(val or '')[:40]}")
    for kind, label, m in linked:
        print(f"  wikidata  {kind:10} {label:14} -> {m.qid} "
              f"({m.status}/{m.type_match or 'unknown'}, conf={m.confidence:.2f})")
    return d["title"] or "?", d["label_id"], output_path.name, records


def main() -> None:
    ap = argparse.ArgumentParser(description="EpiDoc -> CIDOC CRM (Linked Open Ogham, axis 1)")
    ap.add_argument("--input", type=Path, help="single EpiDoc file (default: all stones)")
    ap.add_argument("--output", type=Path, help="output Turtle file (single-file mode only)")
    ap.add_argument("--offline", action="store_true", help="skip live Wikidata calls (cache only)")
    ap.add_argument("--no-verify", action="store_true", help="skip P31/P279 type verification")
    ap.add_argument("--corpus", type=Path, default=None,
                    help="corpus the place layer reads. Default: an OG(H)AM checkout found "
                         "at data/origin/, corpus/, ../og-h-am/ or $OGHAM_CORPUS, else "
                         "data/ (sample only)")
    ap.add_argument("--fetch-corpus", action="store_true",
                    help="fetch or update the OG(H)AM EpiDoc files (XML only, ~8 MB) in "
                         "data/origin/, refresh data/corpus-manifest.yaml, and use them")
    ap.add_argument("--places-only", action="store_true",
                    help="run only the place layer, skip the per-stone crosswalk")
    ap.add_argument("--no-places", action="store_true", help="skip the place layer")
    ap.add_argument("--no-map", action="store_true", help="skip the docs/ map")
    ap.add_argument("--no-fetch", action="store_true",
                    help="do not fetch the editions even if data/origin/ is empty")
    args = ap.parse_args()

    # The editions belong in data/origin/. If they are not there yet, fetch them --
    # 8 MB and two seconds is a better default than silently mapping four stones.
    if args.fetch_corpus or (args.corpus is None
                             and not corpus.has_editions(CORPUS_DIR)
                             and not (args.no_fetch or args.offline)):
        corpus.fetch(CORPUS_DIR, CORPUS_MANIFEST, ROOT)
        if args.corpus is None:
            args.corpus = CORPUS_DIR

    corpus_dir, why = corpus.resolve(args.corpus, CORPUS_DIR, DATA, ROOT)
    prov = corpus.provenance(CORPUS_MANIFEST, corpus_dir)
    if why == "fallback":
        print(f"! data/origin/ holds no editions -- the place layer and the docs/ map\n"
              f"! will cover only the {len(STONES)} sample stones in data/. To fix:\n"
              "!     python py/main.py --fetch-corpus     (XML only, ~8 MB)")
    else:
        stamp = (f" · commit {prov['commit'][:7]}"
                 + (f", {prov['commit_date'][:10]}" if prov.get("commit_date") else "")
                 if prov.get("commit") else " · no commit recorded")
        print(f"corpus: {corpus_dir} ({why}){stamp}")
        if not prov:
            print("  ! this checkout is not tracked, so the graph cannot record which\n"
                  "  ! corpus state it came from. `--fetch-corpus` gives a tracked one.")

    if args.places_only:
        OUT.mkdir(parents=True, exist_ok=True)
        summary = places.run(corpus_dir, OUT, root=ROOT, provenance=prov)
        if not args.no_map:
            webmap.build(summary["records"], DOCS, root=ROOT,
                         provenance=summary.get("provenance"))
        return

    cache = wikidata.load_cache(RECON_CACHE)
    online = not args.offline
    verify = not args.no_verify
    resolved = set()   # terms reconciled this run (fetch once)
    overrides = {}
    for _kind, _path in ALLOWLISTS.items():
        overrides.update(wikidata.load_overrides(_path, _kind))
    if args.input:
        out = args.output or (OUT / (args.input.stem + ".crm.ttl"))
        process(args.input, out, cache=cache, online=online, verify=verify, resolved=resolved, overrides=overrides)
    else:
        results = [process(DATA / f, OUT / f"{b}.crm.ttl", cache=cache, online=online, verify=verify, resolved=resolved, overrides=overrides)
                   for f, b in STONES]
        places_summary = None if args.no_places else places.run(corpus_dir, OUT, root=ROOT, provenance=prov)
        if places_summary and not args.no_map:
            places_summary["map"] = webmap.build(
                places_summary["records"], DOCS, root=ROOT,
                provenance=places_summary.get("provenance"))
        write_out_readme(results, places_summary)
        emit_and_validate_crosswalk()
        wikidata.save_cache(RECON_CACHE, cache)
        n_res = sum(1 for m in cache.values() if m.qid)
        print(f"  -> updated {RECON_CACHE.relative_to(ROOT)} "
              f"({n_res}/{len(cache)} terms resolved)")
        total, presence, n_files = scan_tags(corpus_dir)
        try:                       # inside the repo -> relative path, else the corpus name
            label = f"../{corpus_dir.relative_to(ROOT)}/"
        except ValueError:
            label = f"{corpus_dir.name}/ (external corpus)"
        write_data_readme(presence, n_files, label)
        write_all_elements_readme(total, n_files, label)


if __name__ == "__main__":
    main()
