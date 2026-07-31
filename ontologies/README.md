# Reference ontologies

Local copies, so the pipeline can check what it emits without a network call and
without anyone having to remember which version was meant.

| file | what | namespace |
|---|---|---|
| `ogham.owl` | the Linked Open Ogham ontology | `http://ontology.ogham.link/` |
| `CIDOC_CRM_v7.1.3.rdf` | CIDOC CRM 7.1.3 | `http://www.cidoc-crm.org/cidoc-crm/` |
| `CRMtex_v2.0.rdf` | CRMtex 2.0 | `http://www.cidoc-crm.org/extensions/crmtex/` |
| `amt.ttl`, `amt-shapes.ttl` | the Academic Meta Tool vocabulary and its shapes | `http://academic-meta-tool.xyz/vocab#` |

`py/validate.py` reads them to check every class and property the crosswalk emits:
that the term exists, and that its subject and object are of the declared domain
and range. Before this, `crosswalk SHACL: VALID` meant twelve class declarations
had been checked and the twenty thousand triples in `out/` had not.

Note the CRMtex namespace: **`/extensions/crmtex/`**, not `/cidoc-crm/crmtex/`.
