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

CSS = r"""
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

nav{display:flex;gap:2px;margin-bottom:14px}
nav a{flex:1;text-align:center;padding:7px 4px;font-size:12px;letter-spacing:.04em;
  color:var(--muted);text-decoration:none;background:var(--panel-2);
  border:1px solid var(--line);border-radius:3px}
nav a:hover{color:var(--text)}
nav a[aria-current]{background:var(--sc);border-color:var(--sc);color:#0f1918;font-weight:600}

.wordlist{margin-top:6px}
.wordgroup{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:#6d7b77;
  margin:16px 0 5px;padding-top:11px;border-top:1px solid var(--line)}
.wordgroup:first-child{border-top:0;padding-top:0;margin-top:8px}
.word{display:flex;align-items:baseline;gap:8px;padding:4px 0;cursor:pointer;font-size:13px}
.word input{margin:0;accent-color:var(--sc);flex:0 0 13px}
.word b{font-family:var(--mono);font-weight:500;font-size:12.5px}
.word .tr{color:var(--muted);font-size:11.5px;flex:1;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.word .n{font-family:var(--mono);font-size:11px;color:var(--muted)}
.word:hover b{color:#fff}

.gloss{background:var(--panel-2);border:1px solid var(--line);border-radius:3px;
  padding:11px 12px;margin:14px 0 0;font-size:12.5px;line-height:1.55}
.gloss h2{font-family:var(--display);font-size:19px;margin:0 0 2px;font-weight:600}
.gloss .meta{color:var(--muted);font-size:11.5px;margin-bottom:7px}
.gloss a{color:var(--stone)}
.legend{display:flex;gap:14px;font-size:11.5px;color:var(--muted);margin-top:11px;
  align-items:center;flex-wrap:wrap}
.legend span{display:flex;align-items:center;gap:6px}
.pop .rdg{font-family:var(--mono);font-size:11.5px;line-height:1.5;margin:0 0 8px}
.pop .rdg em{color:var(--muted);font-style:normal}
.pop mark{background:rgba(63,125,140,.45);color:#eef0ea;border-radius:2px;padding:0 1px}

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
"""

HEAD = r"""<!DOCTYPE html>
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
<style>__CSS__</style>
</head>
<body>
"""

FOOT = r"""</script>
</body>
</html>
"""

SCRIPTS = r"""<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.min.js"></script>
<script>
"""

BODY = r"""<div id="app">
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
      <nav>
        <a href="index.html" aria-current="page">Findspots</a>
        <a href="words.html">Formulaic words</a>
      </nav>
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

"""

JS = r"""const DATA = __DATA__;
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
"""

HEAD_WORDS = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Linked Open Ogham — formulaic words</title>
<meta name="description" content="Formulaic words and name elements across the readings of the OG(H)AM ogham corpus.">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Vollkorn:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>__CSS__</style>
</head>
<body>
"""

WORDS_BODY = r"""<div id="app">
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
      <h1>Formulaic words</h1>
      <p class="sub">McManus's formulaic vocabulary matched against every reading
      of every ogham inscription — not just the current one.</p>
    </header>
    <div class="scroll">
      <nav>
        <a href="index.html">Findspots</a>
        <a href="words.html" aria-current="page">Formulaic words</a>
      </nav>
      <div class="tally"><b id="count">0</b><span id="countLabel">stones shown</span></div>

      <div id="gloss" class="gloss"></div>

      <div class="legend">
        <span><i class="pin" style="width:11px;height:11px;background:#3f7d8c;
          border:1.6px solid rgba(19,28,27,.7)"></i> in the current edition</span>
        <span><i class="pin vague" style="width:11px;height:11px;
          border:1.6px dashed #b07d2b"></i> only in an older reading</span>
      </div>

      <label class="field" for="q" style="margin-top:22px">Filter the vocabulary</label>
      <input type="search" id="q" placeholder="maqi, son, hound…" autocomplete="off">

      <div class="wordlist" id="wordlist"></div>

      <p class="note">Word list from
      <a href="https://github.com/LinkedOpenOgham/o3d-epidoc-extractor">o3d-epidoc-extractor</a>
      (Homburg &amp; Thiery, DHd 2020), after McManus 1991. <b>Name elements are
      matched as substrings</b>, which is that project's semantics and is not
      precise: short elements such as CON or VIR also fire inside unrelated names.
      Each hit records which mode produced it.</p>

      <p class="dl">
        <a href="words.csv" download>Download matches (CSV)</a><br>
        <a href="https://github.com/LinkedOpenOgham/tei--epidoc-crosswalk">Source &amp; RDF on GitHub</a>
      </p>
      <p class="note" style="margin-top:16px">Generated <span id="built">__BUILT__</span> by
      <code>py/webmap.py</code> from __PROV__. Editions &copy; the OG(H)AM project,
      CC BY 4.0.</p>
    </div>
  </aside>
  <div id="map"></div>
</div>

"""

WORDS_JS = r"""const WORDS = __WORDS__;
const STONES = __STONES__;

const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const CURRENT = "#3f7d8c", OLDER = "#b07d2b";
const GROUPS = [["formula","Formula words"],["element","Name elements"],["compound","Compound names"]];

const map = L.map("map", {zoomControl:false}).setView([53.6,-7.5], 6);
L.control.zoom({position:"bottomright"}).addTo(map);
L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
  attribution:'&copy; OpenStreetMap contributors &copy; CARTO · editions: OG(H)AM (CC BY 4.0)',
  subdomains:"abcd", maxZoom:19
}).addTo(map);

const cluster = L.markerClusterGroup({
  maxClusterRadius: 40, showCoverageOnHover:false, spiderfyDistanceMultiplier:1.6,
  iconCreateFunction: c => {
    const n = c.getChildCount();
    const tier = n < 10 ? "sm" : n < 50 ? "md" : "lg";
    return L.divIcon({html:`<div><span>${n}</span></div>`,
                      className:`ogham-cluster ${tier}`, iconSize:L.point(40,40)});
  }
});
map.addLayer(cluster);

function icon(current){
  const d = 13, colour = current ? CURRENT : OLDER;
  return L.divIcon({className:"", iconSize:[d,d], iconAnchor:[d/2,d/2],
    html:`<div class="pin${current?"":" vague"}" style="width:${d}px;height:${d}px;`
       + `background:${current?colour:"transparent"};border-color:${current?"rgba(19,28,27,.7)":colour}"></div>`});
}

// highlight the matched token inside the reading it was found in
function markup(text, token){
  if (!token) return esc(text);
  const i = text.toUpperCase().indexOf(token.toUpperCase());
  if (i < 0) return esc(text);
  return esc(text.slice(0,i)) + "<mark>" + esc(text.slice(i, i+token.length))
       + "</mark>" + esc(text.slice(i+token.length));
}

function popup(stone, key){
  const hits = stone.hits[key] || [];
  const rows = hits.map(h => {
    const r = stone.readings[h.r];
    return `<p class="rdg"><em>${esc(r.e)}</em><br>${markup(r.t, h.tk)}</p>`;
  }).join("");
  const w = key ? WORDS[key] : null;
  return `<div class="pop">
    <h2>${esc(stone.title || stone.id)}</h2>
    <div class="where">${esc([stone.county, stone.country].filter(Boolean).join(", "))}
      ${stone.ciic ? " · CIIC " + esc(stone.ciic) : ""}</div>
    ${w ? `<span class="flag">${esc(w.word)}${w.tr ? " — " + esc(w.tr) : ""}</span>` : ""}
    ${rows}
    <div class="links">
      <a href="index.html">on the findspot map</a>
      ${w && w.wd ? `<a href="${esc(w.wd)}" target="_blank" rel="noopener">Wikidata</a>` : ""}
    </div>
  </div>`;
}

STONES.forEach(s => { s._m = {}; });

let selected = null;   // null = every word

function stonesFor(key){
  return key === null ? STONES.filter(s => Object.keys(s.hits).length)
                      : STONES.filter(s => s.hits[key]);
}
function isCurrent(stone, key){
  const hits = key === null ? Object.values(stone.hits).flat() : stone.hits[key];
  return hits.some(h => stone.readings[h.r].c);
}

function draw(){
  const keep = stonesFor(selected);
  cluster.clearLayers();
  cluster.addLayers(keep.map(s => {
    const cur = isCurrent(s, selected);
    const m = L.marker([s.lat, s.lon], {icon:icon(cur), title:s.title || s.id});
    m.bindPopup(() => popup(s, selected), {maxWidth:340});
    return m;
  }));
  document.getElementById("count").textContent = keep.length;
  document.getElementById("countLabel").textContent =
    keep.length === 1 ? "stone shown" : "stones shown";
  if (keep.length) map.fitBounds(L.latLngBounds(keep.map(s => [s.lat, s.lon])).pad(0.08));

  const g = document.getElementById("gloss");
  if (selected === null){
    g.innerHTML = `<h2>All words</h2><div class="meta">every stone with at least one match</div>`;
    return;
  }
  const w = WORDS[selected];
  g.innerHTML = `<h2>${esc(w.word)}</h2>
    <div class="meta">${esc(w.modeLabel)}${w.tr ? " · " + esc(w.tr) : ""}</div>
    <div>Variants: <code>${w.variants.map(esc).join(", ")}</code></div>
    ${w.ref ? `<div class="meta" style="margin:6px 0 0">${esc(w.ref)}</div>` : ""}
    ${w.wd ? `<div style="margin-top:6px"><a href="${esc(w.wd)}" target="_blank" rel="noopener">Wikidata</a></div>` : ""}`;
}

function buildList(){
  const box = document.getElementById("wordlist");
  const term = document.getElementById("q").value.trim().toLowerCase();
  box.innerHTML = "";
  const all = document.createElement("label");
  all.className = "word";
  all.innerHTML = `<input type="radio" name="w" value="" ${selected===null?"checked":""}>`
                + `<b>All words</b><span class="tr"></span>`
                + `<span class="n">${STONES.filter(s=>Object.keys(s.hits).length).length}</span>`;
  box.appendChild(all);
  GROUPS.forEach(([mode, label]) => {
    const keys = Object.keys(WORDS)
      .filter(k => WORDS[k].mode === mode && WORDS[k].n > 0)
      .filter(k => !term || (WORDS[k].word + " " + WORDS[k].tr).toLowerCase().includes(term))
      .sort((a,b) => WORDS[b].n - WORDS[a].n || WORDS[a].word.localeCompare(WORDS[b].word));
    if (!keys.length) return;
    const h = document.createElement("div");
    h.className = "wordgroup";
    h.textContent = `${label} · ${keys.length}`;
    box.appendChild(h);
    keys.forEach(k => {
      const w = WORDS[k];
      const l = document.createElement("label");
      l.className = "word";
      l.innerHTML = `<input type="radio" name="w" value="${esc(k)}" ${selected===k?"checked":""}>`
                  + `<b>${esc(w.word)}</b><span class="tr">${esc(w.tr)}</span>`
                  + `<span class="n">${w.n}</span>`;
      box.appendChild(l);
    });
  });
  box.querySelectorAll("input[name=w]").forEach(i =>
    i.addEventListener("change", () => { selected = i.value || null; draw(); }));
}

document.getElementById("q").addEventListener("input", buildList);
buildList();
draw();
"""


def _page(head: str, body: str, js: str) -> str:
    """Assemble a page from the shared shell."""
    return head.replace("__CSS__", CSS) + body + SCRIPTS + js + FOOT


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

    html = (_page(HEAD, BODY, JS)
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


def build_words(word_records: list[dict], place_records: list[dict],
                vocabulary: list[dict], docs: Path, root: Path | None = None,
                provenance: dict | None = None) -> dict:
    """Write docs/words.html: the formulaic vocabulary on the map.

    Joined to the findspots by OG(H)AM id, so a word only appears where the place
    layer resolved a coordinate. Words with no occurrence in the corpus are kept
    out of the picker rather than shown as empty options.
    """
    docs.mkdir(parents=True, exist_ok=True)
    coords = {r["ogham_id"]: r for r in place_records if r.get("lat") is not None}

    vocab: dict[str, dict] = {}
    for entry in vocabulary:
        key = f"{entry['word']}|{entry['mode']}"
        vocab[key] = {"word": entry["word"], "mode": entry["mode"],
                      "modeLabel": entry["mode_label"], "tr": entry["translation"],
                      "ref": entry["reference"], "wd": entry["wikidata"],
                      "variants": entry["variants"], "n": 0}

    stones = []
    for rec in word_records:
        place = coords.get(rec["ogham_id"])
        if place is None:
            continue
        readings, hits = [], {}
        for r in rec["readings"]:
            if not r["matches"]:
                continue
            idx = len(readings)
            readings.append({"e": r["editor"], "t": r["text"], "c": bool(r["current"])})
            for m in r["matches"]:
                key = f"{m['word']}|{m['mode']}"
                hits.setdefault(key, []).append({"r": idx, "tk": m["token"]})
        if not hits:
            continue
        for key in hits:
            if key in vocab:
                vocab[key]["n"] += 1
        stones.append({
            "id": rec["ogham_id"], "title": rec["title"], "ciic": rec["ciic"],
            "county": place.get("pn_county", ""), "country": place.get("pn_country", ""),
            "lat": place["lat"], "lon": place["lon"],
            "readings": readings, "hits": hits,
        })

    html = (_page(HEAD_WORDS, WORDS_BODY, WORDS_JS)
            .replace("__WORDS__", json.dumps(vocab, ensure_ascii=False, separators=(",", ":")))
            .replace("__STONES__", json.dumps(stones, ensure_ascii=False, separators=(",", ":")))
            .replace("__BUILT__", dt.date.today().isoformat())
            .replace("__PROV__", _provenance_html(provenance or {})))
    (docs / "words.html").write_text(html, encoding="utf-8")

    rel = (lambda p: p.relative_to(root)) if root else (lambda p: p)
    size = (docs / "words.html").stat().st_size / 1024
    used = sum(1 for v in vocab.values() if v["n"])
    print(f"  -> wrote {rel(docs / 'words.html')} ({len(stones)} stones, "
          f"{used} words attested, {size:.0f} KB)")
    return {"stones": len(stones), "words_attested": used}
