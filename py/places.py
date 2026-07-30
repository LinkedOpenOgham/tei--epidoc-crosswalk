#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""places.py -- the place layer of the TEI/EpiDoc -> CIDOC CRM crosswalk.

Companion module of ``main.py``. Where ``main.py`` crosswalks a handful of stones
in full, this module crosswalks **one aspect across the whole corpus**: the
geography. It reads every EpiDoc file it is pointed at, extracts the findspot and
the administrative place hierarchy, and emits

* ``out/places.crm.ttl``  -- CIDOC CRM place graph (``E53_Place`` + GeoSPARQL)
* ``out/places.csv``      -- flat table, one row per inscription
* ``out/places.geojson``  -- point layer, WGS84, for any GIS or web map

Modelling follows the same three-layer crosswalk as the rest of the repository
(EpiDoc -> Linked Open Ogham class -> CIDOC CRM):

    <origPlace>                      -> crm:E53_Place        (the findspot, carries the geometry)
    <geo>                            -> geo:asWKT            on that E53
    <placeName type="townland|...">  -> crm:E53_Place        chained with P89_falls_within
    @type of the placeName           -> crm:E55_Type         via P2_has_type
    <distinct xml:lang="ga">         -> rdfs:label@ga        on the place
    <ref target="logainm|...">       -> skos:closeMatch      weighted, as for Wikidata

Two deliberate modelling choices:

1. **The findspot is its own E53, distinct from the townland it lies in.** Stones
   in the same townland do not always carry the same coordinates (21 townlands in
   the OG(H)AM corpus disagree with themselves), so putting the geometry on the
   shared townland node would fabricate a consensus the sources do not support.
   The findspot ``P89_falls_within`` the townland instead.

2. **Hedged coordinates are flagged, not weighted.** ``<geo>`` is not a strictly
   typed field: beside plain pairs it holds ``(approximate)``,
   ``(possible original location)``, ``@cert="low"`` and, in a few records, prose
   instead of numbers. The hedge is preserved as ``ogham:geoStatus`` plus a
   ``P3_has_note``; turning it into an ``amt:weight`` belief is axis 2's job
   (``tei--epidoc-amt``), and this is the handle it needs.
"""
from __future__ import annotations

import copy
import csv
import json
import re
from pathlib import Path

from lxml import etree
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

TEI = "http://www.tei-c.org/ns/1.0"
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
OGHAM = Namespace("http://ontology.ogham.link/")
DATA_NS = Namespace("http://data.ogham.link/crm/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
AMT = Namespace("http://academic-meta-tool.xyz/vocab#")
PROV = Namespace("http://www.w3.org/ns/prov#")

# Administrative levels, most specific first. The hierarchy emitted per record is
# whichever of these are present, chained with P89_falls_within.
PLACE_LEVELS = [
    "building", "graveyard", "ecclesiastical_site", "site", "lake",
    "townland", "civil_parish", "parish", "town", "city",
    "sheading", "county", "region", "island", "historical", "country",
]

# Gazetteers the editors link to from inside <origPlace>.
XML_NS = "http://www.w3.org/XML/1998/namespace"

GAZETTEERS = {
    "logainm.ie": "Logainm (Placenames Database of Ireland)",
    "historicplacenames.rcahmw.gov.uk": "RCAHMW Historic Place Names of Wales",
    "coflein.gov.uk": "Coflein (NMRW)",
}

# a decimal pair, optionally followed by a free-text hedge such as "(approximate)"
COORD_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*[,;]\s*(-?\d+(?:\.\d+)?)\s*(?P<rest>.*)$")
# OG(H)AM edition identifier, e.g. I-COR-001, S-ARL-001, W-PEM-X02
OGHAM_ID_RE = re.compile(r"[A-Z]-[A-Z]{3}-[A-Z0-9]+")
ITM_RE = re.compile(r"(ITM|National Grid Reference|Irish Grid)[^:]*:\s*(?P<v>[^<;]+)", re.I)


def _text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def _clean_label(text: str) -> str:
    """Tidy a place label after the vernacular form has been lifted out of it.

    Removes a bare URL printed as the <ref> content (some records show the Logainm
    link twice, once as @target and once as text), the now-empty bracket the
    vernacular sat in, and truncates at an unbalanced opening bracket -- which the
    corpus produces where a closing bracket was typed outside the <placeName>
    (e.g. Kilmovee, I-MAY-004).
    """
    text = re.sub(r"https?://[^\s)\]]+", "", text)
    text = re.sub(r"\(\s*[\u2018\u2019'\"]?\s*\)", "", text)
    if text.count("(") > text.count(")"):
        text = text[:text.rfind("(")]
    elif text.count(")") > text.count("("):
        text = text[:text.find(")")]
    text = re.sub(r"\(\s+", "(", re.sub(r"\s+\)", ")", text))
    return re.sub(r"\s+", " ", text).strip(" ,;\u2018\u2019'\"")


# Editorial prose the corpus sometimes packs into a <placeName> alongside the name
# itself ("Ballynahunt but possibly originally from Kilduff…"). The name becomes the
# label; the editors' full wording is kept as a note on the place.
# The lookbehinds keep "Co. Kerry", "St. Mary's" and "Mt. Brandon" intact -- without
# them every county collapses onto a single "Co" node.
PROSE_RE = re.compile(r"(?<!\bCo)(?<!\bSt)(?<!\bMt)\.\s|;\s|\sbut\s|\sprobably\s|\spossibly\s", re.I)


def _split_prose(label: str) -> tuple[str, str]:
    """(short label, full text) -- identical when the placeName holds only a name."""
    m = PROSE_RE.search(label)
    if not m:
        return label, ""
    short = _clean_label(label[:m.start()])
    return (short, label) if short else (label, "")


def _label_without_vernacular(pn) -> str:
    """Label of a <placeName> with every <distinct> subtree removed but its tail
    text kept, so 'Coomleagh East (An Com Liath Thoir)' becomes 'Coomleagh East'."""
    clone = copy.deepcopy(pn)
    etree.strip_elements(clone, f"{{{TEI}}}distinct", with_tail=False)
    return _clean_label(_text(clone))


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text or "").strip("_") or "x"


def stone_key(idnos: dict) -> str:
    """Identifier the stone's URI is built from.

    The **OG(H)AM edition id** (``I-COR-001``) is preferred over the CIIC number,
    because CIIC is a bibliographic numbering that is neither complete nor unique:
    across the corpus 2 stones share CIIC 214 (Kilgobnet) and many carry no CIIC at
    all, so CIIC-based URIs would silently merge distinct stones. CIIC stays in the
    graph as an ``E42_Identifier``, which is where a bibliographic number belongs.

    ``main.parse()`` uses this too, so the per-stone graphs and the corpus place
    graph mint the same ``data:stone_*`` URIs and can be merged.
    """
    ogham_id = (idnos.get("filename") or "").strip()
    if OGHAM_ID_RE.fullmatch(ogham_id):
        return ogham_id
    return (idnos.get("CIIC") or "").strip() or ogham_id or "x"


def is_edition(rec: dict) -> bool:
    """False for the template and test files the corpus keeps beside the editions."""
    return bool(OGHAM_ID_RE.fullmatch(rec.get("ogham_id") or ""))


def parse_geo(raw: str):
    """(lat, lon, hedge) from a TEI <geo> value; the hedge is kept, not dropped."""
    raw = (raw or "").strip()
    m = COORD_RE.search(raw)
    if not m:
        return None, None, raw
    lat, lon = float(m.group(1)), float(m.group(2))
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None, None, raw
    return lat, lon, m.group("rest").strip(" ()")


RECOVERED: list[str] = []          # files that needed the recovering parser


def parse_xml(path: Path):
    """Parse an EpiDoc file, tolerating validity errors.

    The corpus occasionally carries a duplicate ``xml:id``, which lxml rejects at
    parse time even though the document is well-formed. Dropping such an edition
    would silently shrink the corpus, so it is re-parsed in recovery mode and
    recorded. Returns None only if the file is beyond recovery.
    """
    try:
        return etree.parse(str(path))
    except etree.XMLSyntaxError as exc:
        try:
            tree = etree.parse(str(path), etree.XMLParser(recover=True))
        except etree.XMLSyntaxError:
            print(f"  ! {path.name}: unparseable ({str(exc).splitlines()[0]})")
            return None
        RECOVERED.append(f"{path.name}: {str(exc).splitlines()[0]}")
        return tree


def parse_place(path: Path) -> dict | None:
    """Extract the geography of one EpiDoc file."""
    tree = parse_xml(path)
    if tree is None:
        return None

    idnos = {}
    for i in tree.findall(f".//{{{TEI}}}idno[@type]"):
        value = (i.text or "").strip()
        if value:
            idnos.setdefault(i.get("type"), value)

    rec: dict = {
        "file": path.name,
        "stone_key": stone_key(idnos),
        "ogham_id": idnos.get("filename", path.stem),
        "title": _text(tree.find(f".//{{{TEI}}}title")),
        "ciic": idnos.get("CIIC", ""),
        "cisp": idnos.get("CISP", ""),
        "cisp_url": "",
        "tm": idnos.get("TM", ""),
        "smr": idnos.get("SMR", ""),
        "repository": _text(tree.find(f".//{{{TEI}}}msIdentifier/{{{TEI}}}repository")),
    }

    cisp_el = tree.find(f".//{{{TEI}}}idno[@type='CISP']")
    if cisp_el is not None and cisp_el.get("corresp"):
        rec["cisp_url"] = cisp_el.get("corresp")

    origplace = tree.find(f".//{{{TEI}}}history/{{{TEI}}}origin/{{{TEI}}}origPlace")
    if origplace is None:
        origplace = tree.find(f".//{{{TEI}}}origPlace")
    if origplace is None:
        rec["hierarchy"] = []
        rec["geo_status"] = "no_origplace"
        return rec

    rec["origplace_text"] = _text(origplace)

    # place names, keyed by @type; the Irish form is marked <distinct xml:lang="ga">
    named: dict[str, dict] = {}
    for pn in origplace.findall(f".//{{{TEI}}}placeName"):
        ptype = pn.get("type", "untyped")
        # vernacular forms, each with its own language tag -- the corpus uses ga
        # (Irish) but also sga (Old Irish), so do not hard-code one code
        vernacular = []
        for dn in pn.findall(f".//{{{TEI}}}distinct"):
            form = _clean_label(_text(dn))
            if form:
                vernacular.append((dn.get(f"{{{XML_NS}}}lang") or "ga", form))
        label = _label_without_vernacular(pn) if vernacular else _clean_label(_text(pn))
        label, prose = _split_prose(label)
        if not label:
            continue
        links = [r.get("target") for r in pn.findall(f".//{{{TEI}}}ref[@target]") if r.get("target")]
        entry = named.setdefault(ptype, {"label": label, "prose": prose,
                                        "vernacular": vernacular, "links": links})
        if not entry["vernacular"] and vernacular:
            entry["vernacular"] = vernacular

    # most specific first
    rec["hierarchy"] = [
        dict(level=lvl, **named[lvl]) for lvl in PLACE_LEVELS if lvl in named
    ]
    rec["untyped"] = [v["label"] for k, v in named.items() if k not in PLACE_LEVELS]
    for lvl in PLACE_LEVELS:
        rec[f"pn_{lvl}"] = named.get(lvl, {}).get("label", "")
    rec["pn_vernacular"] = " | ".join(
        f"{form} ({lang})" for v in named.values() for lang, form in v["vernacular"])

    # coordinates
    geo = origplace.find(f".//{{{TEI}}}geo")
    rec["geo_raw"] = _text(geo)
    rec["geo_cert"] = geo.get("cert", "") if geo is not None else ""
    lat, lon, hedge = parse_geo(rec["geo_raw"])
    rec["lat"], rec["lon"], rec["geo_hedge"] = lat, lon, hedge
    if lat is None:
        rec["geo_status"] = "missing" if not rec["geo_raw"] else "textual_only"
    elif rec["geo_cert"] or hedge:
        rec["geo_status"] = "qualified"
    else:
        rec["geo_status"] = "asserted"

    # projected national-grid coordinates that some records tuck into a <note>
    for note in origplace.findall(f".//{{{TEI}}}note"):
        m = ITM_RE.search(_text(note))
        if m:
            rec["grid_raw"] = m.group("v").strip()
            break

    # all authority links inside the findspot, whichever placeName they hang off
    gaz = [r.get("target") for r in origplace.findall(f".//{{{TEI}}}ref[@target]") if r.get("target")]
    rec["gazetteer_uris"] = " | ".join(
        u for u in gaz if any(host in u for host in GAZETTEERS)
    )
    return rec


# --- RDF ----------------------------------------------------------------------

def _place_uri(chain: list[str]) -> URIRef:
    """URI for a place, qualified by its ancestors so that identical names in
    different counties stay apart (e.g. two townlands called Ballynahow)."""
    return DATA_NS["place_" + "_".join(_slug(c) for c in reversed(chain))]


def add_provenance(g: Graph, prov: dict) -> None:
    """Record which upstream state the graph was derived from.

    The corpus is a living repository, so a graph without a commit is not
    reproducible. `data/corpus-manifest.yaml` holds the state; this puts the same
    fact into the graph itself, where a consumer will actually find it.
    """
    if not prov:
        return
    import datetime as _dt
    g.bind("prov", PROV)
    node = DATA_NS["places-graph"]
    g.add((node, RDF.type, PROV.Entity))
    g.add((node, RDFS.label, Literal("OG(H)AM findspots -- corpus-wide place layer")))
    g.add((node, PROV.generatedAtTime,
           Literal(_dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
                   datatype=XSD.dateTime)))
    if prov.get("tree_url"):
        g.add((node, PROV.wasDerivedFrom, URIRef(prov["tree_url"])))
    elif prov.get("source"):
        g.add((node, PROV.wasDerivedFrom, URIRef(prov["source"])))
    if prov.get("commit"):
        g.add((node, OGHAM.corpusCommit, Literal(prov["commit"])))
    if prov.get("commit_date"):
        g.add((node, OGHAM.corpusCommitDate, Literal(prov["commit_date"])))
    if prov.get("edition_count"):
        g.add((node, OGHAM.corpusEditionCount,
               Literal(int(prov["edition_count"]), datatype=XSD.integer)))


def build_place_graph(records: list[dict], prov: dict | None = None) -> tuple[Graph, dict]:
    """Corpus-wide CIDOC CRM place graph. Returns (graph, summary)."""
    g = Graph()
    for pfx, ns in (("crm", CRM), ("geo", GEO), ("ogham", OGHAM), ("data", DATA_NS),
                    ("skos", SKOS), ("amt", AMT), ("rdfs", RDFS), ("xsd", XSD)):
        g.bind(pfx, ns)
    add_provenance(g, prov or {})

    emitted_places: set[URIRef] = set()
    emitted_types: set[str] = set()
    gaz_links = 0

    def place_type(level: str) -> URIRef:
        node = DATA_NS[f"placetype_{_slug(level)}"]
        if level not in emitted_types:
            g.add((node, RDF.type, CRM["E55_Type"]))
            g.add((node, RDFS.label, Literal(level.replace("_", " "), lang="en")))
            emitted_types.add(level)
        return node

    def gazetteer_match(node: URIRef, uri: str) -> None:
        """Weighted skos:closeMatch, reified as an AMT quadruple -- the same shape
        the Wikidata reconciliation uses, so both are queryable alike. These links
        are asserted by the editors in the source, hence weight 1.0."""
        nonlocal gaz_links
        target = URIRef(uri)
        if (node, SKOS.closeMatch, target) in g:
            return
        g.add((node, SKOS.closeMatch, target))
        st = DATA_NS[f"match_{str(node).rsplit('/', 1)[-1]}_{_slug(uri.rsplit('/', 1)[-1])}"]
        g.add((st, RDF.type, RDF.Statement))
        g.add((st, RDF.subject, node))
        g.add((st, RDF.predicate, SKOS.closeMatch))
        g.add((st, RDF.object, target))
        g.add((st, AMT.weight, Literal("1.00", datatype=XSD.decimal)))
        g.add((st, OGHAM.matchConfidence, Literal("1.00", datatype=XSD.decimal)))
        g.add((st, OGHAM.matchStatus, Literal("source-asserted")))
        g.add((st, OGHAM.matchTypeCheck, Literal("curated")))
        for host, label in GAZETTEERS.items():
            if host in uri:
                g.add((st, OGHAM.matchSource, Literal(label)))
                break
        gaz_links += 1

    for rec in records:
        sid = _slug(rec["stone_key"])
        stone = DATA_NS[f"stone_{sid}"]
        # minimal re-assertion so that places.crm.ttl also stands on its own
        g.add((stone, RDF.type, CRM["E22_Human-Made_Object"]))
        g.add((stone, RDF.type, OGHAM.OghamStone))
        label = rec["title"] or rec["ogham_id"]
        g.add((stone, RDFS.label, Literal(f"{label} ({rec['ogham_id']})")))
        g.add((stone, CRM["P1_is_identified_by"], Literal(rec["ogham_id"])))

        hierarchy = rec.get("hierarchy") or []
        if not hierarchy and rec.get("lat") is None:
            continue

        # the administrative chain, broadest node first so parents exist
        chain_uris: list[URIRef] = []
        names = [h["label"] for h in hierarchy]
        for i, h in enumerate(hierarchy):
            uri = _place_uri(names[i:])
            chain_uris.append(uri)
            if uri not in emitted_places:
                g.add((uri, RDF.type, CRM["E53_Place"]))
                g.add((uri, RDF.type, OGHAM.Place))
                g.add((uri, RDFS.label, Literal(h["label"], lang="en")))
                for lang, form in h["vernacular"]:
                    g.add((uri, RDFS.label, Literal(form, lang=lang)))
                if h.get("prose"):      # the editors' own wording, kept verbatim
                    g.add((uri, CRM["P3_has_note"], Literal(h["prose"])))
                g.add((uri, CRM["P2_has_type"], place_type(h["level"])))
                emitted_places.add(uri)
            for link in h["links"]:
                if any(host in link for host in GAZETTEERS):
                    gazetteer_match(uri, link)
        for narrow, broad in zip(chain_uris, chain_uris[1:]):
            g.add((narrow, CRM["P89_falls_within"], broad))

        # the findspot itself: its own E53, inside the narrowest named place
        findspot = DATA_NS[f"findspot_{sid}"]
        g.add((findspot, RDF.type, CRM["E53_Place"]))
        g.add((findspot, RDF.type, OGHAM.Place))
        g.add((findspot, RDFS.label,
               Literal(f"findspot of {rec['ogham_id']}" + (f" ({', '.join(names)})" if names else ""))))
        g.add((findspot, CRM["P2_has_type"], place_type("findspot")))
        g.add((stone, CRM["P53_has_former_or_current_location"], findspot))
        if chain_uris:
            g.add((findspot, CRM["P89_falls_within"], chain_uris[0]))

        if rec.get("lat") is not None:
            g.add((findspot, GEO.asWKT,
                   Literal(f"POINT({rec['lon']} {rec['lat']})", datatype=GEO.wktLiteral)))
        g.add((findspot, OGHAM.geoStatus, Literal(rec.get("geo_status", "missing"))))
        if rec.get("geo_status") == "supplied":
            # not the edition's claim: record where it came from and how far it is trusted
            if rec.get("geo_source"):
                g.add((findspot, OGHAM.coordinateSource, Literal(rec["geo_source"])))
            if rec.get("geo_note"):
                g.add((findspot, CRM["P3_has_note"], Literal(rec["geo_note"])))
            if rec.get("geo_qid"):
                target = URIRef("http://www.wikidata.org/entity/" + rec["geo_qid"])
                g.add((findspot, SKOS.closeMatch, target))
                st = DATA_NS[f"match_findspot_{sid}"]
                g.add((st, RDF.type, RDF.Statement))
                g.add((st, RDF.subject, findspot))
                g.add((st, RDF.predicate, SKOS.closeMatch))
                g.add((st, RDF.object, target))
                weight = "1.00" if rec.get("geo_supplied_status") == "verified" else "0.70"
                g.add((st, AMT.weight, Literal(weight, datatype=XSD.decimal)))
                g.add((st, OGHAM.matchStatus, Literal(rec.get("geo_supplied_status", "auto"))))
        # the axis-2 hook: the editors' own hedge, verbatim
        if rec.get("geo_hedge"):
            g.add((findspot, CRM["P3_has_note"], Literal(rec["geo_hedge"])))
        if rec.get("geo_cert"):
            g.add((findspot, OGHAM.geoCertainty, Literal(rec["geo_cert"])))
        if rec.get("grid_raw"):
            g.add((findspot, CRM["P3_has_note"], Literal(f"national grid: {rec['grid_raw']}")))

    summary = {
        "stones": len(records),
        "places": len(emitted_places),
        "levels": len(emitted_types),
        "gazetteer_links": gaz_links,
        "triples": len(g),
    }
    return g, summary


def add_ontology_terms(g: Graph) -> None:
    """Declare the annotation properties this module introduces, so that they are
    documented in ``out/crosswalk.ttl`` alongside the reconciliation properties."""
    from rdflib.namespace import OWL
    for prop, lbl in (
        ("geoStatus", "findspot coordinate status (asserted/qualified/textual_only/missing)"),
        ("geoCertainty", "editorial @cert on the <geo> value"),
        ("matchSource", "gazetteer the close match points into"),
        ("corpusCommit", "upstream OG(H)AM commit the graph was derived from"),
        ("corpusCommitDate", "date of that upstream commit"),
        ("corpusEditionCount", "number of editions in that corpus state"),
        ("coordinateSource", "where a supplied findspot coordinate came from"),
    ):
        g.add((OGHAM[prop], RDF.type, OWL.AnnotationProperty))
        g.add((OGHAM[prop], RDFS.label, Literal(lbl)))


# --- coordinates supplied from outside the edition ----------------------------
# Twenty editions carry an empty <geo/>. Where the findspot is known from CISP,
# Macalister or Wikidata it can be supplied here rather than left blank -- but it
# must never look like something the edition asserts, so it gets its own
# geoStatus, keeps its source in a note, and is drawn like a hedged findspot.
OVERRIDE_FIELDS = ["ogham_id", "lat", "lon", "qid", "source", "status", "note"]


def load_overrides(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return {row["ogham_id"]: row for row in csv.DictReader(fh)
                if row.get("ogham_id") and row.get("lat") and row.get("lon")}


def apply_overrides(records: list[dict], overrides: dict[str, dict]) -> dict:
    """Fill in findspots the edition leaves empty. Never silently replaces one."""
    applied, refused = [], []
    for rec in records:
        row = overrides.get(rec.get("ogham_id", ""))
        if not row:
            continue
        if rec.get("lat") is not None:
            refused.append(rec["ogham_id"])      # the edition has its own coordinate
            continue
        rec["lat"], rec["lon"] = float(row["lat"]), float(row["lon"])
        rec["geo_status"] = "supplied"
        rec["geo_source"] = row.get("source", "")
        rec["geo_note"] = row.get("note", "")
        rec["geo_qid"] = row.get("qid", "")
        rec["geo_supplied_status"] = row.get("status", "auto")
        applied.append(rec["ogham_id"])
    return {"applied": applied, "refused": refused}


# --- tabular / spatial exports ------------------------------------------------

CSV_FIELDS = (
    ["file", "ogham_id", "stone_key", "title", "ciic", "cisp", "cisp_url", "tm", "smr", "repository"]
    + [f"pn_{lvl}" for lvl in PLACE_LEVELS]
    + ["pn_vernacular", "geo_source", "geo_note", "geo_qid", "gazetteer_uris", "geo_raw", "geo_cert", "geo_hedge",
       "geo_status", "lat", "lon", "grid_raw", "origplace_text"]
)


def write_csv(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)


def write_geojson(records: list[dict], path: Path) -> int:
    features = []
    for rec in records:
        if rec.get("lat") is None:
            continue
        props = {k: v for k, v in rec.items()
                 if k in CSV_FIELDS and k not in {"lat", "lon"} and v not in (None, "")}
        props["uri"] = str(DATA_NS[f"findspot_{_slug(rec['stone_key'])}"])
        features.append({
            "type": "Feature",
            "id": rec["ogham_id"],
            "geometry": {"type": "Point", "coordinates": [rec["lon"], rec["lat"]]},
            "properties": props,
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(
        {"type": "FeatureCollection", "name": "OG(H)AM findspots", "features": features},
        ensure_ascii=False, indent=1), encoding="utf-8")
    return len(features)


# --- entry point used by main.py ----------------------------------------------

# Never descend into these: `origin/` is the fetched OG(H)AM checkout that lives
# inside `data/`, so scanning `data/` must not pick the whole corpus up twice.
SKIP_DIRS = frozenset({"origin", ".git", "corpus", "og-h-am"})
SKIP_FILES = frozenset({"OG_H_AM.xml", "charDecl.xml"})   # corpus-level wrappers


def collect_files(corpus: Path) -> list[Path]:
    """Every EpiDoc file under ``corpus``. Works both on this repository's
    ``data/`` directory and on a checkout of the OG(H)AM corpus (``XML/<REGION>/``)."""
    if corpus.is_file():
        return [corpus]
    return sorted(
        p for p in corpus.rglob("*.xml")
        if not p.name.startswith(".")
        and p.name not in SKIP_FILES
        and not SKIP_DIRS.intersection(p.relative_to(corpus).parts[:-1])
    )


def run(corpus: Path, out_dir: Path, root: Path | None = None,
        provenance: dict | None = None, overrides: Path | None = None) -> dict:
    """Parse the corpus, emit places.crm.ttl / places.csv / places.geojson."""
    files = collect_files(corpus)
    RECOVERED.clear()
    print(f"\nplace layer -- {len(files)} EpiDoc files under {corpus}")
    parsed = [r for r in (parse_place(f) for f in files) if r]
    records = [r for r in parsed if is_edition(r)]
    skipped = [r["file"] for r in parsed if not is_edition(r)]
    if skipped:
        print(f"  skipped {len(skipped)} non-edition file(s): {', '.join(sorted(skipped))}")
    if RECOVERED:
        print(f"  recovered {len(RECOVERED)} file(s) with XML validity errors "
              f"(kept, content intact):")
        for line in RECOVERED:
            print(f"    {line}")

    ov = apply_overrides(records, load_overrides(overrides)) if overrides else {"applied": [], "refused": []}
    if ov["applied"]:
        print(f"  supplied {len(ov['applied'])} findspot(s) the edition leaves empty: "
              f"{', '.join(ov['applied'])}")
    for oid in ov["refused"]:
        print(f"  ! override for {oid} ignored: the edition already gives a coordinate")

    g, summary = build_place_graph(records, provenance)
    ttl = out_dir / "places.crm.ttl"
    g.serialize(destination=str(ttl), format="turtle")
    write_csv(records, out_dir / "places.csv")
    n_geo = write_geojson(records, out_dir / "places.geojson")

    status = {}
    for rec in records:
        status[rec.get("geo_status", "missing")] = status.get(rec.get("geo_status", "missing"), 0) + 1
    summary.update(files=len(files), skipped=len(skipped), mapped=n_geo, status=status,
                   corpus=str(corpus), records=records, provenance=provenance or {})

    rel = (lambda p: p.relative_to(root)) if root else (lambda p: p)
    print(f"  {summary['stones']} stones, {summary['places']} distinct places "
          f"({summary['levels']} levels), {summary['gazetteer_links']} gazetteer links")
    print(f"  coordinates: " + ", ".join(f"{k} {v}" for k, v in sorted(status.items())))
    print(f"  -> wrote {rel(ttl)} ({summary['triples']} triples)")
    print(f"  -> wrote {rel(out_dir / 'places.csv')} ({len(records)} rows)")
    print(f"  -> wrote {rel(out_dir / 'places.geojson')} ({n_geo} points)")
    return summary


def readme_section(summary: dict) -> list[str]:
    """Markdown for the generated ``out/README.md``."""
    L, add = [], None
    L = []; add = L.append
    st = summary["status"]
    add("## 8. The place layer across the whole corpus (`places.crm.ttl`)\n")
    add("`main.py` crosswalks a few stones in full; the place layer crosswalks **one "
        "aspect across every EpiDoc file it is given** (`--corpus`, default `data/`). "
        f"This run read **{summary['files']} files** "
        f"({summary['stones']} editions"
        + (f", {summary['skipped']} template/test files skipped" if summary.get("skipped") else "")
        + f") and produced "
        f"**{summary['places']} distinct places** over {summary['levels']} administrative "
        f"levels, {summary['gazetteer_links']} gazetteer links and "
        f"{summary['triples']} triples.\n")
    add("| EpiDoc | Linked Open Ogham class | CIDOC CRM | property |")
    add("|---|---|---|---|")
    add("| `<origPlace>` | `ogham:Place` | `crm:E53_Place` | `P53_has_former_or_current_location` from the stone |")
    add("| `<geo>` | — | (on the `E53`) | `geo:asWKT` |")
    add("| `<placeName type=…>` | `ogham:Place` | `crm:E53_Place` | `P89_falls_within` (chained) |")
    add("| `@type` of the `<placeName>` | — | `crm:E55_Type` | `P2_has_type` |")
    add("| `<distinct xml:lang=…>` | — | — | `rdfs:label` with that language tag |")
    add("| `<ref target=\"logainm…\">` | — | — | weighted `skos:closeMatch` |\n")
    add("**The findspot is a place of its own, not the townland.** Stones in one "
        "townland do not always carry the same coordinates, so the geometry sits on a "
        "per-stone `data:findspot_*` node which `P89_falls_within` the shared townland "
        "node. Putting the geometry on the townland would invent a consensus the "
        "editions do not assert.\n")
    add("### Coordinate status\n")
    add("`<geo>` is not a strictly typed field. Beside plain `lat, lon` pairs it holds "
        "hedges (`(approximate)`, `(possible original location)`), `@cert=\"low\"`, and "
        "in a few records prose instead of numbers. Every findspot therefore carries "
        "`ogham:geoStatus`, and the editors' own wording is kept verbatim in a "
        "`P3_has_note`:\n")
    add("| `ogham:geoStatus` | n | meaning |")
    add("|---|---|---|")
    for key, meaning in (("asserted", "bare coordinate pair, no hedge"),
                         ("qualified", "coordinates plus `@cert` or a textual hedge"),
                         ("textual_only", "prose in `<geo>`, no numbers"),
                         ("supplied", "empty in the edition, filled from an outside source"),
                         ("missing", "empty `<geo/>`"),
                         ("no_origplace", "no `<origPlace>` in the file")):
        if st.get(key):
            add(f"| `{key}` | {st[key]} | {meaning} |")
    add("")
    add("This is the **hand-over point to axis 2**: `tei--epidoc-amt` turns "
        "`geoStatus`/`geoCertainty` and the note into an `amt:weight`-bearing reified "
        "statement over `geo:asWKT`, bridged to `crminf:I2_Belief`. Axis 1 stays "
        "structural and only records that the editors hedged, and how.\n")
    add("### Side outputs\n")
    add(f"`places.csv` ({summary['stones']} rows) and `places.geojson` "
        f"({summary['mapped']} points, WGS84) are written from the same parse, so the "
        "table, the map layer and the graph cannot drift apart. Each GeoJSON feature "
        "carries the URI of its `data:findspot_*` node, which is how a map click gets "
        "back into the graph.\n")
    prov = summary.get("provenance") or {}
    if prov.get("commit"):
        add("### Which corpus state this is\n")
        add("The editions are a living repository, so the graph records what it was built "
            "from — in `../data/corpus-manifest.yaml` and, as PROV-O, in the graph itself "
            "on `data:places-graph`:\n")
        add("| | |")
        add("|---|---|")
        add(f"| upstream commit | `{prov['commit'][:12]}` ({prov.get('commit_date', '')[:10]}) |")
        add(f"| fetched | {prov.get('fetched', '')[:10]} |")
        add(f"| editions | {prov.get('edition_count', '?')} |")
        if prov.get("tree_url"):
            add(f"| tree | <{prov['tree_url']}> |")
        add("")
    if summary.get("map"):
        add("`py/webmap.py` publishes the same records as a Leaflet map in `docs/` "
            f"({summary['map']['mapped']} points), which is what GitHub Pages serves. "
            "Nothing there re-parses the XML, so map, table and graph cannot disagree.\n")
    return L
