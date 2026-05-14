from __future__ import annotations

import argparse
import ast
import json
import mimetypes
import os
import re
from datetime import datetime, timedelta, timezone
from html import escape as html_escape
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlparse

from .common import clean
from .db import connect
from .summary import STOPWORDS, source_summary


PUBLIC_SITE_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Disclosure Archive</title>
  <!-- SEO_META -->
  <!-- SECURITY_META -->
  <!-- STRUCTURED_DATA -->
  <!-- ANALYTICS_SNIPPET -->
  <style>
    :root {
      color-scheme: dark;
      --bg: #050806;
      --panel: rgba(9, 22, 16, 0.92);
      --panel-2: rgba(5, 14, 10, 0.96);
      --ink: #e7fff2;
      --muted: #8fb39e;
      --line: rgba(74, 255, 151, 0.22);
      --accent: #42ff8c;
      --accent-2: #72d7ff;
      --warn: #ffd166;
      --soft: rgba(66, 255, 140, 0.12);
      --mark: rgba(255, 209, 102, 0.28);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background:
        linear-gradient(rgba(66,255,140,0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(66,255,140,0.035) 1px, transparent 1px),
        radial-gradient(circle at 20% 0%, rgba(114,215,255,0.16), transparent 30%),
        radial-gradient(circle at 80% 18%, rgba(66,255,140,0.12), transparent 32%),
        var(--bg);
      background-size: 28px 28px, 28px 28px, auto, auto, auto;
      color: var(--ink);
      font: 14px/1.45 ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background: repeating-linear-gradient(to bottom, rgba(255,255,255,0.035) 0, rgba(255,255,255,0.035) 1px, transparent 1px, transparent 4px);
      mix-blend-mode: overlay;
      opacity: 0.45;
    }
    header {
      background: linear-gradient(180deg, rgba(4, 18, 11, 0.98), rgba(4, 12, 8, 0.86));
      border-bottom: 1px solid var(--line);
      box-shadow: 0 0 34px rgba(66,255,140,0.12);
    }
    .wrap {
      width: min(1160px, calc(100% - 32px));
      margin: 0 auto;
    }
    .top > div,
    .body,
    .details,
    .source-note,
    .refs {
      min-width: 0;
    }
    .top {
      min-height: 72px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
    }
    .top-actions {
      display: grid;
      gap: 8px;
      justify-items: end;
    }
    .nav {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 8px;
    }
    .nav-link {
      min-height: 32px;
      padding: 0 10px;
      color: var(--accent-2);
      text-transform: uppercase;
      font-size: 12px;
    }
    .nav-link.active {
      border-color: var(--accent);
      color: var(--accent);
      background: rgba(66,255,140,0.14);
    }
    h1 {
      margin: 0;
    }
    .brand-title {
      min-height: 0;
      border: 0;
      border-radius: 0;
      padding: 0;
      background: transparent;
      box-shadow: none;
      font-size: 23px;
      letter-spacing: 0;
      color: var(--accent);
      text-shadow: 0 0 18px rgba(66,255,140,0.42);
      cursor: pointer;
    }
    .brand-title:hover,
    .brand-title:focus-visible {
      color: var(--accent-2);
      outline: none;
      text-shadow: 0 0 20px rgba(114,215,255,0.45);
    }
    main { padding: 22px 0 36px; }
    .search {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 118px;
      gap: 10px;
    }
    input, button, select { font: inherit; }
    input[type="search"] {
      height: 46px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 13px;
      background: rgba(0, 0, 0, 0.42);
      color: var(--ink);
      box-shadow: inset 0 0 18px rgba(66,255,140,0.06);
    }
    input[type="search"]::placeholder { color: #6f927d; }
    button, .button {
      min-height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: rgba(7, 24, 15, 0.92);
      color: var(--ink);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      text-decoration: none;
      font-weight: 650;
      box-shadow: 0 0 0 1px rgba(66,255,140,0.04), 0 0 18px rgba(66,255,140,0.06);
    }
    button:hover, .button:hover {
      border-color: rgba(66,255,140,0.55);
      color: var(--accent);
      text-decoration: none;
    }
    button.primary {
      border-color: var(--accent);
      background: linear-gradient(180deg, rgba(66,255,140,0.24), rgba(66,255,140,0.11));
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0;
    }
    .tools {
      margin-top: 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }
    .tools select {
      min-width: min(220px, 100%);
    }
    select {
      height: 36px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel-2);
      padding: 0 10px;
      color: var(--ink);
    }
    .status {
      margin: 14px 0;
      color: var(--muted);
      font-size: 13px;
    }
    .view[hidden] {
      display: none;
    }
    .home-search-panel {
      margin: 0 0 16px;
      padding: 14px;
      border: 1px solid rgba(66,255,140,0.22);
      border-radius: 8px;
      background: rgba(4, 14, 10, 0.82);
      box-shadow: 0 16px 44px rgba(0,0,0,0.22), 0 0 24px rgba(66,255,140,0.05);
    }
    .home-search-panel .section-head {
      margin-bottom: 10px;
    }
    .best-of {
      margin: 16px 0 24px;
      padding: 14px;
      border: 1px solid rgba(114,215,255,0.24);
      border-radius: 8px;
      background: linear-gradient(180deg, rgba(7, 24, 15, 0.94), rgba(4, 12, 8, 0.9));
      box-shadow: 0 16px 44px rgba(0,0,0,0.28), 0 0 28px rgba(114,215,255,0.06);
    }
    .best-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }
    .best-head h2 {
      margin: 0;
      font-size: 18px;
    }
    .best-title-row {
      min-width: 0;
    }
    .best-count {
      color: var(--muted);
      font-size: 12px;
    }
    .best-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }
    .best-card {
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(2, 10, 6, 0.74);
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .best-media {
      height: 150px;
      border-bottom: 1px solid var(--line);
      background: #020503;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }
    .best-media img,
    .best-media video {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
      background: #111;
    }
    .best-body {
      padding: 11px;
      display: flex;
      flex-direction: column;
      flex: 1;
    }
    .best-label {
      color: var(--warn);
      font-size: 11px;
      text-transform: uppercase;
      font-weight: 700;
    }
    .best-title {
      margin: 5px 0 6px;
      color: var(--accent);
      font-size: 14px;
      line-height: 1.25;
      overflow-wrap: anywhere;
    }
    .best-summary {
      color: var(--ink);
      font-size: 12px;
      display: -webkit-box;
      -webkit-line-clamp: 5;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .best-facts {
      margin: 8px 0 0;
      padding-left: 15px;
      color: var(--muted);
      font-size: 11px;
    }
    .best-facts li {
      margin: 3px 0;
    }
    .best-link {
      align-self: flex-start;
      margin-top: 9px;
      min-height: 30px;
      padding: 0 8px;
      font-size: 11px;
      color: var(--accent-2);
    }
    .search-section {
      margin-top: 18px;
      padding-top: 18px;
      border-top: 1px solid var(--line);
    }
    .section-head {
      margin-bottom: 12px;
    }
    .section-head h2 {
      margin-bottom: 4px;
    }
    .section-head p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
    }
    .globe-panel {
      display: none;
      margin: 14px 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(1, 10, 7, 0.78);
      box-shadow: 0 16px 44px rgba(0,0,0,0.34), 0 0 28px rgba(66,255,140,0.06);
      overflow: hidden;
    }
    .globe-panel.open {
      display: grid;
    }
    .globe-toggle {
      min-height: 36px;
      padding: 0 10px;
      font-size: 12px;
      color: var(--accent-2);
    }
    .globe-stage {
      position: relative;
      height: clamp(320px, 46vh, 520px);
      min-height: 320px;
      background:
        radial-gradient(circle at 50% 45%, rgba(66,255,140,0.09), transparent 36%),
        radial-gradient(circle at 50% 50%, rgba(114,215,255,0.07), transparent 52%),
        #020503;
    }
    #globeCanvas {
      width: 100%;
      height: 100%;
      min-height: 320px;
      display: block;
      cursor: grab;
      touch-action: none;
      overscroll-behavior: contain;
    }
    #globeCanvas:active { cursor: grabbing; }
    .globe-popup {
      position: absolute;
      right: 14px;
      top: 14px;
      width: min(340px, calc(100% - 28px));
      border: 1px solid rgba(66,255,140,0.42);
      border-radius: 8px;
      background: rgba(2, 10, 6, 0.92);
      box-shadow: 0 18px 42px rgba(0,0,0,0.42), 0 0 26px rgba(66,255,140,0.1);
      padding: 12px;
      padding-right: 42px;
      z-index: 2;
    }
    .globe-popup[hidden] { display: none; }
    .globe-close {
      position: absolute;
      top: 8px;
      right: 8px;
      width: 28px;
      min-width: 28px;
      height: 28px;
      min-height: 28px;
      padding: 0;
      border-radius: 50%;
      font-size: 18px;
      line-height: 1;
    }
    .globe-popup h3 {
      margin-top: 0;
      color: var(--accent);
    }
    .globe-popup p {
      color: var(--ink);
      font-size: 12px;
    }
    .result {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      margin-bottom: 12px;
      box-shadow: 0 12px 34px rgba(0,0,0,0.28), 0 0 22px rgba(66,255,140,0.05);
    }
    .shell {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 220px;
      align-items: start;
    }
    .result.media-rich .shell {
      grid-template-columns: minmax(0, 1fr) minmax(340px, 42%);
    }
    .body { padding: 15px; }
    .media {
      width: 220px;
      height: 180px;
      border-left: 1px solid var(--line);
      background: #020503;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      position: sticky;
      top: 10px;
    }
    .result.media-rich .media {
      width: 100%;
      height: clamp(260px, 32vw, 420px);
    }
    .media img, .media video {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
      background: #111;
    }
    h2 {
      margin: 0 0 8px;
      font-size: 17px;
      letter-spacing: 0;
      color: var(--accent);
      overflow-wrap: anywhere;
    }
    h3 {
      margin: 14px 0 6px;
      font-size: 14px;
      letter-spacing: 0;
    }
    p { margin: 7px 0; overflow-wrap: anywhere; }
    ul { margin: 8px 0 0; padding-left: 18px; }
    li { margin: 5px 0; overflow-wrap: anywhere; }
    .muted, .refs, .source-note {
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    .tags {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 8px 0 10px;
    }
    .tag {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 3px 8px;
      background: var(--soft);
      color: var(--accent);
      font-size: 12px;
      font-weight: 650;
      cursor: pointer;
      overflow-wrap: anywhere;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }
    .icon-button {
      min-width: 38px;
      min-height: 34px;
      padding: 0 10px;
    }
    .source-button,
    .summary-button {
      gap: 7px;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0;
    }
    .source-button span,
    .summary-button span {
      overflow-wrap: anywhere;
    }
    .details {
      display: none;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid var(--line);
    }
    .result.open .details { display: block; }
    .empty {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      color: var(--muted);
    }
    .load-more {
      display: grid;
      justify-items: center;
      gap: 10px;
      margin: 16px 0 0;
    }
    .load-more[hidden] {
      display: none;
    }
    .load-more button {
      min-width: 160px;
      color: var(--accent-2);
    }
    .result-sentinel {
      width: 100%;
      height: 1px;
    }
    mark { background: var(--mark); padding: 0 2px; }
    a { color: var(--accent-2); }
    a:hover { color: var(--accent); }
    @media (max-width: 980px) and (min-width: 761px) {
      .best-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 760px) {
      body { font-size: 13px; }
      .wrap { width: min(1160px, calc(100% - 20px)); }
      .top { align-items: flex-start; flex-direction: column; padding: 16px 0; }
      .top-actions { justify-items: start; width: 100%; }
      .nav { justify-content: flex-start; width: 100%; }
      .brand-title { font-size: 20px; text-align: left; }
      .search { grid-template-columns: 1fr; }
      input[type="search"], button, .button, select { min-height: 44px; }
      .tools { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
      .tools select, .tools button { width: 100%; min-width: 0; }
      .best-of { padding: 12px; }
      .best-head { align-items: flex-start; flex-direction: column; }
      .best-grid { grid-template-columns: 1fr; }
      .best-media { height: min(230px, 54vw); }
      .shell { grid-template-columns: 1fr; }
      .body { padding: 12px; }
      .media { order: -1; width: 100%; height: 160px; border-left: 0; border-bottom: 1px solid var(--line); position: static; }
      .result.media-rich .shell { grid-template-columns: 1fr; }
      .result.media-rich .media { height: min(340px, 66vw); }
      .actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .actions > * { width: 100%; min-width: 0; }
      .globe-stage { height: clamp(300px, 82vw, 460px); min-height: 300px; }
      #globeCanvas { min-height: 300px; }
      .globe-popup { inset: 10px 10px auto 10px; width: auto; max-height: calc(100% - 20px); overflow: auto; }
    }
    @media (max-width: 430px) {
      .tools, .actions { grid-template-columns: 1fr; }
      .result.media-rich .media { height: min(320px, 78vw); }
    }
  </style>
</head>
<body>
  <header>
    <div class="wrap top">
      <div>
        <h1><button type="button" class="brand-title" id="brandReset" title="Reset archive search">Disclosure Archive</button></h1>
      </div>
      <div class="top-actions">
        <nav class="nav" aria-label="Primary">
          <button type="button" class="nav-link active" data-view-target="home">Highlights</button>
          <button type="button" class="nav-link" data-view-target="search">Search</button>
        </nav>
      </div>
    </div>
  </header>
  <main class="wrap">
    <section id="homeView" class="view">
      <section class="home-search-panel">
        <div class="section-head">
          <h2>Explore The Release</h2>
        </div>
        <form class="search" id="homeSearchForm">
          <input id="homeQ" type="search" autocomplete="off" placeholder="Search titles, summaries, videos, photos, agencies">
          <button class="primary" type="submit">Search</button>
        </form>
      </section>
      <section id="bestOf" class="best-of" hidden></section>
    </section>
    <section class="view search-section" id="searchView" hidden>
      <div class="section-head">
        <h2>Search The Index</h2>
      </div>
      <form class="search" id="searchForm">
        <input id="q" type="search" autocomplete="off" placeholder="Search summaries, titles, agencies, tags, references">
        <button class="primary" type="submit">Search</button>
      </form>
      <div class="tools">
        <select id="agencyFilter" aria-label="Agency filter"></select>
        <select id="sourceFilter" aria-label="Source filter">
          <option value="">All source types</option>
          <option value="media_image">Photos</option>
          <option value="media_video">Videos</option>
          <option value="pdf_text">PDF text</option>
          <option value="ocr_text">OCR text</option>
          <option value="caption">Captions</option>
          <option value="video_metadata">Video metadata</option>
          <option value="metadata">Metadata</option>
        </select>
        <select id="yearFilter" aria-label="Year filter">
          <option value="">All years</option>
        </select>
        <button type="button" class="globe-toggle" id="globeToggle" aria-expanded="false">Open location globe</button>
        <button type="button" id="reset">Reset</button>
      </div>
      <div class="status" id="status">Loading...</div>
      <section id="globePanel" class="globe-panel" aria-hidden="true">
        <div class="globe-stage">
          <canvas id="globeCanvas" aria-label="Interactive globe with document locations"></canvas>
          <div class="globe-popup" id="globePopup" hidden></div>
        </div>
      </section>
      <section id="results"></section>
      <div class="load-more" id="loadMoreWrap" hidden>
        <button type="button" id="loadMore">Load more</button>
        <div class="result-sentinel" id="resultSentinel" aria-hidden="true"></div>
      </div>
    </section>
  </main>
  <script>
    const $ = (id) => document.getElementById(id);
    const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[char]));
    const icon = (name) => {
      if (name === "source") return '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M3.6 9h16.8"/><path d="M3.6 15h16.8"/><path d="M12 3a14 14 0 0 1 0 18"/><path d="M12 3a14 14 0 0 0 0 18"/><path d="M15 9h5v5"/><path d="m20 9-6 6"/></svg>';
      return '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z"/><path d="M14 2v5h5"/><path d="M8 11h8"/><path d="M8 15h8"/><path d="M8 19h5"/></svg>';
    };
    const track = (name, props = {}) => {
      if (typeof window.plausible === "function") {
        window.plausible(name, { props });
      }
    };
    let archive = null;
    let docs = [];
    let currentView = "home";
    const SEARCH_BATCH_SIZE = 20;
    const resultState = { matches: [], visible: 0 };
    let resultObserver = null;
    const globeState = { ready: false, initializing: false, locations: [], markers: [], selected: null, selectedIndex: null };

    function searchable(doc) {
      return [
        doc.title, doc.agency, doc.incident_date, doc.incident_location,
        doc.summary?.quick_summary, doc.summary?.overview,
        ...(doc.summary?.mysterious_uap_element || []).map((item) => item.text || item.label),
        ...(doc.summary?.detailed_contents || []).map((item) => item.text || item.label),
        ...(doc.summary?.references || []).map((item) => item.snippet || item.label),
        ...(doc.tags || [])
      ].join(" ").toLowerCase();
    }

    function scoreDoc(doc, terms) {
      if (!terms.length) return 1;
      const haystack = doc._search;
      let score = 0;
      for (const term of terms) {
        if (!haystack.includes(term)) return 0;
        if ((doc.title || "").toLowerCase().includes(term)) score += 6;
        if ((doc.tags || []).some((tag) => tag.toLowerCase().includes(term))) score += 4;
        if ((doc.summary?.quick_summary || "").toLowerCase().includes(term)) score += 3;
        score += 1;
      }
      return score;
    }

    function docYear(doc) {
      const text = [doc.incident_date, doc.release_date, doc.title].filter(Boolean).join(" ");
      const matches = [...text.matchAll(/\b(18|19|20)\d{2}\b/g)].map((match) => Number(match[0]));
      return matches.length ? matches[0] : 0;
    }

    function allLocations() {
      const out = [];
      const seen = new Set();
      docs.forEach((doc) => {
        (doc.locations || []).forEach((location) => {
          const lat = Number(location.latitude);
          const lon = Number(location.longitude);
          if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
          const key = `${doc.doc_id}:${lat.toFixed(4)}:${lon.toFixed(4)}:${location.raw_location}`;
          if (seen.has(key)) return;
          seen.add(key);
          out.push({
            ...location,
            doc_id: doc.doc_id,
            title: doc.title,
            agency: doc.agency,
            source_url: doc.source_url || doc.media?.document_url || "",
            quick_summary: doc.summary?.quick_summary || doc.summary?.overview || "",
            latitude: lat,
            longitude: lon,
          });
        });
      });
      return out;
    }

    function pageUrl(url, page) {
      if (!url || !page) return url || "";
      return `${url}#page=${page}`;
    }

    function sourceKinds(doc) {
      return new Set((doc.summary?.references || []).map((ref) => ref.source_kind).filter(Boolean));
    }

    function videoUrl(value) {
      if (!value) return "";
      if (typeof value === "string" && value.startsWith("http")) return value;
      if (typeof value === "object" && value.src) return String(value.src);
      const text = String(value);
      const match = text.match(/['"]src['"]\s*:\s*['"]([^'"]+)['"]/);
      return match ? match[1] : text;
    }

    function isImageUrl(value) {
      return /\.(avif|gif|jpe?g|png|webp)(\?|#|$)/i.test(String(value || ""));
    }

    function isRichMedia(doc) {
      return Boolean(videoUrl(doc.media?.video_url)) || isImageUrl(doc.media?.document_url);
    }

    function hasMediaKind(doc, kind) {
      const assets = doc.assets || [];
      if (kind === "media_image") return assets.some((asset) => asset.media_type === "image" && asset.kind !== "thumbnail");
      if (kind === "media_video") return Boolean(videoUrl(doc.media?.video_url)) || assets.some((asset) => asset.media_type === "video" || asset.kind === "video");
      return false;
    }

    function matchesSourceFilter(doc, source) {
      if (!source) return true;
      if (source.startsWith("media_")) return hasMediaKind(doc, source);
      return sourceKinds(doc).has(source);
    }

    function renderMedia(doc) {
      const media = doc.media || {};
      const playableVideo = videoUrl(media.video_url);
      if (playableVideo) {
        const poster = media.thumbnail_url ? ` poster="${esc(media.thumbnail_url)}"` : "";
        return `<video controls preload="metadata"${poster} src="${esc(playableVideo)}"></video>`;
      }
      const imagePreview = isImageUrl(media.document_url) ? media.document_url : media.thumbnail_url;
      if (imagePreview) {
        return `<a href="${esc(media.document_url || doc.source_url || imagePreview)}" target="_blank" rel="noopener"><img loading="lazy" src="${esc(imagePreview)}" alt="${esc(doc.title)} preview"></a>`;
      }
      return `<div class="muted">No public preview</div>`;
    }

    function renderBestMedia(item) {
      const media = item.media || {};
      const playableVideo = videoUrl(media.video_url);
      if (playableVideo) {
        const poster = media.thumbnail_url ? ` poster="${esc(media.thumbnail_url)}"` : "";
        return `<video controls preload="metadata"${poster} src="${esc(playableVideo)}"></video>`;
      }
      const imagePreview = isImageUrl(media.document_url) ? media.document_url : media.thumbnail_url;
      if (imagePreview) {
        return `<img loading="lazy" src="${esc(imagePreview)}" alt="${esc(item.title)} preview">`;
      }
      return `<div class="muted">No preview</div>`;
    }

    function renderBestOf(items) {
      const panel = $("bestOf");
      if (!panel || !items?.length) return;
      panel.innerHTML = `
        <div class="best-head">
          <div class="best-title-row">
            <h2>HIGHLIGHTS</h2>
            <div class="best-count">${items.length} discussed records, videos, and photos</div>
          </div>
        </div>
        <div class="best-grid">
          ${items.map((item) => `
            <article class="best-card">
              <div class="best-media">${renderBestMedia(item)}</div>
              <div class="best-body">
                <div class="best-label">${esc(item.kicker)}</div>
                <h3 class="best-title">${esc(item.title)}</h3>
                <p class="best-summary">${esc(item.summary)}</p>
                <ul class="best-facts">${(item.facts || []).map((fact) => `<li>${esc(fact)}</li>`).join("")}</ul>
                <button type="button" class="button best-link" data-feature-doc="${esc(item.doc_id)}">Open in index</button>
              </div>
            </article>
          `).join("")}
        </div>
      `;
      panel.hidden = false;
    }

    function actionLinks(doc) {
      const pdf = doc.media?.document_url || doc.source_url;
      const gov = doc.source_url || pdf;
      const video = videoUrl(doc.media?.video_url);
      const links = [];
      if (gov) links.push(`<a class="button icon-button source-button" href="${esc(gov)}" target="_blank" rel="noopener" data-track="source" data-doc-id="${esc(doc.doc_id)}" aria-label="Government source" title="Government source">${icon("source")}<span>Source</span></a>`);
      if (video) links.push(`<a class="button icon-button source-button" href="${esc(video)}" target="_blank" rel="noopener" data-track="video" data-doc-id="${esc(doc.doc_id)}" aria-label="Open video" title="Open video">${icon("source")}<span>Video</span></a>`);
      links.push(`<button type="button" class="icon-button summary-button details-button" data-doc-id="${esc(doc.doc_id)}" aria-label="Read summary details" title="Read summary details">${icon("summary")}<span>Summary</span></button>`);
      return `<div class="actions">${links.join("")}</div>`;
    }

    function renderTags(tags) {
      if (!tags?.length) return "";
      return `<div class="tags">${tags.slice(0, 10).map((tag) => `<button class="tag" type="button" data-tag="${esc(tag)}">${esc(tag)}</button>`).join("")}</div>`;
    }

    function renderDetails(doc) {
      const mystery = doc.summary?.mysterious_uap_element || [];
      const details = doc.summary?.detailed_contents || [];
      const related = doc.related_documents || [];
      return `
        <div class="details">
          <h3>Mysterious UAP Element</h3>
          <ul>${mystery.map((item) => `<li>${esc(item.label || item.text || item)}</li>`).join("")}</ul>
          <h3>More Detailed Contents</h3>
          <ul>${details.map((item) => `<li>${esc(item.label || item.text || item)}</li>`).join("")}</ul>
          ${related.length ? `<h3>Related Documents</h3><ul>${related.map((item) => `<li><button class="tag" type="button" data-related="${esc(item.doc_id)}">${esc(item.title)}</button> <span class="muted">${esc(item.reason)}</span></li>`).join("")}</ul>` : ""}
          <p class="source-note">${esc(doc.summary?.source_note || "")}</p>
        </div>
      `;
    }

    function renderDoc(doc) {
      const mediaClass = isRichMedia(doc) ? " media-rich" : "";
      return `
        <article class="result${mediaClass}" id="doc-${esc(doc.doc_id)}">
          <div class="shell">
            <div class="body">
              <h2>${esc(doc.title)}</h2>
              <div class="muted">${esc([doc.agency, doc.incident_date, doc.incident_location].filter(Boolean).join(" | "))}</div>
              ${renderTags(doc.tags)}
              <p>${esc(doc.summary?.quick_summary || doc.summary?.overview || "No summary available.")}</p>
              ${actionLinks(doc)}
              ${renderDetails(doc)}
            </div>
            <div class="media">${renderMedia(doc)}</div>
          </div>
        </article>
      `;
    }

    function agencyOptions() {
      const agencies = [...new Set(docs.map((doc) => doc.agency).filter(Boolean))].sort();
      $("agencyFilter").innerHTML = `<option value="">All agencies</option>` + agencies.map((agency) => `<option value="${esc(agency)}">${esc(agency)}</option>`).join("");
    }

    function yearOptions() {
      const years = [...new Set(docs.map(docYear).filter(Boolean))].sort((a, b) => b - a);
      $("yearFilter").innerHTML = `<option value="">All years</option>` + years.map((year) => `<option value="${year}">${year}</option>`).join("");
    }

    function locationLabel(location) {
      return location.normalized_location || location.raw_location || `${location.latitude.toFixed(2)}, ${location.longitude.toFixed(2)}`;
    }

    function updateGlobeSelection() {
      globeState.markers.forEach((marker, index) => {
        const selected = index === globeState.selectedIndex;
        marker.material = selected ? marker.userData.selectedMaterial : marker.userData.defaultMaterial;
        marker.scale.setScalar(selected ? 1.8 : 1);
      });
    }

    function renderSelectedLocation(location) {
      if (!location) {
        if ($("globePopup")) $("globePopup").hidden = true;
        return;
      }
      renderGlobePopup(location);
    }

    function renderGlobePopup(location) {
      const popup = $("globePopup");
      if (!popup || !location) return;
      const fullSummary = location.quick_summary || "";
      const summary = fullSummary ? fullSummary.slice(0, 360) : "No summary is available for this checkpoint.";
      popup.innerHTML = `
        <button type="button" class="globe-close" data-globe-close aria-label="Close location">x</button>
        <h3>${esc(locationLabel(location))}</h3>
        <p class="muted">${esc(location.precision || "location")} - ${esc(location.method || "indexed location")}</p>
        <p><strong>${esc(location.title || "Document")}</strong></p>
        <p>${esc(summary)}${fullSummary.length > 360 ? "..." : ""}</p>
        <div class="actions">
          ${location.source_url ? `<a class="button source-button" href="${esc(location.source_url)}" target="_blank" rel="noopener" data-track="globe_source" data-doc-id="${esc(location.doc_id)}">Source</a>` : ""}
          <button type="button" class="summary-button" data-globe-doc="${esc(location.doc_id)}">View result</button>
        </div>
      `;
      popup.hidden = false;
    }

    function latLonVector(lat, lon, radius) {
      const phi = (90 - lat) * Math.PI / 180;
      const theta = (lon + 180) * Math.PI / 180;
      return {
        x: -radius * Math.sin(phi) * Math.cos(theta),
        y: radius * Math.cos(phi),
        z: radius * Math.sin(phi) * Math.sin(theta),
      };
    }

    async function addCountryBorders(THREE, globeGroup) {
      try {
        const [topology, topojson] = await Promise.all([
          fetch("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json").then((response) => response.json()),
          import("https://cdn.jsdelivr.net/npm/topojson-client@3.1.0/+esm"),
        ]);
        const countries = topojson.feature(topology, topology.objects.countries);
        const borderMaterial = new THREE.LineBasicMaterial({ color: 0x72d7ff, transparent: true, opacity: 0.44 });
        countries.features.forEach((feature) => {
          const geom = feature.geometry;
          if (!geom) return;
          const polygons = geom.type === "Polygon" ? [geom.coordinates] : geom.coordinates;
          polygons.forEach((polygon) => {
            polygon.forEach((ring) => {
              if (!ring || ring.length < 2) return;
              const points = ring.map(([lon, lat]) => {
                const p = latLonVector(lat, lon, 1.014);
                return new THREE.Vector3(p.x, p.y, p.z);
              });
              globeGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), borderMaterial));
            });
          });
        });
      } catch (error) {
        console.warn("Country borders could not be loaded", error);
      }
    }

    async function initGlobe() {
      if (globeState.ready || globeState.initializing) return;
      globeState.initializing = true;
      globeState.locations = allLocations();
      renderSelectedLocation(null);
      const THREE = await import("https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js");
      const canvas = $("globeCanvas");
      const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
      camera.position.set(0, 0, 3.8);
      const globeGroup = new THREE.Group();
      scene.add(globeGroup);
      scene.add(new THREE.AmbientLight(0x8fffb8, 1.25));
      const light = new THREE.DirectionalLight(0x72d7ff, 1.8);
      light.position.set(3, 2, 4);
      scene.add(light);
      const globe = new THREE.Mesh(
        new THREE.SphereGeometry(1, 96, 48),
        new THREE.MeshStandardMaterial({
          color: 0x07170f,
          roughness: 0.8,
          metalness: 0.1,
          emissive: 0x092414,
          emissiveIntensity: 0.62,
          transparent: true,
          opacity: 0.96,
        })
      );
      globeGroup.add(globe);
      const gridMaterial = new THREE.LineBasicMaterial({ color: 0x42ff8c, transparent: true, opacity: 0.24 });
      for (let lat = -60; lat <= 60; lat += 30) {
        const points = [];
        for (let lon = -180; lon <= 180; lon += 4) {
          const p = latLonVector(lat, lon, 1.006);
          points.push(new THREE.Vector3(p.x, p.y, p.z));
        }
        globeGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), gridMaterial));
      }
      for (let lon = -150; lon <= 180; lon += 30) {
        const points = [];
        for (let lat = -90; lat <= 90; lat += 4) {
          const p = latLonVector(lat, lon, 1.008);
          points.push(new THREE.Vector3(p.x, p.y, p.z));
        }
        globeGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), gridMaterial));
      }
      await addCountryBorders(THREE, globeGroup);
      const markerGeometry = new THREE.SphereGeometry(0.025, 16, 16);
      const placeMaterial = new THREE.MeshBasicMaterial({ color: 0x42ff8c });
      const coordinateMaterial = new THREE.MeshBasicMaterial({ color: 0xffd166 });
      const selectedMaterial = new THREE.MeshBasicMaterial({ color: 0x72d7ff });
      globeState.locations.forEach((location, index) => {
        const p = latLonVector(location.latitude, location.longitude, 1.045);
        const marker = new THREE.Mesh(markerGeometry, location.precision === "coordinate" ? coordinateMaterial : placeMaterial);
        marker.position.set(p.x, p.y, p.z);
        marker.userData.locationIndex = index;
        marker.userData.defaultMaterial = marker.material;
        marker.userData.selectedMaterial = selectedMaterial;
        globeGroup.add(marker);
        globeState.markers.push(marker);
      });
      const raycaster = new THREE.Raycaster();
      const pointer = new THREE.Vector2();
      let dragging = false;
      let moved = false;
      let lastX = 0;
      let lastY = 0;
      let touchMode = "";
      let touchStartX = 0;
      let touchStartY = 0;
      let pinchStartDistance = 0;
      let pinchStartZ = camera.position.z;
      const clampZoom = (z) => Math.max(2.25, Math.min(6.2, z));
      const touchDistance = (touches) => {
        if (!touches || touches.length < 2) return 0;
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.hypot(dx, dy);
      };
      const pickMarker = (clientX, clientY) => {
        const rect = canvas.getBoundingClientRect();
        pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
        pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
        raycaster.setFromCamera(pointer, camera);
        const hit = raycaster.intersectObjects(globeState.markers)[0];
        if (hit) selectGlobeLocation(hit.object.userData.locationIndex);
      };
      function resize() {
        const rect = canvas.parentElement.getBoundingClientRect();
        const width = Math.max(320, rect.width);
        const minHeight = window.matchMedia("(max-width: 760px)").matches ? 300 : 360;
        const height = Math.max(minHeight, rect.height);
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
      }
      canvas.addEventListener("pointerdown", (event) => {
        if (event.pointerType === "touch") return;
        event.preventDefault();
        dragging = true;
        moved = false;
        lastX = event.clientX;
        lastY = event.clientY;
        canvas.setPointerCapture(event.pointerId);
      });
      canvas.addEventListener("pointermove", (event) => {
        if (event.pointerType === "touch") return;
        if (!dragging) return;
        event.preventDefault();
        const dx = event.clientX - lastX;
        const dy = event.clientY - lastY;
        const speed = 0.006;
        if (Math.abs(dx) + Math.abs(dy) > 6) moved = true;
        globeGroup.rotation.y += dx * speed;
        globeGroup.rotation.x += dy * speed * 0.7;
        globeGroup.rotation.x = Math.max(-1.15, Math.min(1.15, globeGroup.rotation.x));
        lastX = event.clientX;
        lastY = event.clientY;
      });
      canvas.addEventListener("wheel", (event) => {
        event.preventDefault();
        const delta = Math.sign(event.deltaY) * 0.26;
        camera.position.z = clampZoom(camera.position.z + delta);
        camera.updateProjectionMatrix();
      }, { passive: false });
      canvas.addEventListener("pointerup", (event) => {
        if (event.pointerType === "touch") return;
        dragging = false;
        if (canvas.hasPointerCapture(event.pointerId)) {
          canvas.releasePointerCapture(event.pointerId);
        }
        if (moved) return;
        pickMarker(event.clientX, event.clientY);
      });
      canvas.addEventListener("pointercancel", (event) => {
        if (event.pointerType === "touch") return;
        dragging = false;
      });
      canvas.addEventListener("touchstart", (event) => {
        event.preventDefault();
        moved = false;
        if (event.touches.length >= 2) {
          touchMode = "pinch";
          pinchStartDistance = touchDistance(event.touches);
          pinchStartZ = camera.position.z;
          moved = true;
          return;
        }
        const touch = event.touches[0];
        if (!touch) return;
        touchMode = "rotate";
        touchStartX = touch.clientX;
        touchStartY = touch.clientY;
        lastX = touch.clientX;
        lastY = touch.clientY;
      }, { passive: false });
      canvas.addEventListener("touchmove", (event) => {
        event.preventDefault();
        if (event.touches.length >= 2) {
          if (touchMode !== "pinch") {
            touchMode = "pinch";
            pinchStartDistance = touchDistance(event.touches);
            pinchStartZ = camera.position.z;
          }
          const distance = touchDistance(event.touches);
          if (pinchStartDistance > 0 && distance > 0) {
            camera.position.z = clampZoom(pinchStartZ * (pinchStartDistance / distance));
            camera.updateProjectionMatrix();
          }
          moved = true;
          return;
        }
        const touch = event.touches[0];
        if (!touch || touchMode !== "rotate") return;
        const dx = touch.clientX - lastX;
        const dy = touch.clientY - lastY;
        if (Math.abs(touch.clientX - touchStartX) + Math.abs(touch.clientY - touchStartY) > 6) moved = true;
        globeGroup.rotation.y += dx * 0.009;
        globeGroup.rotation.x += dy * 0.0063;
        globeGroup.rotation.x = Math.max(-1.15, Math.min(1.15, globeGroup.rotation.x));
        lastX = touch.clientX;
        lastY = touch.clientY;
      }, { passive: false });
      canvas.addEventListener("touchend", (event) => {
        event.preventDefault();
        if (event.touches.length >= 2) {
          touchMode = "pinch";
          pinchStartDistance = touchDistance(event.touches);
          pinchStartZ = camera.position.z;
          return;
        }
        if (event.touches.length === 1) {
          const touch = event.touches[0];
          touchMode = "rotate";
          lastX = touch.clientX;
          lastY = touch.clientY;
          touchStartX = touch.clientX;
          touchStartY = touch.clientY;
          return;
        }
        const changed = event.changedTouches[0];
        if (touchMode === "rotate" && changed && !moved) {
          pickMarker(changed.clientX, changed.clientY);
        }
        touchMode = "";
        pinchStartDistance = 0;
      }, { passive: false });
      canvas.addEventListener("touchcancel", () => {
        touchMode = "";
        pinchStartDistance = 0;
        moved = false;
      }, { passive: false });
      window.addEventListener("resize", resize);
      function animate() {
        requestAnimationFrame(animate);
        resize();
        renderer.render(scene, camera);
      }
      resize();
      animate();
      globeState.ready = true;
      globeState.initializing = false;
    }

    function selectGlobeLocation(index) {
      const location = globeState.locations[index];
      globeState.selected = location || null;
      globeState.selectedIndex = location ? index : null;
      updateGlobeSelection();
      renderSelectedLocation(globeState.selected);
      if (location) {
        track("globe_checkpoint", { doc_id: location.doc_id, precision: location.precision || "", method: location.method || "" });
      }
    }

    function clearGlobeLocation() {
      globeState.selected = null;
      globeState.selectedIndex = null;
      updateGlobeSelection();
      renderSelectedLocation(null);
    }

    function setView(view, options = {}) {
      currentView = view === "search" ? "search" : "home";
      const home = $("homeView");
      const search = $("searchView");
      if (home) home.hidden = currentView !== "home";
      if (search) search.hidden = currentView !== "search";
      document.querySelectorAll("[data-view-target]").forEach((button) => {
        button.classList.toggle("active", button.dataset.viewTarget === currentView);
      });
      if (currentView === "search") {
        initGlobe();
      }
      if (options.scroll) {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    }

    function searchHash(query) {
      const q = String(query || "").trim();
      return q ? `#search?q=${encodeURIComponent(q)}` : "#search";
    }

    function setRouteHash(hash) {
      if (window.location.hash === hash) return;
      history.pushState(null, "", hash || `${window.location.pathname}${window.location.search}`);
    }

    function openSearch(query = "", options = {}) {
      const q = String(query || "").trim();
      $("q").value = q;
      $("homeQ").value = q;
      if (options.resetFilters) {
        $("agencyFilter").value = "";
        $("sourceFilter").value = "";
        $("yearFilter").value = "";
      }
      setView("search", { scroll: options.scroll });
      performSearch();
      if (options.updateHash) {
        setRouteHash(searchHash(q));
      }
    }

    function showHome(options = {}) {
      setView("home", { scroll: options.scroll });
      if (options.updateHash) {
        setRouteHash("");
      }
    }

    function applyRoute() {
      const hash = window.location.hash || "";
      if (hash.startsWith("#search")) {
        const queryText = hash.includes("?") ? hash.slice(hash.indexOf("?") + 1) : "";
        const params = new URLSearchParams(queryText);
        openSearch(params.get("q") || "", { updateHash: false });
      } else {
        showHome({ updateHash: false });
      }
    }

    function toggleGlobe() {
      const panel = $("globePanel");
      const button = $("globeToggle");
      if (!panel || !button) return;
      const open = panel.classList.toggle("open");
      button.textContent = open ? "Hide location globe" : "Open location globe";
      button.setAttribute("aria-expanded", open ? "true" : "false");
      panel.setAttribute("aria-hidden", open ? "false" : "true");
      track("globe_toggle", { open: open ? "true" : "false" });
    }

    function renderSearchResults() {
      const total = resultState.matches.length;
      const visible = Math.min(resultState.visible, total);
      const shownDocs = resultState.matches.slice(0, visible);
      $("status").textContent = total
        ? `${visible} of ${total} result${total === 1 ? "" : "s"} shown from ${docs.length} documents.`
        : `No matching documents from ${docs.length} documents.`;
      $("results").innerHTML = shownDocs.length ? shownDocs.map(renderDoc).join("") : `<div class="empty">No matching documents.</div>`;
      const hasMore = visible < total;
      const wrap = $("loadMoreWrap");
      const button = $("loadMore");
      if (wrap) wrap.hidden = !hasMore;
      if (button) button.textContent = hasMore ? `Load more (${total - visible} remaining)` : "Load more";
    }

    function loadMoreResults() {
      if (currentView !== "search") return;
      if (resultState.visible >= resultState.matches.length) return;
      resultState.visible = Math.min(resultState.visible + SEARCH_BATCH_SIZE, resultState.matches.length);
      renderSearchResults();
      track("load_more_results", { visible: String(resultState.visible), total: String(resultState.matches.length) });
    }

    function setupResultObserver() {
      const sentinel = $("resultSentinel");
      if (!sentinel || resultObserver || !("IntersectionObserver" in window)) return;
      resultObserver = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          loadMoreResults();
        }
      }, { rootMargin: "360px 0px" });
      resultObserver.observe(sentinel);
    }

    function performSearch() {
      const q = $("q").value.trim().toLowerCase();
      const agency = $("agencyFilter").value;
      const source = $("sourceFilter").value;
      const year = $("yearFilter").value;
      const terms = q.split(/\s+/).filter(Boolean);
      const scored = docs
        .filter((doc) => !agency || doc.agency === agency)
        .filter((doc) => matchesSourceFilter(doc, source))
        .filter((doc) => !year || String(docYear(doc)) === year)
        .map((doc) => [scoreDoc(doc, terms), doc])
        .filter(([score]) => score > 0)
        .sort((a, b) => {
          if (terms.length) return b[0] - a[0] || a[1].title.localeCompare(b[1].title);
          return (a[1].row_number || 0) - (b[1].row_number || 0) || a[1].title.localeCompare(b[1].title);
        })
        .map(([, doc]) => doc);
      resultState.matches = scored;
      resultState.visible = Math.min(SEARCH_BATCH_SIZE, scored.length);
      renderSearchResults();
    }

    function resetArchiveView() {
      $("q").value = "";
      $("homeQ").value = "";
      $("agencyFilter").value = "";
      $("sourceFilter").value = "";
      $("yearFilter").value = "";
      globeState.selected = null;
      globeState.selectedIndex = null;
      updateGlobeSelection();
      renderSelectedLocation(null);
      const globePanel = $("globePanel");
      const globeButton = $("globeToggle");
      if (globePanel && globeButton) {
        globePanel.classList.remove("open");
        globePanel.setAttribute("aria-hidden", "true");
        globeButton.textContent = "Open location globe";
        globeButton.setAttribute("aria-expanded", "false");
      }
      document.querySelectorAll(".result.open").forEach((card) => card.classList.remove("open"));
      openSearch("", { updateHash: true, scroll: true });
    }

    document.addEventListener("click", (event) => {
      const viewTarget = event.target.closest("[data-view-target]");
      if (viewTarget) {
        if (viewTarget.dataset.viewTarget === "search") {
          track("nav_search");
          openSearch($("q").value, { updateHash: true, scroll: true });
        } else {
          track("nav_highlights");
          showHome({ updateHash: true, scroll: true });
        }
      }
      const tag = event.target.closest("[data-tag]");
      if (tag) {
        track("tag_filter", { tag: tag.dataset.tag });
        openSearch(tag.dataset.tag, { updateHash: true, scroll: true });
      }
      const button = event.target.closest(".details-button");
      if (button) {
        const card = document.getElementById(`doc-${button.dataset.docId}`);
        if (card) card.classList.toggle("open");
        track("summary_toggle", { doc_id: button.dataset.docId, open: card?.classList.contains("open") ? "true" : "false" });
      }
      const tracked = event.target.closest("[data-track]");
      if (tracked) {
        track(tracked.dataset.track, { doc_id: tracked.dataset.docId || "" });
      }
      const related = event.target.closest("[data-related]");
      if (related) {
        const relatedDoc = docs.find((doc) => doc.doc_id === related.dataset.related);
        track("related_doc", { doc_id: related.dataset.related });
        openSearch(relatedDoc ? relatedDoc.title : "", { resetFilters: true, updateHash: true });
        const card = document.getElementById(`doc-${related.dataset.related}`);
        if (card) {
          card.classList.add("open");
        }
      }
      const globeDoc = event.target.closest("[data-globe-doc]");
      if (globeDoc) {
        const doc = docs.find((item) => item.doc_id === globeDoc.dataset.globeDoc);
        if (!doc) return;
        track("globe_view_result", { doc_id: doc.doc_id });
        openSearch(doc.title, { resetFilters: true, updateHash: true });
        window.setTimeout(() => {
          const card = document.getElementById(`doc-${doc.doc_id}`);
          if (card) {
            card.classList.add("open");
          }
        }, 80);
      }
      const globeClose = event.target.closest("[data-globe-close]");
      if (globeClose) {
        clearGlobeLocation();
      }
      const featured = event.target.closest("[data-feature-doc]");
      if (featured) {
        const doc = docs.find((item) => item.doc_id === featured.dataset.featureDoc);
        if (!doc) return;
        track("featured_index_entry", { doc_id: doc.doc_id });
        openSearch(doc.title, { resetFilters: true, updateHash: true, scroll: true });
        window.setTimeout(() => {
          const card = document.getElementById(`doc-${doc.doc_id}`);
          if (card) {
            card.classList.add("open");
            card.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        }, 80);
      }
    });
    $("homeSearchForm").addEventListener("submit", (event) => {
      event.preventDefault();
      track("home_search", { query_length: String($("homeQ").value.trim().length) });
      openSearch($("homeQ").value, { resetFilters: true, updateHash: true, scroll: true });
    });
    $("searchForm").addEventListener("submit", (event) => {
      event.preventDefault();
      track("search", { query_length: String($("q").value.trim().length) });
      openSearch($("q").value, { updateHash: true });
    });
    $("agencyFilter").addEventListener("change", () => {
      track("filter_agency", { value: $("agencyFilter").value || "all" });
      performSearch();
    });
    $("sourceFilter").addEventListener("change", () => {
      track("filter_source", { value: $("sourceFilter").value || "all" });
      performSearch();
    });
    $("yearFilter").addEventListener("change", () => {
      track("filter_year", { value: $("yearFilter").value || "all" });
      performSearch();
    });
    $("brandReset").addEventListener("click", () => {
      track("reset", { control: "title" });
      $("q").value = "";
      $("homeQ").value = "";
      $("agencyFilter").value = "";
      $("sourceFilter").value = "";
      $("yearFilter").value = "";
      showHome({ updateHash: true, scroll: true });
    });
    $("reset").addEventListener("click", () => {
      track("reset", { control: "button" });
      resetArchiveView();
    });
    $("globeToggle").addEventListener("click", toggleGlobe);
    $("loadMore").addEventListener("click", loadMoreResults);
    window.addEventListener("popstate", applyRoute);
    window.addEventListener("hashchange", applyRoute);

    fetch(`data/documents.json?v=${Date.now()}`, { cache: "no-store" })
      .then((response) => response.json())
      .then((payload) => {
        archive = payload;
        docs = payload.documents.map((doc) => ({ ...doc, _search: searchable(doc) }));
        agencyOptions();
        yearOptions();
        globeState.locations = allLocations();
        renderBestOf(payload.featured_documents || []);
        setupResultObserver();
        applyRoute();
      })
      .catch((error) => {
        $("status").textContent = `Failed to load public index: ${error.message}`;
      });
  </script>
</body>
</html>
"""


TAG_STOPWORDS = STOPWORDS | {
    "additional",
    "available",
    "caption",
    "captions",
    "case",
    "chunks",
    "civilian",
    "compliance",
    "complete",
    "concerning",
    "contains",
    "contents",
    "coordinates",
    "dated",
    "description",
    "derived",
    "detailed",
    "director",
    "department",
    "document",
    "documents",
    "excerpt",
    "file",
    "flying",
    "general",
    "government",
    "include",
    "includes",
    "incident",
    "indexed",
    "information",
    "investigative",
    "location",
    "locations",
    "media",
    "metadata",
    "native",
    "object",
    "objects",
    "ocr",
    "page",
    "pages",
    "pdf",
    "primarily",
    "provided",
    "quick",
    "received",
    "record",
    "recorded",
    "records",
    "reference",
    "references",
    "release",
    "report",
    "reports",
    "section",
    "submitted",
    "source",
    "sources",
    "summary",
    "text",
    "thumbnail",
    "unidentified",
    "video",
    "which",
    "written",
    "your",
}

TAG_ALIASES = {
    "aacs": "AACS",
    "aaro": "AARO",
    "aerial": "Aerial phenomena",
    "anomalous": "Anomalous object",
    "anomaly": "Anomalous object",
    "aircraft": "Aircraft",
    "airplane": "Aircraft",
    "airplanes": "Aircraft",
    "apollo": "Apollo",
    "astronaut": "Astronauts",
    "astronauts": "Astronauts",
    "ball": "Spherical object",
    "balls": "Spherical object",
    "bogey": "Radar contact",
    "bogeys": "Radar contact",
    "caa": "CAA",
    "disc": "Discs",
    "discs": "Discs",
    "disk": "Discs",
    "disks": "Discs",
    "dod": "DOD",
    "drone": "Drone",
    "drones": "Drone",
    "dvids": "DVIDS",
    "fbi": "FBI",
    "fireball": "Fireball",
    "fireballs": "Fireball",
    "foo": "Foo fighters",
    "foofighter": "Foo fighters",
    "foofighters": "Foo fighters",
    "gemini": "Gemini",
    "helicopter": "Helicopter",
    "helicopters": "Helicopter",
    "light": "Lights",
    "lights": "Lights",
    "missile": "Missile",
    "missiles": "Missile",
    "moon": "Moon",
    "nasa": "NASA",
    "orb": "Orbs",
    "orbs": "Orbs",
    "radar": "Radar",
    "rocket": "Rocket",
    "rockets": "Rocket",
    "saucer": "Saucers",
    "saucers": "Saucers",
    "sphere": "Spherical object",
    "spheres": "Spherical object",
    "uap": "UAP",
    "uaps": "UAP",
    "ufo": "UFO",
    "ufos": "UFO",
    "usaf": "USAF",
    "uss": "Navy",
    "weapon": "Weapons",
    "weapons": "Weapons",
}

TAG_PHRASES = [
    (re.compile(r"\ball[- ]domain\s+anomal(?:y|ous)\s+resolution\b", re.I), "AARO"),
    (re.compile(r"\bair\s+force\b", re.I), "Air Force"),
    (re.compile(r"\bfoo[- ]?fighters?\b", re.I), "Foo fighters"),
    (re.compile(r"\bflying\s+(?:disc|disk|saucer)s?\b", re.I), "Flying discs"),
    (re.compile(r"\bradar\s+(?:contact|track|return|targets?)s?\b", re.I), "Radar contact"),
    (re.compile(r"\b(?:unidentified|unknown)\s+(?:flying\s+)?objects?\b", re.I), "Unidentified object"),
    (re.compile(r"\b(?:bright|flashing|blinking|green|red|white)\s+lights?\b", re.I), "Lights"),
    (re.compile(r"\b(?:lunar|moon)\s+(?:surface|orbit|flash|phenomena)\b", re.I), "Lunar observation"),
    (re.compile(r"\bhelicopter\s+(?:crew|sighting|encounter)\b", re.I), "Helicopter encounter"),
    (re.compile(r"\bflight\s+(?:crew|service|safety|operations?)\b", re.I), "Flight operations"),
    (re.compile(r"\b(?:photo|image|photograph|video|film)\s+(?:analysis|evidence|footage)\b", re.I), "Media evidence"),
]

AGENCY_TAGS = {
    "Department of War": "War Department",
    "Department of State": "State Department",
    "FBI": "FBI",
    "NASA": "NASA",
}

FEATURED_SELECTIONS = [
    {
        "match": "Western US Event",
        "kicker": "Headline modern case",
        "summary": "The most accessible modern entry point in the release: seven federal employees describe multiple categories of phenomena over two days in the western United States. It is useful because the accounts can be compared side by side, from distant orb activity to a close stationary light and a translucent kite-like object.",
        "facts": [
            "Agency: Department of War",
            "Incident year: 2023",
            "Why it stands out: multiple witnesses in one indexed case",
        ],
    },
    {
        "match": "USPER Statement about UAP Sighting",
        "kicker": "Senior official narrative",
        "summary": "A heavily redacted witness statement attributed in the archive metadata to a US person, describing a multi-hour western US encounter and response activity. It became one of the most discussed documents because it reads like a narrative report while still preserving the uncertainty and redactions of the source record.",
        "facts": [
            "Agency: Department of State",
            "Incident year: 2025",
            "Why it stands out: detailed first-person style account with redactions",
        ],
    },
    {
        "match": "FBI September 2023 Sighting - Composite Sketch",
        "kicker": "FBI visual reconstruction",
        "summary": "A site photo with an FBI Lab graphic overlay tied to September 2023 eyewitness material. The public metadata describes an apparent bronze ellipsoid emerging from a bright light, with estimated size and abrupt disappearance recorded as part of the case file.",
        "facts": [
            "Agency: FBI",
            "Incident date: September 1, 2023",
            "Why it stands out: image-based record tied to witness interviews",
        ],
    },
    {
        "match": "FBI Photo A1",
        "kicker": "Late-2025 image set",
        "summary": "One of the release's western US evidence images, presented as an infrared still with accompanying source media. It belongs near the top because many readers look first for photos and videos, and this image cluster is part of the same modern visual trail that drew outside attention.",
        "facts": [
            "Agency: FBI",
            "Incident date: Late 2025",
            "Why it stands out: public photo record with linked media",
        ],
    },
    {
        "match": "NASA-UAP-VM6, Apollo 17, 1972",
        "kicker": "Apollo lunar image",
        "summary": "A released Apollo 17 lunar image record showing a highlighted area above the Moon's surface. It is one of the strongest landing-page visuals in the archive because it connects the public image set to the Apollo transcript and debriefing cluster.",
        "facts": [
            "Agency: NASA",
            "Incident year: 1972",
            "Why it stands out: visual lunar record with highlighted anomaly area",
        ],
    },
    {
        "match": "NASA-UAP-D2, Apollo 17 Transcript, 1972",
        "kicker": "Lunar transcript",
        "summary": "An Apollo 17 air-to-ground transcript excerpt centered on a lunar-surface observation near Grimaldi. The record anchors the lunar imagery cluster to mission context, speakers, and page-level transcript provenance rather than leaving the image as a free-floating curiosity.",
        "facts": [
            "Agency: NASA",
            "Incident year: 1972",
            "Why it stands out: mission transcript context for a lunar observation",
        ],
    },
    {
        "match": "255-t-763-r1b-excerpt",
        "kicker": "Gemini VII audio",
        "summary": "A NASA audio excerpt from Gemini VII in which Frank Borman reports an unidentified object during air-to-ground communications. The pairing of audio metadata and transcript material makes it one of the archive's most approachable spaceflight entries.",
        "facts": [
            "Agency: NASA",
            "Incident date: December 5, 1965",
            "Why it stands out: mission audio and transcript context",
        ],
    },
    {
        "match": "State Department UAP Cable 1, Papua New Guinea",
        "kicker": "Diplomatic cable",
        "summary": "A State Department cable from Port Moresby relaying a 1985 Papua New Guinea report through diplomatic channels. It is useful because the UFO account appears inside ordinary embassy traffic rather than a dedicated UFO case file.",
        "facts": [
            "Agency: Department of State",
            "Incident date: January 24, 1985",
            "Why it stands out: local report preserved in embassy correspondence",
        ],
    },
    {
        "match": "State Department UAP Cable 2, Kazakhstan",
        "kicker": "Post-Soviet cable",
        "summary": "A Kazakhstan cable that broadens the archive beyond US military sensor cases and legacy FBI files. It gives researchers a diplomatic-document comparison point for how unusual reports were forwarded, summarized, and preserved outside the headline American cases.",
        "facts": [
            "Agency: Department of State",
            "Incident year: 1994",
            "Why it stands out: international cable traffic in the release",
        ],
    },
    {
        "match": "331_120752_Numeric_Files_1944",
        "kicker": "Wartime foo-fighter file",
        "summary": "A SHAEF-era file collecting messages and memorandums about night phenomena, flak rockets, cylindrical objects, and blinking lights. It gives the archive historical depth: UAP-like reports appear here in the vocabulary and operational worries of 1944-1945 air war records.",
        "facts": [
            "Agency: Department of War",
            "Incident date: March 18, 1945",
            "Why it stands out: early military reports before the postwar flying-disc wave",
        ],
    },
    {
        "match": "65_HS1-834228961_62-HQ-83894_Section_5",
        "kicker": "FBI master file",
        "summary": "Part of the large FBI 62-HQ-83894 flying-disc file. This section represents the dense historical core of the release: memos, reports, and correspondence where the value is not one dramatic clip but the accumulated paper trail across the early UFO era.",
        "facts": [
            "Agency: FBI",
            "Records span: 1947-1968 cluster",
            "Why it stands out: deep archival FBI flying-disc material",
        ],
    },
    {
        "match": "DOW-UAP-PR46",
        "kicker": "INDOPACOM video",
        "summary": "A 2024 Indo-Pacific Command video record that drew attention because the object is described in outside coverage as football-shaped with radial projections. It gives the highlights section a clear modern sensor-video entry from the Pacific theater.",
        "facts": [
            "Agency: Department of War",
            "Incident region: East China Sea",
            "Why it stands out: widely discussed football-shaped video",
        ],
    },
    {
        "match": "DOW-UAP-PR47",
        "kicker": "Japan sensor case",
        "summary": "A 2023 INDOPACOM unresolved report connected to Japan-area sensor footage. It pairs well with PR46 because the two entries let visitors compare nearby command-region videos without starting in the full document table.",
        "facts": [
            "Agency: Department of War",
            "Incident region: Japan",
            "Why it stands out: modern Indo-Pacific video record",
        ],
    },
    {
        "match": "DOW-UAP-PR48",
        "kicker": "Wind-farm video",
        "summary": "A longer 2024 INDOPACOM video entry that outside coverage highlighted for its small bright target moving through a field of wind turbines. It is a good landing-page clip because the setting is visually distinctive and easy to recognize.",
        "facts": [
            "Agency: Department of War",
            "Incident year: 2024",
            "Why it stands out: distinctive wind-turbine sensor scene",
        ],
    },
    {
        "match": "DOW-UAP-PR34",
        "kicker": "Aegean maneuver video",
        "summary": "A Greece/Aegean video report discussed for sharp-looking directional changes over water. It belongs in highlights because it is one of the more memorable non-US locations in the modern sensor-video set.",
        "facts": [
            "Agency: Department of War",
            "Incident region: Greece",
            "Why it stands out: Aegean video with notable reported movement",
        ],
    },
    {
        "match": "DOW-UAP-PR28",
        "kicker": "Glowing IR signature",
        "summary": "A Greece-related unresolved report with an infrared frame described in release readers as a diffuse glowing halo around a central point. It adds a different visual flavor from the aircraft and maritime clips: less object-outline, more sensor signature.",
        "facts": [
            "Agency: Department of War",
            "Incident region: Greece",
            "Why it stands out: distinctive halo-like IR appearance",
        ],
    },
    {
        "match": "DOW-UAP-PR43",
        "kicker": "Africa airspace video",
        "summary": "A 2025 Africa unresolved report, useful because it widens the video set beyond the Middle East, Europe, and INDOPACOM clusters. The official release preview describes a military operator's reported UAP within African airspace.",
        "facts": [
            "Agency: Department of War",
            "Incident region: Africa",
            "Why it stands out: geographic breadth in the video release",
        ],
    },
    {
        "match": "DOW-UAP-PR49",
        "kicker": "2026 Army report",
        "summary": "A North America / Department of the Army video entry from 2026, making it one of the newest records in Release 01. It closes the highlights list by showing that the archive is not just historical material: it also includes very recent unresolved reporting.",
        "facts": [
            "Agency: Department of War",
            "Incident year: 2026",
            "Why it stands out: one of the newest records in the release",
        ],
    },
]


def media_type(kind: str, url: str) -> str:
    mime = mimetypes.guess_type(url)[0] or ""
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("video/"):
        return "video"
    if mime == "application/pdf" or kind == "document":
        return "document"
    if kind == "caption" or mime.startswith("text/"):
        return "text"
    return "file"


def video_src_from_metadata(raw_source_url: str, metadata_json: str) -> str:
    source_url = clean(raw_source_url)
    if source_url.startswith("http"):
        return source_url
    if (source_url.startswith('"') and source_url.endswith('"')) or (source_url.startswith("'") and source_url.endswith("'")):
        try:
            unwrapped = ast.literal_eval(source_url)
            if isinstance(unwrapped, str):
                source_url = clean(unwrapped)
                if source_url.startswith("http"):
                    return source_url
        except (SyntaxError, ValueError):
            pass
    if source_url.startswith("{"):
        try:
            value = ast.literal_eval(source_url)
            if isinstance(value, dict) and clean(value.get("src")):
                return clean(value.get("src"))
        except (SyntaxError, ValueError):
            pass
    try:
        metadata = json.loads(metadata_json or "{}")
    except json.JSONDecodeError:
        metadata = {}
    for item in metadata.get("all_mp4s") or []:
        src = clean(item.get("src"))
        if src:
            return src
    return source_url


def public_assets(conn, doc_id: str) -> List[Dict]:
    rows = conn.execute(
        """
        SELECT kind, source_url, bytes, metadata_json
        FROM assets
        WHERE doc_id = ? AND coalesce(source_url, '') != ''
        ORDER BY
          CASE kind
            WHEN 'thumbnail' THEN 0
            WHEN 'document' THEN 1
            WHEN 'video' THEN 2
            WHEN 'caption' THEN 3
            ELSE 4
          END,
          source_url
        """,
        (doc_id,),
    ).fetchall()
    assets = []
    seen = set()
    for row in rows:
        url = video_src_from_metadata(row["source_url"], row["metadata_json"]) if row["kind"] == "video" else clean(row["source_url"])
        key = (row["kind"], url)
        if key in seen:
            continue
        seen.add(key)
        assets.append(
            {
                "kind": row["kind"],
                "source_url": url,
                "media_type": media_type(row["kind"], url),
                "bytes": row["bytes"] or 0,
            }
        )
    return assets


def public_media(assets: List[Dict]) -> Dict:
    def first(kind: str) -> str:
        for asset in assets:
            if asset["kind"] == kind:
                return asset["source_url"]
        return ""

    return {
        "thumbnail_url": first("thumbnail"),
        "document_url": first("document"),
        "video_url": first("video"),
    }


def public_locations(conn, doc_id: str) -> List[Dict]:
    rows = conn.execute(
        """
        SELECT location_id, chunk_id, raw_location, normalized_location, latitude, longitude,
               precision, confidence, source_kind, method
        FROM locations
        WHERE doc_id = ?
        ORDER BY confidence DESC, precision, raw_location
        """,
        (doc_id,),
    ).fetchall()
    return [
        {
            "location_id": row["location_id"],
            "chunk_id": row["chunk_id"],
            "raw_location": row["raw_location"],
            "normalized_location": row["normalized_location"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "precision": row["precision"],
            "confidence": row["confidence"],
            "source_kind": row["source_kind"],
            "method": row["method"],
        }
        for row in rows
    ]


def summary_text_items(summary: Dict, key: str) -> Iterable[str]:
    for item in summary.get(key) or []:
        if isinstance(item, dict):
            yield clean(item.get("text") or item.get("label") or "")
        else:
            yield clean(item)


def add_tag(tags: List[str], label: str, limit: int = 10) -> None:
    label = clean(label)
    if not label or len(tags) >= limit:
        return
    if label.lower() in {tag.lower() for tag in tags}:
        return
    tags.append(label)


def tag_year(value: str) -> str:
    match = re.search(r"\b(18|19|20)\d{2}\b", clean(value))
    return match.group(0) if match else ""


def location_tag(location: str) -> str:
    location = clean(location)
    if not location or location == "N/A":
        return ""
    parts = [part.strip() for part in re.split(r"[,;/]", location) if part.strip()]
    candidate = parts[-1] if parts else location
    if len(candidate) < 3 or candidate.lower() in TAG_STOPWORDS:
        return ""
    return candidate[:40]


def tags_for(doc, summary: Dict, assets: List[Dict], locations: List[Dict]) -> List[str]:
    tags = []
    agency = clean(doc["agency"])
    add_tag(tags, AGENCY_TAGS.get(agency, agency if agency != "N/A" else ""))
    add_tag(tags, tag_year(doc["incident_date"] or doc["release_date"] or clean(doc["title"])))
    add_tag(tags, location_tag(doc["incident_location"]))
    if not location_tag(doc["incident_location"]):
        for location in locations[:2]:
            add_tag(tags, location_tag(location.get("normalized_location") or location.get("raw_location")))
    if any(asset.get("media_type") == "image" and asset.get("kind") != "thumbnail" for asset in assets):
        add_tag(tags, "Photos")
    if any(asset.get("media_type") == "video" for asset in assets):
        add_tag(tags, "Videos")

    text = " ".join(
        [
            clean(doc["title"]),
            clean(doc["incident_location"]),
            clean(doc["description"]),
            clean(summary.get("quick_summary")),
            " ".join(summary_text_items(summary, "mysterious_uap_element")),
            " ".join(summary_text_items(summary, "detailed_contents")),
        ]
    )
    for pattern, label in TAG_PHRASES:
        if pattern.search(text):
            add_tag(tags, label)

    weighted: Dict[str, int] = {}
    for term in re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", text):
        key = term.lower().strip("-")
        if key in TAG_STOPWORDS or len(key) < 4 or any(char.isdigit() for char in key):
            continue
        if key.startswith(("hs", "hq", "serial", "section", "chunk")):
            continue
        if key not in TAG_ALIASES:
            continue
        label = TAG_ALIASES[key]
        if label.lower() in {tag.lower() for tag in tags}:
            continue
        weight = 3 if key in TAG_ALIASES else 1
        weighted[label] = weighted.get(label, 0) + weight
    for label, _ in sorted(weighted.items(), key=lambda item: (-item[1], item[0]))[:20]:
        if weighted[label] < 2 and label.lower() not in {value.lower() for value in TAG_ALIASES.values()}:
            continue
        add_tag(tags, label)
        if len(tags) >= 10:
            break
    return tags


def add_reference_urls(summary: Dict, document_url: str) -> Dict:
    for key in ("mysterious_uap_element", "detailed_contents", "key_points"):
        for item in summary.get(key) or []:
            if isinstance(item, dict) and document_url and item.get("page_number"):
                item["source_url"] = f"{document_url}#page={item['page_number']}"
    for ref in summary.get("references") or []:
        if document_url and ref.get("page_number"):
            ref["source_url"] = f"{document_url}#page={ref['page_number']}"
    return summary


def related_tags(doc: Dict) -> set[str]:
    excluded = {
        clean(doc.get("agency")).lower(),
        "photos",
        "videos",
        "metadata",
        "war department",
        "state department",
    }
    return {
        tag.lower()
        for tag in doc.get("tags", [])
        if tag.lower() not in excluded and not re.fullmatch(r"(18|19|20)\d{2}", tag) and len(tag) > 2
    }


def attach_related_documents(documents: List[Dict]) -> None:
    tag_sets = {doc["doc_id"]: related_tags(doc) for doc in documents}
    by_id = {doc["doc_id"]: doc for doc in documents}
    for doc in documents:
        candidates = []
        tags = tag_sets[doc["doc_id"]]
        if not tags:
            doc["related_documents"] = []
            continue
        for other_id, other_tags in tag_sets.items():
            if other_id == doc["doc_id"]:
                continue
            overlap = sorted(tags & other_tags)
            if not overlap:
                continue
            candidates.append((len(overlap), overlap, by_id[other_id]))
        related = []
        for _, overlap, other in sorted(candidates, key=lambda item: (-item[0], item[2]["title"]))[:5]:
            related.append(
                {
                    "doc_id": other["doc_id"],
                    "title": other["title"],
                    "reason": "Shared tags: " + ", ".join(overlap[:3]),
                }
            )
        doc["related_documents"] = related


def featured_documents(documents: List[Dict]) -> List[Dict]:
    featured = []
    used = set()
    for selection in FEATURED_SELECTIONS:
        match = selection["match"].lower()
        doc = next((item for item in documents if match in item["title"].lower()), None)
        if not doc or doc["doc_id"] in used:
            continue
        used.add(doc["doc_id"])
        featured.append(
            {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "kicker": selection["kicker"],
                "summary": selection["summary"],
                "facts": selection["facts"],
                "agency": doc["agency"],
                "incident_date": doc["incident_date"],
                "incident_location": doc["incident_location"],
                "source_url": doc["source_url"],
                "media": doc["media"],
                "tags": doc["tags"][:6],
            }
        )
    return featured


def export_documents(conn) -> List[Dict]:
    rows = conn.execute(
        """
        SELECT doc_id, row_number, title, release_type, agency, release_date,
               incident_date, incident_location, description, source_url
        FROM documents
        ORDER BY row_number, title
        """
    ).fetchall()
    documents = []
    for row in rows:
        assets = public_assets(conn, row["doc_id"])
        media = public_media(assets)
        locations = public_locations(conn, row["doc_id"])
        summary = add_reference_urls(source_summary(conn, row["doc_id"]), media["document_url"] or clean(row["source_url"]))
        documents.append(
            {
                "doc_id": row["doc_id"],
                "row_number": row["row_number"],
                "title": clean(row["title"]),
                "release_type": clean(row["release_type"]),
                "agency": clean(row["agency"]),
                "release_date": clean(row["release_date"]),
                "incident_date": clean(row["incident_date"]),
                "incident_location": clean(row["incident_location"]),
                "description": clean(row["description"]),
                "source_url": clean(row["source_url"]),
                "media": media,
                "assets": assets,
                "locations": locations,
                "tags": tags_for(row, summary, assets, locations),
                "summary": summary,
            }
        )
    attach_related_documents(documents)
    return documents


def validate_public_payload(payload: Dict) -> List[str]:
    text = json.dumps(payload, ensure_ascii=False)
    forbidden = ["DisclosureArchivePackage", "derived/", "derived\\", "indexes/uap_release.sqlite", "indexes\\uap_release.sqlite", "Z:\\", "C:\\Users"]
    return [item for item in forbidden if item in text]


def analytics_snippet(domain: str = "", script_url: str = "https://plausible.io/js/script.js") -> str:
    domain = clean(domain)
    script_url = clean(script_url)
    if not domain:
        return ""
    if not re.fullmatch(r"[A-Za-z0-9.-]+", domain):
        raise ValueError("analytics domain must contain only letters, numbers, dots, and hyphens")
    if not script_url.startswith("https://"):
        raise ValueError("analytics script URL must be HTTPS")
    return (
        f'<script defer data-domain="{domain}" src="{script_url}"></script>\n'
        "  <script>window.plausible = window.plausible || function(){"
        '(window.plausible.q = window.plausible.q || []).push(arguments)};</script>'
    )


def normalize_site_url(site_url: str) -> str:
    site_url = clean(site_url) or "https://disclosurearchive.org"
    if not re.match(r"^https://[A-Za-z0-9.-]+(?::\d+)?(?:/.*)?$", site_url):
        raise ValueError("site URL must be an HTTPS URL")
    return site_url.rstrip("/")


def origin_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return ""


def seo_meta(site_url: str) -> str:
    canonical = f"{site_url}/"
    description = (
        "Explore curated highlights and a searchable public index of the PURSUE "
        "UFO/UAP release, with government source links, summaries, videos, photos, "
        "and provenance-preserving references."
    )
    image = "https://www.war.gov/medialink/ufo/release_1/nasa-uap-vm6-apollo-17-1972.jpg"
    title = "Disclosure Archive"
    return "\n  ".join(
        [
            f'<meta name="description" content="{html_escape(description, quote=True)}">',
            '<meta name="robots" content="index,follow,max-image-preview:large">',
            '<meta name="googlebot" content="index,follow,max-image-preview:large">',
            '<meta name="theme-color" content="#050806">',
            f'<link rel="canonical" href="{html_escape(canonical, quote=True)}">',
            '<link rel="sitemap" type="application/xml" href="/sitemap.xml">',
            '<meta property="og:type" content="website">',
            f'<meta property="og:url" content="{html_escape(canonical, quote=True)}">',
            f'<meta property="og:title" content="{html_escape(title, quote=True)}">',
            f'<meta property="og:description" content="{html_escape(description, quote=True)}">',
            f'<meta property="og:image" content="{html_escape(image, quote=True)}">',
            '<meta property="og:site_name" content="Disclosure Archive">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{html_escape(title, quote=True)}">',
            f'<meta name="twitter:description" content="{html_escape(description, quote=True)}">',
            f'<meta name="twitter:image" content="{html_escape(image, quote=True)}">',
        ]
    )


def csp_policy(analytics_script_url: str = "https://plausible.io/js/script.js") -> str:
    analytics_origin = origin_from_url(analytics_script_url)
    script_sources = ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"]
    connect_sources = ["'self'", "https://cdn.jsdelivr.net"]
    if analytics_origin:
        script_sources.append(analytics_origin)
        connect_sources.append(analytics_origin)
    return "; ".join(
        [
            "default-src 'self'",
            f"script-src {' '.join(dict.fromkeys(script_sources))}",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "media-src 'self' https:",
            f"connect-src {' '.join(dict.fromkeys(connect_sources))}",
            "font-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
    )


def security_meta(analytics_script_url: str = "https://plausible.io/js/script.js") -> str:
    policy = csp_policy(analytics_script_url)
    return "\n  ".join(
        [
            '<meta name="referrer" content="strict-origin-when-cross-origin">',
            f'<meta http-equiv="Content-Security-Policy" content="{html_escape(policy, quote=True)}">',
        ]
    )


def structured_data(site_url: str, document_count: int) -> str:
    canonical = f"{site_url}/"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{canonical}#website",
                "name": "Disclosure Archive",
                "url": canonical,
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": f"{canonical}#search?q={{search_term_string}}",
                    "query-input": "required name=search_term_string",
                },
            },
            {
                "@type": "Dataset",
                "@id": f"{canonical}#dataset",
                "name": "Disclosure Archive public UFO/UAP release index",
                "description": "Curated summaries and searchable metadata for the public PURSUE UFO/UAP release.",
                "url": canonical,
                "isAccessibleForFree": True,
                "license": "https://www.usa.gov/government-works",
                "keywords": ["UFO", "UAP", "PURSUE", "government records", "public archive"],
                "distribution": {
                    "@type": "DataDownload",
                    "encodingFormat": "application/json",
                    "contentUrl": f"{canonical}data/documents.json",
                },
                "measurementTechnique": "SQLite FTS, OCR, public source metadata, deterministic extractive summaries",
                "variableMeasured": f"{document_count} public records",
            },
        ],
    }
    text = json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
    return f'<script type="application/ld+json">{text}</script>'


def write_crawler_and_security_files(out: Path, site_url: str, generated_at: str, analytics_script_url: str) -> None:
    canonical = f"{site_url}/"
    (out / "robots.txt").write_text(
        "\n".join(
            [
                "User-agent: *",
                "Allow: /",
                "",
                f"Sitemap: {canonical}sitemap.xml",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (out / "sitemap.xml").write_text(
        "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
                "  <url>",
                f"    <loc>{html_escape(canonical)}</loc>",
                f"    <lastmod>{html_escape(generated_at[:10])}</lastmod>",
                "    <changefreq>weekly</changefreq>",
                "    <priority>1.0</priority>",
                "  </url>",
                "</urlset>",
                "",
            ]
        ),
        encoding="utf-8",
    )
    expires = (datetime.now(timezone.utc) + timedelta(days=365)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    security_txt = "\n".join(
        [
            f"Contact: {site_url}/",
            "Contact: https://github.com/GeorgiKostov/DisclosureArchive/issues",
            f"Expires: {expires}",
            "Preferred-Languages: en",
            f"Canonical: {site_url}/.well-known/security.txt",
            "Policy: https://github.com/GeorgiKostov/DisclosureArchive/security/policy",
            "",
        ]
    )
    well_known = out / ".well-known"
    well_known.mkdir(parents=True, exist_ok=True)
    (well_known / "security.txt").write_text(security_txt, encoding="utf-8")
    (out / "security.txt").write_text(security_txt, encoding="utf-8")
    policy = csp_policy(analytics_script_url)
    (out / "_headers").write_text(
        "\n".join(
            [
                "/*",
                f"  Content-Security-Policy: {policy}",
                "  Referrer-Policy: strict-origin-when-cross-origin",
                "  X-Content-Type-Options: nosniff",
                "  X-Frame-Options: DENY",
                "  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_site(
    db: Path,
    out: Path,
    analytics_domain: str = "",
    analytics_script_url: str = "https://plausible.io/js/script.js",
    site_url: str = "https://disclosurearchive.org",
) -> Dict:
    site_url = normalize_site_url(site_url)
    conn = connect(db)
    documents = export_documents(conn)
    featured = featured_documents(documents)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = {
        "schema": "disclosurearchive.public_site.v1",
        "generated_at": generated_at,
        "document_count": len(documents),
        "featured_documents": featured,
        "documents": documents,
    }
    leaks = validate_public_payload(payload)
    if leaks:
        raise RuntimeError(f"public export contains forbidden local/private strings: {', '.join(leaks)}")

    data_dir = out / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "documents.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    html = (
        PUBLIC_SITE_HTML.replace("<!-- SEO_META -->", seo_meta(site_url))
        .replace("<!-- SECURITY_META -->", security_meta(analytics_script_url))
        .replace("<!-- STRUCTURED_DATA -->", structured_data(site_url, len(documents)))
        .replace("<!-- ANALYTICS_SNIPPET -->", analytics_snippet(analytics_domain, analytics_script_url))
    )
    (out / "index.html").write_text(html, encoding="utf-8")
    write_crawler_and_security_files(out, site_url, generated_at, analytics_script_url)
    return {
        "out": str(out),
        "documents": len(documents),
        "analytics": "enabled" if analytics_domain else "disabled",
        "site_url": site_url,
        "json": str(data_dir / "documents.json"),
        "html": str(out / "index.html"),
        "robots": str(out / "robots.txt"),
        "sitemap": str(out / "sitemap.xml"),
        "security": str(out / ".well-known" / "security.txt"),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Export a static public summary/search site.")
    parser.add_argument("--db", type=Path, default=Path("indexes/uap_release.sqlite"))
    parser.add_argument("--out", type=Path, default=Path("public_site"))
    parser.add_argument("--analytics-domain", default=os.environ.get("DISCLOSURE_ANALYTICS_DOMAIN", ""), help="Optional Plausible-compatible analytics domain, e.g. example.com")
    parser.add_argument("--analytics-script-url", default=os.environ.get("DISCLOSURE_ANALYTICS_SCRIPT_URL", "https://plausible.io/js/script.js"), help="Optional HTTPS Plausible-compatible script URL")
    parser.add_argument("--site-url", default=os.environ.get("DISCLOSURE_SITE_URL", "https://disclosurearchive.org"), help="Canonical public HTTPS URL for SEO files")
    args = parser.parse_args(argv)

    result = write_site(args.db, args.out, analytics_domain=args.analytics_domain, analytics_script_url=args.analytics_script_url, site_url=args.site_url)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
