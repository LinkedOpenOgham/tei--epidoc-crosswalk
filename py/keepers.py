#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""keepers.py -- where the stones are now, and how far that is from where they were found.

``<msIdentifier>/<repository>`` names an institution but gives no coordinate, so the
displacement from findspot to present keeper cannot be drawn without geocoding those
39 names. This module resolves them against **Wikidata** first (an institution has a
QID, and the QID is what belongs in the graph) and falls back to **OSM Nominatim**
for the small local museums Wikidata does not carry.

The result is a committed CSV, ``reconciliation/keeper-coordinates.csv``, in the same
shape as the existing Wikidata cache: machine suggestions are marked ``auto`` and are
meant to be read and either confirmed (``verified``) or corrected. A geocode is a
claim about the world, and an unchecked one should look unchecked.

CIDOC CRM modelling, which also resolves an ambiguity the place layer left open:

    stone  crm:P50_has_current_keeper      keeper        (E39_Actor / E40_Legal_Body)
    stone  crm:P55_has_current_location    keeperPlace   (E53_Place)
    keeper crm:P74_has_current_or_former_residence  keeperPlace

The findspot keeps ``P53_has_former_or_current_location``; the museum gets ``P55``,
which is specifically the *current* location. Both were previously candidates for
P53, which would have made the two indistinguishable in a query.
"""
from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict, fields
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

WD_API = "https://www.wikidata.org/w/api.php"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
NOMINATIM_LOOKUP = "https://nominatim.openstreetmap.org/lookup"
OSM_API = "https://api.openstreetmap.org/api/0.6"
UA = "LinkedOpenOgham-keeper-geocoder/0.1 (https://github.com/LinkedOpenOgham)"

CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
OGHAM = Namespace("http://ontology.ogham.link/")
DATA_NS = Namespace("http://data.ogham.link/crm/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
AMT = Namespace("http://academic-meta-tool.xyz/vocab#")
WD = Namespace("http://www.wikidata.org/entity/")

# A candidate is only accepted if one of its P31 types reads like a place that keeps
# things. Without this, "Perth Museum" happily resolves to a town in Australia.
TYPE_KEYWORDS = {
    "museum", "library", "gallery", "university", "college", "collection",
    "archive", "church", "abbey", "cathedral", "heritage", "institution",
    "organization", "organisation", "building", "castle", "chapel",
}


@dataclass
class Keeper:
    repository: str = ""
    alias_of: str = ""        # another repository string naming the same place
    osm_id: str = ""          # e.g. way/404085430 -- a human-checked identification
    qid: str = ""
    wd_label: str = ""
    lat: str = ""
    lon: str = ""
    source: str = ""          # wikidata | osm | manual
    status: str = "pending"   # pending | auto | verified
    note: str = ""

    @property
    def located(self) -> bool:
        return bool(self.lat and self.lon)


def _get(url: str, params: dict, timeout: int = 12):
    try:
        full = f"{url}?{urllib.parse.urlencode(params)}" if params else url
        req = urllib.request.Request(full, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except Exception:
        return None


# The corpus qualifies institution names in ways a search engine chokes on:
# "Carmarthen Museum, Abergwili", "Armagh Robinson library (No 5 Vicars’ Hill
# Museum)", "Museum nan Eilean in Steòrnabhagh | Stornoway". Searching the full
# string returns nothing; the leading name almost always resolves. Tried in order,
# most specific first, so a qualifier is only dropped when it has to be.
def name_variants(name: str) -> list[str]:
    import re
    out, seen = [], set()
    for candidate in (name,
                      re.sub(r"\s*\([^)]*\)", "", name),
                      re.split(r"\s*[|,]", name)[0],
                      re.sub(r"\s*\([^)]*\)", "", re.split(r"\s*[|,]", name)[0])):
        # The parenthetical alone is deliberately NOT tried: "Llansaint Chapel
        # (All Saints' Church)" fell through to the dedication and matched a
        # church in Ireland, 317 km from a Carmarthenshire stone.
        candidate = candidate.strip(" ,|")
        if len(candidate) > 3 and candidate.lower() not in seen:
            seen.add(candidate.lower())
            out.append(candidate)
    return out


# A church, chapel or graveyard normally holds a stone *in situ*: a large distance
# from the findspot means the geocoder found a different church of the same
# dedication, not that the stone travelled. St Brynach's is the case in point --
# there are five in Wales, and the stone is at the one in Nevern.
IN_SITU_WORDS = {"church", "chapel", "graveyard", "cemetery", "abbey", "cathedral",
                 "eaglais", "capel", "llan"}
IN_SITU_MAX_KM = 25.0

# An institution is looked for in the country its stones come from -- but as a
# *preference*, never a filter. Stones really do cross borders: nine Irish stones
# are in the British Museum and three in the Pitt Rivers, and a hard country test
# would throw out exactly the cases this map exists to show. So each lookup runs
# twice: in-country first, then unrestricted.
COUNTRY_BOX = {
    "Ireland": (51.3, 55.5, -10.8, -5.9),
    "Northern Ireland": (53.9, 55.4, -8.3, -5.3),
    "Scotland": (54.5, 61.0, -8.7, -0.7),
    "Wales": (51.3, 53.5, -5.4, -2.6),
    "England": (49.8, 55.9, -6.5, 1.9),
    "Isle of Man": (54.0, 54.5, -4.9, -4.2),
}
COUNTRY_CODE = {"Ireland": "ie", "Northern Ireland": "gb", "Scotland": "gb",
                "Wales": "gb", "England": "gb", "Isle of Man": "im"}


def in_country(lat: float, lon: float, country: str) -> bool:
    box = COUNTRY_BOX.get(country or "")
    if not box:
        return True
    a, b, c, d = box
    return a <= lat <= b and c <= lon <= d


def looks_in_situ(name: str) -> bool:
    lowered = name.lower()
    return any(w in lowered for w in IN_SITU_WORDS)


def _wikidata_by_qid(qid: str) -> tuple[str, str, str]:
    """(label, lat, lon) for one named entity -- no searching involved.

    A QID written into the cache by hand is a decision, not a guess, so it is
    resolved directly. Searching by name would only re-open the question the QID
    was put there to close.
    """
    data = _get(WD_API, {"action": "wbgetentities", "ids": qid,
                         "props": "claims|labels", "languages": "en", "format": "json"})
    entity = (data or {}).get("entities", {}).get(qid)
    if not entity:
        return "", "", ""
    label = entity.get("labels", {}).get("en", {}).get("value", "")
    for claim in entity.get("claims", {}).get("P625", []):
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if value:
            return label, f"{float(value['latitude']):.6f}", f"{float(value['longitude']):.6f}"
    return label, "", ""


def _wikidata(name: str, country: str = "") -> tuple[str, str, str, str]:
    """(qid, label, lat, lon) from Wikidata, or empty strings.

    ``country`` is the country the institution's stones were found in; a candidate
    whose coordinate falls outside it is passed over.
    """
    hits = _get(WD_API, {"action": "wbsearchentities", "search": name, "language": "en",
                         "uselang": "en", "format": "json", "limit": 7, "type": "item"})
    ids = [h["id"] for h in (hits or {}).get("search", [])]
    if not ids:
        return "", "", "", ""
    data = _get(WD_API, {"action": "wbgetentities", "ids": "|".join(ids[:7]),
                         "props": "claims|labels", "languages": "en", "format": "json"})
    entities = (data or {}).get("entities", {})

    # resolve the P31 type labels once, so a candidate can be judged on what it is
    type_ids = {c["mainsnak"]["datavalue"]["value"]["id"]
                for e in entities.values()
                for c in e.get("claims", {}).get("P31", [])
                if c.get("mainsnak", {}).get("datavalue")}
    labels = {}
    if type_ids:
        info = _get(WD_API, {"action": "wbgetentities", "ids": "|".join(sorted(type_ids)[:50]),
                             "props": "labels", "languages": "en", "format": "json"})
        labels = {k: (v.get("labels", {}).get("en", {}).get("value") or "").lower()
                  for k, v in (info or {}).get("entities", {}).items()}

    fallback = ("", "", "", "")
    for restrict in (True, False):        # in-country first, then anywhere
        for qid in ids:                   # search order is Wikidata's relevance order
            entity = entities.get(qid)
            if not entity:
                continue
            types = [labels.get(c["mainsnak"]["datavalue"]["value"]["id"], "")
                     for c in entity.get("claims", {}).get("P31", [])
                     if c.get("mainsnak", {}).get("datavalue")]
            if not any(k in t for t in types for k in TYPE_KEYWORDS):
                continue
            label = entity.get("labels", {}).get("en", {}).get("value", "")
            for claim in entity.get("claims", {}).get("P625", []):
                value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
                if not value:
                    continue
                lat, lon = float(value["latitude"]), float(value["longitude"])
                if restrict and country and not in_country(lat, lon, country):
                    continue
                return qid, label, f"{lat:.6f}", f"{lon:.6f}"
            if not fallback[0]:           # right kind of thing but no coordinate
                fallback = (qid, label, "", "")
    return fallback


def _osm_centroid(kind: str, number: str) -> tuple[str, str]:
    """Mean of an object's node coordinates, straight from the OSM API.

    Nominatim only knows objects its indexer has picked up; the OSM API knows
    every object that exists, including ones mapped last week. It is the fallback
    when a perfectly valid id comes back empty from the geocoder.
    """
    if kind == "node":
        data = _get(f"{OSM_API}/node/{number}.json", {})
        nodes = [e for e in (data or {}).get("elements", []) if e.get("type") == "node"]
    else:
        data = _get(f"{OSM_API}/{kind}/{number}/full.json", {})
        nodes = [e for e in (data or {}).get("elements", []) if e.get("type") == "node"]
    if not nodes:
        return "", ""
    lat = sum(n["lat"] for n in nodes) / len(nodes)
    lon = sum(n["lon"] for n in nodes) / len(nodes)
    return f"{lat:.6f}", f"{lon:.6f}"


def _osm_lookup(osm_id: str) -> tuple[str, str]:
    """Coordinates for a specific OSM object, e.g. ``way/404085430``.

    An OSM id supplied by an editor is worth more than any search: it names one
    object, it can be checked, and it does not drift the way a coordinate typed
    from a map does. Where one is present it is used in preference to searching.

    Two sources are tried. Nominatim's ``/lookup`` endpoint -- note *lookup*, not
    *search*: ``osm_ids`` is not a search parameter, and sending it to /search
    silently returns nothing, which is exactly how this failed the first time.
    Then the OSM API itself, whose coverage is complete.
    """
    kind, _, number = osm_id.strip().lower().partition("/")
    prefix = {"way": "W", "node": "N", "relation": "R"}.get(kind)
    if not prefix or not number.isdigit():
        return "", ""
    data = _get(NOMINATIM_LOOKUP, {"osm_ids": f"{prefix}{number}", "format": "json"})
    time.sleep(1.1)
    if data:
        return f"{float(data[0]['lat']):.6f}", f"{float(data[0]['lon']):.6f}"
    return _osm_centroid(kind, number)


def _nominatim(name: str, country: str = "") -> tuple[str, str, str]:
    """(lat, lon, osm_id). The search response names the object it matched, so the
    identifier is kept: it is what turns a guess into something checkable, and what
    lets a later run fetch the coordinate without searching again."""
    code = COUNTRY_CODE.get(country or "")
    for params in ([{"q": name, "format": "json", "limit": 1, "countrycodes": code}] if code else []) \
                  + [{"q": name, "format": "json", "limit": 1}]:
        data = _get(NOMINATIM, params)
        time.sleep(1.1)                   # Nominatim asks for at most one call a second
        if data:
            hit = data[0]
            osm = (f"{hit['osm_type']}/{hit['osm_id']}"
                   if hit.get("osm_type") and hit.get("osm_id") else "")
            return f"{float(hit['lat']):.6f}", f"{float(hit['lon']):.6f}", osm
    return "", "", ""


def load_cache(path: Path) -> dict[str, Keeper]:
    if not path.exists():
        return {}
    names = {f.name for f in fields(Keeper)}
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return {row["repository"]: Keeper(**{k: (v or "") for k, v in row.items() if k in names})
                for row in csv.DictReader(fh) if row.get("repository")}


def save_cache(path: Path, cache: dict[str, Keeper]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[f.name for f in fields(Keeper)])
        w.writeheader()
        for key in sorted(cache):
            w.writerow(asdict(cache[key]))


def apply_identifiers(cache: dict[str, Keeper], entries: dict) -> int:
    """Lay the hand-set file over the cache. Runs before every resolve, so the
    cache can be deleted without losing a single decision."""
    applied = 0
    for name, row in (entries or {}).items():
        entry = cache.setdefault(name, Keeper(repository=name))
        touched = False
        for field in ("qid", "osm_id", "alias_of", "note"):
            if row.get(field) and getattr(entry, field) != str(row[field]):
                setattr(entry, field, str(row[field]))
                touched = True
        if row.get("lat") is not None and row.get("lon") is not None:
            lat, lon = f"{float(row['lat']):.6f}", f"{float(row['lon']):.6f}"
            if (entry.lat, entry.lon) != (lat, lon):
                entry.lat, entry.lon = lat, lon
                entry.source = row.get("source") or "manual"
                entry.status = "verified"
                touched = True
        if touched:
            applied += 1
    return applied


def resolve(names: list[str], cache: dict[str, Keeper], online: bool = True,
            countries: dict[str, str] | None = None) -> dict:
    """Fill in whatever is missing. Verified entries are never touched."""
    countries = countries or {}
    fetched = 0
    for name in names:
        entry = cache.setdefault(name, Keeper(repository=name))
        if entry.alias_of:                # merged into another row; nothing to look up
            continue
        if entry.source == "manual":      # a coordinate typed from a source is final
            continue
        # An identifier is refreshed on every run rather than resolved once: the
        # fixed file holds the identifier, this cache holds today's coordinate, and
        # if Wikidata or OSM moves the point the next run picks it up. Only a search
        # result is taken from the cache, because repeating a search is not a refresh
        # -- it is another chance to land somewhere else.
        pinned = bool(entry.qid or entry.osm_id)
        if entry.located and not pinned:
            continue
        if not online:
            continue
        country = countries.get(name, "")
        qid = label = lat = lon = source = ""

        # Order of precedence: a QID set by hand, then an OSM id set by hand, then a
        # search. Both identifiers are human decisions; the QID wins because it is
        # what ends up in the graph as the close match anyway.
        if entry.qid:
            label, lat, lon = _wikidata_by_qid(entry.qid)
            if lat:
                entry.lat, entry.lon = lat, lon
                entry.wd_label = label or entry.wd_label
                entry.source, entry.status = "wikidata-qid", "verified"
                fetched += 1
                print(f"    {name[:44]:46} wd-qid   {entry.qid} {lat}, {lon}")
                continue
            print(f"    {name[:44]:46} {entry.qid} has no coordinate (P625); "
                  f"leaving it unset rather than searching")
            entry.note = f"{entry.note} || {entry.qid} carries no P625".strip(" |")
            continue

        if entry.osm_id:                  # a named object: fetch its coordinate
            lat, lon = _osm_lookup(entry.osm_id)
            if lat:
                entry.lat, entry.lon = lat, lon
                entry.source = "osm-id"
                # the identification was human; only the coordinate was looked up
                entry.status = "verified"
                fetched += 1
                print(f"    {name[:44]:46} osm-id   {lat}, {lon}")
            else:
                # Deliberately no fall-back to searching. An id is usually present
                # *because* the search got it wrong, so quietly reinstating the
                # search result would undo the correction and mark it plausible.
                entry.note = (entry.note or "") and entry.note.split(" || ")[0]
                entry.note = f"{entry.note} || {entry.osm_id} did not resolve".strip(" |")
                print(f"    {name[:44]:46} {entry.osm_id} did not resolve; left unset "
                      f"rather than falling back to a search")
            continue

        for variant in name_variants(name):
            qid, label, lat, lon = _wikidata(variant, country)
            if lat:
                source = "wikidata"
                break
        if not lat:
            for variant in name_variants(name):
                lat, lon, found_osm = _nominatim(variant, country)
                if lat:
                    source = "osm"
                    if found_osm and not entry.osm_id:
                        entry.osm_id = found_osm
                    break
        if qid:
            entry.qid, entry.wd_label = qid, label
        if lat:
            entry.lat, entry.lon, entry.source, entry.status = lat, lon, source, "auto"
            fetched += 1
            print(f"    {name[:44]:46} {source:8} {lat}, {lon}")
        else:
            entry.note = entry.note or "not found; fill lat/lon by hand"
            print(f"    {name[:44]:46} not found")
    # An alias has no coordinate of its own by design, so it is neither located
    # nor outstanding: counting it would report a permanent shortfall.
    wanted = [n for n in names if not (cache.get(n) and cache[n].alias_of)]
    return {"fetched": fetched,
            "located": sum(1 for n in wanted if cache.get(n) and cache[n].located),
            "total": len(wanted),
            "aliases": len(names) - len(wanted)}


# --- linking ------------------------------------------------------------------

def _slug(text: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9]+", "_", text or "").strip("_") or "x"


def _km(a_lat, a_lon, b_lat, b_lon) -> float:
    import math
    r = 6371.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = p2 - p1, math.radians(b_lon - a_lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def check(links: list[dict]) -> list[dict]:
    """Geocodes worth a second look, so they do not sit unexamined in the graph."""
    # Distance alone says nothing: Shetland to Edinburgh is genuinely 460 km and
    # Cork to the British Museum 600, both correct. Only the in-situ case is a real
    # signal, and on the current data it fires once -- on the right record.
    return [{**r, "why": f"a church or chapel {r['km']} km from the findspot is probably "
                         f"the wrong one of that dedication; if the stone is in situ the "
                         f"keeper coordinate is {r['lat']:.4f}, {r['lon']:.4f}"}
            for r in links
            if looks_in_situ(r["keeper"]) and r["km"] > IN_SITU_MAX_KM]


def canonical(name: str, cache: dict[str, Keeper]) -> str:
    """Follow ``alias_of`` to the string that stands for the place.

    The corpus names an institution at two granularities -- "National Museums of
    Scotland" (the body) and "National Museum of Scotland" (the building on
    Chambers Street). Wikidata rightly gives them different QIDs; on a map of
    *places* they are one point, so the alias merges them.
    """
    seen = set()
    while True:
        entry = cache.get(name)
        if not entry or not entry.alias_of or name in seen:
            return name
        seen.add(name)
        name = entry.alias_of


def link(place_records: list[dict], cache: dict[str, Keeper]) -> list[dict]:
    """One record per stone that has both a findspot and a located keeper."""
    out = []
    for rec in place_records:
        name = canonical((rec.get("repository") or "").strip(), cache)
        if not name or rec.get("lat") is None:
            continue
        keeper = cache.get(name)
        if not keeper or not keeper.located:
            continue
        klat, klon = float(keeper.lat), float(keeper.lon)
        out.append({
            "ogham_id": rec["ogham_id"], "stone_key": rec["stone_key"],
            "title": rec["title"], "ciic": rec.get("ciic", ""),
            "county": rec.get("pn_county", ""), "country": rec.get("pn_country", ""),
            "lat": rec["lat"], "lon": rec["lon"],
            "keeper": name, "keeper_qid": keeper.qid,
            "keeper_lat": klat, "keeper_lon": klon, "keeper_source": keeper.source,
            "km": round(_km(rec["lat"], rec["lon"], klat, klon), 1),
        })
    return out


def undrawable(place_records: list[dict], cache: dict[str, Keeper]) -> list[dict]:
    """Stones that name a keeper but cannot be drawn, and why.

    A count in the sidebar that quietly disagrees with the corpus is worse than a
    gap that is stated: University College Cork holds 28 stones, but one of them
    (I-COR-087, Mountmusic) has an empty <geo/>, so only 27 arcs exist.
    """
    out = []
    for rec in place_records:
        raw = (rec.get("repository") or "").strip()
        if not raw:
            continue
        name = canonical(raw, cache)
        keeper = cache.get(name)
        if rec.get("lat") is None:
            why = "no findspot coordinate in the edition"
        elif not keeper or not keeper.located:
            why = "the institution is not geocoded yet"
        else:
            continue
        out.append({"ogham_id": rec.get("ogham_id", ""), "ciic": rec.get("ciic", ""),
                    "title": rec.get("title", ""), "keeper": raw, "why": why})
    return out


CSV_FIELDS = ["ogham_id", "ciic", "title", "findspot_county", "findspot_country",
              "findspot_lat", "findspot_lon", "keeper", "keeper_qid",
              "keeper_lat", "keeper_lon", "keeper_source", "distance_km"]


def write_csv(links: list[dict], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in links:
            w.writerow({
                "ogham_id": r["ogham_id"], "ciic": r["ciic"], "title": r["title"],
                "findspot_county": r["county"], "findspot_country": r["country"],
                "findspot_lat": r["lat"], "findspot_lon": r["lon"],
                "keeper": r["keeper"], "keeper_qid": r["keeper_qid"],
                "keeper_lat": r["keeper_lat"], "keeper_lon": r["keeper_lon"],
                "keeper_source": r["keeper_source"], "distance_km": r["km"],
            })
    return len(links)


def build_graph(links: list[dict], cache: dict[str, Keeper]) -> tuple[Graph, dict]:
    g = Graph()
    for pfx, ns in (("crm", CRM), ("geo", GEO), ("ogham", OGHAM), ("data", DATA_NS),
                    ("skos", SKOS), ("amt", AMT), ("wd", WD), ("rdfs", RDFS), ("xsd", XSD)):
        g.bind(pfx, ns)

    seen: set[str] = set()
    for r in links:
        sid = _slug(r["stone_key"])
        kid = _slug(r["keeper"])
        stone = DATA_NS[f"stone_{sid}"]
        keeper = DATA_NS[f"keeper_{kid}"]
        place = DATA_NS[f"place_keeper_{kid}"]

        if kid not in seen:
            seen.add(kid)
            # E40_Legal_Body was removed in CIDOC CRM 7.x. A holding institution is
            # an E74_Group, which is an E39_Actor -- and being an Actor is what
            # P50_has_current_keeper and P74 require of it.
            g.add((keeper, RDF.type, CRM["E74_Group"]))
            g.add((keeper, RDFS.label, Literal(r["keeper"])))
            g.add((place, RDF.type, CRM["E53_Place"]))
            g.add((place, RDFS.label, Literal(f"{r['keeper']} (present location)")))
            g.add((place, GEO.asWKT,
                   Literal(f"POINT({r['keeper_lon']} {r['keeper_lat']})",
                           datatype=GEO.wktLiteral)))
            g.add((place, OGHAM.geocodedFrom, Literal(r["keeper_source"])))
            g.add((keeper, CRM["P74_has_current_or_former_residence"], place))
            entry = cache.get(r["keeper"])
            if entry and entry.qid:
                target = WD[entry.qid]
                g.add((keeper, SKOS.closeMatch, target))
                st = DATA_NS[f"match_keeper_{kid}"]
                g.add((st, RDF.type, RDF.Statement))
                g.add((st, RDF.subject, keeper))
                g.add((st, RDF.predicate, SKOS.closeMatch))
                g.add((st, RDF.object, target))
                weight = "1.00" if entry.status == "verified" else "0.70"
                g.add((st, AMT.weight, Literal(weight, datatype=XSD.decimal)))
                g.add((st, OGHAM.matchConfidence, Literal(weight, datatype=XSD.decimal)))
                g.add((st, OGHAM.matchStatus, Literal(entry.status)))

        g.add((stone, CRM["P50_has_current_keeper"], keeper))
        g.add((stone, CRM["P55_has_current_location"], place))

    return g, {"stones": len(links), "keepers": len(seen)}
