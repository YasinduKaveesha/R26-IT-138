"""Static guards for the BE2 Limited authorization boundary."""

import ast
import re
from pathlib import Path

from app.infrastructure.persistence_models import AUTHORIZED_TABLES, Base
from app.main import app


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
}
BE2_BASE_TABLES = EXPECTED_TABLES - {
    "teacher_profiles", "classrooms", "classroom_invites", "classroom_memberships"
}
PROHIBITED_COLUMN_TERMS = {
    "mastery", "bkt", "guess_guard", "certif", "sequenc", "hint", "answer",
    "correct", "error_class", "population", "dd_subtype", "true_mastery",
    "simulated", "latency", "off_day", "random_effect", "experiment",
}


def test_exact_authorized_model_table_set_and_no_scientific_columns() -> None:
    assert AUTHORIZED_TABLES == EXPECTED_TABLES
    assert set(Base.metadata.tables) == EXPECTED_TABLES
    columns = {column.name.lower() for table in Base.metadata.tables.values() for column in table.columns}
    assert not {name for name in columns if any(term in name for term in PROHIBITED_COLUMN_TERMS)}


def test_no_new_api_route_or_lifecycle_service() -> None:
    routes = {
        (path, tuple(sorted(method.upper() for method in operations)))
        for path, operations in app.openapi()["paths"].items()
    }
    assert routes == {
        ("/health/live", ("GET",)),
        ("/health/ready", ("GET",)),
        ("/api/v1/me", ("GET",)),
        ("/api/v1/teacher/profile", ("GET", "POST")),
        ("/api/v1/learner/profile", ("GET", "POST")),
        ("/api/v1/classrooms", ("GET", "POST")),
        ("/api/v1/classrooms/{classroom_id}", ("GET",)),
        ("/api/v1/teacher/profile", ("GET", "POST")),
        ("/api/v1/learner/profile", ("GET", "POST")),
        ("/api/v1/classrooms", ("GET", "POST")),
        ("/api/v1/classrooms/{classroom_id}", ("GET",)),
    }
    assert not any(Path("app").rglob("*session*service*.py"))


def test_no_yass_research_or_scientific_imports() -> None:
    prohibited_import_roots = {
        "component_b_generator", "yass", "bkt", "sequencing", "certification",
        "guess_guard", "pipeline", "pilot",
    }
    for path in Path("app").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name.split(".")[0].lower() for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported = {node.module.split(".")[0].lower()}
            else:
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
    paths = set(app.openapi()["paths"])
    assert not any("invite" in path or "membership" in path for path in paths)
    assert not any("session" in path or "attempt" in path or "hint" in path for path in paths)


def test_profile_classroom_migration_and_routes_stay_within_authorization() -> None:
    migration = Path("migrations/versions/20260722_0004_profile_classroom_foundations.py").read_text(encoding="utf-8")
    assert set(re.findall(r'op\.create_table\(\s*"([^"]+)"', migration)) == {"teacher_profiles", "classrooms", "classroom_invites", "classroom_memberships"}
    lowered = migration.lower()
    assert "learner_profiles" not in lowered
    assert "bulk_insert" not in lowered
    assert "component_b_generator" not in lowered
    assert "yass" not in lowered
    paths = set(app.openapi()["paths"])
    assert not any("invite" in path or "membership" in path for path in paths)
    assert not any("session" in path or "attempt" in path or "hint" in path for path in paths)
