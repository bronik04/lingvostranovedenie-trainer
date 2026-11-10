# Final read-only review

Critical: none found.

## Important

**Rechecked: I1 addressed.** The mismatched category quote and local shoreline metaphor are gone. The coastal row now has3 substantive official entries; the Yangtze row has2. New stored quotations explicitly name their projects. The Ministry of Finance full page was independently reopened and confirms its quote; the forestry2012 quotation was independently confirmed in indexed primary results (direct open timed out).

- **I1 (original finding, now closed) — source quotations for forest-coastal and forest-yangtze do not support those rows.** In `data/dossiers/nature.json`, their first source stores only `太行山绿化`, the name of the neighboring Taihang project. This cannot count as a supporting quotation for the coastal or Yangtze project. The second Yangtze quote is the title of an article about 163 km of Yueyang shoreline greening; the live page confirms its local scope. Replace the mismatched quotations with verified relevant category or substantive project text. Accepted questions/options/keys should remain intact.

## Publication routing

- **R1 — №19 has no separate language runtime.** It is stored locally in literature/phraseologytypes and safely hidden with an explicit hold. Its generic definition MCQ does not fit the current chengyu schema. Route before any later release; do not describe a separate language pool as implemented.

## Pre-existing problems

- `python3 scripts/dossiers.py` exits 1 on old pairs `literature-q66 → literature-q114: 诗歌` and `nature-q140 → modern-china-q26: 黄金`. Independent in-memory checking of the frozen baseline returns the exact same two errors. These are not integration regressions. Parent subsequently protected both stable embedded bank IDs via the existing word-hint group; independent final in-memory `check_dossiers` now returns `[]` (zero fatal errors).

## Minor

- №4 exhibition gloss remains a full sentence without a «Название — факт» split. Content is useful, but format is inconsistent.

## Verified

- Exact 17 new records / 68 captions; accepted stems/questionZh/option IDs/order/text/keys preserved. No rejected IDs16/18/20 returned.
- No old IDs removed and no old text, options, pools, keys or captions changed. All old authored records exact preserved. Changes to old bank records are only evidence/factGroup metadata.
- One accepted embed per new record, all new pools exactly4; mapped cell Chinese text agrees.
- All17 hidden; all old hidden entries and other site settings unchanged; visible1108 IDs unchanged; HEAD remains baseline.
- All25 documented direct/word hint pairs protected in actual groups. Additional colour/Xinjiang protections present. Residual typhoon→Pacific-ocean generated candidate is correctly documented as a semantic false positive.
- Baseline hash sweep found no mutations to user drafts outside intended accepted-manifest state; QUESTION_RESERVE and CHANGELOG remain baseline-identical.

## Declined to judge

- Full test/build rerun (parent is running them).
- Independent fresh opening of every source URL; all stored quotations and audit matrices were inspected, with live spot checks on the forest issue.
- Unrelated earlier drafts and release/deployment infrastructure.
