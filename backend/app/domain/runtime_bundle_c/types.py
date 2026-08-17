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
from typing import Mapping, Optional

from app.domain.runtime_bundle.types import Checksum, Compatibility, SourceArtifact, VersionedArtifact


@dataclass(frozen=True)
class SelectionConfigurationArtifact:
    """Phase 4b, schema_version 1.1. Mirrors ``provenance/c-runtime-bundle.schema.json``'s
    (AMENDED, seven-field) ``selectionConfiguration`` $def exactly -- the owner's ruling to carry
    the full ``CSelectionConfig``, not only the window. ``approval_status`` stays the governance
    gate value (consumed by the bundle approval check only); ``config_version``/
    ``parameter_source_status`` are carried as their OWN independent fields, never derived from
    ``version``/``approval_status`` (see the schema's own field-by-field provenance for why
    collapsing them would be a vocabulary coercion). Every numeric/config value here is whatever
    the bundle manifest records -- CALIBRATION_PENDING today -- never a default supplied by this
    type; a bundle without this block produces no instance of it at all (``Optional`` on
    ``CRuntimeBundle`` below), never a placeholder instance."""

    version: str
    checksum: Checksum
    approval_status: str
    config_version: str
    parameter_source_status: str
    familiarization_window_by_grade: Mapping[int, int]
    familiarization_difficulty_level: int
    fallback_difficulty_level: int
    familiarization_session_difficulty_cap: int
    fallback_difficulty_cap: int


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
    selection_configuration: Optional[SelectionConfigurationArtifact]
