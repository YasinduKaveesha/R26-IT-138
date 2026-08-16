"""Neutral BE2 persistence facts authorized by the governance boundary.

These models intentionally contain no lifecycle methods, scientific state, learner
responses, or synthetic-generator fields.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    false,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


SOURCE_CLASSES = ("REAL", "SYNTHETIC", "IMPORTED", "TEST")
SESSION_STATES = (
    "starting", "active", "completing", "completed", "abandoned", "expired", "technical_failed"
)


class Base(DeclarativeBase):
    """Metadata root for the eight authorized BE2 tables."""


class ProvenanceMixin:
    """Mandatory neutral provenance and audit metadata."""

    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="RESTRICT"), nullable=True
    )
    system_actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    operation_or_event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    before_reference_or_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    after_reference_or_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_class: Mapped[str] = mapped_column(String(16), nullable=False)
    source_system: Mapped[str] = mapped_column(String(128), nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    environment: Mapped[str] = mapped_column(String(32), nullable=False)
    schema_revision: Mapped[str] = mapped_column(String(64), nullable=False)
    approval_evidence_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    @staticmethod
    def provenance_constraints(prefix: str) -> tuple[CheckConstraint, ...]:
        return (
            CheckConstraint(
                "source_class IN ('REAL', 'SYNTHETIC', 'IMPORTED', 'TEST')",
                name=f"ck_{prefix}_source_class",
            ),
            CheckConstraint(
                "(actor_user_id IS NOT NULL) <> (system_actor IS NOT NULL)",
                name=f"ck_{prefix}_actor_exactly_one",
            ),
            CheckConstraint(
                "environment <> '' AND source_system <> '' AND request_id <> ''",
                name=f"ck_{prefix}_required_provenance_nonblank",
            ),
        )


class AppUser(ProvenanceMixin, Base):
    __tablename__ = "app_users"
    __table_args__ = (
        UniqueConstraint("supabase_subject", name="uq_app_users_supabase_subject"),
        CheckConstraint("supabase_subject <> ''", name="ck_app_users_subject_nonblank"),
        CheckConstraint("status <> ''", name="ck_app_users_status_nonblank"),
        CheckConstraint(
            "profile_type IS NULL OR profile_type IN ('LEARNER', 'TEACHER')",
            name="ck_app_users_profile_type",
        ),
        *ProvenanceMixin.provenance_constraints("app_users"),
    )

    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    supabase_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    profile_type: Mapped[str | None] = mapped_column(String(16), nullable=True)


class Learner(ProvenanceMixin, Base):
    __tablename__ = "b_learners"
    __table_args__ = (
        CheckConstraint("grade IS NULL OR grade IN (2, 3)", name="ck_b_learners_grade"),
        CheckConstraint("status <> ''", name="ck_b_learners_status_nonblank"),
        CheckConstraint("name IS NULL OR btrim(name) <> ''", name="ck_b_learners_name_nonblank"),
        *ProvenanceMixin.provenance_constraints("b_learners"),
    )

    learner_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    grade: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)


class AppUserLearnerLink(ProvenanceMixin, Base):
    __tablename__ = "app_user_learner_links"
    __table_args__ = (
        UniqueConstraint("user_id", "learner_id", name="uq_app_user_learner_links_pair"),
        UniqueConstraint("user_id", name="uq_app_user_learner_links_user"),
        UniqueConstraint("learner_id", name="uq_app_user_learner_links_learner"),
        *ProvenanceMixin.provenance_constraints("app_user_learner_links"),
    )

    link_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="RESTRICT"), nullable=False
    )
    learner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_learners.learner_id", ondelete="RESTRICT"), nullable=False
    )


class RuntimeBundleRecord(ProvenanceMixin, Base):
    __tablename__ = "b_runtime_bundle_records"
    __table_args__ = (
        UniqueConstraint("bundle_version", name="uq_b_runtime_bundle_records_version"),
        UniqueConstraint("manifest_checksum", name="uq_b_runtime_bundle_records_checksum"),
        CheckConstraint("manifest_checksum ~ '^[0-9a-f]{64}$'", name="ck_b_runtime_bundle_records_checksum"),
        CheckConstraint(
            "publication_state IN ('DRAFT', 'PUBLISHED', 'RETIRED')",
            name="ck_b_runtime_bundle_records_publication_state",
        ),
        CheckConstraint(
            "publication_state <> 'PUBLISHED' OR immutable_after_publication",
            name="ck_b_runtime_bundle_records_published_immutable",
        ),
        *ProvenanceMixin.provenance_constraints("b_runtime_bundle_records"),
    )

    runtime_bundle_record_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bundle_version: Mapped[str] = mapped_column(String(128), nullable=False)
    manifest_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    publication_state: Mapped[str] = mapped_column(String(16), nullable=False)
    approval_status: Mapped[str] = mapped_column(String(64), nullable=False)
    immutable_after_publication: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())


class SessionRecord(ProvenanceMixin, Base):
    __tablename__ = "b_sessions"
    __table_args__ = (
        CheckConstraint(
            "state IN ('starting', 'active', 'completing', 'completed', 'abandoned', 'expired', 'technical_failed')",
            name="ck_b_sessions_state",
        ),
        CheckConstraint("row_version >= 0", name="ck_b_sessions_row_version"),
        CheckConstraint(
            "state <> 'active' OR runtime_bundle_record_id IS NOT NULL",
            name="ck_b_sessions_active_bundle_required",
        ),
        Index(
            "uq_b_sessions_one_starting_or_active_per_learner",
            "learner_id",
            unique=True,
            postgresql_where=text("state IN ('starting', 'active')"),
        ),
        *ProvenanceMixin.provenance_constraints("b_sessions"),
    )

    session_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    learner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_learners.learner_id", ondelete="RESTRICT"), nullable=False
    )
    runtime_bundle_record_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("b_runtime_bundle_records.runtime_bundle_record_id", ondelete="RESTRICT"),
        nullable=True,
    )
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    expires_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))


class SessionEvent(ProvenanceMixin, Base):
    __tablename__ = "b_session_events"
    __table_args__ = (*ProvenanceMixin.provenance_constraints("b_session_events"),)

    session_event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_sessions.session_id", ondelete="RESTRICT"), nullable=False
    )


class IdempotencyRecord(ProvenanceMixin, Base):
    __tablename__ = "b_idempotency_records"
    __table_args__ = (
        UniqueConstraint(
            "actor_user_id", "http_method", "operation_identifier", "idempotency_key",
            name="uq_b_idempotency_records_scope",
        ),
        CheckConstraint("actor_user_id IS NOT NULL", name="ck_b_idempotency_records_actor_required"),
        CheckConstraint("processing_status <> ''", name="ck_b_idempotency_records_status_nonblank"),
        CheckConstraint("request_fingerprint ~ '^[0-9a-f]{64}$'", name="ck_b_idempotency_records_fingerprint"),
        CheckConstraint("expires_at_utc > created_at_utc", name="ck_b_idempotency_records_expiry"),
        *ProvenanceMixin.provenance_constraints("b_idempotency_records"),
    )

    idempotency_record_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    http_method: Mapped[str] = mapped_column(String(16), nullable=False)
    operation_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    processing_status: Mapped[str] = mapped_column(String(32), nullable=False)
    canonical_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    response_status: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    expires_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditEvent(ProvenanceMixin, Base):
    __tablename__ = "b_audit_events"
    __table_args__ = (*ProvenanceMixin.provenance_constraints("b_audit_events"),)

    audit_event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)


class TeacherProfile(ProvenanceMixin, Base):
    __tablename__ = "teacher_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_teacher_profiles_user"),
        CheckConstraint("btrim(name) <> ''", name="ck_teacher_profiles_name_nonblank"),
        *ProvenanceMixin.provenance_constraints("teacher_profiles"),
    )

    teacher_profile_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class Classroom(ProvenanceMixin, Base):
    __tablename__ = "classrooms"
    __table_args__ = (
        CheckConstraint("grade IN ('GRADE_2', 'GRADE_3')", name="ck_classrooms_grade"),
        CheckConstraint("name IS NULL OR btrim(name) <> ''", name="ck_classrooms_name_nonblank"),
        Index("uq_classrooms_teacher_normalized_name", "teacher_profile_id", func.lower(func.btrim(text("name"))), unique=True, postgresql_where=text("name IS NOT NULL")),
        CheckConstraint("row_version >= 0", name="ck_classrooms_row_version"),
        *ProvenanceMixin.provenance_constraints("classrooms"),
    )

    classroom_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    teacher_profile_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("teacher_profiles.teacher_profile_id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    grade: Mapped[str] = mapped_column(String(16), nullable=False)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))


class ClassroomInvite(ProvenanceMixin, Base):
    __tablename__ = "classroom_invites"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_classroom_invites_token_hash"),
        CheckConstraint("token_hash ~ '^[0-9a-f]{64}$'", name="ck_classroom_invites_token_hash"),
        CheckConstraint("row_version >= 0", name="ck_classroom_invites_row_version"),
        *ProvenanceMixin.provenance_constraints("classroom_invites"),
    )

    classroom_invite_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    classroom_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("classrooms.classroom_id", ondelete="RESTRICT"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="RESTRICT"), nullable=False)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))


class ClassroomMembership(ProvenanceMixin, Base):
    __tablename__ = "classroom_memberships"
    __table_args__ = (
        UniqueConstraint("classroom_id", "learner_id", name="uq_classroom_memberships_pair"),
        CheckConstraint("state IN ('PENDING', 'APPROVED', 'REJECTED')", name="ck_classroom_memberships_state"),
        CheckConstraint("(state = 'PENDING' AND decided_at_utc IS NULL AND decided_by_user_id IS NULL) OR (state IN ('APPROVED', 'REJECTED') AND decided_at_utc IS NOT NULL AND decided_by_user_id IS NOT NULL)", name="ck_classroom_memberships_decision"),
        CheckConstraint("row_version >= 0", name="ck_classroom_memberships_row_version"),
        Index(
            "uq_classroom_memberships_one_approved_per_learner",
            "learner_id",
            unique=True,
            postgresql_where=text("state = 'APPROVED'"),
        ),
        *ProvenanceMixin.provenance_constraints("classroom_memberships"),
    )

    classroom_membership_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    classroom_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("classrooms.classroom_id", ondelete="RESTRICT"), nullable=False)
    learner_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("b_learners.learner_id", ondelete="RESTRICT"), nullable=False)
    classroom_invite_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("classroom_invites.classroom_invite_id", ondelete="RESTRICT"), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    requested_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="RESTRICT"), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))


class ItemOpportunityRecord(ProvenanceMixin, Base):
    """BE4a (BEplan §9 BE4.1): one live-loop opportunity per row. PRIVATE table — the
    ``selection_provenance`` column never appears in any public DTO or log; see
    ``app.domain.b_opportunity``."""

    __tablename__ = "b_item_opportunities"
    __table_args__ = (
        CheckConstraint("state IN ('OPEN', 'CLOSED')", name="ck_b_item_opportunities_state"),
        CheckConstraint("row_version >= 0", name="ck_b_item_opportunities_row_version"),
        CheckConstraint(
            "timeout_deadline_utc > created_at_utc", name="ck_b_item_opportunities_timeout_after_created"
        ),
        Index(
            "uq_b_item_opportunities_one_open_per_session",
            "session_id",
            unique=True,
            postgresql_where=text("state = 'OPEN'"),
        ),
        *ProvenanceMixin.provenance_constraints("b_item_opportunities"),
    )

    item_opportunity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_sessions.session_id", ondelete="RESTRICT"), nullable=False
    )
    learner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_learners.learner_id", ondelete="RESTRICT"), nullable=False
    )
    skill_id: Mapped[str] = mapped_column(String(128), nullable=False)
    item_template_id: Mapped[str] = mapped_column(String(128), nullable=False)
    opportunity_index: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    presented_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timeout_deadline_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    selection_provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))


class TaskInstanceRecord(ProvenanceMixin, Base):
    """BE4a (BEplan §9 BE4.1): the constructed task for one opportunity, split into a SAFE
    presentation subset (prompt/presented_choices — computed once at creation using the same
    allow-list logic as BE3c's ``project_to_public``) and PRIVATE columns that never leave this
    table. This batch creates the schema only; BE4b populates rows via the adapter."""

    __tablename__ = "b_task_instances"
    __table_args__ = (
        UniqueConstraint("item_opportunity_id", name="uq_b_task_instances_opportunity"),
        CheckConstraint("grade IN (2, 3)", name="ck_b_task_instances_grade"),
        *ProvenanceMixin.provenance_constraints("b_task_instances"),
    )

    task_instance_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    item_opportunity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_item_opportunities.item_opportunity_id", ondelete="RESTRICT"), nullable=False
    )
    item_template_id: Mapped[str] = mapped_column(String(128), nullable=False)
    skill_id: Mapped[str] = mapped_column(String(128), nullable=False)
    grade: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    difficulty_level: Mapped[str] = mapped_column(String(64), nullable=False)
    representation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    response_format: Mapped[str] = mapped_column(String(64), nullable=False)
    # SAFE presentation subset (BE3c allow-list) — the only columns a public DTO may read.
    prompt: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    presented_choices: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    # PRIVATE — never read by any public-DTO projection or structured log.
    correct_answer: Mapped[str] = mapped_column(String(255), nullable=False)
    allowed_equivalent_answers: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    distractor_candidates: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    distractor_rule_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    generated_operands: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    generation_seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    applied_guard_ids: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    catalogue_version: Mapped[str] = mapped_column(String(128), nullable=False)
    catalogue_checksum: Mapped[str] = mapped_column(String(64), nullable=False)


class PresentationTokenRecord(ProvenanceMixin, Base):
    """BE4a (BEplan §9 BE4.1): an opaque, short-lived presentation token bound to
    (session, opportunity, learner, runtime bundle). Only the SHA-256 hash of the token is
    stored, matching the ``classroom_invites.token_hash`` convention — the raw token is returned
    to the caller exactly once, at issuance."""

    __tablename__ = "b_presentation_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_b_presentation_tokens_token_hash"),
        CheckConstraint("token_hash ~ '^[0-9a-f]{64}$'", name="ck_b_presentation_tokens_token_hash"),
        CheckConstraint("expires_at_utc > issued_at_utc", name="ck_b_presentation_tokens_expiry"),
        *ProvenanceMixin.provenance_constraints("b_presentation_tokens"),
    )

    presentation_token_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_sessions.session_id", ondelete="RESTRICT"), nullable=False
    )
    item_opportunity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_item_opportunities.item_opportunity_id", ondelete="RESTRICT"), nullable=False
    )
    learner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_learners.learner_id", ondelete="RESTRICT"), nullable=False
    )
    runtime_bundle_record_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("b_runtime_bundle_records.runtime_bundle_record_id", ondelete="RESTRICT"),
        nullable=False,
    )
    issued_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LearnerSkillStateRecord(ProvenanceMixin, Base):
    """BE4b (BEplan §9 BE4.2): one row per (learner, skill) — the current P(L) mastery estimate
    and observation count. PRIVATE table. BE4b only reads and initializes (from the pinned
    bundle's TEST-fixture P(L0) priors); BE4c owns updates after the first real attempt. No
    cross-skill transfer: every row is independent."""

    __tablename__ = "b_learner_skill_states"
    __table_args__ = (
        UniqueConstraint("learner_id", "skill_id", name="uq_b_learner_skill_states_pair"),
        CheckConstraint("p_l >= 0.0 AND p_l <= 1.0", name="ck_b_learner_skill_states_p_l_bounded"),
        CheckConstraint("observation_count >= 0", name="ck_b_learner_skill_states_observation_count"),
        *ProvenanceMixin.provenance_constraints("b_learner_skill_states"),
    )

    learner_skill_state_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    learner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_learners.learner_id", ondelete="RESTRICT"), nullable=False
    )
    skill_id: Mapped[str] = mapped_column(String(128), nullable=False)
    p_l: Mapped[float] = mapped_column(Float, nullable=False)
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))


class AttemptRecord(ProvenanceMixin, Base):
    """BE4c (BEplan §9 BE4.3): one row per submitted attempt or governed timeout event on an
    opportunity. PRIVATE table. ``attempt_index`` is derived server-side under a row lock on the
    parent opportunity and is unique per opportunity. ``submitted_value`` is the learner's raw
    submission (never the accepted-answer set); ``response_matched`` is the server-computed
    outcome for ``RESPONSE`` events only (``NULL`` for ``TIMEOUT``). ``client_elapsed_ms`` is
    telemetry only — never used for correctness or BKT.

    BF-2 (migration 20260801_0001): ``submitted_value`` is NOT NULL unconditionally, including on
    ``TIMEOUT`` — a late-but-real answer is persisted (never scored: ``response_matched`` stays
    NULL for ``TIMEOUT``, exactly as before). Previously the constraint below required
    ``submitted_value IS NULL`` on timeout, which meant the answer was discarded and unrecoverable
    the moment the request completed."""

    __tablename__ = "b_attempts"
    __table_args__ = (
        UniqueConstraint("item_opportunity_id", "attempt_index", name="uq_b_attempts_opportunity_index"),
        CheckConstraint("event_kind IN ('RESPONSE', 'TIMEOUT')", name="ck_b_attempts_event_kind"),
        CheckConstraint("attempt_index >= 1", name="ck_b_attempts_attempt_index_positive"),
        CheckConstraint(
            "submitted_value IS NOT NULL "
            "AND ((event_kind = 'RESPONSE' AND response_matched IS NOT NULL) "
            "OR (event_kind = 'TIMEOUT' AND response_matched IS NULL))",
            name="ck_b_attempts_response_matched_consistency",
        ),
        CheckConstraint("client_elapsed_ms IS NULL OR client_elapsed_ms >= 0", name="ck_b_attempts_client_elapsed_ms_nonnegative"),
        *ProvenanceMixin.provenance_constraints("b_attempts"),
    )

    attempt_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    item_opportunity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_item_opportunities.item_opportunity_id", ondelete="RESTRICT"), nullable=False
    )
    learner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_learners.learner_id", ondelete="RESTRICT"), nullable=False
    )
    attempt_index: Mapped[int] = mapped_column(Integer, nullable=False)
    event_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    submitted_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    response_matched: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    client_elapsed_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    server_submitted_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SkillStateTransitionRecord(ProvenanceMixin, Base):
    """BE4c (BEplan §9 BE4.4): the immutable first-attempt-only BKT observation + mastery
    transition. PRIVATE table. ``uq_b_skill_state_transitions_opportunity`` is simultaneously the
    DB-level claim on the unique first-attempt observation for an opportunity and the transition
    row itself — a concurrent second claim for the same opportunity fails this unique index. No
    application code path ever updates or deletes a row in this table."""

    __tablename__ = "b_skill_state_transitions"
    __table_args__ = (
        UniqueConstraint("item_opportunity_id", name="uq_b_skill_state_transitions_opportunity"),
        UniqueConstraint("attempt_id", name="uq_b_skill_state_transitions_attempt"),
        CheckConstraint("p_l_before >= 0.0 AND p_l_before <= 1.0", name="ck_b_skill_state_transitions_p_l_before_bounded"),
        CheckConstraint(
            "predicted_probability >= 0.0 AND predicted_probability <= 1.0",
            name="ck_b_skill_state_transitions_predicted_probability_bounded",
        ),
        CheckConstraint("posterior_p_l >= 0.0 AND posterior_p_l <= 1.0", name="ck_b_skill_state_transitions_posterior_p_l_bounded"),
        CheckConstraint("p_l_after >= 0.0 AND p_l_after <= 1.0", name="ck_b_skill_state_transitions_p_l_after_bounded"),
        *ProvenanceMixin.provenance_constraints("b_skill_state_transitions"),
    )

    skill_state_transition_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    learner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_learners.learner_id", ondelete="RESTRICT"), nullable=False
    )
    skill_id: Mapped[str] = mapped_column(String(128), nullable=False)
    item_opportunity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_item_opportunities.item_opportunity_id", ondelete="RESTRICT"), nullable=False
    )
    attempt_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_attempts.attempt_id", ondelete="RESTRICT"), nullable=False
    )
    response_matched: Mapped[bool] = mapped_column(Boolean, nullable=False)
    p_l_before: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_probability: Mapped[float] = mapped_column(Float, nullable=False)
    posterior_p_l: Mapped[float] = mapped_column(Float, nullable=False)
    p_l_after: Mapped[float] = mapped_column(Float, nullable=False)


class HintEventRecord(ProvenanceMixin, Base):
    """BE4d (BEplan §9 BE4.5): one row per governed L1/L2/L3 assist request on an opportunity.
    PRIVATE table, SEPARATE from ``b_attempts``/``b_skill_state_transitions`` — a hint request is
    never a mastery/BKT observation and this table is never joined into any BKT computation.
    Column names avoid every ``PROHIBITED_COLUMN_TERMS`` entry (see
    ``tests/test_be2_architecture_guards.py``): the governed hint level is spelled
    ``assist_level``, not ``hint_level``. Only the catalogue reconstruction key
    (``content_id`` + ``catalogue_version`` + ``catalogue_checksum``) is persisted — never the
    hint text itself, which is always re-fetched from the governed catalogue via
    ``LiveEngineAdapter.get_hint`` at request time."""

    __tablename__ = "b_hint_events"
    __table_args__ = (
        UniqueConstraint("item_opportunity_id", "assist_level", name="uq_b_hint_events_opportunity_level"),
        CheckConstraint("assist_level >= 1 AND assist_level <= 3", name="ck_b_hint_events_assist_level_bounded"),
        *ProvenanceMixin.provenance_constraints("b_hint_events"),
    )

    assist_event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    item_opportunity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_item_opportunities.item_opportunity_id", ondelete="RESTRICT"), nullable=False
    )
    learner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_learners.learner_id", ondelete="RESTRICT"), nullable=False
    )
    assist_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    content_id: Mapped[str] = mapped_column(String(255), nullable=False)
    catalogue_version: Mapped[str] = mapped_column(String(128), nullable=False)
    catalogue_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SessionAggregateResultRecord(ProvenanceMixin, Base):
    """BE4e (BEplan §9 BE4.6): one immutable row per completed session — session-level aggregate
    statistics computed via ``LiveEngineAdapter.aggregate_session`` from the session's own
    attempts/hints/first-attempt outcomes. PRIVATE table: never read by any public-DTO projection
    (see ``app.domain.b_completion``). Column names avoid every ``PROHIBITED_COLUMN_TERMS`` entry
    (``outcome_pattern_distribution`` not ``error_class_distribution``,
    ``assisted_opportunity_count`` not ``hint_bearing_opportunities``). No application code path
    ever updates or deletes a row here."""

    __tablename__ = "b_session_aggregate_results"
    __table_args__ = (
        UniqueConstraint("session_id", name="uq_b_session_aggregate_results_session"),
        CheckConstraint(
            "first_attempt_match_rate IS NULL OR (first_attempt_match_rate >= 0.0 AND first_attempt_match_rate <= 1.0)",
            name="ck_b_session_aggregate_results_match_rate_bounded",
        ),
        CheckConstraint(
            "completion_rate IS NULL OR (completion_rate >= 0.0 AND completion_rate <= 1.0)",
            name="ck_b_session_aggregate_results_completion_rate_bounded",
        ),
        *ProvenanceMixin.provenance_constraints("b_session_aggregate_results"),
    )

    session_aggregate_result_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_sessions.session_id", ondelete="RESTRICT"), nullable=False
    )
    learner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_learners.learner_id", ondelete="RESTRICT"), nullable=False
    )
    opportunity_count: Mapped[int] = mapped_column(Integer, nullable=False)
    first_attempt_match_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    completion_count: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_retry_count: Mapped[int] = mapped_column(Integer, nullable=False)
    assisted_opportunity_count: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_mean_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    response_time_median_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    response_time_std_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome_pattern_distribution: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    skill_ids_practiced: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    completion_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)


class SkillCertificationResultRecord(ProvenanceMixin, Base):
    """BE4e (BEplan §9 BE4.6): one immutable row per (session, skill) roll-up — the TEST-fixture
    plausibility-check and certification decision from ``LiveEngineAdapter.plausibility_floor``/
    ``evaluate``/``certify_skill``. PRIVATE table; column names avoid every
    ``PROHIBITED_COLUMN_TERMS`` entry (``skill_estimate`` not ``mastery``/``p_l``,
    ``threshold_met_flag`` not ``certified_flag``, ``plausibility_status`` not
    ``guess_guard_status``, ``first_attempt_match_count`` not ``first_attempt_correct_count``).
    GATE-B deferred: theta_B and the plausibility numerics behind this row are the
    TEST_FIXTURE_ONLY engineering config, never an approved value; never exposed through any
    public DTO (see ``app.domain.b_completion``)."""

    __tablename__ = "b_skill_certification_results"
    __table_args__ = (
        UniqueConstraint("session_id", "skill_id", name="uq_b_skill_certification_results_session_skill"),
        CheckConstraint(
            "skill_estimate IS NULL OR (skill_estimate >= 0.0 AND skill_estimate <= 1.0)",
            name="ck_b_skill_certification_results_skill_estimate_bounded",
        ),
        CheckConstraint(
            "plausibility_status IS NULL OR plausibility_status IN "
            "('NOT_TRIGGERED', 'TRIGGERED', 'INSUFFICIENT_EVIDENCE')",
            name="ck_b_skill_certification_results_plausibility_status",
        ),
        *ProvenanceMixin.provenance_constraints("b_skill_certification_results"),
    )

    skill_result_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_sessions.session_id", ondelete="RESTRICT"), nullable=False
    )
    learner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_learners.learner_id", ondelete="RESTRICT"), nullable=False
    )
    skill_id: Mapped[str] = mapped_column(String(128), nullable=False)
    opportunity_count: Mapped[int] = mapped_column(Integer, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False)
    first_attempt_match_count: Mapped[int] = mapped_column(Integer, nullable=False)
    skill_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    plausibility_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    threshold_met_flag: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class CRuntimeBundleRecord(ProvenanceMixin, Base):
    """Component C Phase 2: mirrors ``RuntimeBundleRecord``'s (b_runtime_bundle_records)
    column set and constraint style exactly, pinning Component C's own
    (``prabathi-component-c-live-engine``) runtime-bundle manifests rather than B's. No
    relationship to ``b_runtime_bundle_records`` or any other B table."""

    __tablename__ = "c_runtime_bundle_records"
    __table_args__ = (
        UniqueConstraint("bundle_version", name="uq_c_runtime_bundle_records_version"),
        UniqueConstraint("manifest_checksum", name="uq_c_runtime_bundle_records_checksum"),
        CheckConstraint("manifest_checksum ~ '^[0-9a-f]{64}$'", name="ck_c_runtime_bundle_records_checksum"),
        CheckConstraint(
            "publication_state IN ('DRAFT', 'PUBLISHED', 'RETIRED')",
            name="ck_c_runtime_bundle_records_publication_state",
        ),
        CheckConstraint(
            "publication_state <> 'PUBLISHED' OR immutable_after_publication",
            name="ck_c_runtime_bundle_records_published_immutable",
        ),
        *ProvenanceMixin.provenance_constraints("c_runtime_bundle_records"),
    )

    c_runtime_bundle_record_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    bundle_version: Mapped[str] = mapped_column(String(128), nullable=False)
    manifest_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    publication_state: Mapped[str] = mapped_column(String(16), nullable=False)
    approval_status: Mapped[str] = mapped_column(String(64), nullable=False)
    immutable_after_publication: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())


# =====================================================================================
# Component C Phase 3a — the ten tables (Component_C_Master_Build_Plan_v3.0.md §11 Phase 3).
# Tables only: no cross-row invariant (terminal-event uniqueness, event_index continuity,
# timestamp monotonicity, attempt-count bounds) is enforced here — that is Phase 3b, per the
# owner's scope split (Phase 3a work order, "SCOPE" / "OUT OF SCOPE" sections). Two exceptions
# land in 3a because they are genuinely single-row/single-table, not cross-row: the UNIQUE on
# c_sessions(student_id, intervention_session_id), and the single-row CHECK
# event_timestamp_relative_ms >= 0 on c_gameplay_events — both BUILDER JUDGMENT, ratified as
# "R-E" in the Phase 3a work order ("UNIQUE(student_id, intervention_session_id) on c_sessions
# and the single-row CHECK event_timestamp_relative_ms >= 0 LAND IN 3a under scope item 2.
# Every other invariant in your Q6 table is 3b. Do not build a trigger this phase.").
#
# Every enum-style CHECK below cites its source: either a Literal type verified directly against
# the installed component_c_generator wheel during Phase 1b/3a planning (named per column), or
# an existing structural constant already in this file (SESSION_STATES, the grade-2/3 convention
# already used by RuntimeBundleRecord's B sibling TaskInstanceRecord). No CHECK constraint in
# this block contains an invented numeric threshold (Phase 3a work order, R-G).
# =====================================================================================


class CSessionRecord(ProvenanceMixin, Base):
    """Component C Phase 3a. Session lifecycle, pinned catalogue/config versions,
    ``mastery_context_mode``, ``session_phase`` (Component_C_Master_Build_Plan_v3.0.md §11
    Phase 3 table purpose). ``state`` is left without an enum CHECK deliberately — BUILDER
    JUDGMENT, UNRATIFIED: the exact C session-lifecycle vocabulary is Phase 4's ("session
    lifecycle... modes... cold-start gate") to define; the column exists now so Phase 4 needs no
    migration just to add a foundational session column."""

    __tablename__ = "c_sessions"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "intervention_session_id", name="uq_c_sessions_student_intervention_session"
        ),
        CheckConstraint("session_mode IN ('combined', 'c_only')", name="ck_c_sessions_session_mode"),
        CheckConstraint(
            "session_phase IN ('familiarization', 'mastery_driven', 'c_only')",
            name="ck_c_sessions_session_phase",
        ),
        CheckConstraint(
            "mastery_context_mode IN ('same_session_fresh', 'unavailable_fallback')",
            name="ck_c_sessions_mastery_context_mode",
        ),
        CheckConstraint("grade IN (2, 3)", name="ck_c_sessions_grade"),
        *ProvenanceMixin.provenance_constraints("c_sessions"),
    )

    c_session_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_learners.learner_id", ondelete="RESTRICT"), nullable=False
    )
    intervention_session_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    session_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    session_phase: Mapped[str] = mapped_column(String(32), nullable=False)
    # ALLOW-LISTED (AUTHORIZED_C_COLUMN_EXCEPTIONS) -- false-positive-name class (R-C): contains
    # "mastery" but its domain is exactly the two values in the CHECK above, never a mastery
    # scalar.
    mastery_context_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    catalogue_version: Mapped[str] = mapped_column(String(128), nullable=False)
    catalogue_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    c_runtime_bundle_record_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("c_runtime_bundle_records.c_runtime_bundle_record_id", ondelete="RESTRICT"),
        nullable=False,
    )
    grade: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    global_seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    started_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))


class CTaskOpportunityRecord(ProvenanceMixin, Base):
    """Component C Phase 3a. One row per offered task; selection evidence; terminal result
    (v3.0 §11 Phase 3)."""

    __tablename__ = "c_task_opportunities"
    __table_args__ = (
        CheckConstraint(
            "session_phase IN ('familiarization', 'mastery_driven', 'c_only')",
            name="ck_c_task_opportunities_session_phase",
        ),
        CheckConstraint(
            "mastery_context_mode IN ('same_session_fresh', 'unavailable_fallback')",
            name="ck_c_task_opportunities_mastery_context_mode",
        ),
        *ProvenanceMixin.provenance_constraints("c_task_opportunities"),
    )

    c_task_opportunity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    c_session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("c_sessions.c_session_id", ondelete="RESTRICT"), nullable=False
    )
    task_index: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_skill_id: Mapped[str] = mapped_column(String(128), nullable=False)
    selected_template_id: Mapped[str] = mapped_column(String(128), nullable=False)
    initial_difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False)
    # ALLOW-LISTED -- false-positive-name class, same reasoning as c_sessions above.
    mastery_context_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    # ALLOW-LISTED -- carries-real-content class (R-D): SelectionResult's own returned
    # provenance for the governed clamp(round(1 + 4 x mastery), 1, 5) initial-difficulty
    # decision (C-17). C auditing its own reviewed calculation, not re-storing B's contract.
    mastery_selected_skill: Mapped[float | None] = mapped_column(Float, nullable=True)
    session_phase: Mapped[str] = mapped_column(String(32), nullable=False)
    terminal_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    task_offered_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CTaskInstanceRecord(ProvenanceMixin, Base):
    """Component C Phase 3a. PRIVATE. Instance, difficulty vector, correct answer, seed lineage
    (v3.0 §11 Phase 3). No projection to a public DTO exists in this codebase yet -- building
    one (mirroring B's BE3c ``project_task_instance_to_presentation`` allow-list pattern) is
    Phase 5's job, not this batch's. Mirrors B's ``TaskInstanceRecord`` minimal-FK style: reached
    only via ``c_task_opportunity_id``, no denormalized session/student id."""

    __tablename__ = "c_task_instances"
    __table_args__ = (
        UniqueConstraint("c_task_opportunity_id", name="uq_c_task_instances_opportunity"),
        CheckConstraint("grade_scope IN (2, 3)", name="ck_c_task_instances_grade_scope"),
        CheckConstraint(
            "scaffold_state IN ('C0', 'C1', 'C2', 'C3', 'C4')", name="ck_c_task_instances_scaffold_state"
        ),
        CheckConstraint("technical_status IN ('OK', 'FAILED')", name="ck_c_task_instances_technical_status"),
        *ProvenanceMixin.provenance_constraints("c_task_instances"),
    )

    c_task_instance_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    c_task_opportunity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("c_task_opportunities.c_task_opportunity_id", ondelete="RESTRICT"),
        nullable=False,
    )
    game_family_id: Mapped[str] = mapped_column(String(32), nullable=False)
    game_task_template_id: Mapped[str] = mapped_column(String(64), nullable=False)
    template_version: Mapped[str] = mapped_column(String(64), nullable=False)
    catalogue_version: Mapped[str] = mapped_column(String(128), nullable=False)
    generator_version: Mapped[str] = mapped_column(String(64), nullable=False)
    task_index: Mapped[int] = mapped_column(Integer, nullable=False)
    skill_id: Mapped[str] = mapped_column(String(128), nullable=False)
    curriculum_node_id: Mapped[str] = mapped_column(String(128), nullable=False)
    grade_scope: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty_vector: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    functional_role: Mapped[str] = mapped_column(String(32), nullable=False)
    representation_mode: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    interactive_assets: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    # ALLOW-LISTED -- carries-real-content class: the private, never-public correct answer.
    correct_answer_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    # ALLOW-LISTED -- carries-real-content class: not named by v3.0 §8, found by this batch's
    # own term-by-term derivation (Phase 3a work order R-B): "correctness_function_id" contains
    # "correct".
    correctness_function_id: Mapped[str] = mapped_column(String(64), nullable=False)
    valid_action_space: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    completion_condition: Mapped[str] = mapped_column(String(255), nullable=False)
    failure_condition: Mapped[str] = mapped_column(String(255), nullable=False)
    scaffold_state: Mapped[str] = mapped_column(String(8), nullable=False)
    recovery_parent_instance_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("c_task_instances.c_task_instance_id", ondelete="RESTRICT"), nullable=True
    )
    technical_status: Mapped[str] = mapped_column(String(16), nullable=False)
    seed_lineage_global_seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    seed_lineage_path: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    seed_lineage_seed: Mapped[int] = mapped_column(BigInteger, nullable=False)


class CGameplayEventRecord(ProvenanceMixin, Base):
    """Component C Phase 3a. The canonical stream (C3 §14). Table shape only -- append-only /
    immutable enforcement (no UPDATE after insert) and every cross-row invariant (exactly one
    terminal event per task, event_index continuity, timestamp monotonicity) are Phase 3b, not
    built here (v3.0 §11 Phase 3 names these as DB-level constraints, but the Phase 3a work
    order's own scope split reserves every cross-row invariant for 3b)."""

    __tablename__ = "c_gameplay_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ("
            "'game_task_offered', 'game_task_started', 'action_performed', 'answer_submitted', "
            "'answer_evaluated', 'retry_started', 'pause_started', 'pause_ended', "
            "'scaffold_requested', 'scaffold_shown', 'technical_issue', 'game_task_completed', "
            "'game_task_skipped', 'game_task_quit')",
            name="ck_c_gameplay_events_event_type",
        ),
        CheckConstraint("event_timestamp_relative_ms >= 0", name="ck_c_gameplay_events_timestamp_non_negative"),
        CheckConstraint(
            "scaffold_code IS NULL OR scaffold_code IN ('C0', 'C1', 'C2', 'C3', 'C4')",
            name="ck_c_gameplay_events_scaffold_code",
        ),
        CheckConstraint(
            "terminal_reason IS NULL OR terminal_reason IN ("
            "'completed_correct', 'completed_incorrect', 'skipped', 'quit_after_error', "
            "'quit_without_recent_error', 'technical_issue', 'attempt_cap_exhausted', "
            "'timeout_no_response', 'safe_session_stop')",
            name="ck_c_gameplay_events_terminal_reason",
        ),
        *ProvenanceMixin.provenance_constraints("c_gameplay_events"),
    )

    c_gameplay_event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    c_session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("c_sessions.c_session_id", ondelete="RESTRICT"), nullable=False
    )
    game_task_instance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("c_task_instances.c_task_instance_id", ondelete="RESTRICT"), nullable=False
    )
    task_index: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    event_index: Mapped[int] = mapped_column(Integer, nullable=False)
    attempt_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event_timestamp_relative_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    action_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    evaluation_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    scaffold_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    technical_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    terminal_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    seed_lineage_global_seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    seed_lineage_path: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    seed_lineage_seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    generator_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_checksum: Mapped[str] = mapped_column(String(64), nullable=False)


class CTaskOpportunitySummaryRecord(ProvenanceMixin, Base):
    """Component C Phase 3a. Derived per-task rollup (C3 §15). Derived only, never sampled --
    exactly one summary per task instance (UNIQUE below)."""

    __tablename__ = "c_task_opportunity_summaries"
    __table_args__ = (
        UniqueConstraint("game_task_instance_id", name="uq_c_task_opportunity_summaries_instance"),
        CheckConstraint(
            "highest_scaffold_level IS NULL OR highest_scaffold_level IN ('C0', 'C1', 'C2', 'C3', 'C4')",
            name="ck_c_task_opportunity_summaries_highest_scaffold_level",
        ),
        CheckConstraint(
            "terminal_reason IS NULL OR terminal_reason IN ("
            "'completed_correct', 'completed_incorrect', 'skipped', 'quit_after_error', "
            "'quit_without_recent_error', 'technical_issue', 'attempt_cap_exhausted', "
            "'timeout_no_response', 'safe_session_stop')",
            name="ck_c_task_opportunity_summaries_terminal_reason",
        ),
        *ProvenanceMixin.provenance_constraints("c_task_opportunity_summaries"),
    )

    c_task_opportunity_summary_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    c_session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("c_sessions.c_session_id", ondelete="RESTRICT"), nullable=False
    )
    game_task_instance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("c_task_instances.c_task_instance_id", ondelete="RESTRICT"), nullable=False
    )
    task_index: Mapped[int] = mapped_column(Integer, nullable=False)
    task_offered: Mapped[bool] = mapped_column(Boolean, nullable=False)
    task_started: Mapped[bool] = mapped_column(Boolean, nullable=False)
    task_completed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    task_skipped: Mapped[bool] = mapped_column(Boolean, nullable=False)
    task_quit: Mapped[bool] = mapped_column(Boolean, nullable=False)
    technical_issue: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # ALLOW-LISTED -- carries-real-content class.
    correct_task: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    total_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False)
    scaffold_requested: Mapped[bool] = mapped_column(Boolean, nullable=False)
    scaffold_count: Mapped[int] = mapped_column(Integer, nullable=False)
    highest_scaffold_level: Mapped[str | None] = mapped_column(String(8), nullable=True)
    # ALLOW-LISTED -- carries-real-content class.
    c_answer_changes: Mapped[int] = mapped_column(Integer, nullable=False)
    # ALLOW-LISTED -- carries-real-content class.
    task_latency_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    inactive_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    inactivity_periods: Mapped[int] = mapped_column(Integer, nullable=False)
    quit_after_error: Mapped[bool] = mapped_column(Boolean, nullable=False)
    terminal_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # ALLOW-LISTED -- carries-real-content class.
    first_attempt_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # ALLOW-LISTED -- carries-real-content class.
    final_attempt_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # NOT allow-listed -- verified this batch (R-B) to NOT collide: the prohibited term is
    # "error_class", and this column contains "error_max", not "error_class". v3.0 §8 names this
    # column as colliding; that is a documented error in v3.0, not reproduced here.
    consecutive_error_max_within_task: Mapped[int] = mapped_column(Integer, nullable=False)


class CSessionAggregateResultRecord(ProvenanceMixin, Base):
    """Component C Phase 3a. PRIVATE. Aggregate + C-COMP-v1 + C-LS-v1 (v3.0 §11 Phase 3). No
    projection to a public DTO exists in this codebase yet -- Phase 5's job, not this batch's."""

    __tablename__ = "c_session_aggregate_results"
    __table_args__ = (
        UniqueConstraint("c_session_id", name="uq_c_session_aggregate_results_session"),
        CheckConstraint(
            "difficulty_trend IN ('increasing', 'stable', 'decreasing')",
            name="ck_c_session_aggregate_results_difficulty_trend",
        ),
        CheckConstraint(
            "telemetry_quality_status IS NULL OR telemetry_quality_status IN "
            "('complete', 'insufficient_evidence', 'technical_issue')",
            name="ck_c_session_aggregate_results_telemetry_quality_status",
        ),
        CheckConstraint(
            "learner_state IS NULL OR learner_state IN "
            "('engaged', 'productive_struggle', 'overloaded', 'disengaged')",
            name="ck_c_session_aggregate_results_learner_state",
        ),
        CheckConstraint(
            "state_reason IS NULL OR state_reason IN ("
            "'technical_issue', 'insufficient_session_evidence', 'safety_override_with_error_burst', "
            "'quit_after_error', 'repeated_floor_hits_with_low_completion', 'high_behavioral_friction', "
            "'low_engagement_score', 'inactivity_with_low_completion', 'high_engagement_low_friction', "
            "'sustained_participation_under_challenge', 'insufficient_sustained_participation')",
            name="ck_c_session_aggregate_results_state_reason",
        ),
        *ProvenanceMixin.provenance_constraints("c_session_aggregate_results"),
    )

    c_session_aggregate_result_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    c_session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("c_sessions.c_session_id", ondelete="RESTRICT"), nullable=False
    )
    task_opportunity_count: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_task_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # ALLOW-LISTED -- carries-real-content class.
    correct_task_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_attempts_per_task: Mapped[float | None] = mapped_column(Float, nullable=True)
    task_completion_rate: Mapped[float] = mapped_column(Float, nullable=False)
    inactivity_periods: Mapped[int] = mapped_column(Integer, nullable=False)
    inactive_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    inactive_time_available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    session_duration_sec: Mapped[float] = mapped_column(Float, nullable=False)
    time_in_target_band_sec: Mapped[float] = mapped_column(Float, nullable=False)
    consecutive_error_max: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty_floor_hits: Mapped[int] = mapped_column(Integer, nullable=False)
    quit_after_error: Mapped[bool] = mapped_column(Boolean, nullable=False)
    safety_override_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # ALLOW-LISTED -- carries-real-content class.
    c_mean_game_task_latency_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    # ALLOW-LISTED -- carries-real-content class.
    c_median_game_task_latency_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty_trend: Mapped[str] = mapped_column(String(16), nullable=False)
    session_technical_issue_flag: Mapped[bool] = mapped_column(Boolean, nullable=False)
    engagement_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    engagement_completion_component: Mapped[float | None] = mapped_column(Float, nullable=True)
    engagement_activity_component: Mapped[float | None] = mapped_column(Float, nullable=True)
    engagement_target_band_component: Mapped[float | None] = mapped_column(Float, nullable=True)
    engagement_accuracy_component: Mapped[float | None] = mapped_column(Float, nullable=True)
    frustration_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    frustration_error_run_component: Mapped[float | None] = mapped_column(Float, nullable=True)
    frustration_excess_attempt_component: Mapped[float | None] = mapped_column(Float, nullable=True)
    frustration_inactivity_burden_component: Mapped[float | None] = mapped_column(Float, nullable=True)
    frustration_floor_hit_component: Mapped[float | None] = mapped_column(Float, nullable=True)
    frustration_quit_after_error_component: Mapped[float | None] = mapped_column(Float, nullable=True)
    frustration_safety_override_component: Mapped[float | None] = mapped_column(Float, nullable=True)
    telemetry_quality_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    learner_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    state_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)


class CLearnerLocalStateRecord(ProvenanceMixin, Base):
    """Component C Phase 3a. Longitudinal: ``eligible_combined_handoffs_completed`` (N),
    per-skill ``sessions_since_last_practice``, ``prior_session_end_state`` (v3.0 §11 Phase 3).
    One row per learner."""

    __tablename__ = "c_learner_local_state"
    __table_args__ = (
        UniqueConstraint("student_id", name="uq_c_learner_local_state_student"),
        CheckConstraint(
            "prior_session_end_state IS NULL OR prior_session_end_state IN "
            "('engaged', 'productive_struggle', 'overloaded', 'disengaged')",
            name="ck_c_learner_local_state_prior_session_end_state",
        ),
        *ProvenanceMixin.provenance_constraints("c_learner_local_state"),
    )

    c_learner_local_state_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("b_learners.learner_id", ondelete="RESTRICT"), nullable=False
    )
    eligible_combined_handoffs_completed: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    sessions_since_last_practice: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    prior_session_end_state: Mapped[str | None] = mapped_column(String(32), nullable=True)


class CPolicyDecisionRecord(ProvenanceMixin, Base):
    """Component C Phase 3a. Every proposal and applied action, versioned, incl.
    ``increase_block_remaining`` (v3.0 §11 Phase 3). ``evidence_snapshot`` holds the
    ``PolicyObservableEvidence`` the decision was based on as JSONB rather than flattened
    columns -- BUILDER JUDGMENT, UNRATIFIED: flattening would add more prohibited-term columns
    (e.g. ``recent_correctness_rate``) without changing what is stored."""

    __tablename__ = "c_policy_decisions"
    __table_args__ = (
        CheckConstraint(
            "policy_mode IN ('rule_based_baseline', 'q_learning_offline', 'frozen_q_evaluation')",
            name="ck_c_policy_decisions_policy_mode",
        ),
        CheckConstraint(
            "selected_action IN ('decrease_difficulty', 'hold', 'increase_difficulty')",
            name="ck_c_policy_decisions_selected_action",
        ),
        CheckConstraint(
            "applied_action IN ('decrease_difficulty', 'hold', 'increase_difficulty')",
            name="ck_c_policy_decisions_applied_action",
        ),
        CheckConstraint(
            "rolling_strain_bucket IN ('low', 'moderate', 'high', 'severe')",
            name="ck_c_policy_decisions_rolling_strain_bucket",
        ),
        CheckConstraint(
            "session_start_state_bucket IS NULL OR session_start_state_bucket IN "
            "('engaged', 'productive_struggle', 'overloaded', 'disengaged')",
            name="ck_c_policy_decisions_session_start_state_bucket",
        ),
        *ProvenanceMixin.provenance_constraints("c_policy_decisions"),
    )

    c_policy_decision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    c_session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("c_sessions.c_session_id", ondelete="RESTRICT"), nullable=False
    )
    c_task_opportunity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("c_task_opportunities.c_task_opportunity_id", ondelete="RESTRICT"),
        nullable=False,
    )
    policy_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    rl_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    selected_action: Mapped[str] = mapped_column(String(32), nullable=False)
    applied_action: Mapped[str] = mapped_column(String(32), nullable=False)
    action_overridden: Mapped[bool] = mapped_column(Boolean, nullable=False)
    safety_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    difficulty_before: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty_after: Mapped[int] = mapped_column(Integer, nullable=False)
    rolling_strain_bucket: Mapped[str] = mapped_column(String(16), nullable=False)
    session_start_state_bucket: Mapped[str | None] = mapped_column(String(32), nullable=True)
    increase_block_remaining: Mapped[int] = mapped_column(Integer, nullable=False)
    internal_reward: Mapped[float | None] = mapped_column(Float, nullable=True)
    seed_lineage_global_seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    seed_lineage_path: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    seed_lineage_seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    evidence_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class CSafetyEventRecord(ProvenanceMixin, Base):
    """Component C Phase 3a. Every intervention, with trigger and action (v3.0 §11 Phase 3).
    ``trigger_reason``/``action_taken`` are left without an enum CHECK -- BUILDER JUDGMENT,
    UNRATIFIED: no verified package Literal names the closed vocabulary for these two fields the
    way it does for e.g. ``policy_mode``; adding an invented enum would risk exactly the kind of
    unsourced value R-G prohibits for numeric literals, applied here to strings instead."""

    __tablename__ = "c_safety_events"
    __table_args__ = (*ProvenanceMixin.provenance_constraints("c_safety_events"),)

    c_safety_event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    c_session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("c_sessions.c_session_id", ondelete="RESTRICT"), nullable=False
    )
    c_policy_decision_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("c_policy_decisions.c_policy_decision_id", ondelete="RESTRICT"), nullable=True
    )
    trigger_reason: Mapped[str] = mapped_column(String(128), nullable=False)
    action_taken: Mapped[str] = mapped_column(String(64), nullable=False)
    difficulty_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty_after: Mapped[int | None] = mapped_column(Integer, nullable=True)


class CScaffoldEventRecord(ProvenanceMixin, Base):
    """Component C Phase 3a. Requests and shows, C0-C4 (v3.0 §11 Phase 3). ``event_type`` is
    left without an enum CHECK -- BUILDER JUDGMENT, UNRATIFIED: "requested"/"shown" is inferred
    from v3.0's own prose ("Requests and shows"), not verified against a package Literal the way
    ``scaffold_level`` is; not adding an unsourced enum here."""

    __tablename__ = "c_scaffold_events"
    __table_args__ = (
        CheckConstraint(
            "scaffold_level IN ('C0', 'C1', 'C2', 'C3', 'C4')", name="ck_c_scaffold_events_scaffold_level"
        ),
        *ProvenanceMixin.provenance_constraints("c_scaffold_events"),
    )

    c_scaffold_event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    c_session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("c_sessions.c_session_id", ondelete="RESTRICT"), nullable=False
    )
    c_task_opportunity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("c_task_opportunities.c_task_opportunity_id", ondelete="RESTRICT"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(16), nullable=False)
    scaffold_level: Mapped[str] = mapped_column(String(8), nullable=False)
    consecutive_incorrect_current_task: Mapped[int] = mapped_column(Integer, nullable=False)
    safety_forces_recovery: Mapped[bool] = mapped_column(Boolean, nullable=False)


AUTHORIZED_TABLES = frozenset(Base.metadata.tables)
