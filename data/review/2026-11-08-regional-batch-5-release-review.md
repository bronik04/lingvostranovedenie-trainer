# Independent pre-merge release review — regional batch 5

Reviewed the actual uncommitted working tree on `codex/regional-batch-5-review`, base HEAD `088dc3de926b79b6631873d3155cef6b90d56097`, against `/tmp/lingvo-batch5-embed-base` and the release-before snapshot. Read-only review of the repository; no commits, pushes, deployment or repository edits performed by this reviewer.

## Strengths

- The built site contains exactly 1045 records: all previous 1030 plus exactly the 15 IDs in `2026-11-08-regional-batch-5-release-application.json`. No previous visible ID was lost. The compiled bank exactly equals the existing `site_bank` filter applied to the full bank.
- All 16 locally accepted Russian/Chinese stems, keys, original four option IDs/texts and all 64 captions independently match the immutable accepted-proposals manifest. Therefore the published 15 retain all 60 accepted captions exactly.
- №20 (`2024-25-mun-krsk-6`) is accepted locally in its author-approved wording, has no competing glosses.json entry, and is explicitly hidden by site settings. It is absent from the compiled site's QUESTION_BANK. Review numbers 11/12/14/17 remain absent as well.
- The full bank retains exactly the same 1269 IDs. Every previous visible learner-facing stem, option/pool, answer/caption, explanation, topic, occurrence, merged ID, dossier and factRow is unchanged. The same comparison also found no learner-field changes in any unselected full-bank record.
- Previous reading and pinyin entries remain intact; every released record has its four original choices, complete required pinyin and reading links. The reading source file is byte-identical to baseline. All 1045 visible records have generated reading links.
- All prior fact-group pair protections remain. The largest group is 170 and retains the canonical `province-names-river-lake` ID. No engine, source, dependency, workflow or test changes were introduced.
- Exactly 16 embedding definitions were appended; all are now accepted locally. Only the two existing modern-history definitions add exclusions to protect their prior pools. All 40 appended dossier rows have at least two distinct official/academic quoted source entries. Existing texts/captions/source entries remain; old-row identity references and olympiad list appends are appropriate.
- After removing the generated JSON constants and replacing the generated 1030→1045 metadata counts, the HTML artifact is byte-identical in its static markup, CSS and runtime JavaScript. Thus this release does not add an execution or dependency regression surface.

## Issues

### Critical (Must Fix)

None.

### Important (Should Fix)

None.

### Minor (Nice to Have)

No new actionable defect found.

## Known limits and declined-to-judge items

- Fresh factual re-sourcing of the 15 accepted items was deliberately not repeated: the task explicitly relies on the prior independent primary-source review. This review checked preservation, source-bundle structure, embedding effects and release behavior.
- №20's historical uniqueness concern was not reopened after the author's explicit acceptance. Its publication is outside the authorized 15-item release; the explicit hiddenQuestions guard contains that scope boundary.
- Standalone dossier checking still returns exactly the two documented source-form false positives (`literature-q66`→`literature-q114`, 诗歌; `nature-q140`→`modern-china-q26`, 黄金). Independently invoking `validate_links` and `cross_leak_errors` on the final bank returns zero errors. This is a pre-editorial checker limitation, not a learner-visible defect or reason to weaken tests.
- Existing local-integration reports/manifests describe their earlier stage; the release manifest is the authority for the current +15 publication scope. Current embedding acceptance notes also append the later publication instruction.
- Live deployment, origin synchronization and final commit contents are subsequent release operations, outside this read-only review. The two unrelated untracked batch-3/4 deployment-check files must remain excluded from the release commit; the index was empty during this review.

## Verification evidence read after implementation

- `/tmp/lingvo-batch5-release-build.log`: successful build, 1269 full / 1045 visible, 224 hidden.
- `data/review/2026-11-08-regional-batch-5-release-check.json`: passed, errors [], exact +15 IDs, 60 captions, all16 locally accepted, no previous learner/pool changes, 40 source-backed rows, no unresolved new hint candidates.
- `/tmp/lingvo-batch5-release-python.log`: Ran 494 tests in 32.916s; OK.
- `/tmp/lingvo-batch5-release-node.log`: 172 tests, 172 passed, 0 failed/cancelled/skipped; 160881.670646ms.
- `data/review/2026-11-08-regional-batch-5-release-browser-check.json` and browser log: 120 card displays / 480 choices, 1280px and 375px, pinyin off/on, correct/incorrect responses; exact captions, no overflow/clipping/page errors. The saved mobile screenshot was visually inspected.
- Independent read-only comparison and validation additionally confirmed exact accepted strings, stable full-bank IDs, preserved old fields/pools/reading/pinyin/protections, correct site filtering, no final-bank direct hint errors and no broken dossier identity links.
- `git diff --check` passes.
- Independently computed built HTML SHA256: `19f1e59cd71d4afa7c296fb2257461c1d0c352a408452e1846742a2db887dcd6` (matches release-check).

## Assessment

**Ready to merge and PUBLISH 15 only: YES.**

The reviewed tree implements the authorized 1030→1045 release exactly and preserves the previous learner experience. No Critical or Important issue remains; №20 is accepted only locally and explicitly excluded from this publication. Proceed with the ordinary authorized release, excluding unrelated batch-3/4 proofs, and verify the deployed artifact against the recorded SHA256.
