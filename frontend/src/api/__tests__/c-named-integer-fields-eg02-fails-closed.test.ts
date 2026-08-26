// C-EG-02 also resolves to `named-integer-fields` (registry.ts maps it there for 10g's own future
// use), so registering `named-integer-fields-surface.tsx` in SURFACE_TABLE this batch makes EG-02
// reachable before 10g has designed for it. This file pins down that it fails closed anyway --
// structurally, on its own wire shape, never on a template-id refusal -- and pins WHY, so the guard
// is not later "tidied away" as apparently redundant. See named-integer-fields-logic.ts's header,
// "C-EG-02 REACHES THIS ARCHETYPE AND FAILS CLOSED HERE, STRUCTURALLY".

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

import type { CNextTaskResponse } from '@/src/api/generated/openapi-types';
import { EXEMPLAR_ENTRIES } from '@/src/api/generated/c-prompt-exemplars';
import { resolveArchetype } from '@/src/features/c-session/archetypes/registry';
import { resolveNamedIntegerFieldsSpec } from '@/src/features/c-session/archetypes/named-integer-fields-logic';

const here = dirname(fileURLToPath(import.meta.url));

const EG02_ENTRIES = EXEMPLAR_ENTRIES.filter((entry) => entry.game_task_template_id === 'C-EG-02');

function makeTask(entry: (typeof EXEMPLAR_ENTRIES)[number]): CNextTaskResponse {
  return {
    blanks: entry.blanks,
    c_task_instance_id: 'task-1',
    difficulty_level: entry.difficulty_level,
    game_family_id: 'C-GF-07',
    game_task_template_id: entry.game_task_template_id,
    interactive_assets: entry.interactive_assets,
    prompt_payload: entry.prompt_payload,
    prompt_text: entry.prompt_text,
    representation_mode: 'TEST_FIXTURE_ONLY_REPRESENTATION',
    request_id: 'req-1',
    scaffold_state: 'C0',
    skill_id: 'number-sense',
    task_index: 1,
    technical_status: 'OK',
    valid_action_space: entry.valid_action_space,
  };
}

test('C-EG-02 has 5 exemplar rows and resolves to the named-integer-fields archetype id', () => {
  assert.equal(EG02_ENTRIES.length, 5);
  const entry = EG02_ENTRIES[0]!;
  assert.equal(resolveArchetype('C-EG-02', entry.valid_action_space), 'named-integer-fields');
});

// A surface IS registered for named-integer-fields by this batch -- EG-02 therefore genuinely
// reaches this resolver, not a missing-surface fail-closed. Checked by reading archetype-surfaces.ts
// as text rather than importing it: that module pulls in real React Native surface components, which
// esbuild/node --test cannot transform (react-native's own index.js uses Flow syntax), so every pure
// resolver test file in this project avoids importing it directly -- the same constraint
// game-catalogue.ts's own header documents for readinessOf.
test('archetype-surfaces.ts registers a SURFACE_TABLE entry for named-integer-fields (source check, not a runtime import)', () => {
  const source = readFileSync(
    resolve(here, '..', '..', 'features', 'c-session', 'archetype-surfaces.ts'),
    'utf-8',
  );
  assert.match(source, /'named-integer-fields':\s*NamedIntegerFieldsSurface/);
});

test('C-EG-02 nonetheless fails closed at every difficulty level, because its prompt_payload carries a non-number value (direction)', () => {
  for (const entry of EG02_ENTRIES) {
    const payload = entry.prompt_payload as Record<string, unknown>;
    assert.equal(typeof payload.direction, 'string', `level ${entry.difficulty_level}: expected direction to be a string in the real data`);
    const spec = resolveNamedIntegerFieldsSpec(makeTask(entry));
    assert.equal(spec, null, `C-EG-02 level ${entry.difficulty_level} should fail closed`);
  }
});

test("the refusal is structural (the numbers-only payload guard), not a game_task_template_id === 'C-EG-02' branch", () => {
  const task = makeTask(EG02_ENTRIES[0]!);
  // Strip the offending non-number key and confirm resolution would otherwise SUCCEED -- proving
  // the refusal traces to that one guard, not to template-id special-casing anywhere in the file.
  const { direction: _direction, ...numbersOnlyPayload } = task.prompt_payload as Record<string, unknown>;
  task.prompt_payload = numbersOnlyPayload;
  const spec = resolveNamedIntegerFieldsSpec(task);
  assert.notEqual(spec, null, 'with the non-number key removed, the same C-EG-02 task resolves fine -- proving no template-id refusal exists');
});
