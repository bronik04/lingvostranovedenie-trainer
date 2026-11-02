# Header and Mobile Navigation Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement the tasks in this session.

**Goal:** Apply the approved settings menu, numeric answers, and floating mobile navigation.

**Architecture:** Reuse the existing settings menu and next buttons. Change presentation and state synchronization without introducing duplicate actions or changing persisted progress.

**Tech Stack:** HTML, CSS semantic tokens, JavaScript, node:test and Playwright.

**Spec:** `docs/superpowers/specs/2026-10-31-header-mobile-design.md`

## Global Constraints

- Do not edit `src/ink/` or question data.
- Preserve themes, settings, keyboard controls and review functionality.
- No arrow in the next-question button.
- Work in the existing `codex/question-review` checkout; leave unrelated untracked files untouched and changes available for review.

## Review Focus

- Desktop Escape closes settings before it exits a round.
- Mobile review control stays accessible while desktop uses the hotkey.
- Numeric labels preserve answer identity after shuffling.
- Recall does not allow advancing before self-assessment.
- Floating actions disappear on results and on desktop after viewport resize.

### Task 1: Settings and answer numbers

**Files:** `src/template.html`, `src/quiz.css`, `src/quiz.ui.js`, `src/review.ui.js`, `src/quiz.mjs`, `src/chengyu.mjs`, `README.md`, existing tests.

**Interfaces:** Retain `setViewMenu(open)`, menu element IDs, and labelled-option objects; their labels become numeric strings.

- [x] Add assertions for one settings control, desktop/mobile review visibility, Escape, and numeric option labels; run and observe failures.
- [x] Replace separate header toggles with the shared popover and keep its controls synchronized.
- [x] Update existing tests and documentation for the menu and numbers; run the focused tests.

### Task 2: Mobile next action

**Files:** `src/quiz.css`, `src/quiz.ui.js`, `src/chengyu.ui.js`, `test/ui.test.mjs`, built `dist/lingvostranovedenie-trainer.html`.

**Interfaces:** Keep `nextButton`, `cyNextButton`, their labels, and current answer guards.

- [x] Add a browser test proving the next action remains in the viewport through scrolling and disappears on advancing; observe failure.
- [x] Fix existing next buttons to the mobile viewport after answering and reserve space for content; remove obsolete scrolling to the next button.
- [x] Verify recall assessment, end-of-round behavior, Chengyu, resize, both themes and 320px layout.
- [x] Build, run JavaScript and Python suites, inspect screenshots and review the complete diff.

Verification: baseline 81 logic tests passed; numeric labels and both new browser behaviors failed before implementation; 10 focused tests passed after implementation. Final suites: 154 JavaScript tests and 475 Python tests passed, no skips or failures. Build succeeded. Screenshots inspected at desktop, 375px dark and 320px light. Independent final code review reported no actionable findings.

Publication authorized by the user on 2026-11-02: commit the approved files, fast-forward `origin/master`, and verify the GitHub Pages deployment and published page.
