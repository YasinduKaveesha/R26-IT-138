"""SQLAlchemy repositories for the twelve neutral BE2 tables."""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence_models import (
    AppUser, AppUserLearnerLink, AuditEvent, Base, Classroom, ClassroomInvite,
    ClassroomMembership, IdempotencyRecord, Learner, RuntimeBundleRecord,
    SessionEvent, SessionRecord, TeacherProfile,
)


ModelT = TypeVar("ModelT", bound=Base)


class SqlAlchemyNeutralRepository(Generic[ModelT]):
    model_type: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, record: ModelT) -> None:
        self.session.add(record)
        await self.session.flush()

    async def get_by_id(self, record_id: UUID) -> ModelT | None:
        return await self.session.get(self.model_type, record_id)

    async def exists(self, record_id: UUID) -> bool:
        return await self.get_by_id(record_id) is not None


class AppUserRepository(SqlAlchemyNeutralRepository[AppUser]):
    model_type = AppUser

    async def find_by_subject(self, subject: str) -> AppUser | None:
        return await self.session.scalar(select(AppUser).where(AppUser.supabase_subject == subject))


class LearnerRepository(SqlAlchemyNeutralRepository[Learner]):
    model_type = Learner


class AppUserLearnerLinkRepository(SqlAlchemyNeutralRepository[AppUserLearnerLink]):
    model_type = AppUserLearnerLink

    async def find_by_user(self, user_id: UUID) -> AppUserLearnerLink | None:
        return await self.session.scalar(select(AppUserLearnerLink).where(AppUserLearnerLink.user_id == user_id))


class RuntimeBundleRecordRepository(SqlAlchemyNeutralRepository[RuntimeBundleRecord]):
    model_type = RuntimeBundleRecord


class SessionRecordRepository(SqlAlchemyNeutralRepository[SessionRecord]):
    model_type = SessionRecord


class SessionEventRepository(SqlAlchemyNeutralRepository[SessionEvent]):
    model_type = SessionEvent


class IdempotencyRecordRepository(SqlAlchemyNeutralRepository[IdempotencyRecord]):
    model_type = IdempotencyRecord

    async def find_scoped(
        self,
        actor_user_id: UUID,
        http_method: str,
        operation_identifier: str,
        idempotency_key: str,
    ) -> IdempotencyRecord | None:
        statement: Select[tuple[IdempotencyRecord]] = select(IdempotencyRecord).where(
            IdempotencyRecord.actor_user_id == actor_user_id,
            IdempotencyRecord.http_method == http_method,
            IdempotencyRecord.operation_identifier == operation_identifier,
            IdempotencyRecord.idempotency_key == idempotency_key,
        )
        return await self.session.scalar(statement)


class AuditEventRepository(SqlAlchemyNeutralRepository[AuditEvent]):
    model_type = AuditEvent


class TeacherProfileRepository(SqlAlchemyNeutralRepository[TeacherProfile]):
    model_type = TeacherProfile

    async def find_by_user(self, user_id: UUID) -> TeacherProfile | None:
        return await self.session.scalar(select(TeacherProfile).where(TeacherProfile.user_id == user_id))


class ClassroomRepository(SqlAlchemyNeutralRepository[Classroom]):
    model_type = Classroom

    async def list_owned(self, teacher_profile_id: UUID) -> list[Classroom]:
        result = await self.session.scalars(select(Classroom).where(Classroom.teacher_profile_id == teacher_profile_id).order_by(Classroom.created_at_utc, Classroom.classroom_id))
        return list(result)

    async def get_owned(self, classroom_id: UUID, teacher_profile_id: UUID) -> Classroom | None:
        return await self.session.scalar(select(Classroom).where(Classroom.classroom_id == classroom_id, Classroom.teacher_profile_id == teacher_profile_id))


class ClassroomInviteRepository(SqlAlchemyNeutralRepository[ClassroomInvite]):
    model_type = ClassroomInvite

    async def find_by_token_hash(self, token_hash: str) -> ClassroomInvite | None:
        return await self.session.scalar(select(ClassroomInvite).where(ClassroomInvite.token_hash == token_hash))

    async def get_owned(self, classroom_invite_id: UUID, teacher_profile_id: UUID) -> ClassroomInvite | None:
        statement = (
            select(ClassroomInvite)
            .join(Classroom, Classroom.classroom_id == ClassroomInvite.classroom_id)
            .where(ClassroomInvite.classroom_invite_id == classroom_invite_id, Classroom.teacher_profile_id == teacher_profile_id)
        )
        return await self.session.scalar(statement)


class ClassroomMembershipRepository(SqlAlchemyNeutralRepository[ClassroomMembership]):
    model_type = ClassroomMembership

    async def find_by_classroom_and_learner(self, classroom_id: UUID, learner_id: UUID) -> ClassroomMembership | None:
        return await self.session.scalar(
            select(ClassroomMembership).where(ClassroomMembership.classroom_id == classroom_id, ClassroomMembership.learner_id == learner_id)
        )

    async def get_owned(self, classroom_membership_id: UUID, teacher_profile_id: UUID) -> ClassroomMembership | None:
        statement = (
            select(ClassroomMembership)
            .join(Classroom, Classroom.classroom_id == ClassroomMembership.classroom_id)
            .where(ClassroomMembership.classroom_membership_id == classroom_membership_id, Classroom.teacher_profile_id == teacher_profile_id)
        )
        return await self.session.scalar(statement)

    async def learner_has_other_approved_membership(self, learner_id: UUID, excluding_membership_id: UUID) -> bool:
        existing = await self.session.scalar(
            select(ClassroomMembership.classroom_membership_id).where(
                ClassroomMembership.learner_id == learner_id,
                ClassroomMembership.state == "APPROVED",
                ClassroomMembership.classroom_membership_id != excluding_membership_id,
            )
        )
        return existing is not None

    async def list_for_classroom_with_learner_name(self, classroom_id: UUID) -> list[tuple[ClassroomMembership, str | None]]:
        statement = (
            select(ClassroomMembership, Learner.name)
            .join(Learner, Learner.learner_id == ClassroomMembership.learner_id)
            .where(ClassroomMembership.classroom_id == classroom_id)
            .order_by(ClassroomMembership.requested_at_utc, ClassroomMembership.classroom_membership_id)
        )
        result = await self.session.execute(statement)
        return list(result.all())

    async def list_approved_for_classroom_with_learner_name(self, classroom_id: UUID) -> list[tuple[ClassroomMembership, str | None]]:
        statement = (
            select(ClassroomMembership, Learner.name)
            .join(Learner, Learner.learner_id == ClassroomMembership.learner_id)
            .where(ClassroomMembership.classroom_id == classroom_id, ClassroomMembership.state == "APPROVED")
            .order_by(ClassroomMembership.decided_at_utc, ClassroomMembership.classroom_membership_id)
        )
        result = await self.session.execute(statement)
        return list(result.all())

    async def list_for_learner_with_classroom(self, learner_id: UUID) -> list[tuple[ClassroomMembership, str | None, str]]:
        statement = (
            select(ClassroomMembership, Classroom.name, Classroom.grade)
            .join(Classroom, Classroom.classroom_id == ClassroomMembership.classroom_id)
            .where(ClassroomMembership.learner_id == learner_id)
            .order_by(ClassroomMembership.requested_at_utc, ClassroomMembership.classroom_membership_id)
        )
        result = await self.session.execute(statement)
        return list(result.all())
