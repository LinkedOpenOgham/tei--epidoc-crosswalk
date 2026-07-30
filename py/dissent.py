#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dissent.py -- where the editors disagree.

The crosswalk already models every competing reading as a
``crmtex:TX6_Transcription`` attributed to its editor with PROV-O. This module
adds no triples: it is a **view over structure the graph already carries**, which
is the point — the same question is one SPARQL query away:

    SELECT ?stone (COUNT(DISTINCT ?reading) AS ?n) WHERE {
      ?stone crm:P128_carries ?inscription .
      ?inscription crmtex:TXP4_has_segment ?reading .
      ?reading a crmtex:TX6_Transcription ; prov:wasAttributedTo ?editor .
    } GROUP BY ?stone HAVING (?n > 1)

What it computes is the *degree* of disagreement, and that is an analytical aid,
not an assertion: a character-level similarity between the current OG(H)AM edition
and each earlier reading of the same script. Two readings can score 0.83 and still
differ over everything that matters (MAQI against MAQI MUCOI), or score 0.5 because
one editor saw four more letters on a broken stone. The score orders the corpus for
inspection; the readings themselves are what a reader should judge.

Readings are only compared **within one script**. A bilingual stone carries an
ogham and a Roman-script reading of the same monument; comparing them would
measure the difference between two languages, not between two editors.
"""
from __future__ import annotations

import csv
import difflib
from pathlib import Path

# how far apart two readings are, and what to call it
BANDS = [
    (1.00, "identical", "the same reading, differently printed"),
    (0.80, "close", "small differences in letters or length"),
    (0.50, "diverging", "substantially different text"),
    (0.00, "far apart", "little or nothing in common"),
]


def band(similarity: float) -> str:
    for threshold, name, _ in BANDS:
        if similarity >= threshold:
            return name
    return BANDS[-1][1]


def compare(record: dict, normalise, find, vocabulary) -> dict | None:
    """Pair the current edition against every earlier reading of the same script."""
    readings = record.get("readings") or []
    if len(readings) < 2:
        return None

    pairs = []
    for script in sorted({r.get("script", "ogham") for r in readings}):
        same = [r for r in readings if r.get("script", "ogham") == script]
        current = next((r for r in same if r["current"]), None)
        if current is None or len(same) < 2:
            continue
        base = normalise(current["text"])
        base_tokens = base.split()
        base_words = {(m["word"], m["mode"]) for m in find(base, vocabulary)}
        for other in same:
            if other is current:
                continue
            text = normalise(other["text"])
            tokens = text.split()
            words_here = {(m["word"], m["mode"]) for m in find(text, vocabulary)}
            gained = sorted(w for w, mode in words_here - base_words if mode == "formula")
            lost = sorted(w for w, mode in base_words - words_here if mode == "formula")
            similarity = difflib.SequenceMatcher(None, base, text).ratio() if (base or text) else 1.0
            pairs.append({
                "script": script,
                "editor": other["editor"],
                "editor_id": other["id"],
                "current_text": current["text"],
                "other_text": other["text"],
                "current_norm": base,
                "other_norm": text,
                "similarity": round(similarity, 3),
                "band": band(similarity),
                "only_current": [t for t in base_tokens if t not in tokens],
                "only_other": [t for t in tokens if t not in base_tokens],
                "formula_gained": gained,
                "formula_lost": lost,
            })
    if not pairs:
        return None

    worst = min(p["similarity"] for p in pairs)
    return {
        "ogham_id": record["ogham_id"],
        "stone_key": record["stone_key"],
        "title": record["title"],
        "ciic": record["ciic"],
        "pairs": pairs,
        "editors": sorted({p["editor"] for p in pairs}),
        "min_similarity": worst,
        "band": band(worst),
        "formula_at_stake": any(p["formula_gained"] or p["formula_lost"] for p in pairs),
    }


def analyse(records: list[dict], normalise, find, vocabulary) -> list[dict]:
    out = [compare(r, normalise, find, vocabulary) for r in records]
    return [r for r in out if r]


CSV_FIELDS = ["ogham_id", "ciic", "title", "script", "editor", "similarity", "band",
              "formula_gained", "formula_lost", "only_in_current_edition",
              "only_in_this_reading", "current_edition_text", "this_reading_text"]


def write_csv(analysis: list[dict], path: Path) -> int:
    rows = []
    for rec in analysis:
        for p in rec["pairs"]:
            rows.append({
                "ogham_id": rec["ogham_id"], "ciic": rec["ciic"], "title": rec["title"],
                "script": p["script"], "editor": p["editor"],
                "similarity": f"{p['similarity']:.3f}", "band": p["band"],
                "formula_gained": " ".join(p["formula_gained"]),
                "formula_lost": " ".join(p["formula_lost"]),
                "only_in_current_edition": " ".join(p["only_current"]),
                "only_in_this_reading": " ".join(p["only_other"]),
                "current_edition_text": p["current_text"],
                "this_reading_text": p["other_text"],
            })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def summarise(analysis: list[dict]) -> dict:
    bands: dict[str, int] = {}
    editors: dict[str, int] = {}
    for rec in analysis:
        bands[rec["band"]] = bands.get(rec["band"], 0) + 1
        for p in rec["pairs"]:
            editors[p["editor"]] = editors.get(p["editor"], 0) + 1
    return {
        "stones": len(analysis),
        "pairs": sum(len(r["pairs"]) for r in analysis),
        "editors": len(editors),
        "formula_at_stake": sum(1 for r in analysis if r["formula_at_stake"]),
        "bands": bands,
        "by_editor": editors,
    }
