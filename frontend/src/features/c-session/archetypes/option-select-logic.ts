// Pure resolution logic for the `option-select` archetype (10d). No React/React Native import in
// this file -- the surface (option-select-surface.tsx) is a thin layer over this, mirroring
// `value-report-logic.ts`'s and `line-traversal-logic.ts`'s own split.
//
// `option-select`'s real registry rows split into two genuinely different option sources
// (10d work order, §KEY SETS):
//   - a pipe-string `valid_action_space` value (`exact-choice-control`, field-kinds.ts) whose own
//     parsed alternatives ARE the options -- e.g. `left|right|equal`, `<|>|=`;
//   - an `int`-typed key (`integer-field`) whose options are a `prompt_payload`-borne numeral array
//     (`numeral_options`), and whose submitted value is one of those numbers.
//
// THIS BATCH BUILDS THE FIRST SOURCE ONLY. See the REFUSAL block below for why the second is not a
// missing feature but a structural refusal, decided by owner ruling (2026-08-26), not a builder
// choice deferred for convenience.
//
// WHY THE `integer-field` PATH IS REFUSED, NOT BUILT. `value-report-logic.ts`'s payload numbers are
// OPERANDS -- the answer is computed from them, so showing them is never showing the answer. Here
// the payload number this path would need to display (`target_representation_value` for one real
// template, `set_size` for another -- names withheld deliberately, see below) IS ITSELF one of the
// numbers in the option list, i.e. the correct answer. Re-verified directly against every real
// exemplar this owns (all five difficulty levels, both templates that would hit this path): the
// "other" payload key's value is always present, unmodified, inside `numeral_options` at every
// level. Rendering it as a read-only numeral token -- the only rendering this archetype's other
// path knows how to do -- would put the answer on screen, the same class of defect
// `line-traversal-logic.ts`'s header exists to prevent ("it never adds the addends together...
// would put the answer on screen").
//
// It cannot simply be omitted from the screen either: every real `prompt_text` on this path is
// deictic ("the amount shown", "Count the objects...") and `interactive_assets` is `{}` at every
// level, so the quantity these templates ask about can only be shown honestly as a QUANTITY OF
// OBJECTS (a picture, a count of dots) -- and no such rendering primitive exists in this codebase.
// Building one is explicitly out of this batch's scope (10d work order §PRE-FLIGHT-adjacent
// STOP-AND-REPORT, not a design task here).
//
// This refusal is deliberately NOT a template-id blocklist (contrast `value-report-logic.ts`'s
// explicit, named `C-TC-02` exclusion): it is keyed on the declared TYPE alone (`integer-field`),
// so it refuses every template that would ever reach this path -- known or future -- with the same
// single check, and self-deletes the day a quantity-as-objects renderer is approved and built,
// rather than requiring a growing list of excluded ids. Per the two-layer rule, no template id is
// named anywhere in this file.
//
// All `prompt_payload` / `valid_action_space` access goes through
// `Object.prototype.hasOwnProperty.call(...)` / `Object.keys(...)`, never bare property access:
// both objects originate on the wire, and a key named `constructor`, `toString` or `__proto__`
// resolves to an inherited `Object.prototype` member under bare access.

import type { CNextTaskResponse } from '@/src/api/generated/openapi-types';
import { bindFieldKind, type FieldKindBinding } from '@/src/features/c-session/archetypes/field-kinds';
import { labelForPayloadKey } from '@/src/features/c-session/archetypes/payload-value-labels';

export type OptionSelectExtraField = {
  key: string;
  binding: FieldKindBinding;
};

export type OptionSelectPayloadValue = {
  key: string;
  label: string;
  value: number;
};

export type OptionSelectSpec = {
  promptText: string;
  /** Every declared `prompt_payload` key, in the wire's own key order -- there is no option-source
   * key to exclude on this path, since the options come from the pipe-string itself, not the
   * payload. */
  payloadValues: readonly OptionSelectPayloadValue[];
  /** The one `exact-choice-control` key -- where the child's choice is submitted. */
  scoreKey: string;
  /** The pipe-string's own parsed alternatives (field-kinds.ts guarantees at least two). */
  alternatives: readonly string[];
  extraFields: readonly OptionSelectExtraField[];
  interactiveAssets: Record<string, unknown>;
};

/**
 * Resolve one task's `option-select` rendering spec, or `null` if resolution cannot proceed. `null`
 * here is what drives `FailClosedFrame` in the surface -- never a guessed rendering, never a
 * partial one.
 *
 * Fails closed for: `prompt_text` absent or empty; `prompt_payload` absent, not an object, empty,
 * or containing any value that is not a finite number (this is the ONLY thing holding the
 * non-numeric-payload templates on this path shut -- see the file header's own note on why it must
 * never be relaxed to skip or tolerate a non-numeric value); `valid_action_space` declaring no key;
 * a declared type this codebase does not bind (field-kinds.ts); ANY key bound to `integer-field`
 * (the structural refusal, see header -- fires before this function looks at `prompt_payload` at
 * all for that key); a declared-type count of `exact-choice-control` keys other than exactly one;
 * any other declared key whose bound kind is not `boolean-control`; `task.blanks` not exactly
 * `null`.
 */
export function resolveOptionSelectSpec(task: CNextTaskResponse): OptionSelectSpec | null {
  if (typeof task.prompt_text !== 'string' || task.prompt_text.length === 0) return null;

  const promptPayload = task.prompt_payload;
  if (typeof promptPayload !== 'object' || promptPayload === null) return null;

  const payloadKeys = Object.keys(promptPayload);
  if (payloadKeys.length === 0) return null;
  const payloadValues: OptionSelectPayloadValue[] = [];
  for (const key of payloadKeys) {
    const value = (promptPayload as Record<string, unknown>)[key];
    if (typeof value !== 'number' || !Number.isFinite(value)) return null;
    payloadValues.push({ key, label: labelForPayloadKey(key), value });
  }

  const validActionSpace = task.valid_action_space;
  const keys = Object.keys(validActionSpace);
  if (keys.length === 0) return null;

  let scoreKey: string | null = null;
  let alternatives: readonly string[] | null = null;
  const extraFields: OptionSelectExtraField[] = [];

  for (const key of keys) {
    const declaredType = validActionSpace[key];
    const binding = bindFieldKind(declaredType);
    if (binding === null) return null;

    // The structural refusal (see header) -- keyed on declared TYPE alone, never a template id.
    if (binding.kind === 'integer-field') return null;

    if (binding.kind === 'exact-choice-control') {
      if (scoreKey !== null) return null;
      scoreKey = key;
      alternatives = binding.alternatives;
      continue;
    }

    if (binding.kind !== 'boolean-control') return null;
    extraFields.push({ key, binding });
  }

  if (scoreKey === null || alternatives === null) return null;
  if (task.blanks !== null) return null;

  return {
    promptText: task.prompt_text,
    payloadValues,
    scoreKey,
    alternatives,
    extraFields,
    interactiveAssets: task.interactive_assets,
  };
}
