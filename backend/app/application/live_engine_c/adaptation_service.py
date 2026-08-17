"""Component C Phase 6b: ``build_policy_evidence`` -> ``decide_adaptation`` per completed task,
persisted to ``c_policy_decisions``/``c_safety_events``.

v3.0 §11 Phase 6 scope, quoted: "build_policy_evidence -> decide_adaptation per completed task;
persist AdaptationDecision to c_policy_decisions and interventions to c_safety_events." "history
passed to build_policy_evidence is the full running session history including the just-finished
task (§7.2)." "increase_block_remaining is persisted and fed back as the next
evidence.safety_increase_block_remaining (§7.3)."

BOTH PORTS THROUGH THE ADAPTER (T6-a's own discipline, carried forward): this module never
reimplements evidence assembly or the policy/safety pipeline -- it calls
``LiveEngineCAdapter.build_policy_evidence``/``compute_rolling_strain``/``decide_adaptation``
(``PolicyEvidencePort``/``AdaptationPort``, built and unwired since Phase 1b, called for the
first time here) and persists their output verbatim.

X8-c (owner condition): NO threshold value is defaulted or hardcoded anywhere in this module.
``policy_mode``/``policy_config``/``safety_config``/``selection_config``/``evidence_window_config``
are all REQUIRED, no-default parameters (W1-shape, S8-a's guard extension covers
``safety_config``/``default_safety_config`` specifically).

DISCLOSED (X2-3, carried from ``session_lifecycle.py``): the session-start gate (S2/X4) means no
session can exist in production for this module's own per-task call to ever run against. This
module is exercised end-to-end only via direct calls with ``smoke_mode``-shaped test fixtures,
mirroring Phase 5's own "COMPLETE, TESTED, DELIBERATELY NOT LIVE" serving path precedent.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.live_engine_c.mastery_fixture import FIXTURE_MASTERY_SOURCE_STUDENT_ID
from app.application.live_engine_c.session_lifecycle import _provenance
from app.domain.live_engine_c.types import (
    EvidenceWindowConfig,
    LearnerState,
    PolicyConfig,
    PolicyMode,
    SafetyConfig,
    SeedLineage,
    SelectionConfig,
    SessionMode,
    SessionPhase,
    TaskOpportunitySummary,
)
from app.infrastructure.live_engine_c.adapter import LiveEngineCAdapter
from app.infrastructure.persistence_models import (
    CPolicyDecisionRecord,
    CSafetyEventRecord,
    CTaskOpportunitySummaryRecord,
)
from app.infrastructure.repositories import (
    CPolicyDecisionRecordRepository,
    CSafetyEventRecordRepository,
    CTaskOpportunitySummaryRecordRepository,
)

# X7-a: the safety-reason tokens are STABLE, PINNED literals -- verified by direct read of
# safety/controller.py (byte-identical, vendored code, never edited by this project). The
# AdaptationPort/decide_adaptation composed AdaptationDecision does NOT expose
# activate_recovery_flag/request_safe_termination as their own booleans (only the pinned
# SafetyDecision -- an internal package type never crossing X-3 on its own -- carries them); this
# module and its tests detect them from safety_reason's own semicolon-joined reason tokens
# instead, since that IS what crosses the boundary. Never re-derived, never guessed: each token
# below is the exact string controller.py's own `reasons.append(...)` calls use.
RECOVERY_TRIGGER_REASON_TOKENS = ("consecutive_error_safety_trigger", "rolling_strain_safety_trigger")
INCREASE_VETO_REASON_TOKEN = "increase_blocked_active_window"
TECHNICAL_NEUTRALIZED_REASON_TOKEN = "technical_issue_neutralized"
SAFE_TERMINATION_REASON_TOKEN = "safe_session_termination_requested"


def _to_domain_summary(
    record: CTaskOpportunitySummaryRecord, *, student_id: str, intervention_session_id: str, c_session_id: str
) -> TaskOpportunitySummary:
    """Reconstructs the domain ``TaskOpportunitySummary`` the adapter's ``PolicyEvidencePort``
    expects, from one persisted row -- identity fields supplied by the caller (Phase 3a's
    minimal-FK style, same reasoning as every other ``_to_domain_*`` helper in this codebase),
    every OTHER field a straight ``record.<field>`` copy."""
    return TaskOpportunitySummary(
        student_id=student_id,
        intervention_session_id=intervention_session_id,
        c_session_id=c_session_id,
        game_task_instance_id=f"{c_session_id}-T{record.task_index:03d}-X001",
        task_index=record.task_index,
        task_offered=record.task_offered,
        task_started=record.task_started,
        task_completed=record.task_completed,
        task_skipped=record.task_skipped,
        task_quit=record.task_quit,
        technical_issue=record.technical_issue,
        correct_task=record.correct_task,
        total_attempts=record.total_attempts,
        retry_count=record.retry_count,
        scaffold_requested=record.scaffold_requested,
        scaffold_count=record.scaffold_count,
        highest_scaffold_level=record.highest_scaffold_level,  # type: ignore[arg-type]
        c_answer_changes=record.c_answer_changes,
        task_latency_sec=record.task_latency_sec,
        inactive_time_sec=record.inactive_time_sec,
        inactivity_periods=record.inactivity_periods,
        quit_after_error=record.quit_after_error,
        terminal_reason=record.terminal_reason,  # type: ignore[arg-type]
        first_attempt_correct=record.first_attempt_correct,
        final_attempt_correct=record.final_attempt_correct,
        consecutive_error_max_within_task=record.consecutive_error_max_within_task,
    )


async def build_evidence_for_session(
    session: AsyncSession,
    *,
    adapter: LiveEngineCAdapter,
    c_session_id: UUID,
    student_id: str,
    intervention_session_id: str,
    stu_session_id: str,
    session_mode: SessionMode,
    session_phase: SessionPhase,
    current_difficulty_level: int,
    is_recovery_context: bool,
    prior_session_end_state: Optional[LearnerState],
    evidence_window_config: EvidenceWindowConfig,
):
    """v3.0 §7.2: "history passed to build_policy_evidence is the full running session history
    including the just-finished task." Reads EVERY persisted summary for the session, in order --
    never filtered here (the adapter's own windowing, criterion 2's own subject, happens inside
    the shipped pipeline/evidence.py, not in this function). ``safety_increase_block_remaining``
    is read from the most recent persisted ``CPolicyDecisionRecord`` for this session (0 if this
    is the session's first decision -- S8-b's own feedback loop, fed back here, never a fresh
    default each call)."""
    summaries = await CTaskOpportunitySummaryRecordRepository(session).list_ordered_for_session(c_session_id)
    history = [
        _to_domain_summary(
            record, student_id=student_id, intervention_session_id=intervention_session_id,
            c_session_id=stu_session_id,
        )
        for record in summaries
    ]
    most_recent_decision = await CPolicyDecisionRecordRepository(session).most_recent_for_session(c_session_id)
    safety_increase_block_remaining = (
        most_recent_decision.increase_block_remaining if most_recent_decision is not None else 0
    )
    return adapter.build_policy_evidence(
        session_mode=session_mode,
        session_phase=session_phase,
        current_difficulty_level=current_difficulty_level,
        history=history,
        is_recovery_context=is_recovery_context,
        prior_session_end_state=prior_session_end_state,
        safety_increase_block_remaining=safety_increase_block_remaining,
        config=evidence_window_config,
    )


async def decide_and_persist_adaptation(
    session: AsyncSession,
    *,
    adapter: LiveEngineCAdapter,
    c_session_id: UUID,
    c_task_opportunity_id: UUID,
    policy_mode: PolicyMode,
    evidence,
    current_difficulty_level: int,
    seed_lineage: SeedLineage,
    policy_config: PolicyConfig,
    safety_config: SafetyConfig,
    selection_config: SelectionConfig,
    request_id: str,
) -> CPolicyDecisionRecord:
    """v3.0 §11 Phase 6 scope: "persist AdaptationDecision to c_policy_decisions and
    interventions to c_safety_events." S8-c: ``decide_adaptation`` (the ONE function that ever
    produces an ``AdaptationDecision``, ``adaptation.py``, pinned) unconditionally calls
    ``apply_safety`` internally -- there is no code path by which this function's own caller
    could ever receive a decision safety was not applied to; this is a structural property of the
    composed, pinned function, not a check this module performs."""
    decision = adapter.decide_adaptation(
        policy_mode=policy_mode,
        evidence=evidence,
        current_difficulty_level=current_difficulty_level,
        seed_lineage=seed_lineage,
        policy_config=policy_config,
        safety_config=safety_config,
        selection_config=selection_config,
    )

    decision_id = uuid4()
    record = CPolicyDecisionRecord(
        c_policy_decision_id=decision_id,
        c_session_id=c_session_id,
        c_task_opportunity_id=c_task_opportunity_id,
        policy_mode=decision.policy_mode,
        policy_version=decision.policy_version,
        rl_state=dict(decision.rl_state) if decision.rl_state is not None else None,
        selected_action=decision.selected_action,
        applied_action=decision.applied_action,
        action_overridden=decision.action_overridden,
        safety_reason=decision.safety_reason,
        difficulty_before=decision.difficulty_before,
        difficulty_after=decision.difficulty_after,
        rolling_strain_bucket=decision.rolling_strain_bucket,
        session_start_state_bucket=decision.session_start_state_bucket,
        increase_block_remaining=decision.increase_block_remaining,
        internal_reward=decision.internal_reward,
        seed_lineage_global_seed=decision.seed_lineage.global_seed,
        seed_lineage_path=[list(pair) for pair in decision.seed_lineage.path],
        seed_lineage_seed=decision.seed_lineage.seed,
        evidence_snapshot={
            "session_mode": evidence.session_mode,
            "session_phase": evidence.session_phase,
            "current_difficulty_level": evidence.current_difficulty_level,
            "recent_correctness_rate": evidence.recent_correctness_rate,
            "recent_avg_attempts": evidence.recent_avg_attempts,
            "recent_inactivity_periods": evidence.recent_inactivity_periods,
            "recent_scaffold_use_count": evidence.recent_scaffold_use_count,
            "recent_consecutive_error_max": evidence.recent_consecutive_error_max,
            "rolling_strain_score": evidence.rolling_strain_score,
            "prior_session_end_state": evidence.prior_session_end_state,
            "is_recovery_context": evidence.is_recovery_context,
            "technical_issue_current_task": evidence.technical_issue_current_task,
            "safety_increase_block_remaining": evidence.safety_increase_block_remaining,
        },
        **_provenance("c_policy_decision", decision_id, request_id, "c_task.adaptation_decided"),
    )
    await CPolicyDecisionRecordRepository(session).add(record)

    reason_text = decision.safety_reason or ""
    intervened = (
        any(token in reason_text for token in RECOVERY_TRIGGER_REASON_TOKENS)
        or INCREASE_VETO_REASON_TOKEN in reason_text
        or TECHNICAL_NEUTRALIZED_REASON_TOKEN in reason_text
        or SAFE_TERMINATION_REASON_TOKEN in reason_text
        or decision.action_overridden
    )
    if intervened:
        event_id = uuid4()
        safety_event = CSafetyEventRecord(
            c_safety_event_id=event_id,
            c_session_id=c_session_id,
            c_policy_decision_id=decision_id,
            trigger_reason=decision.safety_reason or "action_overridden_no_reason_token",
            action_taken=decision.applied_action,
            difficulty_before=decision.difficulty_before,
            difficulty_after=decision.difficulty_after,
            **_provenance("c_safety_event", event_id, request_id, "c_task.safety_intervened"),
        )
        await CSafetyEventRecordRepository(session).add(safety_event)

    return record
