#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""setting.py -- where a stone stands today, as far as the corpus says.

`<msIdentifier>/<repository>` answers one question: is it in an institution? For
the 322 stones where it is silent, the answer is not *unknown* — it is **not known
to be in an institution**, and `<provenance type="observed">` usually says a good
deal more:

    "In situ in pasture, on a gentle south facing slope"
    "Built into the wall of a summer house in the garden of Lancarffe House"
    "Still in place above the south window of the church at Knockboy"
    "Kept in a nearby modern enclosure with I-KER-118 and a boulder with rock art"

So the classification runs on two axes. The **custody** axis is coarse and mostly
reliable: in an institution, in the landscape, indoors but visitable, lost, or not
described. The **setting** axis is finer and is a reading of free prose, so every
verdict carries the sentence it was drawn from and how it was reached.

The rules were written against the corpus, not guessed at: they are ordered so that
the more specific claim wins, because *"Still in place above the south window of
the church"* is a stone built into a fabric, not a stone standing in a churchyard.

Nothing here is asserted more strongly than it is known. A stone with no observed
statement is `not described`, not `in situ`; `reconciliation/setting-overrides.csv`
is where a human verdict replaces a machine one.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

# (key, label, custody, colour, shape, rule)
# Ordered: the first rule that matches wins, so specific settings precede general
# ones. `None` as a rule means the category is decided by <repository>.
CATEGORIES = [
    ("lost", "lost or unlocated", "lost", "#b0413e", "circle",
     r"(no longer (?:visible|extant|to be seen|survives)|now missing|gone missing|"
     r"cannot be located|currently unlocated|is (?:now )?lost|^lost$|was lost|"
     r"subsequently lost|destroyed|broken up|whereabouts (?:are |is )?(?:now )?not known|"
     r"whereabouts (?:are |is )?(?:now )?unknown|nothing is now known|"
     r"present location .{0,20}not known|whereabouts .{0,14}not .{0,6}known|"
     r"no visible surface)"),

    ("institution", "museum or college", "institution", "#5b6f8c", "square", None),

    # A bare "conservation" appears in project credits -- it put the seven Knockboy
    # lintels, which are built into a church wall, in a conservation workshop.
    ("conservation", "in conservation", "institution", "#7a5c8e", "square",
     r"(for conservation|in conservation|conservator|conservation (?:workshop|studio|"
     r"laborator)|being conserved|undergoing conservation)"),

    ("church", "inside a church", "indoors", "#3f7d8c", "square",
     r"((?:in|inside|within|at)[^.]{0,40}\b(?:church|chapel|cathedral|capel|kirk|"
     r"priory|abbey)\b|nave|chancel|transept|church porch|house of crosses)"),

    ("visitor", "visitor or heritage centre", "indoors", "#6ba3a8", "square",
     r"(visitor'?s? centre|exhibition centre|heritage centre|interpretive centre|"
     r"geopark|victory hall|on display at)"),

    ("structure", "built into a structure", "landscape", "#b07d2b", "circle",
     r"(built into|incorporated into|re-?used in|set in(?:to)? |embedded in|"
     r"still in place above|attached to|souterrain|lintel|in the wall|wall of|"
     r"gable|bridge|stile|gate ?post|barrow|cashel|ringfort|\brath\b|holy well|"
     r"promontory fort|outbuilding|farmyard|farmhouse)"),

    ("enclosure", "in a protective enclosure", "landscape", "#9aab3f", "circle",
     r"(modern enclosure|small enclosure|own enclosure|nearby .{0,12}enclosure|"
     r"modern collection|enclosure surrounding|glass case|under cover)"),

    ("churchyard", "in a churchyard", "landscape", "#7fae7c", "circle",
     r"(churchyard|graveyard|cemetery|burial ground|killeen|kileen|lych-?gate|"
     r"ecclesiastical (?:site|enclosure))"),

    ("in_situ", "in situ or at the find site", "landscape", "#3f7a3d", "circle",
     r"(in situ|on site|at or close to find|still at the find|"
     r"(?:at|on) (?:the )?find ?s(?:ite|pot)|near find ?s(?:ite|pot)|pres\.? loc|"
     r"position in which it was discovered|where it was found|"
     r"in a field|in the field|in pasture|field fence|field boundary|in a hedge|"
     r"standing stone|still stands|now stands|remains standing|on a rock|outcrop|"
     r"dunes|on the hill|hillside|strand)"),

    ("grounds", "in private or institutional grounds", "landscape", "#8d9a97", "circle",
     r"(private possession|re-?erected|roadside|beside a .{0,12}road|by the road|"
     r"grass island|village green|garden|grounds of|demesne|estate|"
     r"house\b|hall\b|castle|school|college|col\u00e1iste|scoil|ollscoil|forecourt|lawn|"
     r"moved to|removed to|taken to|brought .{0,20}to|new premises)"),
]

RULES = [(k, lbl, cust, col, shp, re.compile(r, re.I) if r else None)
         for k, lbl, cust, col, shp, r in CATEGORIES]

UNDESCRIBED = ("undescribed", "setting not described", "undescribed", "#6d7b77", "circle")

CUSTODY_LABEL = {
    "institution": "in an institution",
    "indoors": "indoors, but visitable",
    "landscape": "out in the landscape",
    "lost": "lost or unlocated",
    "undescribed": "not described",
}

# The prose sometimes names an institution the repository field omits.
INSTITUTION_RE = re.compile(
    r"\b(museum|college|col\u00e1iste|library|institution|university|academy)\b", re.I)


def classify(repository: str, observed: str) -> dict:
    """Category for one stone, with the evidence and how it was reached."""
    text = (observed or "").strip()
    low = text.lower()

    for key, label, custody, colour, shape, rule in RULES:
        if key == "institution":
            if repository:
                return {"key": key, "label": label, "custody": custody,
                        "colour": colour, "shape": shape, "evidence": repository,
                        "method": "repository"}
            continue
        if rule and rule.search(low):
            m = rule.search(low)
            return {"key": key, "label": label, "custody": custody, "colour": colour,
                    "shape": shape, "evidence": text,
                    "method": f"matched \u201c{text[m.start():m.end()][:38]}\u201d"}

    if text and INSTITUTION_RE.search(text):
        # named in the prose but missing from <repository> -- reported, not silently
        # promoted, because the repository field is what the crosswalk models
        return {"key": "institution_unrecorded", "label": "institution named only in prose",
                "custody": "institution", "colour": "#5b6f8c", "shape": "square",
                "evidence": text, "method": "named in the observed statement, "
                                            "but <repository> is empty"}

    key, label, custody, colour, shape = UNDESCRIBED
    return {"key": key, "label": label, "custody": custody, "colour": colour,
            "shape": shape, "evidence": text, "method": "no rule matched" if text
            else "no observed statement in the edition"}


def load_overrides(path: Path) -> dict[str, dict]:
    if not path or not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return {r["ogham_id"]: r for r in csv.DictReader(fh)
                if r.get("ogham_id") and r.get("key")}


def apply(records: list[dict], observed: dict[str, str],
          overrides: dict[str, dict] | None = None) -> dict:
    """Classify every record in place. Returns counts by category and custody."""
    overrides = overrides or {}
    by_key: dict[str, int] = {}
    by_custody: dict[str, int] = {}
    lookup = {k: (lbl, cust, col, shp) for k, lbl, cust, col, shp, _ in RULES}
    lookup[UNDESCRIBED[0]] = UNDESCRIBED[1:]
    lookup["institution_unrecorded"] = ("institution named only in prose",
                                        "institution", "#5b6f8c", "square")
    for rec in records:
        oid = rec.get("ogham_id", "")
        verdict = classify(rec.get("repository", ""), observed.get(oid, ""))
        row = overrides.get(oid)
        if row and row["key"] in lookup:
            label, custody, colour, shape = lookup[row["key"]]
            verdict = {"key": row["key"], "label": label, "custody": custody,
                       "colour": colour, "shape": shape,
                       "evidence": row.get("note") or verdict["evidence"],
                       "method": "set by hand"}
        rec["setting"] = verdict
        by_key[verdict["key"]] = by_key.get(verdict["key"], 0) + 1
        by_custody[verdict["custody"]] = by_custody.get(verdict["custody"], 0) + 1
    return {"by_key": by_key, "by_custody": by_custody, "overrides": len(overrides)}


CSV_FIELDS = ["ogham_id", "ciic", "title", "county", "country", "custody", "category",
              "key", "method", "repository", "observed"]


def write_csv(records: list[dict], observed: dict[str, str], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        for rec in records:
            v = rec.get("setting")
            if not v:
                continue
            w.writerow({
                "ogham_id": rec.get("ogham_id", ""), "ciic": rec.get("ciic", ""),
                "title": rec.get("title", ""), "county": rec.get("pn_county", ""),
                "country": rec.get("pn_country", ""),
                "custody": CUSTODY_LABEL.get(v["custody"], v["custody"]),
                "category": v["label"], "key": v["key"], "method": v["method"],
                "repository": rec.get("repository", ""),
                "observed": observed.get(rec.get("ogham_id", ""), ""),
            })
    return sum(1 for r in records if r.get("setting"))
