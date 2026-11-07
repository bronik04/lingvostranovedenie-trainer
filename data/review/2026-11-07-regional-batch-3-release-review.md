# Independent final branch review — regional batch 3

Reviewed worktree: `/Users/bronik04/.codex/worktrees/regional-batch-3-release/lingvostranovedenie-trainer`.
Base: `b5730dfec0f33e0e9d0022a0481843e589812020`; release changes were uncommitted. Read-only review; no worktree, index, HEAD, or branch mutations and no subagents.

## Strengths

- Release content matches the approved manifest exactly: 16 accepted review numbers (1,3,5,6,7,8,9,10,12,13,15,16,17,18,19,20), 16 accepted embeds, 64 exact Chinese option strings and stable option IDs, unchanged original answer keys, exact approved Russian stems and captions. The five approved stem changes and three explanation changes are applied through editorial.json. Captions have a maximum length of 84 characters and add useful contextual knowledge. No added 市/省 suffixes change the approved toponyms.
- Direct comparison with the base bank confirms that all other records retain their question text, option pools/IDs, answers, captions and explanations. Their only changed fields are factGroup/evidence. The 32 existing dossier-question edits only add excludes, preserving previous pools while the 41 new rows supply approved variant context. Existing cell captions remain intact; new context columns contain the new captions.
- All 41 new rows carry at least two distinct official/academic source URLs with quotations. Read the saved proposal/source/feedback evidence and compared quotations with the actual cells. The minor provenance concern raised during review was resolved: region-group rows now cite their actual member regions; rg-dongbei includes the National Bureau of Statistics grouping and the correct capital sources, rather than copied Fujian-only material.
- The sensitive distinctions are implemented consistently: north–black is expressly limited to 五行; 青 is not replaced with 蓝; 三教's Christian distractor uses the broad meaning of Christianity, with Catholicism and Protestantism as branches; Port Arthur is asked as a toponym and Lüshun is described as a Dalian district; Gao Xingjian is described by language, and his row's country is France; the five-religion explanation explicitly avoids inferring a ban on other religions. No newly ambiguous answer set was found.
- Read the 63-item hint triage. All 17 newly protected caption constraints and eight direct constraints resolve to a shared current factGroup. All 26 old-content index hits have unchanged stems/options/answers/captions/explanations relative to base; the 20 same-row entries carry the canonical-row flag. Checked every old fact-group membership set: each is still entirely protected within one current group after unions. Existing protections are not silently dropped.
- Independent checks passed: `python3 scripts/dossiers.py` (exit 0, no dossier errors); programmatic exact comparison of 16 records/64 options/captions/three explanations; prior-record field comparison; prior-group preservation; all declared hint constraints; source-count/quote checks; `site_bank` reports 1269 full records and 1014 visible records, with all 16 accepted IDs and none of the four excluded IDs visible. General regional visibility remains false.

## Issues

### Critical (Must Fix)
None found.

### Important (Should Fix)
None found.

### Minor (Nice to Have)
None outstanding. The provenance cleanup identified during review has been inspected and resolved without changing approved content.

## Recommendations

Finish the already planned full Python/Node/Chrome verification and release evidence, then publish and verify the live site. Those execution steps were still being performed by the root agent during this review; this report does not claim they have completed. Preserve the exact manifest/content checks when integrating with the current master.

## Declined to judge

- Global re-audit of the older 103/1032 questions and pre-existing hint backlog: explicitly outside this release's authorized scope; reviewed actual changes and newly affected relationships instead.
- Reopening every primary webpage/PDF: source verification was already performed by the source workers and saved in the release evidence; this review checked those quotations/provenance against the changed content and did not claim an independent full external-source re-audit.
- Unchanged historical spellings/typography in the original Chinese option strings: explicitly required to remain stable; no new spelling changes were introduced.
- Unrelated UI/reading changes in the main checkout: excluded from this release; no such implementation changes appear in the reviewed branch.

## Assessment

**Ready to merge? Yes — content/review gate passed.**

The release preserves the approved 16-question experience and existing question pools, and closes the documented new hint dependencies without losing earlier group protections. No critical or important issue remains in the reviewed content/data diff; the executor must still finish and record the planned integration, full verification, deployment and live checks.

## Executor verification after integration

Preserved published reading feature from22af68f. Integrated build1269total/1014visible,492Python +172Node tests, no failures or skips;128card renders/512options at1280px and375px with both pinyin states and correct/incorrect answers passed. New hint constraints unresolved:0. Reading materials cover1014/1014. HTML hash recorded in application/check JSON. Publication follows this verified revision.
