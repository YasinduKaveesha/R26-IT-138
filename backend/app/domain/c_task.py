"""Public contracts for Component C's task-serving endpoints (Phase 5).

Mirrors ``app.domain.c_session``'s discipline exactly (X-4, allow-list construction -- named
fields only, never a serialised model with fields subtracted, never ``**record.__dict__``).

PRIVATE/PUBLIC SPLIT (Phase 5 work order P2, S3): the following ``c_task_instances`` columns are
NEVER exposed here, regardless of their status at the database-allow-list layer
(``AUTHORIZED_C_COLUMN_EXCEPTIONS`` governs whether a column may legitimately EXIST and hold
private content -- it says nothing about HTTP exposure; Phase 4b established this distinction
with ``mastery_context_mode`` and it applies with full force here):
  - ``correct_answer_payload`` -- the secret itself. Never public, under any name, ever.
  - ``correctness_function_id`` -- evaluator internals (P1-d).
  - ``c_task_opportunities.mastery_selected_skill`` -- the raw mastery float feeding the
    initial-difficulty formula (C-17). A real, B-mastery-derived scientific value; never public.
  - ``c_task_opportunities.mastery_context_mode`` -- same R-1 reasoning as ``c_sessions``:
    derivable client-side from ``session_mode`` alone, never re-exposed.
  - SIX COLUMNS RULED PRIVATE (S3, all six, no case-by-case judgment): ``curriculum_node_id``,
    ``functional_role``, ``completion_condition``, ``failure_condition``, ``terminal_reason``,
    ``difficulty_vector``. "Adding a field later is additive; removing one is breaking -- the
    conservative direction is the reversible one." Rendering data travels via
    ``prompt_payload``/``interactive_assets``, which is what makes ``difficulty_vector`` private
    rather than a judgment call (owner's own words).
  - ``template_version``, ``catalogue_version``, ``generator_version``, every ``seed_lineage_*``
    column -- governance/audit metadata, mirrors B's own ``project_task_instance_to_presentation``
    precedent (``b_opportunity.py``) excluding the equivalent fields.
  - ``student_id``, ``c_session_id`` on the instance -- already known from the session context
    (auth + path param); re-exposing invites the same class of bug R-5 fixed for B's identity.

PROMPT_PAYLOAD/INTERACTIVE_ASSETS ARE PUBLIC BUT PER-TEMPLATE (P3). This is necessarily what the
child is shown, and its safety was verified per-template by the Phase 5 leak-test loop (S5) --
NOT proven here by any static analysis. A template whose prompt embeds a partially-worked example
containing the final answer would be a real leak in these two fields specifically, not a naming
defect this module could catch.

R-6 (SUPERVISOR RULING, Phase 5 continuation): ``CSubmitActionResult``'s verdict field is named
``response_matched``, not ``is_correct``. Regenerating the frozen contract surfaced that
``is_correct`` contains the substring "correct", tripping BE5a's ``FORBIDDEN_FIELD_TERMS`` guard
(``tests/test_be5a_contract_freeze.py``, no allow-list mechanism, not modified here). This is NOT
a rename invented to dodge the guard (the exact pattern R-H already condemned once) -- it adopts
the name of the REVIEWED, ALREADY-FROZEN sibling field for this identical semantic:
``app/domain/b_attempt.py:34``, ``AttemptResponseFields.response_matched``. B's field is typed
``bool | None`` (``None`` for a ``TIMEOUT`` event kind, where no comparison ever happened); this
field stays plain ``bool`` -- a submitted action that reached this response has always been
evaluated, so there is no "no verdict yet" state to represent here. That typing divergence is
deliberate, not an oversight.
"""

from typing import Any, Mapping
from uuid import UUID

from app.domain.c_session import StrictModel


class CTaskFields(StrictModel):
    c_task_instance_id: UUID
    game_family_id: str
    game_task_template_id: str
    task_index: int
    skill_id: str
    difficulty_level: int
    representation_mode: str
    prompt_payload: Mapping[str, Any]
    interactive_assets: Mapping[str, Any]
    valid_action_space: Mapping[str, str]
    scaffold_state: str
    technical_status: str


class CNextTaskResponse(CTaskFields):
    request_id: str


class CSubmitActionResult(StrictModel):
    c_task_instance_id: UUID
    response_matched: bool
    request_id: str
