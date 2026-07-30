# Worklist — where the corpus can be enhanced

> **Generated** by `python py/main.py`. Every gap the pipeline can see, ordered by what a fix is worth. Fill findspot coordinates through `reconciliation/findspot-overrides.csv`, which records the source alongside the value and is applied only where the edition says nothing.

## How to read the identifiers

OG(H)AM's numbering carries a distinction worth keeping:

| series | example | meaning |
|---|---|---|
| numbered | `I-KER-042` | extant and catalogued |
| `L` | `I-KER-L02` | **lost** — *"broken up for building material, no record of its inscription was preserved"* (Macalister 1945). The stone is gone; its findspot may still be recorded. |
| `X` | `I-KER-X01` | **doubtful** — often *"findspot uncertain"* in the edition itself, sometimes not accepted as ogham at all. |

Supplying a coordinate for a numbered stone completes a record. Supplying one for an `X` stone may assert a precision the evidence does not carry, which is the opposite of the point. The tiers below follow that.

## 1. Extant stones with no findspot — 5

The highest-value gaps: catalogued, in the ground or in a museum, and simply missing a coordinate. CISP records a grid reference for many of them.

| stone | CIIC | CISP | townland / parish | county | held by | what the edition says |
|---|---|---|---|---|---|---|
| `I-KER-042` | 174 | — | — | Co. Kerry | — | _empty_ |
| `I-KER-043` | 175 | [BRHAM/1](https://www.ucl.ac.uk/archaeology/cisp/database/stone/brham_1.html) | Burnham East | Co. Kerry | — | `(original provenance is unrecorded)` — **stated as not recoverable** |
| `I-KER-083` | 214 | [KLGOB/2](https://www.ucl.ac.uk/archaeology/cisp/database/stone/klgob_2.html) | Kilgobnet (Cill Ghobnait) | Co. Kerry | — | _empty_ |
| `I-KER-151` | — | — | BAILE MÓR THIAR | Co. Kerry | — | _empty_ |
| `I-KER-153` | — | — | — | Co. Kerry | — | _empty_ |

## 2. Coordinates the editors hedged — 6

These are on the map already, drawn as dashed rings. A better source may turn a hedge into an assertion — or confirm that the hedge is right, which is worth recording too.

| stone | CIIC | CISP | townland / parish | county | held by | what the edition says |
|---|---|---|---|---|---|---|
| `I-COR-009` | 61 | [BIISL/1](https://www.ucl.ac.uk/archaeology/cisp/database/stone/biisl_1.html) | Bishop’s Island | Co. Cork | University College Cork | `52.004, -8.358` |
| `I-COR-020` | 72 | [AUTAG/1](https://www.ucl.ac.uk/archaeology/cisp/database/stone/autag_1.html) | Aultagh | Co. Cork | — | `51.770030, -9.09023` |
| `I-KER-034` | 166 | [BLHER/1](https://www.ucl.ac.uk/archaeology/cisp/database/stone/blher_1.html) | Rathduff? Ballyandreen? | Co. Kerry | National Museum of Ireland | `52.168473 , -10.028213 (possible orig loc)` |
| `I-KER-084` | 214 | [KLGOB/1](https://www.ucl.ac.uk/archaeology/cisp/database/stone/klgob_1.html) | Kilgobnet (Cill Ghobnait) | Co. Kerry | — | `52.063009 , -9.722075 (possible original location)` |
| `I-KER-120` | 248 | [BAWGL/1](https://www.ucl.ac.uk/archaeology/cisp/database/stone/bawgl_1.html) | Bawnaglanna (Bán an Ghleanna) | Co. Kerry | — | `52.153985 , -9.443458 (approximate)` |
| `W-BRE-003` | 345 | [YFLL2/1](https://www.ucl.ac.uk/archaeology/cisp/database/stone/yfll2_1.html) | — | Brecknockshire | Cyfarthfa Museum | `51.809528, -3.553209` |

## 3. Lost stones — 7

The stone is gone, but Macalister and the antiquarian record often name the field. A findspot for a lost stone is a real datum: it is where ogham *was*.

| stone | CIIC | CISP | townland / parish | county | held by | what the edition says |
|---|---|---|---|---|---|---|
| `I-KER-L02` | — | — | — | Co. Kerry | — | _empty_ |
| `I-KER-L03` | — | — | Burnham East (Baile an Ghóilín) | Co. Kerry | — | _empty_ |
| `I-KER-L04` | — | — | Coolnagoppoge | Co. Kerry | — | _empty_ |
| `I-KER-L05` | 237 | — | Killurly (Cill Urlaí) | Co. Kerry | — | _empty_ |
| `I-KER-L06` | — | — | Loher (An Lóthar) | Co. Kerry | — | _empty_ |
| `I-KER-L07` | 242A | [PARAR/2](https://www.ucl.ac.uk/archaeology/cisp/database/stone/parar_2.html) | Parkavonear (Páirc an Mhóinéir) | Co. Kerry | — | _empty_ |
| `I-KER-L11` | — | — | Castleconway | Co. Kerry | — | _empty_ |

## 4. Doubtful stones — 10

Lowest priority, and the one place where **not** filling the gap may be the right answer. Several say *findspot uncertain* in the edition; that is a finding, not an omission.

| stone | CIIC | CISP | townland / parish | county | held by | what the edition says |
|---|---|---|---|---|---|---|
| `I-KER-X01` | — | — | Bushmount | Co. Kerry | — | `findspot uncertain` — **stated as not recoverable** |
| `I-KER-X02` | — | — | — | Co. Kerry | — | _empty_ |
| `I-KER-X03` | — | — | Clonsharagh | Co. Kerry | — | _empty_ |
| `I-KER-X04` | — | — | Gortacurraun | Co. Kerry | — | _empty_ |
| `I-KER-X05` | — | — | Vicarstown | Co. Kerry | — | _empty_ |
| `I-KER-X06` | — | — | Mangerton (An Mhangarta) | Co. Kerry | — | _empty_ |
| `I-KER-X07` | — | — | Derreen (An Doirín) | Co. Kerry | — | _empty_ |
| `I-KER-X08` | — | — | Laharan South (An Leathfhearann Theas) | Co. Kerry | — | _empty_ |
| `I-KER-X09` | — | — | Laharan South (An Leathfhearann Theas) | Co. Kerry | — | _empty_ |
| `W-PEM-X02` | 429 | [CLYDI/2](https://www.ucl.ac.uk/archaeology/cisp/database/stone/clydi_2.html) | Clydau | Pembrokeshire | — | `Coordinates unknown` — **stated as not recoverable** |

## 5. Editions with no text at all — 38

No transcription in any reading, so these stones are invisible to the formulaic-word and disagreement layers. Where Macalister prints a reading, adding it as an `<app>/<rdg>` would bring the stone into both.

| stone | CIIC | CISP | townland / parish | county | held by |
|---|---|---|---|---|---|
| `E-CON-X01` | — | [LWNCC/1](https://www.ucl.ac.uk/archaeology/cisp/database/stone/lwncc_1.html) | Lewannick | Cornwall | — |
| `E-DEV-X01` | — | — | Brendon | Devon | — |
| `E-STS-001` | — | — | Uttoxeter | Staffordshire | — |
| `I-COR-L11` | 78 | [COOLN/1](https://www.ucl.ac.uk/archaeology/cisp/database/stone/cooln_1.html) | Coolowen | Co. Cork | — |
| `I-FER-001` | 315 | [TMOUN/1](https://www.ucl.ac.uk/archaeology/cisp/database/stone/tmoun_1.html) | Topped Mountain (also Toppid Mountain) | Co. Fermanagh | Ulster Museum, Belfast |
| `I-FER-L01` | — | — | Drumnarullagh | Co. Fermanagh | — |
| `I-FER-X01` | — | — | Ballydoolaghh | Co. Fermanagh | National Museum of Ireland |
| `I-KER-042` | 174 | — | — | Co. Kerry | — |
| `I-KER-057` | 189 | [KINET/2](https://www.ucl.ac.uk/archaeology/cisp/database/stone/kinet_2.html) | Kinard East (Cinn Aird) | Co. Kerry | — |
| `I-KER-133` | 1085 | [RTHKE/3](https://www.ucl.ac.uk/archaeology/cisp/database/stone/rthke_3.html) | Rathkenny (Ráth Cionaoith) | Co. Kerry | — |
| `I-KER-145` | — | — | Tubrid Beg | Co. Kerry | — |
| `I-KER-149` | — | — | Kilmoyly South (Cill Mhaoile Theas) | Co. Kerry | — |
| `I-KER-150` | — | — | Fermoyle | Co. Kerry | Kerry County Museum |
| `I-KER-152` | — | — | Ballyvelly | Co. Kerry | — |
| `I-KER-L01` | 154A | [BALIG/8](https://www.ucl.ac.uk/archaeology/cisp/database/stone/balig_8.html) | Ballinrannig | Co. Kerry | — |
| `I-KER-L02` | — | — | — | Co. Kerry | — |
| `I-KER-L03` | — | — | Burnham East (Baile an Ghóilín) | Co. Kerry | — |
| `I-KER-L04` | — | — | Coolnagoppoge | Co. Kerry | — |
| `I-KER-L05` | 237 | — | Killurly (Cill Urlaí) | Co. Kerry | — |
| `I-KER-L06` | — | — | Loher (An Lóthar) | Co. Kerry | — |
| `I-KER-L09` | — | [RFILD/6](https://www.ucl.ac.uk/archaeology/cisp/database/stone/rfild_6.html) | Rockfield Middle (Gort na Cloiche Meánach) | Co. Kerry | — |
| `I-KER-L10` | — | — | Ardywanig (Ard Uí Mhánaigh) | Co. Kerry | — |
| `I-KER-L11` | — | — | Castleconway | Co. Kerry | — |
| `I-KER-X01` | — | — | Bushmount | Co. Kerry | — |
| `I-KER-X02` | — | — | — | Co. Kerry | — |
| `I-KER-X03` | — | — | Clonsharagh | Co. Kerry | — |
| `I-KER-X05` | — | — | Vicarstown | Co. Kerry | — |
| `I-KER-X06` | — | — | Mangerton (An Mhangarta) | Co. Kerry | — |
| `I-KER-X07` | — | — | Derreen (An Doirín) | Co. Kerry | — |
| `I-KER-X08` | — | — | Laharan South (An Leathfhearann Theas) | Co. Kerry | — |
| `I-KER-X09` | — | — | Laharan South (An Leathfhearann Theas) | Co. Kerry | — |
| `I-KER-X10` | — | — | Cahernead | Co. Kerry | — |
| `I-MAY-X02` | — | [KEELW/1](https://www.ucl.ac.uk/archaeology/cisp/database/stone/keelw_1.html) | Keel West | Co. Mayo | National Museum of Ireland |
| `S-DGY-001` | — | [LONAW/1](https://www.ucl.ac.uk/archaeology/cisp/database/stone/lonaw_1.html) | Leswalt | Dumfries and Galloway | Dumfries Museum |
| `S-ORK-X01` | — | — | Sanday | Orkney | Orkney Museum |
| `S-SHE-005` | — | [STNIN/2](http://www.ucl.ac.uk/archaeology/cisp/database/stone/stnin_2.html) | Dunrossness | Shetland | National Museums of Scotland |
| `S-SHE-006` | — | [STNIN/3](http://www.ucl.ac.uk/archaeology/cisp/database/stone/stnin_3.html) | Dunrossness | Shetland | National Museums of Scotland |
| `S-SHE-008` | — | [CBURG/3](http://www.ucl.ac.uk/archaeology/cisp/database/stone/cburg_3.html) | Dunrossness | Shetland | — |

## 6. CISP links that do not resolve — 200

Not a research task but a corpus fix. CISP publishes a stone at `.../stone/wvale_1.html`; the `corresp` on `<idno type="CISP">` often carries the *identifier* form instead, or nothing at all.

| form in the corpus | stones | example | what resolves |
|---|---|---|---|
| empty | 40 | `.html` | `—` |
| identifier form | 160 | `TMINE/1.html` | `tmine_1.html` |

The identifier-form ones convert mechanically — lowercase, and `/` becomes `_` — so the links in this worklist are already repaired. The empty ones have no CISP identifier in the edition either, so they need one before a link can exist.

## Summary

| gap | stones |
|---|---|
| numbered without findspot | 5 |
| hedged | 6 |
| lost without findspot | 7 |
| doubtful without findspot | 10 |
| without edition text | 38 |
| broken cisp links | 200 |

