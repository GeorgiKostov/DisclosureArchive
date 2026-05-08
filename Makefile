PYTHON ?= python3
SOURCE_ROOT ?= /Users/georgikostov/Desktop/ufo_war_release
DB ?= indexes/uap_release.sqlite

.PHONY: setup index rebuild search-vector search-hybrid stats

setup:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && python -m pip install --upgrade pip
	. .venv/bin/activate && pip install -e .

index:
	. .venv/bin/activate && python -m ufo_indexer.index --source-root "$(SOURCE_ROOT)" --db "$(DB)"

rebuild:
	. .venv/bin/activate && python -m ufo_indexer.index --source-root "$(SOURCE_ROOT)" --db "$(DB)" --rebuild

search-hybrid:
	. .venv/bin/activate && python -m ufo_indexer.search --db "$(DB)" --mode hybrid --q "$(Q)"

search-vector:
	. .venv/bin/activate && python -m ufo_indexer.search --db "$(DB)" --mode vector --q "$(Q)"

stats:
	. .venv/bin/activate && python -c 'import sqlite3; conn=sqlite3.connect("$(DB)"); [print(t, conn.execute(f"select count(*) from {t}").fetchone()[0]) for t in ["documents","assets","chunks","embeddings"]]'
