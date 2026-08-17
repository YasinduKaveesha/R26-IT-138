"""``resolve_c_bundle_and_catalogue`` -- the one function in this batch that maps a fail-closed
runtime-bundle/catalogue failure to the stable, public ``ConflictError`` (409) contract.

Mirrors ``app.application.opportunity_selection``'s own bundle-resolution pattern
(``except (RuntimeBundleError, LiveEngineError) as exc: raise ConflictError() from exc``) for
Component C: ``CRuntimeBundleLoader`` (not B's ``RuntimeBundleLoader`` -- see
``app.infrastructure.runtime_bundle_c.loader`` for why) validates the bundle manifest and its
declared checksums; the adapter then loads and checksums the catalogue artefact itself.

Not a service, not a router, no session logic, no persistence write -- a single pure function
with one job: translate every fail-closed exception this chain can raise into the one stable
error type the public API contract already knows how to render as HTTP 409 with a request id
(``app.core.errors.install_error_handlers``, unmodified, unrelated to this batch).
"""

from __future__ import annotations

from typing import Mapping, Optional

from app.core.errors import ConflictError
from app.domain.live_engine_c.errors import LiveEngineCError, SelectionConfigurationMissingError
from app.domain.live_engine_c.types import Catalogue, SelectionConfig
from app.domain.runtime_bundle.errors import RuntimeBundleError
from app.domain.runtime_bundle_c.types import CRuntimeBundle
from app.infrastructure.live_engine_c.adapter import LiveEngineCAdapter
from app.infrastructure.runtime_bundle_c.loader import CRuntimeBundleLoader


def resolve_c_bundle_and_catalogue(
    *,
    bundle_path: str,
    schema_path: str,
    catalogue_path: str,
    require_approved: bool = True,
    artifact_paths: Optional[Mapping[str, str]] = None,
) -> tuple[CRuntimeBundle, Catalogue, str]:
    """Load + validate the C runtime bundle manifest, then load + checksum the catalogue it
    points at. Fails closed: any ``RuntimeBundleError`` (schema failure, checksum mismatch,
    missing file, unapproved status) or ``LiveEngineCError`` (catalogue load failure) is
    translated into ``ConflictError`` -- never returned as a partial result, never silently
    substituted with a fallback.
    """
    resolved_artifact_paths = dict(artifact_paths or {})
    resolved_artifact_paths.setdefault("catalogue", catalogue_path)
    try:
        bundle = CRuntimeBundleLoader().load_and_validate(
            bundle_path,
            schema_path,
            artifact_paths=resolved_artifact_paths,
            require_approved=require_approved,
        )
        adapter = LiveEngineCAdapter()
        catalogue = adapter.load(catalogue_path)
        catalogue_checksum = adapter.checksum(catalogue_path)
    except (RuntimeBundleError, LiveEngineCError) as exc:
        raise ConflictError() from exc
    return bundle, catalogue, catalogue_checksum


def resolve_selection_config(bundle: CRuntimeBundle) -> SelectionConfig:
    """Phase 4b, owner condition 1: "Fail-closed means halt, not default." Raises
    ``SelectionConfigurationMissingError`` when ``bundle.selection_configuration`` is ``None``
    (a real, expected state for any bundle not yet republished with the block, B1-b/additive-
    only) -- never defaults, never substitutes a placeholder, never partially constructs
    ``SelectionConfig``. When present, this is a direct field-by-field carry: no vocabulary
    coercion (``approval_status`` is not read here at all -- it is the bundle's own governance
    gate value, already enforced by ``resolve_c_bundle_and_catalogue``'s ``require_approved``;
    ``config_version``/``parameter_source_status`` are read from their own, independent manifest
    fields)."""
    artifact = bundle.selection_configuration
    if artifact is None:
        raise SelectionConfigurationMissingError(
            f"runtime bundle {bundle.bundle_version!r} carries no selection_configuration -- "
            "halting rather than proceeding on a default (owner condition 1)"
        )
    return SelectionConfig(
        config_version=artifact.config_version,
        parameter_source_status=artifact.parameter_source_status,
        familiarization_window_by_grade=artifact.familiarization_window_by_grade,
        familiarization_difficulty_level=artifact.familiarization_difficulty_level,
        fallback_difficulty_level=artifact.fallback_difficulty_level,
        familiarization_session_difficulty_cap=artifact.familiarization_session_difficulty_cap,
        fallback_difficulty_cap=artifact.fallback_difficulty_cap,
    )
