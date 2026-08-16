"""Domain ports over the reviewed live-safe Component C capabilities (Phase 1 batch 1b).

One small ``Protocol`` per §7 capability area. Every method signature uses only backend domain
types (``app.domain.live_engine_c.types``) — never the vendored package's Pydantic models, and
never ``models.contracts.BToCMasteryPayload`` (X-3; the seven mastery values cross this boundary
as a plain ``Mapping[str, float]`` — see the module docstring of
``app.domain.live_engine_c.types`` and ``app.infrastructure.live_engine_c.adapter._to_pkg_mastery_payload``).
The concrete implementation lives in ``app.infrastructure.live_engine_c.adapter``.
"""

from __future__ import annotations

from typing import Mapping, Optional, Protocol, Sequence

from .types import (
    ActivationDecision,
    AdaptationDecision,
    AggregationConfig,
    AttendanceStatus,
    Catalogue,
    ChildFacingReward,
    CompositeFormulaVersion,
    EngagementComponents,
    EvaluationResult,
    EvidenceWindowConfig,
    FrustrationComponents,
    GameTaskTemplate,
    GameplayEvent,
    GenerationConfig,
    Grade,
    LearnerSessionState,
    LearnerState,
    PolicyConfig,
    PolicyMode,
    PolicyObservableEvidence,
    PrerequisiteRedirectContext,
    RecoveryConfig,
    RewardOutcomeContext,
    SafetyConfig,
    ScaffoldConfig,
    ScaffoldDecisionContext,
    ScaffoldLevel,
    SeedLineage,
    SelectionConfig,
    SelectionResult,
    SessionAggregate,
    SessionMode,
    SessionPhase,
    StateReason,
    TaskInstance,
    TaskOpportunitySummary,
    TelemetryQualityStatus,
)


class CataloguePort(Protocol):
    """Catalogue loading and validation (v3.0 §7, Phase 2)."""

    def load(self, catalogue_path: str) -> Catalogue: ...

    def checksum(self, catalogue_path: str) -> str: ...

    def supported_template_ids(self) -> tuple[str, ...]:
        """Code-sourced (``component_c_generator.tasks.registry``), not catalogue-file-sourced
        -- the 21st adapter method (Phase 2)."""
        ...


class ActivationPort(Protocol):
    """Activation and grade eligibility (v3.0 §7, Phase 5). ``decide_activation`` takes the
    whole ``catalogue`` plus a template id (mirrors ``app.domain.live_engine``'s
    ``ActivationPort`` shape) rather than a pre-fetched template — the adapter re-derives the
    package-native template from the governed catalogue file, never hand-builds one from the
    trimmed domain type."""

    def decide_activation(
        self,
        catalogue: Catalogue,
        game_task_template_id: str,
        supported_template_ids: tuple[str, ...],
        grade: Grade,
    ) -> ActivationDecision: ...

    def eligible_templates(
        self, catalogue: Catalogue, grade: Grade, supported_template_ids: tuple[str, ...]
    ) -> tuple[GameTaskTemplate, ...]: ...


class SessionPhasePort(Protocol):
    """Cold-start / familiarization phase gate (v3.0 §7, Phase 4).

    ``selection_config`` is REQUIRED with NO DEFAULT on every method below (owner ruling, Phase 4
    work order, "W — OWNER-RULED... W1: SelectionConfig is a REQUIRED parameter with NO DEFAULT on
    every C application-layer path that needs it"). ``familiarization_window_by_grade`` is
    ENGINEERING_ASSUMPTION + CALIBRATION_PENDING; this port's shape defers that question, it does
    not resolve it — no value is approved by this port existing."""

    def decide_session_phase(
        self, eligible_combined_handoffs_completed: int, window_w: int
    ) -> str: ...

    def decide_next_session_phase(
        self,
        *,
        session_mode: SessionMode,
        grade: Grade,
        state: LearnerSessionState,
        selection_config: SelectionConfig,
    ) -> SessionPhase:
        """Translates ``component_c_generator.pipeline.session_state.decide_next_session_phase``
        (kept verbatim in the shipped wheel specifically for this call, per the master build
        plan's Batch 1a trim table). ``c_only`` always maps to the literal ``"c_only"``; combined
        calls ``decide_session_phase`` with the current N and ``selection_config``'s window for
        this grade. Do not reimplement this branching in application code — call this instead."""
        ...

    def is_eligible_combined_handoff(
        self,
        session_mode: SessionMode,
        b_payload_valid: bool,
        attendance_status: AttendanceStatus,
        technical_blocked_bootstrap: bool,
    ) -> bool:
        """Translates ``component_c_generator.pipeline.session_state.is_eligible_combined_handoff``
        — the five-condition ELIGIBLE COMPLETED COMBINED B->C HANDOFF predicate (cold-start
        assessment §5). Do not reimplement this predicate in application code — call this
        instead."""
        ...


class SelectionPort(Protocol):
    """The cold-start chokepoint select_task (v3.0 §7.1, Phase 5).

    ``mastery_payload`` crosses THIS PORT boundary as a plain ``Mapping[str, float]`` keyed by
    the seven frozen skill names — that is the INGRESS shape only (SUPERVISOR RULING (lead), R2,
    Phase 4 work order). It is not the shape the engine consumes: internally, the adapter
    assembles the full mapping into a payload and calls ``validate_payload(payload, "b_to_c")``,
    and the VALIDATED ``BToCMasteryPayload`` — never the raw mapping — is what actually reaches
    the package's engine functions. Nothing downstream of the adapter accepts an unvalidated
    mapping. Building the package's ``BToCMasteryPayload`` also needs B's own identity fields
    (``mastery_source_student_id`` matches B's ``STU-####`` pattern,
    ``mastery_source_intervention_session_id`` matches B's ``STU-####-I-###`` pattern,
    ``mastery_source_intervention_session_number``) — these are B-owned identifiers, NOT the
    same values as this call's own ``student_id``/``c_session_id``, and are therefore separate,
    explicit parameters rather than reused/derived from C's own identifiers. Required only when
    ``mastery_payload`` is not ``None``."""

    def select_task(
        self,
        *,
        session_mode: SessionMode,
        session_phase: str,
        grade: Grade,
        catalogue: Catalogue,
        supported_template_ids: tuple[str, ...],
        student_id: str,
        c_session_id: str,
        task_index: int,
        mastery_payload: Optional[Mapping[str, float]],
        mastery_source_student_id: Optional[str],
        mastery_source_intervention_session_id: Optional[str],
        mastery_source_intervention_session_number: Optional[int],
        sessions_since_last_practice: Mapping[str, int],
        component_c_session_lineage: SeedLineage,
        task_opportunity_lineage: SeedLineage,
        generation_config: GenerationConfig,
        selection_config: SelectionConfig,
    ) -> SelectionResult: ...


class TaskConstructionPort(Protocol):
    """Deterministic single-instance task construction (v3.0 §7, Phase 5). Takes ``catalogue``
    plus a template id, same reasoning as ``ActivationPort.decide_activation`` above."""

    def build_task_instance(
        self,
        catalogue: Catalogue,
        game_task_template_id: str,
        seed_lineage: SeedLineage,
        grade: Grade,
        difficulty_level: int,
        student_id: str,
        c_session_id: str,
        task_index: int,
        config: GenerationConfig,
    ) -> TaskInstance: ...


class EvaluationPort(Protocol):
    """Server-owned correctness evaluation (v3.0 §7, Phase 5)."""

    def evaluate(
        self, task_instance: TaskInstance, learner_action: Mapping[str, object]
    ) -> EvaluationResult: ...


class SummaryPort(Protocol):
    """Pure gameplay-event -> task-opportunity-summary derivation (v3.0 §7, Phase 8)."""

    def derive_task_opportunity_summary(self, events: Sequence[GameplayEvent]) -> TaskOpportunitySummary: ...


class PolicyEvidencePort(Protocol):
    """The C-4 chokepoint: policy-observable evidence assembly and rolling strain (v3.0 §7.2,
    Phase 6)."""

    def build_policy_evidence(
        self,
        *,
        session_mode: SessionMode,
        session_phase: SessionPhase,
        current_difficulty_level: int,
        history: Sequence[TaskOpportunitySummary],
        is_recovery_context: bool,
        prior_session_end_state: Optional[LearnerState],
        safety_increase_block_remaining: int,
        config: EvidenceWindowConfig,
    ) -> PolicyObservableEvidence: ...

    def compute_rolling_strain(self, recent_summaries: Sequence[TaskOpportunitySummary]) -> float: ...


class AdaptationPort(Protocol):
    """Policy proposal + hard safety layer, assembled as one call (v3.0 §7.3, Phase 6)."""

    def decide_adaptation(
        self,
        *,
        policy_mode: PolicyMode,
        evidence: PolicyObservableEvidence,
        current_difficulty_level: int,
        seed_lineage: SeedLineage,
        policy_config: PolicyConfig,
        safety_config: SafetyConfig,
        selection_config: SelectionConfig,
    ) -> AdaptationDecision: ...


class ScaffoldPort(Protocol):
    """The C0-C4 scaffold ladder decision (v3.0 §7, Phase 7)."""

    def decide_scaffold_level(
        self, context: ScaffoldDecisionContext, config: ScaffoldConfig
    ) -> ScaffoldLevel: ...


class RecoveryPort(Protocol):
    """C4 recovery task construction (v3.0 §7, Phase 7)."""

    def build_recovery_task(
        self,
        parent_instance: TaskInstance,
        skill_id: str,
        task_index: int,
        catalogue: Catalogue,
        supported_template_ids: tuple[str, ...],
        generation_config: GenerationConfig,
        seed_lineage: SeedLineage,
        recovery_config: RecoveryConfig,
        *,
        safety_required: bool = False,
        prerequisite_context: Optional[PrerequisiteRedirectContext] = None,
    ) -> TaskInstance: ...


class RewardPort(Protocol):
    """Safe child-facing reward decision (v3.0 §7, Phase 7)."""

    def decide_child_facing_reward(self, context: RewardOutcomeContext) -> Optional[ChildFacingReward]: ...


class AggregationPort(Protocol):
    """Session aggregate derivation (v3.0 §7, Phase 9)."""

    def derive_session_aggregate(
        self,
        events: Sequence[GameplayEvent],
        summaries: Sequence[TaskOpportunitySummary],
        adaptation_decisions: Sequence[AdaptationDecision],
        *,
        time_in_target_band_sec: float,
        safety_override_count: int,
        inactive_time_available: bool,
        config: AggregationConfig,
    ) -> SessionAggregate: ...


class CompositePort(Protocol):
    """C-COMP-v1 / C-LS-v1: engagement, frustration, telemetry quality, and learner state
    (v3.0 §7, Phase 9)."""

    def compute_engagement(
        self, aggregate: SessionAggregate, formula_version: CompositeFormulaVersion
    ) -> tuple[EngagementComponents, float]: ...

    def compute_frustration(
        self, aggregate: SessionAggregate, formula_version: CompositeFormulaVersion
    ) -> tuple[FrustrationComponents, float]: ...

    def decide_telemetry_quality_status(
        self,
        session_technical_issue_flag: bool,
        task_opportunity_count: int,
        completed_task_count: int,
        session_duration_sec: float,
        accuracy_rate: Optional[float],
        task_completion_rate: Optional[float],
    ) -> TelemetryQualityStatus: ...

    def decide_learner_state(
        self,
        telemetry_quality_status: TelemetryQualityStatus,
        safety_override_count: int,
        consecutive_error_max: int,
        quit_after_error: bool,
        difficulty_floor_hits: int,
        task_completion_rate: float,
        inactivity_periods: int,
        engagement_score: Optional[float],
        frustration_index: Optional[float],
    ) -> tuple[Optional[LearnerState], StateReason]: ...
