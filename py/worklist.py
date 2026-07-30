#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""worklist.py -- what in the corpus is worth a trip to the literature.

Generates ``out/worklist.md``: every gap this pipeline can see, grouped by how
much a fix is worth and how likely one exists. It is generated rather than written
by hand so it shrinks as the corpus and the override files grow.

The grouping matters more than the list. The OG(H)AM identifiers encode a
distinction that a naive gap report would flatten:

  I-KER-042   a numbered stone -- extant, catalogued, and simply missing a datum
  I-KER-L02   the L series -- lost. "Broken up for building material, no record of
              its inscription was preserved" (Macalister 1945). The stone is gone;
              its findspot may still be recorded.
  I-KER-X01   the X series -- doubtful. Often "findspot uncertain" in the edition
              itself, and sometimes not accepted as ogham at all.

Filling a coordinate for a numbered stone is completing a record. Doing it for an
X stone may be asserting a precision the evidence does not carry, which is the
opposite of the point.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

SERIES_RE = re.compile(r"^[A-Z]-[A-Z]{3}-([A-Z]?)")

SERIES = {
    "": ("numbered", "extant and catalogued"),
    "L": ("lost", "stone gone; the findspot may still be recorded"),
    "X": ("doubtful", "uncertain findspot, or not accepted as ogham"),
}


# CISP publishes a stone at .../stone/wvale_1.html, but 153 of the corpus's
# corresp URLs carry the *identifier* form .../stone/WVALE/1.html, which 404s, and
# 47 more are empty. The conversion is mechanical, so the worklist links are
# repaired on the way out rather than sending anyone to a dead page.
CISP_BASE = "https://www.ucl.ac.uk/archaeology/cisp/database/stone/"
CISP_OK_RE = re.compile(r"[a-z0-9]+_\d+\.html$")

# The edition sometimes states that a findspot is not recoverable. That is a
# finding, not a gap, and chasing it wastes an afternoon.
SETTLED_RE = re.compile(r"unrecorded|uncertain|unknown|not recorded", re.I)


def cisp_link(cisp_id: str, corpus_url: str) -> str:
    """A URL that resolves, from whichever of the two the corpus gives."""
    if corpus_url and CISP_OK_RE.search(corpus_url):
        return corpus_url
    if cisp_id and "/" in cisp_id:
        return CISP_BASE + cisp_id.lower().replace("/", "_") + ".html"
    return ""


def cisp_url_state(cisp_id: str, corpus_url: str) -> str:
    if not corpus_url:
        return "none"
    if CISP_OK_RE.search(corpus_url):
        return "ok"
    return "empty" if corpus_url.rstrip("/").endswith("/.html") else "identifier form"


def series_of(ogham_id: str) -> str:
    m = SERIES_RE.match(ogham_id or "")
    return m.group(1) if m else ""


def _row(rec: dict) -> dict:
    place = (rec.get("pn_townland") or rec.get("pn_parish") or rec.get("pn_site")
             or rec.get("pn_graveyard") or "")
    return {
        "id": rec.get("ogham_id", ""),
        "series": series_of(rec.get("ogham_id", "")),
        "ciic": rec.get("ciic", ""),
        "cisp": rec.get("cisp", ""),
        "cisp_url": cisp_link(rec.get("cisp", ""), rec.get("cisp_url", "")),
        "cisp_url_raw": rec.get("cisp_url", ""),
        "cisp_url_state": cisp_url_state(rec.get("cisp", ""), rec.get("cisp_url", "")),
        "title": rec.get("title", ""),
        "county": rec.get("pn_county") or rec.get("pn_country", ""),
        "place": place,
        "keeper": rec.get("repository", ""),
        "geo_raw": (rec.get("geo_raw") or "").strip(),
        "gazetteer": rec.get("gazetteer_uris", ""),
        "status": rec.get("geo_status", ""),
    }


def _table(rows: list[dict], show_geo: bool = False) -> list[str]:
    if not rows:
        return ["_none_\n"]
    head = "| stone | CIIC | CISP | townland / parish | county | held by |"
    rule = "|---|---|---|---|---|---|"
    if show_geo:
        head += " what the edition says |"
        rule += "---|"
    out = [head, rule]
    for r in rows:
        cisp = f"[{r['cisp']}]({r['cisp_url']})" if r["cisp"] and r["cisp_url"] else (r["cisp"] or "—")
        line = (f"| `{r['id']}` | {r['ciic'] or '—'} | {cisp} | {r['place'] or '—'} | "
                f"{r['county'] or '—'} | {r['keeper'] or '—'} |")
        if show_geo:
            said = f"`{r['geo_raw']}`" if r["geo_raw"] else "_empty_"
            if r["geo_raw"] and SETTLED_RE.search(r["geo_raw"]):
                said += " — **stated as not recoverable**"
            line += f" {said} |"
        out.append(line)
    out.append("")
    return out


def build(place_records: list[dict], word_records: list[dict], path: Path) -> dict:
    rows = [_row(r) for r in place_records]
    by_id = {r["id"]: r for r in rows}

    no_geo = [r for r in rows if r["status"] in ("missing", "textual_only")]
    numbered = [r for r in no_geo if r["series"] == ""]
    lost = [r for r in no_geo if r["series"] == "L"]
    doubtful = [r for r in no_geo if r["series"] == "X"]
    hedged = [r for r in rows if r["status"] == "qualified"]
    no_text = [by_id[r["ogham_id"]] for r in word_records
               if not r["readings"] and r["ogham_id"] in by_id]

    L: list[str] = []
    add = L.append
    add("# Worklist — where the corpus can be enhanced\n")
    add("> **Generated** by `python py/main.py`. Every gap the pipeline can see, "
        "ordered by what a fix is worth. Fill findspot coordinates through "
        "`reconciliation/findspot-overrides.csv`, which records the source alongside "
        "the value and is applied only where the edition says nothing.\n")

    add("## How to read the identifiers\n")
    add("OG(H)AM's numbering carries a distinction worth keeping:\n")
    add("| series | example | meaning |")
    add("|---|---|---|")
    add("| numbered | `I-KER-042` | extant and catalogued |")
    add("| `L` | `I-KER-L02` | **lost** — *\"broken up for building material, no record "
        "of its inscription was preserved\"* (Macalister 1945). The stone is gone; its "
        "findspot may still be recorded. |")
    add("| `X` | `I-KER-X01` | **doubtful** — often *\"findspot uncertain\"* in the "
        "edition itself, sometimes not accepted as ogham at all. |")
    add("")
    add("Supplying a coordinate for a numbered stone completes a record. Supplying one "
        "for an `X` stone may assert a precision the evidence does not carry, which is "
        "the opposite of the point. The tiers below follow that.\n")

    add(f"## 1. Extant stones with no findspot — {len(numbered)}\n")
    add("The highest-value gaps: catalogued, in the ground or in a museum, and simply "
        "missing a coordinate. CISP records a grid reference for many of them.\n")
    L.extend(_table(numbered, show_geo=True))

    add(f"## 2. Coordinates the editors hedged — {len(hedged)}\n")
    add("These are on the map already, drawn as dashed rings. A better source may turn "
        "a hedge into an assertion — or confirm that the hedge is right, which is worth "
        "recording too.\n")
    L.extend(_table(hedged, show_geo=True))

    add(f"## 3. Lost stones — {len(lost)}\n")
    add("The stone is gone, but Macalister and the antiquarian record often name the "
        "field. A findspot for a lost stone is a real datum: it is where ogham *was*.\n")
    L.extend(_table(lost, show_geo=True))

    add(f"## 4. Doubtful stones — {len(doubtful)}\n")
    add("Lowest priority, and the one place where **not** filling the gap may be the "
        "right answer. Several say *findspot uncertain* in the edition; that is a "
        "finding, not an omission.\n")
    L.extend(_table(doubtful, show_geo=True))

    add(f"## 5. Editions with no text at all — {len(no_text)}\n")
    add("No transcription in any reading, so these stones are invisible to the "
        "formulaic-word and disagreement layers. Where Macalister prints a reading, "
        "adding it as an `<app>/<rdg>` would bring the stone into both.\n")
    L.extend(_table(no_text))

    broken = [r for r in rows if r["cisp_url_state"] in ("identifier form", "empty")]
    by_state = {}
    for r in broken:
        by_state.setdefault(r["cisp_url_state"], []).append(r)
    add(f"## 6. CISP links that do not resolve — {len(broken)}\n")
    add("Not a research task but a corpus fix. CISP publishes a stone at "
        "`.../stone/wvale_1.html`; the `corresp` on `<idno type=\"CISP\">` often carries "
        "the *identifier* form instead, or nothing at all.\n")
    add("| form in the corpus | stones | example | what resolves |")
    add("|---|---|---|---|")
    for state, group in sorted(by_state.items()):
        ex = group[0]
        shown = ex["cisp_url_raw"].rsplit("/stone/", 1)[-1] or "(empty)"
        fixed = ex["cisp_url"].rsplit("/stone/", 1)[-1] if ex["cisp_url"] else "—"
        add(f"| {state} | {len(group)} | `{shown}` | `{fixed}` |")
    add("")
    add("The identifier-form ones convert mechanically — lowercase, and `/` becomes `_` "
        "— so the links in this worklist are already repaired. The empty ones have no "
        "CISP identifier in the edition either, so they need one before a link can "
        "exist.\n")

    counts = {
        "numbered_without_findspot": len(numbered),
        "hedged": len(hedged),
        "lost_without_findspot": len(lost),
        "doubtful_without_findspot": len(doubtful),
        "without_edition_text": len(no_text),
        "broken_cisp_links": len(broken),
    }
    add("## Summary\n")
    add("| gap | stones |")
    add("|---|---|")
    for key, n in counts.items():
        add(f"| {key.replace('_', ' ')} | {n} |")
    add("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return counts


def write_csv(place_records: list[dict], word_records: list[dict], path: Path) -> int:
    """The same gaps as a table, for working through offline."""
    rows = [_row(r) for r in place_records]
    by_id = {r["id"]: r for r in rows}
    no_text = {r["ogham_id"] for r in word_records if not r["readings"]}
    out = []
    for r in rows:
        gaps = []
        if r["status"] in ("missing", "textual_only"):
            gaps.append("findspot")
        elif r["status"] == "qualified":
            gaps.append("findspot hedged")
        if r["id"] in no_text:
            gaps.append("no edition text")
        if not gaps:
            continue
        kind, why = SERIES.get(r["series"], ("numbered", ""))
        out.append({**r, "series_label": kind, "series_note": why, "gaps": "; ".join(gaps)})
    fields = ["id", "series", "series_label", "series_note", "gaps", "ciic", "cisp",
              "cisp_url", "cisp_url_state", "title", "place", "county", "keeper",
              "geo_raw", "gazetteer", "status"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(out, key=lambda r: (r["series"], r["county"], r["id"])))
    return len(out)
