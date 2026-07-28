#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wikidata.py -- Wikidata reconciliation with type verification (axis 1 enrichment).
Orchestrated by ``py/main.py``.

Anchors selected terms (materials, object types, editors) to Wikidata QIDs and
returns a **confidence** in [0, 1] -- reconciliation is itself a vagueness problem,
so links are weighted rather than asserted as hard ``owl:sameAs``.

Two levels:

* basic  -- take the best ``wbsearchentities`` hit, confidence from label match;
* verify -- also fetch each candidate's types (P31 "instance of" / P279 "subclass
  of") and keep the highest-ranked candidate whose type fits the term's **kind**
  (editor -> human Q5; material -> rock/stone/material; object type -> monument/
  standing-stone/...). If none fits, the top hit is kept but its confidence is
  halved and it is flagged ``type_match = mismatch`` -- exactly the case that
  catches "Pillar -> column (architectural)" or "Rhys -> the given name".

A committed CSV cache (``data/wikidata-links.csv``) makes runs deterministic and
lets a human verify/override machine suggestions (``verified`` entries are trusted;
``auto`` entries are refreshed when online; ``pending`` entries resolved next run).
Any network failure falls back to the cache, so the pipeline never breaks.
"""
from __future__ import annotations

import csv
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

WD = "http://www.wikidata.org/entity/"
API = "https://www.wikidata.org/w/api.php"

# expected type per kind: for editors an exact P31 QID; for the rest, keywords that
# must appear in the label of a P31/P279 type of the candidate.
HUMAN_QID = "Q5"
TYPE_KEYWORDS = {
    "material": {"rock", "stone", "material", "mineral", "lithology", "sandstone", "granite"},
    "objectType": {"monument", "standing stone", "menhir", "megalith", "stele", "stela",
                   "cross", "pillar", "archaeological", "stone"},
}
# better search strings for known editors (label stays the surname; query is richer)
EDITOR_HINTS = {
    "Rhys": "John Rhys", "Macalister": "Robert Alexander Stewart Macalister",
    "Jackson": "Kenneth H. Jackson", "Diack": "Francis C. Diack",
}


@dataclass
class Match:
    qid: str = ""
    wd_label: str = ""
    confidence: float = 0.0
    status: str = "pending"       # pending | auto | verified
    type_match: str = ""          # ok | mismatch | unknown


def _api_get(params: dict, timeout: int = 8):
    try:
        url = f"{API}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "LinkedOpenOgham-reconciler/0.2"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except Exception:
        return {}


def _search(label: str, limit: int = 7):
    data = _api_get({"action": "wbsearchentities", "search": label, "language": "en",
                     "uselang": "en", "format": "json", "type": "item", "limit": str(limit)})
    return data.get("search", [])


def _confidence(label: str, hit: dict) -> float:
    lab = (hit.get("label") or "").strip().lower()
    q = label.strip().lower()
    if lab == q:
        return 0.90
    if q in lab or lab in q:
        return 0.70
    return 0.50


def candidate_types(qids: list) -> dict:
    """{qid: {'p31': set(QIDs), 'labels': set(lowercased type labels)}} for the P31/P279
    types of each candidate. Two batched calls; {} on any network failure."""
    if not qids:
        return {}
    claims = _api_get({"action": "wbgetentities", "ids": "|".join(qids),
                       "props": "claims", "format": "json"}).get("entities", {})
    types = {q: {"p31": set(), "labels": set()} for q in qids}
    all_type_qids = set()
    for q in qids:
        for prop in ("P31", "P279"):
            for stmt in claims.get(q, {}).get("claims", {}).get(prop, []):
                try:
                    tgt = stmt["mainsnak"]["datavalue"]["value"]["id"]
                except (KeyError, TypeError):
                    continue
                if prop == "P31":
                    types[q]["p31"].add(tgt)
                all_type_qids.add(tgt)
                types[q].setdefault("_tqids", set()).add(tgt)
    if all_type_qids:
        labels = _api_get({"action": "wbgetentities", "ids": "|".join(sorted(all_type_qids)),
                           "props": "labels", "languages": "en", "format": "json"}).get("entities", {})
        lab = {q: (labels.get(q, {}).get("labels", {}).get("en", {}).get("value", "")).lower()
               for q in all_type_qids}
        for q in qids:
            for tq in types[q].get("_tqids", set()):
                if lab.get(tq):
                    types[q]["labels"].add(lab[tq])
    return types


def _type_ok(kind: str, info: dict) -> bool:
    if kind == "editor":
        return HUMAN_QID in info.get("p31", set())
    kws = TYPE_KEYWORDS.get(kind, set())
    return any(any(k in lbl for k in kws) for lbl in info.get("labels", set()))


def reconcile(label: str, kind: str, cache: dict, online: bool = True,
              verify: bool = True, search_term: str = None, overrides: dict = None) -> Match:
    key = (kind, label)
    if overrides and key in overrides:             # curated allowlist wins over everything
        qid, wd_label = overrides[key]
        m = Match(qid, wd_label, 1.0, "verified", "curated")
        cache[key] = m
        return m
    cached = cache.get(key)
    if cached and cached.status == "verified":
        return cached
    if not online:
        return cached or Match()

    query = search_term or (EDITOR_HINTS.get(label, label) if kind == "editor" else label)
    hits = _search(query)
    if not hits:
        return cached or Match()

    if not verify:
        top = hits[0]
        m = Match(top["id"], top.get("label", ""), _confidence(label, top), "auto", "unknown")
        cache[key] = m
        return m

    types = candidate_types([h["id"] for h in hits[:5]])
    has_info = any((v.get("p31") or v.get("labels")) for v in types.values())
    if not has_info:                               # type lookup unavailable -> basic result
        top = hits[0]
        m = Match(top["id"], top.get("label", ""), _confidence(label, top), "auto", "unknown")
        cache[key] = m
        return m

    for hit in hits[:5]:                           # first candidate whose type fits the kind
        if _type_ok(kind, types.get(hit["id"], {})):
            m = Match(hit["id"], hit.get("label", ""),
                      min(1.0, round(_confidence(label, hit) + 0.05, 2)), "auto", "ok")
            cache[key] = m
            return m

    top = hits[0]                                  # nothing fits -> keep top, halve confidence, flag
    m = Match(top["id"], top.get("label", ""),
              round(_confidence(label, top) * 0.5, 2), "auto", "mismatch")
    cache[key] = m
    return m


def load_cache(path: Path) -> dict:
    cache: dict = {}
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                cache[(row["kind"], row["label"])] = Match(
                    qid=row.get("qid", "") or "", wd_label=row.get("wd_label", "") or "",
                    confidence=float(row["confidence"]) if row.get("confidence") else 0.0,
                    status=row.get("status", "pending") or "pending",
                    type_match=row.get("type_match", "") or "")
    return cache


def load_overrides(path: Path, kind: str) -> dict:
    """Curated allowlist: {(kind, term): (qid, wd_label)} for rows with a QID.
    These human-asserted anchors override the automatic reconciliation."""
    ov: dict = {}
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                qid = (row.get("qid") or "").strip()
                if qid:
                    ov[(kind, row["term"])] = (qid, (row.get("wd_label") or "").strip())
    return ov


def save_cache(path: Path, cache: dict) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "label", "qid", "wd_label", "confidence", "status", "type_match"])
        for (kind, label), m in sorted(cache.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            w.writerow([kind, label, m.qid, m.wd_label,
                        f"{m.confidence:.2f}" if m.qid else "", m.status, m.type_match])
