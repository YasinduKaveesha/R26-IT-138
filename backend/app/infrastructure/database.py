"""Async PostgreSQL connectivity lifecycle for BE1.

MANAGED-POSTGRES NOTE (Supabase and equivalents). This module accepts a connection string copied
verbatim from a managed provider's dashboard. Two things in such a string are incompatible with
asyncpg and are normalised here rather than being left for whoever pastes it to discover:

1. ``sslmode`` and friends are **libpq** parameters. psycopg2 understands them; asyncpg does not,
   and raises ``TypeError: connect() got an unexpected keyword argument 'sslmode'`` on a string
   that works fine in ``psql``. They are stripped from the URL and translated into asyncpg's own
   ``ssl`` connect-arg, so the security intent of the pasted string is preserved rather than
   silently dropped. (asyncpg's own default is ``prefer``, which would negotiate TLS against a
   provider that requires it anyway -- but ``prefer`` does not *insist*, so a string that asked
   for ``require`` must keep asking for it.)
2. A **transaction-mode connection pooler** (Supabase's port 6543, and the ``pooler`` hostnames)
   multiplexes many clients onto few server connections, which breaks asyncpg's prepared-statement
   cache -- the symptom is an intermittent ``prepared statement "__asyncpg_stmt_x__" does not
   exist`` under concurrency, not a clean failure at startup. Both caches are disabled when a
   pooler is detected: asyncpg's via ``statement_cache_size``, SQLAlchemy's via the dialect's own
   ``prepared_statement_cache_size`` URL parameter.

Detection is by port and hostname only. A local Docker ``DATABASE_URL`` carries no query string and
no pooler port, so it is passed through completely unchanged -- this note describes an addition,
not a change to how local development already worked.

``pg_advisory_xact_lock`` (used for session/attempt idempotency across eight call sites) is
transaction-scoped and therefore safe under transaction pooling. A session-scoped advisory lock
would not have been.
"""

from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

# libpq query parameters asyncpg does not accept as keyword arguments. Stripped from the URL;
# `sslmode` is additionally translated (see `_ssl_for_sslmode`), the rest are file-based TLS
# options with no asyncpg keyword equivalent and are dropped rather than half-honoured.
_LIBPQ_ONLY_QUERY_KEYS = frozenset(
    {"sslmode", "sslrootcert", "sslcert", "sslkey", "sslpassword", "channel_binding"}
)

# libpq's `prefer`/`allow` negotiate opportunistically; asyncpg's `ssl=True` insists. Anything
# stricter than `require` still maps to `True` here: asyncpg performs no CA or hostname
# verification without an explicit SSLContext, so claiming `verify-full` would overstate what is
# actually enforced. Recorded rather than silently downgraded.
_SSLMODE_TO_ASYNCPG_SSL: dict[str, Any] = {
    "disable": False,
    "allow": "prefer",
    "prefer": "prefer",
    "require": True,
    "verify-ca": True,
    "verify-full": True,
}

_TRANSACTION_POOLER_PORT = 6543


def _is_transaction_pooler(host: str | None, port: int | None) -> bool:
    if port == _TRANSACTION_POOLER_PORT:
        return True
    return bool(host and "pooler." in host.lower())


def async_database_url(database_url: str) -> str:
    """Normalise any accepted PostgreSQL URL into an asyncpg URL SQLAlchemy can consume.

    Alembic builds its `sqlalchemy.url` through this same function (`migrations/env.py`), so a
    managed-provider connection string is stripped identically for migrations and for the running
    application -- there is no second place where a pasted `sslmode` can survive.
    """
    if database_url.startswith("postgresql+asyncpg://"):
        normalised = database_url
    elif database_url.startswith("postgresql://"):
        normalised = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        normalised = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    else:
        raise ValueError("DATABASE_URL must use PostgreSQL")

    parts = urlsplit(normalised)
    retained = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in _LIBPQ_ONLY_QUERY_KEYS
    ]
    if _is_transaction_pooler(parts.hostname, parts.port) and not any(
        key.lower() == "prepared_statement_cache_size" for key, _ in retained
    ):
        retained.append(("prepared_statement_cache_size", "0"))
    return urlunsplit(parts._replace(query=urlencode(retained)))


def asyncpg_connect_args(database_url: str) -> dict[str, Any]:
    """Connect-args derived from the libpq parameters `async_database_url` had to strip."""
    parts = urlsplit(database_url)
    query = {key.lower(): value for key, value in parse_qsl(parts.query, keep_blank_values=True)}
    connect_args: dict[str, Any] = {}

    sslmode = query.get("sslmode", "").strip().lower()
    if sslmode:
        if sslmode not in _SSLMODE_TO_ASYNCPG_SSL:
            raise ValueError(f"Unsupported sslmode in DATABASE_URL: {sslmode!r}")
        connect_args["ssl"] = _SSLMODE_TO_ASYNCPG_SSL[sslmode]

    if _is_transaction_pooler(parts.hostname, parts.port):
        connect_args["statement_cache_size"] = 0
    return connect_args


_settings = get_settings()
engine: AsyncEngine = create_async_engine(
    async_database_url(_settings.database_url),
    pool_pre_ping=True,
    connect_args=asyncpg_connect_args(_settings.database_url),
)
session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_database_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


async def probe_database() -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def dispose_database() -> None:
    await engine.dispose()
