"""SQLAlchemy repositories for the eight neutral BE2 tables."""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence_models import (
    AppUser, AppUserLearnerLink, AuditEvent, Base, Classroom, IdempotencyRecord,
    Learner, RuntimeBundleRecord, SessionEvent, SessionRecord, TeacherProfile,
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
