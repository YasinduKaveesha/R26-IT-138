"""Component C Phase 4: session creation/start, resume, abandon; the two session modes;
mastery_context_mode determination; the cold-start gate (SF-043); C-16's closure.

W — OWNER-RULED, INJECTION, NO DEFAULT ANYWHERE (Phase 4 work order): every function below that
needs a ``SelectionConfig`` takes it as a REQUIRED, no-default parameter. This module never
calls ``default_selection_config()`` and never hardcodes ``familiarization_window_by_grade``
anywhere. That is asserted mechanically, not by convention -- see
``backend/tests/test_be2_architecture_guards.py::test_no_app_code_defaults_or_calls_default_selection_config``.

R3 — NO CACHING AT THIS LAYER. This module holds no module-level or instance-level mastery
state. Every mastery payload is validated fresh, used once (to satisfy the SF-043 gate and
determine ``mastery_context_mode``), and is never persisted to ``c_sessions`` or any other table
-- ``c_sessions`` has no ``mastery_*`` column (Phase 3a schema, unchanged this batch).

Q1 — the chokepoint this phase owns: session CREATION itself. A ``combined`` session's mastery
payload is validated BEFORE the ``CSessionRecord`` is ever added to the database session; if
validation fails, no row is created. Tests spy on ``CSessionRecordRepository.add`` to prove this
mechanically, not by inference from "an error was raised somewhere."
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Mapping, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.live_engine_c.errors import SF043OrderingError
from app.domain.live_engine_c.types import Grade, LearnerSessionState, SelectionConfig, SessionMode
from app.infrastructure.live_engine_c.adapter import LiveEngineCAdapter
from app.infrastructure.persistence_models import CLearnerLocalStateRecord, CSessionRecord
from app.infrastructure.repositories import CLearnerLocalStateRepository, CSessionRecordRepository

SCHEMA_REVISION = "20260816_0004"


def mastery_context_mode_for(session_mode: SessionMode) -> str:
    """v3.0 §11 Phase 4 hard constraint: fixed by mode, never inferred from anything else."""
    if session_mode == "combined":
        return "same_session_fresh"
    return "unavailable_fallback"


def _provenance(resource_type: str, resource_id: UUID, request_id: str, operation: str) -> dict[str, object]:
    return {
        "system_actor": "c-session-lifecycle",
        "request_id": request_id,
        "operation_or_event_type": operation,
        "reason_code": "AUTHORIZED_C_SESSION_LIFECYCLE_COMMAND",
        "resource_type": resource_type,
        "resource_id": resource_id,
        "source_class": "REAL",
        "source_system": "upadya-api",
        "environment": "live-endpoint",
        "schema_revision": SCHEMA_REVISION,
    }


async def _learner_session_state(
    session: AsyncSession, student_id: UUID
) -> tuple[LearnerSessionState, Optional[CLearnerLocalStateRecord]]:
    record = await CLearnerLocalStateRepository(session).find_by_student(student_id)
    if record is None:
        return LearnerSessionState(
            eligible_combined_handoffs_completed=0,
            sessions_since_last_practice={},
            prior_session_end_state=None,
        ), None
    return LearnerSessionState(
        eligible_combined_handoffs_completed=record.eligible_combined_handoffs_completed,
        sessions_since_last_practice=dict(record.sessions_since_last_practice),
        prior_session_end_state=record.prior_session_end_state,
    ), record


async def create_session(
    session: AsyncSession,
    adapter: LiveEngineCAdapter,
    *,
    student_id: UUID,
    grade: Grade,
    session_mode: SessionMode,
    catalogue_version: str,
    catalogue_checksum: str,
    c_runtime_bundle_record_id: UUID,
    global_seed: int,
    selection_config: SelectionConfig,
    request_id: str,
    mastery_by_skill: Optional[Mapping[str, float]] = None,
    mastery_source_student_id: Optional[str] = None,
    mastery_source_intervention_session_id: Optional[str] = None,
    mastery_source_intervention_session_number: Optional[int] = None,
    session_creation_spy: Optional[list] = None,
) -> CSessionRecord:
    """v3.0 §11 Phase 4: ``POST /api/v1/c/sessions`` (idempotent by learner state -- an existing
    starting/active session for this student is returned unchanged rather than creating a
    second). ``session_creation_spy``, when supplied, has one item appended to it each time (and
    only when) a ``CSessionRecord`` is actually added -- Q1's non-arrival proof."""
    repository = CSessionRecordRepository(session)
    existing = await repository.find_starting_or_active_for_learner(student_id)
    if existing is not None:
        return existing

    if session_mode == "c_only":
        if mastery_by_skill is not None:
            raise SF043OrderingError(
                "c_only session must not receive a B mastery payload (SF-043)"
            )
    else:
        if mastery_by_skill is None:
            raise SF043OrderingError(
                "combined session requires a same-session B mastery payload (SF-043)"
            )
        assert mastery_source_student_id is not None
        assert mastery_source_intervention_session_id is not None
        assert mastery_source_intervention_session_number is not None
        # Validated here, BEFORE any session row exists -- Q1's chokepoint. A
        # MasteryPayloadContractValidationError propagates straight out; nothing below this
        # point executes, and nothing is added to `session`.
        adapter.validate_mastery_payload(
            mastery_by_skill,
            mastery_source_student_id=mastery_source_student_id,
            mastery_source_intervention_session_id=mastery_source_intervention_session_id,
            mastery_source_intervention_session_number=mastery_source_intervention_session_number,
        )

    learner_state, _ = await _learner_session_state(session, student_id)
    session_phase = adapter.decide_next_session_phase(
        session_mode=session_mode, grade=grade, state=learner_state, selection_config=selection_config,
    )

    c_session_id = uuid4()
    record = CSessionRecord(
        c_session_id=c_session_id,
        student_id=student_id,
        intervention_session_id=mastery_source_intervention_session_id,
        session_mode=session_mode,
        session_phase=session_phase,
        mastery_context_mode=mastery_context_mode_for(session_mode),
        catalogue_version=catalogue_version,
        catalogue_checksum=catalogue_checksum,
        c_runtime_bundle_record_id=c_runtime_bundle_record_id,
        grade=grade,
        state="active",
        global_seed=global_seed,
        started_at_utc=datetime.now(UTC),
        completed_at_utc=None,
        row_version=0,
        **_provenance("c_session", c_session_id, request_id, "c_session.started"),
    )
    await repository.add(record)
    if session_creation_spy is not None:
        session_creation_spy.append(c_session_id)
    return record


async def get_active_session(session: AsyncSession, student_id: UUID) -> Optional[CSessionRecord]:
    """v3.0 §11 Phase 4: ``GET /api/v1/c/sessions/active`` -- resume after a crash."""
    return await CSessionRecordRepository(session).find_active_for_learner(student_id)


async def abandon_session(session: AsyncSession, c_session_id: UUID, student_id: UUID) -> CSessionRecord:
    """v3.0 §11 Phase 4: ``POST /api/v1/c/sessions/{id}/abandon`` -- safe termination. Reachable
    Phase-4 states: active -> abandoned only (S-1)."""
    from app.core.errors import ConflictError, ResourceNotFoundError

    repository = CSessionRecordRepository(session)
    record = await repository.get_owned(c_session_id, student_id)
    if record is None:
        raise ResourceNotFoundError()
    if record.state != "active":
        raise ConflictError()
    record.state = "abandoned"
    record.row_version += 1
    await session.flush()
    return record
