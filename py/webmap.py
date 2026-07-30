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
.btn{flex:1;padding:8px 6px;font-family:var(--sans);font-size:12px;cursor:pointer;
  color:var(--text);background:var(--panel-2);border:1px solid var(--line);border-radius:3px}
.btn:hover{border-color:var(--sc);color:#fff}
.btn:active{background:var(--sc);color:#0f1918}
.btn:disabled{opacity:.5;cursor:progress}

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
.pop .badge{display:inline-block;font-size:10px;padding:1px 6px;border-radius:2px;
  margin-left:6px;font-family:var(--sans);letter-spacing:.02em}
.pop .gain{color:#9aab3f;font-size:11px}
.pop .loss{color:#b0413e;font-size:11px}

/* landing page: one centred column, no map */
body.landing{overflow:auto}
.wrap{max-width:760px;margin:0 auto;padding:56px 28px 72px}
.wrap .stem{height:44px;margin-bottom:22px}
.wrap h1{font-family:var(--display);font-size:38px;line-height:1.08;margin:0 0 12px;font-weight:700}
.lede{font-size:15.5px;line-height:1.6;color:#c3ccc8;margin:0 0 8px;max-width:60ch}
.lede code{font-size:13.5px;color:var(--stone)}
.byline{font-size:12.5px;color:var(--muted);margin:0 0 40px}
.byline a{color:var(--stone)}

.cards{display:grid;gap:14px;margin-bottom:44px}
.card{display:block;text-decoration:none;color:inherit;background:var(--panel);
  border:1px solid var(--line);border-radius:4px;padding:20px 22px;
  transition:border-color .15s ease,background .15s ease}
.card:hover{border-color:var(--sc);background:var(--panel-2)}
.card h2{font-family:var(--display);font-size:22px;margin:0 0 5px;font-weight:600}
.card p{margin:0 0 13px;font-size:13.5px;line-height:1.55;color:#b9c2be;max-width:58ch}
.figs{display:flex;gap:26px;flex-wrap:wrap}
.fig{font-family:var(--mono);font-size:11px;color:var(--muted);line-height:1.35}
.fig b{display:block;font-size:19px;font-weight:500;color:var(--text);letter-spacing:-.02em}
.soon{border-style:dashed;opacity:.6}
.soon:hover{border-color:var(--line);background:var(--panel)}

.section{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);
  margin:0 0 12px;padding-top:26px;border-top:1px solid var(--line)}
.files{display:grid;gap:9px;margin:0 0 34px;font-size:13px}
.files a{color:var(--stone);text-decoration:none;border-bottom:1px solid var(--line)}
.files a:hover{color:#fff;border-color:var(--sc)}
.files span{color:var(--muted);font-size:12px}
.foot{font-size:12px;color:var(--muted);line-height:1.6}
.foot a{color:var(--stone)}
.foot code{font-size:11.5px}

.hex-legend{background:rgba(27,39,37,.93);color:var(--text);padding:8px 11px;
  border-radius:3px;font-family:var(--mono);font-size:11px;line-height:1.75;
  box-shadow:0 1px 6px rgba(0,0,0,.3)}
.hex-legend b{font-family:var(--sans);font-size:11px;letter-spacing:.06em;
  text-transform:uppercase;color:var(--muted);font-weight:500}
.hex-legend .sw{display:inline-block;width:13px;height:13px;margin-right:7px;
  vertical-align:-2px;border:1px solid rgba(0,0,0,.35)}
.leaflet-bar a.ogham-fs{display:flex;align-items:center;justify-content:center;
  color:#3b4a46}
.leaflet-bar a.ogham-fs:hover{color:#131c1b}
#map:fullscreen{width:100vw;height:100vh}

.seg{display:flex;gap:2px;margin:0 0 10px}
.seg label{flex:1;text-align:center;padding:6px 4px;font-size:12px;cursor:pointer;
  color:var(--muted);background:var(--panel-2);border:1px solid var(--line);border-radius:3px}
.seg label:hover{color:var(--text)}
.seg input{position:absolute;opacity:0;pointer-events:none}
.seg input:checked + span{color:#0f1918}
.seg label:has(input:checked){background:var(--sc);border-color:var(--sc);
  color:#0f1918;font-weight:600}
.seg label:focus-within{outline:2px solid var(--sc);outline-offset:2px}
#hexsize,#hexscale{display:none}
#hexsize.on,#hexscale.on{display:flex}

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

EXPORT_JS = r"""
// --- export the current view --------------------------------------------------
// Both formats are drawn from the same scene description that the display switch
// keeps up to date, so an export shows what is on screen rather than a re-run of
// the filters. Points are drawn individually even when the screen shows clusters:
// a figure wants the distribution, not the bubbles.
//
// Basemap tiles are cross-origin. Rather than putting `crossOrigin` on the live
// tile layer -- which would break the map outright if the server ever stopped
// sending CORS headers -- the tiles are re-fetched with it only at export time,
// and the export degrades to a vector-only file if that fails.
let scene = { points: [], hexes: [], legend: null, title: "", noun: "stone" };

function tileURLs(mapEl, rect) {
  return [...mapEl.querySelectorAll("img.leaflet-tile")]
    .filter(i => i.src && i.complete && i.naturalWidth)
    .map(i => {
      const r = i.getBoundingClientRect();
      return { src: i.src, x: r.left - rect.left, y: r.top - rect.top,
               w: r.width, h: r.height };
    });
}

function loadCORS(src) {
  return new Promise(resolve => {
    const im = new Image();
    im.crossOrigin = "anonymous";
    im.onload = () => resolve(im);
    im.onerror = () => resolve(null);
    im.src = src;
  });
}

async function basemapRaster(scale) {
  const mapEl = document.getElementById("map");
  const rect = mapEl.getBoundingClientRect();
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(rect.width * scale);
  canvas.height = Math.round(rect.height * scale);
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#e8e6df";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const tiles = tileURLs(mapEl, rect);
  const images = await Promise.all(tiles.map(t => loadCORS(t.src)));
  let drawn = 0;
  images.forEach((im, i) => {
    if (!im) return;
    const t = tiles[i];
    ctx.drawImage(im, t.x * scale, t.y * scale, t.w * scale, t.h * scale);
    drawn++;
  });
  try {
    return { canvas, ctx, dataURL: canvas.toDataURL("image/png"),
             complete: drawn === tiles.length && drawn > 0 };
  } catch (e) {                       // tainted despite the CORS attempt
    ctx.fillStyle = "#e8e6df";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    return { canvas, ctx, dataURL: null, complete: false };
  }
}

function projected() {
  const pt = ll => map.latLngToContainerPoint(L.latLng(ll[0], ll[1]));
  return {
    hexes: scene.hexes.map(h => ({
      fill: h.fill,
      ring: h.ring.map(ll => { const p = pt(ll); return [p.x, p.y]; })
    })),
    points: scene.points.map(p0 => {
      const p = pt([p0.lat, p0.lon]);
      return { x: p.x, y: p.y, colour: p0.colour, vague: p0.vague };
    })
  };
}

const ATTRIB = "\u00a9 OpenStreetMap contributors \u00a9 CARTO \u00b7 editions: OG(H)AM (CC BY 4.0)";

function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

function stamp(ext) {
  const bits = ["ogham", scene.slug || "map",
                (scene.title || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")];
  return bits.filter(Boolean).join("-").slice(0, 70) + "-"
       + new Date().toISOString().slice(0, 10) + "." + ext;
}

// Bottom-right, matching where the legend sits on screen and leaving the top-left
// corner -- now the zoom and full-screen controls -- out of the figure.
function drawLegendOnCanvas(ctx, rect) {
  if (!scene.legend || !scene.legend.length) return;
  const rows = scene.legend.length, lh = 17, bw = 132;
  const bh = rows * lh + 24, bx = rect.width - bw - 12, by = rect.height - bh - 26;
  ctx.fillStyle = "rgba(27,39,37,.93)";
  ctx.beginPath();
  ctx.roundRect ? ctx.roundRect(bx, by, bw, bh, 3) : ctx.rect(bx, by, bw, bh);
  ctx.fill();
  ctx.fillStyle = "#93a29d";
  ctx.font = "10px sans-serif";
  ctx.fillText((scene.legendTitle || "").toUpperCase(), bx + 10, by + 17);
  ctx.font = "11px monospace";
  scene.legend.forEach((b, i) => {
    const y = by + 30 + i * lh;
    ctx.fillStyle = b.colour;
    ctx.fillRect(bx + 10, y, 12, 12);
    ctx.strokeStyle = "rgba(0,0,0,.35)";
    ctx.lineWidth = 1;
    ctx.strokeRect(bx + 10.5, y + 0.5, 11, 11);
    ctx.fillStyle = "#e9e5da";
    ctx.fillText(b.label, bx + 28, y + 10);
  });
}

async function exportRaster() {
  const rect = document.getElementById("map").getBoundingClientRect();
  const scale = 2;
  const { canvas, ctx, complete } = await basemapRaster(scale);
  const geo = projected();
  ctx.save();
  ctx.scale(scale, scale);
  for (const h of geo.hexes) {
    ctx.beginPath();
    h.ring.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
    ctx.closePath();
    ctx.fillStyle = h.fill; ctx.globalAlpha = 0.75; ctx.fill();
    ctx.globalAlpha = 1; ctx.strokeStyle = "#2b3a37"; ctx.lineWidth = 0.7; ctx.stroke();
  }
  for (const p of geo.points) {
    ctx.beginPath();
    ctx.arc(p.x, p.y, 6.5, 0, Math.PI * 2);
    if (p.vague) {
      ctx.strokeStyle = p.colour; ctx.lineWidth = 1.6; ctx.setLineDash([3, 2]);
      ctx.stroke(); ctx.setLineDash([]);
    } else {
      ctx.fillStyle = p.colour; ctx.fill();
      ctx.strokeStyle = "rgba(19,28,27,.7)"; ctx.lineWidth = 1.6; ctx.stroke();
    }
  }
  drawLegendOnCanvas(ctx, rect);
  ctx.font = "11px sans-serif";
  const pad = 6, text = ATTRIB + (complete ? "" : " \u00b7 basemap incomplete");
  const w = ctx.measureText(text).width;
  ctx.fillStyle = "rgba(255,255,255,.82)";
  ctx.fillRect(rect.width - w - pad * 2, rect.height - 18, w + pad * 2, 18);
  ctx.fillStyle = "#333";
  ctx.fillText(text, rect.width - w - pad, rect.height - 5);
  ctx.restore();
  canvas.toBlob(b => download(b, stamp("jpg")), "image/jpeg", 0.92);
}

async function exportVector() {
  const rect = document.getElementById("map").getBoundingClientRect();
  const w = Math.round(rect.width), h = Math.round(rect.height);
  const { dataURL } = await basemapRaster(2);
  const geo = projected();
  const esc2 = t => String(t).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  const out = [];
  out.push(`<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" `
         + `width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">`);
  out.push(`<title>${esc2(scene.title || "Ogham map")}</title>`);
  out.push(`<desc>${esc2(ATTRIB)}</desc>`);
  out.push(`<rect width="${w}" height="${h}" fill="#e8e6df"/>`);
  if (dataURL) {
    out.push(`<g id="basemap"><image x="0" y="0" width="${w}" height="${h}" `
           + `xlink:href="${dataURL}"/></g>`);
  } else {
    out.push(`<!-- basemap omitted: tiles could not be read cross-origin -->`);
  }
  out.push('<g id="data">');
  for (const hx of geo.hexes) {
    const d = hx.ring.map(([x, y], i) => (i ? "L" : "M") + x.toFixed(1) + " " + y.toFixed(1)).join(" ") + " Z";
    out.push(`<path d="${d}" fill="${hx.fill}" fill-opacity="0.75" stroke="#2b3a37" stroke-width="0.7"/>`);
  }
  for (const p of geo.points) {
    out.push(p.vague
      ? `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="6.5" fill="none" `
        + `stroke="${p.colour}" stroke-width="1.6" stroke-dasharray="3 2"/>`
      : `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="6.5" fill="${p.colour}" `
        + `stroke="rgba(19,28,27,.7)" stroke-width="1.6"/>`);
  }
  out.push("</g>");
  if (scene.legend && scene.legend.length) {
    const lh = 17, bw = 132, bh = scene.legend.length * lh + 24;
    const bx = w - bw - 12, by = h - bh - 26;
    out.push(`<g id="legend"><rect x="${bx}" y="${by}" width="${bw}" height="${bh}" rx="3" `
           + `fill="rgba(27,39,37,.93)"/>`);
    out.push(`<text x="${bx + 10}" y="${by + 17}" font-family="sans-serif" font-size="10" `
           + `fill="#93a29d" letter-spacing="0.6">${esc2((scene.legendTitle || "").toUpperCase())}</text>`);
    scene.legend.forEach((b, i) => {
      const y = by + 30 + i * lh;
      out.push(`<rect x="${bx + 10}" y="${y}" width="12" height="12" fill="${b.colour}" `
             + `stroke="rgba(0,0,0,.35)"/>`);
      out.push(`<text x="${bx + 28}" y="${y + 10}" font-family="monospace" font-size="11" `
             + `fill="#e9e5da">${esc2(b.label)}</text>`);
    });
    out.push("</g>");
  }
  out.push(`<text x="${w - 6}" y="${h - 6}" text-anchor="end" font-family="sans-serif" `
         + `font-size="10" fill="#555">${esc2(ATTRIB)}</text>`);
  out.push("</svg>");
  download(new Blob([out.join("\n")], { type: "image/svg+xml" }), stamp("svg"));
}

function wireExport(id, fn) {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener("click", async () => {
    el.disabled = true;
    try { await fn(); } finally { el.disabled = false; }
  });
}
wireExport("dl-svg", exportVector);
wireExport("dl-jpg", exportRaster);
"""

MAPUI_JS = r"""
// --- map controls -------------------------------------------------------------
// Zoom sits top-left so the bottom-right corner is free for the density legend,
// which is where the legend also lands in an exported figure. Full screen uses the
// browser's own Fullscreen API on the map pane rather than a plugin: one less
// dependency, and the sidebar gets out of the way while inspecting a cluster.
function addMapControls(map) {
  L.control.zoom({ position: "topleft" }).addTo(map);

  const ICON_IN =
    '<svg viewBox="0 0 18 18" width="14" height="14" aria-hidden="true">' +
    '<g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="square">' +
    '<path d="M2 6V2h4M16 6V2h-4M2 12v4h4M16 12v4h-4"/></g></svg>';
  const ICON_OUT =
    '<svg viewBox="0 0 18 18" width="14" height="14" aria-hidden="true">' +
    '<g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="square">' +
    '<path d="M6 2v4H2M12 2v4h4M6 16v-4H2M12 16v-4h4"/></g></svg>';

  const Fullscreen = L.Control.extend({
    options: { position: "topleft" },
    onAdd: function () {
      const wrap = L.DomUtil.create("div", "leaflet-bar leaflet-control");
      const link = L.DomUtil.create("a", "ogham-fs", wrap);
      link.href = "#";
      link.title = "Full screen";
      link.setAttribute("role", "button");
      link.innerHTML = ICON_IN;
      L.DomEvent.on(link, "click", L.DomEvent.stopPropagation)
                .on(link, "click", L.DomEvent.preventDefault)
                .on(link, "click", () => {
        const el = document.getElementById("map");
        const on = document.fullscreenElement || document.webkitFullscreenElement;
        if (on) (document.exitFullscreen || document.webkitExitFullscreen).call(document);
        else (el.requestFullscreen || el.webkitRequestFullscreen).call(el);
      });
      this._link = link;
      return wrap;
    }
  });
  const control = new Fullscreen();
  map.addControl(control);

  const sync = () => {
    const on = !!(document.fullscreenElement || document.webkitFullscreenElement);
    if (control._link) {
      control._link.innerHTML = on ? ICON_OUT : ICON_IN;
      control._link.title = on ? "Leave full screen" : "Full screen";
    }
    setTimeout(() => map.invalidateSize(), 120);
  };
  document.addEventListener("fullscreenchange", sync);
  document.addEventListener("webkitfullscreenchange", sync);
}
"""

HEX_JS = r"""
// --- hex-binned density -------------------------------------------------------
// Ported from the holy-wells notebook of the SPARQLing Archaeology OER
// (n4o-rse/oer-001-sparqling-archaeology): axial hex coordinates with cube
// rounding, latitude corrected against the mean latitude of the points so cells
// stay roughly equal-area over the corpus's 10 degrees of latitude. Binning runs
// in the browser on whatever is currently filtered, not once at build time.
const HEX = (function () {
  const RAMP = ["#e7e6d4", "#bccbaa", "#84ae9a", "#4f8b8d", "#2b5f6b"];
  let ky = 1;

  function setLatitude(meanLat) { ky = 1 / Math.cos(meanLat * Math.PI / 180); }

  function key(lon, lat, size) {
    const x = lon, y = lat * ky;
    const q = (2 / 3) * x / size;
    const r = (-1 / 3) * x / size + (Math.sqrt(3) / 3) * y / size;
    let cx = q, cz = r, cy = -cx - cz;
    let rx = Math.round(cx), ry = Math.round(cy), rz = Math.round(cz);
    const dx = Math.abs(rx - cx), dy = Math.abs(ry - cy), dz = Math.abs(rz - cz);
    if (dx > dy && dx > dz) rx = -ry - rz;
    else if (dy > dz) ry = -rx - rz;
    else rz = -rx - ry;
    return rx + "," + rz;
  }

  function polygon(q, r, size) {
    const cx = size * 1.5 * q;
    const cy = size * Math.sqrt(3) * (r + q / 2);
    const out = [];
    for (let i = 0; i < 6; i++) {
      const a = 60 * i * Math.PI / 180;
      out.push([(cy + size * Math.sin(a)) / ky, cx + size * Math.cos(a)]);
    }
    return out;
  }

  // Two ways of cutting the counts into five steps.
  //
  //   linear  the notebook's scheme: equal-width bands over 1..max
  //   log     equal-ratio bands
  //
  // Linear is faithful to the original but unreadable on this corpus: the
  // findspots are so concentrated in Kerry and Cork that ~91% of cells fall in
  // the palest band and the map goes flat. Counts this skewed (median 1-2,
  // maximum 25-81 depending on cell size) are what log binning is for, so that
  // is the default here; linear stays available for comparison.
  function edges(maxN, scale) {
    const n = RAMP.length, out = [];
    for (let i = 0; i < n; i++) {
      out.push(scale === "log"
        ? Math.max(1, Math.round(Math.pow(maxN, (i + 1) / n)))
        : Math.ceil((i + 1) / n * maxN));
    }
    out[n - 1] = maxN;
    return out;
  }

  function bandOf(count, maxN, scale) {
    if (maxN <= 1) return 0;
    const t = scale === "log"
      ? Math.log(count) / Math.log(maxN)
      : (count - 1) / maxN;
    return Math.min(RAMP.length - 1, Math.floor(t * RAMP.length));
  }

  // Integer count ranges per ramp step, so the legend never claims a band the
  // data cannot fill (max 3 stones must not read as "1-5").
  function bands(maxN, scale) {
    const out = [];
    let prev = 1;
    edges(maxN, scale).forEach((edge, i) => {
      if (edge < prev) return;
      out.push({ colour: RAMP[i], label: edge === prev ? String(prev) : prev + "\u2013" + edge });
      prev = edge + 1;
    });
    return out;
  }

  function build(points, size, noun, scale) {
    scale = scale || "log";
    const counts = {};
    for (const [lon, lat] of points) {
      const k = key(lon, lat, size);
      counts[k] = (counts[k] || 0) + 1;
    }
    const values = Object.values(counts);
    const maxN = values.length ? Math.max.apply(null, values) : 1;
    const layer = L.layerGroup();
    for (const k in counts) {
      const [q, r] = k.split(",").map(Number);
      const n = counts[k];
      L.polygon(polygon(q, r, size), {
        color: "#2b3a37", weight: 0.7,
        fillColor: RAMP[bandOf(n, maxN, scale)], fillOpacity: 0.75
      }).bindTooltip("<b>" + n + "</b> " + noun + (n !== 1 ? "s" : ""), { sticky: true })
        .addTo(layer);
    }
    return { layer, legend: bands(maxN, scale), cells: Object.keys(counts).length };
  }

  return { setLatitude, build };
})();

function makeLegend(map) {
  const control = L.control({ position: "bottomright" });
  control.onAdd = function () {
    const div = L.DomUtil.create("div", "hex-legend");
    div.innerHTML = control._html || "";
    return div;
  };
  control.set = function (title, bands) {
    control._html = "<b>" + title + "</b><br>" + bands.map(b =>
      '<span class="sw" style="background:' + b.colour + '"></span>' + b.label).join("<br>");
    if (control._container) control._container.innerHTML = control._html;
  };
  return control;
}
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
__NAV__
      <div class="tally"><b id="count">0</b><span id="countLabel">stones shown</span></div>

      <label class="field" for="q">Search name or identifier</label>
      <input type="search" id="q" placeholder="Ballintaggart, CIIC 55, I-COR-001…" autocomplete="off">

      <fieldset id="countries"><legend class="field">Country</legend></fieldset>

      <fieldset>
        <legend class="field">Certainty</legend>
        <label class="opt"><input type="checkbox" id="onlyVague"> Only hedged findspots
          <span class="n" id="vagueN"></span></label>
      </fieldset>

      <p class="field" style="margin-top:20px">Display</p>
      <div class="seg" id="mode">
        <label><input type="radio" name="mode" value="points" checked><span>Points</span></label>
        <label><input type="radio" name="mode" value="density"><span>Density</span></label>
      </div>
      <div class="seg" id="hexsize">
        <label><input type="radio" name="hex" value="0.5"><span>Coarse</span></label>
        <label><input type="radio" name="hex" value="0.25" checked><span>Medium</span></label>
        <label><input type="radio" name="hex" value="0.12"><span>Fine</span></label>
      </div>
      <div class="seg" id="hexscale">
        <label><input type="radio" name="scale" value="log" checked><span>Log</span></label>
        <label><input type="radio" name="scale" value="linear"><span>Linear</span></label>
      </div>

      <p class="note">Dashed rings mark findspots the editors hedged — either
      <code>@cert="low"</code> on <code>&lt;geo&gt;</code> or a qualifier such as
      “approximate” written into the coordinate string. In the graph these carry
      <code>ogham:geoStatus</code>; the weight over them is added in axis 2.</p>

      <details>
        <summary id="missingSummary">Records without coordinates</summary>
        <ul id="missingList"></ul>
      </details>

      <p class="dl" style="display:flex;gap:8px;margin-bottom:6px">
        <button class="btn" id="dl-svg" type="button">Download SVG</button>
        <button class="btn" id="dl-jpg" type="button">Download JPG</button>
      </p>
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
addMapControls(map);
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
  scene.slug = "findspots";
  scene.title = [...document.querySelectorAll(".cc:checked")].length === 6 && !q.value.trim()
              ? "" : "filtered";
  scene.points = keep.map(p => ({lat:p.lat, lon:p.lon,
                                 colour:colourFor(p.country), vague:!!p.vague}));
  showOn(map, keep.map(p => [p.lon, p.lat]), keep.map(p => p._m),
         "stone", "Stones per cell");
  document.getElementById("count").textContent = keep.length;
  document.getElementById("countLabel").textContent = keep.length === 1 ? "stone shown" : "stones shown";
}
const redraw = apply;

// --- points vs. density -------------------------------------------------------
const hexGroup = L.layerGroup();
const hexLegend = makeLegend(map);
let displayMode = "points";
let hexSize = 0.25;
let hexScale = "log";

function showOn(map_, coords, markers, noun, title){
  scene.noun = noun;
  scene.legendTitle = title;
  // the export draws the scene, so it must hold only what is actually displayed
  if (displayMode !== "points") scene.points = [];
  if (displayMode === "points"){
    map.removeLayer(hexGroup);
    hexLegend.remove();
    if (!map.hasLayer(cluster)) map.addLayer(cluster);
    cluster.clearLayers();
    cluster.addLayers(markers);
    scene.hexes = [];
    scene.legend = null;
  } else {
    map.removeLayer(cluster);
    hexGroup.clearLayers();
    if (coords.length){
      HEX.setLatitude(coords.reduce((a,c) => a + c[1], 0) / coords.length);
      const built = HEX.build(coords, hexSize, noun, hexScale);
      built.layer.eachLayer(l => hexGroup.addLayer(l));
      hexLegend.set(title, built.legend);
      hexLegend.addTo(map);
      scene.hexes = built.layer.getLayers().map(l => ({
        ring: l.getLatLngs()[0].map(p => [p.lat, p.lng]),
        fill: l.options.fillColor
      }));
      scene.legend = built.legend;
    } else {
      hexLegend.remove();
      scene.hexes = [];
      scene.legend = null;
    }
    if (!map.hasLayer(hexGroup)) map.addLayer(hexGroup);
  }
}

document.querySelectorAll("#mode input").forEach(i => i.addEventListener("change", () => {
  displayMode = i.value;
  ["hexsize", "hexscale"].forEach(id =>
    document.getElementById(id).classList.toggle("on", displayMode === "density"));
  redraw();
}));
document.querySelectorAll("#hexsize input").forEach(i => i.addEventListener("change", () => {
  hexSize = parseFloat(i.value);
  if (displayMode === "density") redraw();
}));
document.querySelectorAll("#hexscale input").forEach(i => i.addEventListener("change", () => {
  hexScale = i.value;
  if (displayMode === "density") redraw();
}));

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

HEAD_LANDING = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Linked Open Ogham — TEI/EpiDoc to CIDOC CRM</title>
<meta name="description" content="The OG(H)AM TEI/EpiDoc editions crosswalked to CIDOC CRM: findspot map, formulaic vocabulary, RDF.">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Vollkorn:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>__CSS__</style>
</head>
<body class="landing">
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
__NAV__
      <div class="tally"><b id="count">0</b><span id="countLabel">stones shown</span></div>

      <div id="gloss" class="gloss"></div>

      <div class="legend">
        <span><i class="pin" style="width:11px;height:11px;background:#3f7d8c;
          border:1.6px solid rgba(19,28,27,.7)"></i> in the current edition</span>
        <span><i class="pin vague" style="width:11px;height:11px;
          border:1.6px dashed #b07d2b"></i> only in an older reading</span>
      </div>

      <p class="field" style="margin-top:20px">Display</p>
      <div class="seg" id="mode">
        <label><input type="radio" name="mode" value="points" checked><span>Points</span></label>
        <label><input type="radio" name="mode" value="density"><span>Density</span></label>
      </div>
      <div class="seg" id="hexsize">
        <label><input type="radio" name="hex" value="0.5"><span>Coarse</span></label>
        <label><input type="radio" name="hex" value="0.25" checked><span>Medium</span></label>
        <label><input type="radio" name="hex" value="0.12"><span>Fine</span></label>
      </div>
      <div class="seg" id="hexscale">
        <label><input type="radio" name="scale" value="log" checked><span>Log</span></label>
        <label><input type="radio" name="scale" value="linear"><span>Linear</span></label>
      </div>

      <label class="field" for="q">Filter the vocabulary</label>
      <input type="search" id="q" placeholder="maqi, son, hound…" autocomplete="off">

      <div class="wordlist" id="wordlist"></div>

      <p class="note">Word list from
      <a href="https://github.com/LinkedOpenOgham/o3d-epidoc-extractor">o3d-epidoc-extractor</a>
      (Homburg &amp; Thiery, DHd 2020), after McManus 1991. <b>Name elements are
      matched as substrings</b>, which is that project's semantics and is not
      precise: short elements such as CON or VIR also fire inside unrelated names.
      Each hit records which mode produced it.</p>

      <p class="dl" style="display:flex;gap:8px;margin-bottom:6px">
        <button class="btn" id="dl-svg" type="button">Download SVG</button>
        <button class="btn" id="dl-jpg" type="button">Download JPG</button>
      </p>
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

HEAD_READINGS = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Linked Open Ogham — editorial disagreement</title>
<meta name="description" content="Ogham stones carrying more than one reading, and how far the current edition sits from earlier ones.">
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
__NAV__
      <div class="tally"><b id="count">0</b><span id="countLabel">stones shown</span></div>

      <div id="gloss" class="gloss"></div>

      <div class="legend">
        <span><i class="pin" style="width:11px;height:11px;background:#3f7d8c;
          border:1.6px solid rgba(19,28,27,.7)"></i> in the current edition</span>
        <span><i class="pin vague" style="width:11px;height:11px;
          border:1.6px dashed #b07d2b"></i> only in an older reading</span>
      </div>

      <p class="field" style="margin-top:20px">Display</p>
      <div class="seg" id="mode">
        <label><input type="radio" name="mode" value="points" checked><span>Points</span></label>
        <label><input type="radio" name="mode" value="density"><span>Density</span></label>
      </div>
      <div class="seg" id="hexsize">
        <label><input type="radio" name="hex" value="0.5"><span>Coarse</span></label>
        <label><input type="radio" name="hex" value="0.25" checked><span>Medium</span></label>
        <label><input type="radio" name="hex" value="0.12"><span>Fine</span></label>
      </div>
      <div class="seg" id="hexscale">
        <label><input type="radio" name="scale" value="log" checked><span>Log</span></label>
        <label><input type="radio" name="scale" value="linear"><span>Linear</span></label>
      </div>

      <label class="field" for="q">Filter the vocabulary</label>
      <input type="search" id="q" placeholder="maqi, son, hound…" autocomplete="off">

      <div class="wordlist" id="wordlist"></div>

      <p class="note">Word list from
      <a href="https://github.com/LinkedOpenOgham/o3d-epidoc-extractor">o3d-epidoc-extractor</a>
      (Homburg &amp; Thiery, DHd 2020), after McManus 1991. <b>Name elements are
      matched as substrings</b>, which is that project's semantics and is not
      precise: short elements such as CON or VIR also fire inside unrelated names.
      Each hit records which mode produced it.</p>

      <p class="dl" style="display:flex;gap:8px;margin-bottom:6px">
        <button class="btn" id="dl-svg" type="button">Download SVG</button>
        <button class="btn" id="dl-jpg" type="button">Download JPG</button>
      </p>
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

READINGS_JS = r"""
const STONES = __STONES__;
const BANDS  = __BANDS__;

const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const BAND_COLOUR = {"identical":"#8d9a97", "close":"#9aab3f",
                     "diverging":"#b07d2b", "far apart":"#b0413e"};
const BAND_ORDER = ["far apart","diverging","close","identical"];

const map = L.map("map", {zoomControl:false}).setView([53.6,-7.5], 6);
addMapControls(map);
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

function icon(colour){
  const d = 13;
  return L.divIcon({className:"", iconSize:[d,d], iconAnchor:[d/2,d/2],
    html:`<div class="pin" style="width:${d}px;height:${d}px;background:${colour};`
       + `border-color:rgba(19,28,27,.7)"></div>`});
}

// A token that one reading has and the other does not is what a reader is looking
// for, so it is marked rather than left to be spotted.
function tokens(text, missing){
  const gone = new Set(missing);
  return esc(text).split(/\s+/).map(t =>
    gone.has(t) ? `<mark>${t}</mark>` : t).join(" ");
}

function popup(s){
  const head = s.pairs[0];
  const rows = s.pairs.map(p => `
    <p class="rdg"><em>${esc(p.editor)}</em>
      <span class="badge" style="background:${BAND_COLOUR[p.band]}22;color:${BAND_COLOUR[p.band]}">
        ${esc(p.band)} · ${p.sim.toFixed(2)}</span><br>
      ${tokens(p.oth, p.onlyOth)}
      ${p.gained.length ? `<br><span class="gain">+ ${p.gained.map(esc).join(" ")}</span>` : ""}
      ${p.lost.length ? `<br><span class="loss">\u2212 ${p.lost.map(esc).join(" ")}</span>` : ""}
    </p>`).join("");
  return `<div class="pop">
    <h2>${esc(s.title || s.id)}</h2>
    <div class="where">${esc([s.county, s.country].filter(Boolean).join(", "))}
      ${s.ciic ? " · CIIC " + esc(s.ciic) : ""}</div>
    <p class="rdg"><em>current OG(H)AM edition</em><br>${tokens(head.cur, head.onlyCur)}</p>
    <hr style="border:0;border-top:1px solid #33433f;margin:9px 0">
    ${rows}
    <div class="links"><a href="findspots.html">on the findspot map</a>
      <a href="words.html">formulaic words</a></div>
  </div>`;
}

let bandFilter = null, editorFilter = null;

function matches(s){
  if (bandFilter && s.band !== bandFilter) return false;
  if (editorFilter && !s.editors.includes(editorFilter)) return false;
  if (document.getElementById("onlyFormula").checked && !s.formula) return false;
  return true;
}

function draw(){
  const keep = STONES.filter(matches);
  scene.slug = "readings";
  scene.title = [bandFilter, editorFilter].filter(Boolean).join(" ") || "";
  scene.points = keep.map(s => ({lat:s.lat, lon:s.lon,
                                 colour:BAND_COLOUR[s.band] || "#8d9a97", vague:false}));
  const markers = keep.map(s =>
    L.marker([s.lat, s.lon], {icon:icon(BAND_COLOUR[s.band]), title:s.title || s.id})
     .bindPopup(() => popup(s), {maxWidth:360}));
  showOn(map, keep.map(s => [s.lon, s.lat]), markers, "stone", "Stones per cell");
  document.getElementById("count").textContent = keep.length;
  document.getElementById("countLabel").textContent =
    keep.length === 1 ? "stone shown" : "stones shown";
  if (keep.length) map.fitBounds(L.latLngBounds(keep.map(s => [s.lat, s.lon])).pad(0.08));
}

function radioList(box, items, current, onPick, allLabel){
  box.innerHTML = "";
  const add = (value, label, gloss, n, checked) => {
    const l = document.createElement("label");
    l.className = "word";
    l.innerHTML = `<input type="radio" name="${box.id}" ${checked ? "checked" : ""}>`
                + (gloss === null ? `<b>${esc(label)}</b><span class="tr"></span>`
                   : `<span class="dot" style="background:${gloss}"></span>`
                     + `<b>${esc(label)}</b><span class="tr"></span>`)
                + `<span class="n">${n}</span>`;
    l.querySelector("input").addEventListener("change", () => { onPick(value); });
    box.appendChild(l);
  };
  add(null, allLabel, null, items.reduce((a, i) => a + i.n, 0), current === null);
  items.forEach(i => add(i.value, i.label, i.colour ?? null, i.n, current === i.value));
}

function buildLists(){
  radioList(document.getElementById("bandlist"),
    BAND_ORDER.filter(b => BANDS.bands[b]).map(b => ({
      value:b, label:b, n:BANDS.bands[b], colour:BAND_COLOUR[b] })),
    bandFilter, v => { bandFilter = v; draw(); buildLists(); }, "Any distance");
  radioList(document.getElementById("editorlist"),
    Object.keys(BANDS.editors).sort((a,b) => BANDS.editors[b] - BANDS.editors[a]
      || a.localeCompare(b)).map(e => ({ value:e, label:e, n:BANDS.editors[e] })),
    editorFilter, v => { editorFilter = v; draw(); buildLists(); }, "Any editor");
}

document.getElementById("formulaN").textContent = STONES.filter(s => s.formula).length;
document.getElementById("onlyFormula").addEventListener("change", draw);
const redraw = draw;

// --- points vs. density -------------------------------------------------------
const hexGroup = L.layerGroup();
const hexLegend = makeLegend(map);
let displayMode = "points";
let hexSize = 0.25;
let hexScale = "log";

function showOn(map_, coords, markers, noun, title){
  scene.noun = noun;
  scene.legendTitle = title;
  // the export draws the scene, so it must hold only what is actually displayed
  if (displayMode !== "points") scene.points = [];
  if (displayMode === "points"){
    map.removeLayer(hexGroup);
    hexLegend.remove();
    if (!map.hasLayer(cluster)) map.addLayer(cluster);
    cluster.clearLayers();
    cluster.addLayers(markers);
    scene.hexes = [];
    scene.legend = null;
  } else {
    map.removeLayer(cluster);
    hexGroup.clearLayers();
    if (coords.length){
      HEX.setLatitude(coords.reduce((a,c) => a + c[1], 0) / coords.length);
      const built = HEX.build(coords, hexSize, noun, hexScale);
      built.layer.eachLayer(l => hexGroup.addLayer(l));
      hexLegend.set(title, built.legend);
      hexLegend.addTo(map);
      scene.hexes = built.layer.getLayers().map(l => ({
        ring: l.getLatLngs()[0].map(p => [p.lat, p.lng]),
        fill: l.options.fillColor
      }));
      scene.legend = built.legend;
    } else {
      hexLegend.remove();
      scene.hexes = [];
      scene.legend = null;
    }
    if (!map.hasLayer(hexGroup)) map.addLayer(hexGroup);
  }
}

document.querySelectorAll("#mode input").forEach(i => i.addEventListener("change", () => {
  displayMode = i.value;
  ["hexsize", "hexscale"].forEach(id =>
    document.getElementById(id).classList.toggle("on", displayMode === "density"));
  redraw();
}));
document.querySelectorAll("#hexsize input").forEach(i => i.addEventListener("change", () => {
  hexSize = parseFloat(i.value);
  if (displayMode === "density") redraw();
}));
document.querySelectorAll("#hexscale input").forEach(i => i.addEventListener("change", () => {
  hexScale = i.value;
  if (displayMode === "density") redraw();
}));

buildLists();
draw();
"""

READINGS_BODY = r"""<div id="app">
  <aside id="side">
    <header>
      <!-- MAP on a stemline. M = aicme Muine 1, one stroke crossing the stemline
           diagonally. A = aicme Ailme 1, one stroke crossing it perpendicularly.
           P has no orthodox letter: this is the forfid peith (U+169A), drawn as
           beithe with the crossbar that softens it. -->
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
      <h1>Where the editors disagree</h1>
      <p class="sub">Stones whose inscription has been read more than one way, and how
      far apart those readings are.</p>
    </header>
    <div class="scroll">
__NAV__
      <div class="tally"><b id="count">0</b><span id="countLabel">stones shown</span></div>

      <p class="field">Distance from the current edition</p>
      <div class="wordlist" id="bandlist"></div>

      <fieldset>
        <legend class="field">What is at stake</legend>
        <label class="opt"><input type="checkbox" id="onlyFormula"> Only where a formulaic
          word is gained or lost <span class="n" id="formulaN"></span></label>
      </fieldset>

      <p class="field" style="margin-top:20px">Display</p>
      <div class="seg" id="mode">
        <label><input type="radio" name="mode" value="points" checked><span>Points</span></label>
        <label><input type="radio" name="mode" value="density"><span>Density</span></label>
      </div>
      <div class="seg" id="hexsize">
        <label><input type="radio" name="hex" value="0.5"><span>Coarse</span></label>
        <label><input type="radio" name="hex" value="0.25" checked><span>Medium</span></label>
        <label><input type="radio" name="hex" value="0.12"><span>Fine</span></label>
      </div>
      <div class="seg" id="hexscale">
        <label><input type="radio" name="scale" value="log" checked><span>Log</span></label>
        <label><input type="radio" name="scale" value="linear"><span>Linear</span></label>
      </div>

      <label class="field" for="q" style="margin-top:22px">Editor</label>
      <div class="wordlist" id="editorlist"></div>

      <p class="note">The similarity is a character-level comparison of the two
      readings after editorial marks are stripped, and it is an <b>ordering aid, not
      a verdict</b>: two readings can score 0.83 and still differ over everything
      that matters. Readings are only compared within one script, so an ogham
      reading is never measured against a Roman-script one.</p>

      <p class="dl" style="display:flex;gap:8px;margin-bottom:6px">
        <button class="btn" id="dl-svg" type="button">Download SVG</button>
        <button class="btn" id="dl-jpg" type="button">Download JPG</button>
      </p>
      <p class="dl">
        <a href="readings.csv" download>Download comparisons (CSV)</a><br>
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
addMapControls(map);
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
      <a href="findspots.html">on the findspot map</a>
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
  const markers = keep.map(s => {
    const cur = isCurrent(s, selected);
    const m = L.marker([s.lat, s.lon], {icon:icon(cur), title:s.title || s.id});
    m.bindPopup(() => popup(s, selected), {maxWidth:340});
    return m;
  });
  scene.slug = "words";
  scene.title = selected === null ? "all words" : WORDS[selected].word;
  scene.points = keep.map(s => ({lat:s.lat, lon:s.lon,
                                 colour:isCurrent(s, selected) ? CURRENT : OLDER,
                                 vague:!isCurrent(s, selected)}));
  showOn(map, keep.map(s => [s.lon, s.lat]), markers, "stone",
         selected === null ? "Stones per cell" : WORDS[selected].word + " per cell");
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

const redraw = draw;

// --- points vs. density -------------------------------------------------------
const hexGroup = L.layerGroup();
const hexLegend = makeLegend(map);
let displayMode = "points";
let hexSize = 0.25;
let hexScale = "log";

function showOn(map_, coords, markers, noun, title){
  scene.noun = noun;
  scene.legendTitle = title;
  // the export draws the scene, so it must hold only what is actually displayed
  if (displayMode !== "points") scene.points = [];
  if (displayMode === "points"){
    map.removeLayer(hexGroup);
    hexLegend.remove();
    if (!map.hasLayer(cluster)) map.addLayer(cluster);
    cluster.clearLayers();
    cluster.addLayers(markers);
    scene.hexes = [];
    scene.legend = null;
  } else {
    map.removeLayer(cluster);
    hexGroup.clearLayers();
    if (coords.length){
      HEX.setLatitude(coords.reduce((a,c) => a + c[1], 0) / coords.length);
      const built = HEX.build(coords, hexSize, noun, hexScale);
      built.layer.eachLayer(l => hexGroup.addLayer(l));
      hexLegend.set(title, built.legend);
      hexLegend.addTo(map);
      scene.hexes = built.layer.getLayers().map(l => ({
        ring: l.getLatLngs()[0].map(p => [p.lat, p.lng]),
        fill: l.options.fillColor
      }));
      scene.legend = built.legend;
    } else {
      hexLegend.remove();
      scene.hexes = [];
      scene.legend = null;
    }
    if (!map.hasLayer(hexGroup)) map.addLayer(hexGroup);
  }
}

document.querySelectorAll("#mode input").forEach(i => i.addEventListener("change", () => {
  displayMode = i.value;
  ["hexsize", "hexscale"].forEach(id =>
    document.getElementById(id).classList.toggle("on", displayMode === "density"));
  redraw();
}));
document.querySelectorAll("#hexsize input").forEach(i => i.addEventListener("change", () => {
  hexSize = parseFloat(i.value);
  if (displayMode === "density") redraw();
}));
document.querySelectorAll("#hexscale input").forEach(i => i.addEventListener("change", () => {
  hexScale = i.value;
  if (displayMode === "density") redraw();
}));

document.getElementById("q").addEventListener("input", buildList);
buildList();
draw();
"""


# --- the site ------------------------------------------------------------------
# One entry per page. The navigation and the landing page are both generated from
# this list, so adding a view later means adding a builder and one entry here --
# not editing three templates.
PAGES = [
    {
        "slug": "findspots.html",
        "nav": "Findspots",
        "title": "Findspot map",
        "blurb": "Where the inscribed stones were found, read out of "
                 "<code>&lt;origPlace&gt;/&lt;geo&gt;</code> and crosswalked to CIDOC CRM "
                 "<code>E53_Place</code>. Filterable by country; findspots the editors "
                 "hedged are drawn as dashed rings.",
    },
    {
        "slug": "words.html",
        "nav": "Formulaic words",
        "title": "Formulaic words",
        "blurb": "McManus's formulaic vocabulary matched against every reading of every "
                 "inscription — so a word belongs to a reading and its editor, not to a "
                 "stone. Picks up the DHd 2020 extractor on the successor corpus.",
    },
    {
        "slug": "readings.html",
        "nav": "Disagreement",
        "title": "Where the editors disagree",
        "blurb": "Stones that carry more than one reading, coloured by how far the "
                 "current edition sits from what an earlier editor saw. Filterable by "
                 "editor, and by whether a formulaic word is what is at stake.",
    },
]


def nav_html(active_slug: str) -> str:
    """Navigation shared by the map pages; the landing page navigates by its cards."""
    links = ['      <nav>', '        <a href="index.html">Overview</a>']
    for page in PAGES:
        current = ' aria-current="page"' if page["slug"] == active_slug else ""
        links.append(f'        <a href="{page["slug"]}"{current}>{page["nav"]}</a>')
    links.append('      </nav>')
    return "\n".join(links)


LANDING = r"""<div class="wrap">
  <!-- MAP on a stemline: M = aicme Muine 1 (diagonal), A = aicme Ailme 1
       (perpendicular), P = the forfid peith, beithe with its softening crossbar.
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
  <h1>Linked Open Ogham</h1>
  <p class="lede">The TEI/EpiDoc editions of the OG(H)AM corpus, crosswalked to
  <b>CIDOC CRM 7.1.3</b> and <b>CRMtex</b>. These pages are the browsable side of that
  graph: each one is generated from the same parse as the RDF, so a map and the
  triples behind it cannot disagree.</p>
  <p class="byline">Axis 1 of the Linked Open Ogham crosswalk ·
  <a href="https://github.com/LinkedOpenOgham/tei--epidoc-crosswalk">source and RDF on GitHub</a></p>

  <div class="cards">__CARDS__</div>

  <p class="section">Data</p>
  <div class="files">__FILES__</div>

  <p class="section">Provenance</p>
  <p class="foot">__FOOT__</p>
</div>

"""


def _card(page: dict, figures: list[tuple[str, str]]) -> str:
    figs = "".join(f'<span class="fig"><b>{value}</b>{label}</span>'
                   for value, label in figures)
    return (f'<a class="card" href="{page["slug"]}">\n'
            f'      <h2>{page["title"]}</h2>\n'
            f'      <p>{page["blurb"]}</p>\n'
            f'      <div class="figs">{figs}</div>\n    </a>')


def build_readings(analysis: list[dict], place_records: list[dict], summary: dict,
                   docs: Path, root: Path | None = None,
                   provenance: dict | None = None) -> dict:
    """docs/readings.html -- stones with competing readings, by how far apart."""
    docs.mkdir(parents=True, exist_ok=True)
    coords = {r["ogham_id"]: r for r in place_records if r.get("lat") is not None}

    stones, editors, bands = [], {}, {}
    for rec in analysis:
        place = coords.get(rec["ogham_id"])
        if place is None:
            continue
        stones.append({
            "id": rec["ogham_id"], "title": rec["title"], "ciic": rec["ciic"],
            "county": place.get("pn_county", ""), "country": place.get("pn_country", ""),
            "lat": place["lat"], "lon": place["lon"],
            "band": rec["band"], "sim": rec["min_similarity"],
            "editors": rec["editors"], "formula": rec["formula_at_stake"],
            "pairs": [{"editor": p["editor"], "sim": p["similarity"], "band": p["band"],
                       "cur": p["current_norm"], "oth": p["other_norm"],
                       "onlyCur": p["only_current"], "onlyOth": p["only_other"],
                       "gained": p["formula_gained"], "lost": p["formula_lost"]}
                      for p in rec["pairs"]],
        })
        bands[rec["band"]] = bands.get(rec["band"], 0) + 1
        for e in rec["editors"]:
            editors[e] = editors.get(e, 0) + 1

    html = (_page(HEAD_READINGS, READINGS_BODY, READINGS_JS)
            .replace("__NAV__", nav_html("readings.html"))
            .replace("__STONES__", json.dumps(stones, ensure_ascii=False, separators=(",", ":")))
            .replace("__BANDS__", json.dumps({"bands": bands, "editors": editors},
                                             ensure_ascii=False, separators=(",", ":")))
            .replace("__BUILT__", dt.date.today().isoformat())
            .replace("__PROV__", _provenance_html(provenance or {})))
    (docs / "readings.html").write_text(html, encoding="utf-8")

    rel = (lambda x: x.relative_to(root)) if root else (lambda x: x)
    size = (docs / "readings.html").stat().st_size / 1024
    print(f"  -> wrote {rel(docs / 'readings.html')} ({len(stones)} stones, "
          f"{len(editors)} editors, {size:.0f} KB)")
    return {"stones": len(stones), "editors": len(editors)}


def build_landing(docs: Path, figures: dict[str, list[tuple[str, str]]],
                  root: Path | None = None, provenance: dict | None = None) -> None:
    """docs/index.html -- the way in, and the place a new view gets announced."""
    docs.mkdir(parents=True, exist_ok=True)
    cards = "\n    ".join(_card(page, figures.get(page["slug"], [])) for page in PAGES)

    prov = provenance or {}
    files = [
        ("places.geojson", "every resolved findspot, WGS84"),
        ("words.csv", "every word occurrence, per reading"),
    ]
    files_html = "\n    ".join(
        f'<div><a href="{name}" download>{name}</a> <span>— {desc}</span></div>'
        for name, desc in files if (docs / name).exists())
    files_html += ('\n    <div><a href="https://github.com/LinkedOpenOgham/'
                   'tei--epidoc-crosswalk/tree/main/out">out/*.ttl</a> '
                   '<span>— the CIDOC CRM graphs themselves</span></div>')

    if prov.get("commit"):
        tree = prov.get("tree_url", "")
        foot = (f'Built from OG(H)AM corpus commit '
                f'<a href="{tree}" target="_blank" rel="noopener"><code>{prov["commit"][:7]}</code></a> '
                f'({(prov.get("commit_date") or "")[:10]}), {prov.get("edition_count", "?")} editions. '
                f'Generated {dt.date.today().isoformat()}.<br>'
                f'Editions &copy; the OG(H)AM project, CC BY 4.0. '
                f'Word list from <a href="https://github.com/LinkedOpenOgham/o3d-epidoc-extractor">'
                f'o3d-epidoc-extractor</a>, MIT.')
    else:
        foot = (f'Generated {dt.date.today().isoformat()}. Editions &copy; the OG(H)AM '
                f'project, CC BY 4.0.')

    html = (_page(HEAD_LANDING, LANDING, "")
            .replace("__CARDS__", cards)
            .replace("__FILES__", files_html)
            .replace("__FOOT__", foot))
    (docs / "index.html").write_text(html, encoding="utf-8")
    rel = (lambda x: x.relative_to(root)) if root else (lambda x: x)
    print(f"  -> wrote {rel(docs / 'index.html')} ({len(PAGES)} views linked)")


def _page(head: str, body: str, js: str) -> str:
    """Assemble a page from the shared shell. Empty js means no map libraries."""
    shell = head.replace("__CSS__", CSS) + body
    # EXPORT_JS declares `scene`, which the page scripts write to as soon as they
    # first draw, so it has to be in scope before them.
    return shell + SCRIPTS + MAPUI_JS + HEX_JS + EXPORT_JS + js + FOOT if js else shell + "</body>\n</html>\n"


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
            .replace("__NAV__", nav_html("findspots.html"))
            .replace("__DATA__", json.dumps(mapped, ensure_ascii=False, separators=(",", ":")))
            .replace("__MISSING__", json.dumps(missing, ensure_ascii=False, separators=(",", ":")))
            .replace("__BUILT__", dt.date.today().isoformat())
            .replace("__PROV__", _provenance_html(provenance or {})))
    (docs / "findspots.html").write_text(html, encoding="utf-8")

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
    size = (docs / "findspots.html").stat().st_size / 1024
    print(f"  -> wrote {rel(docs / 'findspots.html')} ({len(mapped)} points, {size:.0f} KB)")
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
            .replace("__NAV__", nav_html("words.html"))
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
