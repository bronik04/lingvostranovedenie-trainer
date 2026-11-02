# Comment Dialog and Results Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan inline. Steps use checkbox syntax for tracking.

**Goal:** Implement the approved comment dialog and full return buttons after a round.

**Architecture:** Keep the native dialog, existing storage and report format. Separate its scrollable body from the header and footer; switch list/editor actions together. Bound the dialog to the visual viewport for mobile keyboard use.

**Tech Stack:** Static HTML/CSS, vanilla JavaScript, Playwright/Node tests, Python HTML builder.

**Spec:** `docs/superpowers/specs/2026-11-02-comment-dialog-design.md`

## Global Constraints

- Preserve autosave, question snapshots, progress, keyboard Escape, both themes and existing fonts.
- Do not change `src/ink/` or unrelated user files.
- Keep confirmation accessible at 320px and after visible viewport reduction.
- Independent review must precede publication to `master`.

## Review Focus

- Long questions, expanded options and large comments must scroll without losing confirmation.
- Mobile visual viewport resizing/panning must leave the footer reachable.
- Missing/corrupt storage must not display a false saved state; export remains reachable via the list.
- Removal from another tab must not resurrect the entry on confirmation.
- Recall without options, Chengyu, keyboard focus and Escape must preserve round state.

### Task 1: Approved results and comment flow

**Files:** `src/template.html`, `src/quiz.css`, `src/review.ui.js`, results rendering in `src/quiz.ui.js` and `src/chengyu.ui.js`, `test/ui.test.mjs`, generated `dist/lingvostranovedenie-trainer.html`.

**Interfaces:** Preserve existing review/report IDs and storage schema. Add `reviewConfirm`, `reviewDialogBody`, `reviewContext`, `reviewContextTitle`; keep `reviewClose` for the list only. `updateDialogViewport()` measures `visualViewport`; `saveComment()` reports whether the current entry still exists.

- [x] Add browser cases for confirm/reopen/reload, long mobile body and visual viewport resize, empty recall context; adapt existing export and keyboard tests to the approved flow. Observe the new behavior fail before implementation.
- [x] Move return buttons into results action rows with secondary styling; implement dialog body/footer, collapsible context and mode-specific actions using existing tokens.
- [x] Add confirmation, viewport sizing and list/editor state management without changing autosave/report semantics.
- [x] Build with `python3 scripts/build_html.py`; run focused browser tests. Expected: all selected tests pass without errors or skips.
- [x] Inspect dark/light renders at 320px, 375px and desktop; run the Impeccable detector once over changed UI sources and `git diff --check`.
- [x] Run `npm test`. Expected: all tests pass, no skips. Commit the scoped changes and obtain independent review against the spec before pushing.

Publication follows the review: fast-forward `origin/master`, verify successful Pages deployment and the live comment/return flows.

## Verification record

- Browser and JavaScript suite: 163 passed, no skips; Python suite: 475 passed.
- Inspected desktop, 375px dark and 320px light renders; confirmed return navigation, autosave and editor/list controls.
- Independent review found one keyboard viewport issue: the active line of a long comment could be clipped. Fixed with caret-aware scrolling and a RED→GREEN test for lines 1, 10 and 20 at visible heights 240px and 280px; the full suite passed afterward.
- Physical iOS keyboard and native share sheet were not exercised; viewport behavior was checked in Chrome using viewport events.
