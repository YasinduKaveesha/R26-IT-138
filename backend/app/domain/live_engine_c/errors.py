"""Stable internal/application errors for the Component C live-engine adapter (Phase 1 batch 1b).

The adapter never lets a package-internal exception type cross into
``app.application``/``app.api``. Every failure from the vendored package is translated into one
of these instead. The nine package exceptions translated here were verified present in the
installed wheel by direct inspection (not assumed): ``CatalogueValidationError``,
``SelectionInputError``, ``TaskGenerationTechnicalError``, ``UnsupportedTemplateError``,
``UnknownTemplateError``, ``NoEligibleRecoveryTemplateError``, ``RecoveryPreconditionError``,
``QLearningDisabledError``, ``UnknownPolicyModeError``.
"""

from __future__ import annotations


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
