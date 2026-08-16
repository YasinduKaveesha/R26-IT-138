"""``LiveEngineCAdapter`` — binds every ``app.domain.live_engine_c`` port to the vendored,
reviewed live-safe subset of the Component C generator (``component_c_generator``, packaged as
``prabathi-component-c-live-engine``; see
``backend/provenance/component-c-live-engine-manifest.json``).

No formula is copied or rewritten here: every method below calls straight through to the
package's own pure functions. This module's job is exactly what
Component_C_Master_Build_Plan_v3.0.md §11 Phase 1 item 2 asks for: import surface and DTO
mapping. It contains no route, no service, no persistence, no caller, no session logic, no
orchestration, and no mutable instance state — every method is traceable to exactly one row of
the 20-call §7 table this batch verified against the installed wheel.

X-1: this is the ONLY file that imports ``component_c_generator`` (enforced by
``backend/tests/test_be2_architecture_guards.py``). X-3: no package type — neither
``component_c_generator``'s nor ``models.contracts.BToCMasteryPayload`` — crosses into
``app.domain``; every package object is mapped to/from a backend-owned dataclass before or after
crossing this boundary.

SEED DERIVATION IS OUT OF SCOPE. The domain ``SeedLineage`` type is a plain three-field mirror of
the package's ``CSeedLineage``. This file references none of
``component_c_generator.seeds.derive_child_lineage``, ``seeds.SeedManager``, ``seeds.rng_from``,
or ``seeds.SUBSTREAMS`` — none of the 20 verified §7 calls name them, and inventing a wrapper for
them here would be inventing a call not in §7 (G3). Obtaining a real seed value is left to
whichever future phase's work order explicitly authorizes that call
(``backend/tests/test_be2_architecture_guards.py::test_adapter_references_no_seed_derivation_symbol``
asserts this by AST, not by review).

MASTERY PAYLOAD — A DELIBERATELY ISOLATED, PROVISIONAL RESOLUTION. §5 says Component C consumes
``models.contracts.BToCMasteryPayload`` and must not re-declare that frozen contract; X-3 says no
package type may cross into ``app.domain``. These two rules conflict for this one type. The
supervisor's provisional ruling (pending owner confirmation) is that the seven mastery values
cross the adapter boundary as a plain ``Mapping[str, float]`` keyed by the seven frozen skill
names, and this ONE function — ``_to_pkg_mastery_payload`` — is the only place anywhere that
constructs ``models.contracts.BToCMasteryPayload``. If the owner overturns the ruling, this is
the only function that needs to change.

CONFIG TYPES CARRY NO DEFAULT. Every ``_to_pkg_*_config`` helper below performs a pure 1:1 field
copy from the caller-supplied domain config to the package's pydantic config model. No threshold,
weight, window, or cap is ever chosen or defaulted here — Component C is PROPOSED, not approved
(v3.0 §2), and a hardcoded value in this file would be recording an unapproved parameter (G1).
Unlike ``app.infrastructure.live_engine.adapter``, which legitimately hardcodes B's FROZEN,
already-approved sequencing weights, nothing here is approved, so nothing here is hardcoded.
"""

from __future__ import annotations

from typing import Mapping, Optional, Sequence

from component_c_generator.adaptation import decide_adaptation as _pkg_decide_adaptation
from component_c_generator.aggregation.derive import (
    derive_session_aggregate as _pkg_derive_session_aggregate,
)
from component_c_generator.behaviour.summary import (
    derive_task_opportunity_summary as _pkg_derive_task_opportunity_summary,
)
from component_c_generator.catalogue.loader import (
    CatalogueValidationError as _PkgCatalogueValidationError,
    catalogue_file_checksum as _pkg_catalogue_file_checksum,
    load_catalogue as _pkg_load_catalogue,
)
from component_c_generator.composites.engagement_frustration import (
    compute_engagement as _pkg_compute_engagement,
    compute_frustration as _pkg_compute_frustration,
)
from component_c_generator.composites.learner_state import (
    decide_learner_state as _pkg_decide_learner_state,
    decide_telemetry_quality_status as _pkg_decide_telemetry_quality_status,
)
from component_c_generator.eligibility import (
    decide_activation as _pkg_decide_activation,
    eligible_templates as _pkg_eligible_templates,
)
from component_c_generator.evaluation import (
    UnknownTemplateError as _PkgEvalUnknownTemplateError,
    evaluate as _pkg_evaluate,
)
from component_c_generator.generation import (
    TaskGenerationTechnicalError as _PkgTaskGenerationTechnicalError,
    UnsupportedTemplateError as _PkgUnsupportedTemplateError,
    build_task_instance as _pkg_build_task_instance,
)
from component_c_generator.pipeline.evidence import (
    build_policy_evidence as _pkg_build_policy_evidence,
    compute_rolling_strain as _pkg_compute_rolling_strain,
)
from component_c_generator.policy.rule_based import (
    QLearningDisabledError as _PkgQLearningDisabledError,
    UnknownPolicyModeError as _PkgUnknownPolicyModeError,
)
from component_c_generator.rewards import (
    decide_child_facing_reward as _pkg_decide_child_facing_reward,
)
from component_c_generator.scaffolds.ladder import (
    decide_scaffold_level as _pkg_decide_scaffold_level,
)
from component_c_generator.scaffolds.recovery import (
    NoEligibleRecoveryTemplateError as _PkgNoEligibleRecoveryTemplateError,
    PrerequisiteRedirectContext as _PkgPrerequisiteRedirectContext,
    RecoveryPreconditionError as _PkgRecoveryPreconditionError,
    build_recovery_task as _pkg_build_recovery_task,
)
from component_c_generator.selection.phase import (
    decide_session_phase as _pkg_decide_session_phase,
)
from component_c_generator.selection.selector import (
    SelectionInputError as _PkgSelectionInputError,
    select_task as _pkg_select_task,
)
from component_c_generator.tasks.registry import (
    supported_template_ids as _pkg_supported_template_ids,
)

from models.contracts import BToCMasteryPayload as _PkgBToCMasteryPayload

from app.domain.live_engine_c.errors import (
    CatalogueUnavailableError,
    NoEligibleRecoveryTemplateError,
    QLearningDisabledError,
    RecoveryPreconditionError,
    SelectionInputError,
    TaskGenerationTechnicalError,
    UnknownPolicyModeError,
    UnknownTemplateError,
    UnsupportedTemplateError,
)
from app.domain.live_engine_c.types import (
    ActivationDecision,
    AdaptationDecision,
    AggregationConfig,
    Catalogue,
    ChildFacingReward,
    CompositeFormulaVersion,
    EngagementComponents,
    EvaluationResult,
    EvidenceWindowConfig,
    FrustrationComponents,
    GameFamily,
    GameTaskTemplate,
    GenerationConfig,
    Grade,
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
    TemplateGenerationParams,
)


def _load_package_catalogue(source_path: str):
    """Re-load the package's own ``LoadedCatalogue`` from the same governed path.

    Mirrors ``app.infrastructure.live_engine.adapter._load_package_catalogue``: every port
    method that needs a package-native catalogue/template object re-derives it from
    ``source_path`` rather than reconstructing a package Pydantic model by hand from the trimmed
    domain ``Catalogue`` — so the object handed to the reviewed package functions is always the
    real, fully-validated loader output.
    """
    try:
        return _pkg_load_catalogue(source_path)
    except _PkgCatalogueValidationError as exc:
        raise CatalogueUnavailableError(str(exc)) from exc


def _template_by_id(pkg_catalogue, game_task_template_id: str):
    template = pkg_catalogue.by_id(game_task_template_id)
    if template is None:
        raise UnknownTemplateError(f"unknown game_task_template_id: {game_task_template_id!r}")
    return template


def _map_game_family(family) -> GameFamily:
    return GameFamily(
        game_family_id=family.game_family_id,
        family_name=family.family_name,
        template_id_prefix=family.template_id_prefix,
    )


def _map_game_task_template(template) -> GameTaskTemplate:
    return GameTaskTemplate(
        game_family_id=template.game_family_id,
        family_name=template.family_name,
        game_task_template_id=template.game_task_template_id,
        template_title=template.template_title,
        primary_skill_ids=tuple(template.primary_skill_ids),
        curriculum_node_ids=tuple(template.curriculum_node_ids),
        grade_scope_text=template.grade_scope_text,
        status=template.status,
        status_note=template.status_note,
        functional_role=template.functional_role,
        representations=tuple(template.representations),
        representations_note=template.representations_note,
        learner_action=template.learner_action,
        correctness=template.correctness,
        error_signatures=(
            tuple(template.error_signatures) if template.error_signatures is not None else None
        ),
        main_difficulty_levers=template.main_difficulty_levers,
        recovery=template.recovery,
        eligible_grades=tuple(template.eligible_grades),
        grade_gate_status=template.grade_gate_status,
    )


def _map_catalogue(catalogue) -> Catalogue:
    return Catalogue(
        catalogue_version=catalogue.catalogue_version,
        catalogue_status=catalogue.catalogue_status,
        source_path=catalogue.source_path,
        skills=tuple(catalogue.skills),
        families=tuple(_map_game_family(f) for f in catalogue.families),
        templates=tuple(_map_game_task_template(t) for t in catalogue.templates),
    )


def _to_pkg_seed_lineage(lineage: SeedLineage):
    from component_c_generator.models.seed import CSeedLineage as _PkgCSeedLineage

    return _PkgCSeedLineage(
        global_seed=lineage.global_seed,
        path=lineage.path,
        seed=lineage.seed,
    )


def _to_domain_seed_lineage(lineage) -> SeedLineage:
    return SeedLineage(
        global_seed=lineage.global_seed,
        path=tuple(lineage.path),
        seed=lineage.seed,
    )


def _map_activation_decision(decision) -> ActivationDecision:
    return ActivationDecision(
        game_task_template_id=decision.game_task_template_id,
        recognized=decision.recognized,
        generation_supported=decision.generation_supported,
        grade_eligible=decision.grade_eligible,
        curriculum_active=decision.curriculum_active,
        catalogue_status_ok=decision.catalogue_status_ok,
        calibration_restricted=decision.calibration_restricted,
        active=decision.active,
        reason=decision.reason,
    )


def _map_task_instance(instance) -> TaskInstance:
    return TaskInstance(
        game_family_id=instance.game_family_id,
        game_task_template_id=instance.game_task_template_id,
        game_task_instance_id=instance.game_task_instance_id,
        template_version=instance.template_version,
        catalogue_version=instance.catalogue_version,
        generator_version=instance.generator_version,
        seed_lineage=_to_domain_seed_lineage(instance.seed_lineage),
        student_id=instance.student_id,
        c_session_id=instance.c_session_id,
        task_index=instance.task_index,
        skill_id=instance.skill_id,
        curriculum_node_id=instance.curriculum_node_id,
        grade_scope=instance.grade_scope,
        difficulty_level=instance.difficulty_level,
        difficulty_vector=dict(instance.difficulty_vector),
        functional_role=instance.functional_role,
        representation_mode=instance.representation_mode,
        prompt_payload=dict(instance.prompt_payload),
        interactive_assets=dict(instance.interactive_assets),
        correct_answer_payload=dict(instance.correct_answer_payload),
        correctness_function_id=instance.correctness_function_id,
        valid_action_space=dict(instance.valid_action_space),
        completion_condition=instance.completion_condition,
        failure_condition=instance.failure_condition,
        scaffold_state=instance.scaffold_state,
        recovery_parent_instance_id=instance.recovery_parent_instance_id,
        technical_status=instance.technical_status,
    )


def _to_pkg_task_instance(instance: TaskInstance):
    from component_c_generator.models.task_instance import GameTaskInstance as _PkgGameTaskInstance

    return _PkgGameTaskInstance(
        game_family_id=instance.game_family_id,
        game_task_template_id=instance.game_task_template_id,
        game_task_instance_id=instance.game_task_instance_id,
        template_version=instance.template_version,
        catalogue_version=instance.catalogue_version,
        generator_version=instance.generator_version,
        seed_lineage=_to_pkg_seed_lineage(instance.seed_lineage),
        student_id=instance.student_id,
        c_session_id=instance.c_session_id,
        task_index=instance.task_index,
        skill_id=instance.skill_id,
        curriculum_node_id=instance.curriculum_node_id,
        grade_scope=instance.grade_scope,
        difficulty_level=instance.difficulty_level,
        difficulty_vector=dict(instance.difficulty_vector),
        functional_role=instance.functional_role,
        representation_mode=instance.representation_mode,
        prompt_payload=dict(instance.prompt_payload),
        interactive_assets=dict(instance.interactive_assets),
        correct_answer_payload=dict(instance.correct_answer_payload),
        correctness_function_id=instance.correctness_function_id,
        valid_action_space=dict(instance.valid_action_space),
        completion_condition=instance.completion_condition,
        failure_condition=instance.failure_condition,
        scaffold_state=instance.scaffold_state,
        recovery_parent_instance_id=instance.recovery_parent_instance_id,
        technical_status=instance.technical_status,
    )


def _map_selection_result(result) -> SelectionResult:
    return SelectionResult(
        session_phase=result.session_phase,
        selected_skill_id=result.selected_skill_id,
        selected_template_id=result.selected_template_id,
        initial_difficulty_level=result.initial_difficulty_level,
        mastery_context_mode=result.mastery_context_mode,
        mastery_selected_skill=result.mastery_selected_skill,
        task_instance=_map_task_instance(result.task_instance),
    )


def _map_evaluation_result(result) -> EvaluationResult:
    return EvaluationResult(
        game_task_instance_id=result.game_task_instance_id,
        game_task_template_id=result.game_task_template_id,
        correctness_function_id=result.correctness_function_id,
        learner_action=dict(result.learner_action),
        is_correct=result.is_correct,
        details=dict(result.details),
    )


def _to_pkg_gameplay_event(event):
    from component_c_generator.models.gameplay import GameplayEvent as _PkgGameplayEvent

    return _PkgGameplayEvent(
        event_id=event.event_id,
        event_type=event.event_type,
        event_index=event.event_index,
        student_id=event.student_id,
        intervention_session_id=event.intervention_session_id,
        c_session_id=event.c_session_id,
        game_task_instance_id=event.game_task_instance_id,
        task_index=event.task_index,
        attempt_number=event.attempt_number,
        event_timestamp_relative_ms=event.event_timestamp_relative_ms,
        action_payload=(dict(event.action_payload) if event.action_payload is not None else None),
        evaluation_payload=(
            dict(event.evaluation_payload) if event.evaluation_payload is not None else None
        ),
        scaffold_code=event.scaffold_code,
        technical_flag=event.technical_flag,
        terminal_reason=event.terminal_reason,
        seed_lineage=_to_pkg_seed_lineage(event.seed_lineage),
        generator_version=event.generator_version,
        config_checksum=event.config_checksum,
    )


def _map_task_opportunity_summary(summary) -> TaskOpportunitySummary:
    return TaskOpportunitySummary(
        student_id=summary.student_id,
        intervention_session_id=summary.intervention_session_id,
        c_session_id=summary.c_session_id,
        game_task_instance_id=summary.game_task_instance_id,
        task_index=summary.task_index,
        task_offered=summary.task_offered,
        task_started=summary.task_started,
        task_completed=summary.task_completed,
        task_skipped=summary.task_skipped,
        task_quit=summary.task_quit,
        technical_issue=summary.technical_issue,
        correct_task=summary.correct_task,
        total_attempts=summary.total_attempts,
        retry_count=summary.retry_count,
        scaffold_requested=summary.scaffold_requested,
        scaffold_count=summary.scaffold_count,
        highest_scaffold_level=summary.highest_scaffold_level,
        c_answer_changes=summary.c_answer_changes,
        task_latency_sec=summary.task_latency_sec,
        inactive_time_sec=summary.inactive_time_sec,
        inactivity_periods=summary.inactivity_periods,
        quit_after_error=summary.quit_after_error,
        terminal_reason=summary.terminal_reason,
        first_attempt_correct=summary.first_attempt_correct,
        final_attempt_correct=summary.final_attempt_correct,
        consecutive_error_max_within_task=summary.consecutive_error_max_within_task,
    )


def _to_pkg_task_opportunity_summary(summary: TaskOpportunitySummary):
    from component_c_generator.models.gameplay import (
        CTaskOpportunitySummary as _PkgCTaskOpportunitySummary,
    )

    return _PkgCTaskOpportunitySummary(
        student_id=summary.student_id,
        intervention_session_id=summary.intervention_session_id,
        c_session_id=summary.c_session_id,
        game_task_instance_id=summary.game_task_instance_id,
        task_index=summary.task_index,
        task_offered=summary.task_offered,
        task_started=summary.task_started,
        task_completed=summary.task_completed,
        task_skipped=summary.task_skipped,
        task_quit=summary.task_quit,
        technical_issue=summary.technical_issue,
        correct_task=summary.correct_task,
        total_attempts=summary.total_attempts,
        retry_count=summary.retry_count,
        scaffold_requested=summary.scaffold_requested,
        scaffold_count=summary.scaffold_count,
        highest_scaffold_level=summary.highest_scaffold_level,
        c_answer_changes=summary.c_answer_changes,
        task_latency_sec=summary.task_latency_sec,
        inactive_time_sec=summary.inactive_time_sec,
        inactivity_periods=summary.inactivity_periods,
        quit_after_error=summary.quit_after_error,
        terminal_reason=summary.terminal_reason,
        first_attempt_correct=summary.first_attempt_correct,
        final_attempt_correct=summary.final_attempt_correct,
        consecutive_error_max_within_task=summary.consecutive_error_max_within_task,
    )


def _map_policy_observable_evidence(evidence) -> PolicyObservableEvidence:
    return PolicyObservableEvidence(
        session_mode=evidence.session_mode,
        session_phase=evidence.session_phase,
        current_difficulty_level=evidence.current_difficulty_level,
        recent_correctness_rate=evidence.recent_correctness_rate,
        recent_avg_attempts=evidence.recent_avg_attempts,
        recent_inactivity_periods=evidence.recent_inactivity_periods,
        recent_scaffold_use_count=evidence.recent_scaffold_use_count,
        recent_consecutive_error_max=evidence.recent_consecutive_error_max,
        rolling_strain_score=evidence.rolling_strain_score,
        prior_session_end_state=evidence.prior_session_end_state,
        is_recovery_context=evidence.is_recovery_context,
        technical_issue_current_task=evidence.technical_issue_current_task,
        safety_increase_block_remaining=evidence.safety_increase_block_remaining,
    )


def _to_pkg_policy_observable_evidence(evidence: PolicyObservableEvidence):
    from component_c_generator.models.adaptation import (
        CPolicyObservableEvidence as _PkgCPolicyObservableEvidence,
    )

    return _PkgCPolicyObservableEvidence(
        session_mode=evidence.session_mode,
        session_phase=evidence.session_phase,
        current_difficulty_level=evidence.current_difficulty_level,
        recent_correctness_rate=evidence.recent_correctness_rate,
        recent_avg_attempts=evidence.recent_avg_attempts,
        recent_inactivity_periods=evidence.recent_inactivity_periods,
        recent_scaffold_use_count=evidence.recent_scaffold_use_count,
        recent_consecutive_error_max=evidence.recent_consecutive_error_max,
        rolling_strain_score=evidence.rolling_strain_score,
        prior_session_end_state=evidence.prior_session_end_state,
        is_recovery_context=evidence.is_recovery_context,
        technical_issue_current_task=evidence.technical_issue_current_task,
        safety_increase_block_remaining=evidence.safety_increase_block_remaining,
    )


def _map_adaptation_decision(decision) -> AdaptationDecision:
    return AdaptationDecision(
        decision_id=decision.decision_id,
        policy_mode=decision.policy_mode,
        policy_version=decision.policy_version,
        rl_state=(dict(decision.rl_state) if decision.rl_state is not None else None),
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
        seed_lineage=_to_domain_seed_lineage(decision.seed_lineage),
    )


def _to_pkg_adaptation_decision(decision: AdaptationDecision):
    from component_c_generator.models.adaptation import (
        AdaptationDecision as _PkgAdaptationDecision,
    )

    return _PkgAdaptationDecision(
        decision_id=decision.decision_id,
        policy_mode=decision.policy_mode,
        policy_version=decision.policy_version,
        rl_state=(dict(decision.rl_state) if decision.rl_state is not None else None),
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
        seed_lineage=_to_pkg_seed_lineage(decision.seed_lineage),
    )


def _to_pkg_scaffold_decision_context(context: ScaffoldDecisionContext):
    from component_c_generator.scaffolds.ladder import (
        ScaffoldDecisionContext as _PkgScaffoldDecisionContext,
    )

    return _PkgScaffoldDecisionContext(
        consecutive_incorrect_current_task=context.consecutive_incorrect_current_task,
        safety_forces_recovery=context.safety_forces_recovery,
    )


def _to_pkg_reward_outcome_context(context: RewardOutcomeContext):
    from component_c_generator.rewards import RewardOutcomeContext as _PkgRewardOutcomeContext

    return _PkgRewardOutcomeContext(
        task_completed_correctly=context.task_completed_correctly,
        is_recovery_task=context.is_recovery_task,
        retried_after_incorrect_then_continued=context.retried_after_incorrect_then_continued,
        continued_after_safety_event_without_quitting=(
            context.continued_after_safety_event_without_quitting
        ),
    )


def _map_child_facing_reward(reward) -> Optional[ChildFacingReward]:
    if reward is None:
        return None
    return ChildFacingReward(reward_reason=reward.reward_reason)


def _map_session_aggregate(aggregate) -> SessionAggregate:
    return SessionAggregate(
        task_opportunity_count=aggregate.task_opportunity_count,
        completed_task_count=aggregate.completed_task_count,
        correct_task_count=aggregate.correct_task_count,
        total_attempt_count=aggregate.total_attempt_count,
        accuracy_rate=aggregate.accuracy_rate,
        avg_attempts_per_task=aggregate.avg_attempts_per_task,
        task_completion_rate=aggregate.task_completion_rate,
        inactivity_periods=aggregate.inactivity_periods,
        inactive_time_sec=aggregate.inactive_time_sec,
        inactive_time_available=aggregate.inactive_time_available,
        session_duration_sec=aggregate.session_duration_sec,
        time_in_target_band_sec=aggregate.time_in_target_band_sec,
        consecutive_error_max=aggregate.consecutive_error_max,
        difficulty_floor_hits=aggregate.difficulty_floor_hits,
        quit_after_error=aggregate.quit_after_error,
        safety_override_count=aggregate.safety_override_count,
        c_mean_game_task_latency_sec=aggregate.c_mean_game_task_latency_sec,
        c_median_game_task_latency_sec=aggregate.c_median_game_task_latency_sec,
        current_difficulty_level=aggregate.current_difficulty_level,
        difficulty_trend=aggregate.difficulty_trend,
        session_technical_issue_flag=aggregate.session_technical_issue_flag,
    )


def _to_pkg_session_aggregate(aggregate: SessionAggregate):
    from component_c_generator.aggregation.models import CSessionAggregate as _PkgCSessionAggregate

    return _PkgCSessionAggregate(
        task_opportunity_count=aggregate.task_opportunity_count,
        completed_task_count=aggregate.completed_task_count,
        correct_task_count=aggregate.correct_task_count,
        total_attempt_count=aggregate.total_attempt_count,
        accuracy_rate=aggregate.accuracy_rate,
        avg_attempts_per_task=aggregate.avg_attempts_per_task,
        task_completion_rate=aggregate.task_completion_rate,
        inactivity_periods=aggregate.inactivity_periods,
        inactive_time_sec=aggregate.inactive_time_sec,
        inactive_time_available=aggregate.inactive_time_available,
        session_duration_sec=aggregate.session_duration_sec,
        time_in_target_band_sec=aggregate.time_in_target_band_sec,
        consecutive_error_max=aggregate.consecutive_error_max,
        difficulty_floor_hits=aggregate.difficulty_floor_hits,
        quit_after_error=aggregate.quit_after_error,
        safety_override_count=aggregate.safety_override_count,
        c_mean_game_task_latency_sec=aggregate.c_mean_game_task_latency_sec,
        c_median_game_task_latency_sec=aggregate.c_median_game_task_latency_sec,
        current_difficulty_level=aggregate.current_difficulty_level,
        difficulty_trend=aggregate.difficulty_trend,
        session_technical_issue_flag=aggregate.session_technical_issue_flag,
    )


def _map_engagement_components(components) -> EngagementComponents:
    return EngagementComponents(
        completion_component=components.completion_component,
        activity_component=components.activity_component,
        target_band_component=components.target_band_component,
        accuracy_component=components.accuracy_component,
    )


def _map_frustration_components(components) -> FrustrationComponents:
    return FrustrationComponents(
        error_run_component=components.error_run_component,
        excess_attempt_component=components.excess_attempt_component,
        inactivity_burden_component=components.inactivity_burden_component,
        floor_hit_component=components.floor_hit_component,
        quit_after_error_component=components.quit_after_error_component,
        safety_override_component=components.safety_override_component,
    )


def _to_pkg_mastery_payload(
    mastery_by_skill: Mapping[str, float],
    *,
    mastery_source_student_id: str,
    mastery_source_intervention_session_id: str,
    mastery_source_intervention_session_number: int,
) -> _PkgBToCMasteryPayload:
    """PROVISIONAL, SUPERVISOR-RULED, ISOLATED (see module docstring). The only function in this
    codebase that constructs ``models.contracts.BToCMasteryPayload``. If the owner overturns
    this ruling, this is the only function that needs to change.

    The three ``mastery_source_*`` identity fields are B's own — B's ``student_id`` matches
    ``^STU-[0-9]{4}$`` and B's ``intervention_session_id`` matches ``^STU-[0-9]{4}-I-[0-9]{3}$``,
    neither of which is the same value space as C's own ``student_id``/``c_session_id``. They
    must be supplied by the caller; this function never derives or invents them from C's own
    identifiers (G3)."""
    return _PkgBToCMasteryPayload(
        mastery_counting=mastery_by_skill["counting"],
        mastery_number_sense=mastery_by_skill["number_sense"],
        mastery_place_value=mastery_by_skill["place_value"],
        mastery_addition=mastery_by_skill["addition"],
        mastery_subtraction=mastery_by_skill["subtraction"],
        mastery_multiplication=mastery_by_skill["multiplication"],
        mastery_division=mastery_by_skill["division"],
        schema_version="2.1",
        student_id=mastery_source_student_id,
        intervention_session_id=mastery_source_intervention_session_id,
        intervention_session_number=mastery_source_intervention_session_number,
        component_source="B",
    )


def _to_pkg_evidence_window_config(config: EvidenceWindowConfig):
    from component_c_generator.pipeline.config import (
        CEvidenceWindowConfig as _PkgCEvidenceWindowConfig,
    )

    return _PkgCEvidenceWindowConfig(
        config_version=config.config_version,
        parameter_source_status=config.parameter_source_status,
        recent_window_task_count=config.recent_window_task_count,
    )


def _to_pkg_template_generation_params(params: TemplateGenerationParams):
    from component_c_generator.generation_config import (
        TemplateGenerationParams as _PkgTemplateGenerationParams,
    )

    return _PkgTemplateGenerationParams(
        magnitude_a_by_level=params.magnitude_a_by_level,
        magnitude_b_by_level=params.magnitude_b_by_level,
        count_a_by_level=params.count_a_by_level,
        count_b_by_level=params.count_b_by_level,
        choice_set=params.choice_set,
        max_generation_attempts=params.max_generation_attempts,
    )


def _to_pkg_generation_config(config: GenerationConfig):
    from component_c_generator.generation_config import CGenerationConfig as _PkgCGenerationConfig

    return _PkgCGenerationConfig(
        config_version=config.config_version,
        parameter_source_status=config.parameter_source_status,
        per_template={
            template_id: _to_pkg_template_generation_params(params)
            for template_id, params in config.per_template.items()
        },
    )


def _to_pkg_selection_config(config: SelectionConfig):
    from component_c_generator.selection.config import CSelectionConfig as _PkgCSelectionConfig

    return _PkgCSelectionConfig(
        config_version=config.config_version,
        parameter_source_status=config.parameter_source_status,
        familiarization_window_by_grade=dict(config.familiarization_window_by_grade),
        familiarization_difficulty_level=config.familiarization_difficulty_level,
        fallback_difficulty_level=config.fallback_difficulty_level,
        familiarization_session_difficulty_cap=config.familiarization_session_difficulty_cap,
        fallback_difficulty_cap=config.fallback_difficulty_cap,
    )


def _to_pkg_policy_config(config: PolicyConfig):
    from component_c_generator.policy.config import CPolicyConfig as _PkgCPolicyConfig

    return _PkgCPolicyConfig(
        config_version=config.config_version,
        parameter_source_status=config.parameter_source_status,
        increase_correctness_threshold=config.increase_correctness_threshold,
        increase_max_avg_attempts=config.increase_max_avg_attempts,
        increase_max_strain=config.increase_max_strain,
        decrease_correctness_threshold=config.decrease_correctness_threshold,
        decrease_error_run_threshold=config.decrease_error_run_threshold,
        decrease_min_strain=config.decrease_min_strain,
    )


def _to_pkg_safety_config(config: SafetyConfig):
    from component_c_generator.safety.config import CSafetyConfig as _PkgCSafetyConfig

    return _PkgCSafetyConfig(
        config_version=config.config_version,
        parameter_source_status=config.parameter_source_status,
        consecutive_error_trigger=config.consecutive_error_trigger,
        strain_trigger=config.strain_trigger,
        increase_block_window=config.increase_block_window,
        prior_overloaded_disengaged_cap=config.prior_overloaded_disengaged_cap,
        safe_termination_error_threshold=config.safe_termination_error_threshold,
        strain_bucket_low_max=config.strain_bucket_low_max,
        strain_bucket_moderate_max=config.strain_bucket_moderate_max,
        strain_bucket_high_max=config.strain_bucket_high_max,
    )


def _to_pkg_aggregation_config(config: AggregationConfig):
    from component_c_generator.aggregation.config import (
        CAggregationConfig as _PkgCAggregationConfig,
    )

    return _PkgCAggregationConfig(
        config_version=config.config_version,
        parameter_source_status=config.parameter_source_status,
        min_completed_tasks_for_difficulty_trend=config.min_completed_tasks_for_difficulty_trend,
    )


def _to_pkg_scaffold_config(config: ScaffoldConfig):
    from component_c_generator.scaffolds.config import CScaffoldConfig as _PkgCScaffoldConfig

    return _PkgCScaffoldConfig(
        config_version=config.config_version,
        parameter_source_status=config.parameter_source_status,
        level_c1_min_consecutive_incorrect=config.level_c1_min_consecutive_incorrect,
        level_c2_min_consecutive_incorrect=config.level_c2_min_consecutive_incorrect,
        level_c3_min_consecutive_incorrect=config.level_c3_min_consecutive_incorrect,
        level_c4_min_consecutive_incorrect=config.level_c4_min_consecutive_incorrect,
    )


def _to_pkg_recovery_config(config: RecoveryConfig):
    from component_c_generator.scaffolds.recovery import CRecoveryConfig as _PkgCRecoveryConfig

    return _PkgCRecoveryConfig(
        config_version=config.config_version,
        parameter_source_status=config.parameter_source_status,
    )


def _to_pkg_prerequisite_redirect_context(context: PrerequisiteRedirectContext):
    return _PkgPrerequisiteRedirectContext(
        prerequisite_curriculum_node_id=context.prerequisite_curriculum_node_id,
        prerequisite_mastery_bucket=context.prerequisite_mastery_bucket,
    )


class LiveEngineCAdapter:
    """Concrete adapter implementing every ``app.domain.live_engine_c`` port.

    Stateless: every method is a pure function of its arguments (plus, for catalogue-dependent
    calls, a re-read of the governed catalogue file at ``Catalogue.source_path``). No mutable
    instance state is held between calls.
    """

    # ---- CataloguePort ---------------------------------------------------------------

    def load(self, catalogue_path: str) -> Catalogue:
        return _map_catalogue(_load_package_catalogue(catalogue_path))

    def checksum(self, catalogue_path: str) -> str:
        try:
            return _pkg_catalogue_file_checksum(catalogue_path)
        except _PkgCatalogueValidationError as exc:
            raise CatalogueUnavailableError(str(exc)) from exc

    def supported_template_ids(self) -> tuple[str, ...]:
        """The 21st adapter method (Phase 2). Argument-free pass-through to
        ``component_c_generator.tasks.registry.supported_template_ids`` -- code-sourced, not
        catalogue-file-sourced; already a plain ``tuple[str, ...]``, so no type mapping is
        needed."""
        return _pkg_supported_template_ids()

    # ---- ActivationPort ---------------------------------------------------------------

    def decide_activation(
        self,
        catalogue: Catalogue,
        game_task_template_id: str,
        supported_template_ids: tuple[str, ...],
        grade: Grade,
    ) -> ActivationDecision:
        pkg_catalogue = _load_package_catalogue(catalogue.source_path)
        template = _template_by_id(pkg_catalogue, game_task_template_id)
        decision = _pkg_decide_activation(
            template, supported_template_ids, grade, pkg_catalogue.catalogue_status
        )
        return _map_activation_decision(decision)

    def eligible_templates(
        self, catalogue: Catalogue, grade: Grade, supported_template_ids: tuple[str, ...]
    ) -> tuple[GameTaskTemplate, ...]:
        pkg_catalogue = _load_package_catalogue(catalogue.source_path)
        templates = _pkg_eligible_templates(pkg_catalogue, grade, supported_template_ids)
        return tuple(_map_game_task_template(t) for t in templates)

    # ---- SessionPhasePort ---------------------------------------------------------------

    def decide_session_phase(self, eligible_combined_handoffs_completed: int, window_w: int) -> str:
        return _pkg_decide_session_phase(eligible_combined_handoffs_completed, window_w)

    # ---- SelectionPort ---------------------------------------------------------------

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
    ) -> SelectionResult:
        pkg_catalogue = _load_package_catalogue(catalogue.source_path)
        if mastery_payload is not None:
            assert mastery_source_student_id is not None
            assert mastery_source_intervention_session_id is not None
            assert mastery_source_intervention_session_number is not None
            pkg_mastery_payload = _to_pkg_mastery_payload(
                mastery_payload,
                mastery_source_student_id=mastery_source_student_id,
                mastery_source_intervention_session_id=mastery_source_intervention_session_id,
                mastery_source_intervention_session_number=mastery_source_intervention_session_number,
            )
        else:
            pkg_mastery_payload = None
        try:
            result = _pkg_select_task(
                session_mode=session_mode,
                session_phase=session_phase,
                grade=grade,
                catalogue=pkg_catalogue,
                supported_template_ids=supported_template_ids,
                student_id=student_id,
                c_session_id=c_session_id,
                task_index=task_index,
                mastery_payload=pkg_mastery_payload,
                sessions_since_last_practice=dict(sessions_since_last_practice),
                component_c_session_lineage=_to_pkg_seed_lineage(component_c_session_lineage),
                task_opportunity_lineage=_to_pkg_seed_lineage(task_opportunity_lineage),
                generation_config=_to_pkg_generation_config(generation_config),
                selection_config=_to_pkg_selection_config(selection_config),
            )
        except _PkgSelectionInputError as exc:
            raise SelectionInputError(str(exc)) from exc
        return _map_selection_result(result)

    # ---- TaskConstructionPort ---------------------------------------------------------------

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
    ) -> TaskInstance:
        pkg_catalogue = _load_package_catalogue(catalogue.source_path)
        template = _template_by_id(pkg_catalogue, game_task_template_id)
        try:
            instance = _pkg_build_task_instance(
                template,
                _to_pkg_seed_lineage(seed_lineage),
                grade,
                difficulty_level,
                student_id,
                c_session_id,
                task_index,
                pkg_catalogue.catalogue_version,
                _to_pkg_generation_config(config),
            )
        except _PkgUnsupportedTemplateError as exc:
            raise UnsupportedTemplateError(str(exc)) from exc
        except _PkgTaskGenerationTechnicalError as exc:
            raise TaskGenerationTechnicalError(str(exc)) from exc
        return _map_task_instance(instance)

    # ---- EvaluationPort ---------------------------------------------------------------

    def evaluate(
        self, task_instance: TaskInstance, learner_action: Mapping[str, object]
    ) -> EvaluationResult:
        try:
            result = _pkg_evaluate(_to_pkg_task_instance(task_instance), dict(learner_action))
        except _PkgEvalUnknownTemplateError as exc:
            raise UnknownTemplateError(str(exc)) from exc
        return _map_evaluation_result(result)

    # ---- SummaryPort ---------------------------------------------------------------

    def derive_task_opportunity_summary(self, events) -> TaskOpportunitySummary:
        pkg_events = [_to_pkg_gameplay_event(e) for e in events]
        summary = _pkg_derive_task_opportunity_summary(pkg_events)
        return _map_task_opportunity_summary(summary)

    # ---- PolicyEvidencePort ---------------------------------------------------------------

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
    ) -> PolicyObservableEvidence:
        evidence = _pkg_build_policy_evidence(
            session_mode=session_mode,
            session_phase=session_phase,
            current_difficulty_level=current_difficulty_level,
            history=[_to_pkg_task_opportunity_summary(s) for s in history],
            is_recovery_context=is_recovery_context,
            prior_session_end_state=prior_session_end_state,
            safety_increase_block_remaining=safety_increase_block_remaining,
            config=_to_pkg_evidence_window_config(config),
        )
        return _map_policy_observable_evidence(evidence)

    def compute_rolling_strain(self, recent_summaries: Sequence[TaskOpportunitySummary]) -> float:
        return _pkg_compute_rolling_strain(
            [_to_pkg_task_opportunity_summary(s) for s in recent_summaries]
        )

    # ---- AdaptationPort ---------------------------------------------------------------

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
    ) -> AdaptationDecision:
        try:
            decision = _pkg_decide_adaptation(
                policy_mode=policy_mode,
                evidence=_to_pkg_policy_observable_evidence(evidence),
                current_difficulty_level=current_difficulty_level,
                seed_lineage=_to_pkg_seed_lineage(seed_lineage),
                policy_config=_to_pkg_policy_config(policy_config),
                safety_config=_to_pkg_safety_config(safety_config),
                selection_config=_to_pkg_selection_config(selection_config),
            )
        except _PkgQLearningDisabledError as exc:
            raise QLearningDisabledError(str(exc)) from exc
        except _PkgUnknownPolicyModeError as exc:
            raise UnknownPolicyModeError(str(exc)) from exc
        return _map_adaptation_decision(decision)

    # ---- ScaffoldPort ---------------------------------------------------------------

    def decide_scaffold_level(
        self, context: ScaffoldDecisionContext, config: ScaffoldConfig
    ) -> ScaffoldLevel:
        return _pkg_decide_scaffold_level(
            _to_pkg_scaffold_decision_context(context), _to_pkg_scaffold_config(config)
        )

    # ---- RecoveryPort ---------------------------------------------------------------

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
    ) -> TaskInstance:
        pkg_catalogue = _load_package_catalogue(catalogue.source_path)
        try:
            instance = _pkg_build_recovery_task(
                _to_pkg_task_instance(parent_instance),
                skill_id,
                task_index,
                pkg_catalogue,
                supported_template_ids,
                _to_pkg_generation_config(generation_config),
                _to_pkg_seed_lineage(seed_lineage),
                _to_pkg_recovery_config(recovery_config),
                safety_required=safety_required,
                prerequisite_context=(
                    _to_pkg_prerequisite_redirect_context(prerequisite_context)
                    if prerequisite_context is not None
                    else None
                ),
            )
        except _PkgNoEligibleRecoveryTemplateError as exc:
            raise NoEligibleRecoveryTemplateError(str(exc)) from exc
        except _PkgRecoveryPreconditionError as exc:
            raise RecoveryPreconditionError(str(exc)) from exc
        return _map_task_instance(instance)

    # ---- RewardPort ---------------------------------------------------------------

    def decide_child_facing_reward(
        self, context: RewardOutcomeContext
    ) -> Optional[ChildFacingReward]:
        reward = _pkg_decide_child_facing_reward(_to_pkg_reward_outcome_context(context))
        return _map_child_facing_reward(reward)

    # ---- AggregationPort ---------------------------------------------------------------

    def derive_session_aggregate(
        self,
        events,
        summaries: Sequence[TaskOpportunitySummary],
        adaptation_decisions: Sequence[AdaptationDecision],
        *,
        time_in_target_band_sec: float,
        safety_override_count: int,
        inactive_time_available: bool,
        config: AggregationConfig,
    ) -> SessionAggregate:
        aggregate = _pkg_derive_session_aggregate(
            [_to_pkg_gameplay_event(e) for e in events],
            [_to_pkg_task_opportunity_summary(s) for s in summaries],
            [_to_pkg_adaptation_decision(d) for d in adaptation_decisions],
            time_in_target_band_sec=time_in_target_band_sec,
            safety_override_count=safety_override_count,
            inactive_time_available=inactive_time_available,
            config=_to_pkg_aggregation_config(config),
        )
        return _map_session_aggregate(aggregate)

    # ---- CompositePort ---------------------------------------------------------------

    def compute_engagement(
        self, aggregate: SessionAggregate, formula_version: CompositeFormulaVersion
    ) -> tuple[EngagementComponents, float]:
        components, score = _pkg_compute_engagement(
            _to_pkg_session_aggregate(aggregate), formula_version
        )
        return _map_engagement_components(components), score

    def compute_frustration(
        self, aggregate: SessionAggregate, formula_version: CompositeFormulaVersion
    ) -> tuple[FrustrationComponents, float]:
        components, score = _pkg_compute_frustration(
            _to_pkg_session_aggregate(aggregate), formula_version
        )
        return _map_frustration_components(components), score

    def decide_telemetry_quality_status(
        self,
        session_technical_issue_flag: bool,
        task_opportunity_count: int,
        completed_task_count: int,
        session_duration_sec: float,
        accuracy_rate: Optional[float],
        task_completion_rate: Optional[float],
    ) -> TelemetryQualityStatus:
        return _pkg_decide_telemetry_quality_status(
            session_technical_issue_flag,
            task_opportunity_count,
            completed_task_count,
            session_duration_sec,
            accuracy_rate,
            task_completion_rate,
        )

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
    ) -> tuple[Optional[LearnerState], StateReason]:
        return _pkg_decide_learner_state(
            telemetry_quality_status,
            safety_override_count,
            consecutive_error_max,
            quit_after_error,
            difficulty_floor_hits,
            task_completion_rate,
            inactivity_periods,
            engagement_score,
            frustration_index,
        )
