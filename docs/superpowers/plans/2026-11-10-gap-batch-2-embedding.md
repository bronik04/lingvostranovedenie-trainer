# Accepted gap batch 2: local dossier embedding

> **For agentic workers:** Execute this plan inline using executing-plans. The user has approved all 17 items and ordered implementation; do not ask for another approval.

**Goal:** Embed the accepted 17 questions from the revised 2026-11-10 manifest, verify 68 captions and mutual hints, and report only before → after changes plus separate problems. No publication.

**Spec:** Latest user instructions in this chat; exact accepted text snapshot in `.superpowers/sdd/2026-11-10-gap-batch-2-embedding/baseline/data/review/2026-11-10-gap-batch-2-revised-proposals.json`.

**Architecture:** Existing authored additions + dossier embeds. Stable `addition-gap2-NN` IDs preserve all accepted option IDs, order, texts and keys. Dossier cells supply all captions. New context columns limit existing tables to the accepted 4 options. The 17 new IDs are withheld through hiddenQuestions.

**Global constraints:** Do not modify sources, old questions, options or keys; preserve other working tree drafts and QUESTION_RESERVE. Do not revive rejected questions. Do not push, deploy, merge or publish. Keep accepted stems unchanged. Captions and explanations may be corrected without changing meaning. №19 belongs to language/phraseology and must not be silently released in the main country-studies pool.

### Task 1: Freeze input and integrate accepted facts
- [x] Snapshot baseline hashes, complete bank, visible IDs and accepted manifest.
- [x] Review independent mapping, caption evidence and hint audits.
- [x] Add 17 authored records, 17 dossier embeds and their sourced cells, preserving exact 4-option pools. Fix only captions/explanations as necessary.
- [x] Add a temporary publication hold for all 17 IDs; update manifest acceptance state.
Expected: 17 new records; no old question text, options, keys or caption changes.

### Task 2: Resolve mutual hints
- [x] Add factRow links / fact groups for real direct and word hints, preserving substantive captions.
- [x] Inspect generated caption leak report and new pairs manually, distinguish false positives.
Expected: no unresolved real hints involving these 17; no new unrelated question edits.

### Task 3: Verify and report
- [x] Run dossier validation, full Python/Node tests and local build. Verify exact preservation against baseline; visible question IDs remain unchanged.
- [x] Obtain one fresh-context read-only final review, address substantive findings.
- [x] Save report and machine checks; final response only actual before → after changes and separate problems. Do not publish.
Expected: all 17 embedded locally, evidence recorded, site release unchanged.

## Review focus
Exact manifest identity; 17/68 counts; accepted question and key preservation; no rejected items returned; source quotations honestly support their claims; correct captions add knowledge; all new pools exactly 4; old bank pools unchanged; mutual hints both directions including answer.gloss; №19 phraseology placement; publication guard; user drafts untouched.
