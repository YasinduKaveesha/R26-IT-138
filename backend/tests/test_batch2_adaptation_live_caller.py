"""Component C backend remediation, Batch 2: ``decide_and_persist_adaptation``'s first live
caller under ``app/`` -- ``task_service.submit_action``'s ``is_correct`` branch, wired
immediately after ``derive_and_persist_summary`` (ordering load-bearing, see
``task_service.py``'s own in-line comment at that call site).

WIRED, NOT REACHABLE (restated for this file specifically, same shape as every prior Component C
serving-path test file): the six-family session-creation gate
(``session_lifecycle.create_session``) still refuses every real HTTP request. Every positive
control below calls ``TaskService`` methods directly against a ``smoke_mode=True``-created
session, mirroring ``test_c5_task_serve_and_evaluate.py``'s own precedent exactly -- never through
``TestClient``, because there is no way to reach a session through the real route in this batch.
"""

from __future__ import annotations

import asyncio
import subprocess
from uuid import uuid4

import pytest

from app.application.live_engine_c import task_service as task_service_module
from app.application.live_engine_c.bundle_resolution import assert_policy_config_matches_session_gate
from app.application.live_engine_c.c_session_service import _NOT_LIVE_PARAMETER_SOURCE_STATUS
from app.application.live_engine_c.task_service import (
    PRODUCTION_EVIDENCE_WINDOW_CONFIG_PROBE,
    PRODUCTION_GENERATION_CONFIG_PROBE,
    PRODUCTION_POLICY_CONFIG_PROBE,
    PRODUCTION_POLICY_MODE,
    PRODUCTION_SCAFFOLD_CONFIG_PROBE,
    TaskService,
)
from app.domain.live_engine_c.errors import ConfigurationFamilyNotUsableError
from app.domain.live_engine_c.types import PolicyConfig
from app.infrastructure.repositories import CPolicyDecisionRecordRepository
from tests.test_c4_session_lifecycle import isolated_database
from tests.test_c6a_summary_derivation import _create_real_instance_for_c_cc_03


def alembic(*args: str) -> None:
    subprocess.run(["alembic", *args], check=True)


# =====================================================================================
# THE SEAM -- assert_policy_config_matches_session_gate, unit-tested directly (no DB needed):
# the session-start gate (assert_code_gated_family_usable) takes policy_parameter_source_status
# as a separate string; this function is what ties it to the PolicyConfig object actually reaching
# decide_and_persist_adaptation. Both directions proven: matching passes, mismatched refuses and
# names the family.
# =====================================================================================


def _policy_config_with_status(status: str) -> PolicyConfig:
    return PolicyConfig(
        config_version="seam-test-probe",
        parameter_source_status=status,
        increase_correctness_threshold=0.9,
        increase_max_avg_attempts=2.0,
        increase_max_strain=0.1,
        decrease_correctness_threshold=0.2,
        decrease_error_run_threshold=5,
        decrease_min_strain=0.8,
    )


def test_seam_matching_status_does_not_raise() -> None:
    assert_policy_config_matches_session_gate(
        _policy_config_with_status("TEST_FIXTURE_ONLY"),
        session_gated_parameter_source_status="TEST_FIXTURE_ONLY",
    )  # does not raise


def test_seam_mismatched_status_raises_and_names_policy_config() -> None:
    """The scenario the seam exists to catch: a PolicyConfig whose own parameter_source_status
    differs from the status this session was gated on at creation -- e.g. a future session-start
    resolution reading a governed status while the object reaching adaptation still carries the
    old one. Must refuse, and must name policy_config/parameter_source_status, never the values
    themselves (X1/Z2's own one-mechanism discipline)."""
    with pytest.raises(ConfigurationFamilyNotUsableError) as excinfo:
        assert_policy_config_matches_session_gate(
            _policy_config_with_status("TEST_FIXTURE_ONLY"),
            session_gated_parameter_source_status="APPROVED",
        )
    assert excinfo.value.family_name == "policy_config"
    assert excinfo.value.unusable_fields == ("parameter_source_status",)


def test_production_policy_config_probe_carries_the_session_gate_status() -> None:
    """Positive control for the seam's own real inputs: PRODUCTION_POLICY_CONFIG_PROBE's
    parameter_source_status is the SAME imported _NOT_LIVE_PARAMETER_SOURCE_STATUS constant
    session_lifecycle's own six-family gate is fed at session creation -- not a second,
    independently-typed literal that merely happens to read the same today. Would FAIL if either
    constant were ever edited without the other."""
    assert PRODUCTION_POLICY_CONFIG_PROBE.parameter_source_status == _NOT_LIVE_PARAMETER_SOURCE_STATUS
    assert_policy_config_matches_session_gate(
        PRODUCTION_POLICY_CONFIG_PROBE,
        session_gated_parameter_source_status=_NOT_LIVE_PARAMETER_SOURCE_STATUS,
    )  # does not raise -- the real call site's own seam check currently passes


# =====================================================================================
# THE POLICY PROBE -- SUPERVISOR RULING: values must NOT be indistinguishable from a real
# calibration. Proven structurally against the pinned package's own default_policy_config(), so a
# future edit "correcting" the probe toward those values breaks this test rather than silently
# reintroducing the worst-failure-mode shape the ruling exists to prevent.
# =====================================================================================


def test_production_evidence_window_config_probe_uses_the_cited_window_not_an_invented_one() -> None:
    """EvidenceWindowConfig's recent_window_task_count is, unlike Policy's six fields, SPEC-cited
    (C Parameters §14: N=5) -- this probe uses that cited value, the same one the pinned
    package's own (also TEST_FIXTURE_ONLY) default_evidence_window_config() returns, rather than
    inventing a placeholder. See PRODUCTION_EVIDENCE_WINDOW_CONFIG_PROBE's own comment in
    task_service.py for why this family is not gated at session creation at all today (an open
    finding, not a decision made here)."""
    from component_c_generator.pipeline.config import default_evidence_window_config

    assert PRODUCTION_EVIDENCE_WINDOW_CONFIG_PROBE.recent_window_task_count == (
        default_evidence_window_config().recent_window_task_count
    )
    assert PRODUCTION_EVIDENCE_WINDOW_CONFIG_PROBE.parameter_source_status == _NOT_LIVE_PARAMETER_SOURCE_STATUS


def test_production_policy_config_probe_does_not_mirror_the_real_defaults() -> None:
    from component_c_generator.policy.config import default_policy_config

    real = default_policy_config()
    probe = PRODUCTION_POLICY_CONFIG_PROBE
    assert probe.config_version != real.config_version
    for field in (
        "increase_correctness_threshold", "increase_max_avg_attempts", "increase_max_strain",
        "decrease_correctness_threshold", "decrease_error_run_threshold", "decrease_min_strain",
    ):
        assert getattr(probe, field) != getattr(real, field), field
    # And still TEST_FIXTURE_ONLY, same status class as every other config anywhere in this
    # codebase (S1's own words) -- never silently promoted to a governed-looking status.
    assert probe.parameter_source_status == "TEST_FIXTURE_ONLY"


# =====================================================================================
# POSITIVE CONTROL -- a correct-answer submission writes exactly one c_policy_decisions row,
# asserted from the database (never inferred from the absence of an exception).
# =====================================================================================


def test_correct_answer_writes_exactly_one_policy_decision_row() -> None:
    alembic("upgrade", "head")

    async def exercise() -> None:
        database_engine, factory = isolated_database()
        async with factory() as session:
            subject = f"batch2-correct-{uuid4()}"
            _, c_session_id, instance_id, instance = await _create_real_instance_for_c_cc_03(
                session, subject=subject
            )
            # C-CC-03's own evaluator (tasks/count_and_collect.py::_evaluate_cc03) is
            # action["selected_numeral"] == correct["cardinality"] -- NO key-name correspondence
            # between correct_answer_payload and valid_action_space (see
            # _create_real_instance_for_c_cc_03's own docstring, test_c6a_summary_derivation.py).
            correct_payload = {"selected_numeral": instance.correct_answer_payload["cardinality"]}

            result = await TaskService().submit_action(
                session, principal_user_id=subject, request_id=f"req-{uuid4()}",
                c_session_id=c_session_id, c_task_instance_id=instance_id,
                action_payload=correct_payload, generation_config=PRODUCTION_GENERATION_CONFIG_PROBE,
                scaffold_config=PRODUCTION_SCAFFOLD_CONFIG_PROBE,
            )
            assert result.response_matched is True, (
                "fixture assumption failed: C-CC-03's own correct_answer_payload did not evaluate "
                "correct -- this test's premise (a guaranteed-correct submission) no longer holds"
            )

            rows = await CPolicyDecisionRecordRepository(session).list_chronological_for_session(c_session_id)
            assert len(rows) == 1
            row = rows[0]
            assert row.c_session_id == c_session_id
            assert row.policy_mode == PRODUCTION_POLICY_MODE
        await database_engine.dispose()

    asyncio.run(exercise())


# =====================================================================================
# NEGATIVE CONTROL -- an incorrect-answer submission writes none. Proves the row above is
# conditioned on evaluation.is_correct, not written unconditionally.
# =====================================================================================


def test_incorrect_answer_writes_no_policy_decision_row() -> None:
    alembic("upgrade", "head")

    async def exercise() -> None:
        database_engine, factory = isolated_database()
        async with factory() as session:
            subject = f"batch2-incorrect-{uuid4()}"
            _, c_session_id, instance_id, instance = await _create_real_instance_for_c_cc_03(
                session, subject=subject
            )
            wrong_payload = {"selected_numeral": instance.correct_answer_payload["cardinality"] + 1000}

            result = await TaskService().submit_action(
                session, principal_user_id=subject, request_id=f"req-{uuid4()}",
                c_session_id=c_session_id, c_task_instance_id=instance_id,
                action_payload=wrong_payload, generation_config=PRODUCTION_GENERATION_CONFIG_PROBE,
                scaffold_config=PRODUCTION_SCAFFOLD_CONFIG_PROBE,
            )
            assert result.response_matched is False

            rows = await CPolicyDecisionRecordRepository(session).list_chronological_for_session(c_session_id)
            assert rows == []
        await database_engine.dispose()

    asyncio.run(exercise())


# =====================================================================================
# ORDERING -- the adaptation call happens AFTER the summary is persisted. Proven by call-order
# spy (monkeypatching the two names as task_service.py itself resolves them), never merely by
# both having occurred: two calls in the wrong order could still both "occur" and both still
# succeed on a session whose history already has an earlier summary, so a same-occurred check
# would not catch a swap. This test also exercises the FIRST task of a fresh session (empty
# history before this call), where a swap would additionally crash with the pinned
# build_policy_evidence's own ValueError -- both checks independently guard the same property.
# =====================================================================================


def test_adaptation_call_happens_after_summary_is_persisted(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.application.live_engine_c.adaptation_service import decide_and_persist_adaptation as real_decide
    from app.application.live_engine_c.summary_service import derive_and_persist_summary as real_derive

    call_order: list[str] = []

    async def spy_derive_and_persist_summary(*args, **kwargs):
        result = await real_derive(*args, **kwargs)
        call_order.append("summary_persisted")
        return result

    async def spy_decide_and_persist_adaptation(*args, **kwargs):
        call_order.append("adaptation_called")
        return await real_decide(*args, **kwargs)

    monkeypatch.setattr(task_service_module, "derive_and_persist_summary", spy_derive_and_persist_summary)
    monkeypatch.setattr(task_service_module, "decide_and_persist_adaptation", spy_decide_and_persist_adaptation)

    alembic("upgrade", "head")

    async def exercise() -> None:
        database_engine, factory = isolated_database()
        async with factory() as session:
            subject = f"batch2-ordering-{uuid4()}"
            _, c_session_id, instance_id, instance = await _create_real_instance_for_c_cc_03(
                session, subject=subject
            )
            correct_payload = {"selected_numeral": instance.correct_answer_payload["cardinality"]}

            result = await task_service_module.TaskService().submit_action(
                session, principal_user_id=subject, request_id=f"req-{uuid4()}",
                c_session_id=c_session_id, c_task_instance_id=instance_id,
                action_payload=correct_payload, generation_config=PRODUCTION_GENERATION_CONFIG_PROBE,
                scaffold_config=PRODUCTION_SCAFFOLD_CONFIG_PROBE,
            )
            assert result.response_matched is True, (
                "fixture assumption failed: C-CC-03's own correct_answer_payload did not evaluate "
                "correct -- this test's premise (a guaranteed-correct submission) no longer holds"
            )
        await database_engine.dispose()

    asyncio.run(exercise())

    assert call_order == ["summary_persisted", "adaptation_called"]
