"""Backend domain mirror of ``provenance/c-runtime-bundle.schema.json`` (Phase 2).

Reuses ``Checksum``/``SourceArtifact``/``VersionedArtifact``/``Compatibility`` from
``app.domain.runtime_bundle.types`` (Component B's own domain module) directly -- those four
dataclasses carry no B-specific field or meaning; they are unchanged, structurally shared
shapes. Only the top-level aggregate is new: unlike
``app.domain.runtime_bundle.types.RuntimeBundle``, ``CRuntimeBundle`` carries none of B's config
blocks (``bkt_configuration``, ``certification_configuration``, ``guess_guard_configuration``,
``sequencing_configuration``, ``safe_progress_policy``, ``attempt_policy``, ``timeout_policy``,
``completion_policy``, ``cold_start_policy``) -- none of those are Component C concepts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.domain.runtime_bundle.types import Compatibility, SourceArtifact, VersionedArtifact


@dataclass(frozen=True)
class CRuntimeBundle:
    schema_version: str
    bundle_version: str
    publication_state: str
    backend_code_version: str
    database_schema_revision: str
    generator: SourceArtifact
    catalogue: VersionedArtifact
    approval_status: str
    activation_date: Optional[str]
    compatibility: Compatibility
