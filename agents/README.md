# Agent Architecture

DisclosureArchive uses a small role map so future sessions can quickly recover context without rereading every file.

| File | Role |
| --- | --- |
| `agents/architect.md` | Owns routing, integration, task state, and final decisions. |
| `agents/developer.md` | Owns indexer/OCR/search code and reproducible commands. |
| `agents/researcher.md` | Owns evidence summaries, citations, provenance, and case clustering. |
| `agents/archivist.md` | Owns raw-data organization, transfer packages, file counts, checksums, and portability. |

## Source-doc map

- Product/project purpose: `project/bible.md`
- Non-negotiable constraints: `project/constraints.md`
- Decisions already made: `project/decisions.md`
- Active work: `tasks/todo.md`
- Completed work: `tasks/done.md`
- Future work: `tasks/backlog.md`
- Lessons from prior sessions: `tasks/lessons.md`
- Session continuity: `memory/project-disclosurearchive.md`

## Routing

- Code, DB schema, OCR, embedding, and CLI changes go through Developer.
- Evidence interpretation, case summaries, and source comparisons go through Researcher.
- Transfer, packaging, raw archive layout, and machine sync go through Archivist.
- Cross-cutting changes, task updates, and release readiness go through Architect.

