from __future__ import annotations

import argparse
import json
import mimetypes
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from .common import DEFAULT_MODEL, clean
from .db import connect
from .evidence_pack import build_pack, markdown_report, source_label
from .search import hybrid_search, keyword_search, snippet
from .embeddings import vector_search
from .summary import source_summary as build_source_summary


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DisclosureArchive Search</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f7f4;
      --panel: #ffffff;
      --ink: #171a1c;
      --muted: #5e666a;
      --line: #d7d9d4;
      --accent: #0f766e;
      --accent-2: #9a5b00;
      --soft: #e8f1ef;
      --warn: #fff3d8;
      --code: #f2f3ef;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      border-bottom: 1px solid var(--line);
      background: #fbfbf8;
    }
    .wrap {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
    }
    .topbar {
      min-height: 68px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
    }
    h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 720;
      letter-spacing: 0;
    }
    .health {
      color: var(--muted);
      font-size: 12px;
      text-align: right;
    }
    main {
      padding: 22px 0 34px;
    }
    .searchbar {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 108px;
      gap: 10px;
      align-items: stretch;
    }
    input, select, button {
      font: inherit;
    }
    input[type="search"] {
      width: 100%;
      height: 44px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 13px;
      background: var(--panel);
      color: var(--ink);
    }
    button {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      color: var(--ink);
      min-height: 36px;
      cursor: pointer;
    }
    button.primary {
      border-color: var(--accent);
      background: var(--accent);
      color: #fff;
      font-weight: 650;
    }
    button:hover { filter: brightness(0.98); }
    a {
      color: var(--accent);
      font-weight: 650;
      text-decoration: none;
    }
    a:hover { text-decoration: underline; }
    .controls {
      margin-top: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }
    .seg {
      display: inline-grid;
      grid-template-columns: repeat(3, 92px);
      border: 1px solid var(--line);
      border-radius: 6px;
      overflow: hidden;
      background: var(--panel);
    }
    .seg button {
      border: 0;
      border-radius: 0;
      min-height: 34px;
      color: var(--muted);
    }
    .seg button.active {
      background: var(--soft);
      color: var(--accent);
      font-weight: 700;
    }
    select {
      height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      padding: 0 10px;
      color: var(--ink);
    }
    .grid {
      margin-top: 18px;
      display: block;
    }
    .summary, .side, .result, .empty {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .summary {
      display: none;
      padding: 16px;
      margin-bottom: 14px;
    }
    .summary h2, .side h2 {
      margin: 0 0 10px;
      font-size: 15px;
      letter-spacing: 0;
    }
    .summary p {
      margin: 6px 0;
      color: var(--muted);
    }
    .summary ul {
      margin: 10px 0 0;
      padding-left: 18px;
    }
    .summary li { margin: 5px 0; }
    .result {
      padding: 0;
      margin-bottom: 12px;
      overflow: hidden;
    }
    .result-shell {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 220px;
      gap: 0;
      align-items: start;
    }
    .result-media {
      width: 220px;
      height: 180px;
      border-left: 1px solid var(--line);
      background: #eef1ed;
      display: flex;
      align-items: center;
      justify-content: center;
      align-self: start;
      position: sticky;
      top: 10px;
      overflow: hidden;
    }
    .result-media a { width: 100%; height: 100%; display: block; }
    .result-media img,
    .result-media video {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
      background: #101416;
    }
    .result-media .placeholder {
      color: var(--muted);
      font-size: 12px;
      padding: 12px;
      text-align: center;
    }
    .result-main {
      padding: 15px;
    }
    .result-head {
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: flex-start;
    }
    .result h3 {
      margin: 0;
      font-size: 16px;
      line-height: 1.25;
      letter-spacing: 0;
    }
    .score {
      display: none;
      white-space: nowrap;
      color: var(--muted);
      font-variant-numeric: tabular-nums;
      font-size: 12px;
    }
    .meta {
      margin-top: 8px;
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 2px 8px;
      background: #fafaf7;
      color: var(--muted);
      font-size: 12px;
    }
    .chip.debug {
      display: none;
    }
    .tags {
      margin-top: 10px;
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .tag {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 2px 8px;
      background: var(--soft);
      color: var(--accent);
      font-size: 12px;
      font-weight: 650;
    }
    .doc-summary {
      margin-top: 12px;
      color: #25292b;
    }
    .doc-summary p {
      margin: 0;
      overflow-wrap: anywhere;
    }
    .refs {
      margin-top: 8px;
      color: var(--muted);
      font-size: 12px;
    }
    .chip.ocr {
      background: var(--warn);
      color: #6f4100;
      border-color: #ead095;
    }
    .snippet {
      margin: 12px 0 0;
      color: #272b2e;
      overflow-wrap: anywhere;
    }
    .reader-summary {
      margin-top: 12px;
      padding: 11px 12px;
      border-left: 3px solid var(--accent);
      background: #f4f8f6;
      color: #222729;
      border-radius: 6px;
    }
    .reader-summary h4 {
      margin: 0 0 5px;
      font-size: 13px;
      letter-spacing: 0;
    }
    .reader-summary p {
      margin: 0;
      overflow-wrap: anywhere;
    }
    details.cleaned {
      margin-top: 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfbf8;
    }
    details.cleaned summary {
      cursor: pointer;
      padding: 8px 10px;
      color: var(--accent);
      font-weight: 650;
    }
    .cleaned-text {
      padding: 0 10px 10px;
      color: #272b2e;
      overflow-wrap: anywhere;
    }
    .source-summary {
      margin-top: 10px;
      border: 1px solid #cbd6d3;
      border-radius: 8px;
      background: #fbfbf8;
      overflow: hidden;
    }
    .source-summary-body {
      padding: 11px 12px;
      color: #25292b;
    }
    .source-summary-body h4 {
      margin: 0 0 8px;
      font-size: 14px;
      letter-spacing: 0;
    }
    .source-summary-body p {
      margin: 7px 0;
    }
    .source-summary-body ul {
      margin: 8px 0 0;
      padding-left: 18px;
    }
    .source-summary-body li {
      margin: 5px 0;
    }
    .source-summary-body .note {
      color: var(--muted);
      font-size: 12px;
    }
    .summary-progress {
      display: flex;
      align-items: center;
      gap: 9px;
      color: var(--muted);
      font-size: 13px;
    }
    .spinner {
      width: 16px;
      height: 16px;
      border: 2px solid #d8e1de;
      border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      flex: 0 0 auto;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    .links {
      margin-top: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .icon-button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 38px;
      height: 38px;
      padding: 0 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfbf8;
      color: var(--accent);
      text-decoration: none;
      cursor: pointer;
    }
    .icon-button:hover {
      text-decoration: none;
      filter: brightness(0.98);
      border-color: #b7c8c4;
      background: var(--soft);
    }
    .icon-button svg {
      width: 19px;
      height: 19px;
      stroke: currentColor;
      stroke-width: 2;
      fill: none;
      stroke-linecap: round;
      stroke-linejoin: round;
      pointer-events: none;
    }
    .source-button,
    .summary-button {
      gap: 7px;
      width: auto;
      font-weight: 700;
    }
    .media-strip {
      margin-top: 12px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
    }
    .media-preview {
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: #fbfbf8;
    }
    .media-preview img,
    .media-preview video {
      display: block;
      width: 100%;
      max-height: 240px;
      background: #101416;
      object-fit: contain;
    }
    .media-caption {
      padding: 7px 8px;
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    code, .path {
      font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
      font-size: 12px;
    }
    .path {
      margin-top: 10px;
      padding: 8px;
      background: var(--code);
      border-radius: 6px;
      color: #34383a;
      overflow-wrap: anywhere;
    }
    .side {
      padding: 14px;
      position: sticky;
      top: 12px;
    }
    .map {
      width: 100%;
      aspect-ratio: 1.8 / 1;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: linear-gradient(#f8fbfb, #eef4f2);
      margin-bottom: 14px;
      overflow: hidden;
    }
    .map svg {
      display: block;
      width: 100%;
      height: 100%;
    }
    .map-grid {
      stroke: #d8e1de;
      stroke-width: 0.5;
    }
    .map-point {
      fill: var(--accent-2);
      stroke: #fff;
      stroke-width: 1.6;
    }
    .map-labels {
      margin: -6px 0 16px;
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 12px;
    }
    .suggestions {
      display: grid;
      gap: 8px;
    }
    .suggestions button {
      text-align: left;
      padding: 9px 10px;
      min-height: 38px;
      border-color: #cbd6d3;
    }
    .pack-actions {
      margin-top: 16px;
      display: grid;
      gap: 8px;
    }
    textarea {
      width: 100%;
      min-height: 210px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      background: #fbfbf8;
      color: var(--ink);
      font: 12px/1.4 ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
    }
    .empty {
      padding: 18px;
      color: var(--muted);
    }
    .status {
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
      min-height: 20px;
    }
    @media (max-width: 860px) {
      .grid { display: block; }
      .result-shell { grid-template-columns: 1fr; }
      .result-media { width: 100%; height: 170px; border-left: 0; border-top: 1px solid var(--line); position: static; }
      .side { position: static; }
      .searchbar { grid-template-columns: 1fr; }
      .seg { grid-template-columns: repeat(3, 1fr); width: 100%; }
      .topbar { align-items: flex-start; flex-direction: column; padding: 14px 0; }
      .health { text-align: left; }
    }
  </style>
</head>
<body>
  <header>
    <div class="wrap topbar">
      <h1>DisclosureArchive Search</h1>
      <div class="health" id="health">Checking index...</div>
    </div>
  </header>
  <main class="wrap">
    <form id="searchForm" class="searchbar">
      <input id="query" type="search" autocomplete="off" spellcheck="true" value="flying discs flight service regulation 1949">
      <button class="primary" type="submit">Search</button>
    </form>
    <div class="controls">
      <div class="seg" role="group" aria-label="Search mode">
        <button type="button" data-mode="hybrid" class="active">Hybrid</button>
        <button type="button" data-mode="keyword">Keyword</button>
        <button type="button" data-mode="vector">Vector</button>
      </div>
      <select id="sourceKind" aria-label="Source kind">
        <option value="">All sources</option>
        <option value="media_image">Photos</option>
        <option value="media_video">Videos</option>
        <option value="metadata">Metadata</option>
        <option value="pdf_text">Native PDF text</option>
        <option value="ocr_text">OCR text</option>
        <option value="caption">Captions</option>
        <option value="video_metadata">Video metadata</option>
      </select>
      <select id="yearFilter" aria-label="Year filter">
        <option value="">All years</option>
      </select>
      <select id="limit" aria-label="Result limit">
        <option value="5" selected>5 results</option>
        <option value="8">8 results</option>
        <option value="12">12 results</option>
        <option value="20">20 results</option>
      </select>
    </div>
    <div class="status" id="status"></div>
    <section class="grid">
      <div>
        <section class="summary" id="summary">
          <h2>Summary</h2>
          <p>Run a search to review ranked evidence with citations.</p>
        </section>
        <section id="results"></section>
      </div>
    </section>
  </main>
  <script>
    const state = { mode: "hybrid", lastQuery: "", lastResults: [] };
    const $ = (id) => document.getElementById(id);

    function esc(value) {
      return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[ch]));
    }

    function sourceClass(kind) {
      return kind === "ocr_text" ? "chip ocr" : "chip";
    }

    function fileUrl(path) {
      return `/file?path=${encodeURIComponent(path)}`;
    }

    function assetLabel(asset) {
      const kind = asset.kind || "asset";
      if (kind === "thumbnail") return "Thumbnail";
      if (kind === "document") return "PDF";
      if (kind === "video") return "Video";
      if (kind === "caption") return "Caption";
      return kind;
    }

    function icon(name) {
      const icons = {
        source: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M3.6 9h16.8"></path><path d="M3.6 15h16.8"></path><path d="M12 3a14 14 0 0 1 0 18"></path><path d="M12 3a14 14 0 0 0 0 18"></path><path d="M15 9h5v5"></path><path d="m20 9-6 6"></path></svg>`,
        pdf: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><path d="M14 2v6h6"></path><path d="M7 16h1.5a1.5 1.5 0 0 0 0-3H7v5"></path><path d="M12 13v5h1.2a2.5 2.5 0 0 0 0-5H12z"></path><path d="M17 18v-5h2"></path><path d="M17 15h1.5"></path></svg>`,
        summary: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z"></path><path d="M14 2v5h5"></path><path d="M8 11h8"></path><path d="M8 15h8"></path><path d="M8 19h5"></path></svg>`
      };
      return icons[name] || "";
    }

    function renderLinks(item) {
      const links = [];
      if (item.source_url) {
        links.push(`<a class="icon-button source-button" href="${esc(item.source_url)}" target="_blank" rel="noopener" aria-label="Government source" title="Government source">${icon("source")}<span>Source</span></a>`);
      }
      return links.length ? `<div class="links">${links.join("")}</div>` : "";
    }

    function primaryMedia(item) {
      const assets = item.assets || [];
      return assets.find((asset) => asset.kind === "thumbnail" && asset.local_path)
        || assets.find((asset) => asset.media_type === "image" && asset.local_path)
        || assets.find((asset) => asset.media_type === "video" && asset.local_path);
    }

    function renderPrimaryMedia(item) {
      const asset = primaryMedia(item);
      if (!asset) return `<div class="result-media"><div class="placeholder">No preview</div></div>`;
      const url = fileUrl(asset.local_path);
      if (asset.media_type === "video") {
        return `<div class="result-media"><video controls preload="metadata" src="${url}"></video></div>`;
      }
      return `<div class="result-media"><a href="${url}" target="_blank" rel="noopener"><img loading="lazy" src="${url}" alt="${esc(assetLabel(asset))} preview"></a></div>`;
    }

    function renderMedia(item) {
      const main = primaryMedia(item);
      const previews = (item.assets || []).filter((asset) =>
        asset.local_path && asset !== main && asset.media_type === "video"
      );
      if (!previews.length) return "";
      return `<div class="media-strip">${previews.map((asset) => {
        const url = fileUrl(asset.local_path);
        const caption = `${assetLabel(asset)}${asset.bytes ? " | " + Math.round(asset.bytes / 1024) + " KB" : ""}`;
        if (asset.media_type === "video") {
          return `
            <div class="media-preview">
              <video controls preload="metadata" src="${url}"></video>
              <div class="media-caption">${esc(caption)}</div>
            </div>
          `;
        }
        return `
          <div class="media-preview">
            <a href="${url}" target="_blank" rel="noopener"><img loading="lazy" src="${url}" alt="${esc(assetLabel(asset))} preview"></a>
            <div class="media-caption">${esc(caption)}</div>
          </div>
        `;
      }).join("")}</div>`;
    }

    function summaryId(docId) {
      return `source-summary-${String(docId || "").replace(/[^A-Za-z0-9_-]/g, "-")}`;
    }

    function renderSourceSummaryControl(item) {
      return `
        <div class="source-summary">
          <div class="links" style="margin:0; padding:10px 10px 0">
            <button type="button" class="icon-button summary-button source-summary-button" data-doc-id="${esc(item.doc_id)}" aria-label="Read full summary" title="Read full summary">${icon("summary")}<span>Summary</span></button>
          </div>
          <div class="source-summary-body" id="${summaryId(item.doc_id)}">
            <p class="note">Shows UAP element, detailed contents, and page/chunk references.</p>
          </div>
        </div>
      `;
    }

    function renderTags(tags) {
      if (!tags || !tags.length) return "";
      return `<div class="tags">${tags.slice(0, 8).map((tag) => `<span class="tag">${esc(tag)}</span>`).join("")}</div>`;
    }

    function renderRefs(refs) {
      if (!refs || !refs.length) return "";
      return `<div class="refs">Refs: ${refs.slice(0, 3).map((ref) => esc(ref.label || ref)).join(" | ")}</div>`;
    }

    function renderSourceSummary(payload) {
      const mystery = (payload.mysterious_uap_element || []).map((point) => `<li>${esc(point.label || point.text || point)}</li>`).join("");
      const details = (payload.detailed_contents || payload.key_points || []).map((point) => `<li>${esc(point.label || point.text || point)}</li>`).join("");
      const refs = (payload.references || []).map((ref) => `<li>${esc(ref.label || ref)}</li>`).join("");
      return `
        <h4>${esc(payload.title || "Source Summary")}</h4>
        <p><strong>Quick summary:</strong> ${esc(payload.quick_summary || payload.overview || "No summary could be generated.")}</p>
        <p><strong>Mysterious UAP element:</strong></p>
        ${mystery ? `<ul>${mystery}</ul>` : `<p class="note">No clear anomaly-focused passage was found in the indexed text.</p>`}
        <p><strong>More detailed contents:</strong></p>
        ${details ? `<ul>${details}</ul>` : ""}
        ${refs ? `<p class="note">References</p><ul>${refs}</ul>` : ""}
        <p class="note">${esc(payload.source_note || "")}</p>
      `;
    }

    const summaryStages = [
      "Reading indexed PDF/OCR/caption text...",
      "Cleaning OCR noise...",
      "Selecting the clearest source sentences...",
      "Attaching page and chunk references...",
      "Writing source summary..."
    ];

    function renderSummaryProgress(message) {
      return `
        <div class="summary-progress" role="status" aria-live="polite">
          <span class="spinner" aria-hidden="true"></span>
          <span>${esc(message)}</span>
        </div>
      `;
    }

    async function summarizeSource(docId, button) {
      const target = $(summaryId(docId));
      if (!target) return;
      const originalHtml = button.innerHTML;
      const originalLabel = button.getAttribute("aria-label") || "Expand detailed summary";
      let stageIndex = 0;
      button.disabled = true;
      button.setAttribute("aria-label", "Reading source");
      button.title = "Reading source";
      target.innerHTML = renderSummaryProgress(summaryStages[stageIndex]);
      const progressTimer = window.setInterval(() => {
        stageIndex = Math.min(stageIndex + 1, summaryStages.length - 1);
        button.setAttribute("aria-label", summaryStages[stageIndex].replace("...", ""));
        button.title = summaryStages[stageIndex].replace("...", "");
        target.innerHTML = renderSummaryProgress(summaryStages[stageIndex]);
        if (stageIndex === summaryStages.length - 1) {
          window.clearInterval(progressTimer);
        }
      }, 650);
      try {
        const minimumDisplay = new Promise((resolve) => window.setTimeout(resolve, 1400));
        const [payload] = await Promise.all([
          api("/api/source-summary", { doc_id: docId }),
          minimumDisplay
        ]);
        window.clearInterval(progressTimer);
        target.innerHTML = renderSourceSummary(payload);
        button.setAttribute("aria-label", "Summary ready");
        button.title = "Summary ready";
      } catch (error) {
        window.clearInterval(progressTimer);
        target.innerHTML = `<p class="note">Source summary failed: ${esc(error.message)}</p>`;
        button.innerHTML = originalHtml;
        button.setAttribute("aria-label", originalLabel);
        button.title = originalLabel;
      } finally {
        button.disabled = false;
        if (button.getAttribute("aria-label") === "Summary ready") {
          window.setTimeout(() => {
            button.setAttribute("aria-label", "Refresh summary");
            button.title = "Refresh summary";
          }, 1200);
        }
      }
    }

    function pointTitle(location) {
      const bits = [
        location.normalized_location || location.raw_location,
        location.precision,
        `confidence ${Number(location.confidence).toFixed(2)}`,
        location.title
      ].filter(Boolean);
      return bits.join(" | ");
    }

    function renderMap(locations) {
      if (!$("map") || !$("mapLabels")) return;
      const unique = [];
      const seen = new Set();
      (locations || []).forEach((location) => {
        const key = `${location.doc_id}:${location.latitude}:${location.longitude}:${location.raw_location}`;
        if (seen.has(key)) return;
        seen.add(key);
        unique.push(location);
      });
      if (!unique.length) {
        $("map").innerHTML = `<div class="empty">No mappable locations in these results.</div>`;
        $("mapLabels").innerHTML = "";
        return;
      }
      const grid = [
        ...[-120, -60, 0, 60, 120].map((lon) => `<line class="map-grid" x1="${(lon + 180) / 360 * 100}" y1="0" x2="${(lon + 180) / 360 * 100}" y2="100"></line>`),
        ...[-60, -30, 0, 30, 60].map((lat) => `<line class="map-grid" x1="0" y1="${(90 - lat) / 180 * 100}" x2="100" y2="${(90 - lat) / 180 * 100}"></line>`)
      ].join("");
      const points = unique.map((location) => {
        const x = (Number(location.longitude) + 180) / 360 * 100;
        const y = (90 - Number(location.latitude)) / 180 * 100;
        const radius = location.precision === "coordinate" ? 4.5 : 3.5;
        return `<circle class="map-point" cx="${x}" cy="${y}" r="${radius}"><title>${esc(pointTitle(location))}</title></circle>`;
      }).join("");
      $("map").innerHTML = `<svg viewBox="0 0 100 100" role="img" aria-label="Search result locations">${grid}${points}</svg>`;
      $("mapLabels").innerHTML = unique.slice(0, 6).map((location) =>
        `<div>${esc(location.normalized_location || location.raw_location)} · ${esc(location.precision)} · ${Number(location.confidence).toFixed(2)}</div>`
      ).join("");
    }

    function api(path, params) {
      const url = new URL(path, window.location.origin);
      Object.entries(params || {}).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
      });
      return fetch(url).then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      });
    }

    function renderSummary(summary) {
      const citations = (summary.citations || []).map((item) => `<li>${esc(item)}</li>`).join("");
      $("summary").innerHTML = `
        <h2>Summary</h2>
        <p>${esc(summary.overview || "No summary available.")}</p>
        <p>${esc(summary.source_mix || "")}</p>
        <ul>${citations}</ul>
      `;
    }

    function renderResults(results) {
      const visibleResults = filterResultsByYear(results);
      if (!results.length) {
        $("results").innerHTML = `<div class="empty">No results for this search.</div>`;
        return;
      }
      if (!visibleResults.length) {
        $("results").innerHTML = `<div class="empty">No results for this year.</div>`;
        return;
      }
      $("results").innerHTML = visibleResults.map((item) => {
        const page = item.page_number ? `page ${item.page_number}` : "no page";
        return `
          <article class="result">
            <div class="result-shell">
              <div class="result-main">
                <div class="result-head">
                  <h3>${item.rank}. ${esc(item.title)}</h3>
                  <div class="score">${Number(item.score).toFixed(4)}</div>
                </div>
                ${renderTags(item.tags)}
                <section class="doc-summary">
                  <p>${esc(item.doc_summary || item.readable_summary || item.snippet)}</p>
                  ${renderRefs(item.references)}
                </section>
                ${renderLinks(item)}
                ${renderSourceSummaryControl(item)}
                ${renderMedia(item)}
              </div>
              ${renderPrimaryMedia(item)}
            </div>
          </article>
        `;
      }).join("");
      document.querySelectorAll(".source-summary-button").forEach((button) => {
        button.addEventListener("click", () => summarizeSource(button.dataset.docId, button));
      });
    }

    function resultYear(item) {
      const text = [item.incident_date, item.title].filter(Boolean).join(" ");
      const match = text.match(/\b(18|19|20)\d{2}\b/);
      return match ? Number(match[0]) : 0;
    }

    function updateYearOptions(results) {
      const current = $("yearFilter").value;
      const years = [...new Set(results.map(resultYear).filter(Boolean))].sort((a, b) => b - a);
      $("yearFilter").innerHTML = `<option value="">All years</option>` + years.map((year) => `<option value="${year}">${year}</option>`).join("");
      if (current && years.includes(Number(current))) $("yearFilter").value = current;
    }

    function filterResultsByYear(results) {
      const year = $("yearFilter") ? $("yearFilter").value : "";
      if (!year) return results;
      return results.filter((item) => String(resultYear(item)) === year);
    }

    function renderSuggestions(suggestions) {
      if (!$("suggestions")) return;
      if (!suggestions.length) {
        $("suggestions").innerHTML = `<div class="empty">No suggestions yet.</div>`;
        return;
      }
      $("suggestions").innerHTML = suggestions.map((item, index) => `
        <button type="button" data-suggestion="${index}">
          ${esc(item.label)}
        </button>
      `).join("");
      document.querySelectorAll("[data-suggestion]").forEach((button) => {
        button.addEventListener("click", () => {
          const item = suggestions[Number(button.dataset.suggestion)];
          $("query").value = item.q || state.lastQuery;
          if (item.source_kind !== undefined) $("sourceKind").value = item.source_kind || "";
          if (item.mode) setMode(item.mode);
          runSearch();
        });
      });
    }

    function setMode(mode) {
      state.mode = mode;
      document.querySelectorAll("[data-mode]").forEach((button) => {
        button.classList.toggle("active", button.dataset.mode === mode);
      });
    }

    async function runSearch() {
      const q = $("query").value.trim();
      if (!q) return;
      state.lastQuery = q;
      $("status").textContent = "Searching...";
      if ($("packPreview")) $("packPreview").value = "";
      try {
        const payload = await api("/api/search", {
          q,
          mode: state.mode,
          limit: $("limit").value,
          source_kind: $("sourceKind").value
        });
        state.lastResults = payload.results;
        updateYearOptions(payload.results);
        renderSummary(payload.summary);
        renderResults(payload.results);
        renderMap(payload.locations);
        renderSuggestions(payload.suggestions);
        $("status").textContent = `${payload.results.length} results in ${payload.elapsed_ms} ms`;
      } catch (error) {
        $("status").textContent = `Search failed: ${error.message}`;
      }
    }

    async function buildPack() {
      const q = $("query").value.trim();
      if (!q) return;
      if (!$("packPreview")) return;
      $("packPreview").value = "Building evidence pack...";
      try {
        const payload = await api("/api/evidence-pack", {
          q,
          mode: state.mode,
          limit: $("limit").value,
          include_text: "false"
        });
        const lines = [
          `# Evidence Pack`,
          ``,
          `Query: ${payload.query}`,
          `Mode: ${payload.mode}`,
          ``,
          ...payload.evidence.slice(0, 5).map((item) =>
            `${item.rank}. ${item.title}\n   ${item.source_label}${item.page_number ? ", page " + item.page_number : ""} | ${item.chunk_id}\n   ${item.snippet}`
          )
        ];
        $("packPreview").value = lines.join("\n\n");
      } catch (error) {
        $("packPreview").value = `Evidence pack failed: ${error.message}`;
      }
    }

    document.querySelectorAll("[data-mode]").forEach((button) => {
      button.addEventListener("click", () => {
        setMode(button.dataset.mode);
        if ($("query").value.trim()) runSearch();
      });
    });
    $("searchForm").addEventListener("submit", (event) => {
      event.preventDefault();
      runSearch();
    });
    $("sourceKind").addEventListener("change", runSearch);
    $("yearFilter").addEventListener("change", () => renderResults(state.lastResults || []));
    $("limit").addEventListener("change", runSearch);
    if ($("packButton")) $("packButton").addEventListener("click", buildPack);

    api("/api/health").then((health) => {
      $("health").textContent = `${health.documents} docs | ${health.chunks} chunks | ${health.embeddings} embeddings`;
    }).catch(() => {
      $("health").textContent = "Index unavailable";
    });
    runSearch();
  </script>
</body>
</html>
"""


STOPWORDS = {
    "about",
    "after",
    "again",
    "against",
    "agency",
    "also",
    "and",
    "are",
    "because",
    "been",
    "being",
    "between",
    "could",
    "date",
    "from",
    "have",
    "into",
    "its",
    "may",
    "not",
    "object",
    "objects",
    "report",
    "search",
    "should",
    "source",
    "that",
    "the",
    "their",
    "then",
    "there",
    "this",
    "through",
    "were",
    "with",
    "would",
}


OCR_FIXES = [
    (re.compile(r"\bU\s*F\s*O\b", re.IGNORECASE), "UFO"),
    (re.compile(r"\bU\s*A\s*P\b", re.IGNORECASE), "UAP"),
    (re.compile(r"\bA\s*F\s*B\b", re.IGNORECASE), "AFB"),
    (re.compile(r"\bF\s*B\s*I\b", re.IGNORECASE), "FBI"),
    (re.compile(r"\bD\s*O\s*D\b", re.IGNORECASE), "DOD"),
]


def readable_text(text: str) -> str:
    text = clean(text)
    text = re.sub(r"-\s+", "", text)
    text = re.sub(r"[_~`|{}\[\]<>]{2,}", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?<=[a-z])(?=[A-Z][a-z])", " ", text)
    for pattern, replacement in OCR_FIXES:
        text = pattern.sub(replacement, text)
    return clean(text)


def sentence_quality(sentence: str) -> float:
    if not sentence:
        return 0.0
    chars = len(sentence)
    letters = sum(1 for char in sentence if char.isalpha())
    punctuation_noise = sum(1 for char in sentence if char in "_~`|{}[]<>")
    if chars < 35 or chars > 360:
        return 0.1
    return (letters / max(chars, 1)) - (punctuation_noise / max(chars, 1))


def split_sentences(text: str) -> List[str]:
    text = re.sub(r"[-=+.]{3,}", ". ", text)
    candidates = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    if len(candidates) == 1:
        candidates = re.split(r"\s{2,}|;\s+", text)
    out = []
    for item in candidates:
        item = clean(item)
        if len(item) > 320:
            item = item[:320].rsplit(" ", 1)[0] + "."
        if sentence_quality(item) >= 0.45:
            out.append(item)
    return out


def query_terms(query: str) -> set[str]:
    return {term.lower() for term in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", query) if term.lower() not in STOPWORDS}


def readable_summary(text: str, source_kind: str, query: str, max_sentences: int = 2) -> str:
    cleaned = readable_text(text)
    sentences = split_sentences(cleaned)
    if not sentences:
        fallback = snippet(cleaned, max_chars=320)
        if not fallback:
            return "No readable text could be generated from this result."
        prefix = "OCR-readable excerpt" if source_kind == "ocr_text" else "Readable excerpt"
        return f"{prefix}: {fallback}"

    terms = query_terms(query)
    ranked = []
    for index, sentence in enumerate(sentences[:18]):
        lowered = sentence.lower()
        term_hits = sum(1 for term in terms if term in lowered)
        score = term_hits * 3 + sentence_quality(sentence) + max(0, 4 - index) * 0.15
        ranked.append((score, index, sentence))
    selected = sorted(sorted(ranked, key=lambda item: item[0], reverse=True)[:max_sentences], key=lambda item: item[1])
    summary = " ".join(humanize_sentence(sentence) for _, _, sentence in selected)
    label = "OCR text says" if source_kind == "ocr_text" else "Source text says"
    return f"{label}: {summary}"


def cleaned_excerpt(text: str) -> str:
    return snippet(humanize_sentence(readable_text(text)), max_chars=900)


def humanize_sentence(sentence: str) -> str:
    letters = [char for char in sentence if char.isalpha()]
    if not letters:
        return sentence
    upper_ratio = sum(1 for char in letters if char.isupper()) / len(letters)
    if upper_ratio < 0.72:
        return sentence
    text = sentence.lower()
    replacements = {
        "ufo": "UFO",
        "uap": "UAP",
        "fbi": "FBI",
        "dod": "DOD",
        "nasa": "NASA",
        "p.a.o.": "P.A.O.",
        "gemini": "Gemini",
        "houston": "Houston",
    }
    for old, new in replacements.items():
        text = re.sub(rf"\b{re.escape(old)}\b", new, text)
    return text[:1].upper() + text[1:]


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def first(params: Dict[str, List[str]], key: str, default: str = "") -> str:
    values = params.get(key)
    return values[0] if values else default


def clamp_int(value: str, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


def run_search(conn, query: str, mode: str, model: str, limit: int) -> List[Tuple[float, object]]:
    if mode == "keyword":
        return keyword_search(conn, query, limit)
    if mode == "vector":
        return vector_search(conn, query, model_name=model, limit=limit)
    return hybrid_search(conn, query, model, limit)


def row_metadata(row) -> Dict:
    return json.loads(row["metadata_json"] or "{}")


def media_type(kind: str, local_path: str) -> str:
    mime = mimetypes.guess_type(local_path)[0] or ""
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("video/"):
        return "video"
    if mime == "application/pdf" or kind == "document":
        return "document"
    if kind == "caption" or mime.startswith("text/"):
        return "text"
    return "file"


def document_source_url(conn, doc_id: str) -> str:
    row = conn.execute("SELECT source_url FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()
    return clean(row["source_url"]) if row else ""


def result_assets(conn, doc_id: str) -> List[Dict]:
    rows = conn.execute(
        """
        SELECT kind, local_path, source_url, bytes, metadata_json
        FROM assets
        WHERE doc_id = ?
        ORDER BY
          CASE kind
            WHEN 'thumbnail' THEN 0
            WHEN 'video' THEN 1
            WHEN 'document' THEN 2
            WHEN 'caption' THEN 3
            ELSE 4
          END,
          local_path
        """,
        (doc_id,),
    ).fetchall()
    assets = []
    seen = set()
    for row in rows:
        local_path = clean(row["local_path"])
        source_url = clean(row["source_url"])
        key = (row["kind"], local_path, source_url)
        if key in seen:
            continue
        seen.add(key)
        assets.append(
            {
                "kind": row["kind"],
                "local_path": local_path,
                "source_url": source_url,
                "bytes": row["bytes"] or 0,
                "media_type": media_type(row["kind"], local_path),
            }
        )
    return assets


def result_locations(conn, doc_id: str) -> List[Dict]:
    rows = conn.execute(
        """
        SELECT l.*, d.title, d.agency, d.incident_date, d.incident_location
        FROM locations l
        JOIN documents d ON d.doc_id = l.doc_id
        WHERE l.doc_id = ?
        ORDER BY l.confidence DESC, l.precision, l.raw_location
        """,
        (doc_id,),
    ).fetchall()
    return [
        {
            "location_id": row["location_id"],
            "doc_id": row["doc_id"],
            "chunk_id": row["chunk_id"],
            "raw_location": row["raw_location"],
            "normalized_location": row["normalized_location"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "precision": row["precision"],
            "confidence": row["confidence"],
            "source_kind": row["source_kind"],
            "method": row["method"],
            "title": row["title"],
            "agency": row["agency"],
            "incident_date": row["incident_date"],
            "incident_location": row["incident_location"],
        }
        for row in rows
    ]


TAG_STOPWORDS = STOPWORDS | {
    "available",
    "case",
    "chunks",
    "contains",
    "contents",
    "detailed",
    "department",
    "document",
    "file",
    "flying",
    "includes",
    "incident",
    "indexed",
    "investigative",
    "compliance",
    "native",
    "object",
    "objects",
    "page",
    "pages",
    "pdf",
    "primarily",
    "quick",
    "record",
    "release",
    "report",
    "reports",
    "source",
    "service",
    "summary",
    "text",
    "unidentified",
    "written",
}


def summary_tags(payload: Dict, row) -> List[str]:
    tags = []
    if row["source_kind"] == "ocr_text":
        tags.append("OCR")

    mystery_text = " ".join(
        clean(item.get("text") or item.get("label") or "") if isinstance(item, dict) else clean(item)
        for item in payload.get("mysterious_uap_element") or []
    )
    text = " ".join(
        [
            clean(row["title"]),
            clean(payload.get("quick_summary")),
            mystery_text,
        ]
    )
    for term in re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", text):
        key = term.lower().strip("-")
        if key in TAG_STOPWORDS or len(key) < 4 or any(char.isdigit() for char in key):
            continue
        if key.startswith(("hs", "hq", "serial", "section")):
            continue
        label = "UFOs" if key in {"ufo", "ufos"} else key.upper() if key in {"uap", "fbi", "dod", "nasa", "caa", "mats", "aacs"} else key.title()
        if label not in tags:
            tags.append(label)
        if len(tags) >= 8:
            break
    return tags


def compact_doc_summary(payload: Dict) -> str:
    quick = clean(payload.get("quick_summary"))
    mystery = payload.get("mysterious_uap_element") or []
    if mystery:
        first_item = mystery[0]
        first_text = first_item.get("text") or first_item.get("label") or "" if isinstance(first_item, dict) else first_item
        first_mystery = re.sub(r"\s+\([^)]*\)$", "", clean(first_text))
        if first_mystery and first_mystery not in quick:
            quick = f"{quick} UAP element: {first_mystery}"
    return snippet(quick, max_chars=620)


def result_item(conn, score: float, row, rank: int, query: str) -> Dict:
    metadata = row_metadata(row)
    text = clean(row["text"])
    doc_source_url = document_source_url(conn, row["doc_id"])
    source_url = clean(metadata.get("source_url")) or doc_source_url
    summary_payload = build_source_summary(conn, row["doc_id"])
    return {
        "rank": rank,
        "score": score,
        "chunk_id": row["chunk_id"],
        "doc_id": row["doc_id"],
        "title": row["title"],
        "agency": row["agency"],
        "incident_date": row["incident_date"],
        "incident_location": row["incident_location"],
        "source_kind": row["source_kind"],
        "source_label": source_label(row["source_kind"]),
        "page_number": row["page_number"],
        "chunk_index": row["chunk_index"],
        "local_path": clean(metadata.get("local_path")),
        "source_url": source_url,
        "assets": result_assets(conn, row["doc_id"]),
        "locations": result_locations(conn, row["doc_id"]),
        "snippet": snippet(text, max_chars=700),
        "readable_summary": readable_summary(text, row["source_kind"], query),
        "cleaned_excerpt": cleaned_excerpt(text),
        "doc_summary": compact_doc_summary(summary_payload),
        "tags": summary_tags(summary_payload, row),
        "references": summary_payload.get("references", [])[:4],
        "provenance": {
            "title": row["title"],
            "agency": row["agency"],
            "incident_date": row["incident_date"],
            "incident_location": row["incident_location"],
            "source_kind": row["source_kind"],
            "source_label": source_label(row["source_kind"]),
            "page_number": row["page_number"],
            "chunk_id": row["chunk_id"],
        },
    }


def result_has_media(item: Dict, media_filter: str) -> bool:
    assets = item.get("assets") or []
    if media_filter == "media_image":
        return any(asset.get("kind") == "thumbnail" or asset.get("media_type") == "image" for asset in assets)
    if media_filter == "media_video":
        return any(asset.get("kind") == "video" or asset.get("media_type") == "video" for asset in assets)
    return True


def filtered_results(
    conn,
    *,
    query: str,
    mode: str,
    model: str,
    limit: int,
    source_kind: str,
) -> List[Dict]:
    media_filter = source_kind if source_kind in {"media_image", "media_video"} else ""
    chunk_source_kind = "" if media_filter else source_kind
    search_limit = limit * 12 if media_filter else limit * 5 if chunk_source_kind else limit
    rows = run_search(conn, query, mode, model, search_limit)
    items = []
    for score, row in rows:
        if chunk_source_kind and row["source_kind"] != chunk_source_kind:
            continue
        item = result_item(conn, score, row, len(items) + 1, query)
        if media_filter and not result_has_media(item, media_filter):
            continue
        items.append(item)
        if len(items) >= limit:
            break
    return items


def result_location_payload(results: List[Dict]) -> List[Dict]:
    out = []
    seen = set()
    for item in results:
        for location in item.get("locations", []):
            key = (
                location["doc_id"],
                location["chunk_id"],
                location["raw_location"],
                location["latitude"],
                location["longitude"],
            )
            if key in seen:
                continue
            seen.add(key)
            out.append(location)
    return out


def summarize_results(query: str, results: List[Dict]) -> Dict:
    if not results:
        return {
            "overview": f"No indexed evidence matched {query!r}.",
            "source_mix": "",
            "citations": [],
        }
    source_counts: Dict[str, int] = {}
    for item in results:
        source_counts[item["source_label"]] = source_counts.get(item["source_label"], 0) + 1
    mix = ", ".join(f"{count} {label}" for label, count in sorted(source_counts.items()))
    top_titles = []
    for item in results:
        if item["title"] not in top_titles:
            top_titles.append(item["title"])
        if len(top_titles) == 3:
            break
    citations = []
    for item in results[:4]:
        page = f", page {item['page_number']}" if item["page_number"] else ""
        citations.append(
            f"{item['title']} ({item['source_label']}{page}; chunk {item['chunk_id']})"
        )
    return {
        "overview": f"Top matches point to {', '.join(top_titles)}.",
        "source_mix": f"Source mix: {mix}. OCR text is machine-read and should be checked against the PDF.",
        "citations": citations,
    }


def term_counts(results: List[Dict]) -> List[str]:
    counts: Dict[str, int] = {}
    for item in results[:5]:
        for term in re.findall(r"[A-Za-z][A-Za-z0-9-]{4,}", item["snippet"]):
            key = term.lower()
            if key in STOPWORDS:
                continue
            counts[key] = counts.get(key, 0) + 1
    return [term for term, _ in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:5]]


def suggestions(query: str, results: List[Dict]) -> List[Dict]:
    out: List[Dict] = []
    if not results:
        return out
    first_result = results[0]
    if first_result["title"]:
        out.append({"label": f"More from {first_result['title']}", "q": first_result["title"], "mode": "hybrid"})
    for item in results:
        if item["agency"]:
            out.append({"label": f"Agency: {item['agency']}", "q": f"{query} {item['agency']}", "mode": "hybrid"})
            break
    for item in results:
        if item["incident_location"] and item["incident_location"] != "N/A":
            out.append({"label": f"Location: {item['incident_location']}", "q": f"{query} {item['incident_location']}", "mode": "hybrid"})
            break
    if any(item["source_kind"] == "ocr_text" for item in results):
        out.append({"label": "Search OCR text only", "q": query, "mode": "hybrid", "source_kind": "ocr_text"})
    elif any(item["source_kind"] == "metadata" for item in results):
        out.append({"label": "Search metadata only", "q": query, "mode": "hybrid", "source_kind": "metadata"})
    for term in term_counts(results):
        if term not in query.lower():
            out.append({"label": f"Follow term: {term}", "q": f"{query} {term}", "mode": "hybrid"})
        if len(out) >= 7:
            break
    deduped = []
    seen = set()
    for item in out:
        key = (item.get("label"), item.get("q"), item.get("source_kind", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[:7]


UAP_TERMS = {
    "uap",
    "ufo",
    "unidentified",
    "object",
    "objects",
    "bogey",
    "sighting",
    "sightings",
    "light",
    "lights",
    "orb",
    "orbs",
    "disc",
    "disk",
    "saucer",
    "aerial",
    "anomaly",
    "unknown",
    "formation",
    "tumbling",
}


def sentence_ref(row) -> str:
    page = f"page {row['page_number']}" if row["page_number"] else "no page"
    return f"{source_label(row['source_kind'])}, {page}, chunk {row['chunk_id']}"


def sentence_line(row, sentence: str) -> str:
    page = f"page {row['page_number']}" if row["page_number"] else "no page"
    return f"{sentence} ({source_label(row['source_kind'])}, {page})"


def sentence_has_uap_terms(sentence: str) -> bool:
    words = set(re.findall(r"[a-z][a-z0-9-]+", sentence.lower()))
    return bool(words & UAP_TERMS)


def unique_sentence_items(items: List[Tuple[float, object, str]], limit: int, chronological: bool = False) -> List[Tuple[object, str]]:
    selected = []
    seen = set()
    iterable = items if chronological else sorted(items, key=lambda item: item[0], reverse=True)
    for _, row, sentence in iterable:
        sentence = humanize_sentence(sentence)
        key = re.sub(r"[^a-z0-9]+", " ", sentence.lower()).strip()[:100]
        if not key or key in seen:
            continue
        seen.add(key)
        selected.append((row, sentence))
        if len(selected) >= limit:
            break
    return selected


def source_summary(conn, doc_id: str) -> Dict:
    doc = conn.execute(
        """
        SELECT doc_id, title, agency, incident_date, incident_location, description, source_url
        FROM documents
        WHERE doc_id = ?
        """,
        (doc_id,),
    ).fetchone()
    if not doc:
        raise ValueError("document not found")

    rows = conn.execute(
        """
        SELECT source_kind, page_number, chunk_index, chunk_id, text
        FROM chunks
        WHERE doc_id = ?
        ORDER BY
          CASE source_kind
            WHEN 'pdf_text' THEN 0
            WHEN 'ocr_text' THEN 1
            WHEN 'caption' THEN 2
            WHEN 'video_metadata' THEN 3
            WHEN 'metadata' THEN 4
            ELSE 5
          END,
          page_number,
          chunk_index
        """,
        (doc_id,),
    ).fetchall()
    evidence_rows = [row for row in rows if row["source_kind"] in {"pdf_text", "ocr_text", "caption", "video_metadata"}]
    if not evidence_rows:
        evidence_rows = rows

    source_counts: Dict[str, int] = {}
    for row in evidence_rows:
        source_counts[row["source_kind"]] = source_counts.get(row["source_kind"], 0) + 1

    sentences: List[Tuple[float, object, str]] = []
    chronological_sentences: List[Tuple[float, object, str]] = []
    for row in evidence_rows:
        text = readable_text(row["text"])
        for sentence in split_sentences(text)[:5]:
            quality = sentence_quality(sentence)
            if row["source_kind"] in {"pdf_text", "ocr_text"}:
                quality += 0.2
            if row["page_number"]:
                quality += 0.1
            sentences.append((quality, row, sentence))
            chronological_sentences.append((quality, row, sentence))

    title = clean(doc["title"])
    location = clean(doc["incident_location"])
    date = clean(doc["incident_date"])
    agency = clean(doc["agency"])
    overview_bits = [f"{title} is indexed as a {agency or 'source'} record"]
    if date and date != "N/A":
        overview_bits.append(f"with incident date {date}")
    if location and location != "N/A":
        overview_bits.append(f"and location {location}")
    overview = " ".join(overview_bits) + "."
    description = readable_text(doc["description"])
    if description:
        overview = f"{overview} {snippet(humanize_sentence(description), max_chars=280)}"

    top_items = unique_sentence_items(sentences, 5)
    uap_items = unique_sentence_items(
        [(score + 0.8, row, sentence) for score, row, sentence in sentences if sentence_has_uap_terms(sentence)],
        4,
    )
    detail_items = unique_sentence_items(chronological_sentences, 10, chronological=True)

    if top_items:
        quick_summary = f"{overview} Main readable passages include: " + " ".join(sentence for _, sentence in top_items[:2])
    else:
        quick_summary = overview

    mysterious_uap_element = [sentence_line(row, sentence) for row, sentence in uap_items]
    if not mysterious_uap_element:
        mysterious_uap_element = [
            "No clear anomaly-focused passage was found in the indexed text for this source; review the PDF/media manually if the title or metadata suggests a UAP connection."
        ]

    detailed_contents = [sentence_line(row, sentence) for row, sentence in detail_items]
    if not detailed_contents:
        detailed_contents = [
            "No readable PDF/OCR/caption sentences were available for this source. Try opening the PDF or running OCR review for this document."
        ]

    references = []
    for row, _ in [*top_items, *uap_items, *detail_items]:
        ref = sentence_ref(row)
        if ref not in references:
            references.append(ref)

    mix = ", ".join(f"{count} {source_label(kind)} chunks" for kind, count in sorted(source_counts.items()))
    source_note = f"Summary generated locally from the entire indexed source text for this document. Source mix: {mix or 'no indexed text chunks'}. OCR text may contain recognition errors; verify important points against the source file."
    return {
        "doc_id": doc["doc_id"],
        "title": title,
        "agency": agency,
        "incident_date": date,
        "incident_location": location,
        "source_url": clean(doc["source_url"]),
        "overview": overview,
        "quick_summary": quick_summary,
        "mysterious_uap_element": mysterious_uap_element,
        "detailed_contents": detailed_contents,
        "key_points": detailed_contents,
        "references": references[:10],
        "source_note": source_note,
    }


def health_payload(db: Path) -> Dict:
    conn = connect(db)
    counts = {
        "db": str(db),
        "documents": conn.execute("SELECT count(*) FROM documents").fetchone()[0],
        "assets": conn.execute("SELECT count(*) FROM assets").fetchone()[0],
        "chunks": conn.execute("SELECT count(*) FROM chunks").fetchone()[0],
        "ocr_chunks": conn.execute("SELECT count(*) FROM chunks WHERE source_kind = 'ocr_text'").fetchone()[0],
        "embeddings": conn.execute("SELECT count(*) FROM embeddings").fetchone()[0],
    }
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    counts["integrity"] = integrity
    return counts


def allowed_file_paths(db: Path) -> set[Path]:
    conn = connect(db)
    paths: set[Path] = set()
    for row in conn.execute("SELECT local_path FROM assets WHERE local_path != ''"):
        path = Path(row["local_path"])
        if path.exists():
            paths.add(path.resolve())
    for row in conn.execute("SELECT metadata_json FROM chunks WHERE metadata_json LIKE '%local_path%'"):
        metadata = json.loads(row["metadata_json"] or "{}")
        local_path = clean(metadata.get("local_path"))
        if local_path:
            path = Path(local_path)
            if path.exists():
                paths.add(path.resolve())
    return paths


class SearchServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class, *, db: Path, model: str):
        super().__init__(server_address, handler_class)
        self.db = db
        self.model = model
        self.allowed_paths = allowed_file_paths(db)


class Handler(BaseHTTPRequestHandler):
    server: SearchServer

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")

    def send_json(self, payload: Dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self) -> None:
        body = HTML.encode("utf-8")
        self.send_response(HTTPStatus.OK.value)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        try:
            if parsed.path in {"/", "/index.html"}:
                self.send_html()
            elif parsed.path == "/api/health":
                self.send_json(health_payload(self.server.db))
            elif parsed.path == "/api/search":
                self.handle_search(params)
            elif parsed.path == "/api/source-summary":
                self.handle_source_summary(params)
            elif parsed.path == "/api/evidence-pack":
                self.handle_evidence_pack(params)
            elif parsed.path == "/file":
                self.handle_file(params)
            else:
                self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_search(self, params: Dict[str, List[str]]) -> None:
        import time

        query = clean(first(params, "q"))
        mode = first(params, "mode", "hybrid")
        if mode not in {"keyword", "vector", "hybrid"}:
            mode = "hybrid"
        limit = clamp_int(first(params, "limit", "8"), 8, 1, 20)
        source_kind = first(params, "source_kind")
        if source_kind not in {"", "media_image", "media_video", "metadata", "pdf_text", "ocr_text", "caption", "video_metadata"}:
            source_kind = ""
        start = time.time()
        conn = connect(self.server.db)
        results = filtered_results(
            conn,
            query=query,
            mode=mode,
            model=self.server.model,
            limit=limit,
            source_kind=source_kind,
        ) if query else []
        payload = {
            "query": query,
            "mode": mode,
            "limit": limit,
            "source_kind": source_kind,
            "elapsed_ms": int((time.time() - start) * 1000),
            "summary": summarize_results(query, results),
            "suggestions": suggestions(query, results),
            "locations": result_location_payload(results),
            "results": results,
        }
        self.send_json(payload)

    def handle_source_summary(self, params: Dict[str, List[str]]) -> None:
        doc_id = clean(first(params, "doc_id"))
        if not doc_id:
            self.send_json({"error": "missing doc_id"}, HTTPStatus.BAD_REQUEST)
            return
        conn = connect(self.server.db)
        self.send_json(build_source_summary(conn, doc_id))

    def handle_evidence_pack(self, params: Dict[str, List[str]]) -> None:
        query = clean(first(params, "q"))
        mode = first(params, "mode", "hybrid")
        if mode not in {"keyword", "vector", "hybrid"}:
            mode = "hybrid"
        limit = clamp_int(first(params, "limit", "8"), 8, 1, 20)
        include_text = parse_bool(first(params, "include_text", "false"))
        payload = build_pack(
            db=self.server.db,
            query=query,
            mode=mode,
            model=self.server.model,
            limit=limit,
            include_text=include_text,
        )
        payload["markdown_preview"] = markdown_report(payload)
        self.send_json(payload)

    def handle_file(self, params: Dict[str, List[str]]) -> None:
        requested = clean(first(params, "path"))
        if not requested:
            self.send_json({"error": "missing path"}, HTTPStatus.BAD_REQUEST)
            return
        path = Path(requested)
        try:
            resolved = path.resolve()
        except OSError:
            self.send_json({"error": "invalid path"}, HTTPStatus.BAD_REQUEST)
            return
        if resolved not in self.server.allowed_paths or not resolved.exists() or not resolved.is_file():
            self.send_json({"error": "file is not referenced by the index"}, HTTPStatus.FORBIDDEN)
            return
        content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
        data = resolved.read_bytes()
        self.send_response(HTTPStatus.OK.value)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition", f'inline; filename="{resolved.name}"')
        self.end_headers()
        self.wfile.write(data)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local DisclosureArchive search UI.")
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args(argv)

    db = args.db.expanduser().resolve()
    server = SearchServer((args.host, args.port), Handler, db=db, model=args.model)
    print(f"DisclosureArchive search UI: http://{args.host}:{args.port}")
    print(f"DB: {db}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping search UI")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
    "primarily",
