"""FIXTURE — stands in for a future B-owned producer that would emit the seven mastery values at
real B session completion (Phase 4 work order, planning item 6, ratified verbatim in the
implementation work order: "Keep that docstring wording — it was correct, including the explicit
refusal to claim P(L) parity.").

That producer does not exist: it is blocked on GATE-B (the safe-progress policy, unresolved).
This fixture supplies contract-shaped values for Phase 4's session-lifecycle wiring only; it is
NOT a P(L) passthrough and makes no claim that BKT P(L) (``b_learner_skill_states.p_l``) and
``BToCMasteryPayload.mastery_*`` are the same quantity — that is an unsigned scientific question
neither this fixture nor its caller may answer.

HARD LINE: this module reads NOTHING from ``b_learner_skill_states`` or any other B-private
table. Reading it would not be a fixture — it would silently make Component C the de-facto
producer of B's own mastery estimate and cross a component boundary with no gate (the work
order's own words: "worse than the fixture... exactly the C-4-in-a-new-costume failure").
"""

from __future__ import annotations

from typing import Mapping

# The seven frozen skill names (models.contracts.SKILLS), fixed at 0.5 (a neutral, uninformative
# midpoint -- not derived from any B computation, not a claim about any real learner).
FIXTURE_MASTERY_BY_SKILL: Mapping[str, float] = {
    "counting": 0.5,
    "number_sense": 0.5,
    "place_value": 0.5,
    "addition": 0.5,
    "subtraction": 0.5,
    "multiplication": 0.5,
    "division": 0.5,
}


def fixture_b_mastery_payload_for_phase_4() -> Mapping[str, float]:
    """Returns the FIXTURE seven-value mastery mapping (see module docstring). Callers must still
    supply real B identity fields (student_id, intervention_session_id,
    intervention_session_number) themselves -- this function never invents those (G3)."""
    return dict(FIXTURE_MASTERY_BY_SKILL)
