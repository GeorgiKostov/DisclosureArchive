PYTHON ?= python3
SOURCE_ROOT ?= /Users/georgikostov/Desktop/ufo_war_release
DB ?= indexes/uap_release.sqlite
EXPORT ?= /Volumes/DisclosureTransfer/DisclosureArchivePackage
OCR_WORKERS ?= 1
TESSERACT_BIN ?= tesseract
REVIEW_REASONS ?= zero_text_pages low_avg_chars
OCR_DPI ?= 300
OCR_PSM ?= 11

.PHONY: setup index rebuild classify ocr ocr-classified ocr-status ocr-retry ocr-one eval-search evidence-pack web search-vector search-hybrid stats export-site export-package verify-package

setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && python -m pip install --upgrade pip
	. .venv/bin/activate && pip install -e .

index:
	. .venv/bin/activate && python -m ufo_indexer.index --source-root "$(SOURCE_ROOT)" --db "$(DB)"

rebuild:
	. .venv/bin/activate && python -m ufo_indexer.index --source-root "$(SOURCE_ROOT)" --db "$(DB)" --rebuild

classify:
	. .venv/bin/activate && python -m ufo_indexer.classify --source-root "$(SOURCE_ROOT)" --out reports/pdf_classification.json

ocr:
	. .venv/bin/activate && python -m ufo_indexer.ocr --source-root "$(SOURCE_ROOT)" --workers "$(OCR_WORKERS)" --tesseract-bin "$(TESSERACT_BIN)"

ocr-classified:
	. .venv/bin/activate && python -m ufo_indexer.ocr --source-root "$(SOURCE_ROOT)" --from-classification reports/pdf_classification.json --classes scan_only low_text mixed --workers "$(OCR_WORKERS)" --tesseract-bin "$(TESSERACT_BIN)"

ocr-status:
	. .venv/bin/activate && python -m ufo_indexer.ocr_status --source-root "$(SOURCE_ROOT)" --classification reports/pdf_classification.json --out reports/ocr_status.json

ocr-retry:
	. .venv/bin/activate && python -m ufo_indexer.ocr --source-root "$(SOURCE_ROOT)" --from-status reports/ocr_status.json --review-reasons $(REVIEW_REASONS) --workers "$(OCR_WORKERS)" --tesseract-bin "$(TESSERACT_BIN)" --dpi "$(OCR_DPI)" --psm "$(OCR_PSM)"

ocr-one:
	. .venv/bin/activate && python -m ufo_indexer.ocr --source-root "$(SOURCE_ROOT)" --pdf "$(PDF)" --tesseract-bin "$(TESSERACT_BIN)"

eval-search:
	. .venv/bin/activate && python -m ufo_indexer.eval_search --db "$(DB)" --queries eval/retrieval_queries.json --out reports/retrieval_eval.json

evidence-pack:
	. .venv/bin/activate && python -m ufo_indexer.evidence_pack --db "$(DB)" --q "$(Q)" --mode hybrid --out reports/evidence_pack.json

web:
	. .venv/bin/activate && python -m ufo_indexer.web --db "$(DB)" --host 127.0.0.1 --port 8765

search-hybrid:
	. .venv/bin/activate && python -m ufo_indexer.search --db "$(DB)" --mode hybrid --q "$(Q)"

search-vector:
	. .venv/bin/activate && python -m ufo_indexer.search --db "$(DB)" --mode vector --q "$(Q)"

stats:
	. .venv/bin/activate && python -c 'import sqlite3; conn=sqlite3.connect("$(DB)"); [print(t, conn.execute(f"select count(*) from {t}").fetchone()[0]) for t in ["documents","assets","chunks","embeddings"]]'

export-site:
	. .venv/bin/activate && python -m ufo_indexer.export_site --db "$(DB)" --out public_site

export-package:
	EXPORT="$(EXPORT)" SOURCE_ROOT="$(SOURCE_ROOT)" DB="$(DB)" ./scripts/export_transfer_package.sh

verify-package:
	./scripts/verify_transfer_package.sh "$(EXPORT)"
