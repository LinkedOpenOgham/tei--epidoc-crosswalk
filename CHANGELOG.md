# Changelog

All notable changes to this repository. Dates are release dates. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.2] - 2026-11-01

Moves the corpus from `bb62ccd` (2026-07-02) to `9a68afd` (2026-10-29): 41 upstream commits, two new
editions (`I-KIK-015`, `I-WAT-046`) and 13 changed ones. The code is unchanged.

### Changed
- Stones in the place layer: 504 to 506 (393 distinct places, 148 gazetteer links); findspot coordinates
  `asserted` 475 to 477.
- Word layer: 290 to 292 stones with a match, 673 to 677 occurrences.
- Person layer: 365 people, 35 kin groups, 119 relations in 99 groups.
- Setting layer: 214 out in the landscape (was 213), 59 indoors but visitable (was 58).
- `data/corpus-manifest.yaml`, `out/`, `docs/`, `element-docs/`. README figures brought up to date.

### Unchanged
- The seven per-stone graphs (none of their editions changed upstream) and the record-status and
  doubt-profile properties. The two new editions are `numbered`, so the status counts are 458 numbered,
  14 lost, 34 doubtful.

## [0.2.1] - 2026-11-01

Makes the build clock-free: two runs over the same corpus give the same bytes.

### Fixed
- `prov:generatedAtTime` in `out/places.crm.ttl` is the date of the corpus commit (`ogham:corpusCommitDate`),
  not the time of the run.
- The pages in `docs/` say "Built from the corpus state of <date of the corpus commit>" instead of
  "Generated <today>"; the landing page footer likewise.
- `ontologies/CHANGES.md` no longer carries a date.

### Added
- ORCID of the author in `CITATION.cff`.

### Unchanged
- Every triple apart from the one `prov:generatedAtTime` value. Tags: `v0.1.0` on `cff6341` (the state before
  the changelog), `v0.2.0` on `6ea33a9`.

### Known
- `element-docs/README.md` writes the corpus path with the separator of the operating system
  (`data\origin` on Windows, `data/origin` on Linux), so a build on another platform differs on that line.

## [0.2.0] - 2026-11-01

Takes in the three stones that the CAA UK 2026 poster ("Purported, Alleged, Undetermined: Four Degrees of
Doubt in the Ogham Corpus") needs and makes the status and the doubt markup of a stone queryable.

### Added
- Three stones in `data/` and in `STONES`: Dyke (`S-MOR-001`), Blackwaterfoot 1 (`S-BUT-001`) and
  Bishop Loch (`S-LKS-X01`), with `out/dyke.crm.ttl`, `out/blackwaterfoot-1.crm.ttl` and
  `out/bishop-loch.crm.ttl`. The base names are shared with `tei--epidoc-amt`.
- `ogham:recordStatus` on every stone (per-stone graphs and `places.crm.ttl`): `numbered`, `lost` (series L)
  or `doubtful` (series X), read from the identifier. Corpus-wide: 456 numbered, 14 lost, 34 doubtful.
  *Proposed term.*
- A doubt profile on every per-stone graph: `ogham:unclearCount`, `suppliedCount`, `gapCount`, `choiceCount`,
  `appCount`, `rdgCount`. Counted in the transliteration edition(s) and the apparatus only, never in the
  duplicate ogham-script edition. *Proposed terms.*
- `out/README.md`: section "Doubt markup per stone" with the counts, and a statement of the method's limit
  (Bishop Loch: the doubt about the status of the object is in prose only).
- `README.md`: section "Doubt, status and where the markup is blind".
- `PRIMER.md` (work plan, German), `CHANGELOG.md`, `CITATION.cff`.

### Fixed
- A `<rdg>` without `@source` was attributed to an invented shared agent (`data:agent_x`). It now has no
  `prov:wasAttributedTo`. Only Blackwaterfoot 1 was affected; the four earlier stones are unchanged.
- Readings are `ogham:Reading`, not `crmtex:TX6_Transcription`, throughout the documentation (README,
  generated `out/README.md`, docstrings). The code already did this; the text was stale. In the patched
  ontology `ogham:Reading` is a subclass of `crmtex:TX7_Written_Text_Segment`.
- The SPARQL example for competing readings used `crm:P128_carries` and `crmtex:TXP4_has_segment`, which the
  graph does not assert, and an alias in `HAVING`. It now uses `ogham:carries` and `ogham:identifiedAs`, and
  returns rows against `out/`.
- The generated README no longer says that no `<origDate>` occurs in the corpus (134 of 502 carry a value).
  They are still not mapped, see PRIMER D2.

### Unchanged
- Every triple of the four earlier stones, apart from the status and doubt-profile properties on each stone node. The place
  layer, keeper layer, word layer and the corpus state (`bb62ccd`, 504 editions) are as before.

## [0.1.0]

State before this changelog: four stones, crosswalk ontology and SHACL, place, keeper, word and reading
layers, GitHub Pages. Tagged `v0.1.0` retroactively on `cff6341`.
