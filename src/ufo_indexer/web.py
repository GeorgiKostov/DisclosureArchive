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
      display: grid;
      grid-template-columns: minmax(0, 1fr) 340px;
      gap: 18px;
      align-items: start;
    }
    .summary, .side, .result, .empty {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .summary {
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
      padding: 15px;
      margin-bottom: 12px;
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
      .grid { grid-template-columns: 1fr; }
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
        <option value="metadata">Metadata</option>
        <option value="pdf_text">Native PDF text</option>
        <option value="ocr_text">OCR text</option>
        <option value="caption">Captions</option>
        <option value="video_metadata">Video metadata</option>
      </select>
      <select id="limit" aria-label="Result limit">
        <option value="5">5 results</option>
        <option value="8" selected>8 results</option>
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
      <aside class="side">
        <h2>Dig Deeper</h2>
        <div class="suggestions" id="suggestions"></div>
        <div class="pack-actions">
          <button type="button" id="packButton">Build Evidence Pack</button>
          <textarea id="packPreview" readonly placeholder="Evidence-pack preview"></textarea>
        </div>
      </aside>
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
      if (!results.length) {
        $("results").innerHTML = `<div class="empty">No results for this search.</div>`;
        return;
      }
      $("results").innerHTML = results.map((item) => {
        const page = item.page_number ? `page ${item.page_number}` : "no page";
        const path = item.local_path ? `
          <div class="path">
            ${esc(item.local_path)}
            <div style="margin-top:8px">
              <a href="${fileUrl(item.local_path)}" target="_blank" rel="noopener">Open source</a>
            </div>
          </div>
        ` : "";
        return `
          <article class="result">
            <div class="result-head">
              <h3>${item.rank}. ${esc(item.title)}</h3>
              <div class="score">${Number(item.score).toFixed(4)}</div>
            </div>
            <div class="meta">
              <span class="${sourceClass(item.source_kind)}">${esc(item.source_label)}</span>
              <span class="chip">${esc(item.agency || "unknown agency")}</span>
              <span class="chip">${esc(item.incident_date || "unknown date")}</span>
              <span class="chip">${esc(item.incident_location || "unknown location")}</span>
              <span class="chip">${esc(page)}</span>
              <span class="chip">${esc(item.chunk_id)}</span>
            </div>
            <p class="snippet">${esc(item.snippet)}</p>
            ${path}
          </article>
        `;
      }).join("");
    }

    function renderSuggestions(suggestions) {
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
      $("packPreview").value = "";
      try {
        const payload = await api("/api/search", {
          q,
          mode: state.mode,
          limit: $("limit").value,
          source_kind: $("sourceKind").value
        });
        state.lastResults = payload.results;
        renderSummary(payload.summary);
        renderResults(payload.results);
        renderSuggestions(payload.suggestions);
        $("status").textContent = `${payload.results.length} results in ${payload.elapsed_ms} ms`;
      } catch (error) {
        $("status").textContent = `Search failed: ${error.message}`;
      }
    }

    async function buildPack() {
      const q = $("query").value.trim();
      if (!q) return;
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
    $("limit").addEventListener("change", runSearch);
    $("packButton").addEventListener("click", buildPack);

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


def result_item(score: float, row, rank: int) -> Dict:
    metadata = row_metadata(row)
    text = clean(row["text"])
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
        "source_url": clean(metadata.get("source_url")),
        "snippet": snippet(text, max_chars=700),
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


def filtered_results(
    conn,
    *,
    query: str,
    mode: str,
    model: str,
    limit: int,
    source_kind: str,
) -> List[Dict]:
    search_limit = limit * 5 if source_kind else limit
    rows = run_search(conn, query, mode, model, search_limit)
    items = []
    for score, row in rows:
        if source_kind and row["source_kind"] != source_kind:
            continue
        items.append(result_item(score, row, len(items) + 1))
        if len(items) >= limit:
            break
    return items


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
        if source_kind not in {"", "metadata", "pdf_text", "ocr_text", "caption", "video_metadata"}:
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
            "results": results,
        }
        self.send_json(payload)

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
