"""Component C Phase 5: the application-service layer behind the two task-serving HTTP endpoints
(``POST .../tasks/next``, ``POST .../tasks/{tid}/actions``).

HEADLINE CONSEQUENCE — STATE PLAINLY (Phase 5 work order, verbatim instruction): PHASE 5 DELIVERS
A COMPLETE, TESTED SERVING PATH THAT IS DELIBERATELY NOT LIVE. Every real (non-smoke) call to
``next_task`` refuses before any task is generated, because GenerationConfig has no governed
values anywhere in this codebase (S1, Phase 5 work order): "The frozen catalogue supplies no
numeric bound and no action-space enumeration for any of the 30 templates and the Parameters do
not fix them either; every value is an ENGINEERING_ASSUMPTION tagged TEST_FIXTURE_ONLY.
Governance assigned no values here." ``app.domain.live_engine_c.generation_mode_guard.
assert_generation_config_permitted`` is the guard that enforces this; it is wired in below, for
the first time, exactly as S1 instructs ("This is that call"). A green test suite exercising this
module with ``smoke_mode=True`` is evidence the SERVING MECHANISM works — it is explicitly NOT
evidence that Component C can serve a task to a real child. Do not read it that way.

GENERATIONCONFIG STAYS INJECTION-ONLY, NO DEFAULT ANYWHERE (S1, mirrors W1's shape for
SelectionConfig): every function below that needs a ``GenerationConfig`` takes it as a required,
no-default parameter. This module never calls ``default_generation_config()`` and never reads
``generation_config.DEFAULT_TEMPLATE_GENERATION_PARAMS`` directly either — reading the underlying
table would hide the same dependency the named-function ban exists to surface (W2's own
reasoning, extended). Asserted mechanically, not by convention — see
``test_be2_architecture_guards.py::test_no_app_code_defaults_or_calls_default_generation_config``.

PRODUCTION GENERATION-CONFIG PROBE (BUILDER JUDGMENT — UNRATIFIED): the real HTTP route
(``app.api.routes.c_task``) has no legitimate source for a populated ``GenerationConfig`` — no
bundle mechanism exists (S1 explicitly forbids building one) and no default call is permitted
(above). It therefore passes an intentionally EMPTY probe (``per_template={}``,
``parameter_source_status="TEST_FIXTURE_ONLY"``) together with a hardcoded, never-client-
influenced ``smoke_mode=False``. Since every ``GenerationConfig`` value that exists anywhere in
this codebase is tagged ``TEST_FIXTURE_ONLY`` or ``SMOKE_ONLY`` (there is no other kind — S1's own
words), the guard call below refuses this probe UNCONDITIONALLY, regardless of what it contains;
its emptiness is a second, redundant containment (even if the guard were ever bypassed, an empty
``per_template`` cannot generate anything real) — not the only one. This construction is NOT
sanctioned by name in the Phase 5 work order; it is disclosed here for exactly that reason.

SEED LINEAGE — BUILDER JUDGMENT — UNRATIFIED, DISCLOSED PROMINENTLY. ``SeedLineage``'s own
docstring (``app/domain/live_engine_c/types.py``) says: "obtaining a real seed value is left to
whichever future phase's work order explicitly authorizes that call" — this work order does not
mention seed lineage construction anywhere. What follows is the minimum, non-derived plumbing
needed to call ``select_task`` at all: ``component_c_session_lineage`` is the session's own
``global_seed`` at the ROOT (``path=()``, ``seed=global_seed`` — the value BEFORE any derivation,
not a derived one); ``task_opportunity_lineage`` uses ``task_index`` (a real, already-known,
non-invented value) as its sole path-distinguishing element so that different tasks within one
session receive different lineages, matching the name's own singular-per-opportunity shape. NO
hash/mixing function is called here — ``derive_child_lineage``/``SeedManager``/``rng_from``/
``SUBSTREAMS`` are called ONLY inside the package's own ``select_task``, never in this module or
the adapter (unchanged from Phase 1b's boundary). These are plain integers/string-pair tuples,
not a B-shaped identifier of any kind — see R-8 below for the field that IS.

R-8 (SUPERVISOR RULING, Phase 5 continuation): the ORIGINAL version of this module derived its own
``STU-####``/``STU-####-C-###`` values from a UUID hash (a SECOND, independent construction site
minting a B-shaped identifier, alongside the mastery fixture's own ``FIXTURE_MASTERY_SOURCE_
STUDENT_ID = "STU-0001"``). That is exactly the defect R-5 exists to prevent: two places computing
what is nominally "the same real child's platform identity" would almost always DISAGREE (a
UUID-hash derivation here, a fixed fictional constant there), for the SAME learner, inside the
SAME call. Collapsed to the single existing source: ``select_task``/``build_task_instance``'s
``student_id``/``c_session_id`` parameters, and ``evaluate``'s reconstructed ``TaskInstance``, now
read ``FIXTURE_MASTERY_SOURCE_STUDENT_ID`` (``mastery_fixture.py``) directly, for EVERY session
mode -- not only combined. This is deliberate, not an oversight: these two package parameters are
format-validated only (``^STU-[0-9]{4}$`` / ``^STU-[0-9]{4}-C-[0-9]{3}$``), never used for lookup,
RNG, or cross-referencing anywhere the installed wheel or this codebase does (confirmed: seed
derivation is the separate ``SeedLineage`` parameter above; nothing stores ``game_task_instance_id``
as its own column). For a ``c_only`` session there is no B mastery involved at all and no
real-B-session claim is being made by reusing this constant -- it is functioning here purely as
the ONE already-reviewed, already-fictional placeholder this codebase uses to satisfy the
package's format requirement, never as an assertion that B is involved. ``_stu_session_id_suffix``
below supplies a fixed session-distinguishing suffix for the same reason -- one constant, one
source, never a second minting site.

SESSIONS_SINCE_LAST_PRACTICE (P4): sourced EXCLUSIVELY through ``session_lifecycle.
_learner_session_state``, the SAME function Phase 4's session-phase decision already uses — never
re-derived here, never touching any B table or B-derived value.

MASTERY SOURCE + IDENTITY: reuses the exact same fixture producer as ``c_session_service.py``
(``fixture_b_mastery_payload_for_phase_4`` / ``fixture_b_provenance_for_phase_4``) for combined-
mode sessions — never from the client, same R-5 reasoning.

RAW EVENTS ONLY (S6): this module writes ``CGameplayEventRecord`` rows directly
(``game_task_offered`` on ``next_task``, ``answer_evaluated`` on ``submit_action``) and nothing
else — no ``CTaskOpportunitySummaryRecord`` derivation. v3.0's own Phase 5 scope text names no
summary derivation and ``SummaryPort.derive_task_opportunity_summary``'s own docstring names
Phase 8 explicitly.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any, Mapping, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.live_engine_c.bundle_resolution import resolve_c_bundle_and_catalogue, resolve_selection_config
from app.application.live_engine_c.c_session_service import _require_learner_id
from app.application.live_engine_c.mastery_fixture import (
    FIXTURE_MASTERY_SOURCE_STUDENT_ID,
    fixture_b_mastery_payload_for_phase_4,
    fixture_b_provenance_for_phase_4,
)
from app.application.live_engine_c.session_lifecycle import _learner_session_state, _provenance
from app.core.errors import ActionPayloadRejectedError, ConflictError, ResourceNotFoundError
from app.domain.c_task import CNextTaskResponse, CSubmitActionResult, CTaskFields
from app.domain.live_engine_c.action_payload_validation import (
    ActionPayloadValidationError,
    validate_action_payload,
)
from app.domain.live_engine_c.errors import LiveEngineCError, UnknownTemplateError
from app.domain.live_engine_c.generation_mode_guard import (
    GenerationConfigNotPermittedError,
    assert_generation_config_permitted,
)
from app.domain.live_engine_c.types import GenerationConfig, SeedLineage, TaskInstance
from app.infrastructure.live_engine_c.adapter import LiveEngineCAdapter
from app.infrastructure.persistence_models import CGameplayEventRecord, CTaskInstanceRecord, CTaskOpportunityRecord
from app.infrastructure.repositories import (
    CGameplayEventRecordRepository,
    CSessionRecordRepository,
    CTaskInstanceRecordRepository,
    CTaskOpportunityRecordRepository,
)

# Same ENGINEERING-ONLY TEST-provenance bridge as c_session_service.py, same disclosure.
_BUNDLE_PATH = "tests/fixtures/runtime_bundle_c/valid_unapproved_bundle_c.json"
_SCHEMA_PATH = "provenance/c-runtime-bundle.schema.json"
_CATALOGUE_PATH = "tests/fixtures/runtime_bundle_c/test_catalogue_c.md"

# The production probe described in the module docstring -- deliberately empty, deliberately
# always-refused. NOT a real generation config; never used to generate anything (the guard call
# raises before any per-template lookup could occur).
PRODUCTION_GENERATION_CONFIG_PROBE = GenerationConfig(
    config_version="phase5-not-live-probe",
    parameter_source_status="TEST_FIXTURE_ONLY",
    per_template={},
)


# R-8: the ONE fixed session-distinguishing suffix used with FIXTURE_MASTERY_SOURCE_STUDENT_ID
# to satisfy build_task_instance's ^STU-[0-9]{4}-C-[0-9]{3}$ requirement -- never a second
# per-session derivation, since the underlying student id is already a single fixed constant.
_STU_SESSION_SUFFIX = "001"


def _stu_session_id() -> str:
    return f"{FIXTURE_MASTERY_SOURCE_STUDENT_ID}-C-{_STU_SESSION_SUFFIX}"


def _generation_config_checksum(config: GenerationConfig) -> str:
    """No existing column precedent pins down what ``c_gameplay_events.config_checksum`` should
    cover (undocumented since Phase 3a) -- BUILDER JUDGMENT — UNRATIFIED: a deterministic digest
    of the generation config's own identity strings, mirroring ``catalogue_checksum``'s role for
    the catalogue."""
    return hashlib.sha256(f"{config.config_version}:{config.parameter_source_status}".encode()).hexdigest()


def _task_fields(record: CTaskInstanceRecord) -> CTaskFields:
    """Allow-list construction (X-4) -- see app/domain/c_task.py's own docstring for the full
    private/public rationale, column by column."""
    return CTaskFields(
        c_task_instance_id=record.c_task_instance_id,
        game_family_id=record.game_family_id,
        game_task_template_id=record.game_task_template_id,
        task_index=record.task_index,
        skill_id=record.skill_id,
        difficulty_level=record.difficulty_level,
        representation_mode=record.representation_mode,
        prompt_payload=record.prompt_payload,
        interactive_assets=record.interactive_assets,
        valid_action_space=record.valid_action_space,
        scaffold_state=record.scaffold_state,
        technical_status=record.technical_status,
    )


def _to_domain_task_instance(
    record: CTaskInstanceRecord, *, student_id: str, c_session_id: str
) -> TaskInstance:
    """Reconstructs the domain ``TaskInstance`` the adapter's ``evaluate`` port expects, from the
    persisted PRIVATE row. ``student_id``/``c_session_id`` are not stored on this table (Phase
    3a's minimal-FK style) and are supplied by the caller, who already has them from the
    authenticated request -- never invented, never re-derived."""
    # The package's own GameTaskInstance model requires game_task_instance_id to match
    # ^STU-####-C-###-T###-X###$ -- built from the already-STU-formatted c_session_id and this
    # record's own task_index, mirroring build_task_instance's own construction
    # (f"{c_session_id}-T{task_index:03d}-X001") rather than the raw private UUID.
    game_task_instance_id = f"{c_session_id}-T{record.task_index:03d}-X001"
    return TaskInstance(
        game_family_id=record.game_family_id,
        game_task_template_id=record.game_task_template_id,
        game_task_instance_id=game_task_instance_id,
        template_version=record.template_version,
        catalogue_version=record.catalogue_version,
        generator_version=record.generator_version,
        seed_lineage=SeedLineage(
            global_seed=record.seed_lineage_global_seed,
            path=tuple(tuple(pair) for pair in record.seed_lineage_path),
            seed=record.seed_lineage_seed,
        ),
        student_id=student_id,
        c_session_id=c_session_id,
        task_index=record.task_index,
        skill_id=record.skill_id,
        curriculum_node_id=record.curriculum_node_id,
        grade_scope=record.grade_scope,
        difficulty_level=record.difficulty_level,
        difficulty_vector=dict(record.difficulty_vector),
        functional_role=record.functional_role,
        representation_mode=record.representation_mode,
        prompt_payload=dict(record.prompt_payload),
        interactive_assets=dict(record.interactive_assets),
        correct_answer_payload=dict(record.correct_answer_payload),
        correctness_function_id=record.correctness_function_id,
        valid_action_space=dict(record.valid_action_space),
        completion_condition=record.completion_condition,
        failure_condition=record.failure_condition,
        scaffold_state=record.scaffold_state,  # type: ignore[arg-type]
        recovery_parent_instance_id=record.recovery_parent_instance_id,
        technical_status=record.technical_status,
    )


class TaskService:
    async def next_task(
        self,
        session: AsyncSession,
        *,
        principal_user_id: str,
        request_id: str,
        c_session_id: UUID,
        generation_config: GenerationConfig,
        smoke_mode: bool,
    ) -> CNextTaskResponse:
        student_id = await _require_learner_id(session, principal_user_id)
        session_record = await CSessionRecordRepository(session).get_owned(c_session_id, student_id)
        if session_record is None:
            raise ResourceNotFoundError()
        if session_record.state != "active":
            raise ConflictError()

        try:
            assert_generation_config_permitted(generation_config, smoke_mode=smoke_mode)
        except GenerationConfigNotPermittedError as exc:
            raise ConflictError() from exc

        adapter = LiveEngineCAdapter()
        try:
            bundle, _catalogue_manifest, catalogue_checksum = resolve_c_bundle_and_catalogue(
                bundle_path=_BUNDLE_PATH,
                schema_path=_SCHEMA_PATH,
                catalogue_path=_CATALOGUE_PATH,
                require_approved=False,
            )
            selection_config = resolve_selection_config(bundle)
            catalogue = adapter.load(_CATALOGUE_PATH)
        except LiveEngineCError as exc:
            raise ConflictError() from exc

        learner_state, _local_state_record = await _learner_session_state(session, student_id)
        # task_index is 1-based: the package's own GameTaskInstance model requires >= 1.
        task_index = await CTaskOpportunityRecordRepository(session).count_for_session(c_session_id) + 1

        mastery_by_skill: Optional[Mapping[str, float]] = None
        mastery_source_student_id: Optional[str] = None
        mastery_source_intervention_session_id: Optional[str] = None
        mastery_source_intervention_session_number: Optional[int] = None
        if session_record.session_mode == "combined":
            mastery_by_skill = fixture_b_mastery_payload_for_phase_4()
            (
                mastery_source_student_id,
                mastery_source_intervention_session_id,
                mastery_source_intervention_session_number,
            ) = fixture_b_provenance_for_phase_4()

        # See module docstring, "SEED LINEAGE" -- root construction only, no derivation.
        session_lineage = SeedLineage(
            global_seed=session_record.global_seed, path=(), seed=session_record.global_seed
        )
        task_opportunity_lineage = SeedLineage(
            global_seed=session_record.global_seed,
            path=(("task_index", str(task_index)),),
            seed=session_record.global_seed,
        )

        try:
            result = adapter.select_task(
                session_mode=session_record.session_mode,
                session_phase=session_record.session_phase,
                grade=session_record.grade,
                catalogue=catalogue,
                supported_template_ids=adapter.supported_template_ids(),
                student_id=FIXTURE_MASTERY_SOURCE_STUDENT_ID,
                c_session_id=_stu_session_id(),
                task_index=task_index,
                mastery_payload=mastery_by_skill,
                mastery_source_student_id=mastery_source_student_id,
                mastery_source_intervention_session_id=mastery_source_intervention_session_id,
                mastery_source_intervention_session_number=mastery_source_intervention_session_number,
                sessions_since_last_practice=learner_state.sessions_since_last_practice,
                component_c_session_lineage=session_lineage,
                task_opportunity_lineage=task_opportunity_lineage,
                generation_config=generation_config,
                selection_config=selection_config,
            )
        except LiveEngineCError as exc:
            raise ConflictError() from exc

        opportunity_id = uuid4()
        opportunity = CTaskOpportunityRecord(
            c_task_opportunity_id=opportunity_id,
            c_session_id=c_session_id,
            task_index=task_index,
            selected_skill_id=result.selected_skill_id,
            selected_template_id=result.selected_template_id,
            initial_difficulty_level=result.initial_difficulty_level,
            mastery_context_mode=result.mastery_context_mode,
            mastery_selected_skill=result.mastery_selected_skill,
            session_phase=result.session_phase,
            terminal_reason=None,
            task_offered_at_utc=datetime.now(UTC),
            **_provenance("c_task_opportunity", opportunity_id, request_id, "c_task.offered"),
        )
        await CTaskOpportunityRecordRepository(session).add(opportunity)

        instance = result.task_instance
        instance_id = uuid4()
        instance_record = CTaskInstanceRecord(
            c_task_instance_id=instance_id,
            c_task_opportunity_id=opportunity_id,
            game_family_id=instance.game_family_id,
            game_task_template_id=instance.game_task_template_id,
            template_version=instance.template_version,
            catalogue_version=instance.catalogue_version,
            generator_version=instance.generator_version,
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
            recovery_parent_instance_id=None,
            technical_status=instance.technical_status,
            seed_lineage_global_seed=instance.seed_lineage.global_seed,
            seed_lineage_path=[list(pair) for pair in instance.seed_lineage.path],
            seed_lineage_seed=instance.seed_lineage.seed,
            **_provenance("c_task_instance", instance_id, request_id, "c_task.instance_generated"),
        )
        await CTaskInstanceRecordRepository(session).add(instance_record)

        event_id = uuid4()
        offered_event = CGameplayEventRecord(
            c_gameplay_event_id=event_id,
            c_session_id=c_session_id,
            game_task_instance_id=instance_id,
            task_index=task_index,
            event_type="game_task_offered",
            event_index=1,
            attempt_number=None,
            event_timestamp_relative_ms=0,
            action_payload=None,
            evaluation_payload=None,
            scaffold_code=None,
            technical_flag=False,
            terminal_reason=None,
            seed_lineage_global_seed=instance.seed_lineage.global_seed,
            seed_lineage_path=[list(pair) for pair in instance.seed_lineage.path],
            seed_lineage_seed=instance.seed_lineage.seed,
            generator_version=instance.generator_version,
            config_checksum=_generation_config_checksum(generation_config),
            **_provenance("c_gameplay_event", event_id, request_id, "c_task.offered"),
        )
        await CGameplayEventRecordRepository(session).add(offered_event)

        return CNextTaskResponse(**_task_fields(instance_record).model_dump(), request_id=request_id)

    async def submit_action(
        self,
        session: AsyncSession,
        *,
        principal_user_id: str,
        request_id: str,
        c_session_id: UUID,
        c_task_instance_id: UUID,
        action_payload: Mapping[str, Any],
        generation_config: GenerationConfig,
        submission_spy: Optional[list] = None,
    ) -> CSubmitActionResult:
        student_id = await _require_learner_id(session, principal_user_id)
        session_record = await CSessionRecordRepository(session).get_owned(c_session_id, student_id)
        if session_record is None:
            raise ResourceNotFoundError()

        instance_repo = CTaskInstanceRecordRepository(session)
        instance_record = await instance_repo.get_owned(c_task_instance_id, c_session_id)
        if instance_record is None:
            raise ResourceNotFoundError()

        try:
            validate_action_payload(instance_record.valid_action_space, action_payload)
        except ActionPayloadValidationError as exc:
            details = [{"location": list(loc), "type": code} for loc, code in exc.field_errors] or None
            raise ActionPayloadRejectedError(details=details) from exc

        adapter = LiveEngineCAdapter()
        domain_instance = _to_domain_task_instance(
            instance_record,
            student_id=FIXTURE_MASTERY_SOURCE_STUDENT_ID,
            c_session_id=_stu_session_id(),
        )
        try:
            evaluation = adapter.evaluate(domain_instance, action_payload)
        except UnknownTemplateError as exc:
            raise ConflictError() from exc

        if submission_spy is not None:
            submission_spy.append(c_task_instance_id)

        event_repo = CGameplayEventRecordRepository(session)
        max_index, max_timestamp = await event_repo.max_index_and_timestamp_for_instance(c_task_instance_id)
        event_id = uuid4()
        evaluated_event = CGameplayEventRecord(
            c_gameplay_event_id=event_id,
            c_session_id=c_session_id,
            game_task_instance_id=c_task_instance_id,
            task_index=instance_record.task_index,
            event_type="answer_evaluated",
            event_index=max_index + 1,
            attempt_number=1,
            event_timestamp_relative_ms=max_timestamp + 1,
            action_payload=dict(action_payload),
            # NEVER correctness_function_id, NEVER the correct_answer_payload -- only the
            # boolean verdict (P1-d: evaluator internals must never leak).
            evaluation_payload={"is_correct": evaluation.is_correct},
            scaffold_code=None,
            technical_flag=False,
            terminal_reason=None,
            seed_lineage_global_seed=instance_record.seed_lineage_global_seed,
            seed_lineage_path=instance_record.seed_lineage_path,
            seed_lineage_seed=instance_record.seed_lineage_seed,
            generator_version=instance_record.generator_version,
            config_checksum=_generation_config_checksum(generation_config),
            **_provenance("c_gameplay_event", event_id, request_id, "c_task.action_evaluated"),
        )
        await event_repo.add(evaluated_event)

        return CSubmitActionResult(
            c_task_instance_id=c_task_instance_id,
            response_matched=evaluation.is_correct,
            request_id=request_id,
        )
