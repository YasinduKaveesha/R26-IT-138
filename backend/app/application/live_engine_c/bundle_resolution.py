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
from app.domain.live_engine_c.errors import LiveEngineCError
from app.domain.live_engine_c.types import Catalogue
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
