#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wikidata.py -- lightweight Wikidata reconciliation for the crosswalk (axis 1
enrichment). Orchestrated by ``py/main.py``.

Anchors selected terms (materials, object types, editors) to Wikidata QIDs and
returns a **confidence** in [0, 1] -- reconciliation is itself a vagueness problem,
so links are weighted rather than asserted as hard `owl:sameAs`.

A committed CSV cache (``data/wikidata-links.csv``) makes runs deterministic and
lets a human verify or override machine suggestions:

* ``status = verified`` -- human-checked, trusted, never re-fetched;
* ``status = auto``     -- machine-suggested, refreshed from the live API when online;
* ``status = pending``  -- no QID yet (resolved on the next online run).

The live API (``wbsearchentities``) is only queried for non-verified terms, and any
network failure (offline / blocked / rate-limited) silently falls back to the cache,
so the pipeline never breaks.
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


@dataclass
class Match:
    qid: str = ""
    wd_label: str = ""
    confidence: float = 0.0
    status: str = "pending"      # pending | auto | verified


def _search(label: str, limit: int = 5, timeout: int = 6):
    """Call wbsearchentities; return the list of hits, or [] on any failure."""
    params = urllib.parse.urlencode({
        "action": "wbsearchentities", "search": label, "language": "en",
        "uselang": "en", "format": "json", "type": "item", "limit": str(limit)})
    try:
        req = urllib.request.Request(
            f"{API}?{params}", headers={"User-Agent": "LinkedOpenOgham-reconciler/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r).get("search", [])
    except Exception:
        return []


def _confidence(label: str, hits: list) -> float:
    """Documented heuristic confidence for the top hit."""
    if not hits:
        return 0.0
    lab = (hits[0].get("label") or "").strip().lower()
    q = label.strip().lower()
    if lab == q:                       # exact label match
        conf = 0.90
    elif q in lab or lab in q:         # partial match
        conf = 0.70
    else:
        conf = 0.50
    if len(hits) == 1:                 # unambiguous
        conf = min(1.0, conf + 0.05)
    return round(conf, 2)


def reconcile(label: str, kind: str, cache: dict, online: bool = True) -> Match:
    """Return a Match for (kind, label). Verified entries are trusted; auto/pending
    entries are refreshed from the live API when online, else served from cache."""
    key = (kind, label)
    cached = cache.get(key)
    if cached and cached.status == "verified":
        return cached
    if online:
        hits = _search(label)
        if hits:
            m = Match(qid=hits[0]["id"], wd_label=hits[0].get("label", ""),
                      confidence=_confidence(label, hits), status="auto")
            cache[key] = m
            return m
    return cached or Match()


def load_cache(path: Path) -> dict:
    cache: dict = {}
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                cache[(row["kind"], row["label"])] = Match(
                    qid=row.get("qid", "") or "", wd_label=row.get("wd_label", "") or "",
                    confidence=float(row["confidence"]) if row.get("confidence") else 0.0,
                    status=row.get("status", "pending") or "pending")
    return cache


def save_cache(path: Path, cache: dict) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "label", "qid", "wd_label", "confidence", "status"])
        for (kind, label), m in sorted(cache.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            w.writerow([kind, label, m.qid, m.wd_label,
                        f"{m.confidence:.2f}" if m.qid else "", m.status])
