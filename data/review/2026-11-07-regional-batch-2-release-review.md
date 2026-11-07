Review snapshot: completed before the coordinator updated three outdated test expectations; the student-facing data reviewed below remains unchanged.

# Final independent review — regional batch 2

Reviewed the working tree against `59ac848377137689453e84e90aaea3464ae26ed1`; HEAD was still the base. Read CLAUDE.md, the release plan, tracked dossier/question/editorial/site/fact-group changes, and the untracked release, application, evidence, hint-triage, hints, check and prior review records. This review concerns the accepted 19 questions, shared-data effects, and release readiness; the archived 20-question proposal is not the final display specification.

## Strengths

- All 19 final cards are consistent with the accepted outcome. The four stem clarifications, four city labels without 市, 1912–1949, Chinese genre terms and unchanged №19 stem are present. №11 is permanently blocked through hiddenQuestions.
- Independently ran the exact 76-option/caption verifier: 1269 canonical records, 998 visible, exactly 19 additions, no previous visible record lost, and 19 dossier embeddings. Independently compared the full bank to the base: every record ID, answer option ID and original numbered option ID is preserved.
- Read all 27 caption compactions against their approved originals. Names, chronology, examples and substantive distinctions remain intact. Compact noun phrases in the Khachaturyan caption are understandable educational shorthand; no factual or answer-selection defect warrants a revision. Nothing substantial was removed to suppress a hint.
- Read the changed and newly introduced row content and quoted-source evidence. All 40 new rows have at least two official/academic quoted sources. Collector notes disclose indexed-page fallbacks, the corrected official source title, and limitations of historical railway classifications. The shown captions avoid introducing unstable train-prefix rules. Supporting excerpts and notes adequately explain the accepted facts.
- Shared changes were considered beyond the 19 cards: the 21 affected prior records and seven expanded author pools do not acquire a second correct answer from 李颀 or 王绩. Short-name 韩非 and original traditional 王維/王績 are preserved intentionally. Russian name aliases remain semantically sound, and the qualified «жанры цюйи» avoids the documented false stemming match without changing the shown name.
- Reviewed the 32 candidate decisions against the captions and target questions. The 19 protected pairs are actually co-members of their declared groups. All baseline group membership is preserved, including absorbed groups. The remaining 12 candidates are canonical-row repetitions permitted by the existing author policy; the 13th initial repetition is now incidentally grouped. Cross-text audit reports no errors. No unrelated baseline candidate is classified as new.
- No source documents, validator, UI or test implementation changed. Changes use the existing editorial, embedding, visibility and fact-group layers.

## Critical issues

None.

## Important issues

None.

## Minor issues

None requiring action.

## Declined to judge

[]

## Verification and assessment

Read-only checks performed here: exact 19/76 release verifier; full-bank ID/key preservation against base; preservation of every prior fact group; actual membership of all 19 protected caption pairs; minimum source/quote/authority checks for all 40 new dossier rows; inspection of final zero-cross-error hint report. Full Python/Node suites are being run by the release coordinator and were intentionally not duplicated. External source retrieval was reviewed through supplied excerpts and collector evidence, not exhaustively repeated.

**Ready to merge: YES.** No content or implementation blocker found. Publication remains contingent on the coordinator's already-required full test completion and deployment verification; this review does not claim a deployment has occurred.

## Coordinator follow-up: test expectations

The first full Python suite exposed three stale expectations: a newly approved question was still listed as hidden; Shenzhen captions were compared across geography and industry columns as one context; merged fact-group names were asserted instead of the preserved Cao Cao/Manchu relationships. These tests now check the current author decision, table/column-specific caption context, and actual related-question group membership. The three targeted cases were observed failing and then passing. No production validator or UI code changed. Full-suite results are recorded in the final check file.
