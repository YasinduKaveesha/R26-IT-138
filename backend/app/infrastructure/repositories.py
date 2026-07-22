"""SQLAlchemy repositories for the eight neutral BE2 tables."""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence_models import (
    AppUser, AppUserLearnerLink, AuditEvent, Base, IdempotencyRecord,
    Learner, RuntimeBundleRecord, SessionEvent, SessionRecord,
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


class LearnerRepository(SqlAlchemyNeutralRepository[Learner]):
    model_type = Learner


class AppUserLearnerLinkRepository(SqlAlchemyNeutralRepository[AppUserLearnerLink]):
    model_type = AppUserLearnerLink


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

