# UX refinement implementation plan

> **For agentic workers:** Implement in the current checkout, task by task, with focused failing tests before behavior changes and a full verification pass at the end.

**Goal:** Make the trainer easier to start, answer, and browse on desktop and phones while keeping a single standalone HTML file.

**Architecture:** Keep selection logic in `src/quiz.mjs`, browser state and rendering in `src/quiz.ui.js`, structure in `src/template.html`, and styling in `src/quiz.css`. Preserve the existing progress format and source bank.

**Tech Stack:** Vanilla JavaScript, HTML, CSS, Node test runner, Python build script. No product dependencies.

**Spec:** The seven UX changes approved in the conversation on 2026-09-20.

## Global constraints

- The result remains one offline HTML file.
- Questions remain Russian and options Chinese.
- Existing progress JSON keeps version 1 and its fields.
- Existing uncommitted changes and source files remain intact.

## Review focus

- Empty modes must disable Start and offer a working way back to a normal round.
- Topic, year, and stage filters must compose with exactly one selected mode.
- Expanding a database answer must survive loading the next batch.
- Keyboard use must work for radio modes, disclosure controls, and answers.
- Mobile feedback must be brought into view while respecting reduced motion.

## Task 1: Exclusive study modes

**Files:** `src/quiz.mjs`, `src/quiz.ui.js`, `src/template.html`, `src/quiz.css`, `test/quiz.test.mjs`

- [ ] Add a failing test where each mode (`all`, `new`, `mistakes`, `due`) selects the expected records and the other filters still apply.
- [ ] Run `node --test test/quiz.test.mjs` and confirm the mode test fails.
- [ ] Replace the three overlapping progress booleans with `filters.mode`; add four native radio controls. Keep the verified-only checkbox in advanced settings only when unverified records exist.
- [ ] Run the focused test and full Node suite.

## Task 2: Simpler setup and useful empty state

**Files:** `src/template.html`, `src/quiz.ui.js`, `src/quiz.css`

- [ ] Make Start and Database the visible setup actions; put export, import, and reset progress into one native disclosure.
- [ ] Keep the reset-filters control; when the pool is empty show Reset filters and Start normal round actions, with the latter clearing filters before starting.
- [ ] Verify keyboard activation and empty-pool recovery in the browser.

## Task 3: Answer feedback and compact mobile layout

**Files:** `src/template.html`, `src/quiz.ui.js`, `src/quiz.css`

- [ ] Make the header show `Пройдено N из M` and reduce mobile header spacing and type size.
- [ ] After an answer, label correct and selected options with text and icons, focus the feedback, and scroll it into view on narrow screens with reduced-motion handling.
- [ ] Verify desktop and mobile rendering plus keyboard progression in the browser.

## Task 4: Incremental database rendering

**Files:** `src/quiz.mjs`, `src/quiz.ui.js`, `src/template.html`, `src/quiz.css`, `test/quiz.test.mjs`

- [ ] Add a failing test for first and subsequent batches of 50 records, including the final short batch.
- [ ] Run the test and confirm failure.
- [ ] Render 50 database cards initially and append 50 per click without replacing expanded cards; reset the list when search or filters change.
- [ ] Run focused and full tests; verify the browser interaction.

## Task 5: Final verification

**Files:** `CHANGELOG.md`, `dist/lingvostranovedenie-trainer.html`

- [ ] Record the UX changes in the changelog and regenerate the standalone HTML.
- [ ] Run `node --test test/*.test.mjs`, `python3 -m unittest discover -s test -t .`, and `git diff --check`.
- [ ] Verify the seven requested behaviors in the browser and review the final diff.
