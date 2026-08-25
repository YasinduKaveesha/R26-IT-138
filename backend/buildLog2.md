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
