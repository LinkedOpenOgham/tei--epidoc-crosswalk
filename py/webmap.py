#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""webmap.py -- publish the place layer as a browsable map.

Writes ``docs/index.html``, a self-contained Leaflet map of every findspot the
place layer resolved, plus ``docs/places.geojson`` as a plain download. ``docs/``
is what GitHub Pages serves (Settings -> Pages -> Source: main, /docs), so the
map is live as soon as the directory is pushed.

The point data is inlined into the HTML, so the file also opens straight from
disk. Only the basemap tiles and the two Leaflet libraries come off the network.

Called from ``main.py`` after ``places.run()``; nothing here re-parses the XML,
so the map cannot drift away from the graph.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

# Fields carried into the popup. Keys are short because they are inlined 500 times.
FIELDS = {
    "id": "ogham_id", "title": "title", "ciic": "ciic", "cisp": "cisp",
    "tm": "tm", "smr": "smr", "townland": "pn_townland", "parish": "pn_parish",
    "county": "pn_county", "country": "pn_country", "vern": "pn_vernacular",
    "repo": "repository",
}

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Linked Open Ogham — findspots</title>
<meta name="description" content="Findspots of the OG(H)AM ogham corpus, crosswalked to CIDOC CRM.">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Vollkorn:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  --ink:#131c1b; --panel:#1b2725; --panel-2:#233130; --line:#33433f;
  --text:#e9e5da; --muted:#93a29d; --stone:#b8b2a7;
  --ie:#5b8c5a; --ni:#9aab3f; --sc:#3f7d8c; --wa:#b07d2b; --en:#7a5c8e; --im:#b0413e;
  --sans:'IBM Plex Sans',system-ui,-apple-system,sans-serif;
  --mono:'IBM Plex Mono',ui-monospace,monospace;
  --display:'Vollkorn',Georgia,serif;
}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{font-family:var(--sans);background:var(--ink);color:var(--text);overflow:hidden}
#app{display:flex;height:100vh}

#side{width:342px;flex:0 0 342px;background:var(--panel);border-right:1px solid var(--line);
  display:flex;flex-direction:column;overflow:hidden}
header{padding:20px 20px 14px;border-bottom:1px solid var(--line)}
.stem{display:block;width:100%;height:34px;margin-bottom:11px}
h1{font-family:var(--display);font-weight:700;font-size:23px;line-height:1.15;margin:0 0 5px}
.sub{font-size:12.5px;color:var(--muted);line-height:1.5;margin:0}
.sub a{color:var(--stone)}

.scroll{overflow-y:auto;padding:16px 20px 26px;flex:1}
.scroll::-webkit-scrollbar{width:8px}
.scroll::-webkit-scrollbar-thumb{background:var(--line);border-radius:4px}

.tally{font-family:var(--mono);font-size:12px;color:var(--muted);
  padding:2px 0 14px;border-bottom:1px solid var(--line);margin-bottom:16px}
.tally b{color:var(--text);font-size:22px;font-weight:500;display:block;letter-spacing:-.02em}

.field{display:block;font-size:11px;letter-spacing:.09em;text-transform:uppercase;
  color:var(--muted);margin:0 0 7px;padding:0}
input[type=search]{width:100%;padding:9px 11px;background:var(--panel-2);color:var(--text);
  border:1px solid var(--line);border-radius:3px;font-family:var(--mono);font-size:13px}
input[type=search]::placeholder{color:#6d7b77}
input[type=search]:focus{outline:2px solid var(--sc);outline-offset:1px}

fieldset{border:0;padding:0;margin:22px 0 0}
.opt{display:flex;align-items:center;gap:9px;padding:5px 0;cursor:pointer;font-size:13.5px}
.opt input{accent-color:var(--sc);margin:0;width:14px;height:14px;flex:0 0 14px}
.opt .dot{width:11px;height:11px;border-radius:50%;flex:0 0 11px}
.opt .n{margin-left:auto;font-family:var(--mono);font-size:11.5px;color:var(--muted)}
.opt:hover{color:#fff}
.opt:focus-within{outline:1px solid var(--sc);outline-offset:3px}

.note{font-size:12px;color:var(--muted);line-height:1.55;margin-top:22px;
  padding-top:15px;border-top:1px solid var(--line)}
.note code{color:var(--stone);font-size:11.5px}
details{margin-top:12px}
details summary{cursor:pointer;font-size:12.5px;color:var(--stone)}
details ul{font-family:var(--mono);font-size:11px;color:var(--muted);padding-left:16px;line-height:1.75;margin:8px 0 0}
.dl{margin-top:16px;font-size:12px;line-height:1.9}
.dl a{color:var(--stone);text-decoration:none;border-bottom:1px solid var(--line)}
.dl a:hover{color:#fff;border-color:var(--sc)}

#map{flex:1;background:#e8e6df}
.leaflet-container{font-family:var(--sans);background:#e8e6df}
.pin{border-radius:50%;border:1.6px solid rgba(19,28,27,.7);box-shadow:0 1px 3px rgba(0,0,0,.3)}
.pin.vague{border-style:dashed;background:transparent!important}

/* clusters: drawn entirely in CSS, no sprite sheets, no default stylesheet */
.ogham-cluster{background:rgba(51,67,63,.35);border-radius:50%;
  transition:background .15s ease}
.ogham-cluster:hover{background:rgba(63,125,140,.45)}
.ogham-cluster div{width:30px;height:30px;margin:5px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  color:#eef0ea;font-family:var(--mono);font-size:12px;font-weight:500;
  box-shadow:0 1px 4px rgba(0,0,0,.28)}
.ogham-cluster.sm div{background:#4a635e}
.ogham-cluster.md{background:rgba(51,74,70,.34)}
.ogham-cluster.md div{background:#334a46;font-size:12.5px}
.ogham-cluster.lg div{background:#1d2b28;font-size:13px}
.ogham-cluster.lg{background:rgba(29,43,40,.32)}

.leaflet-popup-content-wrapper{background:var(--panel);color:var(--text);border-radius:3px;
  box-shadow:0 3px 16px rgba(0,0,0,.35)}
.leaflet-popup-tip{background:var(--panel)}
.leaflet-popup-content{margin:15px 17px;font-size:13px;line-height:1.5;max-width:290px}
.leaflet-container a.leaflet-popup-close-button{color:var(--muted)}
.pop h2{font-family:var(--display);font-size:17px;margin:0 0 2px;font-weight:600;line-height:1.2}
.pop .where{color:var(--muted);font-size:12.5px;margin-bottom:10px}
.pop .flag{display:inline-block;font-size:11px;padding:2px 7px;border-radius:2px;
  background:rgba(176,125,43,.22);color:#e0bd77;margin-bottom:9px}
.pop dl{display:grid;grid-template-columns:auto 1fr;gap:2px 11px;margin:0 0 10px;
  font-family:var(--mono);font-size:11.5px}
.pop dt{color:var(--muted)}
.pop dd{margin:0;word-break:break-all}
.pop .links a{color:var(--stone);font-size:12px;margin-right:11px}
.leaflet-control-attribution{background:rgba(255,255,255,.82);font-size:10.5px}

@media (max-width:760px){
  #app{flex-direction:column}
  #side{width:100%;flex:0 0 auto;max-height:48vh;border-right:0;border-bottom:1px solid var(--line)}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
</head>
<body>
<div id="app">
  <aside id="side">
    <header>
      <!-- MAP on a stemline. M = aicme Muine 1, one stroke crossing the stemline
           diagonally. A = aicme Ailme 1, one stroke crossing it perpendicularly.
           P has no orthodox letter: this is the forfid peith (U+169A), drawn as
           beithe (one stroke below the line) with the crossbar that softens it.
           Feather marks open and close the inscription. -->
      <svg class="stem" viewBox="0 0 300 34" role="img" aria-label="map, written in ogham">
        <g stroke="#b8b2a7" stroke-width="1.6" fill="none" stroke-linecap="square">
          <path d="M4 17 h292" stroke-width="1.1"/>
          <path d="M4 17 l7 -7 M4 17 l7 7"/>
          <path d="M82 27 l15 -20"/>
          <path d="M150 6 v22"/>
          <path d="M210 17 v11 M203 23 h14"/>
          <path d="M296 17 l-7 -7 M296 17 l-7 7"/>
        </g>
      </svg>
      <h1>Ogham findspots</h1>
      <p class="sub">Findspots of the OG(H)AM corpus, read out of
      <code>&lt;origPlace&gt;/&lt;geo&gt;</code> and crosswalked to CIDOC CRM
      <code>E53_Place</code>.</p>
    </header>
    <div class="scroll">
      <div class="tally"><b id="count">0</b><span id="countLabel">stones shown</span></div>

      <label class="field" for="q">Search name or identifier</label>
      <input type="search" id="q" placeholder="Ballintaggart, CIIC 55, I-COR-001…" autocomplete="off">

      <fieldset id="countries"><legend class="field">Country</legend></fieldset>

      <fieldset>
        <legend class="field">Certainty</legend>
        <label class="opt"><input type="checkbox" id="onlyVague"> Only hedged findspots
          <span class="n" id="vagueN"></span></label>
      </fieldset>

      <p class="note">Dashed rings mark findspots the editors hedged — either
      <code>@cert="low"</code> on <code>&lt;geo&gt;</code> or a qualifier such as
      “approximate” written into the coordinate string. In the graph these carry
      <code>ogham:geoStatus</code>; the weight over them is added in axis 2.</p>

      <details>
        <summary id="missingSummary">Records without coordinates</summary>
        <ul id="missingList"></ul>
      </details>

      <p class="dl">
        <a href="places.geojson" download>Download GeoJSON</a><br>
        <a href="https://github.com/LinkedOpenOgham/tei--epidoc-crosswalk">Source &amp; RDF on GitHub</a>
      </p>
      <p class="note" style="margin-top:16px">Generated <span id="built">__BUILT__</span> by
      <code>py/webmap.py</code> from __PROV__. Editions © the OG(H)AM project,
      CC BY 4.0.</p>
    </div>
  </aside>
  <div id="map"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.min.js"></script>
<script>
const DATA = __DATA__;
const MISSING = __MISSING__;

const COLOURS = {
  "Ireland":"#5b8c5a", "Northern Ireland":"#9aab3f", "Scotland":"#3f7d8c",
  "Wales":"#b07d2b", "England":"#7a5c8e", "Isle of Man":"#b0413e"
};
const colourFor = c => COLOURS[c] || "#8d9a97";
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

const map = L.map("map", {zoomControl:false}).setView([54.2,-6.5], 6);
L.control.zoom({position:"bottomright"}).addTo(map);
L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
  attribution:'&copy; OpenStreetMap contributors &copy; CARTO · editions: OG(H)AM (CC BY 4.0)',
  subdomains:"abcd", maxZoom:19
}).addTo(map);

// Clusters are styled here rather than by MarkerCluster's default stylesheet,
// which ships sprite-sheet backgrounds that do not match this palette.
const cluster = L.markerClusterGroup({
  maxClusterRadius: 40,
  showCoverageOnHover: false,
  spiderfyDistanceMultiplier: 1.6,
  iconCreateFunction: c => {
    const n = c.getChildCount();
    const tier = n < 10 ? "sm" : n < 50 ? "md" : "lg";
    return L.divIcon({html:`<div><span>${n}</span></div>`,
                      className:`ogham-cluster ${tier}`, iconSize:L.point(40,40)});
  }
});
map.addLayer(cluster);

function icon(colour, vague){
  const d = 13;
  return L.divIcon({
    className:"", iconSize:[d,d], iconAnchor:[d/2,d/2],
    html:`<div class="pin${vague?" vague":""}" style="width:${d}px;height:${d}px;`
       + `background:${colour};border-color:${vague?colour:"rgba(19,28,27,.7)"}"></div>`
  });
}

function popup(p){
  const where = [p.townland, p.parish, p.county, p.country].filter(Boolean).join(", ");
  const rows = [["OG(H)AM", p.id], ["CIIC", p.ciic], ["CISP", p.cisp],
                ["Trismegistos", p.tm], ["SMR", p.smr], ["now in", p.repo]].filter(r => r[1]);
  rows.push(["lat, lon", p.lat.toFixed(5) + ", " + p.lon.toFixed(5)]);
  rows.push(["CRM node", "data:findspot_" + p.id.replace(/[^A-Za-z0-9]+/g, "_")]);
  const links = [];
  if (p.logainm) links.push(`<a href="${esc(p.logainm)}" target="_blank" rel="noopener">Gazetteer</a>`);
  if (p.cispUrl) links.push(`<a href="${esc(p.cispUrl)}" target="_blank" rel="noopener">CISP</a>`);
  if (p.tm) links.push(`<a href="https://www.trismegistos.org/text/${esc(p.tm)}" target="_blank" rel="noopener">TM</a>`);
  links.push(`<a href="https://www.openstreetmap.org/?mlat=${p.lat}&mlon=${p.lon}#map=16/${p.lat}/${p.lon}" target="_blank" rel="noopener">OSM</a>`);
  return `<div class="pop">
    <h2>${esc(p.title || p.id)}</h2>
    <div class="where">${esc(where)}${p.vern ? " · " + esc(p.vern) : ""}</div>
    ${p.vague ? `<span class="flag">hedged: ${esc(p.vagueWhy)}</span>` : ""}
    <dl>${rows.map(([k,v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl>
    <div class="links">${links.join("")}</div>
  </div>`;
}

DATA.forEach(p => {
  p._m = L.marker([p.lat, p.lon], {icon:icon(colourFor(p.country), p.vague), title:p.title || p.id})
          .bindPopup(() => popup(p), {maxWidth:330});
  p._hay = [p.title, p.id, p.ciic, p.cisp, p.tm, p.smr, p.townland, p.parish,
            p.county, p.country, p.vern].filter(Boolean).join(" ").toLowerCase();
});

const tallies = {};
DATA.forEach(p => { const c = p.country || "unrecorded"; tallies[c] = (tallies[c] || 0) + 1; });
const fs = document.getElementById("countries");
Object.keys(tallies).sort((a,b) => tallies[b] - tallies[a]).forEach(c => {
  const l = document.createElement("label");
  l.className = "opt";
  l.innerHTML = `<input type="checkbox" class="cc" value="${esc(c)}" checked>`
              + `<span class="dot" style="background:${colourFor(c)}"></span>${esc(c)}`
              + `<span class="n">${tallies[c]}</span>`;
  fs.appendChild(l);
});

const q = document.getElementById("q");
const onlyVague = document.getElementById("onlyVague");
document.getElementById("vagueN").textContent = DATA.filter(p => p.vague).length;

function apply(){
  const on = new Set([...document.querySelectorAll(".cc:checked")].map(i => i.value));
  const term = q.value.trim().toLowerCase();
  const keep = DATA.filter(p =>
    on.has(p.country || "unrecorded") &&
    (!onlyVague.checked || p.vague) &&
    (!term || p._hay.includes(term)));
  cluster.clearLayers();
  cluster.addLayers(keep.map(p => p._m));
  document.getElementById("count").textContent = keep.length;
  document.getElementById("countLabel").textContent = keep.length === 1 ? "stone shown" : "stones shown";
}
fs.addEventListener("change", apply);
onlyVague.addEventListener("change", apply);
q.addEventListener("input", apply);
apply();
if (DATA.length) map.fitBounds(L.latLngBounds(DATA.map(p => [p.lat, p.lon])).pad(0.05));

document.getElementById("missingSummary").textContent =
  `${MISSING.length} records without usable coordinates`;
document.getElementById("missingList").innerHTML =
  MISSING.map(m => `<li>${esc(m.id)} — ${esc(m.reason)}</li>`).join("");
</script>
</body>
</html>
"""


def _slim(rec: dict) -> dict:
    out = {k: rec.get(src, "") for k, src in FIELDS.items()}
    out = {k: v for k, v in out.items() if v}
    out["lat"], out["lon"] = rec["lat"], rec["lon"]
    cisp_url = rec.get("cisp_url")
    if cisp_url:
        out["cispUrl"] = cisp_url
    gaz = (rec.get("gazetteer_uris") or "").split(" | ")[0]
    if gaz:
        out["logainm"] = gaz
    why = rec.get("geo_hedge") or ('cert="low"' if rec.get("geo_cert") else "")
    if why:
        out["vague"] = True
        out["vagueWhy"] = why
    return out


def _provenance_html(prov: dict) -> str:
    """One line naming the corpus state the page was built from."""
    if not prov.get("commit"):
        return "the OG(H)AM EpiDoc corpus"
    short = prov["commit"][:7]
    date = (prov.get("commit_date") or "")[:10]
    if prov.get("tree_url"):
        return (f'OG(H)AM corpus <a href="{prov["tree_url"]}" target="_blank" '
                f'rel="noopener"><code>{short}</code></a> ({date})')
    return f"OG(H)AM corpus <code>{short}</code> ({date})"


def build(records: list[dict], docs: Path, root: Path | None = None,
          provenance: dict | None = None) -> dict:
    """Write docs/index.html and docs/places.geojson from the parsed records."""
    docs.mkdir(parents=True, exist_ok=True)
    mapped = [_slim(r) for r in records if r.get("lat") is not None]
    missing = [{"id": r.get("ogham_id") or r["file"],
                "reason": (r.get("geo_raw") or "").strip() or "empty <geo>"}
               for r in records if r.get("lat") is None]

    html = (TEMPLATE
            .replace("__DATA__", json.dumps(mapped, ensure_ascii=False, separators=(",", ":")))
            .replace("__MISSING__", json.dumps(missing, ensure_ascii=False, separators=(",", ":")))
            .replace("__BUILT__", dt.date.today().isoformat())
            .replace("__PROV__", _provenance_html(provenance or {})))
    (docs / "index.html").write_text(html, encoding="utf-8")

    # GeoJSON beside the map, so the Pages site doubles as a small data endpoint
    features = [{"type": "Feature", "id": p["id"],
                 "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
                 "properties": {k: v for k, v in p.items() if k not in {"lat", "lon"}}}
                for p in mapped]
    (docs / "places.geojson").write_text(json.dumps(
        {"type": "FeatureCollection", "name": "OG(H)AM findspots", "features": features},
        ensure_ascii=False, indent=1), encoding="utf-8")

    # Pages would otherwise run Jekyll over the directory
    (docs / ".nojekyll").write_text("", encoding="utf-8")

    rel = (lambda p: p.relative_to(root)) if root else (lambda p: p)
    size = (docs / "index.html").stat().st_size / 1024
    print(f"  -> wrote {rel(docs / 'index.html')} ({len(mapped)} points, {size:.0f} KB)")
    print(f"  -> wrote {rel(docs / 'places.geojson')}")
    return {"mapped": len(mapped), "missing": len(missing)}
