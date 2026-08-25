# Component B/C Backend Build Log (continued, second rotation)

> `backend/buildLog1.md` is closed as of its final entry, **FE-surface-remount-key** (2026-08-25),
> and must not be appended to or edited further. It had grown past 10,000 lines. This file,
> `buildLog2.md`, is its rotation and continues the same living, append-only development audit log
> from this point forward, under the same rules: future work is appended as a new dated phase or
> batch, earlier entries are never removed, rewritten, or silently altered. `buildLog.md` (closed at
> FE-0c) and `buildLog1.md` (closed at FE-surface-remount-key) remain the earlier history and are
> read-only.

---

## 2026-08-25 — FE-surface-remount-key: supervisor verification (batch committed to `buildLog1.md`, closed before this note could be appended there)

**Provenance.** The batch itself — commit `19d4530`, "Component C: remount the task surface per task
instance, so an entered answer cannot survive into the next question" — was implemented and its
builder register entry appended to `backend/buildLog1.md` (ending, per convention, with the literal
placeholder `**Verification.** — supervisor's, pending`) before the decision to rotate the log. This
entry is the supervisor's verification half of that same batch, recorded here rather than reopening
the closed file.

**Verification — supervisor's, measured.** Independently reproduced, redirected to a file rather than
piped (this project's own SIGPIPE mitigation): `npx tsc --noEmit` exit 0. `npm run test:contract`
**514 tests, 514 passed, 0 failed**, run twice. Reconciles against the pre-batch baseline of 505,
measured at HEAD `682e5ba` immediately before this change: `505 + 9 added − 0 removed = 514`. The nine
new tests were also run in isolation (`node --import tsx --test
src/api/__tests__/c-surface-remounts-per-task.test.ts`): 9/9 pass.

Diff read in full — exactly the one `key` prop on `<Surface>`, its explanatory comment, the new test
file `frontend/src/api/__tests__/c-surface-remounts-per-task.test.ts`, and the builder's own register
entry in `buildLog1.md`; no file outside that set was touched, including the five files the concurrent
game-hub work had already modified in the same tree, confirmed absent from `git diff --stat` and from
the commit itself. Guard proven to fire in both directions (red with the key removed, red with the key
bound to a string constant, green on the real fixed file), with a positive control against a vacuously
`null` predicate.

**What was not verified, restated from the builder's own disclosure.** The remount itself was not
observed — this project has no rendering library, so no test here can mount a tree, drive a submit,
and confirm the input actually clears between tasks. What is proven is that the source binds the key
to a real, non-repeating, required-string field on the wire contract. That React remounts on a changed
key is relied upon, not verified by this project. Confirmed correct as stated: under the dev fixture,
`c_task_instance_id` is constant, so the fix will not visibly change anything in the browser until a
real backend serves genuinely distinct task instances — not a regression, a fixture limitation.

Committed as `19d4530`.

## 2026-08-25 - FE-entry-row-opens-on-slots: the entry scene now opens on the entry slots, with a visible scroll indicator

**Why.** Second finding from the first browser look at a Component C surface, at
`EXPO_PUBLIC_COMPONENT_C_DEV_FIXTURE_DIFFICULTY=5` (C-NP-01, `blanks=2`).

`DisplayWithEntryRow` renders the read-only `shown_sequence` followed by the editable entry slots
inside one horizontal `ScrollView`. The row scrolls rather than shrinking its tokens -- that is the
motor-constancy ruling this file's own header records, and it is correct. The consequence nobody had
seen until it ran: at difficulty 5 the shown sequence is long enough that the entry slots, the only
interactive part of the scene, render past the right edge of the viewport.

The owner filled the one slot that was visible and could not press SUBMIT. The button was correctly
disabled throughout -- `entryValues` still held a `null` in slot 2 -- but there was no way to discover
that. The second slot was off-screen and `showsHorizontalScrollIndicator={false}` was set, so nothing
on screen indicated any further content existed at all. A correct disabled state with no discoverable
cause is, to a child, indistinguishable from a broken button.

**Owner ruling, from two options presented:** open the row on the entry slots rather than on the
read-only sequence. The child can still scroll left to review it.

**What.** Two changes, both confined to `DisplayWithEntryRow`:

1. The `ScrollView` takes a ref and scrolls once, on mount, to `shownSequence.length * TOKEN_STRIDE`.
   That offset is derived, never tuned: the row has no leading horizontal padding and every token
   occupies exactly one `TOKEN_STRIDE`, so that expression IS the first entry slot's position and it
   moves correctly if `TOKEN_TOUCH_TARGET_SIZE` or `TOKEN_SPACING` ever change.
2. `showsHorizontalScrollIndicator={false}` becomes a visible indicator.

The scroll is **not animated**. Content sliding sideways just as the screen appears is a worse
attention cost for this audience than content simply already being in the right place. The work order
required reporting rather than deciding if the project had a documented reason to prefer animation:
`motor-constants.ts` and this feature were both checked, and there is none. `ANIMATION_DURATION_MS`
exists but is documented for the drag-drop return in `DraggableToken`, not for scrolling.

It runs once per mounted scene, guarded by `hasScrolledToEntryRef` rather than by an empty dependency
list, so no later re-render can yank the row back and fight a child's own scrolling. Since
`FE-surface-remount-key` (`19d4530`) now keys the surface on the task instance, a new task is a new
mount -- which is what makes "once per mount" also mean "once per task".

**ReorderRow was not touched, and this was confirmed rather than assumed.** NP-04's arrangement scene
has no entry/read-only split -- every token is the same draggable control and none is hidden behind
another -- so this defect does not arise there. Its indicator setting is unchanged and it gained no
scroll-on-mount. A dedicated guard asserts both, per-function rather than file-wide, because the two
components render structurally similar `ScrollView`s and a whole-file scan could not tell which one
it had found.

Nothing in focus or typing changed: `focusedSlot`, `buffers`, `handleDigit`, `handleDelete` and
`commit` are untouched. This batch makes an existing slot reachable and visible; it does not change
what typing does.

**A separate finding, reported and NOT built here.** With `blanks=2`, filling slot 1 does not advance
focus to slot 2 -- the child must tap the second slot themselves. That is arguably its own
discoverability problem, adjacent to this one but distinct from it. It was explicitly out of this
batch's scope and no auto-advance was added. Recorded here so it is not rediscovered from scratch.

**Verification.**

- `npx tsc --noEmit` - exit 0, achieved by fixing code. No `any`, no `as` cast, no `@ts-ignore`.
- `npm run test:contract` - 528 tests, 528 pass, 0 fail. Baseline measured immediately before this
  change at HEAD 85d973f was 514. Reconciles: 514 + 14 added - 0 removed = 528.
- `npx expo lint` - clean.
- Both guards were proven in BOTH directions against the REAL file, not only against synthetic
  strings: the file is read, mutated in memory back to its exact pre-fix shape, and each guard
  asserted red on it -- with a prior assertion that the mutation actually applied, so a no-op replace
  cannot produce a false red. Nine further negative controls pin each clause individually: an
  animated scroll, a hardcoded pixel offset, a dropped once-guard, an unattached ref, a suppressed
  indicator, a missing function, and a file that only discusses the fix in comments.
- `expo export` NOT run. The change adds no new module import -- `useEffect` and `useRef` come from
  `react`, already imported in this file for `useState` -- so the bundle graph is unchanged.
- The backend suite was NOT run. No backend file was changed by this batch.

**What was NOT done, and cannot be.** The scroll was NOT observed. This project has no rendering
library in devDependencies, so nothing here can mount the row, measure a viewport and assert the entry
slots are on screen. Neither the scroll moving the viewport, nor its timing, nor the absence of
animation in the rendered result is verified by this suite -- only what the source says. One specific
risk this leaves open and unproven: a `scrollTo` issued from a mount effect depends on the row's
content having been laid out by the time the effect runs, and whether that holds on every platform is
exactly the sort of thing only a browser and a device can answer. A supervisor should look at
DIFFICULTY=5 before this is treated as fixed.

**Files touched.** `frontend/src/features/c-session/primitives/value-token-row.tsx`,
`frontend/src/api/__tests__/c-entry-row-opens-on-entry-slots.test.ts`.

**Verification.** — supervisor's, pending

---

## 2026-08-25 — Correction: FE-entry-row-opens-on-slots shipped as row-wrapping, not the auto-scroll described above

**Append-only correction, per this file's own rule.** The entry directly above this one is not edited or removed; it describes an implementation that was superseded in the working tree before it was committed, and nobody wrote that supersession down until now.

**What the entry above says was built:** `DisplayWithEntryRow`'s `ScrollView` takes a ref and scrolls once on mount to `shownSequence.length * TOKEN_STRIDE`, with a visible scroll indicator, guarded by `hasScrolledToEntryRef`.

**What is actually in `value-token-row.tsx` right now:** there is no `ScrollView` in `DisplayWithEntryRow` at all. The shown sequence and the entry slots render inside one `View` styled `entryTokenRow` (`flexWrap: 'wrap'`), so the row wraps onto further lines instead of scrolling. The entry slots cannot go off-screen, because there is no longer a scrollable axis for them to go off of. `ReorderRow` (`C-NP-04`) is unchanged — still a horizontally scrolling `ScrollView`, per its own different reason (the whole draggable token count can exceed one row).

This is a stronger fix than the one ruled and described above, not a weaker one: auto-scroll moves the visible window to a fixed offset computed from `shownSequence.length`, which depends on that length being what the scroll math assumed; wrapping removes the off-screen case as a category, regardless of sequence length. Nobody has reported why the approach changed between the ruling and what shipped — recorded as an open question, not resolved here.

**Verification — supervisor's, measured, of the CURRENT code, independently of the entry above.**

- `npx tsc --noEmit` — exit 0.
- The test file `c-entry-row-opens-on-entry-slots.test.ts` run in isolation (`node --import tsx --test src/api/__tests__/c-entry-row-opens-on-entry-slots.test.ts`): **10 tests, 10 passed, 0 failed.** Its own test names assert the wrapping design directly — *"renders one wrapping row, not a ScrollView"*, *"the row guard fires when a ScrollView is reintroduced"* — which would not describe an auto-scroll implementation if one existed.
- Whole-suite `npm run test:contract`: **512 tests, 510 passed, 2 failed.** The two failures are the pre-existing, unrelated game-hub barrel-import defect (a test whose import graph reaches `react-native` via a theme barrel; diagnosed and documented separately in `10b-10h-master-work-order.md` §5).

**Arithmetic NOT reconciled, and stated as such rather than guessed.** The entry above's own baseline was 514, measured at `85d973f`. This tree also carries several other uncommitted, interleaved changes to the same files (`digit-keypad.tsx`'s calculator-order relayout, `c-session-screen.tsx`'s card-based redesign, `component-c-api.ts`'s dev-fixture family override) whose own individual test-count deltas have not been isolated from this one. A crashed test file's exact contribution to `node --test`'s aggregate `tests`/`fail` counts was also not independently confirmed here. Rather than publish a guessed reconciliation into a permanent record, this is left open: clean arithmetic is only possible from a real before/after diff at the point this work is actually committed, which is when it will be measured.

**What was NOT verified**, restated from the superseded entry's own disclosure and still true of the current code: nothing here can mount a component tree, so the wrapping itself — whether the entry slots genuinely render on-screen at difficulty 5, on a real device — has not been observed. `npx expo export` was not re-run for this correction; no new module import was introduced by switching `ScrollView` to `View`.
