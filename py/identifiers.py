#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""identifiers.py -- the one file a human edits.

``reconciliation/identifiers.yaml`` holds every identifier and coordinate that has
been decided by hand: Wikidata QIDs, OSM object ids, coordinates typed from a
source, and the aliases that merge two names for one place. **The pipeline never
writes it.**

That separation is the point. ``keeper-coordinates.csv`` is a cache: machine
output, rewritten on every run, safe to delete. Before this file existed, hand
decisions lived in that same cache, which meant they sat one ``--regeocode`` away
from being reformatted, reordered, or lost, and nothing distinguished a value a
person had checked from one a search had guessed.

Now the flow is one-way. Hand values are read from here and applied over whatever
the machine found, on every run. Delete the cache and nothing is lost; the next run
rebuilds it and re-applies these.

Keys are what the corpus itself says, so they can be looked up:

    keepers      the exact <repository> string
    findspots    the OG(H)AM edition id

Unknown keys are reported rather than ignored, because a repository string with a
typo in it would otherwise fail silently -- the commonest way for a curated file to
rot.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

QID_RE = re.compile(r"^Q\d+$")
OSM_RE = re.compile(r"^(way|node|relation)/\d+$")
SECTIONS = ("keepers", "findspots")

TEMPLATE = """\
# Identifiers and coordinates decided by hand. THE PIPELINE NEVER WRITES THIS FILE.
#
# Everything here is applied over whatever the automatic lookup found, on every
# run. reconciliation/keeper-coordinates.csv is only a cache -- delete it and this
# file rebuilds the decisions.
#
# Per entry, any of:
#   qid:      Wikidata item, e.g. Q140775537. Resolved directly via P625; no search.
#   osm_id:   OSM object, e.g. way/407744946. Resolved via Nominatim, then the OSM API.
#   lat/lon:  a coordinate typed from a source. Wins over both of the above.
#   alias_of: another key naming the same place; merges the two (keepers only).
#   source:   where the value came from. Say it, even briefly.
#   note:     anything the next person needs, including what you ruled out.
#
# Precedence: lat/lon > qid > osm_id > automatic lookup.

# Institutions named in <msIdentifier>/<repository>. The key is that exact string.
keepers: {}

# Findspots the edition leaves empty. The key is the OG(H)AM edition id.
findspots: {}
"""


def path_or_create(path: Path) -> Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(TEMPLATE, encoding="utf-8")
    return path


def load(path: Path) -> dict:
    if not path.exists():
        return {s: {} for s in SECTIONS}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        print(f"  ! {path.name} is unreadable ({exc}); no hand-set identifiers applied")
        return {s: {} for s in SECTIONS}
    return {s: (data.get(s) or {}) for s in SECTIONS}


def validate(entries: dict, known: dict[str, set[str]]) -> list[str]:
    """Complaints about the file, in the order a reader would want them."""
    problems = []
    for section in SECTIONS:
        for key, value in (entries.get(section) or {}).items():
            where = f"{section}: {key!r}"
            if not isinstance(value, dict):
                problems.append(f"{where} -- expected a mapping, got {type(value).__name__}")
                continue
            if known.get(section) and key not in known[section]:
                problems.append(f"{where} -- no such {section[:-1]} in the corpus; "
                                f"check the spelling, this entry does nothing")
            qid = str(value.get("qid") or "")
            if qid and not QID_RE.match(qid):
                problems.append(f"{where} -- {qid!r} is not a QID (expected Q followed by digits)")
            osm = str(value.get("osm_id") or "")
            if osm and not OSM_RE.match(osm):
                problems.append(f"{where} -- {osm!r} is not an OSM id "
                                f"(expected way/…, node/… or relation/…)")
            has_lat, has_lon = value.get("lat") is not None, value.get("lon") is not None
            if has_lat != has_lon:
                problems.append(f"{where} -- lat and lon must be given together")
            if has_lat:
                try:
                    lat, lon = float(value["lat"]), float(value["lon"])
                    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                        problems.append(f"{where} -- {lat}, {lon} is not a coordinate on earth")
                except (TypeError, ValueError):
                    problems.append(f"{where} -- lat/lon are not numbers")
            unknown = set(value) - {"qid", "osm_id", "lat", "lon", "alias_of", "source",
                                    "note", "status"}
            if unknown:
                problems.append(f"{where} -- ignored key(s): {', '.join(sorted(unknown))}")
    return problems


SUGGEST_HEADER = """\
# Identifiers the automatic lookup found, for review. GENERATED -- rewritten on
# every run, safe to delete.
#
# Each entry is an institution whose coordinate currently comes from a *search*.
# The search also names the object it matched, and that identifier is worth more
# than the coordinate: paste the entry into reconciliation/identifiers.yaml and the
# question stops being re-asked. From then on the run fetches that object's current
# coordinate directly -- one call, no searching, and no chance of landing somewhere
# else because a name was ambiguous.
#
# Check the coordinate in the comment before promoting an entry. A search result is
# a guess until someone has looked at it.

"""


def write_suggestions(path: Path, rows: list[tuple[str, dict, str]]) -> int:
    """Machine-found identifiers, in the shape identifiers.yaml expects.

    Written as a separate file rather than merged: identifiers.yaml is the one
    thing here a person owns, and a generator that rewrites it would take away the
    comments and ordering that make it readable.
    """
    lines = [SUGGEST_HEADER.rstrip(), ""]
    if not rows:
        lines.append("keepers: {}")
    else:
        lines.append("keepers:")
        for key, fields, comment in rows:
            lines.append(f"  # {comment}")
            block = yaml.safe_dump({key: fields}, allow_unicode=True, sort_keys=True,
                                   default_flow_style=False, width=88).rstrip()
            lines.extend("  " + line for line in block.splitlines())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(rows)


def summarise(entries: dict) -> str:
    bits = []
    for section in SECTIONS:
        rows = entries.get(section) or {}
        if rows:
            bits.append(f"{len(rows)} {section}")
    return ", ".join(bits) if bits else "none"
