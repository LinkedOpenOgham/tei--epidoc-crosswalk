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
        req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}",
                                     headers={"User-Agent": UA})
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
                      re.sub(r"\s*\([^)]*\)", "", re.split(r"\s*[|,]", name)[0]),
                      (re.search(r"\(([^)]*)\)", name).group(1) if "(" in name else "")):
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


def looks_in_situ(name: str) -> bool:
    lowered = name.lower()
    return any(w in lowered for w in IN_SITU_WORDS)


def _wikidata(name: str) -> tuple[str, str, str, str]:
    """(qid, label, lat, lon) from Wikidata, or empty strings."""
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

    for qid in ids:                       # search order is Wikidata's relevance order
        entity = entities.get(qid)
        if not entity:
            continue
        types = [labels.get(c["mainsnak"]["datavalue"]["value"]["id"], "")
                 for c in entity.get("claims", {}).get("P31", [])
                 if c.get("mainsnak", {}).get("datavalue")]
        if not any(k in t for t in types for k in TYPE_KEYWORDS):
            continue
        for claim in entity.get("claims", {}).get("P625", []):
            value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
            if value:
                label = entity.get("labels", {}).get("en", {}).get("value", "")
                return qid, label, f"{value['latitude']:.6f}", f"{value['longitude']:.6f}"
        # right kind of thing but no coordinate: keep the QID, geocode elsewhere
        return qid, entity.get("labels", {}).get("en", {}).get("value", ""), "", ""
    return "", "", "", ""


def _nominatim(name: str) -> tuple[str, str]:
    data = _get(NOMINATIM, {"q": name, "format": "json", "limit": 1})
    time.sleep(1.1)                       # Nominatim asks for at most one call a second
    if data:
        return f"{float(data[0]['lat']):.6f}", f"{float(data[0]['lon']):.6f}"
    return "", ""


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


def resolve(names: list[str], cache: dict[str, Keeper], online: bool = True) -> dict:
    """Fill in whatever is missing. Verified entries are never touched."""
    fetched = 0
    for name in names:
        entry = cache.setdefault(name, Keeper(repository=name))
        if entry.status == "verified" or entry.located:
            continue
        if not online:
            continue
        qid = label = lat = lon = source = ""
        for variant in name_variants(name):
            qid, label, lat, lon = _wikidata(variant)
            if lat:
                source = "wikidata"
                break
        if not lat:
            for variant in name_variants(name):
                lat, lon = _nominatim(variant)
                if lat:
                    source = "osm"
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
    return {"fetched": fetched,
            "located": sum(1 for k in cache.values() if k.located),
            "total": len(names)}


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
    return [{**r, "why": f"a church or chapel {r['km']} km from the findspot is "
                         f"probably the wrong one of that dedication"}
            for r in links
            if looks_in_situ(r["keeper"]) and r["km"] > IN_SITU_MAX_KM]


def link(place_records: list[dict], cache: dict[str, Keeper]) -> list[dict]:
    """One record per stone that has both a findspot and a located keeper."""
    out = []
    for rec in place_records:
        name = (rec.get("repository") or "").strip()
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
            g.add((keeper, RDF.type, CRM["E40_Legal_Body"]))
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
