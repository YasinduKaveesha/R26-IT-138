// AC 5: every malformed path renders fail-closed, each with a negative control proving the guard
// fires. Consolidates the fail-closed enumeration for `resolveOptionSelectSpec` beyond what
// c-option-select-logic.test.ts already covers per real template, by proving each guard is
// independently necessary (removing it, one at a time via a passing baseline, would let a bad shape
// through).

import { test } from 'node:test';
import assert from 'node:assert/strict';

import type { CNextTaskResponse } from '@/src/api/generated/openapi-types';
import { resolveOptionSelectSpec } from '@/src/features/c-session/archetypes/option-select-logic';

function validTask(): CNextTaskResponse {
  return {
    blanks: null,
    c_task_instance_id: 'task-1',
    difficulty_level: 3,
    game_family_id: 'C-GF-03',
    game_task_template_id: 'C-MCL-02',
    interactive_assets: {},
    prompt_payload: { left_count: 10, right_count: 27 },
    prompt_text: 'Choose which side has more, or say if they are equal.',
    representation_mode: 'TEST_FIXTURE_ONLY_REPRESENTATION',
    request_id: 'req-1',
    scaffold_state: 'C0',
    skill_id: 'number-sense',
    task_index: 1,
    technical_status: 'OK',
    valid_action_space: { selection: 'left|right|equal' },
  };
}

test('the valid baseline resolves (sanity check for every negative control below)', () => {
  assert.notEqual(resolveOptionSelectSpec(validTask()), null);
});

const NEGATIVE_CONTROLS: Array<{ name: string; mutate: (task: CNextTaskResponse) => void }> = [
  { name: 'prompt_text is an empty string', mutate: (t) => { t.prompt_text = ''; } },
  { name: 'prompt_payload is null', mutate: (t) => { (t as { prompt_payload: unknown }).prompt_payload = null; } },
  { name: 'prompt_payload is an empty object', mutate: (t) => { t.prompt_payload = {}; } },
  { name: 'prompt_payload contains a string value', mutate: (t) => { t.prompt_payload = { left_count: 10, right_count: 'many' }; } },
  { name: 'prompt_payload contains a boolean value', mutate: (t) => { t.prompt_payload = { left_count: 10, right_count: true }; } },
  { name: 'prompt_payload contains a non-finite number (NaN)', mutate: (t) => { t.prompt_payload = { left_count: Number.NaN, right_count: 27 }; } },
  { name: 'valid_action_space is empty', mutate: (t) => { t.valid_action_space = {}; } },
  { name: 'valid_action_space declares an unrecognised type', mutate: (t) => { t.valid_action_space = { selection: 'weird_type' }; } },
  { name: 'valid_action_space declares a pipe-string with fewer than two alternatives (single value, no "|")', mutate: (t) => { t.valid_action_space = { selection: 'left' }; } },
  { name: 'valid_action_space declares two exact-choice-control keys', mutate: (t) => { t.valid_action_space = { selection: 'left|right|equal', verdict: 'up|down' }; } },
  { name: 'valid_action_space declares only a bool key, no choice key', mutate: (t) => { t.valid_action_space = { exchange_performed: 'bool' }; } },
  { name: 'valid_action_space declares an extra key bound to a kind other than boolean-control', mutate: (t) => { t.valid_action_space = { selection: 'left|right|equal', groups: 'list[int]' }; } },
  { name: 'blanks is a positive integer instead of null', mutate: (t) => { t.blanks = 1; } },
];

for (const { name, mutate } of NEGATIVE_CONTROLS) {
  test(`fails closed: ${name}`, () => {
    const task = validTask();
    mutate(task);
    assert.equal(resolveOptionSelectSpec(task), null);
  });
}

test('fails closed on an entirely unknown template shape too (no template-id special-casing rescues it)', () => {
  const task = validTask();
  task.game_task_template_id = 'C-DOES-NOT-EXIST';
  task.valid_action_space = { some_key: 'unbound' };
  assert.equal(resolveOptionSelectSpec(task), null);
});

// --- the integer-field structural refusal (owner ruling 1/2, 2026-08-26) ---------------------------
// Proven here as a POSITIVE proof of refusal: an otherwise perfectly valid payload and action space,
// refused solely because the scene key binds to `integer-field`. This is the one guard this test
// suite proves by temporarily removing it and confirming the negative control goes red -- see the
// verification report for that run, not encoded in this file (removing the guard would require
// editing option-select-logic.ts itself, which this test does not do).

test('the integer-field path refuses even with an otherwise fully valid, all-numeric payload and action space', () => {
  const task = validTask();
  task.game_task_template_id = 'C-MCL-01';
  task.prompt_text = 'Choose the number that matches the amount shown.';
  task.prompt_payload = { numeral_options: [3, 5, 9], target_representation_value: 9 };
  task.valid_action_space = { selected_value: 'int' };
  assert.equal(resolveOptionSelectSpec(task), null);
});

test('a task otherwise identical but with a pipe-string action space (not integer-field) resolves normally (proves the refusal is keyed on the declared TYPE, not accidentally on something else about this shape)', () => {
  const task = validTask();
  task.prompt_payload = { numeral_options_count: 3 };
  task.valid_action_space = { verdict: 'yes|no' };
  const spec = resolveOptionSelectSpec(task);
  assert.notEqual(spec, null);
});

test('the integer-field refusal fires with no numeral_options key present at all (the refusal happens before any payload inspection for that key)', () => {
  const task = validTask();
  task.prompt_payload = { some_unrelated_value: 5 };
  task.valid_action_space = { selected_value: 'int' };
  assert.equal(resolveOptionSelectSpec(task), null);
});

test('the integer-field refusal fires regardless of key name (a synthetic differently-named int key refuses identically -- proves this is not a hardcoded key-name check)', () => {
  const task = validTask();
  task.prompt_payload = { numeral_options: [1, 2], other: 1 };
  task.valid_action_space = { chosen_answer: 'int' };
  assert.equal(resolveOptionSelectSpec(task), null);
});
