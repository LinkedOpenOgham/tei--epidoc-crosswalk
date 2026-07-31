# Reference ontologies

Local copies, so the pipeline can check what it emits without a network call and
without anyone having to remember which version was meant.

`upstream/` holds the files exactly as published and is never edited.
`ogham.ttl` is generated from `upstream/ogham.owl` by `py/ontology_patch.py`, which
corrects it and adds the properties this crosswalk needs; `CHANGES.md` says what
changed and why. Both are rewritten on every run, so a new upstream release can be
dropped into `upstream/` and the patch replayed.

| file | what | namespace |
|---|---|---|
| `upstream/ogham.owl` | the Linked Open Ogham ontology, as published | `http://ontology.ogham.link/` |
| `ogham.ttl` | the same, corrected and extended (generated) | `http://ontology.ogham.link/` |
| `CIDOC_CRM_v7.1.3.rdf` | CIDOC CRM 7.1.3 | `http://www.cidoc-crm.org/cidoc-crm/` |
| `CRMtex_v2.0.rdf` | CRMtex 2.0 | `http://www.cidoc-crm.org/extensions/crmtex/` |
| `amt.ttl`, `amt-shapes.ttl` | the Academic Meta Tool vocabulary and its shapes | `http://academic-meta-tool.xyz/vocab#` |

`py/validate.py` reads them to check every class and property the crosswalk emits:
that the term exists, and that its subject and object are of the declared domain
and range. Before this, `crosswalk SHACL: VALID` meant twelve class declarations
had been checked and the twenty thousand triples in `out/` had not.

Note the CRMtex namespace: **`/extensions/crmtex/`**, not `/cidoc-crm/crmtex/`.
