#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""words.py -- formulaic words and name elements in the ogham editions.

Picks up where the DHd 2020 poster left off. `o3d-epidoc-extractor`
(Homburg & Thiery) matched McManus's formulaic vocabulary against the
*Ogham in 3D* database and mapped the hits; this module does the same against
the TEI/EpiDoc editions of OG(H)AM, the successor project — and adds the thing
the earlier version could not do, because its source had one reading per stone:

**every reading is scanned separately.** A stone whose current edition reads
CASSITTAS MAQI MUCOI CALLITI and whose 1945 reading did not have MUCOI is not a
stone that "has MUCOI"; it is a stone where one editor saw MUCOI and another did
not. The word occurrences therefore hang off the `crmtex:TX6_Transcription`
nodes the crosswalk already mints, not off the stone.

The word list (`data/words.csv`) is taken unchanged from the earlier project,
MIT-licensed, © Timo Homburg and Florian Thiery. Its three classes drive three
matching modes:

  formula word   (Q67381377)  ANM, MAQI, MUCOI …    whole token
  name element   (Q67382150)  CUNA, ERC, CATTU …    substring of a token
  compound name  (Q79401991)  DERCMASOC, CUNAMAGLI  whole token

Substring matching is the earlier project's semantics and is deliberately kept,
but it is not precise: short elements such as CON, VIR or DOV will also fire
inside unrelated names. Matches carry their mode so a reader can tell which kind
of claim they are looking at.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

from lxml import etree
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

TEI = "http://www.tei-c.org/ns/1.0"
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
# CRMtex lives under /extensions/, not under /cidoc-crm/. With the wrong base
# every TX URI in the graph pointed at nothing that exists.
CRMTEX = Namespace("http://www.cidoc-crm.org/extensions/crmtex/")
OGHAM = Namespace("http://ontology.ogham.link/")
DATA_NS = Namespace("http://data.ogham.link/crm/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
AMT = Namespace("http://academic-meta-tool.xyz/vocab#")
PROV = Namespace("http://www.w3.org/ns/prov#")
WD = Namespace("http://www.wikidata.org/entity/")

WORDS_URL = ("https://raw.githubusercontent.com/LinkedOpenOgham/"
             "o3d-epidoc-extractor/master/words/words.csv")

CLASSES = {
    "http://www.wikidata.org/entity/Q67381377": ("formula", "formula word"),
    "http://www.wikidata.org/entity/Q67382150": ("element", "name element"),
    "http://www.wikidata.org/entity/Q79401991": ("compound", "compound name"),
}

# Brackets and strokes are editorial scaffolding *around* letters that are part of
# the reading: C[A]TTINI is CATTINI, MAQQ[/I] is MAQQI. They are removed and the
# letters kept. Everything else that is not a letter becomes a word boundary.
TRANSPARENT = str.maketrans("", "", "[](){}⸢⸣〚〛/\\")
# Parenthesised asides in an otherwise upper-case transliteration are editorial,
# not text: "(vac.)", "(MAC1945: …)". Dropping them stops MAC1945 being read as
# the MAQI variant MAC.
ASIDE_RE = re.compile(r"\([^)]*[a-z0-9][^)]*\)")
# the same aside left unclosed at the end of the field, which the corpus also has
ASIDE_OPEN_RE = re.compile(r"\([^)]*[a-z0-9][^)]*$")
ROMAN_RE = re.compile(r";?\s*\bRoman\b\s*:.*$", re.I)
# "vac." often follows a letter directly (CCICAMINIvac.), so no leading boundary
VACAT_RE = re.compile(r"vacat\b|vac\.", re.I)


def normalise(text: str) -> str:
    """Editorial transliteration -> plain upper-case letters and spaces."""
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")  # dots below
    text = ROMAN_RE.sub(" ", text)          # a trailing Roman-script transcript
    text = ASIDE_RE.sub(" ", text)
    text = ASIDE_OPEN_RE.sub(" ", text)
    text = VACAT_RE.sub(" ", text)
    text = text.translate(TRANSPARENT)
    text = re.sub(r"[^A-Za-z]+", " ", text)
    return re.sub(r"\s+", " ", text).strip().upper()


def fetch_word_list(path: Path) -> Path:
    """Download the word list from the earlier project if it is not committed."""
    import urllib.request
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"fetching the word list from {WORDS_URL}")
    with urllib.request.urlopen(WORDS_URL, timeout=60) as fh:
        path.write_bytes(fh.read())
    return path


def load_words(path: Path) -> list[dict]:
    """The word list, one entry per (word, class) pair -- ERC is listed twice."""
    out = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            word = (row.get("word") or "").strip().upper()
            mode, mode_label = CLASSES.get((row.get("type") or "").strip(),
                                           ("compound", "compound name"))
            variants = [v.strip().upper() for v in
                        (row.get("variants") or "").strip().strip("[]").split("|") if v.strip()]
            if not word:
                continue
            out.append({
                "word": word,
                "mode": mode,
                "mode_label": mode_label,
                "variants": variants or [word],
                "translation": (row.get("translation") or "").strip().strip('"'),
                "reference": (row.get("ref") or "").strip().strip('"'),
                "wikidata": (row.get("wikidata") or "").strip(),
                "class_qid": (row.get("type") or "").strip(),
            })
    # longest variants first, so CUNAS is reported rather than CUNA where both fit
    for entry in out:
        entry["variants"].sort(key=len, reverse=True)
    return out


def find(text: str, words: list[dict]) -> list[dict]:
    """Matches in one normalised reading, de-duplicated per (word, variant)."""
    tokens = text.split()
    hits: dict[tuple, dict] = {}
    for entry in words:
        for variant in entry["variants"]:
            for token in tokens:
                matched = token == variant if entry["mode"] != "element" else variant in token
                if not matched:
                    continue
                key = (entry["word"], entry["mode"], variant)
                hits.setdefault(key, {
                    "word": entry["word"], "mode": entry["mode"], "variant": variant,
                    "token": token, "translation": entry["translation"],
                    "wikidata": entry["wikidata"], "reference": entry["reference"],
                })
                break
    return list(hits.values())


# --- reading extraction -------------------------------------------------------

EDITOR_PREFIXES = {"RHY": "Rhys", "MAC": "Macalister", "DIA": "Diack",
                   "JAC": "Jackson", "FOR": "Forsyth", "OKA": "O\u2019Kelly",
                   "BRA": "Brash", "MCM": "McManus", "PAD": "Padel", "WES": "West",
                   "BRO": "Broderick", "SHE": "Shee", "CLA": "Clarke",
                   "FUL": "Fulford", "JOH": "Johnson"}

# The apparatus attributes a reading in one of two ways: @source on the <rdg>, or
# prose in the <app>'s <note> -- "Macalister (1945, 469) read:". Only 53% of
# readings carry @source, so the note has to be parsed as well; otherwise half the
# corpus's competing readings end up anonymous.
ATTRIB_RE = re.compile(r"([A-Z][\w\u2019'\-]+(?:\s+[A-Z][\w\u2019'\-]+)*?)\s*\((\d{4})")
# <rdg>Ogham: LA[TI]NI</rdg> -- the script of the reading, not part of the text
SCRIPT_RE = re.compile(r"^\s*(Ogham|Roman|Latin)\s*:\s*", re.I)


def editor_label(source_id: str) -> str:
    """Human label for a @source id such as MAC1945. Empty for an unknown source --
    an unattributed reading must not be mistaken for the current edition."""
    m = re.match(r"([A-Za-z]+)(\d{4})", source_id or "")
    if not m:
        return ""
    return f"{EDITOR_PREFIXES.get(m.group(1).upper(), m.group(1).title())} {m.group(2)}"


def attribution_from_note(note_text: str) -> str:
    """'Macalister (1945, 469) read:' -> 'Macalister 1945'."""
    m = ATTRIB_RE.search(note_text or "")
    if not m:
        return ""
    name = m.group(1).rstrip().removesuffix("\u2019s").removesuffix("'s").strip()
    surname = name.split()[-1] if name else ""
    return f"{surname} {m.group(2)}".strip()


def _text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def _split_script(text: str) -> tuple[str, str]:
    m = SCRIPT_RE.match(text or "")
    return (m.group(1).lower(), text[m.end():].strip()) if m else ("ogham", text)


def readings_of(tree) -> list[dict]:
    """Current edition plus every competing <rdg>, in that order.

    Two things the encoding makes necessary. Most <app> elements (305 of 434) hold
    only a <note> -- an editorial remark, not a rival reading -- and must not be
    counted. And where a <rdg> has no @source, the attribution sits in that note,
    so it is parsed from there.
    """
    out = []
    div = tree.find(f".//{{{TEI}}}div[@type='edition'][@subtype='transliteration']")
    if div is None:
        div = tree.find(f".//{{{TEI}}}div[@type='edition']")
    if div is not None:
        ab = div.findall(f".//{{{TEI}}}ab")
        text = _text(ab[-1]) if ab else _text(div)
        if text:
            resp = (div.get("resp") or "").lstrip("#") or "OGHAM"
            script, text = _split_script(text)
            out.append({"id": f"OGHAM_{resp}", "editor": f"OG(H)AM edition ({resp})",
                        "text": text, "script": script, "current": True})

    seen = set()
    for app in tree.findall(f".//{{{TEI}}}app"):
        note = app.find(f"{{{TEI}}}note")
        from_note = attribution_from_note(_text(note)) if note is not None else ""
        for rdg in app.findall(f"{{{TEI}}}rdg"):
            seen.add(rdg)
            src = (rdg.get("source") or rdg.get("resp") or "").lstrip("#")
            text = _text(rdg)
            if not text:
                continue
            script, text = _split_script(text)
            out.append({"id": src or from_note or "unattributed",
                        "editor": editor_label(src) or from_note or "unattributed reading",
                        "text": text, "script": script, "current": False})
    for rdg in tree.findall(f".//{{{TEI}}}rdg"):      # any <rdg> outside an <app>
        if rdg in seen:
            continue
        src = (rdg.get("source") or rdg.get("resp") or "").lstrip("#")
        text = _text(rdg)
        if not text:
            continue
        script, text = _split_script(text)
        out.append({"id": src or "unattributed",
                    "editor": editor_label(src) or "unattributed reading",
                    "text": text, "script": script, "current": False})
    return out


def scan(files, words: list[dict], parse_xml, stone_key, is_edition) -> list[dict]:
    """One record per edition, with its readings and their word matches."""
    records = []
    for path in files:
        tree = parse_xml(path)
        if tree is None:
            continue
        idnos = {}
        for i in tree.findall(f".//{{{TEI}}}idno[@type]"):
            value = (i.text or "").strip()
            if value:
                idnos.setdefault(i.get("type"), value)
        ogham_id = idnos.get("filename", path.stem)
        if not is_edition({"ogham_id": ogham_id}):
            continue
        readings = []
        for r in readings_of(tree):
            normalised = normalise(r["text"])
            readings.append({**r, "normalised": normalised,
                             "matches": find(normalised, words)})
        records.append({
            "file": path.name,
            "ogham_id": ogham_id,
            "stone_key": stone_key(idnos),
            "title": _text(tree.find(f".//{{{TEI}}}title")),
            "ciic": idnos.get("CIIC", ""),
            "readings": readings,
        })
    return records


# --- outputs ------------------------------------------------------------------

CSV_FIELDS = ["ogham_id", "ciic", "title", "reading_id", "editor", "script", "is_current_edition",
              "word", "mode", "variant", "token", "translation", "wikidata",
              "reference", "reading_text"]


def write_csv(records: list[dict], path: Path) -> int:
    rows = []
    for rec in records:
        for r in rec["readings"]:
            for m in r["matches"]:
                rows.append({
                    "ogham_id": rec["ogham_id"], "ciic": rec["ciic"], "title": rec["title"],
                    "reading_id": r["id"], "editor": r["editor"], "script": r.get("script", ""),
                    "is_current_edition": "yes" if r["current"] else "no",
                    "word": m["word"], "mode": m["mode"], "variant": m["variant"],
                    "token": m["token"], "translation": m["translation"],
                    "wikidata": m["wikidata"], "reference": m["reference"],
                    "reading_text": r["text"],
                })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text or "").strip("_") or "x"


def build_graph(records: list[dict], words: list[dict]) -> tuple[Graph, dict]:
    """Word occurrences as CRMtex segments of the reading that carries them."""
    g = Graph()
    for pfx, ns in (("crm", CRM), ("crmtex", CRMTEX), ("ogham", OGHAM), ("data", DATA_NS),
                    ("skos", SKOS), ("amt", AMT), ("prov", PROV), ("wd", WD),
                    ("rdfs", RDFS), ("xsd", XSD)):
        g.bind(pfx, ns)

    # the vocabulary itself, once
    for entry in words:
        node = DATA_NS[f"word_{_slug(entry['word'])}_{entry['mode']}"]
        g.add((node, RDF.type, CRM["E55_Type"]))
        g.add((node, RDF.type, {"formula": OGHAM.FormulaWord,
                                "element": OGHAM.NomenclatureWord}.get(
                                   entry["mode"], OGHAM.Word)))
        g.add((node, RDFS.label, Literal(entry["word"])))
        g.add((node, OGHAM.wordClass, Literal(entry["mode_label"])))
        if entry["translation"]:
            g.add((node, OGHAM.translation, Literal(entry["translation"])))
            g.add((node, SKOS.definition, Literal(entry["translation"], lang="en")))
        if entry["reference"]:
            g.add((node, OGHAM.reference, Literal(entry["reference"])))
        for variant in entry["variants"]:
            g.add((node, SKOS.altLabel, Literal(variant)))
        if entry["wikidata"].startswith("http"):
            target = URIRef(entry["wikidata"].replace("https://www.wikidata.org/wiki/",
                                                      "http://www.wikidata.org/entity/"))
            g.add((node, SKOS.closeMatch, target))
            st = DATA_NS[f"match_word_{_slug(entry['word'])}_{entry['mode']}"]
            g.add((st, RDF.type, RDF.Statement))
            g.add((st, RDF.subject, node))
            g.add((st, RDF.predicate, SKOS.closeMatch))
            g.add((st, RDF.object, target))
            g.add((st, AMT.weight, Literal("1.00", datatype=XSD.decimal)))
            g.add((st, OGHAM.matchStatus, Literal("source-asserted")))
            g.add((st, OGHAM.matchTypeCheck, Literal("curated")))

    occurrences = 0
    for rec in records:
        sid = _slug(rec["stone_key"])
        stone = DATA_NS[f"stone_{sid}"]
        inscription = DATA_NS[f"inscription_{sid}"]
        for r in rec["readings"]:
            if not r["matches"]:
                continue
            reading = DATA_NS[f"reading_{sid}_{_slug(r['id'] or r['text'])}"]
            # Only the ontology's own class. It declares ogham:Reading a subclass of
            # crmtex TX6_Transcription -- a class CRMtex 2.0 does not define, under a
            # namespace that is not CRMtex's -- but that axiom is ogham.owl's to fix.
            # Asserting a CRMtex type here would either duplicate it or contradict it.
            g.add((reading, RDF.type, OGHAM.Reading))
            g.add((reading, RDFS.label, Literal(r["text"])))
            if r.get("script"):
                g.add((reading, OGHAM.script, Literal(r["script"])))
            # ogham:identifiedAs is declared a sub-property of TXP4_has_segment with
            # exactly this domain and range, so the ontology has already made the call
            g.add((inscription, OGHAM.identifiedAs, reading))
            g.add((stone, OGHAM.carries, inscription))
            agent = DATA_NS[f"agent_{_slug(r['id'])}"]
            g.add((agent, RDF.type, PROV.Agent))
            g.add((agent, RDFS.label, Literal(r["editor"])))
            g.add((reading, PROV.wasAttributedTo, agent))
            for m in r["matches"]:
                occ = DATA_NS[f"word_occ_{sid}_{_slug(r['id'])}_{_slug(m['word'])}_{m['mode']}"]
                # the ontology subclasses Word into exactly the two kinds the word
                # list distinguishes, so the mode becomes a class rather than a label
                g.add((occ, RDF.type, {"formula": OGHAM.FormulaWord,
                                       "element": OGHAM.NomenclatureWord}.get(
                                          m["mode"], OGHAM.Word)))
                g.add((occ, RDFS.label, Literal(m["token"])))
                g.add((occ, CRM["P2_has_type"],
                       DATA_NS[f"word_{_slug(m['word'])}_{m['mode']}"]))
                g.add((occ, OGHAM.matchedVariant, Literal(m["variant"])))
                g.add((occ, OGHAM.matchMode, Literal(m["mode"])))
                g.add((stone, OGHAM.shows, occ))
                occurrences += 1

    return g, {"words": len(words), "occurrences": occurrences,
               "stones": sum(1 for r in records
                             if any(x["matches"] for x in r["readings"]))}
