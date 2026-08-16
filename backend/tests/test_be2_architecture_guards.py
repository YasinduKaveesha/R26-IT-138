"""Static guards for the BE2 Limited authorization boundary, extended (Phase 1 batch 1b) with
Component C's full-dotted-path import boundary and column-guard mechanism proof."""

import ast
import dataclasses
import re
from pathlib import Path

from sqlalchemy import Column, Integer, MetaData, String, Table

from app.domain.live_engine_c.types import (
    AggregationConfig,
    EvidenceWindowConfig,
    GenerationConfig,
    PolicyConfig,
    RecoveryConfig,
    SafetyConfig,
    ScaffoldConfig,
    SelectionConfig,
    TemplateGenerationParams,
)
from app.infrastructure.persistence_models import AUTHORIZED_TABLES, Base
from app.main import app
from tests.test_c1a_wheel_provenance import NEVER_SHIP_MODULES


EXPECTED_TABLES = {
    "app_users",
    "b_learners",
    "app_user_learner_links",
    "b_runtime_bundle_records",
    "b_sessions",
    "b_session_events",
    "b_idempotency_records",
    "b_audit_events",
    "teacher_profiles", "classrooms", "classroom_invites", "classroom_memberships",
    "teacher_profiles", "classrooms", "classroom_invites", "classroom_memberships",
    # BE4a (BEplan §9 BE4.1) — private opportunity/task-instance/presentation-token tables.
    "b_item_opportunities", "b_task_instances", "b_presentation_tokens",
    # BE4b (BEplan §9 BE4.2) — private per-learner, per-skill BKT state.
    "b_learner_skill_states",
    # BE4c (BEplan §9 BE4.3 + BE4.4) — private attempt events + immutable BKT transitions.
    "b_attempts", "b_skill_state_transitions",
    # BE4d (BEplan §9 BE4.5) — private governed hint events, separate from attempts/transitions.
    "b_hint_events",
    # BE4e (BEplan §9 BE4.6) — private, immutable session-aggregate + skill-certification results.
    "b_session_aggregate_results", "b_skill_certification_results",
    # Component C Phase 2 — mirrors b_runtime_bundle_records for Component C's own wheel pin.
    "c_runtime_bundle_records",
    # Component C Phase 3a (v3.0 §11 Phase 3) — the ten tables, created by their own migration
    # (20260816_0002), not BE2's 0002.
    "c_sessions", "c_task_opportunities", "c_task_instances", "c_gameplay_events",
    "c_task_opportunity_summaries", "c_session_aggregate_results", "c_learner_local_state",
    "c_policy_decisions", "c_safety_events", "c_scaffold_events",
}
BE2_BASE_TABLES = EXPECTED_TABLES - {
    "teacher_profiles", "classrooms", "classroom_invites", "classroom_memberships",
    "b_item_opportunities", "b_task_instances", "b_presentation_tokens",
    "b_learner_skill_states",
    "b_attempts", "b_skill_state_transitions",
    "b_hint_events",
    "b_session_aggregate_results", "b_skill_certification_results",
    # Component C Phase 2 — created by its own migration (20260816_0001), not BE2's 0002.
    "c_runtime_bundle_records",
    # Component C Phase 3a — created by their own migration (20260816_0002), not BE2's 0002.
    "c_sessions", "c_task_opportunities", "c_task_instances", "c_gameplay_events",
    "c_task_opportunity_summaries", "c_session_aggregate_results", "c_learner_local_state",
    "c_policy_decisions", "c_safety_events", "c_scaffold_events",
}
PROHIBITED_COLUMN_TERMS = {
    "mastery", "bkt", "guess_guard", "certif", "sequenc", "hint", "answer",
    "correct", "error_class", "population", "dd_subtype", "true_mastery",
    "simulated", "latency", "off_day", "random_effect", "experiment",
}
# "answer" and "correct" stay in the blanket prohibition above (blocked everywhere by default).
# BEplan §9 BE4.1 authorizes exactly two PRIVATE columns to carry them — behind the BE3c
# private/public split (never read by any public-DTO projection; see
# ``app.domain.b_opportunity.project_task_instance_to_presentation``) — and only those two cells
# are exempted, via this explicit, minimal allow-list rather than a global term removal.
AUTHORIZED_ANSWER_BEARING_COLUMNS = {
    ("b_task_instances", "correct_answer"),
    ("b_task_instances", "allowed_equivalent_answers"),
}


def test_exact_authorized_model_table_set_and_no_scientific_columns() -> None:
    """R-A (Phase 3a work order): this test's exemption sets are now
    AUTHORIZED_ANSWER_BEARING_COLUMNS | AUTHORIZED_C_COLUMN_EXCEPTIONS. Phase 1b's "leave it
    byte-identical" instruction is superseded for this test and this reason only, per the
    Phase 3a work order's binding ruling R-A. AUTHORIZED_ANSWER_BEARING_COLUMNS itself keeps its
    two B entries and its name, unchanged; C's pairs live in the separate, named
    AUTHORIZED_C_COLUMN_EXCEPTIONS so provenance stays legible. Every assertion below stays
    EXACT EQUALITY -- none relaxed to a subset check (R-A binding condition)."""
    assert AUTHORIZED_TABLES == EXPECTED_TABLES
    assert set(Base.metadata.tables) == EXPECTED_TABLES

    exemptions = AUTHORIZED_ANSWER_BEARING_COLUMNS | AUTHORIZED_C_COLUMN_EXCEPTIONS

    # The allow-list itself must not be stale: every exempted column must actually exist on its
    # named table, and no other table may have an answer/correct-bearing column at all.
    table_columns = {
        table.name: {column.name for column in table.columns} for table in Base.metadata.tables.values()
    }
    for table_name, column_name in exemptions:
        assert column_name in table_columns.get(table_name, set()), (table_name, column_name)
    answer_bearing = {
        (table.name, column.name)
        for table in Base.metadata.tables.values()
        for column in table.columns
        if any(term in column.name.lower() for term in ("answer", "correct"))
    }
    answer_bearing_exemptions = {
        pair for pair in exemptions if any(term in pair[1].lower() for term in ("answer", "correct"))
    }
    assert answer_bearing == answer_bearing_exemptions

    offenders = {
        (table.name, column.name)
        for table in Base.metadata.tables.values()
        for column in table.columns
        if any(term in column.name.lower() for term in PROHIBITED_COLUMN_TERMS)
        and (table.name, column.name) not in exemptions
    }
    assert not offenders, offenders


EXPECTED_ROUTES = {
    ("/health/live", ("GET",)),
    ("/health/ready", ("GET",)),
    ("/api/v1/me", ("GET",)),
    ("/api/v1/teacher/profile", ("GET", "POST")),
    ("/api/v1/learner/profile", ("GET", "POST")),
    ("/api/v1/classrooms", ("GET", "POST")),
    ("/api/v1/classrooms/{classroom_id}", ("GET",)),
    ("/api/v1/classrooms/{classroom_id}/invites", ("POST",)),
    ("/api/v1/classroom-invites/{classroom_invite_id}/revoke", ("POST",)),
    ("/api/v1/classroom-invites/resolve", ("POST",)),
    ("/api/v1/classroom-memberships/requests", ("POST",)),
    ("/api/v1/classrooms/{classroom_id}/membership-requests", ("GET",)),
    ("/api/v1/classroom-memberships/{membership_id}/approve", ("POST",)),
    ("/api/v1/classroom-memberships/{membership_id}/reject", ("POST",)),
    ("/api/v1/classrooms/{classroom_id}/learners", ("GET",)),
    ("/api/v1/learner/classrooms", ("GET",)),
    ("/api/v1/b/sessions", ("POST",)),
    ("/api/v1/b/sessions/active", ("GET",)),
    ("/api/v1/b/sessions/{session_id}/complete", ("POST",)),
    ("/api/v1/b/sessions/{session_id}/abandon", ("POST",)),
    # BE4b (BEplan §9 BE4.2) — the one authorized adaptive-selection route.
    ("/api/v1/b/sessions/{session_id}/opportunities", ("POST",)),
    # BE4c (BEplan §9 BE4.3 + BE4.4) — the one authorized attempt-submission route.
    ("/api/v1/b/sessions/{session_id}/opportunities/{item_opportunity_id}/responses", ("POST",)),
    # BE4d (BEplan §9 BE4.5) — the one authorized governed-hint-request route.
    ("/api/v1/b/sessions/{session_id}/opportunities/{item_opportunity_id}/assists", ("POST",)),
    # BE4e (BEplan §9 BE4.6) — the two authorized next-or-complete / SAFE-standing routes.
    ("/api/v1/b/sessions/{session_id}/opportunities/{item_opportunity_id}/complete", ("POST",)),
    ("/api/v1/b/sessions/{session_id}/summary", ("GET",)),
}
AUTHORIZED_INVITE_MEMBERSHIP_OPERATIONS = {
    ("/api/v1/classrooms/{classroom_id}/invites", ("POST",)),
    ("/api/v1/classroom-invites/resolve", ("POST",)),
    ("/api/v1/classroom-memberships/requests", ("POST",)),
    ("/api/v1/classrooms/{classroom_id}/membership-requests", ("GET",)),
    ("/api/v1/classroom-memberships/{membership_id}/approve", ("POST",)),
    ("/api/v1/classroom-memberships/{membership_id}/reject", ("POST",)),
    ("/api/v1/classrooms/{classroom_id}/learners", ("GET",)),
    ("/api/v1/learner/classrooms", ("GET",)),
    ("/api/v1/classroom-invites/{classroom_invite_id}/revoke", ("POST",)),
}
AUTHORIZED_B_SESSION_LIFECYCLE_OPERATIONS = {
    ("/api/v1/b/sessions", ("POST",)),
    ("/api/v1/b/sessions/active", ("GET",)),
    ("/api/v1/b/sessions/{session_id}/complete", ("POST",)),
    ("/api/v1/b/sessions/{session_id}/abandon", ("POST",)),
}
AUTHORIZED_B_OPPORTUNITY_SELECTION_OPERATIONS = {
    ("/api/v1/b/sessions/{session_id}/opportunities", ("POST",)),
}
AUTHORIZED_B_ATTEMPT_SUBMISSION_OPERATIONS = {
    ("/api/v1/b/sessions/{session_id}/opportunities/{item_opportunity_id}/responses", ("POST",)),
}
AUTHORIZED_B_HINT_REQUEST_OPERATIONS = {
    ("/api/v1/b/sessions/{session_id}/opportunities/{item_opportunity_id}/assists", ("POST",)),
}
AUTHORIZED_B_SESSION_COMPLETION_OPERATIONS = {
    ("/api/v1/b/sessions/{session_id}/opportunities/{item_opportunity_id}/complete", ("POST",)),
    ("/api/v1/b/sessions/{session_id}/summary", ("GET",)),
}
PROHIBITED_SCIENTIFIC_PATH_TERMS = (
    "session", "attempt", "hint", "progress", "bkt", "mastery", "sequenc", "certif", "guess",
)


def _current_routes() -> set[tuple[str, tuple[str, ...]]]:
    return {
        (path, tuple(sorted(method.upper() for method in operations)))
        for path, operations in app.openapi()["paths"].items()
    }


def test_no_new_api_route_or_lifecycle_service() -> None:
    assert _current_routes() == EXPECTED_ROUTES
    assert not any(Path("app").rglob("*session*service*.py"))


def test_openapi_contains_exactly_the_nine_authorized_invite_membership_operations() -> None:
    assert len(AUTHORIZED_INVITE_MEMBERSHIP_OPERATIONS) == 9
    assert AUTHORIZED_INVITE_MEMBERSHIP_OPERATIONS <= _current_routes()
    assert _current_routes() - AUTHORIZED_INVITE_MEMBERSHIP_OPERATIONS == {
        route for route in EXPECTED_ROUTES if route not in AUTHORIZED_INVITE_MEMBERSHIP_OPERATIONS
    }


def test_no_session_question_answer_or_scientific_route_exists() -> None:
    """The blanket "session" path prohibition is carved out only for the four
    authorized BE2.3-BE2.4 neutral session-lifecycle routes plus the one BE4b adaptive-
    selection route (BEplan §9 BE4.2) plus the one BE4c attempt-submission route (BEplan §9
    BE4.3 + BE4.4) plus the one BE4d hint-request route (BEplan §9 BE4.5) plus the two BE4e
    next-or-complete / SAFE-standing routes (BEplan §9 BE4.6); every other prohibited scientific
    term remains prohibited unconditionally, including on those routes themselves — in
    particular every route must never contain "attempt", "hint", "progress", "bkt", "mastery",
    "sequenc", "certif", or "guess" (the BE4e routes spell completion as "complete"/"summary",
    never "progress")."""
    for route in _current_routes():
        path, _ = route
        lowered = path.lower()
        terms = PROHIBITED_SCIENTIFIC_PATH_TERMS
        if (
            route in AUTHORIZED_B_SESSION_LIFECYCLE_OPERATIONS
            or route in AUTHORIZED_B_OPPORTUNITY_SELECTION_OPERATIONS
            or route in AUTHORIZED_B_ATTEMPT_SUBMISSION_OPERATIONS
            or route in AUTHORIZED_B_HINT_REQUEST_OPERATIONS
            or route in AUTHORIZED_B_SESSION_COMPLETION_OPERATIONS
        ):
            terms = tuple(term for term in terms if term != "session")
        assert not any(term in lowered for term in terms), path


def test_openapi_contains_exactly_the_two_authorized_b_session_completion_operations() -> None:
    assert len(AUTHORIZED_B_SESSION_COMPLETION_OPERATIONS) == 2
    assert AUTHORIZED_B_SESSION_COMPLETION_OPERATIONS <= _current_routes()
    non_completion_routes = {route for route in EXPECTED_ROUTES if route not in AUTHORIZED_B_SESSION_COMPLETION_OPERATIONS}
    assert _current_routes() - AUTHORIZED_B_SESSION_COMPLETION_OPERATIONS == non_completion_routes


def test_openapi_contains_exactly_the_one_authorized_b_attempt_submission_operation() -> None:
    assert len(AUTHORIZED_B_ATTEMPT_SUBMISSION_OPERATIONS) == 1
    assert AUTHORIZED_B_ATTEMPT_SUBMISSION_OPERATIONS <= _current_routes()
    non_attempt_routes = {route for route in EXPECTED_ROUTES if route not in AUTHORIZED_B_ATTEMPT_SUBMISSION_OPERATIONS}
    assert _current_routes() - AUTHORIZED_B_ATTEMPT_SUBMISSION_OPERATIONS == non_attempt_routes


def test_openapi_contains_exactly_the_one_authorized_b_hint_request_operation() -> None:
    assert len(AUTHORIZED_B_HINT_REQUEST_OPERATIONS) == 1
    assert AUTHORIZED_B_HINT_REQUEST_OPERATIONS <= _current_routes()
    non_hint_routes = {route for route in EXPECTED_ROUTES if route not in AUTHORIZED_B_HINT_REQUEST_OPERATIONS}
    assert _current_routes() - AUTHORIZED_B_HINT_REQUEST_OPERATIONS == non_hint_routes


def test_openapi_contains_exactly_the_four_authorized_b_session_lifecycle_operations() -> None:
    assert len(AUTHORIZED_B_SESSION_LIFECYCLE_OPERATIONS) == 4
    assert AUTHORIZED_B_SESSION_LIFECYCLE_OPERATIONS <= _current_routes()
    non_session_routes = {route for route in EXPECTED_ROUTES if route not in AUTHORIZED_B_SESSION_LIFECYCLE_OPERATIONS}
    assert _current_routes() - AUTHORIZED_B_SESSION_LIFECYCLE_OPERATIONS == non_session_routes


def test_b_session_dto_contains_no_scientific_expiry_or_attempt_fields() -> None:
    """Scans actual DTO field identifiers only (via AST), not prose/docstrings, since
    this module's docstring legitimately documents excluded terms by name."""
    tree = ast.parse(Path("app/domain/b_session.py").read_text(encoding="utf-8"))
    field_names = {
        node.target.id.lower()
        for class_def in ast.walk(tree)
        if isinstance(class_def, ast.ClassDef)
        for node in class_def.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    }
    forbidden = PROHIBITED_COLUMN_TERMS | {
        "expires_at", "expiry", "timeout", "question", "attempt", "opportunity",
    }
    assert not {name for name in field_names if any(term in name for term in forbidden)}


def test_no_yass_research_or_scientific_imports() -> None:
    """BE3b wires ``app/infrastructure/live_engine/adapter.py`` to the reviewed
    ``component_b_generator`` package (see ``tests/test_be3_live_engine_boundary.py`` for the
    detailed BE3 import-boundary guards). That one file is therefore exempt from the
    ``component_b_generator`` top-level prohibition here, but not from ``yass``/``pipeline``/
    ``pilot`` — every other file in ``app/`` stays fully disjoint from all of these roots."""
    prohibited_import_roots = {
        "component_b_generator", "yass", "bkt", "sequencing", "certification",
        "guess_guard", "pipeline", "pilot",
    }
    allowed_adapter_path = Path("app/infrastructure/live_engine/adapter.py")
    for path in Path("app").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name.split(".")[0].lower() for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported = {node.module.split(".")[0].lower()}
            else:
                continue
            if path == allowed_adapter_path:
                assert imported.isdisjoint({"yass", "pipeline", "pilot"}), (path, imported)
                continue
            assert imported.isdisjoint(prohibited_import_roots), (path, imported)


def test_dependency_files_exclude_research_generator() -> None:
    dependency_files = [
        path
        for name in ("requirements.in", "requirements.lock", "requirements.txt")
        if (path := Path(name)).exists()
    ]
    assert dependency_files
    dependency_text = "\n".join(path.read_text(encoding="utf-8") for path in dependency_files).lower()
    assert "component-b-generator" not in dependency_text
    assert "component_b_generator" not in dependency_text
    assert "yass" not in dependency_text


def test_migration_introduces_only_authorized_tables_and_no_triggers_or_seed_data() -> None:
    migration = Path("migrations/versions/20260722_0002_be2_neutral_persistence.py").read_text(encoding="utf-8")
    created = set(re.findall(r'op\.create_table\(\s*"([^"]+)"', migration))
    assert created == BE2_BASE_TABLES
    lowered = migration.lower()
    assert "create_trigger" not in lowered
    assert "create trigger" not in lowered
    assert "bulk_insert" not in lowered
    assert "op.execute" not in lowered


def test_corrective_migration_adds_only_the_two_authorized_integrity_guards() -> None:
    migration = Path("migrations/versions/20260722_0003_bundle_integrity_guards.py").read_text(
        encoding="utf-8"
    )
    assert not re.findall(r'op\.create_table\(\s*"([^"]+)"', migration)
    assert "enforce_b_session_active_bundle_eligibility" in migration
    assert "trg_b_sessions_active_bundle_eligible" in migration
    assert "enforce_b_runtime_bundle_integrity" in migration
    assert "trg_b_runtime_bundle_integrity" in migration
    lowered = migration.lower()
    assert "insert into" not in lowered
    assert "component_b_generator" not in lowered
    assert "yass" not in lowered


def test_profile_classroom_migration_and_routes_stay_within_authorization() -> None:
    migration = Path("migrations/versions/20260722_0004_profile_classroom_foundations.py").read_text(encoding="utf-8")
    assert set(re.findall(r'op\.create_table\(\s*"([^"]+)"', migration)) == {"teacher_profiles", "classrooms", "classroom_invites", "classroom_memberships"}
    lowered = migration.lower()
    assert "learner_profiles" not in lowered
    assert "bulk_insert" not in lowered
    assert "component_b_generator" not in lowered
    assert "yass" not in lowered
    # The blanket "no invite/membership path" check from the prior limited batch is
    # superseded by the now-authorized invite/membership batch; see
    # test_invite_membership_migration_adds_only_the_authorized_index and
    # test_openapi_contains_exactly_the_nine_authorized_invite_membership_operations
    # for the current, narrower boundary checks. Session/scientific paths remain
    # prohibited unconditionally; see test_no_session_question_answer_or_scientific_route_exists.


def test_invite_membership_migration_adds_only_the_authorized_index() -> None:
    migration = Path("migrations/versions/20260723_0001_classroom_membership_single_approval.py").read_text(encoding="utf-8")
    assert not re.findall(r'op\.create_table\(\s*"([^"]+)"', migration)
    assert not re.findall(r'op\.add_column\(', migration)
    assert not re.findall(r'op\.drop_column\(', migration)
    assert "uq_classroom_memberships_one_approved_per_learner" in migration
    assert '"classroom_memberships"' in migration
    lowered = migration.lower()
    assert "classroom_invites" not in lowered
    assert "create_trigger" not in lowered
    assert "create trigger" not in lowered
    assert "bulk_insert" not in lowered
    assert "component_b_generator" not in lowered
    assert "yass" not in lowered


def test_no_production_failure_injection_or_debug_mechanism() -> None:
    """The corrective batch injects failure only in tests; production code exposes no such hook."""
    markers = (
        "controlled-test-failure", "_failing_audit", "inject_fail", "injectfailure",
        "fail_flag", "failure_flag", "debug_fail", "force_error", "force_failure",
    )
    for path in Path("app").rglob("*.py"):
        lowered = path.read_text(encoding="utf-8").lower()
        for marker in markers:
            assert marker not in lowered, (path, marker)
    paths = set(app.openapi()["paths"])
    assert not any("debug" in path or "inject" in path or "/test" in path for path in paths)


# =====================================================================================
# Phase 1 batch 1b — Component C full-dotted-path import boundary (C-8).
#
# The B guard above (test_no_yass_research_or_scientific_imports) matches import ROOTS only via
# `.split(".")[0]`, which is correct for B but insufficient for C: both the legitimate
# `component_c_generator.pipeline.evidence` and the prohibited
# `component_c_generator.pipeline.session` share the identical root `component_c_generator` --
# a root-only check cannot distinguish them. B's guard, its prohibited_import_roots set, and its
# exempt path are left completely untouched above; everything below is new, additive, and
# independent.
# =====================================================================================

_ALLOWED_C_ADAPTER_PATH = Path("app/infrastructure/live_engine_c/adapter.py")

# The 16 never-ship C module paths, sourced from 1a's own list rather than hand-copied here --
# see test_prohibited_c_full_dotted_paths_matches_1a_never_ship_modules below, which proves this
# derivation stays correct rather than merely asserting it once at import time.
PROHIBITED_C_FULL_DOTTED_PATHS = frozenset(NEVER_SHIP_MODULES)


def _full_dotted_import_candidates(node: ast.AST) -> set[str]:
    """Every full dotted path a single Import/ImportFrom AST node could bind into scope.

    For `ast.ImportFrom` this includes BOTH the bare `node.module` (covers
    `from component_c_generator.pipeline.session import X`, where the prohibited path is
    already the whole module) AND `f"{node.module}.{alias.name}"` for every imported name
    (covers `from component_c_generator.pipeline import session`, where the prohibited path
    only appears once the imported name is appended)."""
    if isinstance(node, ast.Import):
        return {alias.name for alias in node.names}
    if isinstance(node, ast.ImportFrom) and node.module:
        return {node.module} | {f"{node.module}.{alias.name}" for alias in node.names}
    return set()


def _matches_prohibited_full_path(candidate: str, prohibited: frozenset[str]) -> bool:
    """Exact match or dot-bounded prefix match -- NEVER substring containment. This is what
    lets `component_c_generator.pipeline.evidence` pass (it is neither equal to, nor a
    dot-prefix of, any prohibited entry) while `component_c_generator.pipeline.session` and
    `component_c_generator.audits.leakage` (a dot-prefix of the whole-package entry
    `component_c_generator.audits`) are both caught."""
    return any(candidate == p or candidate.startswith(p + ".") for p in prohibited)


def test_component_c_generator_full_dotted_path_enforcement() -> None:
    """SIGNAL: only app/infrastructure/live_engine_c/adapter.py may have `component_c_generator`
    as an import root anywhere under app/ (root check, same style as B's guard); even inside
    that one exempt file, none of the 16 never-ship full dotted paths may appear among its
    import candidates (full-dotted-path check, matched via
    _matches_prohibited_full_path -- exact-or-dot-prefix, never substring). Would FAIL if any
    other file under app/ imported component_c_generator at all, or if the adapter itself
    imported e.g. `component_c_generator.pipeline.session` or `component_c_generator.audits.*`."""
    for path in Path("app").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            candidates = _full_dotted_import_candidates(node)
            roots = {c.split(".")[0] for c in candidates}
            if path != _ALLOWED_C_ADAPTER_PATH:
                assert "component_c_generator" not in roots, (path, candidates)
                continue
            for candidate in candidates:
                if candidate.split(".")[0] != "component_c_generator":
                    continue
                assert not _matches_prohibited_full_path(
                    candidate, PROHIBITED_C_FULL_DOTTED_PATHS
                ), (path, candidate)


def test_full_dotted_path_guard_negative_control_catches_same_root_violation() -> None:
    """POSITIVE PROOF the full-dotted-path matcher is doing real work, not merely inheriting B's
    root-only check. Parses SYNTHETIC, in-memory module source -- never a file under app/, which
    would be a real boundary breach waiting to be committed by accident -- containing
    `from component_c_generator.pipeline import session`, a SAME-ROOT, DIFFERENT-FULL-PATH case
    the OLD root-only matcher could not have distinguished from the legitimate
    `from component_c_generator.pipeline import evidence` (both share root
    `component_c_generator`, exempted for the adapter path). Would FAIL (silently) if the
    matcher were reverted to root-only, since both cases share the same root and a root-only
    check cannot discriminate them -- this is the discrimination pair the negative control
    exists to prove."""
    violating_source = "from component_c_generator.pipeline import session\n"
    legitimate_source = "from component_c_generator.pipeline import evidence\n"

    violating_tree = ast.parse(violating_source, filename="<synthetic-negative-control-violation>")
    legitimate_tree = ast.parse(legitimate_source, filename="<synthetic-negative-control-legitimate>")

    def _any_prohibited(tree: ast.AST) -> bool:
        return any(
            _matches_prohibited_full_path(candidate, PROHIBITED_C_FULL_DOTTED_PATHS)
            for node in ast.walk(tree)
            for candidate in _full_dotted_import_candidates(node)
        )

    assert _any_prohibited(violating_tree), "negative control failed to catch a real violation"
    assert not _any_prohibited(legitimate_tree), (
        "guard incorrectly flagged a legitimate sibling import -- it is not discriminating"
    )


def test_prohibited_c_full_dotted_paths_matches_1a_never_ship_modules() -> None:
    """SIGNAL: PROHIBITED_C_FULL_DOTTED_PATHS (this file, used operationally by the guard above)
    stays set-equal to NEVER_SHIP_MODULES (backend/tests/test_c1a_wheel_provenance.py, the
    16-module never-ship list 1a's wheel-content tests assert against). Would FAIL the moment
    the two lists diverge -- e.g. if a future Phase 1a revision adds a 17th never-ship module and
    this file is not updated to match -- rather than silently leaving this guard one module
    weaker than the wheel's own packaging boundary."""
    assert PROHIBITED_C_FULL_DOTTED_PATHS == frozenset(NEVER_SHIP_MODULES)


# =====================================================================================
# Phase 1 batch 1b — PROHIBITED_COLUMN_TERMS mechanism, proven to fire (X-10), not merely
# present. NEVER touches Base.metadata / EXPECTED_TABLES -- uses a throwaway
# sqlalchemy.MetaData()/Table so test_exact_authorized_model_table_set_and_no_scientific_columns
# above stays byte-identical and its exact-equality assertion is never at risk.
# =====================================================================================

# Phase 3a: the 13 real collisions, derived term-by-term against PROHIBITED_COLUMN_TERMS from
# the ten new C tables (Phase 3a work order R-B). Two classes, named per pair below:
#   CARRIES-REAL-CONTENT -- a private column legitimately holding scientific content, same
#     reasoning as AUTHORIZED_ANSWER_BEARING_COLUMNS's two B entries.
#   FALSE-POSITIVE-NAME -- the term matches the column NAME but the column's value domain
#     (enforced by a CHECK constraint) never actually contains that kind of content.
AUTHORIZED_C_COLUMN_EXCEPTIONS: frozenset[tuple[str, str]] = frozenset(
    {
        # FALSE-POSITIVE-NAME (R-C): domain is exactly ('same_session_fresh',
        # 'unavailable_fallback'), enforced by ck_c_sessions_mastery_context_mode /
        # ck_c_task_opportunities_mastery_context_mode -- never a mastery scalar.
        ("c_sessions", "mastery_context_mode"),
        ("c_task_opportunities", "mastery_context_mode"),
        # CARRIES-REAL-CONTENT (R-D): SelectionResult's own returned provenance for the governed
        # clamp(round(1 + 4 x mastery), 1, 5) initial-difficulty decision (C-17) -- C auditing
        # its own reviewed calculation, not re-storing B's contract.
        ("c_task_opportunities", "mastery_selected_skill"),
        # CARRIES-REAL-CONTENT: the private, never-public correct answer (mirrors B's
        # AUTHORIZED_ANSWER_BEARING_COLUMNS reasoning exactly).
        ("c_task_instances", "correct_answer_payload"),
        # CARRIES-REAL-CONTENT: not named by v3.0 Section 8 -- found by this batch's own
        # term-by-term derivation (R-B). "correctness_function_id" contains "correct".
        ("c_task_instances", "correctness_function_id"),
        ("c_task_opportunity_summaries", "correct_task"),
        ("c_task_opportunity_summaries", "c_answer_changes"),
        ("c_task_opportunity_summaries", "task_latency_sec"),
        ("c_task_opportunity_summaries", "first_attempt_correct"),
        ("c_task_opportunity_summaries", "final_attempt_correct"),
        ("c_session_aggregate_results", "correct_task_count"),
        ("c_session_aggregate_results", "c_mean_game_task_latency_sec"),
        ("c_session_aggregate_results", "c_median_game_task_latency_sec"),
        # CARRIES-REAL-SCIENTIFIC-CONTENT (R-H): name-identical to
        # component_c_generator.scaffolds.ladder.ScaffoldDecisionContext's
        # consecutive_incorrect_current_task field -- the substring match ("incorrect" contains
        # "correct") is incidental, but the semantics are not: this is a count of incorrect
        # attempts, i.e. correctness-derived learner data, same class as correct_task /
        # first_attempt_correct / final_attempt_correct above. Renaming it to dodge the guard
        # would break parity with the governed scaffold-decision contract (R-H, extending R-B/G9).
        # Do NOT reuse mastery_context_mode's false-positive-name justification for this entry.
        ("c_scaffold_events", "consecutive_incorrect_current_task"),
    }
)


def _offending_columns(tables, prohibited_terms, authorized_exceptions) -> set[tuple[str, str]]:
    """Same offender-derivation LOGIC as
    test_exact_authorized_model_table_set_and_no_scientific_columns's inline check above --
    written as a standalone, independently-callable function so it can be run against a
    throwaway MetaData/Table without touching that test's own code or Base.metadata."""
    return {
        (table.name, column.name)
        for table in tables
        for column in table.columns
        if any(term in column.name.lower() for term in prohibited_terms)
        and (table.name, column.name) not in authorized_exceptions
    }


def test_prohibited_column_terms_mechanism_fires_on_synthetic_metadata() -> None:
    """SIGNAL: against a THROWAWAY sqlalchemy.MetaData()/Table (never Base.metadata), a
    deliberately offending column name (`mastery_score`) is flagged, and a SIBLING column that
    ALSO contains a prohibited term (`mastery_baseline_ok`) but is on the allow-list is
    correctly exempted -- proving both halves of the mechanism (detection AND exemption) fire
    against a real SQLAlchemy structure, not merely that an empty allow-list vacuously passes
    against zero C tables. Would FAIL if the offender-derivation logic stopped matching a
    genuinely prohibited term, or if it flagged an allow-listed column anyway."""
    synthetic_metadata = MetaData()
    Table(
        "c_synthetic_test_table",
        synthetic_metadata,
        Column("id", Integer, primary_key=True),
        Column("mastery_score", String),
        Column("mastery_baseline_ok", String),
    )
    synthetic_exceptions = {("c_synthetic_test_table", "mastery_baseline_ok")}

    offenders = _offending_columns(
        synthetic_metadata.tables.values(), PROHIBITED_COLUMN_TERMS, synthetic_exceptions
    )

    assert offenders == {("c_synthetic_test_table", "mastery_score")}
    assert set(Base.metadata.tables) == EXPECTED_TABLES  # untouched by the synthetic metadata above


def test_prohibited_column_terms_allow_list_matches_the_14_computed_pairs() -> None:
    """SIGNAL: AUTHORIZED_C_COLUMN_EXCEPTIONS is EXACTLY the C-side collision set COMPUTED live
    from real Base.metadata against the real PROHIBITED_COLUMN_TERMS -- not a hand-maintained
    list trusted on its own. R-I (Phase 3a UNBLOCK ruling): the 13-pair hand derivation missed
    ("c_scaffold_events", "consecutive_incorrect_current_task"), found only when the guard ran
    against real metadata. The fix is to compute the collision set from source every time this
    test runs and compare AUTHORIZED_C_COLUMN_EXCEPTIONS against it -- never to hand-maintain the
    count alone. Would FAIL if a future column collides and nobody adds its allow-list entry, or
    if an entry is removed/added without a matching real collision, or if the computed set drifts
    from 14 for any reason."""
    computed_c_collisions = {
        (table.name, column.name)
        for table in Base.metadata.tables.values()
        for column in table.columns
        if any(term in column.name.lower() for term in PROHIBITED_COLUMN_TERMS)
        and (table.name, column.name) not in AUTHORIZED_ANSWER_BEARING_COLUMNS
    }
    assert computed_c_collisions == AUTHORIZED_C_COLUMN_EXCEPTIONS
    assert len(AUTHORIZED_C_COLUMN_EXCEPTIONS) == 14
    assert ("c_task_opportunity_summaries", "consecutive_error_max_within_task") not in (
        AUTHORIZED_C_COLUMN_EXCEPTIONS
    ), "this column does not collide (R-B) and must never need an exemption"


# =====================================================================================
# Phase 1 batch 1b — seed-derivation symbols must never be reachable from the adapter (C3).
# AST-based: a text grep would be defeated by this file's own module docstring, which names
# these four symbols in prose to explain why they are absent.
# =====================================================================================

_PROHIBITED_SEED_DERIVATION_SYMBOLS = frozenset(
    {"derive_child_lineage", "SeedManager", "rng_from", "SUBSTREAMS"}
)


def test_adapter_references_no_seed_derivation_symbol() -> None:
    """SIGNAL: parses app/infrastructure/live_engine_c/adapter.py's AST and asserts none of
    derive_child_lineage, SeedManager, rng_from, SUBSTREAMS appears as an imported name, an
    attribute access, or a bare Name reference anywhere in the file -- checked via
    ast.Import/ast.ImportFrom/ast.Attribute/ast.Name nodes, never a text search, so the
    adapter's own module docstring (which names these four symbols in prose to explain their
    absence) cannot trip this test. Would FAIL if a future edit added
    `from component_c_generator.seeds import derive_child_lineage` (or called
    `seeds.SeedManager(...)`/`seeds.rng_from(...)`/referenced `seeds.SUBSTREAMS`) to work around
    the seed-lineage gap instead of waiting for an explicit future authorization (G3)."""
    adapter_path = _ALLOWED_C_ADAPTER_PATH
    tree = ast.parse(adapter_path.read_text(encoding="utf-8"), filename=str(adapter_path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            found |= {alias.name for alias in node.names} & _PROHIBITED_SEED_DERIVATION_SYMBOLS
        elif isinstance(node, ast.Import):
            found |= {
                alias.name.split(".")[-1] for alias in node.names
            } & _PROHIBITED_SEED_DERIVATION_SYMBOLS
        elif isinstance(node, ast.Attribute) and node.attr in _PROHIBITED_SEED_DERIVATION_SYMBOLS:
            found.add(node.attr)
        elif isinstance(node, ast.Name) and node.id in _PROHIBITED_SEED_DERIVATION_SYMBOLS:
            found.add(node.id)
    assert not found, found


# =====================================================================================
# Phase 1 batch 1b — no domain config field may carry a default (G1: a default on a config
# field is a recorded threshold). Asserted structurally, not reviewed.
# =====================================================================================

_DOMAIN_CONFIG_TYPES = (
    AggregationConfig,
    EvidenceWindowConfig,
    GenerationConfig,
    PolicyConfig,
    RecoveryConfig,
    SafetyConfig,
    ScaffoldConfig,
    SelectionConfig,
    TemplateGenerationParams,
)


def test_no_domain_config_field_carries_a_default() -> None:
    """SIGNAL: every field on every Component C domain config dataclass has no default value
    and no default_factory, asserted via dataclasses.fields() -- not a style review. The pinned
    package carries zero defaults across all eight top-level configs (independently verified);
    a default here would be this codebase recording an unapproved scientific threshold, weight,
    window, or cap (G1), since Component C is PROPOSED, not approved. Would FAIL the moment a
    future edit added so much as one `field: float = 0.8`-style default to any of these nine
    dataclasses."""
    for config_type in _DOMAIN_CONFIG_TYPES:
        for config_field in dataclasses.fields(config_type):
            assert config_field.default is dataclasses.MISSING, (
                config_type.__name__, config_field.name,
            )
            assert config_field.default_factory is dataclasses.MISSING, (
                config_type.__name__, config_field.name,
            )
