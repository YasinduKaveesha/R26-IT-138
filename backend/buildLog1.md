# Component B Backend Build Log (continued)

> `backend/buildLog.md` is closed as of its final entry, **FE-0c** (2026-07-29), and must not be
> appended to or edited further. This file, `buildLog1.md`, is its rotation and continues the same
> living, append-only development audit log from FE-0d onward, under the same rules: future work
> is appended as a new dated phase or batch, earlier entries here are never removed, rewritten, or
> silently altered.

---

## 2026-07-29 — FE-0d: close the authorization-bypass hole (BE-G2 dependency)

**Why.** Two shortcuts introduced during Component B page construction had quietly become
authorization bypasses rather than the narrow dev conveniences they were meant to be:
`app/_layout.tsx` forced `learnerAccess: true` / `onboarding: false` whenever
`EXPO_PUBLIC_APP_ENV === 'development'`, and `app/index.tsx` unconditionally redirected every
bootstrap to `(learner)/home` under the same condition — before `useAuth()`'s real `status` was
even consulted. Both meant that in any development build, the entire learner-activation path
(BE-G1's grade assignment, BE-G2's classroom-membership approval, FE-1a's onboarding screens) was
silently unreachable and untested by anyone running the app the normal way. This batch removes
both bypasses and, for the first time, actually exercises FE-1a end-to-end against a live backend.

**The governing distinction for this batch, stated once so it can be pointed back to:** a fixture
flag (`EXPO_PUBLIC_COMPONENT_B_DEV_FIXTURE`, still present and untouched in `component-b-api.ts`)
may legitimately substitute response *data* for a screen that has nothing else to render against
yet. It must never flip an authorization *decision*. The two removed bypasses both violated this;
the fixture flag itself does not and was left exactly as it was.

**Part 0 — closed the optionality hole FE-0c opened.** FE-0c's six new `ComponentBApi` methods
(`getActiveSession`, `selectOpportunity`, `submitResponse`, `requestAssist`,
`completeOpportunity`, `getSessionSummary`) were typed optional solely because `createFixtureApi`
didn't implement them. This batch makes all six required on `ComponentBApi` and implements them in
`createFixtureApi` as immediate `ApiClientError('unavailable', …)` throws — no delay, no fake
payload, no fixture branching by flag value. Comment left in place: the fixture covers the prep
screen's readiness/start path only; the session loop is deliberately unimplemented so a fixture
run can never masquerade as a real session past the prep screen.

**Part 1 — removed the two bypasses.**
- `app/_layout.tsx`: deleted the `componentBPagePreview` constant and its two usages; `learnerAccess`
  is now exactly `authorized || status === 'preview'` (the pre-existing, explicitly user-triggered
  `continueToComponentBPreview()` preview path in `auth-context.tsx` — untouched, out of scope, and
  not an automatic env-keyed bypass) and `onboarding` is exactly `status === 'onboarding'`.
- `app/index.tsx`: deleted the `if (process.env.EXPO_PUBLIC_APP_ENV === 'development') return
  <Redirect href="/(learner)/home" />` block entirely. `BootstrapRoute` now always routes off the
  real `useAuth()` status: `checking` → spinner, `authorized`/`preview` → home, `onboarding` →
  onboarding, everything else → sign-in.

**An incidental, in-scope fix required to get `tsc` green — not part of the bypass removal
itself.** `app/index.tsx`'s onboarding redirect (`<Redirect href="/(onboarding)" />`) has apparently
never been type-checked strictly before: Expo Router's generated route-literal union
(`.expo/types/router.d.ts`) includes only fully-qualified leaf paths
(`` `${'/(onboarding)'}/index` ``, `/index`, etc.), never the bare group-index shorthand
`/(onboarding)` itself, even though that shorthand is a valid runtime route that resolves to
`app/(onboarding)/index.tsx`. This was caught the hard way during Run 3 below: the first fix
attempt changed the href to `/(onboarding)/index` to satisfy `tsc`, which typechecked cleanly but
produced a real "Unmatched Route" screen at runtime — a live regression, caught only because Run 3
was actually driven against a running app rather than assumed from the type system. Reverted to
`/(onboarding)` (confirmed live, see Run 3) and resolved the type error with an explicit
`as Href` cast plus a comment naming this as a known typed-routes gap, not an invalid route.
**Corrected in-flight, not shipped as a regression** — recorded here because a future editor
tightening `tsc` again might otherwise "fix" this the same wrong way.

**Part 2 — standing guard.** New `frontend/src/api/__tests__/no-auth-bypass.test.ts`: asserts
neither `app/_layout.tsx` nor `app/index.tsx` contains the literal string
`EXPO_PUBLIC_APP_ENV`. Grep-as-a-test is inelegant; the test file says so in its own comment,
specifically so nobody deletes it for being ugly — it is standing in for the fact that neither file
has any other structural way to prevent this exact regression class (an env-keyed shortcut
reintroducing an authorization decision) from coming back.

**Verification — static (all from `frontend/`):**
- `npx tsc --noEmit` — clean, no errors.
- `npm run lint` — clean, no errors.
- `npm run test:contract` — **53 passed, 0 failed** (51 pre-existing tests unregressed, 2 new).

**Verification — three live runs against the real running backend (`docker compose`) and real
Supabase auth, driven through an actual browser (Playwright) against `expo start --web`, per the
BE-G2 dependency this batch has (needed the fixture learner's credentials now that the bypass
that made verification unnecessary is gone):**

*Local-only test-environment note (nothing shipped):* `expo start --web` needed
`EXPO_PUBLIC_API_BASE_URL` overridden to `http://localhost:8000` (the committed `.env.local`
points at `10.0.2.2`, the Android-emulator loopback alias, unreachable from a browser) — passed as
a process-level env override, no file changed. The backend's CORS config (`backend/.env`'s
`CORS_ALLOWED_ORIGINS`, `app/main.py`'s `allow_headers`) also had to be widened temporarily to
admit the web origin and the app's `X-Mobile-App-Version` header, neither of which a native app's
CORS-exempt requests ever need. Both were reverted immediately after the three runs completed and
the container rebuilt back to its original state; `git status` confirms zero diff in
`backend/app/main.py`, and `backend/.env` (gitignored, never committed) is back to its
pre-existing single line. No production or committed configuration changed as a result of this
verification.

1. **Signed out → lands on `(auth)/sign-in`, not home.** Confirmed: a fresh page load with no
   session landed on `/sign-in`.
2. **BE-G2 fixture learner → reaches `(learner)/home`.** Signed in as
   `dev-fixture-learner@example.com` (BE-G2's pre-provisioned, APPROVED Grade-2 learner) and landed
   directly on `/home`, greeted "Hi, FIXTURE Learner G2!".
3. **A fresh Supabase user → reaches `(onboarding)`, completes name → join code → pending, then
   approve → reaches home — this is the first real regression test FE-1a has ever had, and it
   passed.** Created a brand-new account (`fe0d-verify-run3@example.com`) through the app's own
   sign-up form. Landed on `/(onboarding)/welcome` (confirming BootstrapRoute's real onboarding
   branch, not the removed bypass); the name field was pre-filled from signup and `CONTINUE`
   advanced to `/(onboarding)/teacher-link`. Minted a fresh classroom invite for the existing
   `FIXTURE Grade 2` classroom via the fixture teacher's credentials (the same
   `POST /api/v1/classrooms/{id}/invites` call `dev_fixture_learner.py` itself makes), entered the
   resulting join code in the app, confirmed the resolved classroom name, and landed on
   `/classroom-status` showing "Waiting for your teacher to approve" (a real `PENDING`
   `classroom_membership`, confirmed via the teacher's own membership-requests listing).
   Approved it via `POST /api/v1/classroom-memberships/{id}/approve` as the fixture teacher — the
   same mechanism `dev_fixture_learner.py`'s `ensure_membership_approved` uses, applied here to a
   fresh learner identity the script itself doesn't manage. `classroom-status-screen.tsx` fetches
   membership status on mount and pull-to-refresh only (no polling, per `frontend.md 15.10`), so a
   plain re-sign-in (rather than a native pull-to-refresh gesture, impractical to drive from a
   browser) re-triggered the check; the app landed on `/home` immediately, greeted "Hi, FE0D Verify
   Learner!". **No FE-1a defect found** — the full activation path (BE-G1's grade assignment,
   BE-G2's approval mechanism, FE-1a's onboarding screens, and this batch's bypass removal) holds
   together end-to-end.

**One piece of user-facing feedback noted during Run 3, out of scope for this batch and not
acted on:** the sign-up screen's gender field (`sign-in-screen.tsx`, not one of this batch's four
scoped files) currently offers four options (Female / Male / Non-binary / Prefer not to say); the
user flagged during live verification that it should offer only Female / Male. Left untouched —
recorded here so it isn't lost before whichever batch next touches that screen.

**Files touched:** `frontend/src/api/component-b-api.ts`, `frontend/app/_layout.tsx`,
`frontend/app/index.tsx`, `frontend/src/api/__tests__/no-auth-bypass.test.ts` (new),
`backend/buildLog1.md` (new — see rotation note above). No file under `backend/app/` left modified
(the temporary CORS/header changes made purely for local live verification were fully reverted).
`backend/buildLog.md` was not touched, per the rotation.

Left uncommitted for Yasindu. Not run: any git command that mutates state.

---

## 2026-07-29 — Post-FE-0d housekeeping: gitignore allow-list correction + sign-up gender narrowing

Two small out-of-batch changes made directly, both authorized by Yasindu during FE-0d review.

**1. `.gitignore` allow-list — silent governance-record loss (the substantive one).**
`.gitignore:29` ignores all `*.md` behind an explicit allow-list. `backend/buildLog.md` is
allow-listed; `backend/buildLog1.md` was not. The FE-0d entry above therefore existed only on
disk and would never have reached the repository — the rotation instruction was followed
correctly and the result was still invisible to git. The same defect had been latent since BE-G2:
`backend/scripts/README.md`, the file carrying the mandatory *"delete this directory when FE-1b
lands"* notice, was likewise ignored. Both are now allow-listed with comments explaining why each
is tracked. Verified with `git check-ignore` (exit 1 for both) and `git status` (both now appear
as untracked rather than vanishing).

Worth noting for future rotations: an append-only log whose file is gitignored fails silently and
in exactly the direction that destroys the audit trail. Any future `buildLog2.md` needs the same
allow-list line added at rotation time, not after.

**2. Sign-up gender options narrowed to Female/Male.**
`Gender` in `frontend/src/auth/auth-context.tsx` went from
`'female' | 'male' | 'non_binary' | 'prefer_not_to_say'` to `'female' | 'male'`, and
`genderOptions` in `frontend/src/features/auth/sign-in-screen.tsx` from four entries to two.

Recorded honestly, because the finding is broader than the change: the field is **write-only**.
`auth-context.tsx` writes it into Supabase `user_metadata` at signup and nothing — frontend or
backend — ever reads it back. The backend has zero references to gender; `ProfileCreateRequest`
is `{name}` only. Narrowing also removes `prefer_not_to_say`, the field's only opt-out, making
disclosure mandatory for data that currently has no consumer and no documented purpose. This
trade-off was raised before the change and the narrowing was reaffirmed; it is implemented as
asked. If gender is later needed as a research covariate it should get a real backend column and
a stated purpose rather than continuing to accumulate in auth metadata.

**Verification (from `frontend/`):** `npx tsc --noEmit` exit 0; `npm run lint` clean;
`npm run test:contract` **53 passed, 0 failed** (unregressed).

**Files touched:** `.gitignore`, `frontend/src/auth/auth-context.tsx`,
`frontend/src/features/auth/sign-in-screen.tsx`, `backend/buildLog1.md`.

Left uncommitted for Yasindu. Not run: any git command that mutates state.

---

## 2026-07-29 — FE-2a: resume detection, and deleting three promises the app could not keep

**Why.** Two unrelated problems lived in the same screen. First, the prep screen had no resume
affordance at all: every visit called `startSession`, and while that is safe by construction
(`POST /api/v1/b/sessions` never 409s on an existing session — `b_session_lifecycle.py:185-194`
takes an advisory lock, finds any starting-or-active session for the learner, and returns it with
`201` regardless of idempotency key), the child had no way to *see* "Resume" before tapping; they
would only discover it after. Second, and unrelated to resume, the screen made three specific
promises to a child that the backend cannot currently keep: a lesson identity ("Counting") that
does not exist before a session starts, a hints affordance that 409s for the overwhelming majority
of templates, and a retry guarantee the app has no approved policy to back. This batch fixes the
first and removes the second — treating both as correctness work, not a redesign.

**Part 1 — resume detection.** `GET /api/v1/b/sessions/active` is treated strictly as a UX
affordance, never a correctness requirement, which is what makes the whole design safe:
- New `resolveResumableSessionId(api, accessToken)` (exported from the screen — pure, no React,
  no rendering): calls `api.getActiveSession`, returns the session id only when
  `session !== null && session.state === 'active'`, and returns `null` on any thrown error. The
  catch is unconditional and silent by design — commented in place — because a failed or stale
  read here is self-correcting: if a session actually exists, starting "a new one" anyway just
  returns it (see the idempotency behavior above), so the child still lands in the right place
  either way. No new error phase was added for this path; the existing 10-state phase machine
  (`checking-identity` through `technical-failure`) was extended, not rewritten.
- Wired into `checkReadiness`: immediately after a successful readiness check sets `phase` to
  `'ready'`, and only then, the resume check runs (skipped entirely for the fixture — see below) —
  fetches an access token, calls `resolveResumableSessionId`, and stores the result in new
  `resumableSessionId` state. When a session is found, `saveActiveSessionId` is called immediately
  (not deferred to a tap), so Batch 13's `clearActiveSessionId` on exit always has a current value
  to work with, matching the store's existing "keep the local hint fresh" discipline from FE-0b.
- `startAdventure`: when `resumableSessionId` is set, tapping the (now "Resume Adventure") button
  routes straight to `/(learner)/session/[sessionId]` via a new shared `navigateToSession` helper
  (factored out of the old `openActiveSession`, which now delegates to it) — `sendStartCommand`,
  and therefore `POST /api/v1/b/sessions`, is never called on the resume path.
- `loadActiveSessionId()` (the FE-0b local-storage reader) was deliberately **not** used to make
  this decision — the stored id is a hint that can go stale (a completed or abandoned session
  would route the child into a dead screen); the server via `getActiveSession` is the only
  authority on what is actually resumable. `loadActiveSessionId` is not called anywhere in this
  file; only `saveActiveSessionId`/`clearActiveSessionId`-adjacent writes happen here.
- **Fixture handling is an explicit skip, not a swallowed error.** FE-0d made
  `createFixtureApi.getActiveSession` throw `ApiClientError('unavailable', …)` by design (the
  fixture covers the prep screen's readiness/start path only, deliberately not a fake session
  engine). Calling it unconditionally would still "work" — `resolveResumableSessionId`'s catch
  would just turn it into `null`, i.e. Start — but that is an accident of the catch block matching
  the fixture's designed-in failure, not a real "no session" answer. Wrapping the resume check in
  `if (!fixture)` keeps that distinction visible in the code instead of hiding a real future
  regression (e.g. the fixture starting to implement this call) behind a catch block that would
  swallow it identically either way.
- Resolved the stale comment this batch was named for: `openActiveSession`'s old "Resume/recovery
  … is deferred to FE-2" note is gone; it now explains why a non-`'active'` `SessionCommandResponse`
  state is only ever reached from the start-a-new-session path, never from resume (which only ever
  targets a session `resolveResumableSessionId` already confirmed is `'active'`).

**An in-flight correction caught during live verification, not shipped as a regression.** No code
change was needed to satisfy this correction — it surfaced and was caught entirely within this
batch's own verification, before anything was left in a broken state, so it is recorded here for
visibility rather than as a fix to something that shipped wrong. (No such issue actually arose in
this batch's `tsc` run — FE-0d's `app/index.tsx` typed-routes gap does not recur here, since this
batch touches no `<Redirect>` call. Noted only to confirm the pattern was checked for and not
present.)

**Part 2 — deleted three promises the app could not keep, not "removed placeholder content."**
Each of the following was a specific, checkable claim, verified false before deletion, not a
generic cleanup:
1. **`previewLesson` (`{skillId: 'counting', skillLabel: 'Counting'}`) and both its uses** — the
   hero subtitle ("Let's start your **Counting** adventure") and the `lessonCard`'s skill row. No
   pre-session lesson identity exists anywhere in the contract; `OpportunitySelectionService`
   (`app/application/opportunity_selection.py`) picks the skill *after* a session starts, adaptively,
   from the learner's seven-skill BKT state. Promising "Counting" to a child when the server may
   serve subtraction is not a simplification of real data, it is a fabricated one — deleted, not
   relocated.
2. **"Hints available — Get helpful hints anytime."** Verified false for the overwhelming majority
   of sessions: hint requests 409 for 34 of 36 templates (governed-hint availability is
   template-scoped and most templates have none configured yet). A blanket "available" claim is
   true for roughly 6% of sessions.
3. **"You can try again — Learn at your own pace."** Attempt-limit behavior is an unapproved
   placeholder (BEplan's safe-progress policy is architecturally GATE-B UNRESOLVED, per
   `app/domain/b_completion.py`'s own module docstring) — the app has no approved policy to point
   to and cannot guarantee this to a child.

The whole `lessonCard` block was deleted (not just the skill row), since the skill it displayed was
its only content. That also removed the grade-badge comment at the card's old bottom edge
("Grade badge removed: no `grade` field exists anywhere reachable from the frozen v1 contract") —
which was itself factually stale as of FE-0c: `grade` **is** reachable, on
`OpportunityPresentationResponse`/`OpportunityPresentationFields`. The comment was not relocated or
corrected; it died with the card it was explaining, since nothing in this batch reads `grade` and
inventing a new place to park a now-moot comment would be scope creep.

The hero subtitle was rewritten to make no lesson claim at all ("Let's start your adventure"). The
readiness `PreparationItem` — driven by the real phase machine, not a claim about the backend's
capabilities — was kept unchanged, now the preparation card's only item. Per the batch's own
instruction, the resulting visual gap was **not** filled with new content: `preparationCard` is
`flex: 1` and absorbs it; inventing replacement copy to pad the space would have reintroduced
exactly the class of unverifiable claim this batch exists to remove.

**Dead styles deleted:** `lessonCard`, `lessonColumn`, `lessonIcon`, `lessonLabel`, `lessonValue`,
`skillIcon`, `heroSkill`, `heroSkillCompact` — confirmed via lint (`expo lint` via `eslint-plugin-react-native`'s
unused-styles rule would have caught any missed).

**Verification (all from `frontend/`):**
- `npx tsc --noEmit` — clean, no errors.
- `npm run lint` — clean, no errors.
- `npm run test:contract` — **57 passed, 0 failed** (53 pre-existing tests unregressed, 4 new).
  New `frontend/src/api/__tests__/resume-decision.test.ts` tests `resolveResumableSessionId` as a
  pure function — active session → returns the id (Resume); `session: null` → `null` (Start); a
  `completed`/`abandoned` session → `null` (Start, both states exercised); a thrown error → `null`
  (Start, degrades silently). No rendering, no RNTL (Batch 15's territory) — this file reached the
  screen's exported pure function the same way FE-0b's store test reached its target: by
  monkeypatching `Module.prototype.require` to stub every React Native/Expo/image-asset specifier
  the screen (and its transitive dependency tree — `auth-context`, `supabase`, `secure-storage`,
  `app-text`, `learner-tab-bar`) pulls in at module-load time but that `resolveResumableSessionId`
  itself never touches (it only calls the `api` parameter it is given). Isolated to this one test
  file's module registry; `node --test` runs each test file in its own worker/process.

**Verification — five live runs against the real running backend and the BE-G2 fixture learner,
driven through an actual browser (Playwright) against `expo start --web`, same local-only CORS/API-base
test-environment setup as FE-0d (widened `CORS_ALLOWED_ORIGINS`/`allow_headers` and an
`EXPO_PUBLIC_API_BASE_URL` override, both reverted immediately after; `git status` confirms zero
diff in `backend/app/main.py` and `backend/.env` is back to its original single line):**

One environment snag hit and resolved before these runs: a stale `expo start --web` process from
the FE-0d session was still holding port 8082 with the original (unreachable-from-a-browser)
`.env.local` API base baked in, so the first sign-in attempt silently called `10.0.2.2:8000`
instead of the intended override and failed with no CORS error at all (confirmed via
`browser_network_requests` — the request never left for the right host). Killed the stale process,
restarted cleanly on the same port with the override, and all five runs below are against that
clean instance.

1. **No active session → Start → lands in a session.** Ran the fixture script fresh (no
   `--keep-session`, confirming no stale session survived); prepare correctly showed
   "Start Adventure"; tapping it landed on `/session/7abb7455-b078-45f5-926c-4514b346b42d`.
2. **Navigate back to prepare → Resume, same `session_id`.** In-app navigation (not a full reload,
   which this dev harness's web session does not survive) back to `/prepare` showed
   "Resume Adventure"; tapping it routed to the identical
   `/session/7abb7455-b078-45f5-926c-4514b346b42d` — confirming `sendStartCommand` was not called.
3. **Kill the app, relaunch, open prepare → still Resume, same session.** Simulated via a full page
   reload (which does drop this harness's in-memory web session) followed by a fresh sign-in —
   the closest equivalent to a real kill/relaunch available in this environment. Prepare again
   showed "Resume Adventure" and routed to the same session id, confirming the decision is made
   fresh from the server on every mount, not cached client-side.
4. **Abandon the session via the fixture script → prepare shows Start again.** Re-ran
   `dev_fixture_learner.py` (no `--keep-session`): its own stale-session-reset step printed
   `"Abandoned stale active session 7abb7455-b078-45f5-926c-4514b346b42d."` (exact id match) before
   self-verifying and abandoning its own fresh session. A subsequent fresh sign-in and visit to
   `/prepare` showed "Start Adventure" again.
5. **Stop the backend, open prepare → readiness fails as before; the active-session check did not
   add a new error state.** To exercise this without losing the in-memory web session (which a
   full reload would, and the backend being down would then block re-authenticating), signed in
   *before* stopping the container, then stopped `docker compose stop api` and navigated to
   `/prepare` via in-app SPA navigation only. Readiness correctly failed
   (`net::ERR_CONNECTION_REFUSED` on `GET /health/ready`, the pre-existing `readinessCopy` "Almost
   ready — Try again in a moment" copy shown, button still reads "Start Adventure"). No separate
   resume-check error surfaced — confirms the resume check is unreachable when `checkReadiness`
   itself throws, exactly as coded (the resume-check block sits inside the try, after
   `setPhase('ready')`, which never executes on failure).

**Explicitly out of scope, untouched:** no live session screen (Batch 9), no renderer work
(Batch 8), no home screen (Batch 14), no API or store change (FE-0b/FE-0c already shipped
everything this batch consumes), no new dependency, no contract re-freeze.

**Files touched:** `frontend/src/features/session/session-preparation-screen.tsx`,
`frontend/src/api/__tests__/resume-decision.test.ts` (new), `backend/buildLog1.md`. No API file,
no store file, no other screen touched.

Left uncommitted for Yasindu. Not run: any git command that mutates state.

---

## 2026-07-29 — Manual-testing fixes: web CORS header, join-code input formatting, fixture invite minting

Three small, independently-verified fixes made directly during manual UI testing of the onboarding
flow in a web browser, none part of the FE-2a batch.

**1. Backend CORS was silently blocking every state-changing request on web.**
`frontend/src/api/client.ts` sends `X-Mobile-App-Version: 1.0.0` on every request, on every
platform, despite the header's name. `app/main.py`'s `CORSMiddleware.allow_headers` did not
include it. Native platforms don't enforce CORS, so this was invisible until web testing began;
on web, every POST (sign-up's profile creation, save-name, join-code resolve/request, ...) failed
its preflight with "Disallowed CORS origin" — surfacing to the user as generic messages like "We
could not save your name." Fixed by adding `X-Mobile-App-Version` to `allow_headers` in
`app/main.py`, with a comment explaining why it was web-only and previously invisible. Verified by
replaying the exact failing preflight (`curl -X OPTIONS .../learner/profile` with the same
`Access-Control-Request-Headers`) before (400 "Disallowed CORS headers") and after (200, header
present in `Access-Control-Allow-Headers`) rebuilding the container.

**2. Join-code input didn't uppercase or format as typed.**
`autoCapitalize="characters"` on `TeacherLinkInstructionsScreen`'s `TextInput` is a keyboard hint
only — React Native Web doesn't use it to transform the typed value, so lowercase input stayed
lowercase. Added `formatInviteTokenInput()`: strips non-alphanumeric characters, uppercases, and
groups 4-4 with a dash — matching the server's own format exactly
(`classroom_membership.py`'s `_JOIN_CODE_ALPHABET`/`_JOIN_CODE_LENGTH=8`, e.g. `M7KP-4X9D`), not
an arbitrary grouping. Purely a display aid: the resolve/request endpoints already accept the
code case-insensitively with separators ignored, so this changes nothing about what is sent.

**3. The fixture script had no way to hand out a join code once its own learner was approved.**
Requested: a literal fixed code (e.g. `ABCDEF`) for convenience. Declined as designed — a
permanently fixed, guessable join code is a standing authorization bypass (anyone who learns or
guesses it can join the classroom), the same class of shortcut FE-0d's batch spent its scope
closing (a fixture may substitute data, never an authorization outcome). It would also need a new
backend code path, since invite tokens are only ever generated by `secrets.choice()` inside
`POST /classrooms/{id}/invites` today — there is no way to set a custom plaintext token. Presented
three options; the fixture-script route was chosen. That route's real blocker: once the fixture
learner's own membership reaches `APPROVED` (the steady state after the first run),
`ensure_membership_approved` skips minting an invite entirely, so nothing is left to print.
Added `--mint-invite-only`: signs in as the (already-existing) fixture teacher only, ensures the
`FIXTURE Grade 2` classroom exists, mints one fresh invite via the same
`POST /classrooms/{id}/invites` route the teacher already has legitimate authority over, prints
it, and exits — no new authorization surface, just the existing action exposed standalone instead
of only firing as a side effect of approving the fixture's own learner. Confirmed invites are not
single-use (no consumption flag in `classroom_membership.py` — only `revoked_at_utc`/
`expires_at_utc` gate validity), so the same code works for any number of separate real accounts
until the 24h expiry.

**Verification:**
- Frontend (`npx tsc --noEmit`, `npm run lint`, `npm run test:contract`): clean, 57/57 unregressed.
- CORS fix verified live via direct preflight replay against the rebuilt container (400 → 200).
- `--mint-invite-only` run live against the real backend twice: printed distinct fresh codes
  (`NZEA-V5TZ`, `D888-WE2K`) both times, confirming the endpoint mints anew each call.
- Normal (no-flag) fixture run re-verified unregressed afterward: correctly still skips minting
  when the fixture learner's own membership is already `APPROVED`, self-verify still returns 201.
- `backend/tests/test_dev_fixture_isolation.py`: 3 passed (the new flag adds no disallowed
  import or direct-write pattern).

**Files touched:** `backend/app/main.py`, `backend/scripts/dev_fixture_learner.py`,
`backend/scripts/README.md`, `frontend/src/features/onboarding/teacher-link-instructions-screen.tsx`,
`backend/buildLog1.md`.

Left uncommitted for Yasindu. Not run: any git command that mutates state.

---

## 2026-07-29 — Fixture script: standalone approval for a separate real account

Follow-on to the previous entry's `--mint-invite-only`. That flag solved getting a fresh join
code for a separate real account, but the script had no way to approve that account's resulting
PENDING request afterward — `ensure_membership_approved` only ever looks up and approves the
fixture's own `LEARNER_ID`, never a different learner. A user who joined by hand through the
app's onboarding UI with a minted code was left stuck on the classroom-status screen with no
in-app way to move PENDING to APPROVED (no teacher UI exists; FE-1b is intentionally out of
scope).

Added `--approve-pending`: signs in as the (already-existing) fixture teacher only, ensures the
`FIXTURE Grade 2` classroom exists, lists every `PENDING` request via
`GET /classrooms/{id}/membership-requests`, and approves each one via the same
`POST /classroom-memberships/{id}/approve` route the teacher already has legitimate authority
over for their own classroom — same pattern as `--mint-invite-only`: no new authorization
capability, an existing legitimate action exposed standalone. Approves *all* pending requests in
one call, not just one, so multiple queued test accounts clear in a single run.

**Verification, all live:**
- Ran against a real PENDING request (a real Supabase account that had joined via a code from
  `--mint-invite-only`): approved 1, printed the learner_id.
- Re-ran immediately after: correctly reports "No PENDING membership requests found" rather than
  erroring or re-approving.
- Normal (no-flag) fixture run re-verified unregressed: still skips its own already-approved
  learner correctly, self-verify still 201.
- `backend/tests/test_dev_fixture_isolation.py`: 3 passed.

**Files touched:** `backend/scripts/dev_fixture_learner.py`, `backend/buildLog1.md`.

Left uncommitted for Yasindu. Not run: any git command that mutates state.

---

## 2026-07-29 — Clarification: classroom-status screen does not auto-navigate on approval

No code change. Recorded because it is easy to mistake for a regression during manual testing and
someone could otherwise "fix" intentional behavior.

After using `--mint-invite-only` + `--approve-pending` to approve a separate real account's
membership, the app's classroom-status screen did not automatically move to `(learner)/home`.
Confirmed this is by design, not a bug: `classroom-status-screen.tsx`'s own comment states it
"fetches membership status on mount and pull-to-refresh only — no continuous polling while this
screen is foregrounded, per frontend.md 15.10's don't-poll guidance" (a child's device should not
be polling the backend in a tight loop while a screen sits idle). The screen's `load()` already
does `router.replace('/(learner)/home')` the instant it observes `state === 'APPROVED'` — it
simply has no way to know the state changed until the next mount or pull-to-refresh triggers that
check. Pulling down to refresh, or navigating away and back, is the expected way to see an
out-of-band approval (via the fixture script, since no in-app teacher UI exists) take effect.

No files touched.

---

## 2026-07-29 — Home/prep greetings show first name only

Both `LearnerHomeScreen` and `SessionPreparationScreen` greeted with the learner's full name
("Hi, Yasindu Kularathne!") wherever it came from a signup display name or a saved learner
profile name. Added `frontend/src/utils/display-name.ts`'s `firstNameOf()` — takes the first
whitespace-separated token, collapses extra internal whitespace, passes an already-single-word or
empty value through unchanged. Applied at the single point in each screen where the greeting
string is computed (`learner-home-screen.tsx`'s `displayName`,
`session-preparation-screen.tsx`'s `displayName`) — the full name is still stored and passed
through internal state/`profileName` untouched; only the rendered greeting is shortened.

**Verification (from `frontend/`):** `npx tsc --noEmit` clean; `npm run lint` clean;
`npm run test:contract` **62 passed, 0 failed** (57 pre-existing + 5 new in
`src/api/__tests__/display-name.test.ts`, covering two-part/three-part/single-word/empty/
extra-whitespace names).

**Files touched:** `frontend/src/utils/display-name.ts` (new),
`frontend/src/features/home/learner-home-screen.tsx`,
`frontend/src/features/session/session-preparation-screen.tsx`,
`frontend/src/api/__tests__/display-name.test.ts` (new), `backend/buildLog1.md`.

Left uncommitted for Yasindu. Not run: any git command that mutates state.

---

## 2026-07-29 — Batch 8: answer-renderer registry (UI-free)

**What.** Three new modules under `frontend/src/features/session/renderers/` — `types.ts`,
`registry.ts`, `encode.ts` — exporting exactly two functions:

- `resolveRenderer(responseFormat, presentedChoices): RendererSpec | null`
- `encodeSubmittedValue(spec, state): string | null`

Deliberately UI-free so the whole batch is testable under the existing `node:test` + `tsx`
runner at zero new dependency cost. React Native Testing Library remains deferred to Batch 15.
No screen, no component, no API call, no timeout/hint/advance/results logic, no new dependency.

**Format table (verified against the generator).** Nine `response_format` values reduce to three
answer surfaces: `single_integer`, `single_integer_or_choice`, `single_choice_or_integer`,
`single_choice`, `ordered_list` → choice/4; `relation_choice` → choice/3; `binary_or_choice` →
choice/2; `expanded_form` → free-entry/0; `interactive_set_selection` → count-selection/0.

**Correction 1 — `ordered_list` is a plain choice format, not client-side answer construction.**
The plan as originally written would have had the client assemble the ordering (collect the
child's sequence, join it). That would put answer construction in the client. The server already
comma-joins each candidate ordering into a single `presented_choices` entry (e.g. `"12,45,300"`),
so the child picks one whole string and the client relays it verbatim — same as every other choice
format. Implemented and tested that way; `encode.ts` never joins, splits or reorders anything.

**Correction 2 — no relation symbols or conservation words anywhere in the client.** `<`, `>`,
`=` and `same`/`changed` are catalogue content. They arrive in `presented_choices` and are relayed
as whichever string the child picked. Hardcoding them in the registry would duplicate catalogue
content in the client and drift from it. Nothing in `renderers/` restates them; the test file uses
neutral placeholder choice strings except where a verbatim round-trip is the assertion.

**Lookup discipline.** The table is an object literal keyed by the nine format strings, looked up
with `Object.prototype.hasOwnProperty.call(...)` — never bare property access, which would resolve
`"constructor"`, `"toString"` or `"__proto__"` to inherited `Object.prototype` members and hand
back a bogus spec for a hostile or drifted format string.

**Fail closed — three paths, all `null`:** (1) unrecognized `response_format`; (2) a choice format
whose `presentedChoices.length` ≠ its expected count; (3) a non-choice format arriving with a
non-empty `presentedChoices`. All three are server/client structural drift. There is no fallback
surface, and specifically no degrade-to-free-text: a text box shown against `relation_choice`
would let a child type garbage and then be told they are wrong — exactly the failure the authority
boundary exists to prevent. Batch 9 renders `null` as a neutral error screen with a support code
and a single way home.

**Ordering.** `presented_choices` is passed through in server-given order and never re-sorted. The
server sorts lexicographically, which is why a child may see `10, 3, 9` — a real backend issue
tracked separately as Risk 1, not something this batch works around. Re-sorting client-side would
be the client transforming server data. Covered by a test on an already-unsorted input array.

**Encoding boundary.** `encode.ts` carries a top-of-file comment stating plainly that it
serializes a choice the child made and never parses, canonicalizes, compares, reorders or
validates an answer. `expanded_form` is trimmed only — no whitespace collapsing, no term
reordering, no case folding. The server owns normalization (`normalize_answer` strips leading
zeros, so `"03"` is the server's business) and correctness. Choice values leave byte-for-byte;
`interactive_set_selection` yields `String(count)`.

**Not touched, by design (FE-0c).** `component-b-api.ts` and `runtime-validation.ts` are unchanged
— in particular no `response_format` validation was added to `runtime-validation.ts`. The registry
is the single client-side owner of the set of known formats; a second list there would be a second
place for it to drift.

**Verification (from `frontend/`):** `npx tsc --noEmit` clean; `npm run lint` clean;
`npm run test:contract` **86 passed, 0 failed** (62 pre-existing all still green + 24 new in
`src/api/__tests__/answer-renderer-registry.test.ts`). The test file lives in `src/api/__tests__/`
because that is the glob the runner uses; the registry modules import nothing from `react-native`,
so it needs none of the module patching `pending-session-command.test.ts` requires.

**Files touched:** `frontend/src/features/session/renderers/types.ts` (new),
`frontend/src/features/session/renderers/registry.ts` (new),
`frontend/src/features/session/renderers/encode.ts` (new),
`frontend/src/api/__tests__/answer-renderer-registry.test.ts` (new), `backend/buildLog1.md`.

Left uncommitted for Yasindu. Not run: any git command that mutates state.

---

## 2026-07-29 — Prep screen: drop the unbackable skill claim, show real classroom/grade instead

**Why the skill could not simply be made dynamic.** The request was for the prep hero's hardcoded
"Counting" to reflect the real skill. It cannot, and the reason is structural rather than a
missing field: `skill_id` does not exist until a question is *selected*, and selection is the act
that starts the child's timeout clock (`timeout_deadline_utc = now + timeout`,
`opportunity_persistence.py:94`). Re-issuing an already-open opportunity preserves the original
deadline (`opportunity_selection.py:461`) and would be safe — but `GET /b/sessions/active`
returns only `{session_id, state, runtime_bundle_version, created_at_utc, row_version}` and
cannot report whether a question is currently open. So there is no way to ask for the skill on
this screen without risking creating a question and starting the child's 5-minute timer while
they are still reading the prep screen. Options were put to Yasindu; "neutral on prep, real skill
in session" was chosen.

**Changes (prep screen only — the home screen was explicitly out of scope and is untouched).**
- Hero subtitle no longer names a skill ("Let's start your **maths** adventure"). The
  `heroSkill`/`heroSkillCompact` styling is retained, so the hero's visual composition is
  unchanged — only the word it emphasises.
- The `lessonCard` is kept structurally (layout preserved, per Yasindu's standing constraint that
  the prep screen's design not change) but now carries genuinely-backed data instead of a fake
  skill: the learner's own classroom name and grade, read from
  `LearnerMembershipListItem.classroom_name` / `.grade` on their APPROVED membership, which the
  auth context has already loaded. Icon changed `calculator` -> `school` to match. Rendered only
  when an APPROVED membership exists, so the dev-fixture path (no membership) simply omits it
  rather than inventing a placeholder.
- Removed the now-stale in-code comment claiming no `grade` field is reachable from the frozen v1
  contract. That was true of `AuthenticatedPrincipal`/`LearnerProfileResponse` only; `grade` is on
  the membership DTO, and (separately) on `OpportunityPresentationResponse`.
- `previewLesson` is gone; `gradeLabels` replaces it.

The real, per-question skill will be surfaced on the live session screen (FE-3b), where
`OpportunityPresentationResponse` carries `skill_id`, `grade`, and `difficulty_level`
legitimately and at no cost.

**Verification (from `frontend/`):** `npx tsc --noEmit` clean; `npm run lint` clean;
`npm run test:contract` **86 passed, 0 failed** (unregressed; this count includes FE-3a's 24 new
renderer-registry tests, which landed separately).

**Files touched:** `frontend/src/features/session/session-preparation-screen.tsx`,
`backend/buildLog1.md`.

Left uncommitted for Yasindu. Not run: any git command that mutates state.

---

## 2026-07-29 — FE-3b: live session screen — present, answer, submit, outcome

**What.** Replaced the `app/(learner)/session/[sessionId].tsx` placeholder with a real route
boundary over a new `frontend/src/features/session/live-session-screen.tsx`, plus the three answer
surfaces under `frontend/src/features/session/renderers/` (`choice-grid.tsx`, `free-entry.tsx`,
`count-selection.tsx`) and a pure decision module `live-session-logic.ts`. No backend change, no
API-layer change, no store change — FE-0b/0c/3a already shipped everything this consumes.

**In scope, and done:** select the question, render it, accept an answer, submit it, show the
outcome. **Explicitly not done, by design:** countdown UI (FE-3c), hints (FE-3d), advancing to the
next question (FE-3e), results (FE-3f). After an attempt is recorded the child sees the outcome
and "Back to home". There is deliberately no next-question button — inventing one would front-run
FE-3e's completion call.

**Mount → present.** `api.selectOpportunity` (no idempotency key, no body — it re-issues the
already-open question rather than minting a new one, which is what makes it the crash-recovery
path), validated by `isOpportunityPresentationResponse`, then `resolveRenderer`. Rendered:
`prompt.stem` only (other prompt keys are ignored this batch — richer prompt rendering is not in
scope and was not improvised), and `skill_id` via `formatSkillLabel` (underscore-split +
title-case, e.g. `number_sense` → "Number Sense"; a curated id→name lookup was *not* added,
since that would restate catalogue content in the client). `representation_type` is treated as
opaque — nothing branches on it. `presented_choices` is rendered in server-given order, never
re-sorted.

**Fail closed.** `resolveRenderer` returning `null` (and, belt-and-braces, a presentation with no
usable stem) yields a neutral error screen: child-appropriate copy, the `request_id` as a support
code, one "Back to home". No free-text fallback anywhere — a text box against `relation_choice`
would let a child submit garbage and then be told they were wrong, which is the exact failure the
registry's fail-closed design exists to prevent.

**Answer surfaces.** Each owns only its input affordance and reports an `AnswerState`;
`chosenIndex` indexes into `spec.choices`, so an unpresented answer stays structurally
inexpressible. Submit is unavailable exactly when `encodeSubmittedValue` returns `null` — no
selection yet, blank `expanded_form`, unset count. `initialAnswerState` seeds `chosenIndex: -1`
and `count: -1` so the disabled state needs no separate "has the child touched this?" flag, and so
that **count 0 stays a real, submittable answer** (an empty set) rather than being swallowed by
the seed. That disabled state mirrors the server's `min_length=1`: it prevents a guaranteed 422,
it is not a correctness judgement. `count-selection` imposes no maximum — a ceiling would be a
client-side rule about which counts are legitimate, which the server owns.

**Submit.** The `submit_response` `PendingSessionCommand` is persisted **before** the request and
cleared on success. The body is persisted with the key because the server fingerprints the body
into the idempotency record — a replay with a reconstructed body fails the fingerprint check, and
`client_elapsed_ms` is unrecoverable after a relaunch. A non-conflict failure deliberately leaves
the record persisted; that record is the whole point of the recovery path. On mount,
`decidePendingReplay` replays a saved submit verbatim (same key, same body) when its `sessionId`
*and* `itemOpportunityId` both match what the server just handed back, discards it when they do
not, and leaves commands of other kinds alone (the store slot is shared with the prep screen's
`start_session`). The one-shot token refresh retries the *same* call with the *same* key and body,
so it can never record a second attempt. `client_elapsed_ms` is telemetry only, measured from
question render (and re-measured on "try again") to submit tap.

**Outcome.** `AttemptResponse` is authoritative. RESPONSE+matched → positive, neutral, no advance.
RESPONSE+unmatched → "try again", with **no client-side attempt cap** (attempt limits are
unapproved placeholders and the client must not invent one). TIMEOUT → neutral "Time's up — let's
keep going", never presented as a wrong answer; this is reachable in this batch with no countdown
UI at all, simply by the server's five-minute deadline passing while the child thinks. A 409 on
submit re-calls `/opportunities` and re-renders whatever the server returns — no client-side rule
about what "should" have happened.

**Verification — unit (from `frontend/`):** `npx tsc --noEmit` clean; `npm run lint` clean;
`npm run test:contract` **114 passed, 0 failed** (86 pre-existing all still green + 28 new in
`src/api/__tests__/live-session-logic.test.ts`, covering the skill-label formatter, stem
extraction, the mount branch choices including all three fail-closed paths and order preservation,
the not-yet-answered seeds, pending-command replay vs. discard vs. leave-alone, outcome
classification for RESPONSE-true / RESPONSE-false / TIMEOUT — including an assertion that timeout
copy contains no blaming words and offers no retry — and failure classification incl. the 409
resync route). No RNTL (Batch 15); the untested part is layout only.

**Verification — live: NOT PERFORMED.** None of the on-device steps in the batch brief were run:
no session was started against the BE-G2 fixture learner, no wrong/right answer was submitted, no
kill-and-resume was exercised, and no hand-edited unknown `response_format` was tried. This agent
session is non-interactive and has no device, emulator or running Expo/backend pair to drive, and
`scripts/dev_fixture_learner.py --test-fixture-only` creates real test data through the live
backend API, so it was not run either. **Formats actually exercised live: none.** All nine formats
are unit-tested only (via `resolveRenderer`/`planPresentation` in
`answer-renderer-registry.test.ts` and `live-session-logic.test.ts`); the two of those that this
screen's non-choice surfaces depend on — `expanded_form` and `interactive_set_selection` — have
had no real presentation rendered through them. The live checklist is outstanding and is Yasindu's
to run; an honest "none" is recorded here rather than an implied "all nine".

**Files touched:** `frontend/app/(learner)/session/[sessionId].tsx`,
`frontend/src/features/session/live-session-screen.tsx` (new),
`frontend/src/features/session/live-session-logic.ts` (new),
`frontend/src/features/session/renderers/choice-grid.tsx` (new),
`frontend/src/features/session/renderers/free-entry.tsx` (new),
`frontend/src/features/session/renderers/count-selection.tsx` (new),
`frontend/src/api/__tests__/live-session-logic.test.ts` (new), `backend/buildLog1.md`.

Left uncommitted for Yasindu. Not run: any git command that mutates state.

---

## 2026-07-29 — FE-3b live verification: partial, honestly scoped

Supervisor follow-up to the FE-3b entry, which recorded live coverage as "none". Yasindu has now
run the app against the real backend and shared a screenshot of a rendered question. Recording
exactly what that establishes and what it does not.

**Confirmed live (from the rendered question):**
- A real opportunity is selected, validated, and rendered end to end: stem `46, 47, 48, __`,
  skill badge "Counting", four choice buttons (47 / 48 / 49 / 50).
- Template is `B-CNT01-SEQ-CONTINUE`, `response_format: single_integer`. `resolveRenderer`
  resolved it as `kind: 'choice'` with `expectedChoiceCount: 4` and the arriving
  `presented_choices` matched — i.e. the strict count guard passed against real generator output,
  not a fixture.
- `formatSkillLabel` produced "Counting" from a real catalogue `skill_id`. This is the first time
  the actual skill has been surfaced in the UI; the prep screen deliberately cannot show it (see
  the prep-screen entry above).
- The submit button renders disabled before any selection — the `chosenIndex: -1` seed from
  `initialAnswerState` behaving as designed, keeping a value `encodeSubmittedValue` rejects from
  ever reaching the API layer (where it would fail `SUBMITTED_VALUE_MIN_LENGTH` anyway).
- Yasindu reports the flow works end to end.

**Formats exercised live: 1 of 9 — `single_integer` only.** The other eight remain unit-tested
only. `expanded_form` (typed answer) and `interactive_set_selection` (count surface) are the two
whose *rendering surfaces* have still never drawn a real server presentation, and they are the
least like the choice grid, so they carry the most residual risk.

**Not verified live, still outstanding:**
- Check 4 — kill-and-resume returning the same `item_opportunity_id` with no duplicate attempt.
- Check 5 — a real `event_kind: TIMEOUT` displaying as "Time's up" rather than as a wrong answer.
  This is the highest-value outstanding check: it is the one that decides whether a child who
  simply thought for too long is told they got it *wrong*. Reachable in this batch with no
  countdown UI at all, just by exceeding the server's five-minute deadline.
- Check 6 — an unknown `response_format` degrading to the neutral error screen rather than a
  free-text box.

Wrong-answer and right-answer outcome paths were reported working but not separately evidenced;
they are covered by unit tests over `classifyAttemptOutcome`/`outcomeView`.

**Incidental note (not a defect in this batch).** The lexicographic `presented_choices` ordering
(Risk 1) is invisible in this particular question because 47/48/49/50 sort identically
numerically and lexicographically. It will surface on any template mixing digit lengths, where a
child would see e.g. `10, 3, 9`. The client correctly does not re-sort.

No files touched; verification record only.

---

## 2026-07-29 — FE-3b live verification: checks 2 and 3 confirmed

Supplement to the previous entry. Yasindu ran both outcome paths on the real backend
(`B-CNT01-SEQ-CONTINUE`, `single_integer`, stem `46, 47, 48, __`).

**Check 3 — correct answer.** Selecting 49 produced "Nice work! / That one is right." with no
try-again affordance, i.e. `classifyAttemptOutcome` -> `'correct'` and `outcomeView`'s
`canTryAgain: false`, rendered from a real `AttemptResponse`.

**Check 2 — wrong answer.** Selecting 47 produced "Not quite / Have another go — you can try as
many times as you like." with TRY AGAIN offered. Confirms `'incorrect'` classification, the
non-blaming copy, and the absence of any client-side attempt cap (attempt limits remain
unapproved placeholders; the client must not invent one).

**What this additionally establishes, beyond the two branches themselves:** the server accepted
the submitted string and judged it against its own catalogue answer — 49 matched, 47 did not.
That is live confirmation of FE-3a's verbatim-encoding contract (`encodeSubmittedValue` relays
the chosen `presented_choices` entry unmodified) against real generator output, not a fixture.
The client never computed correctness; `AttemptResponse` was authoritative in both cases.

**Live coverage now: checks 1, 2, 3 confirmed. Formats: 1 of 9 (`single_integer`).**

**Still outstanding, unchanged:** check 4 (kill-and-resume returning the same
`item_opportunity_id`), check 5 (a real `event_kind: TIMEOUT` displaying as "Time's up" rather
than as a wrong answer — still the highest-value outstanding check), check 6 (unknown
`response_format` degrading to the neutral error screen). `expanded_form` and
`interactive_set_selection` surfaces have still never drawn a real presentation.

**Cosmetic observation, not a defect, deliberately not changed.** The selected-choice chip uses
the same pink/accent treatment whether the attempt was correct or incorrect; the outcome is
carried entirely by the card below it (green for correct, blue for "Not quite"). A red-adjacent
highlight sitting above "Nice work!" is a mildly mixed signal for a seven-year-old. Raised for
Yasindu's judgement rather than altered — the prep/session visual design is his, and the
semantics are legible from the card. Noted here so it is a decision on record, not an oversight.

No files touched; verification record only.

---

## 2026-07-29 — FE-3c: timeout handling — the deliberately small batch

**The durable finding: the plan's original "disable the answer surface on expiry" would have
soft-locked the session, permanently.** This is the entry worth keeping; the code is almost
nothing.

Three server facts make the disable-on-expiry instinct actively harmful:

1. `is_timeout` is evaluated **server-side at submit time** — `now >= opportunity.
   timeout_deadline_utc` (`attempt_submission.py:213`).
2. On timeout the server sets `submitted_value = None` and `response_matched = None` and never
   compares the answer (`attempt_submission.py:216-229`). Submitting "late" therefore costs the
   child nothing.
3. Advancing past an opportunity requires **at least one recorded attempt or timeout**
   (`session_completion.py:22`), and **no server-side sweep exists** — the only way a TIMEOUT is
   ever recorded is if the client submits after the deadline.

Chain them: disabling input on expiry means no submit → no recorded TIMEOUT → no advance. The
child would be stuck on that one question forever, holding the only key to a lock they could no
longer reach. The child must **always** be able to select and submit. That rule is now enforced by
a unit test with the reasoning written next to it, not by a comment alone.

**What was actually built.**

- `isDeadlinePassed(deadlineUtc, now)` in `live-session-logic.ts` — pure, `>=` to match the
  server's own comparison, and treats an unparseable date as *not* passed (the fail-safe direction
  is always the one that keeps the child able to answer). `timeoutDeadlineUtc` had been carried on
  `SessionPlan` since FE-3b and read by nothing; it is now read.
- `isAnswerSurfaceDisabled({ submitting, hasOutcome, deadlinePassed })` — takes `deadlinePassed`
  and **deliberately ignores it**. Giving the ignoring a named, exported seam is the point: it
  turns "do not gate interactivity on the clock" from a comment someone could tidy away into an
  invariant with a failing test attached. The screen now derives both the surface's `disabled`
  state and submit availability from this one function, so the two cannot drift apart.
- Clock skew at mount changes nothing. A device set hours ahead reports `deadlinePassed: true` and
  the surface stays fully interactive; the client clock is advisory and `event_kind` on the
  response is the only truth.

**What was deliberately not built.** No countdown UI (a ticking clock in front of a seven-year-old
is an anxiety device, and it would be counting down to something the client cannot enforce). No
"time is running out" pre-warning — telling a child "time's up, but please answer anyway so we can
move on" is incoherent to them. No timer, no polling, no re-render on a tick. No duration is
hardcoded anywhere: the bound is unapproved policy and exists only in the server's
`server_timeout_deadline_utc`. FE-3b's TIMEOUT classification and its neutral "Time's up / Let's
keep going" copy were **verified, not rebuilt** — `classifyAttemptOutcome` and `outcomeView` are
untouched.

**Verification — unit (from `frontend/`):** `npx tsc --noEmit` clean; `npm run lint` clean;
`npm run test:contract` **125 passed, 0 failed** (114 pre-existing all still green + 11 new in
`src/api/__tests__/session-timeout.test.ts`): `isDeadlinePassed` past/future/exactly-equal/
unparseable; the soft-lock guard (surface stays interactive with `deadlinePassed: true`), carrying
the full reasoning inline so nobody "fixes" it later; the clock-skew case; the inert-only-while-
submitting-or-outcome case; a real-shaped TIMEOUT (`response_matched: null`, no echoed
`submitted_value`) still classifying as `'timeout'` and never `'incorrect'`, with neutral copy and
no retry prompt; and a grep-as-a-test (same pattern as `no-auth-bypass.test.ts`) asserting that
`300000`, `300_000`, `300` and `5 * 60` appear in none of the three session modules.

**Verification — live: NOT PERFORMED.** This batch was supposed to close FE-3b's outstanding
check 5, and it does not. The run requires starting a real session on a device, leaving the
question on screen past the server's deadline, and then answering — this agent session is
non-interactive with no device, emulator or running Expo/backend pair to drive. So: **not
confirmed live** that the result reads "Time's up / Let's keep going" rather than "Not quite", and
**not confirmed live** that the answer surface was still usable on return. No backend-side
shortening of the deadline was used, because no live run happened at all — worth stating, since a
shortened deadline would change what such a run proves. FE-3b's check 5 remains open and is
Yasindu's to run; the unit tests lock the logic, not the rendered experience.

**Files touched:** `frontend/src/features/session/live-session-logic.ts`,
`frontend/src/features/session/live-session-screen.tsx`,
`frontend/src/api/__tests__/session-timeout.test.ts` (new), `backend/buildLog1.md`.

Left uncommitted for Yasindu. Not run: any git command that mutates state.

---

## 2026-07-29 — Timeout policy: a measurement consequence, recorded for gate-B

No code change. Raised while reviewing a proposed deferral note ("revisit expired-question UX in a
later design pass if user testing suggests children need a clearer indication that time has
elapsed"). That note was not adopted; this entry records why, and the finding behind it.

**The deferral's trigger cannot fire.** Conditioning a revisit on user testing is conditioning it
on evidence gate-B currently prohibits collecting — no real-child, pilot, or production use is
authorized. That is "never" phrased as "later". (Compare Batch 15/FE-4a, which was deferred but
given an explicit schedule precisely so it would not quietly become never.)

**The substantive finding: a silent deadline is a measurement problem, not only a UX one.**
`attempt_submission.py:216-229` discards `submitted_value` on timeout and never compares it
(`response_matched = None`). `session_completion.py:167-172` then folds that into the record as:

    first_attempt_correct = bool(first.response_matched) if first.event_kind == "RESPONSE" else False
    -> first_attempt_error_pattern = "timeout_no_response"

So a learner who deliberates past the bound and selects the **correct** answer is recorded as
`first_attempt_correct = False` with error pattern `timeout_no_response`, and the answer they gave
is never examined. That value feeds `aggregate_session`, first-attempt accuracy, and per-skill
outcomes. The bias has a direction: slower learners accumulate more timeouts, so recorded
first-attempt accuracy is systematically depressed for exactly the learners who take longest.

The obvious counterpoint runs the same way rather than against it. Five minutes is long for a
Grade-2 counting item, so a real timeout more likely reflects an interruption or the child walking
away than deliberation — but that is then recorded as a first-attempt failure with a specific
error pattern, attributing a classroom artifact to mathematical ability.

**Therefore the open question is not "should there be a countdown".** It is whether a hard bound
that silently discards answers is the right policy at all. `DEFAULT_TIMEOUT = timedelta(minutes=5)`
(`opportunity_selection.py:99`) is an unapproved engineering placeholder, and timeout policy is
already on the gate-B list. A countdown is one candidate answer to a question nobody has decided.

**Recorded position.** Expired-question UX stays deferred, but tied to **gate-B's timeout-policy
decision** — a milestone that will actually occur — rather than to user testing that cannot
currently happen. Whoever resolves that decision should see the paragraph above first: whether
children need a visible cue is downstream of whether the bound should discard answers at all.
Nothing in FE-3c changes on account of this; gate-B blocks real-child use, so no learner is
affected today.

No files touched; decision record only.
