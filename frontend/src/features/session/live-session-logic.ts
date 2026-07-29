// Pure decision logic for the live session screen (FE-3b), deliberately split out of
// live-session-screen.tsx so every branch this batch introduces is testable under the existing
// `node:test` + `tsx` runner. Nothing here imports react, react-native, expo-*, or the API client;
// the screen keeps only layout, state wiring and the actual network calls. (RNTL is Batch 15.)
//
// Scope reminder: this module decides what to render and how to classify what came back. It never
// judges an answer. `AttemptResponse` is authoritative for correctness, and `submitted_value` is
// built by FE-3a's `encodeSubmittedValue`, not here.

import type { PendingSessionCommand, PendingSubmitResponseCommand } from '@/src/api/contracts';
import { ApiClientError } from '@/src/api/errors';
import type {
  AttemptResponse,
  OpportunityPresentationResponse,
} from '@/src/api/generated/openapi-types';
import { resolveRenderer } from '@/src/features/session/renderers/registry';
import type { AnswerState, RendererSpec } from '@/src/features/session/renderers/types';

// --- skill label ------------------------------------------------------------------------------

/**
 * Turn a catalogue `skill_id` into something a child can read: `number_sense` → "Number Sense".
 *
 * Underscore-split and title-case only. It does not map ids to curated display names — a lookup
 * table here would be catalogue content restated in the client, free to drift from the backend's
 * own skill set. An unrecognized or oddly-shaped id therefore degrades to a readable
 * approximation rather than to a blank or a thrown error.
 */
export function formatSkillLabel(skillId: string): string {
  const words = skillId
    .split(/[_\s-]+/)
    .map((word) => word.trim())
    .filter((word) => word.length > 0);
  if (words.length === 0) return '';
  return words
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

// --- presentation → renderable plan -------------------------------------------------------------

export type SessionPlan =
  | {
      kind: 'render';
      spec: RendererSpec;
      stem: string;
      skillLabel: string;
      itemOpportunityId: string;
      requestId: string;
      timeoutDeadlineUtc: string;
    }
  // Structural drift: an unknown response_format, one whose presented_choices do not match it, or
  // a presentation with no usable stem (which `isOpportunityPresentationFields` should already
  // have rejected — this is belt-and-braces, and kept distinguishable in the support code path).
  // The screen renders a neutral error. It must never degrade to a free-text box — see
  // resolveRenderer's own comment for why that specific fallback is harmful.
  | {
      kind: 'unrenderable';
      reason: 'unsupported-format' | 'missing-stem';
      requestId: string;
      responseFormat: string;
    };

/**
 * `prompt` is an open `Record<string, unknown>` on the wire and carries more than the stem
 * (numbers, options, direction, …). This batch renders the stem and nothing else; improvising a
 * richer prompt renderer from keys whose semantics are per-template is explicitly out of scope.
 */
export function readPromptStem(prompt: Record<string, unknown>): string | null {
  const stem = prompt.stem;
  if (typeof stem !== 'string') return null;
  const trimmed = stem.trim();
  return trimmed.length > 0 ? trimmed : null;
}

/**
 * `presented_choices` is passed to the registry — and from there to the screen — in the server's
 * order, untouched. The server sorts lexicographically, so a child may see 10, 3, 9; that is a
 * backend issue tracked separately, and re-sorting here would be the client transforming server
 * data. `representation_type` is "numeral" for all 36 templates today and is treated as opaque:
 * nothing branches on it.
 */
export function planPresentation(
  presentation: OpportunityPresentationResponse,
): SessionPlan {
  const spec = resolveRenderer(presentation.response_format, presentation.presented_choices);
  const stem = readPromptStem(presentation.prompt);
  if (!spec || !stem) {
    return {
      kind: 'unrenderable',
      reason: spec ? 'missing-stem' : 'unsupported-format',
      requestId: presentation.request_id,
      responseFormat: presentation.response_format,
    };
  }
  return {
    kind: 'render',
    spec,
    stem,
    skillLabel: formatSkillLabel(presentation.skill_id),
    itemOpportunityId: presentation.item_opportunity_id,
    requestId: presentation.request_id,
    timeoutDeadlineUtc: presentation.server_timeout_deadline_utc,
  };
}

// --- answer state seeds ---------------------------------------------------------------------

/**
 * The "nothing chosen yet" state for each surface. `chosenIndex: -1` and `count: -1` are sentinels
 * that `encodeSubmittedValue` already rejects, so submit starts unavailable without the screen
 * needing a second "has the child touched this?" flag. Note `count: 0` is a real answer (an empty
 * set) and must stay submittable — which is exactly why the seed is -1, not 0.
 */
export function initialAnswerState(spec: RendererSpec): AnswerState {
  if (spec.kind === 'choice') return { kind: 'choice', chosenIndex: -1 };
  if (spec.kind === 'free-entry') return { kind: 'free-entry', rawInput: '' };
  return { kind: 'count-selection', count: -1 };
}

// --- the timeout deadline ------------------------------------------------------------------------

/**
 * Whether the server's timeout deadline for this question has passed, according to the device
 * clock. Advisory only — the server evaluates `now >= opportunity.timeout_deadline_utc` itself at
 * submit time (attempt_submission.py:213) and the `event_kind` it returns is the only truth.
 *
 * The comparison is `>=`, matching the server's. An unparseable deadline is treated as *not*
 * passed: the fail-safe direction is always the one that keeps the child able to answer, and the
 * server decides regardless.
 *
 * No duration is hardcoded here or anywhere else in the session modules. The bound is unapproved
 * policy and exists only in the server's response; a literal in the client would both duplicate it
 * and be wrong the moment it changed. (`no-timeout-literal.test.ts` enforces that.)
 */
export function isDeadlinePassed(deadlineUtc: string, now: number): boolean {
  const deadline = Date.parse(deadlineUtc);
  if (Number.isNaN(deadline)) return false;
  return now >= deadline;
}

export type AnswerSurfaceState = {
  submitting: boolean;
  hasOutcome: boolean;
  deadlinePassed: boolean;
};

/**
 * Whether the answer surface (and the submit button) should be inert.
 *
 * `deadlinePassed` is accepted and then **deliberately ignored**. This is not an oversight, and it
 * must not be "fixed":
 *
 *   - No server-side sweep records timeouts. A TIMEOUT is only ever written when the *client*
 *     submits after the deadline (attempt_submission.py:213-229).
 *   - Advancing past an opportunity requires at least one recorded attempt or timeout
 *     (session_completion.py:22).
 *
 * So disabling input once the deadline passes would leave the child holding the only key to a lock
 * they can no longer reach: no submit → no recorded TIMEOUT → no advance → the session is soft-
 * locked on that question, permanently. The child must always be able to select and submit. The
 * server sets `submitted_value = None` and never compares the answer on a timeout, so submitting
 * "late" costs nothing and is the only thing that unblocks the session.
 *
 * The same holds at mount with a skewed device clock: a phone set hours ahead must not stop a
 * child answering. Interactivity never keys off the clock.
 */
export function isAnswerSurfaceDisabled(state: AnswerSurfaceState): boolean {
  return state.submitting || state.hasOutcome;
}

// --- pending-command replay -------------------------------------------------------------------

export type PendingReplayDecision =
  | { action: 'replay'; command: PendingSubmitResponseCommand }
  | { action: 'discard' }
  | { action: 'none' };

/**
 * Decide what to do with a locally persisted submit command when the server hands back an
 * opportunity on mount.
 *
 * A match is replayed *verbatim* — same idempotency key, same body. Same key means the server
 * returns the original attempt instead of recording a second one, and the body must be the saved
 * one because the server fingerprints the request body into the idempotency record: a body
 * rebuilt at replay time would fail the fingerprint check (and `client_elapsed_ms` is
 * unrecoverable after a relaunch anyway).
 *
 * A submit command for a different opportunity is stale — that question has already moved on — so
 * it is discarded rather than sent. Commands of other kinds are left alone: the shared store slot
 * also holds `start_session`, which the prep screen owns.
 */
export function decidePendingReplay(
  pending: PendingSessionCommand | null,
  sessionId: string,
  itemOpportunityId: string,
): PendingReplayDecision {
  if (!pending || pending.kind !== 'submit_response') return { action: 'none' };
  if (pending.sessionId !== sessionId) return { action: 'discard' };
  if (pending.itemOpportunityId !== itemOpportunityId) return { action: 'discard' };
  return { action: 'replay', command: pending };
}

// --- outcome classification --------------------------------------------------------------------

// `AttemptResponse` is authoritative. `isAttemptResponse` already enforces the cross-field
// invariant (response_matched is null iff event_kind is TIMEOUT), so this is a total mapping over
// what a validated response can actually be.
export type AttemptOutcome = 'correct' | 'incorrect' | 'timeout';

/**
 * TIMEOUT is never an incorrect answer. The child did not answer at all — the server's five-minute
 * deadline simply passed, which is reachable in this batch with no countdown UI at all, just by
 * thinking for a while. Showing it as "wrong" would tell a child they got something wrong that
 * they never got the chance to get right. (The full timeout experience is FE-3c; not mishandling
 * it is this batch's job.)
 */
export function classifyAttemptOutcome(attempt: AttemptResponse): AttemptOutcome {
  if (attempt.event_kind === 'TIMEOUT') return 'timeout';
  return attempt.response_matched === true ? 'correct' : 'incorrect';
}

// Copy is neutral in every branch: encouraging for a match, invitational for a miss, and
// explicitly not blaming for a timeout. There is no client-side attempt cap — attempt limits are
// unapproved placeholders and the client must not invent one — so 'incorrect' always offers
// another try.
export type OutcomeView = { title: string; detail: string; canTryAgain: boolean };

export function outcomeView(outcome: AttemptOutcome): OutcomeView {
  if (outcome === 'correct') {
    return { title: 'Nice work!', detail: 'That one is right.', canTryAgain: false };
  }
  if (outcome === 'timeout') {
    return { title: "Time's up", detail: "Let's keep going.", canTryAgain: false };
  }
  return { title: 'Not quite', detail: 'Have another go — you can try as many times as you like.', canTryAgain: true };
}

// --- failure classification ---------------------------------------------------------------------

export type SessionFailure =
  // 409 on submit. The screen re-calls /opportunities and re-renders whatever the server returns.
  // It never applies a client-side rule about what "should" have happened.
  | 'conflict'
  | 'authentication'
  | 'network'
  | 'technical';

export function classifyFailure(error: unknown): SessionFailure {
  if (!(error instanceof ApiClientError)) return 'technical';
  if (error.kind === 'conflict') return 'conflict';
  if (error.kind === 'unauthenticated' || error.kind === 'forbidden') return 'authentication';
  if (error.kind === 'network' || error.kind === 'timeout') return 'network';
  return 'technical';
}

export function failureRequestId(error: unknown): string | null {
  return error instanceof ApiClientError && error.requestId ? error.requestId : null;
}
