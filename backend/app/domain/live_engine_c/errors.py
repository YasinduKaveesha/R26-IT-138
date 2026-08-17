"""Stable internal/application errors for the Component C live-engine adapter (Phase 1 batch 1b).

The adapter never lets a package-internal exception type cross into
``app.application``/``app.api``. Every failure from the vendored package is translated into one
of these instead. The nine package exceptions translated here were verified present in the
installed wheel by direct inspection (not assumed): ``CatalogueValidationError``,
``SelectionInputError``, ``TaskGenerationTechnicalError``, ``UnsupportedTemplateError``,
``UnknownTemplateError``, ``NoEligibleRecoveryTemplateError``, ``RecoveryPreconditionError``,
``QLearningDisabledError``, ``UnknownPolicyModeError``.

VALIDATORS BATCH adds a tenth: ``MasteryPayloadContractValidationError``, translating
``validators.contract_validators.ContractValidationError`` (now shipped in B's wheel at
0.1.0+bf5.09267ab; see backend/provenance/component-b-live-engine-manifest.json's
validators_widened_closure). Same translation pattern as the nine above -- a package exception
type must never cross the X-3 boundary into app.domain.
"""

from __future__ import annotations

from typing import Sequence, Tuple


class LiveEngineCError(Exception):
    """Base type for every stable error raised by the Component C live-engine adapter."""


class CatalogueUnavailableError(LiveEngineCError):
    """The governed catalogue could not be loaded or failed a load-time invariant.

    Translates ``component_c_generator.catalogue.loader.CatalogueValidationError``.
    """


class SelectionInputError(LiveEngineCError):
    """Translates ``component_c_generator.selection.selector.SelectionInputError`` — a fail-closed
    rejection of a wrong or missing ``session_phase``, a B payload supplied in ``c_only`` mode, a
    ``mastery_driven`` phase without a payload, or a ``student_id`` mismatch (v3.0 §7.1)."""


class TaskGenerationTechnicalError(LiveEngineCError):
    """Translates ``component_c_generator.generation.TaskGenerationTechnicalError``."""


class UnsupportedTemplateError(LiveEngineCError):
    """Translates ``component_c_generator.generation.UnsupportedTemplateError``."""


class UnknownTemplateError(LiveEngineCError):
    """Translates ``component_c_generator.evaluation.UnknownTemplateError``."""


class NoEligibleRecoveryTemplateError(LiveEngineCError):
    """Translates ``component_c_generator.scaffolds.recovery.NoEligibleRecoveryTemplateError``."""


class RecoveryPreconditionError(LiveEngineCError):
    """Translates ``component_c_generator.scaffolds.recovery.RecoveryPreconditionError``."""


class QLearningDisabledError(LiveEngineCError):
    """Translates ``component_c_generator.policy.rule_based.QLearningDisabledError`` — raised by
    ``decide_adaptation`` for any ``policy_mode`` other than ``rule_based_baseline`` (v3.0 §7.3:
    Q-learning stays ``EXPERIMENTAL_ONLY``)."""


class UnknownPolicyModeError(LiveEngineCError):
    """Translates ``component_c_generator.policy.rule_based.UnknownPolicyModeError``."""


class MasteryPayloadContractValidationError(LiveEngineCError):
    """Translates ``validators.contract_validators.ContractValidationError`` — raised by
    ``validate_payload(payload, "b_to_c")`` when a mastery payload carries a prohibited field or
    fails the frozen ``BToCMasteryPayload`` contract's own validation (VALIDATORS BATCH).

    Phase 4 work order, Q2: mastery values are exactly what C must never expose to a client, and
    a raw ``str(exc)`` of a pydantic ``ValidationError`` echoes the rejected INPUT VALUE back
    (verified: pydantic's ``errors()`` entries carry an ``input`` key, and its default ``__str__``
    renders it). This type therefore never carries ``str(exc)`` in its message and instead carries
    ``field_errors`` — a tuple of ``(loc_path, error_type_code)`` pairs extracted from the
    package's chained ``pydantic.ValidationError`` (via ``__cause__``), or an empty tuple when no
    such chain exists (e.g. a prohibited-field rejection, which is caught by exact field NAME
    already, no reconstruction needed). ``loc_path`` is a tuple of field-path segments (strings/
    ints); ``error_type_code`` is pydantic's short type string (e.g. ``"string_pattern_mismatch"``,
    ``"float_parsing"``) — NEVER the human-readable ``msg`` (which can itself embed the input for
    some error types) and NEVER the ``input`` value itself."""

    def __init__(self, field_errors: Sequence[Tuple[Tuple[object, ...], str]] = ()) -> None:
        self.field_errors: Tuple[Tuple[Tuple[object, ...], str], ...] = tuple(field_errors)
        rendered = ", ".join(f"{list(loc)}: {code}" for loc, code in self.field_errors) or "b_to_c payload rejected"
        super().__init__(rendered)


class SelectionConfigurationMissingError(LiveEngineCError):
    """Phase 4b, owner condition 1: "If the loader structurally requires a field to be present,
    it is labelled and the code path consuming W must refuse to run rather than proceed on a
    placeholder. Fail-closed means halt, not default." Raised when a code path needs
    ``SelectionConfig`` and the resolved ``CRuntimeBundle.selection_configuration`` is ``None``
    (additive-only means this is a real, expected state for any bundle not yet republished with
    the block, B1-b) -- never defaulted, never substituted."""


class SF043OrderingError(LiveEngineCError):
    """Phase 4: the SF-043 ordering gate at session creation -- "B runs -> B completes ->
    B emits seven mastery values -> C validates the same-session payload -> C begins." Raised
    when a ``combined`` session is requested with no mastery payload supplied, or a ``c_only``
    session is requested WITH one (c_only must never receive, query, cache, or infer a B
    payload). Distinct from ``MasteryPayloadContractValidationError`` (a present but
    contract-invalid payload) and from the package's own ``SelectionInputError`` (translated only
    at the ``select_task`` chokepoint, Phase 5) -- this is the ordering check Phase 4 itself owns,
    enforced before any session row is ever created."""
