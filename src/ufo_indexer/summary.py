from __future__ import annotations

import re
from typing import Dict, List, Tuple

from .common import clean
from .evidence_pack import source_label
from .search import snippet


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
    (re.compile(r"â€œ|â€�|â€ś|â€ť|тАЬ|тАЭ"), '"'),
    (re.compile(r"â€˜|â€™|тАЩ|тАШ"), "'"),
    (re.compile(r"â€[\"“”]?|тА[\\w]*"), " "),
    (re.compile(r"┬й|┬в|┬"), " "),
    (re.compile(r"[Хх]"), "X"),
    (re.compile(r"\bU\s*F\s*O\b", re.IGNORECASE), "UFO"),
    (re.compile(r"\bU\s*A\s*P\b", re.IGNORECASE), "UAP"),
    (re.compile(r"\bA\s*F\s*B\b", re.IGNORECASE), "AFB"),
    (re.compile(r"\bF\s*B\s*I\b", re.IGNORECASE), "FBI"),
    (re.compile(r"\bD\s*O\s*D\b", re.IGNORECASE), "DOD"),
    (re.compile(r"\bdnvolved\b", re.IGNORECASE), "involved"),
    (re.compile(r"\berater\b", re.IGNORECASE), "crater"),
    (re.compile(r"\bfron\b", re.IGNORECASE), "from"),
    (re.compile(r"\bprom\b", re.IGNORECASE), "from"),
    (re.compile(r"\bmowledge\b", re.IGNORECASE), "knowledge"),
    (re.compile(r"\bmst\b", re.IGNORECASE), "must"),
    (re.compile(r"\bpreviosuly\b", re.IGNORECASE), "previously"),
    (re.compile(r"\bsmali\b", re.IGNORECASE), "small"),
    (re.compile(r"\bsm\.?\s*il\b", re.IGNORECASE), "small"),
    (re.compile(r"\bsourees\b", re.IGNORECASE), "sources"),
    (re.compile(r"\bstresks\b", re.IGNORECASE), "streaks"),
    (re.compile(r"\bcontimed\b", re.IGNORECASE), "continued"),
    (re.compile(r"\berews\b", re.IGNORECASE), "crews"),
    (re.compile(r"\bfly:\s*formation\b", re.IGNORECASE), "fly in formation"),
    (re.compile(r"\bsterboard\b", re.IGNORECASE), "starboard"),
    (re.compile(r"\bsquacron\b", re.IGNORECASE), "squadron"),
    (re.compile(r"\beylinder\b", re.IGNORECASE), "cylinder"),
    (re.compile(r"\bsheped\b", re.IGNORECASE), "shaped"),
    (re.compile(r"\bobjsct\b", re.IGNORECASE), "object"),
    (re.compile(r"\bobservea\b", re.IGNORECASE), "observed"),
    (re.compile(r"\birv\b", re.IGNORECASE), "air"),
    (re.compile(r"\bnusber\b", re.IGNORECASE), "number"),
    (re.compile(r"\bpignter\b", re.IGNORECASE), "fighter"),
    (re.compile(r"\bsousdron\b", re.IGNORECASE), "squadron"),
    (re.compile(r"\bsomthing\b", re.IGNORECASE), "something"),
    (re.compile(r"\bbehing\b", re.IGNORECASE), "behind"),
    (re.compile(r"\bplightly\b", re.IGNORECASE), "slightly"),
    (re.compile(r"\bvirst\b", re.IGNORECASE), "first"),
]

COMMON_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "by",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "his",
    "in",
    "is",
    "it",
    "not",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "were",
    "with",
}

OCR_FILLER_WORDS = {
    "ae",
    "aee",
    "eee",
    "ee",
    "oe",
    "oo",
    "ooo",
    "ii",
    "iii",
    "lll",
    "se",
    "sss",
    "te",
}

LOW_VALUE_PATTERNS = [
    re.compile(r"\b(?:click|download|attachment|thumbnail|preview)\b", re.IGNORECASE),
    re.compile(r"\b(?:privacy|terms of use|copyright|all rights reserved)\b", re.IGNORECASE),
    re.compile(r"\b(?:page intentionally left blank|this page left blank)\b", re.IGNORECASE),
    re.compile(r"https?://|www\.|@"),
    re.compile(r"\b(?:file|document|record)\s+(?:number|id|identifier)\b", re.IGNORECASE),
    re.compile(r"\bstrike\s+out\s+methods?\b", re.IGNORECASE),
    re.compile(r"\battached\s+are\s+copies\b", re.IGNORECASE),
]

OCR_DAMAGED_WORDS = {
    "baprdutomary",
    "beg",
    "e390",
    "gaat",
    "hradquare",
    "inre",
    "ite",
    "plightly",
    "prov",
    "sbtauked",
    "urs",
}

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
    "cylindrical",
    "foo",
    "foofighter",
    "foofighters",
    "unknown",
    "formation",
    "phenomena",
    "rocket",
    "rockets",
    "tumbling",
}


def readable_text(text: str) -> str:
    text = clean(text)
    text = re.sub(r"-\s+", "", text)
    for pattern, replacement in OCR_FIXES:
        text = pattern.sub(replacement, text)
    text = re.sub(r"[\u2500-\u259f]+", " ", text)
    text = re.sub(r"[^\x09\x0a\x0d\x20-\x7e]", " ", text)
    text = re.sub(r"\s*[|=~]\s*", " ", text)
    text = re.sub(r"[_~`|{}\[\]<>]{2,}", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:?!)])", r"\1", text)
    text = re.sub(r"([(])\s+", r"\1", text)
    text = re.sub(r"\.\s*,", ",", text)
    text = re.sub(r"\bbut\.\s+", "but ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+[a-z]\.$", ".", text)
    text = re.sub(r'["\']?,\s*\d+\.$', ".", text)
    text = re.sub(r"(?<=[a-z])(?=[A-Z][a-z])", " ", text)
    return clean(text)


def clean_sentence_text(text: str) -> str:
    text = clean(text)
    for pattern, replacement in OCR_FIXES:
        text = pattern.sub(replacement, text)
    text = re.sub(r"\s+[a-z]\.?$", ".", text)
    text = re.sub(r'["\']?,\s*\d+\.?$', ".", text)
    text = re.sub(r"\s+([,.;:?!)])", r"\1", text)
    return clean(text)


def sentence_quality(sentence: str) -> float:
    if not sentence:
        return 0.0
    chars = len(sentence)
    letters = sum(1 for char in sentence if char.isalpha())
    if chars < 35 or chars > 360:
        return 0.1
    tokens = re.findall(r"[A-Za-z0-9]+", sentence)
    words = [token.lower() for token in tokens if re.search(r"[A-Za-z]", token)]
    if len(words) < 5:
        return 0.2
    damaged_ratio = ocr_damage_score(sentence)
    punctuation_noise = sum(1 for char in sentence if char in "_~`|{}[]<>")
    symbol_noise = sum(1 for char in sentence if not char.isalnum() and not char.isspace() and char not in ".,;:?!'\"()/-%")
    short_ratio = sum(1 for word in words if len(word) <= 2) / max(len(words), 1)
    common_ratio = sum(1 for word in words if word in COMMON_WORDS) / max(len(words), 1)
    filler_ratio = sum(1 for word in words if word in OCR_FILLER_WORDS) / max(len(words), 1)
    long_garble_ratio = sum(1 for word in words if len(word) > 24) / max(len(words), 1)
    vowelless_ratio = sum(
        1
        for word in words
        if len(word) >= 4 and not re.search(r"[aeiouy]", word) and not word.isupper()
    ) / max(len(words), 1)
    repeated_noise = len(re.findall(r"\b(?:[a-z]{1,2}\s+){5,}[a-z]{1,2}\b", sentence.lower()))
    quality = letters / max(chars, 1)
    quality -= punctuation_noise / max(chars, 1)
    quality -= symbol_noise / max(chars, 1)
    quality -= max(0.0, short_ratio - 0.42) * 1.1
    quality -= max(0.0, 0.1 - common_ratio) * 2.0
    quality -= filler_ratio * 1.6
    quality -= long_garble_ratio * 4.0
    quality -= vowelless_ratio * 0.8
    quality -= repeated_noise * 0.25
    quality -= damaged_ratio * 2.7
    if common_ratio < 0.12 and short_ratio > 0.34:
        quality -= 0.22
    if re.search(r"\b(?:e{3,}|a{3,}|o{3,}|i{3,})\b", sentence.lower()):
        quality -= 0.2
    if len(set(words)) < max(4, len(words) * 0.45):
        quality -= 0.15
    if sum(1 for char in sentence if char.isdigit()) / max(chars, 1) > 0.24:
        quality -= 0.2
    if any(pattern.search(sentence) for pattern in LOW_VALUE_PATTERNS):
        quality -= 0.25
    return quality


def ocr_damage_score(sentence: str) -> float:
    tokens = re.findall(r"[A-Za-z0-9]+", sentence)
    words = [token.lower() for token in tokens if re.search(r"[A-Za-z]", token)]
    if not words:
        return 1.0
    short_ratio = sum(1 for word in words if len(word) <= 2) / len(words)
    damaged_hits = sum(1 for word in words if word in OCR_DAMAGED_WORDS)
    noisy_token_hits = 0
    for word in words:
        if len(word) >= 4 and re.search(r"(?:[bcdfghjklmnpqrstvwxz]{5,}|[aeiou]{4,})", word):
            noisy_token_hits += 1
        elif len(word) >= 7 and not re.search(r"[aeiouy]", word):
            noisy_token_hits += 1
    upper_tokens = [token for token in tokens if token.isupper() and len(token) <= 3]
    uppercase_fragment_ratio = len(upper_tokens) / max(len(tokens), 1)
    score = damaged_hits / len(words)
    score += max(0.0, short_ratio - 0.34) * 0.9
    score += max(0.0, uppercase_fragment_ratio - 0.22) * 0.7
    score += noisy_token_hits / len(words)
    if re.search(r"\b[A-Z]\s+[A-Z]{2,}\s+[a-z]{3,}\s+[A-Z][a-z]{2,}\s+[a-z]{2,}\s+[A-Z]{2,}\b", sentence):
        score += 0.3
    if re.search(r"\b[a-z]{1,3}\d{2,}\b|\b\d{2,}[a-z]{1,3}\b", sentence.lower()):
        score += 0.18
    return score


def ocr_sentence_is_usable(sentence: str) -> bool:
    if any(pattern.search(sentence) for pattern in LOW_VALUE_PATTERNS):
        return False
    quality = sentence_quality(sentence)
    damage = ocr_damage_score(sentence)
    if damage >= 0.24:
        return False
    if quality < 0.8:
        return False
    return True


def split_sentences(text: str) -> List[str]:
    text = re.sub(r"[-=+.]{3,}", ". ", text)
    candidates = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    if len(candidates) == 1:
        candidates = re.split(r"\s{2,}|;\s+", text)
    out = []
    for item in candidates:
        item = clean_sentence_text(item)
        if len(item) > 320:
            item = item[:320].rsplit(" ", 1)[0] + "."
        if sentence_quality(item) >= 0.56:
            out.append(item)
    return out


def query_terms(query: str) -> set[str]:
    return {term.lower() for term in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", query) if term.lower() not in STOPWORDS}


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


def sentence_ref(row) -> Dict:
    return {
        "chunk_id": row["chunk_id"],
        "source_kind": row["source_kind"],
        "source_label": source_label(row["source_kind"]),
        "page_number": row["page_number"],
        "chunk_index": row["chunk_index"],
        "label": f"{source_label(row['source_kind'])}, {'page ' + str(row['page_number']) if row['page_number'] else 'no page'}, chunk {row['chunk_id']}",
    }


def sentence_line(row, sentence: str) -> Dict:
    return {
        "text": sentence,
        "chunk_id": row["chunk_id"],
        "source_kind": row["source_kind"],
        "source_label": source_label(row["source_kind"]),
        "page_number": row["page_number"],
        "chunk_index": row["chunk_index"],
        "label": f"{sentence} ({source_label(row['source_kind'])}, {'page ' + str(row['page_number']) if row['page_number'] else 'no page'})",
    }


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
        if any(pattern.search(sentence) for pattern in LOW_VALUE_PATTERNS):
            continue
        if row["source_kind"] == "ocr_text" and not ocr_sentence_is_usable(sentence):
            continue
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
            if row["source_kind"] == "ocr_text" and not ocr_sentence_is_usable(sentence):
                continue
            if row["source_kind"] == "pdf_text":
                quality += 0.2
            elif row["source_kind"] == "ocr_text":
                quality += 0.05
            if row["page_number"]:
                quality += 0.1
            if sentence_has_uap_terms(sentence):
                quality += 0.45
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
        overview = f"{overview} {humanize_sentence(description)}"

    top_items = unique_sentence_items(sentences, 5)
    uap_items = unique_sentence_items(
        [(score + 0.8, row, sentence) for score, row, sentence in sentences if sentence_has_uap_terms(sentence)],
        4,
    )
    detail_items = unique_sentence_items(chronological_sentences, 10, chronological=True)

    quick_summary = overview

    mysterious_uap_element = [sentence_line(row, sentence) for row, sentence in uap_items]
    if not mysterious_uap_element:
        mysterious_uap_element = [
            {
                "text": "No clear anomaly-focused passage was found in the indexed text for this source; review the PDF/media manually if the title or metadata suggests a UAP connection.",
                "chunk_id": "",
                "source_kind": "",
                "source_label": "",
                "page_number": None,
                "chunk_index": None,
                "label": "No clear anomaly-focused passage was found in the indexed text for this source; review the PDF/media manually if the title or metadata suggests a UAP connection.",
            }
        ]

    detailed_contents = [sentence_line(row, sentence) for row, sentence in detail_items]
    if not detailed_contents:
        detailed_contents = [
            {
                "text": "The indexed PDF/OCR/caption text did not contain enough clean sentences for a reliable extractive summary. Use the government source link for manual review.",
                "chunk_id": "",
                "source_kind": "",
                "source_label": "",
                "page_number": None,
                "chunk_index": None,
                "label": "The indexed PDF/OCR/caption text did not contain enough clean sentences for a reliable extractive summary. Use the government source link for manual review.",
            }
        ]

    references = []
    seen_refs = set()
    for row, sentence in [*top_items, *uap_items, *detail_items]:
        ref = sentence_ref(row)
        key = (ref["chunk_id"], ref["page_number"], ref["source_kind"])
        if key in seen_refs:
            continue
        seen_refs.add(key)
        ref["snippet"] = snippet(humanize_sentence(readable_text(sentence)), max_chars=240)
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
