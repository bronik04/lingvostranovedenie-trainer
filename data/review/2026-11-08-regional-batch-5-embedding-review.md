# Independent final review — regional batch 5 local embedding

Review scope: uncommitted working tree on `codex/regional-batch-5-review` against HEAD `088dc3de926b79b6631873d3155cef6b90d56097` and preserved `/tmp/lingvo-batch5-embed-base`. Read-only review; no repository edits or publication.

## Verdict

Content/data readiness: **15 accepted local embeddings plus prepared draft №20**. No additional Critical or Important defect found in the 15 applied embeddings. This verdict does not authorize publication, commit, merge, or push. The final embedding-check and complete current suites have passed; execution evidence is listed below.

## Important — acknowledged and contained

1. **№20: uniqueness remains unresolved; retain `draft` + `check.verdict: fix`.** `data/dossiers/crafts-questions.json:383` and `data/review/2026-11-08-regional-batch-5-embedding-sources.json:4225`.
   - The nephrite key is supported. RUC's academic lecture record explicitly connects ancient soft jade with ritual vessels and jade objects with protective beliefs. Independent primary-index search reconfirmed that record.
   - Okamura Hidenori's academic PDF, physical PDF p.8 / printed p.185, was independently read in the local extracted text: protective animal-shaped beads are discussed, then late-Han crystal bixie-shaped beads from Gongyi Xinhua tomb 1 are named. The contextual protective interpretation is credible; these paragraphs do **not** directly establish ritual use of crystal in strict antiquity.
   - Consequently, the evidence supports **“единственность ответа не подтверждена”**, not the stronger assertion that crystal has conclusively been proved a second correct answer to both clauses. The Qing crystal ritual object cannot settle the ancient-period clause.
   - Current draft handling preserves the author's accepted stem, all four choices/captions and key, avoids a fabricated exclusion or silent reformulation, and is appropriate. Its four temporary glosses are valid because only accepted embeddings prohibit glosses.json entries. Keep this blocker visible to the author; no automatic acceptance or withholding is recommended.

## Minor / verification limits

1. Standalone `python3 scripts/dossiers.py` returns two source-form hint errors: literature-q66→literature-q114 (`诗歌`) and nature-q140→modern-china-q26 (`黄金`). The current final bank's editorial layer removes those Chinese expressions from the former questions. A direct independent `cross_leak_errors(final_bank, loaded, groups)` returns no errors, and `validate_links` returns no errors. These are pre-editorial checker limitations, not learner-visible leaks. Do not add groups or change the matcher merely to hide them; record this distinction in final checks.
2. The largest fact group grew from 109 to 170. The union now retains canonical ID `province-names-river-lake`; this data-only correction preserves the partition and resolves the review-found hard-coded merge-test expectation without modifying tests. The union retains prior protections and mostly follows existing policy on explicit answer words/dates. The explicit Лу Ю / Лунь юй collision guard is a conservative false lexical match, not semantic identity; removing that single edge would reduce the maximum from 170 to 169. It is low-impact but should remain honestly labeled. No engine change is warranted in this content task.

## Independent structural and preservation checks

- All 16 final Russian/Chinese stems, 16 answer keys, 64 option IDs/texts, and 64 captions exactly match the accepted manifest. №6 uses the short 2025 stem; №9 uses merchants; №20 uses ritual objects/protection.
- Exactly 16 new dossier definitions: 15 accepted embeddings and one draft; no new standalone questions. Excluded original review numbers 11/12/14/17 were not reintroduced.
- Full bank retains the same 1269 IDs. Site filtering retains exactly the same 1030 visible IDs. All old visible learner-facing stems, options/pools, answers/captions, explanations, topics, occurrences and mergedIds are unchanged; all prior unselected records preserve stems/options/answers/explanations/occurrences/mergedIds.
- The only old question definitions changed are modern-history-q108 and q119, adding exclusions for newly appended rows, preserving prior option pools.
- All 40 new rows have at least two distinct official/academic quoted source entries. Captions were read in context: they add concrete information beyond each stem/answer. Existing rows, existing cell text and old source entries were neither removed nor mutated.
- Identity references connect the same named entity; materials are not falsely equated with their broader mineral class. Projections to canonical places are exact-name refs. New forms are not falsely referenced to individual literary works.
- No previous fact-group pair protection was lost. Existing refs/cells/source bundles remain intact.
- Site settings add only two hiddenQuestions guards for №3/6; earlier showRegional/showRegionalIds/showEmbeddedIn permissions remain unchanged. Both guarded records stay absent from the same 1030-question site view.
- Pinyin diff contains only six new entries: the accepted №3/9 Chinese stems and four Arabic year choices for №16. Prior entries remain unchanged; the additions have appropriate readings.
- Manifest canonical SHA256 (excluding manifestHash; UTF-8, ensure_ascii=False, sorted keys, compact separators) independently recomputed to dd2aab6c3ccd13bdfa44d4d14ff731b2a317e7f78972030fb7c28dea5fd0dffa. Raw file SHA256 is 3486a5eee5fb7c48b845145e22093db9c1531b4f0c03116432675ddf942004f3; these are intentionally different representations.
- Known accepted caveats №6 (usable ore) and №15 (constitutional incorporation in 2004) remain explicit in explanations. They were not silently rewritten.

## Execution evidence

Final evidence read after implementation:

- `data/review/2026-11-08-regional-batch-5-embedding-check.json`: status passed; errors []; exact accepted stems/options/keys/captions true; previous learner/pool changes []; 40 source-backed new rows; complete pinyin; no unresolved final-bank direct hints; same 1269 full / 1030 visible.
- `/tmp/lingvo-batch5-embed-python-complete.log`: 494 tests, OK (29.884 seconds).
- `/tmp/lingvo-batch5-embed-node-complete.log`: 172 tests, 172 pass, 0 fail, 0 skipped (164565.506 milliseconds).
- `/tmp/lingvo-batch5-embed-browser-final.log`: 128 cards / 512 options; mobile and desktop; pinyin off/on; correct/incorrect; exact captions; no clipping, overflow, or page errors. A temporary browser-only hidden-record preview tests all16 while actual built HTML retains1030 and excludes those16.
- Final application state is `local-integration-checked-15-plus-one-draft-no-publication`. Changes-only `2026-11-08-regional-batch-5-embedding.md` and CHANGELOG describe15accepted+draft20, source/checker limits,6pinyin additions, local-only status, and no publication.
- Review-found canonical group naming failure was corrected in data by retaining `province-names-river-lake`; partition/protections unchanged, tests not modified.
- Current HTML SHA256 recorded by final check: `29610bbbd57c1238fed6e49dd5551eb41c7be8d2195aec21776165e5062b0a1c`.

**No further blocking implementation issue remains. №20 is the sole unresolved content blocker, correctly contained as a draft. Final verdict: locally ready15accepted embeddings plus prepared draft20; no publication/merge authorization.**

## Sources specifically rechecked for №20

- RUC academic lecture record: https://cdgi.ruc.edu.cn/ppdt/whssxllt/dyj6/68836ff95f02400a84b1ba68d54242e4.htm
- Okamura academic paper: https://www.kurokawa-institute.or.jp/files/libs/5501/20260402135642533.pdf (local /tmp/lingvo-crystal-okamura.txt, paragraph at lines 313–335).
- NMNS quartz/crystal primary PDF independently reconfirmed by primary-index search: https://libknowledge.nmns.edu.tw/nmns/upload/lib/000001459/209000c/191-5.pdf

## Final report clarity note

Nonblocking copy suggestion sent to coordinator: in the changes-only report, replace Russian «биси» with explicit «мифического зверя 辟邪», and show №20 bank ID `2024-25-mun-krsk-6` directly beside dossier definition `crafts/crafts-q142`. No further tests or review loop are required for these report-only clarifications.
