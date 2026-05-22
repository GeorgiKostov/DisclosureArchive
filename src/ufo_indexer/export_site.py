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
from urllib.parse import quote, urlparse

from .common import clean
from .db import connect
from .summary import STOPWORDS, source_summary


PUBLIC_SITE_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Disclosure Archive | Public UFO/UAP Release Index</title>
  <meta name="disclosure-map-palette" content="archive-green nuclear-orange military-red">
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
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 10px;
      flex-wrap: wrap;
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
    .support-link {
      display: inline-flex;
      align-items: center;
      min-height: 36px;
      padding: 0 11px;
      border-color: rgba(114,215,255,0.58);
      background: linear-gradient(180deg, rgba(114,215,255,0.20), rgba(36,94,128,0.18));
      color: var(--accent-2);
      text-transform: uppercase;
      font-size: 12px;
      box-shadow: 0 0 0 1px rgba(114,215,255,0.06), 0 0 18px rgba(114,215,255,0.12);
    }
    .support-link:hover {
      border-color: rgba(114,215,255,0.85);
      color: #d8f5ff;
      box-shadow: 0 0 0 1px rgba(114,215,255,0.14), 0 0 22px rgba(114,215,255,0.22);
    }
    .support-link svg {
      display: block;
      width: 16px;
      height: 16px;
      stroke: currentColor;
      stroke-width: 2.2;
      flex: 0 0 auto;
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
    .site-footer {
      border-top: 1px solid var(--line);
      background: rgba(2, 10, 6, 0.88);
      box-shadow: 0 -16px 38px rgba(0,0,0,0.2);
    }
    .footer-inner {
      padding: 24px 0 28px;
    }
    .footer-links {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      color: var(--muted);
      font-size: 12px;
      align-items: center;
    }
    .footer-links a {
      color: var(--accent-2);
    }
    .footer-updated {
      color: var(--muted);
      opacity: 0.82;
    }
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
    .release-group {
      border: 1px solid rgba(66,255,140,0.18);
      border-radius: 8px;
      background: rgba(2, 10, 6, 0.34);
      overflow: hidden;
    }
    .release-group + .release-group {
      margin-top: 12px;
    }
    .release-toggle {
      position: relative;
      width: 100%;
      min-height: 46px;
      padding: 0 12px;
      justify-content: space-between;
      border: 0;
      border-bottom: 1px solid rgba(66,255,140,0.16);
      border-radius: 0;
      background: rgba(7, 24, 15, 0.78);
      box-shadow: none;
      text-align: left;
    }
    .release-name {
      color: var(--accent);
      font-size: 13px;
      font-weight: 800;
      text-transform: uppercase;
    }
    .release-date {
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
    }
    .release-toggle::after {
      content: "-";
      color: var(--accent-2);
      font-size: 16px;
      line-height: 1;
    }
    .release-group.collapsed .release-toggle::after {
      content: "+";
    }
    .release-group.collapsed .release-body {
      display: none;
    }
    .release-body {
      padding: 12px;
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
    .best-media a,
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
      font-size: 14px;
      line-height: 1.25;
    }
    .best-title-link {
      min-height: 0;
      padding: 0;
      border: 0;
      border-radius: 0;
      background: transparent;
      color: var(--accent);
      font: inherit;
      line-height: inherit;
      text-align: left;
      box-shadow: none;
      justify-content: flex-start;
      overflow-wrap: anywhere;
    }
    .best-title-link:hover {
      color: var(--accent-2);
      text-decoration: underline;
      border-color: transparent;
      box-shadow: none;
    }
    .best-title-link:focus-visible {
      outline: 1px solid var(--accent-2);
      outline-offset: 3px;
    }
    .best-summary {
      color: var(--ink);
      font-size: 12px;
      line-height: 1.5;
      margin-bottom: 0;
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
      min-height: 30px;
      padding: 0 8px;
      font-size: 11px;
      color: var(--accent-2);
    }
    .best-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      margin-top: 9px;
    }
    .search-section {
      margin-top: 18px;
      padding-top: 18px;
      border-top: 1px solid var(--line);
    }
    .map-section {
      margin-top: 18px;
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
    .map-zoom-controls {
      position: absolute;
      left: 14px;
      top: 14px;
      display: grid;
      gap: 6px;
      z-index: 2;
    }
    .map-zoom-controls button {
      width: 34px;
      height: 34px;
      min-width: 34px;
      min-height: 34px;
      max-width: 34px;
      max-height: 34px;
      padding: 0;
      aspect-ratio: 1;
      border-radius: 50%;
      border: 1px solid rgba(66,255,140,0.38);
      background: rgba(2, 10, 6, 0.88);
      color: var(--accent-2);
      font-size: 20px;
      line-height: 1;
      box-shadow: 0 10px 28px rgba(0,0,0,0.32);
    }
    .map-zoom-controls button:hover {
      border-color: var(--accent);
      color: var(--accent);
    }
    .map-section .globe-panel {
      display: grid;
      margin-top: 0;
    }
    .map-section .globe-stage {
      height: clamp(430px, 64vh, 720px);
    }
    .map-legend {
      position: absolute;
      right: 14px;
      bottom: 14px;
      width: min(282px, calc(100% - 28px));
      border: 1px solid rgba(66,255,140,0.42);
      border-radius: 8px;
      background: rgba(2, 10, 6, 0.92);
      box-shadow: 0 18px 42px rgba(0,0,0,0.42), 0 0 26px rgba(66,255,140,0.1);
      padding: 8px;
      z-index: 2;
    }
    .legend-button {
      width: 100%;
      min-height: 34px;
      justify-content: space-between;
      padding: 0 9px;
      color: var(--accent-2);
      text-transform: uppercase;
      font-size: 11px;
    }
    .legend-button::after {
      content: "-";
      color: var(--accent);
    }
    .map-legend.collapsed {
      width: auto;
      min-width: 92px;
      padding: 6px;
    }
    .map-legend.collapsed .legend-body {
      display: none;
    }
    .map-legend.collapsed .legend-button::after {
      content: "+";
    }
    .legend-body {
      padding: 8px 4px 2px;
    }
    .legend-body p {
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 11px;
    }
    .legend-toggle {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 30px;
      color: var(--ink);
      font-size: 12px;
    }
    .legend-toggle input {
      accent-color: var(--accent);
    }
    .legend-key {
      width: 16px;
      height: 16px;
      border-radius: 4px;
      flex: 0 0 auto;
      display: inline-grid;
      place-items: center;
      color: #06110b;
      font-size: 11px;
      font-weight: 900;
      line-height: 1;
    }
    .legend-key.military { background: #ff6b6b; }
    .legend-key.military::before { content: "★"; }
    .legend-key.nuclear {
      background: #ff9f1c;
      border-radius: 50%;
    }
    .legend-key.nuclear::before { content: "☢"; font-size: 10px; }
    .map-selection {
      margin-top: 12px;
    }
    .map-empty {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(5, 14, 10, 0.78);
      padding: 16px;
      color: var(--muted);
    }
    .reference-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 15px;
      margin-bottom: 12px;
    }
    .reference-card h2 {
      margin-bottom: 6px;
    }
    .reference-card p {
      color: var(--ink);
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
    .media a,
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
    .summary-button,
    .map-button {
      gap: 7px;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0;
    }
    .source-button span,
    .summary-button span,
    .map-button span {
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
      .top-actions { justify-content: flex-start; width: 100%; }
      .nav { justify-content: flex-start; width: 100%; }
      .support-link { order: -1; }
      .brand-title { font-size: 20px; text-align: left; }
      .search { grid-template-columns: 1fr; }
      input[type="search"], button, .button, select { min-height: 44px; }
      .tools { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
      .tools select, .tools button { width: 100%; min-width: 0; }
      .best-of { padding: 12px; }
      .best-head { align-items: flex-start; flex-direction: column; }
      .release-toggle { align-items: flex-start; flex-direction: column; gap: 3px; padding: 9px 12px; }
      .release-toggle::after { position: absolute; right: 12px; top: 14px; }
      .release-body { padding: 10px; }
      .best-grid { grid-template-columns: 1fr; }
      .best-media { height: min(230px, 54vw); }
      .shell { grid-template-columns: 1fr; }
      .body { padding: 12px; }
      .media { order: -1; width: 100%; height: 160px; border-left: 0; border-bottom: 1px solid var(--line); position: static; }
      .result.media-rich .shell { grid-template-columns: 1fr; }
      .result.media-rich .media { height: min(340px, 66vw); }
      .actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .actions > * { width: 100%; min-width: 0; }
      .footer-inner { padding: 20px 0 24px; }
      .globe-stage { height: clamp(300px, 82vw, 460px); min-height: 300px; }
      .map-section .globe-stage { height: clamp(360px, 92vw, 560px); }
      #globeCanvas { min-height: 300px; }
      .map-zoom-controls button { width: 34px; height: 34px; min-width: 34px; min-height: 34px; }
      .map-legend { right: 10px; bottom: 10px; width: min(250px, calc(100% - 20px)); }
      .map-legend.collapsed { width: auto; }
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
        <a class="button support-link" href="https://ko-fi.com/P5P51ZLPBN" target="_blank" rel="noopener" aria-label="Support Disclosure Archive on Ko-fi">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M10 2v2"></path>
            <path d="M14 2v2"></path>
            <path d="M7 2v2"></path>
            <path d="M6 8h11a3 3 0 0 1 0 6h-1"></path>
            <path d="M6 8h10v6a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5V10a2 2 0 0 1 2-2Z"></path>
            <path d="M5 22h13"></path>
          </svg>
          <span>Support</span>
        </a>
        <nav class="nav" aria-label="Primary">
          <button type="button" class="nav-link active" data-view-target="home">Highlights</button>
          <button type="button" class="nav-link" data-view-target="search">Records</button>
          <button type="button" class="nav-link" data-view-target="map">Map</button>
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
        <h2>Documents</h2>
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
        <select id="yearFilter" aria-label="Decade filter">
          <option value="">All decades</option>
        </select>
        <button type="button" id="reset">Reset</button>
      </div>
      <div class="status" id="status">Loading...</div>
      <section id="results"></section>
      <div class="load-more" id="loadMoreWrap" hidden>
        <button type="button" id="loadMore">Load more</button>
        <div class="result-sentinel" id="resultSentinel" aria-hidden="true"></div>
      </div>
    </section>
    <section class="view map-section" id="mapView" hidden>
      <div class="section-head">
        <h2>Map</h2>
      </div>
      <section id="globePanel" class="globe-panel open" aria-hidden="false">
        <div class="globe-stage">
          <canvas id="globeCanvas" aria-label="Interactive globe with document locations"></canvas>
          <div class="map-zoom-controls" aria-label="Map zoom controls">
            <button type="button" id="mapZoomIn" aria-label="Zoom in" title="Zoom in">+</button>
            <button type="button" id="mapZoomOut" aria-label="Zoom out" title="Zoom out">-</button>
          </div>
          <div class="map-legend collapsed" id="mapLegend" aria-label="Map overlays">
            <button type="button" class="legend-button" id="legendToggle" aria-expanded="false">Points of interest</button>
            <div class="legend-body" id="legendBody">
              <p>Public reference points within 500 km of plotted archive locations.</p>
              <label class="legend-toggle">
                <input type="checkbox" data-overlay-toggle="military">
                <span class="legend-key military" aria-hidden="true"></span>
                <span>Military bases</span>
              </label>
              <label class="legend-toggle">
                <input type="checkbox" data-overlay-toggle="nuclear">
                <span class="legend-key nuclear" aria-hidden="true"></span>
                <span>Nuclear sites</span>
              </label>
            </div>
          </div>
        </div>
      </section>
      <section id="mapSelection" class="map-selection">
        <div class="map-empty">Select an archive location on the globe to open its document below.</div>
      </section>
    </section>
  </main>
  <!-- SITE_FOOTER -->
  <script>
    const $ = (id) => document.getElementById(id);
    const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[char]));
    const icon = (name) => {
      if (name === "source") return '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M3.6 9h16.8"/><path d="M3.6 15h16.8"/><path d="M12 3a14 14 0 0 1 0 18"/><path d="M12 3a14 14 0 0 0 0 18"/><path d="M15 9h5v5"/><path d="m20 9-6 6"/></svg>';
      if (name === "map") return '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s7-4.4 7-11a7 7 0 1 0-14 0c0 6.6 7 11 7 11z"/><circle cx="12" cy="10" r="2.3"/></svg>';
      return '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z"/><path d="M14 2v5h5"/><path d="M8 11h8"/><path d="M8 15h8"/><path d="M8 19h5"/></svg>';
    };
    const track = (name, props = {}) => {
      if (typeof window.plausible === "function") {
        window.plausible(name, { props });
      }
      if (typeof window.gtag === "function") {
        window.gtag("event", name, props);
      }
    };
    let archive = null;
    let docs = [];
    let currentView = "home";
    const SEARCH_BATCH_SIZE = 20;
    const resultState = { matches: [], visible: 0 };
    let resultObserver = null;
    const globeState = { ready: false, initializing: false, locations: [], markers: [], selected: null, selectedIndex: null };
    const overlayState = {
      visible: { military: false, nuclear: false },
      markers: [],
      facilities: [
        { kind: "military", name: "Edwards Air Force Base", type: "flight test base", latitude: 34.9054, longitude: -117.8837 },
        { kind: "military", name: "Nellis Air Force Base", type: "training and test range", latitude: 36.2362, longitude: -115.0342 },
        { kind: "military", name: "Creech Air Force Base", type: "remotely piloted aircraft base", latitude: 36.5872, longitude: -115.6736 },
        { kind: "military", name: "Vandenberg Space Force Base", type: "space launch and missile test base", latitude: 34.7420, longitude: -120.5724 },
        { kind: "military", name: "Wright-Patterson Air Force Base", type: "Air Force research and logistics base", latitude: 39.8261, longitude: -84.0483 },
        { kind: "military", name: "Eglin Air Force Base", type: "test and training base", latitude: 30.4832, longitude: -86.5254 },
        { kind: "military", name: "White Sands Missile Range", type: "missile test range", latitude: 32.3801, longitude: -106.4797 },
        { kind: "military", name: "Fort Irwin / National Training Center", type: "training base", latitude: 35.2627, longitude: -116.6848 },
        { kind: "military", name: "Joint Base Pearl Harbor-Hickam", type: "joint base", latitude: 21.3399, longitude: -157.9602 },
        { kind: "military", name: "Ramstein Air Base", type: "U.S. air base", latitude: 49.4369, longitude: 7.6003 },
        { kind: "military", name: "RAF Lakenheath", type: "U.S. air base", latitude: 52.4093, longitude: 0.5609 },
        { kind: "military", name: "Diego Garcia", type: "joint support facility", latitude: -7.3133, longitude: 72.4111 },
        { kind: "military", name: "Al Udeid Air Base", type: "U.S./Qatar air base", latitude: 25.1173, longitude: 51.3149 },
        { kind: "military", name: "Al Dhafra Air Base", type: "UAE air base", latitude: 24.2482, longitude: 54.5477 },
        { kind: "military", name: "Naval Support Activity Bahrain", type: "U.S. naval support activity", latitude: 26.2070, longitude: 50.6130 },
        { kind: "military", name: "Ali Al Salem Air Base", type: "Kuwait air base", latitude: 29.3467, longitude: 47.5208 },
        { kind: "military", name: "Camp Arifjan", type: "U.S./Kuwait logistics base", latitude: 28.9047, longitude: 48.1842 },
        { kind: "military", name: "Al Asad Airbase", type: "Iraq air base", latitude: 33.7856, longitude: 42.4412 },
        { kind: "military", name: "Erbil Air Base", type: "Iraq air base", latitude: 36.2376, longitude: 43.9632 },
        { kind: "military", name: "Muwaffaq Salti Air Base", type: "Jordan air base", latitude: 31.8250, longitude: 36.7820 },
        { kind: "military", name: "Incirlik Air Base", type: "Turkey air base", latitude: 37.0021, longitude: 35.4259 },
        { kind: "military", name: "RAF Akrotiri", type: "UK sovereign base area", latitude: 34.5904, longitude: 32.9879 },
        { kind: "military", name: "Naval Support Activity Souda Bay", type: "NATO/U.S. naval support activity", latitude: 35.5317, longitude: 24.1497 },
        { kind: "military", name: "Naval Air Station Sigonella", type: "NATO/U.S. air station", latitude: 37.4017, longitude: 14.9224 },
        { kind: "military", name: "Aviano Air Base", type: "U.S./Italy air base", latitude: 46.0319, longitude: 12.5965 },
        { kind: "military", name: "Yokota Air Base", type: "U.S./Japan air base", latitude: 35.7485, longitude: 139.3485 },
        { kind: "military", name: "Kadena Air Base", type: "U.S./Japan air base", latitude: 26.3517, longitude: 127.7694 },
        { kind: "military", name: "Misawa Air Base", type: "U.S./Japan air base", latitude: 40.7032, longitude: 141.3683 },
        { kind: "military", name: "Commander Fleet Activities Yokosuka", type: "U.S./Japan naval base", latitude: 35.2920, longitude: 139.6720 },
        { kind: "military", name: "Commander Fleet Activities Sasebo", type: "U.S./Japan naval base", latitude: 33.1594, longitude: 129.7160 },
        { kind: "military", name: "Osan Air Base", type: "U.S./South Korea air base", latitude: 37.0906, longitude: 127.0300 },
        { kind: "military", name: "Kunsan Air Base", type: "U.S./South Korea air base", latitude: 35.9038, longitude: 126.6159 },
        { kind: "military", name: "Andersen Air Force Base", type: "U.S. air base", latitude: 13.5840, longitude: 144.9300 },
        { kind: "military", name: "Naval Base Guam", type: "U.S. naval base", latitude: 13.4430, longitude: 144.6500 },
        { kind: "military", name: "Rota Naval Base", type: "Spain/U.S. naval base", latitude: 36.6450, longitude: -6.3490 },
        { kind: "military", name: "Spangdahlem Air Base", type: "U.S./Germany air base", latitude: 49.9727, longitude: 6.6925 },
        { kind: "nuclear", name: "Malmstrom Air Force Base", type: "ICBM missile wing base", latitude: 47.5047, longitude: -111.1830 },
        { kind: "nuclear", name: "Minot Air Force Base", type: "ICBM missile wing base", latitude: 48.4156, longitude: -101.3583 },
        { kind: "nuclear", name: "F. E. Warren Air Force Base", type: "ICBM missile wing base", latitude: 41.1333, longitude: -104.8667 },
        { kind: "nuclear", name: "Palo Verde Generating Station", type: "nuclear power plant", latitude: 33.3881, longitude: -112.8617 },
        { kind: "nuclear", name: "Vogtle Electric Generating Plant", type: "nuclear power plant", latitude: 33.1431, longitude: -81.7658 },
        { kind: "nuclear", name: "Limerick Generating Station", type: "nuclear power plant", latitude: 40.2267, longitude: -75.5871 },
        { kind: "nuclear", name: "Diablo Canyon Power Plant", type: "nuclear power plant", latitude: 35.2108, longitude: -120.8560 },
        { kind: "nuclear", name: "Hanford Site", type: "nuclear reservation", latitude: 46.5507, longitude: -119.4880 },
        { kind: "nuclear", name: "Savannah River Site", type: "nuclear reservation", latitude: 33.2566, longitude: -81.7354 },
        { kind: "nuclear", name: "Los Alamos National Laboratory", type: "nuclear research site", latitude: 35.8756, longitude: -106.3247 },
        { kind: "nuclear", name: "Oak Ridge Reservation", type: "nuclear research site", latitude: 35.9300, longitude: -84.3100 },
        { kind: "nuclear", name: "Sellafield", type: "nuclear site", latitude: 54.4205, longitude: -3.4975 },
        { kind: "nuclear", name: "Barakah Nuclear Energy Plant", type: "nuclear power plant", latitude: 23.9680, longitude: 52.2350 },
        { kind: "nuclear", name: "Bushehr Nuclear Power Plant", type: "nuclear power plant", latitude: 28.8290, longitude: 50.8860 },
        { kind: "nuclear", name: "Natanz Nuclear Facility", type: "nuclear facility", latitude: 33.7240, longitude: 51.7270 },
        { kind: "nuclear", name: "Fordow Fuel Enrichment Plant", type: "nuclear facility", latitude: 34.8840, longitude: 50.9960 },
        { kind: "nuclear", name: "Negev Nuclear Research Center", type: "nuclear research site", latitude: 31.0000, longitude: 35.1400 },
        { kind: "nuclear", name: "Akkuyu Nuclear Power Plant", type: "nuclear power plant", latitude: 36.1440, longitude: 33.5410 },
        { kind: "nuclear", name: "Kashiwazaki-Kariwa Nuclear Power Plant", type: "nuclear power plant", latitude: 37.4280, longitude: 138.6010 },
        { kind: "nuclear", name: "Fukushima Daiichi Nuclear Power Plant", type: "nuclear power plant", latitude: 37.4210, longitude: 141.0320 },
        { kind: "nuclear", name: "Rokkasho Reprocessing Plant", type: "nuclear fuel cycle facility", latitude: 40.9610, longitude: 141.3260 },
        { kind: "nuclear", name: "Ohi Nuclear Power Plant", type: "nuclear power plant", latitude: 35.5410, longitude: 135.6530 },
        { kind: "nuclear", name: "Takahama Nuclear Power Plant", type: "nuclear power plant", latitude: 35.5220, longitude: 135.5040 },
        { kind: "nuclear", name: "Genkai Nuclear Power Plant", type: "nuclear power plant", latitude: 33.5150, longitude: 129.8370 },
        { kind: "nuclear", name: "Sendai Nuclear Power Plant", type: "nuclear power plant", latitude: 31.8330, longitude: 130.1890 },
        { kind: "nuclear", name: "Ikata Nuclear Power Plant", type: "nuclear power plant", latitude: 33.4910, longitude: 132.3110 },
        { kind: "nuclear", name: "Kori Nuclear Power Plant", type: "nuclear power plant", latitude: 35.3180, longitude: 129.2960 },
        { kind: "nuclear", name: "Wolsong Nuclear Power Plant", type: "nuclear power plant", latitude: 35.7110, longitude: 129.4750 },
        { kind: "nuclear", name: "Hanul Nuclear Power Plant", type: "nuclear power plant", latitude: 37.0920, longitude: 129.3830 },
        { kind: "nuclear", name: "Metsamor Nuclear Power Plant", type: "nuclear power plant", latitude: 40.1800, longitude: 44.1500 },
        { kind: "nuclear", name: "Kozloduy Nuclear Power Plant", type: "nuclear power plant", latitude: 43.7470, longitude: 23.7710 },
        { kind: "nuclear", name: "Chashma Nuclear Power Plant", type: "nuclear power plant", latitude: 32.3900, longitude: 71.4700 },
        { kind: "nuclear", name: "Karachi Nuclear Power Plant", type: "nuclear power plant", latitude: 24.8500, longitude: 66.7900 },
        { kind: "nuclear", name: "Tarapur Atomic Power Station", type: "nuclear power plant", latitude: 19.8300, longitude: 72.6600 },
      ],
    };

    function searchable(doc) {
      return [
        doc.title, doc.agency, doc.incident_date, doc.incident_location,
        doc.description,
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

    function docDecade(doc) {
      const year = docYear(doc);
      return year ? Math.floor(year / 10) * 10 : 0;
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

    function distanceKm(a, b) {
      const toRad = (value) => value * Math.PI / 180;
      const lat1 = toRad(Number(a.latitude));
      const lat2 = toRad(Number(b.latitude));
      const dLat = lat2 - lat1;
      const dLon = toRad(Number(b.longitude) - Number(a.longitude));
      const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
      return 6371 * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
    }

    function nearbyOverlayFacilities(maxKm = 500) {
      if (!globeState.locations.length) return [];
      return overlayState.facilities
        .map((facility) => {
          const nearest = globeState.locations.reduce((best, location) => {
            const distance = distanceKm(facility, location);
            return distance < best.distance ? { location, distance } : best;
          }, { location: null, distance: Infinity });
          return {
            ...facility,
            nearestArchiveLocation: nearest.location,
            nearestDistanceKm: Math.round(nearest.distance),
          };
        })
        .filter((facility) => facility.nearestDistanceKm <= maxKm);
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
        const target = doc.source_url || media.document_url || imagePreview;
        return `<a href="${esc(target)}" target="_blank" rel="noopener" data-track="source" data-doc-id="${esc(doc.doc_id)}" title="Open government source"><img loading="lazy" src="${esc(imagePreview)}" alt="${esc(doc.title)} preview"></a>`;
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
        const target = item.source_url || media.document_url || imagePreview;
        return `<a href="${esc(target)}" target="_blank" rel="noopener" data-track="source" data-doc-id="${esc(item.doc_id)}" title="Open government source"><img loading="lazy" src="${esc(imagePreview)}" alt="${esc(item.title)} preview"></a>`;
      }
      return `<div class="muted">No preview</div>`;
    }

    function formatReleaseDate(value) {
      const text = String(value || "").trim();
      const match = text.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2}|\d{4})$/);
      if (!match) return text;
      const year = Number(match[3].length === 2 ? `20${match[3]}` : match[3]);
      const date = new Date(Date.UTC(year, Number(match[1]) - 1, Number(match[2])));
      if (Number.isNaN(date.getTime())) return text;
      return date.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric", timeZone: "UTC" });
    }

    function highlightReleaseGroups(items) {
      const config = archive?.release_groups?.length
        ? archive.release_groups
        : [{ key: "release-1", label: "RELEASE 1", date: "", fallback_date: "5/8/26" }];
      const byRelease = new Map();
      items.forEach((item) => {
        const key = item.release || "release-1";
        if (!byRelease.has(key)) byRelease.set(key, []);
        byRelease.get(key).push(item);
      });
      const groups = [];
      const seen = new Set();
      const pushGroup = (cfg, groupItems) => {
        if (!groupItems?.length) return;
        const derived = cfg.date || groupItems.find((item) => item.release_date)?.release_date || cfg.fallback_date || "";
        groups.push({
          key: cfg.key,
          label: cfg.label || String(cfg.key || "").toUpperCase(),
          date: derived ? formatReleaseDate(derived) : "",
          items: groupItems,
        });
      };
      config.forEach((cfg) => {
        seen.add(cfg.key);
        pushGroup(cfg, byRelease.get(cfg.key));
      });
      // Render any release keys not declared in the config so highlights are never dropped.
      byRelease.forEach((groupItems, key) => {
        if (seen.has(key)) return;
        pushGroup({ key, label: key.toUpperCase(), date: "", fallback_date: "" }, groupItems);
      });
      return groups;
    }

    function renderBestOf(items) {
      const panel = $("bestOf");
      if (!panel || !items?.length) return;
      const groups = highlightReleaseGroups(items);
      panel.innerHTML = `
        <div class="best-head">
          <div class="best-title-row">
            <h2>HIGHLIGHTS</h2>
            <div class="best-count">${items.length} discussed records, videos, and photos</div>
          </div>
        </div>
        ${groups.map((group) => `
          <section class="release-group" data-release-group="${esc(group.key)}">
            <button type="button" class="release-toggle" data-release-toggle="${esc(group.key)}" aria-expanded="true">
              <span class="release-name">${esc(group.label)}</span>
              <span class="release-date">${group.date ? `Published ${esc(group.date)}` : ""}</span>
            </button>
            <div class="release-body">
              <div class="best-grid">
                ${group.items.map((item) => `
                  <article class="best-card">
                    <div class="best-media">${renderBestMedia(item)}</div>
                    <div class="best-body">
                      <div class="best-label">${esc(item.kicker)}</div>
                      <h3 class="best-title"><button type="button" class="best-title-link" data-feature-doc="${esc(item.doc_id)}">${esc(item.title)}</button></h3>
                      <p class="best-summary">${esc(item.summary)}</p>
                      <ul class="best-facts">${(item.facts || []).map((fact) => `<li>${esc(fact)}</li>`).join("")}</ul>
                      <div class="best-actions">
                        <button type="button" class="button best-link" data-feature-doc="${esc(item.doc_id)}">View record</button>
                        ${hasMapLocation(item) ? `<button type="button" class="button best-link" data-feature-map="${esc(item.doc_id)}">Open map</button>` : ""}
                      </div>
                    </div>
                  </article>
                `).join("")}
                </div>
              </div>
          </section>
        `).join("")}
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
      if (hasMapLocation(doc)) links.push(`<button type="button" class="icon-button map-button" data-doc-map="${esc(doc.doc_id)}" aria-label="Open map location" title="Open map location">${icon("map")}<span>Map</span></button>`);
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

    function recordDescription(doc) {
      return doc.description || doc.summary?.quick_summary || doc.summary?.overview || "No description available.";
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
              <p class="record-description">${esc(recordDescription(doc))}</p>
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
      const decades = [...new Set(docs.map(docDecade).filter(Boolean))].sort((a, b) => b - a);
      $("yearFilter").innerHTML = `<option value="">All decades</option>` + decades.map((decade) => `<option value="${decade}">${decade}s</option>`).join("");
    }

    function locationLabel(location) {
      return location.normalized_location || location.raw_location || `${location.latitude.toFixed(2)}, ${location.longitude.toFixed(2)}`;
    }

    function hasMapLocation(doc) {
      return (doc?.locations || []).some((location) => Number.isFinite(Number(location.latitude)) && Number.isFinite(Number(location.longitude)));
    }

    function updateGlobeSelection() {
      globeState.markers.forEach((marker, index) => {
        const selected = index === globeState.selectedIndex;
        marker.material = selected ? marker.userData.selectedMaterial : marker.userData.defaultMaterial;
        marker.userData.selectionScale = selected ? 1.85 : 1;
      });
    }

    function renderSelectedLocation(location) {
      if (!location) {
        $("mapSelection").innerHTML = `<div class="map-empty">Select an archive location on the globe to open its document below.</div>`;
        return;
      }
      if (location.facilityKind) {
        const nearest = location.nearestArchiveLocation;
        $("mapSelection").innerHTML = `
          <article class="reference-card">
            <h2>${esc(location.name)}</h2>
            <div class="muted">${esc(location.facilityKind === "military" ? "Military base" : "Nuclear site")} | ${esc(location.type || "public reference point")}</div>
            <p>This is a public reference overlay point near ${esc(nearest ? locationLabel(nearest) : "an archive map point")}. It is not part of the document index.</p>
          </article>
        `;
        return;
      }
      const doc = docs.find((item) => item.doc_id === location.doc_id);
      $("mapSelection").innerHTML = doc
        ? renderDoc(doc).replace(`id="doc-${esc(doc.doc_id)}"`, `id="map-doc-${esc(doc.doc_id)}"`)
        : `<div class="map-empty">No matching document could be opened for this location.</div>`;
    }

    function updateOverlayMarkers() {
      overlayState.markers.forEach((marker) => {
        marker.visible = Boolean(overlayState.visible[marker.userData.facility.kind]);
      });
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

    function overlayIconSprite(THREE, kind) {
      const canvas = document.createElement("canvas");
      canvas.width = 96;
      canvas.height = 96;
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const color = kind === "military" ? "#ff6b6b" : "#ff9f1c";
      ctx.fillStyle = color;
      ctx.strokeStyle = "rgba(1, 10, 7, 0.92)";
      ctx.lineWidth = 6;
      if (kind === "military") {
        ctx.beginPath();
        for (let index = 0; index < 10; index += 1) {
          const radius = index % 2 === 0 ? 34 : 15;
          const angle = -Math.PI / 2 + index * Math.PI / 5;
          const x = 48 + Math.cos(angle) * radius;
          const y = 48 + Math.sin(angle) * radius;
          if (index === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.stroke();
        ctx.fill();
      } else {
        ctx.beginPath();
        ctx.arc(48, 48, 35, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fill();
        ctx.fillStyle = "rgba(1, 10, 7, 0.92)";
        ctx.font = "700 42px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("☢", 48, 51);
      }
      if (kind === "military") {
        ctx.fillStyle = "rgba(1, 10, 7, 0.92)";
        ctx.font = "700 28px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("★", 48, 51);
      }
      ctx.textAlign = "center";
      const texture = new THREE.CanvasTexture(canvas);
      texture.needsUpdate = true;
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        depthWrite: false,
      }));
      sprite.userData.baseScaleX = 0.052;
      sprite.userData.baseScaleY = 0.052;
      return sprite;
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
      const markerGeometry = new THREE.SphereGeometry(0.021, 16, 16);
      const placeMaterial = new THREE.MeshBasicMaterial({ color: 0x42ff8c });
      const coordinateMaterial = new THREE.MeshBasicMaterial({ color: 0x42ff8c });
      const selectedMaterial = new THREE.MeshBasicMaterial({ color: 0x72d7ff });
      const militarySprite = overlayIconSprite(THREE, "military");
      const nuclearSprite = overlayIconSprite(THREE, "nuclear");
      globeState.locations.forEach((location, index) => {
        const p = latLonVector(location.latitude, location.longitude, 1.045);
        const marker = new THREE.Mesh(markerGeometry, location.precision === "coordinate" ? coordinateMaterial : placeMaterial);
        marker.position.set(p.x, p.y, p.z);
        marker.userData.locationIndex = index;
        marker.userData.defaultMaterial = marker.material;
        marker.userData.selectedMaterial = selectedMaterial;
        marker.userData.selectionScale = 1;
        globeGroup.add(marker);
        globeState.markers.push(marker);
      });
      overlayState.markers = [];
      nearbyOverlayFacilities(500).forEach((facility) => {
        const p = latLonVector(facility.latitude, facility.longitude, 1.066);
        const marker = (facility.kind === "military" ? militarySprite : nuclearSprite).clone();
        marker.position.set(p.x, p.y, p.z);
        marker.userData.facility = facility;
        marker.visible = Boolean(overlayState.visible[facility.kind]);
        globeGroup.add(marker);
        overlayState.markers.push(marker);
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
      let targetZoom = camera.position.z;
      const clampZoom = (z) => Math.max(1.22, Math.min(7.8, z));
      const setZoom = (z, immediate = false) => {
        targetZoom = clampZoom(z);
        if (immediate) {
          camera.position.z = targetZoom;
        }
      };
      const zoomRotationScale = () => {
        const t = (camera.position.z - 1.22) / (7.8 - 1.22);
        return Math.max(0.32, Math.min(1.18, 0.32 + t * 0.86));
      };
      const applyMarkerZoomScale = () => {
        const zoomRatio = Math.pow(camera.position.z / 3.8, 1.45);
        const archiveScale = Math.max(0.26, Math.min(1.45, zoomRatio));
        const overlayScale = Math.max(0.32, Math.min(1.55, zoomRatio));
        globeState.markers.forEach((marker) => {
          marker.scale.setScalar((marker.userData.selectionScale || 1) * archiveScale);
        });
        overlayState.markers.forEach((marker) => {
          marker.scale.set(
            (marker.userData.baseScaleX || 0.052) * overlayScale,
            (marker.userData.baseScaleY || 0.052) * overlayScale,
            1
          );
        });
      };
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
        const hit = raycaster.intersectObjects([...globeState.markers, ...overlayState.markers.filter((marker) => marker.visible)])[0];
        if (!hit) return;
        if (Number.isInteger(hit.object.userData.locationIndex)) {
          selectGlobeLocation(hit.object.userData.locationIndex);
          return;
        }
        if (hit.object.userData.facility) {
          selectReferencePoint(hit.object.userData.facility);
        }
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
        const speed = 0.006 * zoomRotationScale();
        if (Math.abs(dx) + Math.abs(dy) > 6) moved = true;
        globeGroup.rotation.y += dx * speed;
        globeGroup.rotation.x += dy * speed * 0.7;
        globeGroup.rotation.x = Math.max(-1.15, Math.min(1.15, globeGroup.rotation.x));
        lastX = event.clientX;
        lastY = event.clientY;
      });
      canvas.addEventListener("wheel", (event) => {
        event.preventDefault();
        const delta = Math.max(-0.48, Math.min(0.48, event.deltaY * 0.0028));
        setZoom(targetZoom + delta);
      }, { passive: false });
      $("mapZoomIn").addEventListener("click", () => {
        setZoom(targetZoom - 0.58);
        track("map_zoom", { control: "in" });
      });
      $("mapZoomOut").addEventListener("click", () => {
        setZoom(targetZoom + 0.58);
        track("map_zoom", { control: "out" });
      });
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
            setZoom(pinchStartZ * (pinchStartDistance / distance), true);
          }
          moved = true;
          return;
        }
        const touch = event.touches[0];
        if (!touch || touchMode !== "rotate") return;
        const dx = touch.clientX - lastX;
        const dy = touch.clientY - lastY;
        const speed = zoomRotationScale();
        if (Math.abs(touch.clientX - touchStartX) + Math.abs(touch.clientY - touchStartY) > 6) moved = true;
        globeGroup.rotation.y += dx * 0.009 * speed;
        globeGroup.rotation.x += dy * 0.0063 * speed;
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
        camera.position.z += (targetZoom - camera.position.z) * 0.18;
        applyMarkerZoomScale();
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

    function selectReferencePoint(facility) {
      globeState.selected = null;
      globeState.selectedIndex = null;
      updateGlobeSelection();
      renderSelectedLocation({ ...facility, facilityKind: facility.kind });
      track("map_reference_point", { kind: facility.kind, name: facility.name });
    }

    function clearGlobeLocation() {
      globeState.selected = null;
      globeState.selectedIndex = null;
      updateGlobeSelection();
      renderSelectedLocation(null);
    }

    function setView(view, options = {}) {
      currentView = ["home", "search", "map"].includes(view) ? view : "home";
      const home = $("homeView");
      const search = $("searchView");
      const map = $("mapView");
      if (home) home.hidden = currentView !== "home";
      if (search) search.hidden = currentView !== "search";
      if (map) map.hidden = currentView !== "map";
      document.querySelectorAll("[data-view-target]").forEach((button) => {
        button.classList.toggle("active", button.dataset.viewTarget === currentView);
      });
      if (currentView === "map") {
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

    function openMap(options = {}) {
      setView("map", { scroll: options.scroll });
      if (options.updateHash) {
        setRouteHash("#map");
      }
    }

    function mapHash(docId = "") {
      return docId ? `#map?doc=${encodeURIComponent(docId)}` : "#map";
    }

    function openMapForDoc(docId, options = {}) {
      const doc = docs.find((item) => item.doc_id === docId);
      if (!doc || !hasMapLocation(doc)) return;
      setView("map", { scroll: options.scroll ?? true });
      if (options.updateHash) {
        setRouteHash(mapHash(docId));
      }
      const selectWhenReady = (attempt = 0) => {
        const index = globeState.locations.findIndex((location) => location.doc_id === docId);
        if (globeState.ready && index >= 0) {
          selectGlobeLocation(index);
          track("open_map_doc", { doc_id: docId, source: options.source || "" });
          return;
        }
        if (attempt < 50) {
          window.setTimeout(() => selectWhenReady(attempt + 1), 100);
        }
      };
      selectWhenReady();
    }

    function applyRoute() {
      const hash = window.location.hash || "";
      if (hash.startsWith("#search")) {
        const queryText = hash.includes("?") ? hash.slice(hash.indexOf("?") + 1) : "";
        const params = new URLSearchParams(queryText);
        openSearch(params.get("q") || "", { updateHash: false });
      } else if (hash.startsWith("#map")) {
        const queryText = hash.includes("?") ? hash.slice(hash.indexOf("?") + 1) : "";
        const params = new URLSearchParams(queryText);
        const docId = params.get("doc") || "";
        if (docId) {
          openMapForDoc(docId, { updateHash: false, scroll: false, source: "route" });
        } else {
          openMap({ updateHash: false });
        }
      } else {
        showHome({ updateHash: false });
      }
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
        .filter((doc) => !year || String(docDecade(doc)) === year)
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
      document.querySelectorAll(".result.open").forEach((card) => card.classList.remove("open"));
      openSearch("", { updateHash: true, scroll: true });
    }

    document.addEventListener("click", (event) => {
      const viewTarget = event.target.closest("[data-view-target]");
      if (viewTarget) {
        if (viewTarget.dataset.viewTarget === "search") {
          track("nav_search");
          openSearch($("q").value, { updateHash: true, scroll: true });
        } else if (viewTarget.dataset.viewTarget === "map") {
          track("nav_map");
          openMap({ updateHash: true, scroll: true });
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
        const card = document.getElementById(`doc-${button.dataset.docId}`) || document.getElementById(`map-doc-${button.dataset.docId}`);
        if (card) card.classList.toggle("open");
        track("summary_toggle", { doc_id: button.dataset.docId, open: card?.classList.contains("open") ? "true" : "false" });
      }
      const releaseToggle = event.target.closest("[data-release-toggle]");
      if (releaseToggle) {
        const group = releaseToggle.closest(".release-group");
        const collapsed = !group?.classList.contains("collapsed");
        if (group) group.classList.toggle("collapsed", collapsed);
        releaseToggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
        track("highlight_release_toggle", { release: releaseToggle.dataset.releaseToggle, open: collapsed ? "false" : "true" });
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
      const featureMap = event.target.closest("[data-feature-map]");
      if (featureMap) {
        openMapForDoc(featureMap.dataset.featureMap, { updateHash: true, scroll: true, source: "highlight" });
      }
      const docMap = event.target.closest("[data-doc-map]");
      if (docMap) {
        openMapForDoc(docMap.dataset.docMap, { updateHash: true, scroll: true, source: "index" });
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
      clearGlobeLocation();
      showHome({ updateHash: true, scroll: true });
    });
    $("reset").addEventListener("click", () => {
      track("reset", { control: "button" });
      resetArchiveView();
    });
    $("legendToggle").addEventListener("click", () => {
      const legend = $("mapLegend");
      const collapsed = !legend.classList.contains("collapsed");
      legend.classList.toggle("collapsed", collapsed);
      $("legendToggle").setAttribute("aria-expanded", collapsed ? "false" : "true");
      track("map_legend_toggle", { open: collapsed ? "false" : "true" });
    });
    document.querySelectorAll("[data-overlay-toggle]").forEach((input) => {
      input.addEventListener("change", () => {
        const kind = input.dataset.overlayToggle;
        overlayState.visible[kind] = input.checked;
        updateOverlayMarkers();
        track("map_overlay_toggle", { kind, open: input.checked ? "true" : "false" });
      });
    });
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
    "flir": "FLIR",
    "foo": "Foo fighters",
    "foofighter": "Foo fighters",
    "foofighters": "Foo fighters",
    "gemini": "Gemini",
    "helicopter": "Helicopter",
    "helicopters": "Helicopter",
    "kazakhstan": "Kazakhstan",
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
    "soviet": "Soviet Union",
    "sphere": "Spherical object",
    "spheres": "Spherical object",
    "uap": "UAP",
    "uaps": "UAP",
    "ufo": "UFO",
    "ufos": "UFO",
    "usaf": "USAF",
    "uss": "Navy",
    "ussr": "Soviet Union",
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
    (re.compile(r"\bgreen\s+fireballs?\b", re.I), "Green fireballs"),
    (re.compile(r"\borange\s+orbs?\b", re.I), "Orange orbs"),
    (re.compile(r"\bsandia\s+(?:base|national\s+lab)", re.I), "Sandia Base"),
    (re.compile(r"\blos\s+alamos\b", re.I), "Los Alamos"),
    (re.compile(r"\bnew\s+mexico\b", re.I), "New Mexico"),
    (re.compile(r"\bsary\s+shagan\b", re.I), "Sary Shagan"),
    (re.compile(r"\bpantex\b", re.I), "Pantex Plant"),
    (re.compile(r"\b(?:nuclear|atomic|weapons?)\s+(?:facilit|site|complex|plant|range|reservation)", re.I), "Nuclear facility"),
    (re.compile(r"\btest\s+range\b", re.I), "Test range"),
]

AGENCY_TAGS = {
    "Department of War": "War Department",
    "Department of State": "State Department",
    "FBI": "FBI",
    "NASA": "NASA",
}

# Ordered highlight release groups. Each curated selection belongs to one group
# via its optional "release" key (defaulting to DEFAULT_RELEASE). A group only
# renders on the public site once it has at least one matched selection, so new
# groups can be defined ahead of a drop without changing the visible page.
#   date          - hard display-date override; empty means derive from the
#                   group's documents (their release_date).
#   fallback_date - used only when no override and no document release_date.
DEFAULT_RELEASE = "release-1"
RELEASE_GROUPS = [
    {"key": "release-2", "label": "RELEASE 2", "date": "", "fallback_date": "5/22/26"},
    {"key": "release-1", "label": "RELEASE 1", "date": "", "fallback_date": "5/8/26"},
]

FEATURED_SELECTIONS = [
    {
        "match": "Western US Event",
        "title": "Orbs Launching Orbs",
        "kicker": "Multi-team orb report",
        "summary": "Over two dusk periods in the western United States, three separate two-person teams of federal law-enforcement special agents reported the same pattern: a large orange orb appeared for one or two seconds, released smaller red orbs in groups of two to four, then vanished. The source says the sequence happened at least five times, with the red orbs moving horizontally, angling upward, or swooping downward after launch.",
        "facts": [
            "Agency: Department of War",
            "Incident year: 2023",
            "Source: Western US Event slides, page 1",
            "Why it stands out: multiple teams reported the same pattern from different vantage points",
        ],
    },
    {
        "match": "USPER Statement about UAP Sighting",
        "kicker": "Senior official narrative",
        "summary": "In an FBI 302 interview, a senior U.S. intelligence official described a search near a military facility after earlier orb sightings. The account says a helicopter crew found a \"super-hot\" orb hovering near the ground, pursued it for roughly 20 miles, then saw a swarm of lights and repeated groups of four or five orbs flaring up and fading over the next half hour.",
        "facts": [
            "Agency: Department of State",
            "Incident year: 2025",
            "Why it stands out: detailed first-person style account with redactions",
        ],
    },
    {
        "match": "FBI September 2023 Sighting - Composite Sketch",
        "kicker": "FBI visual reconstruction",
        "summary": "The FBI Lab composite places a rendered bronze ellipsoid over a real site photo to show what corroborating witnesses reported in September 2023. The object was described as emerging from a bright light, measuring roughly 130 to 195 feet, and disappearing instantaneously.",
        "facts": [
            "Agency: FBI",
            "Incident date: September 1, 2023",
            "Why it stands out: image-based record tied to witness interviews",
        ],
    },
    {
        "match": "FBI Photo A1",
        "kicker": "Late-2025 image set",
        "summary": "This FBI-submitted still image came from a U.S. government system and was redacted before being sent to AARO. The record describes a monochrome sensor frame with a crosshair reticle and a small, dark, irregular object just below and to the right of center; no mission report, date, or location was provided.",
        "facts": [
            "Agency: FBI",
            "Incident date: Late 2025",
            "Why it stands out: public photo record with linked media",
        ],
    },
    {
        "match": "NASA-UAP-VM6, Apollo 17, 1972",
        "kicker": "Apollo lunar image",
        "summary": "A December 1972 Apollo 17 photograph shows three dots in a triangular formation in the lower-right lunar sky when magnified. The case notes say the original film was obtained for review and that preliminary U.S. government analysis considered whether the feature could reflect a physical object in the scene, while stopping short of a conclusion.",
        "facts": [
            "Agency: NASA",
            "Incident year: 1972",
            "Why it stands out: visual lunar record with highlighted anomaly area",
        ],
    },
    {
        "match": "NASA-UAP-D2, Apollo 17 Transcript, 1972",
        "kicker": "Lunar transcript",
        "summary": "The Apollo 17 transcript excerpt gathers three unusual observation windows from the mission: bright particles or fragments near the spacecraft, repeated flashing or rotating phenomena during a later three-hour stretch, and Jack Schmitt's report of a flash on the lunar surface north of Grimaldi. The crew discussed possible mundane explanations, including ice, paint, rocket-stage debris, and adapter panels.",
        "facts": [
            "Agency: NASA",
            "Incident year: 1972",
            "Why it stands out: mission transcript context for a lunar observation",
        ],
    },
    {
        "match": "255-t-763-r1b-excerpt",
        "kicker": "Gemini VII audio",
        "summary": "During Gemini VII air-to-ground communications on December 5, 1965, astronaut Frank Borman reported seeing an unidentified object he called a \"bogey.\" The audio excerpt also includes comments from crewmate Jim Lovell and NASA Public Affairs narration, making the exchange directly listenable rather than just summarized.",
        "facts": [
            "Agency: NASA",
            "Incident date: December 5, 1965",
            "Why it stands out: mission audio and transcript context",
        ],
    },
    {
        "match": "State Department UAP Cable 1, Papua New Guinea",
        "kicker": "Diplomatic cable",
        "summary": "A January 1985 cable from the U.S. Embassy in Port Moresby reports that Papua New Guinea intelligence officials asked about high-altitude, high-speed aircraft after residents were frightened by nighttime overflights. The cable cites reports of fast-moving lights, contrails, noise, and an Air Niugini pilot's radar account, while calling the available information \"very sketchy.\"",
        "facts": [
            "Agency: Department of State",
            "Incident date: January 24, 1985",
            "Why it stands out: local report preserved in embassy correspondence",
        ],
    },
    {
        "match": "State Department UAP Cable 2, Kazakhstan",
        "kicker": "Post-Soviet cable",
        "summary": "A January 1994 State Department cable says one Tajik pilot and three American citizens encountered an intense bright object while flying a 747 at 41,000 feet over Kazakhstan. The report describes a bullet-like light approaching at great speed, making 90-degree turns, corkscrews, and circles, with contrails visually estimated near 100,000 feet.",
        "facts": [
            "Agency: Department of State",
            "Incident year: 1994",
            "Why it stands out: international cable traffic in the release",
        ],
    },
    {
        "match": "331_120752_Numeric_Files_1944",
        "kicker": "Wartime foo-fighter file",
        "summary": "This 1944-1945 SHAEF file collects wartime messages about \"night phenomena,\" flak rockets, unidentified cylindrical objects, and blinking lights. Several records point back to observations by the 415th Night Fighter Squadron, placing the so-called foo-fighter material inside operational military traffic rather than later folklore.",
        "facts": [
            "Agency: Department of War",
            "Incident date: March 18, 1945",
            "Why it stands out: early military reports before the postwar flying-disc wave",
        ],
    },
    {
        "match": "65_HS1-834228961_62-HQ-83894_Section_5",
        "kicker": "FBI master file",
        "summary": "The FBI's 62-HQ-83894 file gathers more than two decades of flying-disc and UFO material, including investigative records, eyewitness reports, public correspondence, Oak Ridge photographic material, propulsion proposals, convention programs, and press coverage. This release includes a fuller version of the file than the FBI Vault posting, with newly declassified pages and fewer redactions.",
        "facts": [
            "Agency: FBI",
            "Records span: 1947-1968 cluster",
            "Why it stands out: deep archival FBI flying-disc material",
        ],
    },
    {
        "match": "DOW-UAP-PR46",
        "kicker": "INDOPACOM video",
        "summary": "INDOPACOM submitted nine seconds of 2024 infrared footage from a U.S. military platform over the East China Sea. The release description says the sensor focused on a football-shaped area of contrast with three radial projections, while noting that no oral or written reporter description accompanied the video.",
        "facts": [
            "Agency: Department of War",
            "Incident region: East China Sea",
            "Why it stands out: widely discussed football-shaped video",
        ],
    },
    {
        "match": "DOW-UAP-PR47",
        "kicker": "Japan sensor case",
        "summary": "This Japan-area INDOPACOM record contains one minute and 59 seconds of 2023 infrared sensor footage. The official video description says the sensor tracks three distinct areas of contrast that remain generally centered and appear to hold a fixed position and orientation relative to one another.",
        "facts": [
            "Agency: Department of War",
            "Incident region: Japan",
            "Why it stands out: modern Indo-Pacific video record",
        ],
    },
    {
        "match": "DOW-UAP-PR48",
        "kicker": "Wind-farm video",
        "summary": "In this 2024 INDOPACOM video, an infrared sensor aboard a U.S. military platform tracks one area of contrast for one minute and 39 seconds. The official description is sparse: the target remains generally centered in frame, and the reporter provided no separate oral or written account.",
        "facts": [
            "Agency: Department of War",
            "Incident year: 2024",
            "Why it stands out: distinctive wind-turbine sensor scene",
        ],
    },
    {
        "match": "DOW-UAP-PR34",
        "kicker": "Aegean maneuver video",
        "summary": "CENTCOM's October 2023 Greece report includes nearly three minutes of infrared footage and an accompanying mission report describing a UAP near the ocean surface making multiple 90-degree turns at about 80 miles per hour. The video description says an area of contrast enters from the lower-left field of view, then moves back and forth as the sensor pans to track it.",
        "facts": [
            "Agency: Department of War",
            "Incident region: Greece",
            "Why it stands out: Aegean video with notable reported movement",
        ],
    },
    {
        "match": "DOW-UAP-PR28",
        "kicker": "Glowing IR signature",
        "summary": "In the January 2024 Greece case, CENTCOM submitted one minute and five seconds of multi-sensor footage. The accompanying mission report described a diamond-shaped UAP moving at about 434 knots and detectable only in short-wave infrared, with the video opening in split-screen electro-optical and SWIR views.",
        "facts": [
            "Agency: Department of War",
            "Incident region: Greece",
            "Why it stands out: distinctive halo-like IR appearance",
        ],
    },
    {
        "match": "DOW-UAP-PR43",
        "kicker": "Africa airspace video",
        "summary": "AFRICOM's 2025 Djibouti entry is only two seconds long. The infrared sensor footage shows a small, barely distinguishable area of contrast moving from the left side of the frame toward the lower-right edge; the reporter supplied no separate description.",
        "facts": [
            "Agency: Department of War",
            "Incident region: Africa",
            "Why it stands out: geographic breadth in the video release",
        ],
    },
    {
        "match": "DOW-UAP-PR49",
        "kicker": "2026 Army report",
        "summary": "The Department of the Army's 2026 North America report includes one minute and 49 seconds of infrared video. The sensor first tracks one area of interest, then pans to follow two areas of contrast, zooming in and out while keeping them generally centered; no oral or written reporter description came with the footage.",
        "facts": [
            "Agency: Department of War",
            "Incident year: 2026",
            "Why it stands out: one of the newest records in the release",
        ],
    },
    {
        "match": "ODNI USPER Narrative",
        "release": "release-2",
        "kicker": "Senior officer orb encounter",
        "summary": "In a first-person narrative, a senior U.S. intelligence officer says that in late 2025 he, a colleague, and two pilots flew a helicopter from a Joint Operations Center to investigate loud thuds in mountains on a test range during several nights of UAP sightings. Over more than an hour of close encounters, the officer recounts ground teams reporting a \"super-hot\" object on FLIR that split in two, an object rising from the ground to within ten feet of the helicopter before speeding away, and large oval orange orbs with bright centers that flared stationary just above the rotor disk and formed a \"T\" of four to five orbs that dimmed in reverse order. He says orange orbs later appeared above fighter jets at about 23,000 feet, matched their flight path as if chasing them, and formed a triangle around the helicopter before vanishing.",
        "facts": [
            "Agency: ODNI",
            "Incident year: 2025",
            "Source: ODNI USPER (US Person) narrative; the officer did not photograph the event",
            "Why it stands out: detailed close-encounter account that parallels Release 1's orange-orb cases",
        ],
    },
    {
        "match": "Sandia Base Correspondence",
        "release": "release-2",
        "kicker": "Green fireballs investigation",
        "summary": "This 116-page compilation of late-1940s correspondence centers on Sandia Base in Albuquerque, New Mexico, beside the atomic-weapons complex. Its centerpiece is the 17th District OSI \"Summary of Observations of Aerial Phenomena in the New Mexico area\" — the green fireballs investigation — cataloging unexplained sightings concentrated in New Mexico from late 1948 onward, recurring green fireballs near Los Alamos and Sandia, and a noted surge where the summary says flying-saucer incidents in the region \"attained an all-time high.\" The file describes unidentified lights over the 2nd Armored Division triangulated from multiple observers and references a \"Photo of Sighting No. 175.\"",
        "facts": [
            "Agency: Department of War",
            "Incident years: 1948-1949",
            "Source: Sandia Base security and OSI correspondence, 116 pages",
            "Why it stands out: primary-source material from the early-Cold-War New Mexico green-fireball wave",
        ],
    },
    {
        "match": "Sary Shagan",
        "release": "release-2",
        "kicker": "Soviet test-range sighting",
        "summary": "A CIA Intelligence Information Report sourced to a former Soviet citizen, acquired via Germany and dated December 1973, mostly describes the Soviet Sary Shagan weapons testing range in Kazakhstan, its facilities, the System-75/SA-2 and System-300/Aldan anti-missile warheads, and rumored laser research. The UAP element: one evening in late summer 1973 at \"Site 7,\" the source stepped outside during a televised Canada-USSR sport competition and reports seeing a bright green circular object in the western sky at about 70 degrees elevation. Within 10 to 15 seconds, the source says, the green circle widened and several concentric green circles formed around the mass before the color faded over a few minutes, with no sound and no explanation offered.",
        "facts": [
            "Agency: CIA",
            "Incident year: 1973 (declassified 2026)",
            "Source: CIA Intelligence Information Report, source was a former Soviet citizen",
            "Why it stands out: a Soviet weapons-range observation echoing the green-phenomena pattern",
        ],
    },
    {
        "match": "Pantex Plant Unidentified Object",
        "release": "release-2",
        "kicker": "Radar-tower image",
        "summary": "A Pantex Unidentified Object Incident Report from the U.S. nuclear-weapons assembly and disassembly facility near Amarillo, Texas, centers on an image of an unidentified object captured from a Ground Surveillance Radar Tower, plus Sandia National Labs enhanced images of the object. The release is essentially the imagery pages with little narrative text, and the material is marked UCNI (Unclassified Controlled Nuclear Information).",
        "facts": [
            "Agency: Department of Energy / Pantex Plant",
            "Source: Ground Surveillance Radar Tower image with Sandia enhancements; marked UCNI",
            "Why it stands out: a radar-tower image of an unidentified object over a nuclear-weapons site",
        ],
    },
    {
        "match": "James L. Tuck Correspondence",
        "release": "release-2",
        "kicker": "Los Alamos physicist letters",
        "summary": "Correspondence involving Los Alamos physicist James L. Tuck. In one 1970s letter to the U.S. Army Engineer School at Fort Belvoir, Virginia, the writer asks for the \"recipe\" used in simulated atomic-bomb demonstrations, citing interest in \"large atmospheric vortices\" reported in Dr. Edward U. Condon's \"Scientific Study of Unidentified Flying Objects\" (the Condon Report). Another letter discusses UFO author James M. McCampbell's 1976 book \"UFOLOGY,\" its \"Flight and Propulsion\" chapter, and Einstein's unified field theory.",
        "facts": [
            "Agency: Department of Energy / Los Alamos",
            "Records era: 1970s",
            "Source: James L. Tuck correspondence files",
            "Why it stands out: a working nuclear physicist engaging with UFO propulsion ideas and the Condon Report",
        ],
    },
    {
        "match": "Pajarito Astronomers",
        "release": "release-2",
        "kicker": "Los Alamos meeting notice",
        "summary": "A meeting notice from the Pajarito Astronomers of Los Alamos, New Mexico, dated Tuesday, May 20, 1986, announces a meeting on Thursday, May 29, 1986 in the Ranch Room at Fuller Lodge. The guest speaker is Dr. John Warren of group AT-6, with the topic billed as \"Why Should a Scientist Be Concerned about UFO's?\"",
        "facts": [
            "Agency: Department of Energy / Los Alamos",
            "Incident date: May 1986",
            "Source: Pajarito Astronomers meeting notice",
            "Why it stands out: a Los Alamos science group openly taking up the UFO question",
        ],
    },
    {
        "match": "DOW-UAP-PR071",
        "release": "release-2",
        "kicker": "F-16 engages an object over Lake Huron",
        "summary": "Uploader-titled \"USAF ANG F-16C Shoots Down UAP over Lake Huron with [Weapon System], 12 Feb 2023,\" this 46-second infrared clip is tied to the U.S. Northern Command area in 2023. AARO's deliberately neutral description says the sensor centers on an area of contrast and that around the 20-second mark the footage appears to show a kinetic interaction between two areas of contrast, with the initial subject fragmenting in a radial displacement pattern that AARO says suggests a high-energy event. AARO states the description is informational only and not an analytical conclusion.",
        "facts": [
            "Agency: Department of War (NORTHCOM)",
            "Incident: 12 February 2023, Lake Huron",
            "Source: infrared sensor video uploaded to a classified network",
            "Why it stands out: appears to capture the February 2023 fighter engagement of an object over Lake Huron",
        ],
    },
    {
        "match": "DOW-UAP-PR050",
        "release": "release-2",
        "kicker": "Four objects in formation off Iran",
        "summary": "Uploader-titled \"4 UAP Formation Iran 26 Aug 2022 over water,\" this short infrared clip is tied to U.S. Central Command in 2022. AARO describes four areas of contrast transiting the sensor's field of view, entering from the lower-left and exiting near the bottom center, followed by a fifth area of contrast entering from the top-left corner. AARO frames the account as an informational description only.",
        "facts": [
            "Agency: Department of War (CENTCOM)",
            "Incident: 26 August 2022, over water (Iran area)",
            "Source: infrared sensor video uploaded to a classified network",
            "Why it stands out: a multi-object formation tracked over water",
        ],
    },
    {
        "match": "DOW-UAP-PR051",
        "release": "release-2",
        "kicker": "\"Instant acceleration\" over Syria",
        "summary": "Uploader-titled \"Syrian UAP instant acceleration,\" this roughly five-minute CENTCOM infrared clip was digitally altered before upload and is presented as received. AARO notes the sensor pans to hold an object centered, then at the 20-21 second mark stops tracking, which causes the object to rapidly exit the frame; a later title card within the clip says a white-edge threshold enhancement was applied to highlight the shape. AARO presents the footage without an analytical conclusion.",
        "facts": [
            "Agency: Department of War (CENTCOM)",
            "Incident year: 2021",
            "Note: the apparent rapid acceleration coincides with the sensor ceasing to track the object",
            "Why it stands out: a much-discussed \"instant acceleration\" clip, shown with AARO's neutral framing",
        ],
    },
    {
        "match": "DOW-UAP-PR057b",
        "release": "release-2",
        "kicker": "Sphere over the Yellow Sea",
        "summary": "Uploader-titled both \"Spherical UAP in clouds\" and \"[Platform] Observes UAP in East China Sea, 05 Jan 2023,\" this 70-second infrared clip is tied to a U.S. platform operating above the Yellow Sea in January 2023. AARO describes an area of contrast entering the frame and becoming indistinguishable against the background, after which the sensor zooms and pans to re-acquire and track it. AARO frames the account as an informational description only.",
        "facts": [
            "Agency: Department of War (INDOPACOM)",
            "Incident: 5 January 2023, Yellow Sea / East China Sea",
            "Source: infrared sensor video uploaded to a classified network",
            "Why it stands out: a spherical object tracked near cloud cover in the Pacific theater",
        ],
    },
    {
        "match": "DOW-UAP-PR065",
        "release": "release-2",
        "kicker": "Coast Guard \"Tic Tac\" off Tyndall",
        "summary": "Uploader-titled \"USCG C-144 Tyndall UAP 2 TIC TAC IR hot 24 April 2024,\" this clip comes from an infrared sensor aboard a U.S. Coast Guard aircraft operating over the southeastern United States in 2024. AARO describes the sensor panning to keep an area of contrast in view for about 32 seconds before it leaves the frame. The \"tic tac\" shape and \"IR hot\" signature are the uploader's characterization, not an AARO conclusion.",
        "facts": [
            "Agency: Department of War / U.S. Coast Guard",
            "Incident: 24 April 2024, southeastern United States",
            "Source: infrared sensor video uploaded to a classified network",
            "Why it stands out: a recent Coast Guard \"Tic Tac\" infrared track",
        ],
    },
    {
        "match": "DOW-UAP-PR086",
        "release": "release-2",
        "kicker": "December 2019 East Coast object",
        "summary": "Uploader-titled \"UAP from Dec 2019 (East Coast),\" this 34-second infrared clip is tied to the U.S. Northern Command area in 2019 and was placed on a classified network in September 2020. AARO describes the sensor tracking an area of contrast and switching contrast modes during the clip, and frames the account as an informational description only.",
        "facts": [
            "Agency: Department of War (NORTHCOM)",
            "Incident year: 2019, U.S. East Coast",
            "Source: infrared sensor video uploaded to a classified network",
            "Why it stands out: an East Coast case from the period of the Navy UAP disclosures",
        ],
    },
    {
        "match": "NASA-UAP-D009",
        "release": "release-2",
        "kicker": "Apollo 17 crew describe drifting lights",
        "summary": "On Apollo 17's transit to the Moon on December 7, 1972, commander Gene Cernan, lunar module pilot Harrison Schmitt, and command module pilot Ronald Evans are heard describing bright \"particles\" or \"fragments\" drifting near the spacecraft and the separated Saturn S-IVB stage. The crew call them \"jagged\" and \"angular,\" note that they \"twinkle,\" and speculate the lights are likely paint chips or ice chips coming off the stage.",
        "facts": [
            "Agency: NASA",
            "Incident: 7 December 1972, cislunar space",
            "Source: Apollo 17 mission audio excerpt",
            "Why it stands out: astronaut audio of unexplained drifting lights, with the crew's own mundane hypothesis on the record",
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
                "release": selection.get("release", DEFAULT_RELEASE),
                "title": selection.get("title") or doc["title"],
                "record_title": doc["title"],
                "kicker": selection["kicker"],
                "summary": featured_summary(selection, doc),
                "facts": selection["facts"],
                "agency": doc["agency"],
                "release_date": doc["release_date"],
                "incident_date": doc["incident_date"],
                "incident_location": doc["incident_location"],
                "source_url": doc["source_url"],
                "media": doc["media"],
                "locations": doc.get("locations", []),
                "tags": doc["tags"][:6],
            }
        )
    return featured


def featured_summary(selection: Dict, doc: Dict) -> str:
    return selection["summary"]


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


def normalize_google_analytics_id(measurement_id: str) -> str:
    measurement_id = clean(measurement_id).upper()
    if not measurement_id:
        return ""
    if not re.fullmatch(r"(?:G|GT|AW)-[A-Z0-9-]+", measurement_id):
        raise ValueError("Google Analytics measurement/tag ID must look like G-XXXXXXXX, GT-XXXXXXXX, or AW-XXXXXXXX")
    return measurement_id


def google_analytics_snippet(measurement_id: str = "") -> str:
    measurement_id = normalize_google_analytics_id(measurement_id)
    if not measurement_id:
        return ""
    safe_id = html_escape(measurement_id, quote=True)
    return (
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={safe_id}"></script>\n'
        "  <script>\n"
        "    window.dataLayer = window.dataLayer || [];\n"
        "    function gtag(){dataLayer.push(arguments);}\n"
        "    gtag('js', new Date());\n"
        f"    gtag('config', '{safe_id}');\n"
        "  </script>"
    )


def analytics_markup(
    plausible_domain: str = "",
    plausible_script_url: str = "https://plausible.io/js/script.js",
    google_analytics_id: str = "",
) -> str:
    snippets = [
        analytics_snippet(plausible_domain, plausible_script_url),
        google_analytics_snippet(google_analytics_id),
    ]
    return "\n  ".join(snippet for snippet in snippets if snippet)


def normalize_site_url(site_url: str) -> str:
    site_url = clean(site_url) or "https://disclosurearchive.org"
    if not re.match(r"^https://[A-Za-z0-9.-]+(?::\d+)?(?:/.*)?$", site_url):
        raise ValueError("site URL must be an HTTPS URL")
    return site_url.rstrip("/")


def normalize_contact_email(contact_email: str) -> str:
    contact_email = clean(contact_email) or "contact@rebuilt.cards"
    if contact_email.lower().startswith("mailto:"):
        contact_email = contact_email[7:]
    if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", contact_email):
        raise ValueError("contact email must be a valid email address")
    return contact_email


def origin_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return ""


def seo_meta(site_url: str) -> str:
    canonical = f"{site_url}/"
    description = (
        "Search and explore public UFO/UAP release records with curated highlights, "
        "government source links, document summaries, videos, photos, map locations, "
        "and provenance-preserving references."
    )
    image = f"{site_url}/social-card.png"
    title = "Disclosure Archive | Public UFO/UAP Release Index"
    return "\n  ".join(
        [
            f'<meta name="description" content="{html_escape(description, quote=True)}">',
            '<meta name="keywords" content="UFO archive,UAP archive,UFO documents,UAP documents,Disclosure Archive,government UFO records,NASA UAP,FBI UFO,Department of War UAP">',
            '<meta name="application-name" content="Disclosure Archive">',
            '<meta name="robots" content="index,follow,max-image-preview:large">',
            '<meta name="googlebot" content="index,follow,max-image-preview:large">',
            '<meta name="theme-color" content="#050806">',
            '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
            '<link rel="manifest" href="/site.webmanifest">',
            f'<link rel="canonical" href="{html_escape(canonical, quote=True)}">',
            '<link rel="sitemap" type="application/xml" href="/sitemap.xml">',
            '<meta property="og:type" content="website">',
            f'<meta property="og:url" content="{html_escape(canonical, quote=True)}">',
            f'<meta property="og:title" content="{html_escape(title, quote=True)}">',
            f'<meta property="og:description" content="{html_escape(description, quote=True)}">',
            f'<meta property="og:image" content="{html_escape(image, quote=True)}">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            '<meta property="og:image:type" content="image/png">',
            '<meta property="og:image:alt" content="Disclosure Archive public UFO/UAP release index">',
            '<meta property="og:site_name" content="Disclosure Archive">',
            '<meta property="og:locale" content="en_US">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{html_escape(title, quote=True)}">',
            f'<meta name="twitter:description" content="{html_escape(description, quote=True)}">',
            f'<meta name="twitter:image" content="{html_escape(image, quote=True)}">',
            '<meta name="twitter:image:alt" content="Disclosure Archive public UFO/UAP release index">',
        ]
    )


def csp_policy(analytics_script_url: str = "https://plausible.io/js/script.js", google_analytics_id: str = "") -> str:
    analytics_origin = origin_from_url(analytics_script_url)
    script_sources = ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"]
    connect_sources = ["'self'", "https://cdn.jsdelivr.net"]
    if analytics_origin:
        script_sources.append(analytics_origin)
        connect_sources.append(analytics_origin)
    if normalize_google_analytics_id(google_analytics_id):
        script_sources.append("https://www.googletagmanager.com")
        connect_sources.extend(
            [
                "https://www.google-analytics.com",
                "https://analytics.google.com",
                "https://region1.google-analytics.com",
                "https://region1.analytics.google.com",
            ]
        )
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


def security_meta(analytics_script_url: str = "https://plausible.io/js/script.js", google_analytics_id: str = "") -> str:
    policy = csp_policy(analytics_script_url, google_analytics_id)
    return "\n  ".join(
        [
            '<meta name="referrer" content="strict-origin-when-cross-origin">',
            f'<meta http-equiv="Content-Security-Policy" content="{html_escape(policy, quote=True)}">',
        ]
    )


def format_last_updated(generated_at: str) -> str:
    try:
        value = datetime.fromisoformat(generated_at)
    except ValueError:
        return generated_at[:10]
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc)
    return f"{value.strftime('%B')} {value.day}, {value.year}, {value.strftime('%H:%M')} UTC"


def site_footer(generated_at: str) -> str:
    updated = html_escape(format_last_updated(generated_at), quote=True)
    return f"""
  <footer class="site-footer">
    <div class="wrap footer-inner">
      <div class="footer-links">
        <span>&copy; 2026 Disclosure Archive.</span>
        <span class="footer-updated">Last updated {updated}</span>
        <a href="/contact.html">Contact</a>
        <a href="/legal.html">Legal / Impressum</a>
        <a href="/privacy.html">Privacy</a>
        <a href="/security.html">Security</a>
        <a href="/sitemap.xml">Sitemap</a>
      </div>
    </div>
  </footer>"""


def structured_data(site_url: str, document_count: int, featured: Optional[List[Dict]] = None) -> str:
    canonical = f"{site_url}/"
    featured = featured or []
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
                "publisher": {
                    "@type": "Organization",
                    "name": "Disclosure Archive",
                    "url": canonical,
                },
                "about": ["UFO", "UAP", "public records", "government documents", "archive search"],
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
                "creator": {
                    "@type": "Organization",
                    "name": "Disclosure Archive",
                    "url": canonical,
                },
                "about": [
                    {"@type": "Thing", "name": "Unidentified anomalous phenomena"},
                    {"@type": "Thing", "name": "UFO records"},
                    {"@type": "Thing", "name": "Government document archive"},
                ],
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{canonical}#breadcrumbs",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Disclosure Archive",
                        "item": canonical,
                    }
                ],
            },
        ],
    }
    if featured:
        graph["@graph"].append(
            {
                "@type": "ItemList",
                "@id": f"{canonical}#highlights",
                "name": "Disclosure Archive highlighted UFO/UAP records",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": index + 1,
                        "url": f"{canonical}#search?q={quote(item['title'])}",
                        "name": item["title"],
                        "description": item["summary"][:500],
                    }
                    for index, item in enumerate(featured[:18])
                ],
            }
        )
    text = json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
    return f'<script type="application/ld+json">{text}</script>'


def encoded_email_codes(contact_email: str) -> str:
    return ",".join(str(ord(char)) for char in contact_email)


def static_info_page(title: str, body: str, analytics_script_url: str, google_analytics_id: str = "", extra_script: str = "") -> str:
    safe_title = html_escape(title, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} | Disclosure Archive</title>
  {security_meta(analytics_script_url, google_analytics_id)}
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <style>
    :root {{ color-scheme: dark; --bg: #050806; --ink: #e7fff2; --muted: #8fb39e; --line: rgba(74, 255, 151, 0.22); --accent: #42ff8c; --accent-2: #72d7ff; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; background: var(--bg); color: var(--ink); font: 14px/1.55 ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace; }}
    main {{ width: min(760px, calc(100% - 32px)); margin: 0 auto; padding: 42px 0; }}
    a {{ color: var(--accent-2); }}
    h1 {{ margin: 0 0 18px; color: var(--accent); font-size: 24px; }}
    p, li {{ color: var(--muted); }}
    .panel {{ border: 1px solid var(--line); border-radius: 8px; background: rgba(5, 14, 10, 0.92); padding: 18px; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }}
    button, .button {{ min-height: 36px; border: 1px solid var(--line); border-radius: 6px; background: rgba(7, 24, 15, 0.92); color: var(--ink); cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 0 10px; text-decoration: none; font: inherit; font-weight: 650; }}
    button:hover, .button:hover {{ border-color: var(--accent); color: var(--accent); }}
  </style>
</head>
<body>
  <main>
    <p><a href="/">Disclosure Archive</a></p>
    <section class="panel">
      <h1>{safe_title}</h1>
      {body}
    </section>
  </main>
  {extra_script}
</body>
</html>
"""


def write_info_pages(out: Path, site_url: str, analytics_script_url: str, contact_email: str, google_analytics_id: str = "") -> None:
    email_codes = encoded_email_codes(contact_email)
    contact_body = f"""
      <p>Use this page for corrections, source issues, takedown requests, security reports, and general notes.</p>
      <p>The email address is opened only after you click the button.</p>
      <div class="actions">
        <button type="button" id="emailButton" data-email="{html_escape(email_codes, quote=True)}">Open email link</button>
      </div>
    """
    contact_script = """
  <script>
    (() => {
      const button = document.getElementById("emailButton");
      if (!button) return;
      const address = button.dataset.email.split(",").map((code) => String.fromCharCode(Number(code))).join("");
      button.addEventListener("click", () => {
        window.location.href = `mailto:${address}?subject=Disclosure%20Archive`;
      });
    })();
  </script>"""
    (out / "contact.html").write_text(static_info_page("Contact", contact_body, analytics_script_url, google_analytics_id, contact_script), encoding="utf-8")

    legal_body = """
      <p>Disclosure Archive is an independent public-interest index for public UFO/UAP release materials.</p>
      <p>It is not affiliated with the U.S. Department of War, NASA, FBI, Department of State, or any other source agency.</p>
      <p>Summaries are finding aids, not proof of claims. Verify important details against the linked source records.</p>
    """
    (out / "legal.html").write_text(static_info_page("Legal / Impressum", legal_body, analytics_script_url, google_analytics_id), encoding="utf-8")

    analytics_notice = (
        "<p>This build uses Google Analytics for aggregate traffic and coarse UI events. Search text is not sent; search events include query length only.</p>"
        if normalize_google_analytics_id(google_analytics_id)
        else "<p>Optional privacy-friendly analytics may be enabled without storing search text.</p>"
    )
    privacy_body = f"""
      <p>No accounts, forms, comments, ads, or marketing cookies are used.</p>
      <p>Search runs locally in your browser against static JSON. Search text is not sent to a Disclosure Archive server.</p>
      <p>The hosting provider may process standard request logs.</p>
      {analytics_notice}
    """
    (out / "privacy.html").write_text(static_info_page("Privacy", privacy_body, analytics_script_url, google_analytics_id), encoding="utf-8")

    security_body = f"""
      <p>For security reports, use the contact page or the public security file.</p>
      <div class="actions">
        <a class="button" href="/contact.html">Contact</a>
        <a class="button" href="/.well-known/security.txt">security.txt</a>
        <a class="button" href="{html_escape(site_url, quote=True)}/.well-known/security.txt">Canonical security.txt</a>
      </div>
    """
    (out / "security.html").write_text(static_info_page("Security", security_body, analytics_script_url, google_analytics_id), encoding="utf-8")


def write_social_card(out: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return

    width, height = 1200, 630
    image = Image.new("RGB", (width, height), "#050806")
    draw = ImageDraw.Draw(image)

    for y in range(height):
        green = int(8 + (y / height) * 18)
        blue = int(10 + (1 - y / height) * 16)
        draw.line([(0, y), (width, y)], fill=(5, green, blue))

    for x in range(0, width, 40):
        draw.line([(x, 0), (x, height)], fill=(16, 66, 40))
    for y in range(0, height, 40):
        draw.line([(0, y), (width, y)], fill=(14, 58, 36))

    draw.rectangle([(44, 44), (width - 44, height - 44)], outline=(66, 255, 140), width=3)
    draw.rectangle([(60, 60), (width - 60, height - 60)], outline=(114, 215, 255), width=1)
    draw.ellipse([(720, 95), (1110, 485)], outline=(66, 255, 140), width=5)
    draw.arc([(735, 110), (1095, 470)], 200, 340, fill=(114, 215, 255), width=3)
    draw.arc([(735, 110), (1095, 470)], 20, 160, fill=(114, 215, 255), width=3)
    draw.line([(915, 95), (915, 485)], fill=(114, 215, 255), width=3)
    draw.line([(720, 290), (1110, 290)], fill=(66, 255, 140), width=3)
    draw.ellipse([(1010, 142), (1058, 190)], fill=(255, 209, 102))

    font_candidates = [
        Path("C:/Windows/Fonts/consolab.ttf"),
        Path("C:/Windows/Fonts/consola.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
    ]

    def load_font(size: int):
        for path in font_candidates:
            if path.exists():
                return ImageFont.truetype(str(path), size=size)
        return ImageFont.load_default()

    title_font = load_font(76)
    sub_font = load_font(30)
    small_font = load_font(24)

    draw.text((96, 132), "Disclosure", fill=(231, 255, 242), font=title_font)
    draw.text((96, 218), "Archive", fill=(66, 255, 140), font=title_font)
    draw.text((100, 330), "PUBLIC UFO/UAP RELEASE INDEX", fill=(114, 215, 255), font=sub_font)
    draw.text((100, 382), "Highlights  /  Records  /  Map", fill=(143, 179, 158), font=small_font)
    draw.text((100, 504), "disclosurearchive.org", fill=(255, 209, 102), font=small_font)

    image.save(out / "social-card.png", "PNG", optimize=True)


def write_crawler_and_security_files(out: Path, site_url: str, generated_at: str, analytics_script_url: str, google_analytics_id: str = "") -> None:
    canonical = f"{site_url}/"
    sitemap_paths = ["", "contact.html", "legal.html", "privacy.html", "security.html"]
    sitemap_urls = []
    for index, path in enumerate(sitemap_paths):
        loc = canonical if not path else f"{canonical}{path}"
        priority = "1.0" if index == 0 else "0.4"
        sitemap_urls.append(
            "\n".join(
                [
                    "  <url>",
                    f"    <loc>{html_escape(loc)}</loc>",
                    f"    <lastmod>{html_escape(generated_at[:10])}</lastmod>",
                    "    <changefreq>weekly</changefreq>",
                    f"    <priority>{priority}</priority>",
                    "  </url>",
                ]
            )
        )
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
                *sitemap_urls,
                "</urlset>",
                "",
            ]
        ),
        encoding="utf-8",
    )
    expires = (datetime.now(timezone.utc) + timedelta(days=365)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    security_txt = "\n".join(
        [
            f"Contact: {site_url}/contact.html",
            f"Expires: {expires}",
            "Preferred-Languages: en",
            f"Canonical: {site_url}/.well-known/security.txt",
            "",
        ]
    )
    well_known = out / ".well-known"
    well_known.mkdir(parents=True, exist_ok=True)
    (well_known / "security.txt").write_text(security_txt, encoding="utf-8")
    (out / "security.txt").write_text(security_txt, encoding="utf-8")
    policy = csp_policy(analytics_script_url, google_analytics_id)
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
    (out / "favicon.svg").write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="12" fill="#050806"/>
  <circle cx="32" cy="32" r="22" fill="none" stroke="#42ff8c" stroke-width="3"/>
  <path d="M12 32h40M32 10c7 8 7 36 0 44M32 10c-7 8-7 36 0 44" fill="none" stroke="#72d7ff" stroke-width="2" opacity=".86"/>
  <circle cx="43" cy="21" r="4" fill="#ffd166"/>
</svg>
""",
        encoding="utf-8",
    )
    write_social_card(out)
    (out / "site.webmanifest").write_text(
        json.dumps(
            {
                "name": "Disclosure Archive",
                "short_name": "Disclosure",
                "start_url": "/",
                "display": "standalone",
                "background_color": "#050806",
                "theme_color": "#050806",
                "description": "Public UFO/UAP release archive highlights, search, and map.",
                "icons": [{"src": "/favicon.svg", "sizes": "any", "type": "image/svg+xml"}],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "humans.txt").write_text(
        "\n".join(
            [
                "Disclosure Archive",
                "Site: https://disclosurearchive.org/",
                "Purpose: public-interest index for public UFO/UAP release materials",
                "Contact: https://disclosurearchive.org/contact.html",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (out / "llms.txt").write_text(
        "\n".join(
            [
                "# Disclosure Archive",
                "",
                "Disclosure Archive is a static public index of public UFO/UAP release materials.",
                "Use it as a finding aid, not as proof of claims. Verify important details against linked government source records.",
                "",
                "Important URLs:",
                "- Site: https://disclosurearchive.org/",
                "- Data payload: https://disclosurearchive.org/data/documents.json",
                "- Contact: https://disclosurearchive.org/contact.html",
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
    google_analytics_id: str = "",
    site_url: str = "https://disclosurearchive.org",
    contact_email: str = "contact@rebuilt.cards",
) -> Dict:
    site_url = normalize_site_url(site_url)
    contact_email = normalize_contact_email(contact_email)
    google_analytics_id = normalize_google_analytics_id(google_analytics_id)
    conn = connect(db)
    documents = export_documents(conn)
    featured = featured_documents(documents)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = {
        "schema": "disclosurearchive.public_site.v1",
        "generated_at": generated_at,
        "document_count": len(documents),
        "release_groups": RELEASE_GROUPS,
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
        .replace("<!-- SECURITY_META -->", security_meta(analytics_script_url, google_analytics_id))
        .replace("<!-- STRUCTURED_DATA -->", structured_data(site_url, len(documents), featured))
        .replace("<!-- ANALYTICS_SNIPPET -->", analytics_markup(analytics_domain, analytics_script_url, google_analytics_id))
        .replace("<!-- SITE_FOOTER -->", site_footer(generated_at))
    )
    (out / "index.html").write_text(html, encoding="utf-8")
    write_info_pages(out, site_url, analytics_script_url, contact_email, google_analytics_id)
    write_crawler_and_security_files(out, site_url, generated_at, analytics_script_url, google_analytics_id)
    return {
        "out": str(out),
        "documents": len(documents),
        "analytics": "enabled" if analytics_domain or google_analytics_id else "disabled",
        "plausible": "enabled" if analytics_domain else "disabled",
        "google_analytics": "enabled" if google_analytics_id else "disabled",
        "contact_email": contact_email,
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
    parser.add_argument("--ga-measurement-id", default=os.environ.get("DISCLOSURE_GA_MEASUREMENT_ID", ""), help="Optional Google Analytics 4 measurement/tag ID, e.g. G-XXXXXXXXXX")
    parser.add_argument("--site-url", default=os.environ.get("DISCLOSURE_SITE_URL", "https://disclosurearchive.org"), help="Canonical public HTTPS URL for SEO files")
    parser.add_argument("--contact-email", default=os.environ.get("DISCLOSURE_CONTACT_EMAIL", "contact@rebuilt.cards"), help="Public contact email opened from the generated contact page")
    args = parser.parse_args(argv)

    result = write_site(
        args.db,
        args.out,
        analytics_domain=args.analytics_domain,
        analytics_script_url=args.analytics_script_url,
        google_analytics_id=args.ga_measurement_id,
        site_url=args.site_url,
        contact_email=args.contact_email,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
