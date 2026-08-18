"""Component C Phase 8: server-side telemetry validation (v3.0 §11 Phase 8, "Treat the client's
event stream as untrusted input" -- explicitly marked "no B precedent"; both of this batch's own
planning turns established there is no PACKAGE precedent either -- H1-a, recorded here rather than
left for a reader to wonder whether C-4 ["never reimplement the package's logic"] was skipped:
there is no package logic here to reimplement, because the package has no analog of "did an
untrusted client's telemetry arrive in a well-formed, honest shape." Every check below is new
application logic, a genuine first for this codebase, not a call-through.

K1 -- THE RULE, BOTH HALVES TOGETHER, in one sentence (owner ruling, "ingest" means accept into the
SCORED, DERIVED record, never "write bytes"): Phase 8 ingests every structurally well-formed
submission into the append-only event store unconditionally -- persisted always -- and refuses to
let a distrusted stream ever reach a scored, derived record -- scored never. Owner's reason, which
travels with the rule: "A malformed wrapper does not make the actions inside it fictional, and a
persisted bad stream is recoverable by a later fix while a refused one is not. That asymmetry
decides it." Concretely: this module NEVER writes, deletes, or mutates a ``c_gameplay_events`` row
-- every check below is read-only. It only decides whether ``derive_task_opportunity_summary`` (the
SCORING step) may run at all.

STRUCTURAL, NEVER SCIENTIFIC (H1-b): every check below is a judgment about the SHAPE of the stream
(ordering, counting, pairing) -- never about what the numbers MEAN. Four candidate checks that
would need a judgment about magnitude -- the numeric retry cap (I4), latency plausibility, the
magnitude half of inactivity plausibility, and the magnitude half of clock-drift tolerance -- are
UNBUILT here, each with its own blocker recorded in this module's own tests
(``tests/test_c8_telemetry_validation.py``), never approximated with an invented number.

R0, WIDENED (owner ruling, recorded here because this module's own claims are exactly what it
governs): "any claim that a mechanism DOES something needs the same full trace as a claim that it
doesn't." Every check below states, in its own docstring, exactly what it catches and what it does
not -- not "validates pauses" but "catches overlap and count mismatch; does not catch a pause whose
duration is implausible in isolation (no governed bound exists for that, see UNBUILT above)."
"""

from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.live_engine_c.errors import DistrustedHistoryGapError, TelemetryStreamRejectedError
from app.domain.live_engine_c.types import GameplayEvent
from app.infrastructure.persistence_models import CGameplayEventRecord, CTaskOpportunitySummaryRecord
from app.infrastructure.repositories import (
    CGameplayEventRecordRepository,
    CTaskInstanceRecordRepository,
    CTaskOpportunityRecordRepository,
    CTaskOpportunitySummaryRecordRepository,
)

# Hand-copied from component_c_generator.models.gameplay.TERMINAL_EVENT_TYPES -- the same
# convention CGameplayEventRecordRepository._TERMINAL_EVENT_TYPES already uses (X-1 restricts the
# component_c_generator import root to app/infrastructure/live_engine_c/adapter.py only, so this
# module, like that repository, cannot read the package's own tuple at runtime). Verified against
# the package's live value by test_terminal_event_types_tuple_matches_the_packages_own_live_value
# (test_c6a_summary_derivation.py) for the repository's copy; this module's own copy is verified
# identically in test_c8_telemetry_validation.py (the R-I pattern, applied a second time).
TERMINAL_EVENT_TYPES = ("game_task_completed", "game_task_skipped", "game_task_quit")


def validate_event_stream_structurally(events: Sequence[GameplayEvent]) -> None:
    """The five checks buildable on the DOMAIN ``GameplayEvent`` sequence alone (H2-d): index
    continuity, monotonicity, terminal uniqueness, pause pairing including overlap, and the
    structural half of inactivity plausibility. Raises ``TelemetryStreamRejectedError`` on the
    FIRST violation found -- never continues past the first structural break to accumulate a list,
    since any one of these already makes the stream unusable for derivation. Called BEFORE
    ``LiveEngineCAdapter.derive_task_opportunity_summary`` -- H4-a/K2-i's own requirement -- never
    after. Does NOT check retry bounds (I4, BLOCKED), latency plausibility (BLOCKED), the magnitude
    half of inactivity plausibility (BLOCKED), or clock discipline (a SEPARATE function,
    ``validate_clock_discipline`` below, because it needs the raw persisted row's
    ``created_at_utc``, which this domain type does not carry)."""
    if not events:
        raise TelemetryStreamRejectedError("terminal_uniqueness", "empty event stream")

    # Terminal uniqueness: exactly one, not merely at most one -- the DB-enforced half
    # (uq_c_gameplay_events_at_most_one_terminal_per_instance, persistence_models.py:923-930)
    # already guarantees AT MOST one; this is the "AT LEAST one" half v3.0's own Phase 8 mandate
    # names, catching a stream that never reached a terminal event at all.
    terminal_count = sum(1 for e in events if e.event_type in TERMINAL_EVENT_TYPES)
    if terminal_count != 1:
        raise TelemetryStreamRejectedError(
            "terminal_uniqueness", f"expected exactly one terminal event, found {terminal_count}"
        )

    # Index continuity: event_index consecutive from 1, no gaps, no duplicates -- catches a client
    # that skipped, reordered, or double-submitted an index, independent of what event_type it
    # carries. Does NOT catch a well-formed-but-wrong event_type sequence (e.g. an
    # answer_evaluated before its answer_submitted) -- that is a semantic ordering property no
    # check below asserts; only the INDEX NUMBERS themselves are checked here.
    indices = [e.event_index for e in events]
    if indices != list(range(1, len(events) + 1)):
        raise TelemetryStreamRejectedError(
            "index_continuity", f"event_index sequence {indices} is not consecutive from 1"
        )

    # Monotonicity: event_timestamp_relative_ms non-decreasing across the CLAIMED (event_index)
    # order -- catches a client asserting an earlier relative time for a later-indexed event.
    # Does NOT catch two events sharing the identical timestamp (C3 §14 permits non-decreasing,
    # not strictly increasing) -- that is deliberately not a violation.
    for prev, cur in zip(events, events[1:]):
        if cur.event_timestamp_relative_ms < prev.event_timestamp_relative_ms:
            raise TelemetryStreamRejectedError(
                "monotonicity",
                f"event_index {cur.event_index}'s timestamp {cur.event_timestamp_relative_ms} "
                f"precedes event_index {prev.event_index}'s {prev.event_timestamp_relative_ms}",
            )

    # Pause pairing including overlap: single-pass, at-most-one-open-pause-at-a-time -- this is
    # the C-9 fix at the VALIDATION layer (never at the derivation layer, H4-b): the derivation's
    # own zip(pause_starts, pause_ends) pairs POSITIONALLY, which lets (start1, start2, end1, end2)
    # -- an overlap -- pass every one of its own checks. This algorithm instead tracks whether a
    # pause is currently OPEN; a second pause_started while one is already open is rejected here,
    # BEFORE the derivation's own zip ever sees the stream. Does NOT catch a pause whose OWN
    # duration is implausibly long in isolation (BLOCKED, no governed bound -- see module
    # docstring) -- only mispairing/overlap/unpairing are structural.
    open_pause: Optional[GameplayEvent] = None
    for event in events:
        if event.event_type == "pause_started":
            if open_pause is not None:
                raise TelemetryStreamRejectedError(
                    "pause_pairing",
                    f"event_index {event.event_index} (pause_started) begins before event_index "
                    f"{open_pause.event_index}'s pause_started is closed -- overlapping pauses "
                    "(C-9's own shape: this is caught HERE, never left for derivation to miscount)",
                )
            open_pause = event
        elif event.event_type == "pause_ended":
            if open_pause is None:
                raise TelemetryStreamRejectedError(
                    "pause_pairing", f"event_index {event.event_index} (pause_ended) has no open pause_started"
                )
            if event.event_timestamp_relative_ms < open_pause.event_timestamp_relative_ms:
                raise TelemetryStreamRejectedError(
                    "pause_pairing",
                    f"event_index {event.event_index}'s pause_ended precedes its own pause_started "
                    f"(event_index {open_pause.event_index})",
                )
            open_pause = None
    if open_pause is not None:
        raise TelemetryStreamRejectedError(
            "pause_pairing", f"event_index {open_pause.event_index}'s pause_started has no matching pause_ended"
        )

    # Inactivity plausibility, STRUCTURAL HALF ONLY (H2-d): non-technical inactive time (the same
    # technical_flag routing the derivation itself already applies, C3 §10) cannot exceed the
    # elapsed span of the whole stream. Does NOT judge whether any ONE inactivity period is
    # plausible on its own (BLOCKED, no governed bound).
    #
    # R0, WIDENED, applied to this check's own claim: given the monotonicity check and the
    # pause-pairing/no-overlap check BOTH already ran and passed by the time this line executes,
    # every pause interval is already proven to lie within [first_ts, last_ts] and to be pairwise
    # disjoint from every other pause interval. The sum of disjoint sub-intervals of a bounded
    # range cannot exceed that range's own length -- so THIS ASSERTION IS LOGICALLY IMPLIED BY THE
    # TWO CHECKS ABOVE, given the current shape of pause_pairing, and cannot independently fire
    # today (no synthetic violation was constructible for it in
    # tests/test_c8_telemetry_validation.py; that absence IS the trace, not an oversight).
    #
    # R0, WIDENED, A SECOND TIME -- applied here not to a claim about behaviour but to the
    # RATIONALE FOR KEEPING THE LINE (SUPERVISOR CORRECTION of the builder's own earlier
    # reasoning): the prior comment said a future loosening of pause_pairing's overlap rule "would
    # make this line load-bearing again." That is wrong, not merely optimistic -- the computation
    # below pairs pauses via zip(pause_starts, pause_ends), POSITIONALLY, the exact C-9 defect
    # shape. Under a permitted overlap (start1, start2, end1, end2), that same zip would sum
    # 2000ms + 2000ms = 4000ms against a true union of 3000ms -- it would OVER-COUNT and fire
    # SPURIOUSLY, rejecting a stream this check has no sound basis to reject, rather than
    # protecting anything. So: this line is DORMANT today (cannot independently fire, as traced
    # above), and its CURRENT IMPLEMENTATION WOULD NOT BE A VALID CHECK if overlap were ever
    # permitted -- it would need to be rebuilt with the same non-positional pairing pause_pairing
    # itself would then require, not inherited as-is. Kept anyway, as a MARKER for that future
    # revisit -- not as a protection that would activate correctly -- so whoever loosens
    # pause_pairing's overlap rule is forced to look at this line rather than silently inherit a
    # now-unsound one.
    first_ts = events[0].event_timestamp_relative_ms
    last_ts = events[-1].event_timestamp_relative_ms
    elapsed_ms = last_ts - first_ts
    pause_starts = [e for e in events if e.event_type == "pause_started"]
    pause_ends = [e for e in events if e.event_type == "pause_ended"]
    non_technical_inactive_ms = sum(
        end.event_timestamp_relative_ms - start.event_timestamp_relative_ms
        for start, end in zip(pause_starts, pause_ends)
        if not start.technical_flag
    )
    if non_technical_inactive_ms > elapsed_ms:
        raise TelemetryStreamRejectedError(
            "inactivity_plausibility_structural",
            f"non-technical inactive time {non_technical_inactive_ms}ms exceeds the stream's own "
            f"elapsed span {elapsed_ms}ms",
        )


def validate_clock_discipline(records: Sequence[CGameplayEventRecord]) -> None:
    """The ORDINAL half of clock discipline (H6-b): server-observed receipt order
    (``ProvenanceMixin.created_at_utc``, H6-a's own finding -- already the receipt time, no
    migration) must not CONTRADICT the client-claimed order (``event_index``, which
    ``list_ordered_for_instance`` already orders by). Operates on the RAW persisted row, not the
    domain ``GameplayEvent`` (which carries no receipt timestamp) -- a separate function from
    ``validate_event_stream_structurally`` for exactly that reason. Does NOT check the MAGNITUDE
    half (is the claimed elapsed client time plausible against real elapsed wall-clock time, within
    some tolerance) -- BLOCKED, no governed drift tolerance exists anywhere (H2-a's own search)."""
    for prev, cur in zip(records, records[1:]):
        if cur.created_at_utc < prev.created_at_utc:
            raise TelemetryStreamRejectedError(
                "clock_discipline_ordinal",
                f"event_index {cur.event_index}'s receipt time {cur.created_at_utc} precedes "
                f"event_index {prev.event_index}'s {prev.created_at_utc}",
            )


async def get_derivable_history_for_session(
    session: AsyncSession, *, c_session_id: UUID
) -> Sequence[CTaskOpportunitySummaryRecord]:
    """J1-2/J1-4: THE ONE GUARDED ACCESSOR permitted to call
    ``CTaskOpportunitySummaryRecordRepository.list_ordered_for_session`` under app/ (enforced by
    ``test_be2_architecture_guards.py``'s AST guard, mirroring the T4 evidence-construction guards
    exactly). J1-3: the verdict is ROW-ABSENCE -- no stored verdict field exists anywhere; a
    distrusted stream simply has no summary row (Phase 8's own validator, wired at the derivation
    trigger in summary_service.py, never let one be written). J1-4: OFFERED (every
    ``c_task_opportunities`` row for this session) minus DERIVABLE (every ``c_task_opportunity_
    summaries`` row) minus tasks never reached a terminal event leaves the GAP set -- a task that
    was offered, reached a terminal gameplay event (Q2/K2-d: read from ``c_gameplay_events`` via
    ``has_terminal_for_instance``, resting on the Phase 3b partial-unique index -- self-sufficient,
    never dependent on ``c_task_opportunities.terminal_reason``, which K5's own register entry
    below finds is never populated by any code path) but has no summary row. A non-empty gap set
    RAISES ``DistrustedHistoryGapError`` rather than returning a truncated list -- never 1, 2, 4 for
    a distrusted task 3."""
    opportunities = await CTaskOpportunityRecordRepository(session).list_ordered_for_session(c_session_id)
    summaries = await CTaskOpportunitySummaryRecordRepository(session).list_ordered_for_session(c_session_id)
    derivable_indices = {s.task_index for s in summaries}

    instance_repo = CTaskInstanceRecordRepository(session)
    event_repo = CGameplayEventRecordRepository(session)
    gap_indices: list[int] = []
    for opportunity in opportunities:
        if opportunity.task_index in derivable_indices:
            continue
        instance = await instance_repo.find_by_opportunity(opportunity.c_task_opportunity_id)
        if instance is None:
            continue  # never started -- not a gap, simply not yet attempted
        if await event_repo.has_terminal_for_instance(instance.c_task_instance_id):
            gap_indices.append(opportunity.task_index)

    if gap_indices:
        raise DistrustedHistoryGapError(c_session_id=c_session_id, gap_task_indices=tuple(sorted(gap_indices)))

    return summaries
