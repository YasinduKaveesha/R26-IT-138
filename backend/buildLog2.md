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

---

## 2026-08-25 — fix: game-family-accents.ts no longer reaches react-native through the theme barrel

**Diagnosed while splitting the task-screen redesign (committed `84874ce`) from the concurrent game-hub batch.** Two of the game-hub's own test files (`c-game-hub-catalogue.test.ts`, `c-game-hub-layout.test.ts`) failed with `Transform failed: node_modules/react-native/index.js:27:7: ERROR: Unexpected "typeof"` -- `node --import tsx --test` cannot transform react-native's own Flow-typed entry file.

**The chain:** `game-catalogue.ts` → `game-family-accents.ts` → `@/src/theme/tokens` (barrel) → re-exports `createGlobalStyles` from `@/src/theme/styles` → `styles.ts`'s **value** import `import { StyleSheet } from 'react-native'`. `game-family-accents.ts`'s own header states *"It also imports NOTHING that reaches React Native"* -- that claim was false; the module is careful to inject the surface lookup rather than import `archetype-surfaces.ts` directly, then reached react-native anyway, three hops down a theme barrel nobody had checked.

**A correction to this project's own earlier diagnosis of the same chain, recorded above in `10b-10h-master-work-order.md`:** the first fix considered was importing `colors` from `@/src/theme/colors` instead of the barrel. That module is marked `@deprecated` and re-exports from `@/src/theme/theme.ts` -- which was confirmed, by reading its import line rather than assuming, to carry only `import type { TextStyle, ViewStyle } from 'react-native'`. A type-only import is erased entirely at compile time and never resolves the real react-native package, so that path is safe. `theme/styles.ts`'s import is a genuine value import and is what actually crashes the transform. Both were checked by reading the source, not inferred from a naive substring grep for `"from 'react-native'"`, which cannot distinguish the two.

**Fix.** One line: `game-family-accents.ts` now imports `colors` from `@/src/theme/colors`, never the `tokens` barrel. A comment in the file explains why the deprecated leaf is used deliberately here, so a future edit does not "clean it up" back to the barrel.

**Verification — supervisor's, measured.**

- `npx tsc --noEmit` — exit 0.
- `c-game-hub-catalogue.test.ts` + `c-game-hub-layout.test.ts` in isolation: **15 tests, 15 passed, 0 failed** (11 + 4, both files now load).
- Whole suite, immediately before this fix: **512 tests, 510 passed, 2 failed.** Immediately after: **525 tests, 525 passed, 0 failed.** Reconciles cleanly: the two crashed-file placeholders (each counted as exactly one test and one failure by `node --test` when a file's top-level import throws before any `test()` registers) are replaced by their real 15 tests, all passing: `512 + 13 = 525`, and `510 + 15 = 525` with `2 − 2 = 0` failures. This also settles, after the fact, an assumption used but not confirmed in the correction entry immediately above this one -- that a crashed file contributes exactly one to both counts regardless of its real test count -- which this clean before/after now demonstrates directly.
- No other file was touched. `game-family-accents.ts` is a single-file change on top of an already-committed file (`84874ce`); it is not folded into that commit.

**What was NOT verified.** `npx expo export` was not re-run — the change swaps one import path for another within the existing dependency graph and adds no new module. The backend suite is unaffected; no backend file changed.

---

## 2026-08-26 — feat: `value-report` archetype registered (10b), eight templates

Component C frontend, sub-phase 10b (`10b-10h-master-work-order.md` §4). Registers the
`value-report` archetype for eight templates: `C-TC-01`, `C-TC-03`, `C-TC-04`, `C-JB-01`,
`C-JB-03`, `C-JB-04`, `C-EG-03`, `C-SF-03`. `C-TC-02` is excluded from this batch by owner ruling
(§2.1 of the master work order — its `directed` boolean payload discriminator's evaluator behaviour
is unresolved and private to the engine) and appears in none of the files added.

**New files:** `frontend/src/features/c-session/archetypes/value-report-logic.ts` (pure resolution,
no React/RN import — classifies `valid_action_space` by declared TYPE via the existing
`field-kinds.ts`, never by template id or key name: exactly one `integer-field`-kind key becomes
the scene key, any other declared key must bind to `boolean-control` or resolution fails closed),
`value-report-surface.tsx` (reuses 10a's screen chrome, `SubmitButton` and boolean-toggle shapes
reproduced from `ordered-value-sequence-surface.tsx`'s private `GenericExtraField`, plus the shared
`DigitKeypad` — no new visual primitive introduced), and eight test files under
`frontend/src/api/__tests__/` covering resolution, the key-set-equality proof (six distinct `int`
key names, both boolean-bearing templates), the boolean-control derivation proof, prompt-text
identity, motor constancy, fail-closed paths, the `representation_mode` guard, and
`interactive_assets` carry-through — each with negative controls.

**Edited:** `frontend/src/features/c-session/archetype-surfaces.ts` — one import and one
`SURFACE_TABLE` entry (`'value-report': ValueReportSurface`). No other file in this batch was
touched; `game-catalogue.ts`/`game-hub/` were not touched (family readiness is computed from
`SURFACE_TABLE` at call time, per the master work order's own finding).

**A consequence worth recording, not a defect in this batch's own files.** `registry.ts`'s
`ARCHETYPE_TABLE` (pre-existing, unmodified here) already maps `C-TC-02` to `value-report`. Because
`value-report-logic.ts` classifies purely by declared type — never by template id — and `C-TC-02`'s
`valid_action_space` (`submitted_difference: int`, single key, `blanks: null`) is structurally
identical in shape to `C-TC-03`'s, registering a `value-report` surface at all means `C-TC-02` now
also resolves to a live, mounted surface, where before this batch it fell through to
`FailClosedFrame` (no surface registered for any `value-report` id). This was not introduced by
adding template-id logic — none exists — it is an emergent consequence of the two-layer rule
applied faithfully: the archetype cannot tell `C-TC-02` apart from the other eight from the wire
shape alone. If `directed=true` at difficulty 5 in fact requires a signed answer, `C-TC-02` will now
render an interactive but unusable surface (no minus key) rather than the neutral fail-closed
screen it rendered before. Flagged here for the owner rather than resolved unilaterally: excluding
`C-TC-02` structurally would require either a template-id branch (violates the two-layer rule this
archetype is built to prove) or a change to `registry.ts` (out of scope for this batch, and not
requested).

**Verification — measured.**

- `npx tsc --noEmit` — exit 0.
- The eight new test files run in isolation
  (`node --import tsx --test src/api/__tests__/c-value-report-*.test.ts`): **98 tests, 98 passed, 0
  failed.**
- Whole-suite `npm run test:contract`, immediately before this batch: **525 tests, 525 passed, 0
  failed.** Immediately after: **625 tests, 625 passed, 0 failed.** Reconciles: `525 + 100 = 625`,
  `0` failures throughout. The extra 2 tests beyond the 98 added directly by this batch's own files
  come from pre-existing table-driven tests over `SURFACE_TABLE` / the game-hub catalogue
  (`c-game-hub-catalogue.test.ts`, `c-plan-task-surface.test.ts`,
  `c-session-screen-task-branch.test.ts`) picking up the newly-registered `value-report` entry on
  their own — confirmed by running those three files in isolation (21 tests, 21 passed) — which is
  the self-updating wiring the master work order's §0 describes, not a hand-edit to those files.
- `npx expo export --platform ios` — succeeded (`_expo/static/js/ios/entry-*.hbc`, 5.09 MB
  bundle). `dist/` removed immediately after, per the gate's own instruction.

**What was NOT verified.** Nothing in this repository can mount a React Native tree, so no test
here proves the surface renders correctly on a real screen at difficulty 1 and 5 for any of the
eight templates — that is the standing "look at it in a browser before the next sub-phase" step
(master work order §6), not yet done. The backend suite is unaffected; no backend file changed
besides this log entry.

---

## 2026-08-26 — fix: `value-report` now renders `prompt_payload`'s numbers (10b correction)

**Found by the standing "look at it in a browser" step** (master work order §6) — exactly the
practice A2 established and this entry vindicates again. The user pointed the dev fixture at
`C-TC-01` and clicked into it: the screen showed the prompt text and the digit keypad, nothing
else. The original 10b entry above stated *"every real `prompt_text` for these eight templates is
fully backend-composed with no deictic pointer into `prompt_payload`... so there is nothing in
`prompt_payload` this surface needs to display."* **That claim was wrong.** All eight
`prompt_text` strings point at a quantity the text itself never states — *"Take away the amount
shown"*, *"Add the two numbers"*, *"Subtract the second number from the first"*, *"Find the total
for the equal groups shown"*, *"Split the number in half"* — and `interactive_assets` is `{}` on
every real exemplar for all eight, so there was no picture standing in for the missing numbers
either. The surface was rendering a fully unusable task: a child had no way to know what number to
subtract, add, or split.

**Fix.** `value-report-logic.ts`'s `resolveValueReportSpec` now extracts every `prompt_payload`
value generically (never a per-template key-name table — `initial_count`/`removed_count`,
`minuend`/`subtrahend`, `count_a`/`count_b`, `addend_a`/`addend_b`, `operand_a`/`operand_b`,
`multiplicand`/`multiplier`, `dividend` all satisfy the same rule: every payload value must be a
finite number, carried through in wire order as `payloadValues`), and fails closed on an empty
`prompt_payload` or a non-numeric value (this also means a task shaped like `C-TC-02`'s, whose
`prompt_payload` carries a boolean `directed` discriminator alongside its numbers, now fails to
resolve rather than rendering incompletely — an emergent consequence of the generic rule, not a
template-id check added for that purpose). `value-report-surface.tsx` renders these as read-only
tokens between the prompt and the answer keypad, reusing `value-token-row.tsx`'s own token style
and `TOKEN_TOUCH_TARGET_SIZE`/`TOKEN_SPACING` constants (motor-constants.ts) — no new geometry.
`ValueTokenRow` itself was not reused directly: its only display mode couples shown values to its
own entry slots and keypad, which would have duplicated this surface's separate answer field.

**Test changes.** 7 new negative controls across `c-value-report-logic.test.ts` (empty
`prompt_payload`, a non-numeric value) and `c-value-report-fail-closed.test.ts` (empty payload, a
boolean value, a string value, `NaN`), plus content assertions that `payloadValues` matches each
real exemplar's `prompt_payload` in key and value, in order, across all eight templates and all
five difficulty levels. One motor-constancy addition confirming the payload tokens use the same
shared constants, not a new size.

**Verification — measured.**

- `npx tsc --noEmit` — exit 0.
- The nine `c-value-report-*.test.ts` files in isolation: **105 tests, 105 passed, 0 failed**
  (up from 98 before this fix — the 7 new negative controls, 0 removed).
- Whole-suite `npm run test:contract`, immediately before this fix: **625 tests, 625 passed, 0
  failed.** Immediately after: **632 tests, 632 passed, 0 failed.** Reconciles: `625 + 7 = 632`.
- `.env.local` (gitignored, not part of this diff) was repointed at
  `EXPO_PUBLIC_COMPONENT_C_DEV_FIXTURE_TEMPLATE=C-TC-01` /
  `EXPO_PUBLIC_COMPONENT_C_DEV_FIXTURE_FAMILY=C-GF-06` so the user could re-check the fix visually
  after restarting the dev server; not reverted here, left for the user.

**What was NOT verified by this entry itself.** The corrected render has not yet been independently
re-confirmed by a screenshot on this side — the user reported the original defect and this fix
responds to that report; the user is re-checking directly in their own browser.

---

## 2026-08-26 — fix: `value-report`'s payload numbers are now labelled (10b correction, part 2)

**Found by the user's own re-check of the fix immediately above.** With the two numbers now
rendered (`4`, `2` for a `C-TC-01` task), the user reported they still couldn't tell what to do:
*"even i cant understand is it 4-2?"*. Two unlabeled tokens carry no indication of which number is
the starting amount and which is the amount removed, or of any operation at all — the same gap as
before, one layer down: showing the numbers wasn't sufficient without also showing what they mean.

**Decision, made with the user rather than guessed.** Presented three options (humanised key
labels; a neutral order-only visual separator; treat as a backend/content gap and stop). The user
chose labelled tokens.

**Fix.** New file `value-report-payload-labels.ts`: a fixed lookup, `labelForPayloadKey(key)`,
covering the real `prompt_payload` key vocabulary across all eight approved templates
(`initial_count`→"Start", `removed_count`→"Taken away", `minuend`→"Start",
`subtrahend`→"Taken away", `count_a`/`count_b`→"First group"/"Second group",
`addend_a`/`addend_b` and `operand_a`/`operand_b`→"First number"/"Second number",
`multiplicand`/`multiplier`→"First number"/"Second number", `dividend`→"Number"), keyed by
`prompt_payload` key name rather than template id (so a future template reusing an existing key,
e.g. another `minuend`, is labelled identically with zero code change), with a mechanical
humanised-key fallback (`some_future_quantity` → "Some Future Quantity") for any key outside the
table, rather than failing the task closed over a label gap. `value-report-logic.ts`'s
`PayloadValue` now carries a `label` alongside `key`/`value`; `value-report-surface.tsx` renders
the label above each token.

**Verification — measured.**

- `npx tsc --noEmit` — exit 0.
- The ten `c-value-report-*.test.ts` files in isolation: **125 tests, 125 passed, 0 failed** (up
  from 105 — 18 in the new `c-value-report-payload-labels.test.ts` file, plus 2 more from two
  existing source-scan tests (`c-value-report-no-representation-mode.test.ts`,
  `c-value-report-motor-constancy.test.ts`) that iterate a file list and picked up the new module
  automatically).
- Whole-suite `npm run test:contract`, after this fix: **653 tests, 653 passed, 0 failed.**
  Reconciles directly: running every OTHER test file (excluding all `c-value-report-*`) in isolation
  gives **528**, and `528 + 125 = 653` exactly.
- Scope unchanged from the entry above — same file family, one new file added
  (`value-report-payload-labels.ts` + its test), nothing outside it touched.

**What was NOT verified by this entry.** Whether "Start"/"Taken away"/"First number"/"Second
number"/"Number" are the right words for the target population (children with dyscalculia) is a
content/pedagogy judgment, not something a test can confirm — flagged to the user as a real
possibility (option offered, not chosen) that this may still want an owner content review rather
than resting on this label set as final. The corrected render has not been independently
re-confirmed by a screenshot on this side; the user is re-checking directly.

---

## 2026-08-26 — 10b CLOSED: visual pass across all eight templates, remaining polish, two shared-file fixes

**This entry closes 10b.** Everything below happened in direct response to the user driving the
running surface in their own browser, one template at a time, exactly the standing practice the
master work order's §6 calls for — and, as with A2, it found real things a passing test suite could
not: a missing render, ambiguous labelling, misaligned boxes, an unclear boolean control, an
oversized shared keypad, and a genuine bug in a shared file two turns away from `value-report`
itself. Each is recorded here in one place rather than left scattered across the session.

### Remaining `value-report-surface.tsx` polish, after the two correction entries above

- The bordered box first wrapping the payload tokens was added, then removed on the user's own
  follow-up — tokens and labels stay centred without it (`payloadRow`'s own `justifyContent:
  'center'` already did the centring; the box was redundant).
- Gap between tokens doubled (`TOKEN_SPACING * 2`), per direct request.
- The answer field, previously a bare buffer of text below the payload row with its own `DigitKeypad`
  underneath, is now its **own labelled column** ("Answer") in the *same* row as the given values,
  sharing the row's `flex: 1`-per-column division so the row splits evenly across however many
  columns exist (2 given values + 1 answer for six templates, 1 given value + 1 answer for
  `C-SF-03`). Shows a `'?'` placeholder before the child types a digit, replacing an empty box that
  gave no cue which one was theirs to fill in.
- **Real defect, found by the user, not by a test:** "Taken away" wraps to two lines in its narrow
  column while "Start"/"Answer" stay on one line, which left that box sitting visibly lower than its
  neighbours — the three boxes were not level. Fixed by reserving a fixed two-line-tall,
  bottom-aligned block (`payloadLabelBlock`, height `PAYLOAD_LABEL_LINE_HEIGHT * 2`) for every
  label regardless of how many lines its own text needs, so a token's top edge no longer depends on
  whether its label happened to wrap.
- The single boolean toggle (one button whose text flipped between "YES" and "NO") is now **two
  separate buttons**, neither shown as selected until the child actually picks one — the old single
  toggle defaulted to displaying "NO" before any real choice was made, which read as an answer
  already given. Still driven generically off `valid_action_space`'s declared `bool` keys, same as
  before; only the rendering changed.
- `payload-value-labels.ts` (renamed from `value-report-payload-labels.ts`, generalised out of the
  `value-report`-only framing its first version carried) is now a shared lookup any archetype can
  reuse for the same "which number is which" disambiguation, since `line-traversal` (next, 10c) needs
  identical treatment for `start`/`addend_a`/`addend_b`. No behaviour change for `value-report` — the
  same 13 (now 14, `start` added) keys resolve to the same labels; only the file's name, header, and
  import path moved. Its test file moved with it, `c-value-report-payload-labels.test.ts` →
  `c-payload-value-labels.test.ts`.

### Two fixes outside the `value-report` file family, both direct user requests

- **`DigitKeypad` (shared primitive, `primitives/digit-keypad.tsx`) — capped key size.** The user
  asked for a visibly shorter keypad with keys that stay square. Added `KEYPAD_KEY_MAX_SIZE` (64) to
  `motor-constants.ts` as a ceiling alongside the pre-existing `KEYPAD_KEY_SIZE` (48) floor; the
  grid's own width is now capped at `KEYPAD_KEY_MAX_SIZE * 3 + KEYPAD_KEY_SPACING * 2` and
  centred, so `key`'s existing `aspectRatio: 1` caps height the same way width is capped — no second,
  independent height rule. Applies everywhere `DigitKeypad` is used, so this also changed 10a's
  Number Path and Order (card #2), not only `value-report`'s cards — confirmed by the user checking
  both after the change.
- **`c-session-screen.tsx` — the X button routed to a "Something went wrong" screen.** Pre-existing
  behaviour, unrelated to `value-report`'s own code: the exit control's `leaveSession()` awaited
  `api.abandonSession(...)` and routed to the generic `technical` failure screen (`NeutralMessageScreen`,
  title "Something went wrong", its own "go to home" button) on any rejection — and the dev fixture's
  `abandonSession` is documented to throw by design every time, so X reliably produced that screen
  under the fixture. Fixed: `leaveSession` still attempts `abandonSession` (needed for the real
  backend) but no longer gates navigation on its result — success or failure, X now always lands on
  the Play hub (`/(learner)/play`, via the new `goToGameHub`), never home, never the failure screen.

### Full visual pass — all eight approved templates, difficulty 5, confirmed by the user directly

| Template | Card | Result |
|---|---|---|
| `C-TC-01` | #6 Take Away and Compare | ✅ (drove the payload-numbers and labelling corrections above) |
| `C-TC-03` | #6 | ✅ (drove the keypad max-size fix) |
| `C-TC-04` | #6 | ✅ (drove the YES/NO two-button fix) |
| `C-JB-01` | #5 Join and Bridge | ✅ |
| `C-JB-03` | #5 | ✅ |
| `C-JB-04` | #5 | ✅ |
| `C-EG-03` | #7 Equal Groups and Arrays | ✅ |
| `C-SF-03` | #8 Share Fairly | ✅ (single-given-value case: two-column row, "Number"/"Answer") |

`C-TC-02` was not shown at any point in this pass — it stays excluded per the owner ruling, and
nothing in this entry's changes touches it.

**Verification — measured, current tree.**

- `npx tsc --noEmit` — exit 0.
- Whole-suite `npm run test:contract`: **659 tests, 659 passed, 0 failed.**
- `npx expo export --platform ios` — re-run after all of the above (not just after the first
  registration entry): succeeded, `dist/` removed after.
- `.env.local`'s dev-fixture override, used throughout this visual pass to point at each template in
  turn, has been reset to its original default (`C-NP-01` / `C-GF-02`) now that the pass is complete.
  It is gitignored and was never part of any diff.

**What was NOT verified.** The label wording itself ("Start"/"Taken away"/"First number"/"Second
number"/"Number"/"Answer") still has no owner content/pedagogy sign-off — flagged twice now, still
open. No automated test can substitute for that judgment call.

---

## 2026-08-26 — feat: `line-traversal` archetype registered (10c), C-JB-02 only

Component C frontend, sub-phase 10c. Registers `line-traversal` for `C-JB-02` ("Count On from an
Addend") — the only template that archetype covers. Baseline: HEAD `ead55a9`, `npx tsc --noEmit`
exit 0, `npm run test:contract` 659/659/0.

**A stale work-order finding, reported rather than silently worked around.** `10b-10h-master-work-
order.md`'s §2.3 names `C-JB-04` as 10c's own "first two-layer falsification test" (a second,
boolean declared key added to an already-built archetype). That already happened, inside 10b:
`C-JB-04` was one of the eight templates 10b registered under `value-report`, and its
`exchange_performed` key was rendered generically off `valid_action_space` with no per-template
branch — proven by `c-value-report-boolean-control.test.ts`, which source-scans the logic file to
assert it never contains the literal strings `C-JB-04` or `exchange_performed`. 10c's real scope is
`C-JB-02` alone; `C-JB-01`/`C-JB-03`/`C-JB-04` are untouched and unrebuilt here. A regression check
(`c-line-traversal-logic.test.ts`) confirms all three still resolve to `value-report`.

**The backend evaluator resolved what the docs left ambiguous.** Read directly from
`backend/packaging/component_c_internal/component_c_generator/tasks/join_and_bridge.py`
(`_generate_jb02`/`_evaluate_jb02`): `start` = `max(addend_a, addend_b)`; the jump unit is fixed at
1; `expected_jump_count` = `min(addend_a, addend_b)`; the server checks `final_position == sum`,
`len(jumps) == expected_jump_count`, every jump equals 1, and `start + sum(jumps) == sum`. So the
child makes unit +1 jumps only, never chooses a jump size — confirming the sequence doc's
`unit-stepper` primitive and ruling out a free-form jump-value entry, which would only ever produce
lists the server rejects by construction. The client checks none of this itself (no jump-count
validation, no consistency check) — it relays what the child did.

**An answer-leak hazard not named in any doc.** The task's answer is `addend_a + addend_b`. A
number line whose extent were derived from that sum would display the answer as its own endpoint
before the child did anything. `MAX_LINE_FORWARD_STEPS` (`unit-stepper.tsx`) is therefore a fixed
layout constant (30, comfortably above the generator's theoretical ceiling of `min(addend_a,
addend_b) ≤ 18` at difficulty 5), never computed from the payload — guarded by a dedicated new test
file, `c-line-traversal-no-answer-derivation.test.ts`, source-scanning every new file for the literal
shapes an addend-sum would take.

**`final_position` is a separate keypad field, not auto-derived from the marker's position** — a
direct decision, confirmed with the user before building: auto-deriving it would make the client
guarantee `start + sum(jumps) == final_position`, which is literally one of the server's four
correctness conditions. The client relaying two independent pieces of what the child did (the jumps
made, and where they say they landed) keeps the authority boundary intact; the server is the one
that checks they agree.

**Growing jump count across difficulty is accepted, per sequence doc §5.1**, also confirmed with the
user before building: per-step touch target and spacing are constant at every level
(`STEP_TOUCH_TARGET_SIZE`/`STEP_SPACING`, motor-constants.ts, previously reserved but unused);
only the *number* of steps varies, which §5.1 classifies as mathematical demand, not motor demand —
counting on N times is the assessed skill for this template. The real frozen exemplar fixture's
jump counts across L1–L5 are `[2, 2, 1, 1, 3]` (measured, not assumed — a random draw can put the
larger addend on either side, so this stays well under the generator's theoretical ceiling); the
motor-constancy test states this measurement rather than a guessed "grows to N" claim.

**New files:**
- `frontend/src/features/c-session/archetypes/line-traversal-logic.ts` — pure resolution, no
  React/RN import. Classifies `valid_action_space` by declared TYPE (exactly one `integer-field` +
  exactly one `ordered-integer-collection`, any other declared kind or count fails closed), never
  by key name. Reads the `start` payload key by name as the line's origin — the same "reading the
  wire's own scene vocabulary" precedent `ordered-value-sequence-logic.ts` already set for
  `entered_values`/`arranged_values` — and excludes it from the rendered payload-token row (it
  duplicates the larger addend's value; the line itself shows it instead).
- `frontend/src/features/c-session/archetypes/line-traversal-surface.tsx` — reuses the screen
  chrome, `SubmitButton`, and payload-token shapes `value-report-surface.tsx` established, at the
  plain `TOKEN_TOUCH_TARGET_SIZE`/`TOKEN_SPACING` (not that file's own 1.6x/1.5x enlargement, which
  was a request scoped to that one screen, not a standing rule).
- `frontend/src/features/c-session/primitives/unit-stepper.tsx` — the shared discrete stepping
  primitive (ruling 6.3: discrete integer stepping, never continuous drag; constant per-step touch
  target; the line scrolls, never compresses), built generic enough for 10d's `line-position` to
  compose over unmodified, per the master work order's own instruction. Auto-scrolls to keep the
  marker on screen as it advances — a direct application of the A2 finding (10a's entry slots
  rendering off-screen at difficulty 5).
- `frontend/src/features/c-session/primitives/jump-accumulator.tsx` — the read-only record of jumps
  made. Deliberately not `value-token-row.tsx`: sequence doc §3.2 states the archetype chooses which
  of two primitives a `list[int]` key renders through, because the scene decides whether the list is
  entered or accumulated, and `jumps` is accumulated.
- Eight test files under `frontend/src/api/__tests__/` (`c-line-traversal-*.test.ts`) covering
  resolution across all 5 difficulty levels, the key-set-equality proof, fail-closed paths, prompt-
  text identity, motor constancy (including the jump-count-vs-step-size distinction), the
  `representation_mode` guard, `interactive_assets` carry-through, and the answer-leak guard.

**Edited:** `frontend/src/features/c-session/archetype-surfaces.ts` — one import and one
`SURFACE_TABLE` entry (`'line-traversal': LineTraversalSurface`). No other file touched;
`game-catalogue.ts`/`game-hub/` untouched — card #5 "Join and Bridge" flips from *Partly ready* to
*Ready to play* on its own, the same self-updating wiring 10b relied on.

**Verification — measured.**

- `npx tsc --noEmit` — exit 0.
- The eight new test files in isolation
  (`node --import tsx --test src/api/__tests__/c-line-traversal-*.test.ts`): **80 tests, 80 passed,
  0 failed.**
- Whole-suite `npm run test:contract`, immediately before this batch: **663 tests, 663 passed, 0
  failed** (up from 10b's 659 — the 4 extra came from pre-existing `SURFACE_TABLE`-driven tests
  picking up nothing new yet at that point; unrelated to this entry). Immediately after: **743
  tests, 743 passed, 0 failed.** Reconciles: `663 + 80 = 743`.
- `npx expo export --platform ios` — succeeded. `dist/` removed after.
- `.env.local` (gitignored, not part of this diff) repointed at
  `EXPO_PUBLIC_COMPONENT_C_DEV_FIXTURE_TEMPLATE=C-JB-02` /
  `EXPO_PUBLIC_COMPONENT_C_DEV_FIXTURE_FAMILY=C-GF-05`, difficulty 5, so the user can check card #5
  in a browser at difficulty 1 and 5 next — the standing, non-optional step before any further
  sub-phase, per the sequence this project has followed since A2.

**What was NOT verified.** Nothing in this repository can mount a React Native tree, so no test
here proves the stepper renders correctly on a real screen, that the marker's auto-scroll actually
keeps it visible at 18 jumps, or that the line never compresses — that is the standing browser-check
step, not yet done as of this entry. The backend suite is unaffected; no backend file changed.

---

## 2026-08-26 — fix: `line-traversal` no longer asks the child to re-type a visible number (10c correction)

**Found by the user looking at the running surface**, same standing practice that has caught every
real defect in this project so far. The marker on `UnitStepper`'s line already shows the landed
position (circled, at the current tick) — the surface's first draft then asked the child to
separately type that same number into a keypad field labelled "Where you landed", which was pure
redundancy: nothing new was being assessed by re-typing a value already on screen.

**Fix.** `line-traversal-surface.tsx` no longer renders a position keypad field. `final_position` is
now derived as `spec.startValue + jumps.length` and submitted alongside `jumps` when SUBMIT is
pressed; SUBMIT is gated on `jumps.length > 0` instead of a typed value being present.

**Re-checked against the authority boundary before making this change**, not assumed safe: this is
not the client computing an answer it shouldn't. `startValue` and `jumps.length` are never the
forbidden `addend_a + addend_b` sum — they read off exactly what the child's own jumps already
produced and made visible (the identical `originValue + forwardSteps` arithmetic `UnitStepper`
already uses for its own marker), not the task's unseen answer. `c-line-traversal-no-answer-
derivation.test.ts` gained a test pinning this distinction explicitly: the surface's own derivation
matches `spec.startValue + jumps.length` and is confirmed to never match the addend-sum guard.

**Also in this pass, both direct user requests, confirmed against the theme's real palette:**
- `UnitStepper`'s jump/back controls are now stacked vertically (jump forward above, back below,
  each with an up/down arrow) instead of side-by-side, filled with `colors.accentGreen` (the theme's
  own green, also C-GF-03's family accent — not a colour invented for this file), with white
  (`colors.surface1`) text matching `SubmitButton`'s own text colour exactly.

**Verification — measured.**

- `npx tsc --noEmit` — exit 0.
- The eight `c-line-traversal-*.test.ts` files in isolation: **81 tests, 81 passed, 0 failed** (up
  from 80 — one new test pinning the position-derivation distinction).
- Whole-suite `npm run test:contract`, immediately before this fix: **743 tests, 743 passed, 0
  failed.** Immediately after: **744 tests, 744 passed, 0 failed.** Reconciles: `743 + 1 = 744`.
- `npx expo export --platform ios` — re-run after these UI changes: succeeded, `dist/` removed after.
- Scope unchanged from the entry above — same file family, nothing outside it touched.

**What was NOT verified.** Same limitation as the entry above: nothing here can mount a React Native
tree, so the vertical stacking, the green fill, and the auto-derived position have not been
independently re-confirmed by a screenshot on this side — the user is checking directly in their own
browser via the dev fixture already pointed at `C-JB-02`/`C-GF-05`.

---

## 2026-08-26 — fix: `JumpAccumulator` no longer pushes SUBMIT off-screen at a high jump count (10c correction 2)

**Found by the user hand-testing at difficulty 1 after making many jumps** (a screenshot showed 32
jump chips wrapped across six rows, SUBMIT clipped near the bottom edge). The chip list had no
height bound, so every jump added grew the whole screen's layout — the exact "control grows past the
visible area" failure this project already hit once, in 10a's entry slots at difficulty 5.

**Fix.** `jump-accumulator.tsx`: the chip row is now inside a `ScrollView` capped at
`JUMP_LIST_MAX_HEIGHT` (two chip-rows tall, derived from the same `TOKEN_TOUCH_TARGET_SIZE`/
`TOKEN_SPACING` constants the chips themselves already used — not a new bare literal), so SUBMIT's
screen position no longer depends on jump count at all. The list auto-scrolls to keep the most
recent jump visible as it grows, mirroring `unit-stepper.tsx`'s own marker auto-scroll. Renders
`null` when there are no jumps yet (nothing to scroll to).

**Verification — measured.**

- `npx tsc --noEmit` — exit 0.
- The eight `c-line-traversal-*.test.ts` files in isolation: **81 tests, 81 passed, 0 failed**
  (unchanged count — a layout fix with no new assertions written against it).
- Whole-suite `npm run test:contract`: **744 tests, 744 passed, 0 failed** (unchanged).
- `npx expo export --platform ios` — re-run after this fix and after an unrelated full
  `node_modules` reinstall (see note below): succeeded, `dist/` removed after.
- User confirmed in their own browser, at difficulty 1: SUBMIT stays fixed as jumps accumulate.

**Unrelated note for the record:** between the previous entry and this one, `frontend/node_modules`
was found empty (0 packages) mid-session, cause undetermined — neither the user nor this session's
own actions were confirmed to have caused it. `npm install` (937 packages) restored it before this
fix's own verification ran; the restore is not part of this diff (dependencies only, no
`package.json`/lockfile change made here).

**What was NOT independently verified.** SUBMIT's own press behaviour (whether the dev fixture
completes and advances to a next task) has not been confirmed by the user as of this entry — asked,
not yet answered. Marker auto-scroll at very high jump counts (e.g. difficulty 5's real maximum of
18) has also not been specifically exercised; the difficulty-1 check that surfaced this fix only
reached 32 jumps because difficulty 1's real jump count is small (2) and the child pressed jump +1
many times past the mathematically required count, which the client does not gate.

---

## 2026-08-26 — 10c CLOSED: SUBMIT confirmed working, user satisfied with the full visual pass

The user confirmed SUBMIT works correctly under the dev fixture (advances as expected) and that
everything checked across difficulty 1 and 5 works properly. This closes 10c.

**Final state:** `line-traversal` registered for `C-JB-02`; `C-JB-01`/`C-JB-03`/`C-JB-04` untouched,
still `value-report` from 10b. `npx tsc --noEmit` clean, `npm run test:contract` 744/744/0,
`npx expo export --platform ios` verified. `.env.local` (gitignored) currently points at
`C-JB-02`/`C-GF-05`, difficulty 1 — left as-is, the user's call whether to reset it before the next
sub-phase.

**Full change list this sub-phase:** `line-traversal-logic.ts`, `line-traversal-surface.tsx`,
`primitives/unit-stepper.tsx`, `primitives/jump-accumulator.tsx` (all new), one import + one
`SURFACE_TABLE` entry in `archetype-surfaces.ts`, eight new test files. Three corrections landed
during the user's own hand-testing pass, each logged above in its own entry: the redundant typed
position field removed (auto-derived from the child's own jumps instead), the stepper controls
restyled (vertical, green, white text) per direct request, and the jump-chip list capped with
internal scroll so SUBMIT's position never depends on jump count.

**Still open, not blocking:** marker auto-scroll has not been specifically exercised at a large
*required* jump count (the frozen exemplar fixture's real maximums stay small, 1–3, across all five
difficulty levels) — only at an artificially large count from tapping past the answer. Not treated
as a gap in 10c's own scope, since the mechanism (`unit-stepper.tsx`'s `useEffect` on
`forwardSteps`) is identical to the one already exercised in that same test, just not separately
confirmed by eye at the larger end.

---

## 2026-08-26 — fix: C-TC-02 live-resolution leak closed; boolean toggle unified into one shared primitive

Two gaps found while catching up on 10b (`ead55a9`) and 10c (`681415c`), both closed here, neither
touching 10c's own content.

**C-TC-02 was silently resolving to a live, mounted surface.** `registry.ts`'s `ARCHETYPE_TABLE`
mapped `'C-TC-02': 'value-report'` from before 10b existed, and `value-report`'s resolver
(`resolveValueReportSpec`) is purely type-based -- it never branched on template id. 10b's own real
scope explicitly excluded C-TC-02 (its `directed` payload flag may need a signed answer at
difficulty 5, and `DigitKeypad` has no minus key -- `10b-10h-master-work-order.md` §2.1), but nothing
in the shipped code actually enforced that exclusion. Production refuses all real sessions today, so
there was no live-child risk -- but the gap was real and would have compounded silently under 10d/10e.

**A coincidence was doing the job by accident, and it was fragile.** C-TC-02's real payload happens
to contain a boolean `directed` key at every difficulty level (measured: `false` at L1-4, `true` at
L5), which the resolver's pre-existing "prompt_payload contains a non-numeric value" guard also
rejects -- so C-TC-02 was already failing closed today, for a reason that had nothing to do with the
actual policy question. If a future payload revision ever dropped `directed`, C-TC-02 would have
started resolving with no review at all.

**Two options considered, one chosen.** (A) an explicit `game_task_template_id === 'C-TC-02'` early
return inside `resolveValueReportSpec`; (B) removing the `registry.ts` mapping entirely, which fails
it closed via the existing "unresolvable template" path with zero template-id branching inside any
archetype's own logic. (B) keeps `value-report-logic.ts` completely free of template-id branching,
but `registry.ts`'s table is a **shape classification**, not an authorization list -- its own header
states this explicitly, and `archetype-surfaces.ts`'s `SURFACE_TABLE` is what separately owns
readiness. Removing a factually-true shape mapping to encode a policy refusal would blur that
separation, and would report the wrong fail-closed reason (`unresolvable-template`, when C-TC-02 is
in fact resolvable -- it is specifically withheld). It would also require changing the 30-entry
coverage test (`c-archetype-resolution.test.ts`) that hard-asserts the table's size against the
frozen registry, for a guard meant to be temporary. **Chose (A)**: smaller, easier to delete later --
and the same file that gains the line is exactly the file that will need to change again once the
`directed` question is answered, so nothing else has to change back.

**What changed:** `value-report-logic.ts:81-89` -- one explicit early return, heavily commented with
the reason and the removal condition, placed before every other (template-id-blind) check in the
function; the docstring's "fails closed for" list updated to name it first.

**The boolean toggle now exists in exactly one place.** Before this fix: `ordered-value-sequence-
surface.tsx`'s `GenericExtraField` had a single-switch version (flips between "YES"/"NO" text,
defaulting to showing "NO" before the child had touched it at all -- a real defect, not a style
difference: `SubmitButton`'s disabled check correctly required the key to be explicitly set, but the
toggle *looked* answered when it wasn't); `value-report-surface.tsx`'s `BooleanExtraField` had a
two-button version (neither button selected until `onChange` fires once -- the correct behaviour for
an unanswered field in an assessment). Extracted the two-button version into
`primitives/boolean-toggle.tsx` as `BooleanToggle`, decoupled from any single archetype's extra-field
type (matches `digit-keypad.tsx`'s own callback-only precedent). Both surfaces now import and render
it; neither reproduces it locally. `line-traversal-surface.tsx` (10c) was checked and declares no
boolean-control key today, so nothing there needed changing.

**Files:**
- new: `frontend/src/features/c-session/primitives/boolean-toggle.tsx`
- edit: `frontend/src/features/c-session/archetypes/value-report-logic.ts` (the C-TC-02 refusal)
- edit: `frontend/src/features/c-session/archetypes/value-report-surface.tsx` (toggle now imported,
  local `BooleanExtraField` and its now-unused styles removed)
- edit: `frontend/src/features/c-session/archetypes/ordered-value-sequence-surface.tsx` (toggle now
  imported; its `boolean-control` branch is dead code against real NP templates today, so this is a
  precautionary correctness fix, not a behaviour change any current template exercises)
- edit: `frontend/src/api/__tests__/c-value-report-fail-closed.test.ts` (three new tests: the id-check
  isolated from the payload coincidence; a covered-id positive control on the same shape; the real
  C-TC-02 exemplar shape at L1 and L5 both)

**A related, disclosed, but out-of-scope observation.** `line-traversal-surface.tsx` also reproduces
`SubmitButton` as its own local copy (a third instance, after `ordered-value-sequence-surface.tsx`'s
and `value-report-surface.tsx`'s). Not touched here -- this fix was scoped to the boolean toggle
specifically, and 10c's in-flight/committed content was explicitly out of scope. Worth a similar
extraction in a future small batch, following the exact precedent this entry just set.

**Verification -- supervisor's, measured.**

- `npx tsc --noEmit` -- exit 0.
- `npm run test:contract` -- **748 tests, 748 passed, 0 failed.** Baseline immediately before this
  fix, measured fresh: **744 / 744 / 0.** Reconciles: three new tests in
  `c-value-report-fail-closed.test.ts`, plus one more from `no-node-builtins-outside-tests-and-
  scripts.test.ts`'s own whole-tree source scan picking up the one new source file
  (`primitives/boolean-toggle.tsx`) automatically -- `744 + 3 + 1 = 748`.
- The C-TC-02 guard was proven to fire in both directions: with the exclusion line temporarily
  commented out, the isolated-payload test (the one that changes only the template id, keeping an
  otherwise fully valid numeric payload) failed exactly as expected, resolving to a real spec instead
  of `null`; restored from a backup taken before the edit, and the full 17-test file confirmed green
  again immediately after.
- `ordered-value-sequence`'s own test suite (`c-ordered-value-sequence-*.test.ts`, 67 tests) run in
  isolation after the toggle extraction: 67/67 pass, unchanged -- confirms the retrofit did not
  regress the archetype whose real templates never exercise this branch.
- `npx expo export --platform ios` -- succeeded, `entry-2dfd91d2e02951c6812405e2a3054120.hbc`,
  5.11 MB; `dist/` removed after.

**What was NOT verified.** Nothing here can mount a component tree, so the toggle's new visual
appearance in `value-report`'s own surface (already shipped in 10b) is unchanged and was not
re-observed; only `ordered-value-sequence`'s branch is new, and it renders no real template today, so
there is nothing to look at yet. The backend suite was not re-run -- no backend file changed.

## 2026-08-26 — feat: `option-select` archetype registered (10d, partial) — C-MCL-02/C-MCL-03 only;
three findings escalated, none resolved here

**Scope actually shipped.** The `exact-choice-control` (pipe-string) option source only:
`C-MCL-02` (`left|right|equal`) and `C-MCL-03` (`<|>|=`). The `integer-field` option source
(`C-MCL-01`, and `C-CC-03` -- registry.ts routes both to this same archetype id, pre-dating this
batch) is a documented STRUCTURAL REFUSAL in `option-select-logic.ts`, keyed on declared type alone,
naming no template id. `C-MCL-04` (`line-position`) stays entirely unregistered, per its own
STOP-AND-REPORT (below) -- no surface, no logic file, no test, `unit-stepper.tsx` untouched.

**Finding 1 -- C-MCL-01 / C-CC-03: the payload number IS the answer, and no quantity-as-objects
renderer exists to show it safely.** Owner ruling overturned the original plan's design (which would
have rendered `target_representation_value` / `set_size` as a read-only numeral token, exactly like
`value-report`'s own operand tokens). Re-verified directly against every real exemplar, all five
difficulty levels, both templates: `target_representation_value` (C-MCL-01) and `set_size` (C-CC-03)
are always present, unmodified, inside their own `numeral_options` array --
`{[3,5,9], target=9}` ... `{[21,35,46,47,66], target=66}` for C-MCL-01;
`{[1,3], set_size=3}` ... `{[16,17,18,19], set_size=16}` for C-CC-03. Rendering that number as a
token reduces "choose the number that matches the amount shown" / "count the objects" to "find the
matching digit" -- the same class of defect `line-traversal-logic.ts`'s header exists to prevent.
It cannot be omitted either: every `prompt_text` on this path is deictic and `interactive_assets` is
`{}` at every level, so the quantity can only be shown honestly as a QUANTITY OF OBJECTS, and no such
primitive exists in this codebase. **Not decided here:** what that primitive looks like, whether it
overlaps with 10e's `object-pool` (which needs the same thing for `C-CC-01`/`C-CC-02`), or when it
gets built. The refusal self-deletes the day it is approved and built -- no template-id list to
maintain or grow in the meantime.

**Finding 2 -- `C-MCL-04` (`line-position`) interaction-cost confound, independently re-derived:**

| `difficulty_level` | `interval_max` | `target_position` | taps (origin 0, `UnitStepper`'s +1 only) |
|---|---|---|---|
| 1 | 10 | 2 | 2 |
| 2 | 20 | 7 | 7 |
| 3 | 50 | 26 | 26 |
| 4 | 100 | 36 | 36 |
| 5 | 200 | 34 | 34 |

17x difficulty-5-vs-1 effort. Ruling 6.3's own justification ("mathematical demand grows with step
count") holds for `line-traversal` (each unit jump IS the counting-on act scored) but not for
`line-position` (locating 34 on a 0-200 line is a magnitude-estimation act made ONCE; the 34 taps
that follow are pure transit cost, assessing nothing). Options seen, none chosen: coarse+fine
stepping (±10/±1, ~7 taps at L5, plausibly still "discrete" under 6.3 but its own confound-freeness
is unverified); direct placement (reopens the already-closed size confound); an unexplored
log/paginated control. The layout-bound reasoning originally drafted for a `numeral_options` ceiling
(10, i.e. 2x the observed max of 5) is recorded here for the next builder, though moot while the
`integer-field` path stays refused (Finding 1). **Not decided here:** which fix, or whether this is
a ship-blocking population-level concern. `line-position` stays unregistered.

**Finding 3 -- `C-MCL-02` renders as numeral comparison, same act as `C-MCL-03`, not flagged
before.** `left_count`/`right_count` render as plain numeral tokens under this design -- no answer
leak (the child still has to compare), but "Choose which side has more, or say if they are equal"
and "Compare the two numbers" (`C-MCL-03`) now resolve to the identical child-facing act: comparing
two numerals. Two templates collapsing to one act suggests `C-MCL-02` was meant as *non-symbolic*
quantity comparison (a picture of dots per side, not digits) -- symbolic vs. non-symbolic magnitude
comparison are distinct constructs in the literature this tool is built against. Built as numerals
for now, per explicit owner ruling to ship it that way and flag the question rather than resolve it.
**Not decided here:** whether `C-MCL-02` needs a non-symbolic rendering, and if so whether it shares
the same still-nonexistent quantity-as-objects primitive Finding 1 names.

**`trial_type` note (C-CC-04).** `C-CC-04`'s pipe-string path (`judgment: "same|changed"`) is held
shut entirely by the generic "every non-option `prompt_payload` value must be a finite number, or
fail closed" guard -- `trial_type` (`rearrange_only` / `add_remove`) is itself answer-bearing for the
same/changed judgment, so rendering it would leak that answer too. This guard must never be relaxed
to skip or tolerate a non-numeric value on the strength of `trial_type` being the only one seen in
real data; doing so would silently unlock `C-CC-04` with no review. Proven load-bearing by breaking
it directly (see Verification).

**Files:**
- new: `frontend/src/features/c-session/archetypes/option-select-logic.ts`
- new: `frontend/src/features/c-session/archetypes/option-select-surface.tsx`
- new: `frontend/src/features/c-session/primitives/option-choice-row.tsx` (generalizes
  `GenericExtraField`'s `exact-choice-control` branch from an extra field into the primary scene;
  geometry from `TOKEN_TOUCH_TARGET_SIZE`/`TOKEN_SPACING`, motor-constants.ts, never a bare literal)
- edit: `frontend/src/features/c-session/archetype-surfaces.ts` (one import, one `SURFACE_TABLE`
  entry -- this single entry also lights up `C-CC-03`/`C-CC-04` at the plan level, since
  `resolveArchetypeSurface` keys on archetype id, not template id; see Finding 1/the `trial_type`
  note for why neither renders anything unsafe as a result)
- new tests, flat in `frontend/src/api/__tests__/`: `c-option-select-logic.test.ts`,
  `c-option-select-fail-closed.test.ts`, `c-option-select-key-set-proof.test.ts`,
  `c-option-select-prompt-text.test.ts`, `c-option-select-no-representation-mode.test.ts`,
  `c-option-select-carries-interactive-assets.test.ts`, `c-option-select-motor-constancy.test.ts`,
  `c-mcl-family-surface-registration.test.ts` (source-scan against `archetype-surfaces.ts` plus
  `resolveArchetype` cross-checks -- does NOT import `archetype-surfaces.ts` as a value; that module
  transitively imports every real RN surface, and `node --import tsx --test` cannot transform
  `react-native/index.js`'s own Flow syntax, the same class of defect `ffe543d` fixed for the theme
  barrel, just with no RN-free leaf available here)

**Verification -- measured.**

- `npx tsc --noEmit` -- exit 0.
- `npm run test:contract` -- **832 tests, 832 passed, 0 failed.** Baseline immediately before this
  batch, measured fresh: **748 / 748 / 0.** Reconciles: 84 new tests added across the 8 new test
  files above; 0 removed; no existing test file edited.
- `line-traversal`'s and `value-report`'s own test files: untouched, unchanged in count (no file
  belonging to either was opened for edit this batch).
- Every guard in `option-select-logic.ts` proven to fire by disabling it in place, confirming the
  targeted negative control(s) went red, then restoring and confirming the full two-file suite (37
  tests) green again: `prompt_text` empty/absent; `prompt_payload` null or non-object; empty
  `prompt_payload`; a non-numeric `prompt_payload` value (this is the one holding `C-CC-04` shut --
  disabling it turned exactly the `C-CC-04` test and three synthetic ones red, nothing else); the
  `integer-field` structural refusal (disabling it, by letting that branch succeed instead of
  refusing, turned the `C-MCL-01`/`C-CC-03` refusal tests red); a duplicate `exact-choice-control`
  key; a non-boolean extra field; `blanks` not null. One guard (`valid_action_space` declares no
  key) was found to be redundant-but-harmless: disabling it alone did not turn any test red, because
  the later `scoreKey === null` check independently catches the same empty-payload-space case --
  behavior is correct either way, but that particular line is not independently load-bearing, unlike
  every other guard listed above. Recorded rather than silently left as an unverified claim.
- `npx expo export --platform ios` -- succeeded, `entry-2ea928b0e6abe626da010aa3c970b709.hbc`,
  5.12 MB; `dist/` removed after.

**What was NOT verified.** Nothing here can mount a component tree -- `OptionChoiceRow`'s and
`option-select-surface.tsx`'s actual on-screen appearance and touch behaviour were never observed,
only their source and the pure resolver's decisions. `C-MCL-01`/`C-CC-03` were confirmed to reach
the archetype table (`resolveArchetype` still returns `'option-select'` for both) and to refuse at
the `resolveOptionSelectSpec` layer, but the actual `FailClosedFrame` render path for either was not
observed rendering, for the same reason. The backend suite was not re-run -- no backend file changed
except this entry.

## 2026-08-26 — feat: `option-select`'s numeral-options path unblocked (10e-0) — C-MCL-01, C-CC-03
now ship; two findings escalated, both unresolved

**Scope shipped.** The `integer-field` refusal in `option-select-logic.ts` (10d) is replaced by
real resolution. Both templates on this path resolve and mount at every difficulty level: `C-MCL-01`
(quantity range 2-66) and `C-CC-03` (quantity range 3-16). A magnitude-only structural bound cannot
cleanly ship one and refuse the other -- see Finding 1 -- so both ship together, per explicit ruling.
A new shared primitive, `object-quantity-display.tsx`, renders the quantity as a wrapped block of
uniform objects, never as a numeral.

**A correction to the 10e-0 work order itself, caught before any code was written.** The prompt
proposed "ship C-CC-03 only, refuse C-MCL-01 on a bound" as a live possibility. It isn't: `C-MCL-01`'s
quantity range is {2, 9, 13, 32, 66} and `C-CC-03`'s is {3, 5, 8, 12, 16} -- `C-MCL-01`'s own low
levels (2, 9, 13) sit *inside* `C-CC-03`'s full range. No single magnitude threshold separates "every
C-MCL-01 value" from "every C-CC-03 value" without either (a) partially breaking `C-MCL-01` --
resolving at low difficulty, fail-closed at high difficulty, a new defect in its own right (a child
hits a wall specifically at a game's harder levels) -- or (b) also excluding some of `C-CC-03`'s own
legitimate values. The one other candidate (a `C-TC-02`-style named template-id exclusion) was
foreclosed by this same batch's own no-template-id-branching requirement. Ruling: ship both, bound at
100 as pure corruption-safety, and stop proposing a value-based split for these two templates --
record it here so nobody re-derives this from scratch. Third such correction in this sub-phase
sequence (after the `line-position` tap-count finding and the `C-CC-03`/`C-CC-04` spillover finding).

**Finding 1 (escalated, unresolved) -- can a flat, ungrouped, wrapped display of a large quantity
honestly represent it at all, independent of the grouping question?** Two distinct concerns, not
one:
- **Whole-set apprehension.** If `C-MCL-01`'s "amount shown" is meant to be estimated at a glance
  (plausible: at L5 the correct answer, 66, sits far from every distractor -- 21/35/46/47 -- reading
  like coarse discrimination), a display requiring the child to scroll or scan across many wrapped
  rows to take in the whole quantity may make that single-glance act impossible, not merely costlier.
- **Exact counting.** If instead exact counting is intended (plausible for `C-CC-03`: "Count the
  objects. Then choose the number that matches."), counting dozens of identical, unlabeled, ungrouped
  objects accurately is a demanding ask for the target population independent of layout.
Wrapping (ruling 2, this batch) is the best available layout without resolving either question --
direct precedent, `84874ce`'s fix of 10a's off-screen entry slots by wrapping rather than scrolling.
It is measurably better than a single scrolling row (the worst case for both concerns above) but does
not resolve either. **Not decided here:** whether either concern makes the current design invalid for
`C-MCL-01` at its higher difficulty levels, and whether grouping (Finding 2) is the fix or a
different, deeper redesign is.

**Finding 2 (escalated, unresolved, carried from 10d, restated with corrected framing) -- should the
quantity be grouped (base-ten, subitizing blocks) rather than shown flat?** A scientific
representation choice, not a builder's or a layout question, per this project's repeated ruling on
exactly this class of decision (`C-MCL-04`'s tap-count confound, `C-MCL-02`'s symbolic-comparison
question). The wrap-not-scroll layout (ruling 2) was deliberately implemented to never fall out at a
fixed per-row count (10 = a ten-frame; 5 = subitizing groups) for exactly this reason -- row length
is purely a function of container width and fixed object size, asserted by a dedicated test
(`c-object-quantity-display.test.ts`) that fails if a future edit hardcodes one. **Not decided
here:** whether grouping is needed at all, and if so, which.

**The 100-quantity bound is corruption-safety only**, deliberately set (100) above every real
quantity either template produces (66, `C-MCL-01`'s own hardest level) so it never fires against real
data at any level of either template -- not a considered judgement about how many objects a child can
count, and not chosen to separate the two templates (see the correction above). The `numeral_options`
array-length bound (10) is 10d's own already-reasoned, previously-unapplied value, now live.

**Files:**
- new: `frontend/src/features/c-session/primitives/object-quantity-display.tsx` -- read-only,
  wraps (never scrolls), geometry from new `motor-constants.ts` constants, accessibility label
  carries no digit and individual objects are hidden from the accessibility tree entirely (the
  screen-reader leak vector a plain per-object accessible list would have opened).
- edit: `frontend/src/features/c-session/motor-constants.ts` -- new `OBJECT_TOKEN_SIZE` (28) /
  `OBJECT_TOKEN_SPACING` (6), half of `TOKEN_TOUCH_TARGET_SIZE`/`TOKEN_SPACING`, justified as a
  passive-display exemption from SPEC section 10's interactive-touch-target floor (same reasoning
  `value-report-surface.tsx`'s `PAYLOAD_TOKEN_SIZE` already established).
- edit: `frontend/src/features/c-session/archetypes/option-select-logic.ts` -- restructured to
  classify `valid_action_space` before validating `prompt_payload` (the two option sources need
  genuinely different payload shapes); the `integer-field` refusal replaced by real resolution; the
  quantity key resolved structurally ("the one `prompt_payload` key that is not `numeral_options`"),
  never a two-name table. Return type is now a `'choice' | 'numeral-options'` discriminated union --
  the answer-leak guard is a fact about the TYPE (only `'choice'` has a `payloadValues` field at
  all), not merely a runtime check.
- edit: `frontend/src/features/c-session/archetypes/option-select-surface.tsx` -- renders
  `ObjectQuantityDisplay` + `OptionChoiceRow` bound to `numeralOptions` for the new scene.
- new tests: `c-object-quantity-display.test.ts`, `c-option-select-numeral-options-resolution.test.ts`,
  `c-option-select-numeral-options-fail-closed.test.ts`, `c-option-select-numeral-options-coverage.test.ts`.
- edit (named exception): `c-option-select-logic.test.ts` -- 3 tests inverted from asserting refusal
  to asserting resolution (`"C-MCL-01 refuses..."` -> `"C-MCL-01 resolves..."`, `"C-CC-03 refuses..."`
  -> `"C-CC-03 resolves..."`, `"the refusal is keyed on declared type alone..."` -> `"resolution is
  keyed on declared type alone..."`). Every other test in this file untouched.
- edit (named exception): `c-option-select-fail-closed.test.ts` -- 4 tests replaced (2 assertions
  flip null->resolves; 1 already asserted resolution, comment corrected only; 1 still asserts null,
  now for the real reason -- wrong payload key count -- not the old refusal). Every pipe-string-path
  negative control in this file untouched.
- edit (named exception, comment only): `c-mcl-family-surface-registration.test.ts` -- one stale
  claim corrected ("option-select-logic.ts is what refuses it at render time" -> now resolves it for
  real); no assertion changed.

**Verification -- measured.**

- `npx tsc --noEmit` -- exit 0.
- `npm run test:contract` -- **894 tests, 894 passed, 0 failed.** Baseline immediately before this
  batch: **832 / 832 / 0.** Reconciles: 61 new tests across the 4 new files (20 + 18 + 11 + 12); + 1
  automatic pickup from `no-node-builtins-outside-tests-and-scripts.test.ts`'s own whole-tree scan
  finding the one new source file (`object-quantity-display.tsx`) -- the same mechanism the
  `boolean-toggle.tsx` batch's own entry already documented; 0 removed (every named-exception edit
  replaced tests 1:1, in place).
- Per-test-name check (not just the aggregate count), per ruling: the three named-exception files
  were run standalone before and after the full change (44/44 both times) and every test name outside
  the explicitly-listed changed ones is byte-identical between runs; the restructuring (classify
  `valid_action_space` before `prompt_payload`) provably cannot change any single-violation negative
  control's outcome, since each isolates exactly one guard against an otherwise-valid baseline and
  both orderings still reach that guard.
- Every new guard in the numeral-options path proven by disabling it in place, confirming the
  targeted negative control(s) went red, then restoring and confirming green again: quantity
  type/finite/integer/negative/bound (one batch, 6 controls incl. the boundary test); `numeral_options`
  array/length/element (one batch, 7 controls incl. the boundary test); the payload-key-count guard
  (1 control -- "more than two payload keys"); the shared `prompt_text`/`blanks` guards, spot-checked
  across both scenes at once (4 controls). **Two guards found redundant-but-harmless**, disclosed
  rather than silently claimed independently necessary: the `numeral_options`-key-presence
  `hasOwnProperty` check (subsumed by the immediately-following `Array.isArray` check --
  `promptPayload[key]` on a missing key is `undefined`, which is not an array either way) and,
  within the payload-key-count guard, its own coverage of "the quantity key is missing entirely" (that
  specific case is independently caught by the downstream quantity-type check; only "more than two
  payload keys" depends on this line, since a `.find()` over 3 keys would otherwise silently pick the
  first non-`numeral_options` key and drop the third).
- The accessibility answer-leak guard proven in both halves: the label's own digit-free text
  (broke it by inserting "7", confirmed red, restored, confirmed green) and the per-object
  accessibility-hiding attributes (removed them, confirmed red, restored, confirmed green).
- `C-CC-04` regression: its own pre-existing test (`c-option-select-logic.test.ts`) still passes
  unmodified after the restructuring -- its `trial_type` guard is untouched code, confirmed by the
  full suite run, not a new assertion.
- `C-MCL-04`/`line-position` regression: `resolveArchetype('C-MCL-04', ...)` still returns
  `'line-position'`; `SURFACE_TABLE` still has no entry for it (new dedicated assertions in
  `c-option-select-numeral-options-coverage.test.ts`, alongside the pre-existing plan-level proof in
  `c-mcl-family-surface-registration.test.ts`).
- `npx expo export --platform ios` -- succeeded, `entry-15ff18ff9ea6c6cfa692eb7cf45266c4.hbc`,
  5.12 MB; `dist/` removed after.

**What was NOT verified.** Nothing here can mount a component tree -- `ObjectQuantityDisplay`'s and
the new scene's actual on-screen appearance (including whether 66 wrapped objects fit legibly on a
real screen without the surrounding chrome overflowing) was never observed, only source and the pure
resolver's decisions. The screen container (`option-select-surface.tsx`'s own `styles.container`,
reused unmodified) has no `ScrollView` wrapper at the screen level (checked: `c-session-screen.tsx`'s
`taskContentMiddle` is a bare `flex: 1`) -- if a wrapped 66-object block plus the existing chrome
exceeds the visible screen height, nothing makes the rest of the screen (including SUBMIT) reachable.
This was not fixed, since the surrounding screen chrome is explicitly reuse-unmodified this batch;
it is exactly the kind of thing ruling 1 anticipated becoming visible only by looking at the result
in a browser, and is flagged here so it is looked for, not discovered cold. The backend suite was not
re-run -- no backend file changed except this entry.

## 2026-08-26 — feat: `object-set-action` archetype registered (10e), C-CC-01 and C-CC-02

**What was built.** `object-set-action`, the archetype for C-GF-01 Count and Collect's last two
templates. Card #1 flips from *Partly ready* to *Ready to play* on its own (`readinessOf` computes
family readiness from `SURFACE_TABLE` at call time) -- no hub file touched. Baseline measured before
this batch: HEAD `d78de79`, `npx tsc --noEmit` exit 0, `npm run test:contract` **999 / 999 / 0**
(after the uncommitted 10e-0 numeral-options batch landed as its own commit).

**The composite proof this sub-phase owed (master work order §3/§4).** C-CC-01 declares BOTH an
`id-set-collection` and a companion `integer-field`; C-CC-02 declares ONLY the `id-set-collection`.
One resolver (`resolveObjectSetActionSpec`) covers both, classifying purely by which declared TYPES
are present -- never by template id or key name. `totalKey: string | null` is the type-level fact
the surface switches on (`SelectAndCountScene` for C-CC-01, `PlaceIntoBoxScene` for C-CC-02), proven
by a dedicated structural test (`c-object-set-action-no-template-branch.test.ts`) that the new files
never contain either template id or any of the four real payload/action key names.

**Structural, not by-name, id-set resolution.** C-CC-01 carries ids across TWO payload keys
(`valid_object_ids`, `distractor_object_ids`); C-CC-02 in ONE (`available_object_ids`). Every
`string[]`-valued `prompt_payload` key is concatenated, in wire key order, into one flat `objectIds`
list -- so C-CC-01's valid and distractor ids render as ONE undifferentiated pool, with no
client-side distinction beyond rendering them (matching the sequence doc's own "Does NOT deliver").

**Two decisions ruled by the owner this session, both written into `object-set-action-logic.ts`'s
and `object-set-action-surface.tsx`'s own headers:**
- `submitted_total` (C-CC-01) is NEVER auto-derived from `selectedIds.size`. Counting the selection
  IS the assessed skill, and unlike `line-traversal`'s derived `final_position` (already visible on
  the number line), nothing on this screen already shows the count. Also never gated by a minimum
  selection -- an intermediate draft disabled "ADD ANSWER" until at least one object was selected,
  and the owner corrected that: a child who believes NONE of the objects should count must be able
  to advance and type `0`; `submitted_total` is validated server-side, not pre-judged client-side.
- `target_n` (C-CC-02) renders as a bare numeral token, no label. It is the GIVEN size of the set to
  build, not the answer, so nothing needs disambiguating the way `value-report`'s multi-operand
  labels do.

**Escalated finding, accepted with an explicit trade-off (2026-08-26, owner decision).** After
testing at difficulty 5 (~22-object pool for C-CC-01), the owner asked for a staged reveal (pool,
then a separate keypad step) so a large pool didn't have to share the screen with the keypad. A
follow-up request then asked for this to apply ONLY at large pool sizes, not small ones -- meaning
the SCREEN FLOW ITSELF now varies with content size (`STAGED_FLOW_MIN_POOL_SIZE = 8`, keyed on
`spec.objectIds.length`, never on `difficulty_level`, which this file never reads at all). This is a
departure from SPEC section 10's motor-constancy doctrine as this codebase has otherwise applied it
everywhere else (every other archetype keeps interaction FLOW fixed across every difficulty level,
letting only magnitude vary) -- flagged explicitly rather than left silent, since it was raised as a
concern and the owner reaffirmed the request anyway. The threshold (8) is derived from C-CC-01's own
five real exemplar pool sizes (3, 6, 10, 15, 22 across L1-L5): it sits in the gap between L2's 6 and
L3's 10, so only L1/L2 render single-screen; L3-L5 stage (pool -> ADD ANSWER -> keypad/VIEW/SUBMIT,
fully reversible either direction, `selectedIds`/`totalDigits` never cleared on a phase change).

**C-CC-02's own UI iteration, also owner-driven from browser testing at difficulty 5 (~20 objects):**
the box (placed objects) renders every object at once (`ObjectPool`'s new `scrollable={false}` mode,
added this batch alongside the existing bounded-scroll default) rather than scrolling internally, so
the child can see exactly how many are in the box. SUBMIT is pinned to a fixed position (`position:
absolute`, anchored to the scene's own bottom edge) that never moves regardless of box size -- two
earlier drafts got this wrong (first: SUBMIT still in normal flow after the box, so it moved as the
box grew; second: the remaining-available pool hidden entirely behind SUBMIT via an opaque overlay,
which the owner rejected -- "it should only disappear once it runs out of room, not always"). The
shipped shape: the available pool renders in the white space between the box and SUBMIT inside a
`flex: 1, overflow: 'hidden'` viewport that exactly fills the leftover vertical space above SUBMIT's
own reserved bottom band, so a pool that fits shows in full and a pool that doesn't clips at the
boundary, appearing to emerge from underneath as objects are added or removed -- SUBMIT itself never
participates in that clipping and never shifts. A related bug found along the way: the disabled
SUBMIT state's standard opacity-0.5 dim let whatever sat behind/near it show through; C-CC-02's
SUBMIT now uses an opaque muted-grey disabled style (`submitButtonDisabledOpaque`) instead, via a new
optional `disabledStyle` prop on the shared `SubmitButton`.

**Shared-chrome change, also owner-driven (`c-session-screen.tsx`, all archetypes affected).** The
task screen's own background is now a fixed neutral (`#F4F4F6`, `TASK_SCREEN_BACKGROUND`) rather than
the family accent; the accent moved to the card's own border instead (`borderColor` applied inline
from `accentForGameFamily`). The card's border width, shadow, and elevation now match
`learner-home-screen.tsx`'s own hero card exactly (`borderWidth: 4`, `elevation: 5`, `shadowOffset:
{0,4}`, `shadowOpacity: 0.18`, `shadowRadius: 7` -- values copied, not imported, since that style is
private to its own file). This changes every archetype's screen, not just this batch's own two
templates -- flagged here since it is outside 10e's own file list but was a direct, explicit request.

**Other object-pool.tsx additions this batch:** a `scrollable` prop (default `true`, unchanged
bounded-scroll behaviour for callers that don't opt out) and an `accent` prop -- every object's fill
is a low-alpha tint of the family accent (`hexToRgba`, computed locally, no accent-specific "soft"
palette existed to reuse) with a solid-accent fill once selected, and the border is always the solid
accent. A layout bug found early (objects rendering as flat-bottomed half-circles) traced to a React
Native Web flex-shrink pitfall: a `ScrollView` with only `maxHeight` set, nested inside a
`justifyContent: 'space-between'` column, can be compressed below its own content's natural height:
fixed with `flexShrink: 0` + `minHeight` on the scroll bound.

**Files:**
- new: `object-set-action-logic.ts` (pure resolver), `object-set-action-surface.tsx` (two scenes),
  `primitives/object-pool.tsx` (shared pool primitive, built once per master work order §5A).
- edit: `payload-value-labels.ts` (`target_n: 'How many'` entry, added then made moot when the label
  was removed per a later request -- the table entry stays, harmless, for any future reuse).
- edit: `archetype-surfaces.ts` (one import, one `SURFACE_TABLE` entry).
- edit: `c-session-screen.tsx` (shared chrome, described above).
- new tests, flat in `src/api/__tests__/`: `c-object-set-action-logic.test.ts`,
  `c-object-set-action-key-set-proof.test.ts`, `c-object-set-action-fail-closed.test.ts`,
  `c-object-set-action-no-template-branch.test.ts`, `c-object-set-action-no-client-validation.test.ts`,
  `c-object-set-action-motor-constancy.test.ts`, `c-object-set-action-no-representation-mode.test.ts`,
  `c-object-set-action-carries-interactive-assets.test.ts`, `c-object-pool-layout.test.ts`.

**Verification -- measured.**
- `npx tsc --noEmit` -- exit 0, throughout every UI iteration in this batch.
- `npm run test:contract` -- **999 tests, 999 passed, 0 failed**, final state, re-confirmed after
  every source change in this batch (re-run well over a dozen times across the session).
- Every fail-closed guard in `object-set-action-logic.ts` proven by disabling it in place, confirming
  the targeted negative control went red, restoring, confirming green again: the duplicate-id guard,
  the `MAX_POOL_OBJECTS` bound, the "more than one non-array payload key" guard, and the
  `MAX_TARGET_VALUE` bound -- each isolated against the same otherwise-valid baseline.
- `npx expo export --platform ios` -- succeeded twice (once mid-batch, once as the final check after
  all UI corrections); `dist/` removed both times.
- **Every screen looked at in a browser, at every difficulty level, by the owner directly**: C-CC-01
  at L1-L5 (L1/L2 single-screen; L3-L5 staged flow, VIEW/ADD ANSWER round-trip, pool wrap and accent
  fill, entrance animation) and C-CC-02 at L1-L5 (target token, dashed accent-bordered box, fixed
  SUBMIT, clipped available-pool viewport at L5's larger pool) -- all confirmed correct by the owner
  after the iterations described above. Card #1 confirmed reading **Ready to play** in the hub.

**What was NOT independently re-verified.** The backend suite was not re-run -- no backend file
changed. `ObjectPool`'s `accent`-tint contrast and the shared chrome's new border/shadow were judged
visually by the owner, not measured against any accessibility contrast standard.

## 2026-08-26 — feat: `line-position` archetype registered, completing 10d (C-MCL-04)

**What was built.** `line-position`, the archetype for C-MCL-04 alone -- the fourth and last
template of C-GF-03 Match, Compare, Locate. Card #3 flips from *Partly ready* to *Ready to play* on
its own (`readinessOf` computes family readiness from `SURFACE_TABLE` at call time) -- no hub file
touched. This closes out 10d, left partial since `de91132` (C-MCL-02/C-MCL-03 shipped) and 10e-0
(C-MCL-01 unblocked): all four MCL templates are now registered.

**Why this was still open.** The master work order's own §2.2 blocker was never actually about the
STEPPING MECHANISM -- that was already ruled ("discrete integer stepping, constant per-step touch
target, the line scrolls or paginates, never compresses") and `unit-stepper.tsx` was already built
generic for this reuse in 10c. What was genuinely unresolved was the INTERACTION-COST CONFOUND `de91132`'s
own Finding 2 measured and left open: unit-only stepping from 0 costs 2 taps at L1 and 34 at L5 (a
17x spread), and unlike `line-traversal` (where each unit jump IS the counting-on act being scored),
every tap past the first here is pure transit cost, assessing nothing -- exactly the SPEC section 10
confound that killed 10a's original stepper design. Finding 2 named candidate fixes without choosing
one; the owner this session picked coarse+fine stepping over unit-only (accepting the residual tap
cost) or escalating without shipping.

**The fix: coarse+fine discrete stepping, built into `unit-stepper.tsx` itself, not a new primitive.**
A new optional `coarseStep` prop adds a second `+N`/`-N` button pair alongside the existing `+1`/`-1`
pair -- `line-position` passes a fixed `LINE_POSITION_COARSE_STEP = 10` (never derived from
`interval_max` or `difficulty_level`); `line-traversal` passes nothing, so its own two-button shape
is unchanged. At L5 (target 34) this collapses 34 taps to 7 (3 coarse + 4 fine), measured and
asserted by a dedicated test. Two other additions to the shared primitive, both additive and
`line-traversal`-inert: `maxForwardSteps` (defaults to the old corruption-only
`MAX_LINE_FORWARD_STEPS`; `line-position` passes `interval_max` instead, legitimate here because
that value is the task's own stated range, not an answer to protect) and `targetForwardOffset`
(marks one tick with a distinct visual, omitted by `line-traversal`, which has no such given position
to show).

**`target_position` is the GIVEN, not the answer -- and still never rendered as a bare numeral.**
The prompt ("Move the marker to the target spot on the line") is deictic and needs a visible target;
unlike `line-traversal`'s sum, there is no way to complete the task without showing where the target
is. It renders as a marked tick on the line itself (a solid green circle, after two rounds of visual
correction -- see below), never as a printed digit next to the prompt. A dedicated leak-guard test
(`c-line-position-no-target-leak.test.ts`) proves `spec.targetPosition` is passed to exactly one
place in the surface (`UnitStepper`'s `targetForwardOffset` prop) and never interpolated into any
`AppText` node.

**A real discoverability gap, found by the owner testing at L5, fixed with a bucketed range hint.**
`UnitStepper`'s own auto-scroll only follows the MARKER (which starts at 0); with a target up to 200
units away and entirely off-screen, nothing told the child which direction or how far to go. Fixed
with `targetRangeStart`/`targetRangeEnd` -- a `TARGET_HINT_BUCKET_SIZE`-wide (5) window containing
`target_position`, computed structurally and rendered as "Target is between 30 and 35" above the
line. This narrows the search space without pinpointing the exact value, the same trade-off a paper
number line's own printed gridlines make. Bucket boundaries fall on multiples of 5 ("0-5, 5-10,
10-15"), corrected once after an initial off-by-one draft ("30-34" instead of "30-35").

**UI iteration, owner-driven from browser testing across all 5 difficulty levels:**
- The target tick went through two visual drafts before landing: a 🏁 emoji (did not render
  consistently, showed as a placeholder box) → a hollow green ring → a solid green filled circle.
- The current-position marker and its own tick ring went through a similar correction: solid red
  dot / red ring (original) → faded green dot (rejected, hard to read) → back to a solid red dot,
  but with the ring around it changed to green (accepted) → both reverted to red after the target's
  dot went solid green, since a red-ringed red dot next to a green-ringed green dot reads more
  clearly than a red dot inside a green ring. Final state: current position is entirely red (ring +
  dot), target is entirely green (ring + solid dot) -- two internally-consistent colour pairs, never
  mixed.
- A "The marker is at N" live caption was added, then removed at the owner's request in the same
  session -- the marker's own tick-label numeral already shows this.

**Shared-primitive consequence, flagged rather than left silent.** `unit-stepper.tsx` is shared with
`line-traversal` (10c, shipped and previously browser-verified). Every change above to `tickMarked`'s
ring colour and the `marker` dot's fill also applies to `line-traversal`'s own rendering, since
neither archetype-specific colour was gated behind a prop -- `line-traversal`'s marker now renders
with the same red ring + red dot combination line-position settled on, which happens to match what it
already had (red ring, red dot) after this round's reversions, so no visual regression resulted, but
this was not independently re-confirmed in the browser for `line-traversal` specifically this
session -- only reasoned about from the diff.

**Files:**
- new: `line-position-logic.ts` (pure resolver), `line-position-surface.tsx`.
- edit: `unit-stepper.tsx` (`coarseStep`, `maxForwardSteps`, `targetForwardOffset` props; `marker`/
  `tickMarked`/`tickTarget`/`targetDot` style changes, described above).
- edit: `archetype-surfaces.ts` (one import, one `SURFACE_TABLE` entry).
- edit (named exception): `c-mcl-family-surface-registration.test.ts` -- 3 tests inverted from
  asserting `line-position` has NO surface entry to asserting it now does (the fact this file
  documented changed); every other test in the file untouched.
- new tests, flat in `src/api/__tests__/`: `c-line-position-logic.test.ts`,
  `c-line-position-fail-closed.test.ts`, `c-line-position-key-set-proof.test.ts`,
  `c-line-position-prompt-text.test.ts`, `c-line-position-carries-interactive-assets.test.ts`,
  `c-line-position-no-representation-mode.test.ts`, `c-line-position-motor-constancy.test.ts`,
  `c-line-position-no-target-leak.test.ts`.

**Verification -- measured.**
- `npx tsc --noEmit` -- exit 0, throughout every iteration in this batch.
- `npm run test:contract` -- **1087 tests, 1087 passed, 0 failed**, final state. Baseline
  immediately before this batch: 999 / 999 / 0 (post-10e). Re-run after every source change in this
  batch.
- Both `MAX_INTERVAL_MAX` and the `target_position` range bound (`[0, intervalMax]`) proven by
  disabling each in place, confirming the targeted negative controls went red, restoring, confirming
  green again.
- `npx expo export --platform ios` -- succeeded; `dist/` removed after.
- **Every difficulty level looked at in a browser by the owner directly**: C-MCL-04 at L1-L5
  (interval_max 10/20/50/100/200, target_position 2/7/26/36/34), through every visual correction
  described above, all confirmed correct at the final state. Card #3 confirmed reading **Ready to
  play** in the hub.

**What was NOT independently re-verified.** `line-traversal`'s own rendering, after the shared
`unit-stepper.tsx` colour changes -- see the "Shared-primitive consequence" paragraph above. The
backend suite was not re-run -- no backend file changed.

---

## 10f -- `named-integer-fields` archetype registered, completing C-GF-04 Build and Trade (C-BT-01..04)

**What shipped.** A sixth archetype, `named-integer-fields`, registered in `archetype-surfaces.ts`,
covering all four C-BT-* templates: C-BT-01 (`target_number` -> `tens`/`ones`), C-BT-02
(`target_number` -> `hundreds`/`tens`/`ones`), C-BT-03 and C-BT-04 (`pre_tens`/`pre_ones` ->
`post_tens`/`post_ones`, the two "trade" templates). Card **#4 Build and Trade** now reads **Ready to
play** in the hub, computed by `readinessOf` from the same `SURFACE_TABLE` the task loop reads --
no hub file touched. New files: `archetypes/named-integer-fields-logic.ts` (pure resolver),
`archetypes/named-integer-fields-surface.tsx`, `primitives/named-field-row.tsx` (the labelled
multi-field entry control). Modified: `archetype-surfaces.ts` (one import + one `SURFACE_TABLE`
entry), `payload-value-labels.ts` (three payload-key label entries: `target_number`, `pre_tens`,
`pre_ones`).

**The composite-archetype proof this sub-phase owed.** One resolver covers both the 2-field shape
(BT-01/03/04) and the 3-field shape (BT-02), discriminated purely by the COUNT of `integer-field`
keys `valid_action_space` declares (`MIN_FIELDS = 2`), never by template id or key count table.
`c-named-integer-fields-no-template-branch.test.ts` source-scans the three new files for any
`C-BT-0*` literal or `game_task_template_id` read and finds none.

**Field labels are mechanically derived from the key, never a table** (master work order §3's own
`named-integer-fields` row, verbatim). `humanizeActionKey` (`named-integer-fields-logic.ts`) turns
`post_tens` into "Post Tens" by splitting on `_` and capitalising -- deliberately kept apart from
`payload-value-labels.ts`'s own `FRIENDLY_LABELS` table, which still governs PAYLOAD keys
(`target_number`, `pre_tens`, `pre_ones`) since a payload key is content the child reads, not a field
the child fills, and that table has always been allowed there. The owner was asked explicitly
(AskUserQuestion) whether to extend the payload-label table to action keys too, for friendlier
copy ("Tens now" instead of "Post Tens") -- declined in favour of the strict mechanical rule, to stay
inside the work order's letter and avoid a second name table.

**No auto-carry, no auto-borrow, no pre-fill** (work order §10f row, verbatim). Decomposing
`target_number` (BT-01/02) and performing the trade from `pre_tens`/`pre_ones` (BT-03/04) ARE the
assessed skills. Every entry field starts empty (`useNamedFieldEntry`'s buffers all seed to `''`),
nothing is derived from another field or from a payload value, and SUBMIT gates only on "every field
has a value" (required for `encodeActionPayload` to succeed at all) -- never on the fields summing to
the given number or matching the trade correctly. `c-named-integer-fields-no-client-arithmetic.test.ts`
source-scans for arithmetic performed on a payload-shaped identifier and finds none.

**C-EG-02 reaches this archetype and fails closed structurally, not by template-id refusal.**
`registry.ts` already mapped `C-EG-02` -> `named-integer-fields` before this batch (10g's own future
template, per the work order's sequence table), so registering the surface makes EG-02 reachable
before 10g has designed for it. It fails closed on its own wire shape: its `prompt_payload` carries
`direction: "read"`, a STRING, and the numbers-only payload guard every archetype since 10b has
carried rejects it -- the same class of guard, not a special case. This is deliberately NOT the
explicit `game_task_template_id === 'C-TC-02'` line `value-report-logic.ts` had to carry;
`named-integer-fields-logic.ts` stays entirely template-id-blind.
`c-named-integer-fields-eg02-fails-closed.test.ts` pins both the outcome and the reason, with a
positive control (stripping the offending key resolves fine) proving the refusal traces to that one
guard and not to hidden template-id logic.

**A new primitive was built, not an extension of an existing one -- owner decision (AskUserQuestion,
this batch).** The labelled multi-field entry control (`primitives/named-field-row.tsx`) reuses the
focus/buffer mechanism `value-token-row.tsx`'s entry mode already established, but as a deliberately
separate, copied ~15-line implementation rather than an additive mode on that file. Reasoning: the
two are different scenes (positional blanks vs. named place-value fields), and extending the shared
file would mean a later style change reaches two shipped surfaces at once -- exactly the
`unit-stepper.tsx` / `line-traversal` side effect 10d's own entry already flags. `named-field-row.tsx`
was restructured mid-batch (see "UI iteration" below) from a self-contained row-plus-keypad component
into a state hook (`useNamedFieldEntry`, keyed by field KEY not display position) plus a single-box
renderer (`NamedFieldBox`), so the surface could compose a merged layout freely without the reorder
ever risking a value landing under the wrong submitted key.

**UI iteration, entirely owner-driven from the running app (2026-08-26), in order:**
1. Initial shape: entry fields in a visually separate block below the payload row, smaller box size,
   grey dashed borders, wire-alphabetical field order (`ones` before `tens`, since the wire's own
   `valid_action_space` key order is alphabetical -- not the intuitive place-value order). Owner
   flagged all three as wrong in one pass from a C-BT-01 screenshot.
2. Corrected to: one merged row (payload token + entry fields, same box size, same label style,
   reproducing `value-report-surface.tsx`'s own shapes), fields reordered to descending place value
   (`Tens` before `Ones`) via a new `PLACE_VALUE_RANK` table scoped to display order only (state
   stays keyed by field key, so reordering can never misattribute a submitted value), and unfocused
   borders recoloured from `colors.border` to the family accent.
3. C-BT-02 (3 fields + 1 payload token = 4 columns) then overflowed that merged row: `flex: 1`
   columns inside a `flexWrap: 'wrap'` row compressed instead of wrapping -- the identical RN Web
   flex-shrink pitfall 10e's own `object-pool.tsx` header already documents, recurring in a second
   file. Owner rejected the compressed result outright ("not like that").
4. Owner's actual requested shape, arrived at over three more corrections: the GIVEN payload
   value(s) alone in their own row directly under the prompt (gap halved from the container's
   default); the entry fields as a SEPARATE row directly below that (gap halved again); box size
   reduced from `TOKEN_TOUCH_TARGET_SIZE * 1.6` to `TOKEN_TOUCH_TARGET_SIZE` alone (still above SPEC
   §10's 48px floor, and now the SAME fixed size across every template and level, never a per-scene
   resize) so the widest real row -- C-BT-02's three fields -- fits on one line without wrapping;
   field labels moved from above their box to below it; and, once both rows were reordered
   independently, the given-value row's own alphabetical order (`pre_ones` before `pre_tens`) no
   longer lined up column-for-column under the now-reordered field row (`Post Tens` before
   `Post Ones`) -- so `displayOrder` was generalised to apply the same `PLACE_VALUE_RANK` table to
   both rows, restoring column alignment (`Tens to start` above `Post Tens`, `Ones to start` above
   `Post Ones`).

**The touch-target-size reduction is a single global constant, not a per-scene one.** `PAYLOAD_TOKEN_SIZE`
(surface) and `FIELD_BOX_SIZE` (primitive) both changed from `TOKEN_TOUCH_TARGET_SIZE * 1.6` to
`TOKEN_TOUCH_TARGET_SIZE` alone, together, for every template and every level -- motor constancy
(SPEC §10) holds because C-BT-01/03/04's 3-column row and C-BT-02's 4-column row use the identical
box size; only the row's own WIDTH grows with column count, never any one target's size. Verified by
`c-named-field-row-layout.test.ts`, which asserts both constants share the same literal value.

**Verification.**
- `npx tsc --noEmit` -- exit 0 throughout every UI iteration.
- `npm run test:contract` -- green at 1187/1187 (was 1184 before this batch's 8 new test files:
  `c-named-integer-fields-logic`, `-fail-closed`, `-key-set-proof`, `-no-template-branch`,
  `-no-client-arithmetic`, `-motor-constancy`, `-no-representation-mode`,
  `-carries-interactive-assets`, `-eg02-fails-closed`, plus `c-named-field-row-layout` -- 9 files,
  net +3 tests after several were revised mid-batch to match the two-row restructure).
- Every new guard proven load-bearing by disabling it in place (the numbers-only payload guard / the
  MIN_FIELDS and MAX_FIELDS bounds / the integer-field-kind guard), confirming the targeted negative
  controls went red, restoring from a `$TEMP`-directory backup, confirming an exact diff and green
  tests again.
- `npx expo export --platform ios` -- succeeded twice (initial batch and after the UI restructure);
  `dist/` removed both times.
- **Every difficulty level looked at in a browser by the owner directly**: C-BT-01 at L1 and L5
  (target_number 3, 37), C-BT-02 at L1 and L5 (target_number 185, 586 -- the 4-column overflow case),
  C-BT-03 at L1 and L5 (pre_tens/pre_ones 0/10 and 5/12), C-BT-04 at L1 and L5 (pre_tens/pre_ones
  1/3 and 3/4), through every visual correction described above, all confirmed correct at the final
  state. A full submission (typing digits into both fields, SUBMIT enabling and advancing) was also
  confirmed working end to end. Card #4 confirmed reading **Ready to play** in the hub.

**What was NOT independently re-verified.** Nothing shared -- unlike 10d's `unit-stepper.tsx` change,
every file this batch touches or introduces is new or owned solely by this archetype
(`archetype-surfaces.ts` and `payload-value-labels.ts` were edited additively, one entry each, with
no existing entry altered). The backend suite was not re-run -- no backend file changed.

---

## 2026-08-26 — FE-B-session-ui: Component B's live session screen restyled, home navigation/layout fixes, and a new profile screen

**Scope note.** This batch is Component B frontend work only, driven entirely by the owner iterating
live against the running app in the browser (screenshots, arrows, corrections) rather than a written
work-order spec -- closer in shape to 10f's own "UI iteration" log than to a template-registration
batch. No Component C file was touched; a concurrent agent was working in `c-session/` at the same
time (`archetype-surfaces.ts`, `payload-value-labels.ts`, the `partition-allocation` archetype) and
none of its files are included in this entry or its commit.

**What shipped, `live-session-screen.tsx` (the `/session/:id` game screen):**
- Card layout matching c-session's own task panel shape: a cream card on a neutral ground, edged in
  a per-skill accent colour (`session-skill-accents.ts`, new -- B's own `skill_id`-keyed
  border/soft/text triple, mirroring `game-family-accents.ts`'s pattern without depending on it).
  The skill pill is centred on the card's own x-axis, in the same fixed header row as the exit (X)
  control, and now tints to the skill's own colours instead of a fixed coral.
- Hint control moved from an inline "I NEED A HINT" pill to a top-right circle matching the exit
  button's size and corner, showing only the MOST RECENT hint (a deliberate change from every
  received level staying visible, at the owner's request) in a fixed-`minHeight` box.
- The answer pad centres in the leftover space between the prompt card and the footer (`answerCenter`,
  `flex: 1` inside a `flexGrow: 1` scroll container).
- The correct/incorrect/timeout outcome is now a floating popup (50% width/height of the card's own
  working area, `expo-blur` behind it, no background fill -- just a full-opacity colour-matched glow
  as its edge) instead of an inline banner; the `outcome==='timeout'` case was found mid-batch to
  fall through both style branches (`&&` instead of a ternary) leaving RN's default black shadow --
  fixed to a ternary matching the icon/text logic already in place.
  `outcomeView`'s `incorrect` copy had its second sentence ("...you can try as many times as you
  like") removed at the owner's request; `canTryAgain: true` alone still drives TRY AGAIN.
- CHECK MY ANSWER / NEXT QUESTION / TRY AGAIN restyled to match c-session's flat `SubmitButton`
  (no border, no 3D press effect, `opacity: 0.72` on press) and moved into a fixed footer box below
  the ScrollView, whose gap to the card's own bottom edge is measured live via `onLayout` (three
  `onLayout` calls -- the skill pill, the scroll wrapper, and the prompt card -- combined in one
  shared coordinate space) to exactly equal the pill-bottom-to-prompt-card-top gap, per the owner's
  request that the two match, rather than a static guessed constant.
- Background: a two-colour gradient (`expo-linear-gradient`), the two colours drawn at random each
  question from the same five "game-type" colours `learner-home-screen.tsx`'s own path uses,
  excluding the current skill's own accent so the background can never coincide with the card's
  border, rotating continuously clockwise around the screen's own centre (`react-native-reanimated`,
  45s/revolution). The rotating gradient's own bounding box is sized to the screen's measured
  diagonal (`sqrt(w²+h²)`, via `onLayout`), not a flat `200%` guess -- the flat guess under-covered a
  tall, narrow phone screen's width and showed up as a hard-edged crop in two opposite corners at
  certain rotation angles; found and fixed from an owner screenshot mid-batch.
- Progress bar restyled to a filled pill track (was plain "3 of 8" text); its gap to the prompt card
  specifically doubled at the owner's request (`promptCardAfterProgress`, additive to the scroll's
  own uniform `gap`, applied only when a progress bar is actually rendered).
- `live-session-logic.ts`'s `SessionPlan` gained a `skillId` field alongside the existing formatted
  `skillLabel`, since the accent/pill colouring needs the raw wire id, not the display string.

**What shipped, `learner-home-screen.tsx` (two rounds of navigation/layout bugs, both owner-reported
from the running app):**
1. `openBLearning` (the hero button) was changed to always route through `/prepare`, even when a
   session is already active (previously it skipped straight to `/session/:id` when one was open) --
   restoring the prepare-first flow the owner said used to exist. The "Your Session" card's own
   current-question node then got a SEPARATE handler, `resumeCurrentQuestion`, that DOES skip
   straight to the session: it is reached only when `sessionState.kind === 'in-progress'` already
   (this screen has already confirmed via a live `GET .../summary` read exactly which session and
   question is open), so routing that back through `/prepare`'s own readiness check would be
   redundant on every tap.
2. "Buttons glitch on returning to home" -- root cause: this screen fully remounts on every return
   (`router.replace`, not a stack pop), and `measuredViewportHeight` starts at 0 for one frame, so
   the percentage-positioned path-stage buttons render once at a rough fallback position/size before
   snapping to the real one the instant `onLayout` reports the true height. Fixed with a
   `layoutReady` flag that keeps the ScrollView at `opacity: 0` (still laid out and measured, not
   `display: none`) until the first real layout has landed.
3. "Can't scroll up to see the hero again" -- root cause: `scrollEnabled` was set to `false`
   permanently the first time the hero was scrolled past, as a `handleGestureSettle` side effect.
   Removed entirely; scrolling now stays enabled always. Decoupled from that: `startScrolledToPath`
   (a `useRef`, read once per mount from the module-level `heroDismissedThisAppSession` flag) still
   decides whether THIS mount opens pre-scrolled past the hero, applied exactly once via a new
   `initialScrollAppliedRef` guard so it can never re-fire and yank the child back down after a
   deliberate manual scroll-up.
4. The hero's own CTA button press now also sets `heroDismissedThisAppSession = true` (previously
   only a scroll-past did), and a new cleanup-only `useEffect` sets the same flag on ANY unmount of
   this screen -- covering the Play tab's own `router.replace('/(learner)/play')`, which had no other
   hook into this screen's dismiss logic and was the specific gap the owner reported last.

**What shipped, new profile screen (`/profile`, previously `LearnerEmptyTabScreen` -- deleted, now
unreferenced anywhere).** `learner-profile-screen.tsx`: name (first name, via the header greeting),
classroom and grade (only rendered once an APPROVED `classroomMembership` exists -- the identical
derivation the prep screen already uses, so the two screens can never disagree about whether a
classroom is showing), gender, and a LOG OUT button (`useAuth().signOut()`, same pattern as the two
existing sign-out call sites). Gender required a new field, `profileGender`, added to
`auth-context.tsx`: the backend's `LearnerProfileResponse` carries no gender field at all -- it is
captured once at sign-up into Supabase's own `user_metadata` (alongside `display_name`) and read back
the same way `readDisplayName` already reads the name, via a new `readGender`. Wired into every place
`profileName` was already being set or cleared (sign-in, sign-up, sign-out, session-expiry, the
`SIGNED_OUT` auth-state listener) so the two can never drift out of sync.

**`firstNameOf` (`src/utils/display-name.ts`) now capitalises the first letter** of the returned
token (`"yass"` -> `"Yass"`), leaving the rest exactly as typed (so a name with its own internal
capitalisation, e.g. `"McKay"`, is not fought). All five call sites (home, game hub, profile x2, the
prep screen) share this one helper, so the fix applies everywhere at once with no per-screen change.
Two new test cases added to the existing `display-name.test.ts`.

**Verification -- measured.**
- `npx tsc --noEmit` -- exit 0 after every edit in this batch (checked incrementally, not just at the
  end), filtering only pre-existing, unrelated errors in the concurrently-edited `c-session/` tree
  (`unit-stepper.tsx`'s `targetDot` property, not this batch's file, not fixed here).
- This project's own `node --import tsx --test` suite (Component B has no equivalent of C's
  `npm run test:contract` battery): `live-session-logic.test.ts`, `session-advance.test.ts`,
  `session-hints.test.ts`, `session-results.test.ts`, `session-timeout.test.ts` -- 78/78 passed,
  re-run after every source change touching `live-session-screen.tsx` or `live-session-logic.ts`.
  `home-session-progress.test.ts` -- 20/20, then 24/24 with `resume-decision.test.ts` added to the
  same run, then 27/27 once `display-name.test.ts` gained its two new cases -- re-run after every
  `learner-home-screen.tsx` / `auth-context.tsx` / `display-name.ts` change.
- `npx expo install expo-blur` / `expo-linear-gradient` -- both resolved to SDK 54-compatible
  versions by the Expo CLI itself, not hand-pinned.
- No RNTL/browser rendering was performed by the agent (this environment has no display); every
  visual claim in this entry (crop location, glitch, gradient look, popup shadow visibility) was
  confirmed by the owner directly from the running app, screenshot by screenshot, in the same
  iterative loop 10f's own "UI iteration" section documents -- several stated fixes (the corner crop,
  the black timeout shadow, the glitch, the scroll lock) were themselves owner-reported defects found
  exactly that way, not anticipated by the agent in advance.

**What was NOT independently re-verified.** The backend suite was not re-run -- no backend file
changed. Component C's own `c-session/` files, concurrently modified by a separate agent in the same
working tree, were deliberately left out of this batch's diff and its commit entirely -- confirmed via
`git status`/`git diff --stat` immediately before staging, matching FE-surface-remount-key's own
precedent for excluding concurrent, unrelated in-flight work from a commit.

**Provenance.** Commit `2de9da9`, "Component B: game-styled session UI, home nav fixes, and profile
screen" -- 12 files changed (`app/(learner)/profile.tsx`, `package.json`/`package-lock.json`,
`display-name.test.ts`, `auth-context.tsx`, `learner-home-screen.tsx`,
`learner-empty-tab-screen.tsx` deleted, `live-session-logic.ts`, `live-session-screen.tsx`,
`session-skill-accents.ts` new, `profile/learner-profile-screen.tsx` new, `display-name.ts`).

---

## 10g -- `partition-allocation` archetype + the C-EG-02 array grid, completing C-GF-07 Equal Groups and Arrays

**What shipped.** The seventh of eight archetypes. Two parts:

- **`partition-allocation`** (new): C-EG-01 (`number_of_groups`/`group_size` -> `groups: list[int]`)
  and C-SF-01 (`recipient_count`/`total` -> `allocations: list[int]`), one resolver, no template
  branch. `ValueTokenRow`'s own `display-with-entry` mode is reused UNMODIFIED, exactly as its own
  header and master work order §5A already committed to -- no new label prop, no
  `partition-allocation`-specific behaviour added to that file. `C-SF-02` also resolves to this
  archetype id (its own `groups: list[int]` collection) but fails closed structurally on a
  type-level discriminant: the presence of `submitted_group_count: int` alongside the collection
  marks the variable-bin-count shape §2.3 names as 10h's own falsification test, and pre-building
  that path now would spoil it.
- **The C-EG-02 array grid** (extends 10f's `named-integer-fields`, reversing its own deliberate
  refusal): a new `array-grid.tsx` primitive renders a read-only r x c grid; `rows`/`cols` are read
  by name from `prompt_payload` and consumed STRUCTURALLY as grid dimensions rather than rendered as
  numeral tokens, because both are simultaneously GIVEN and declared `valid_action_space` keys --
  printing either would leak 2 of the 3 answers. `direction` (`"read"` L1-4, `"build"` L5, driving
  different `prompt_text`) is admitted through a single narrow, named string exception and carried
  in the spec, rendered nowhere, branched on nowhere -- 10a's own standing ruling for
  `C-NP-04.direction`, applied unchanged.

**Files.** New: `archetypes/partition-allocation-logic.ts`, `archetypes/partition-allocation-surface.tsx`,
`primitives/array-grid.tsx`. Modified: `archetype-surfaces.ts` (two entries),
`payload-value-labels.ts` (`group_size`, `total`), `archetypes/named-integer-fields-logic.ts` (the
`rows`/`cols`/`direction` extension), `archetypes/named-integer-fields-surface.tsx` (the grid render
branch and the equation-row layout below), `motor-constants.ts` (`GRID_CELL_SIZE`/
`GRID_CELL_SPACING`).

**Named-exception test edit.** `c-named-integer-fields-eg02-fails-closed.test.ts` previously asserted
C-EG-02 fails closed at every level -- that fact is exactly what this batch changes. Inverted in
place (kept its name, following 10d's own `c-mcl-family-surface-registration.test.ts` precedent for
the identical situation) to assert resolution instead, with the corrected reasoning documented in
its own header.

**Shared-primitive consequences, all owner-directed, all re-verified in the browser.** Testing
C-EG-01 at difficulty 5 (5 entry slots) surfaced three issues in `value-token-row.tsx` -- the SAME
primitive NP-01..04 (10a) already ships on:

1. **A latent RN Web flex-shrink wrap bug**, the same class `object-pool.tsx`'s own header already
   documents: `flex: 1` columns inside a `flexWrap: 'wrap'` row compress to fit one line instead of
   wrapping. Fixed by halving `entryTokenRow`'s gap (`TOKEN_SPACING` -> `TOKEN_SPACING / 2`).
2. **The entry-slot token size itself needed splitting in two.** `display-with-entry`'s tokens
   (NP-01..03, and this batch's own `partition-allocation` reuse) are now pinned to
   `TOUCH_TARGET_MIN_SIZE` (48, SPEC §10's own accessibility floor -- the smallest a real touch
   target may shrink to) so 5 entry slots fit one row; `reorder`'s draggable tokens (NP-04 only) stay
   at the original, larger `TOKEN_TOUCH_TARGET_SIZE` (56), per the owner's own separate request that
   NP-04's cards read "a bit bigger." Splitting this surfaced a **latent bug from the size's brief
   single-constant period**: `TOKEN_STRIDE` (driving the reorder-mode drag gesture's slot-movement
   math) would have silently used the entry token's size rather than the dragged token's own the
   moment the two diverged -- caught and fixed (`TOKEN_STRIDE` now derives from
   `TOKEN_TOUCH_TARGET_SIZE` specifically) before it ever shipped as a real bug.
3. **`entryTokenRow` was missing `justifyContent: 'center'`** -- found testing C-SF-01's own
   2-slot row, which left-aligned rather than centering under the prompt/payload token above it.

**A genuinely pre-existing gap, found and fixed in the same pass.** The owner reported NP-04's
drag-to-reorder simply did not respond in the browser. Root cause: `app/_layout.tsx` never wrapped
the app root in `GestureHandlerRootView`, which `react-native-gesture-handler` requires on every
platform including web for gestures to register touches at all -- missing since 10a shipped the
primitive, invisible until someone actually tried to drag in a real browser (nothing in this
repository can mount a tree to catch it structurally). Fixed with one wrapper in the root layout.
Separately, `DraggableToken`'s `.activateAfterLongPress(GESTURE_LONG_PRESS_MS)` (400ms) is by design,
not a bug -- a deliberate discoverability gap with a mouse rather than a touchscreen, documented
here in case it resurfaces.

**A second shared-surface layout fix.** NP-04's own `ArrangeSceneSurface` used the same `container`/
`justifyContent: 'space-between'` shape the entry scene (NP-01..03) uses, which -- with only ONE
middle child (the token row) -- concentrated ALL leftover vertical space into a single gap above and
below it, producing large empty bands the owner flagged. Fixed with scene-scoped styles
(`arrangeContainer`/`arrangeTopBlock`/`arrangeRowWrapper`), left `container`/`promptText` (still used
by the entry scene) completely untouched.

**The C-EG-02 equation row, `named-integer-fields-surface.tsx`'s own addition.** The generic wrapped
`fieldsRow` every other named-integer-fields template uses put C-EG-02's "Submitted Product" field on
its own line -- that label's own unabbreviated width, not a wrapping bug in the general sense, was
wider than the row's remaining space once "Cols"/"Rows" took their share. A dedicated
`EquationFieldsRow` renders "Cols x Rows = Product" as one non-wrapping row instead, using a
DISPLAY-ONLY label override (`EQUATION_FIELD_LABEL_OVERRIDE`, scoped to this one component) that
shortens "Submitted Product" to "Product" -- `spec.fields`' own resolver-produced label stays
"Submitted Product", unchanged, exactly as `humanizeActionKey` produces it; only this one row's own
rendering substitutes the shorter text.

**Verification.**
- `npx tsc --noEmit` -- exit 0 throughout every UI iteration.
- `npm run test:contract` -- green at 1298/1298 (was 1187 before this batch's ~17 new test files
  across both parts, net +111 tests after several existing files were revised mid-batch: the eg02
  inversion, the fail-closed table's new grid/direction controls, and the motor-constancy file's
  updated `NamedFieldBox` call-site count).
- Every new guard proven load-bearing by disabling it in place (partition-allocation's
  fixed/variable-shape discriminant, its bin-count-validity and collection-vocabulary guards; the
  grid-dimension-validity, direction-string, and rows/cols-symmetry guards), confirming the targeted
  negative controls went red, restoring from a `$TEMP`-directory backup, confirming an exact diff and
  green tests again.
- `npx expo export --platform ios` -- succeeded across all three UI-iteration rounds; `dist/` removed
  each time.
- **Every difficulty level looked at in a browser by the owner directly, in two passes as planned**:
  C-EG-01 at L1 and L5 (2 groups of 2, 5 groups of 4 -- the 5-slots-on-one-row case), C-SF-01 at L1,
  C-EG-02 at L1 and **L5** (the only `"build"` row, confirming its own different `prompt_text` and a
  5x5 grid), C-EG-03 spot-checked unchanged. Re-verification of the shared-primitive changes: NP-01
  (twice, after the size split and again after the centering fix), NP-04 (after the gesture-root fix,
  the token-size split, and the layout restructure -- drag-to-reorder confirmed working end to end).
  Card #7 confirmed reading **Ready to play**; card #8 confirmed still not-ready.

**What was NOT independently re-verified.** NP-02/NP-03 (10a's other two entry-scene templates) --
they share `value-token-row.tsx`'s `display-with-entry` mode with NP-01, which WAS re-verified, but
were not separately opened in the browser this session.
