// c-session-screen.tsx must key its <Surface> on the task instance, so React remounts the surface
// for every new task instead of reconciling a new task into the old component instance.
//
// WHY THIS IS A CORRECTNESS GUARD AND NOT A STYLE ONE. Every archetype surface keeps the child's
// in-progress answer in its own local state (10a's ordered-value-sequence holds `entryValues` and
// `order`), and none of it is derived from the task prop. Same element type in the same position
// with no key means React keeps the instance and swaps the prop, so the previous question's
// already-entered answer is still sitting in the input when the next question appears -- and can be
// submitted against it without ever being re-entered. Keying on the instance id makes the discard a
// consequence of mounting rather than a second mechanism that could itself be forgotten.
//
// WHAT THIS FILE CANNOT DO, STATED PLAINLY. It does not observe the remount. This project has no
// rendering library in devDependencies, so no test here can mount a component tree, drive a submit,
// and assert the input cleared. What is proven below is strictly that the source binds a key to a
// task-identifying wire field. That React remounts on a changed key is React's documented
// behaviour, relied on here and NOT verified by this project. The behavioural half remains
// unverified, and is a supervisor observation to make in a browser, not a claim this file supports.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const screenPath = resolve(here, '..', '..', 'features', 'c-session', 'c-session-screen.tsx');
const generatedTypesPath = resolve(here, '..', 'generated', 'openapi-types.ts');

/**
 * Comments stripped before any scan. The fix's own JSX comment explains the key at length and names
 * both `key` and `c_task_instance_id`, so a guard reading raw bytes would pass on a file whose
 * comment merely discusses the key while the element carries none -- the comment-stripping trap the
 * build-steps doc records this project hitting at least four times.
 */
function strippedSource(text: string): string {
  return text.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
}

/**
 * The field name a `<Surface ... />` element's `key` is bound to, or `null` when there is no
 * Surface element, no key on it, or a key bound to anything other than a `task.<field>` member
 * expression -- a string literal, a number, a loop index, or a call all yield `null`.
 *
 * This is the single predicate under test. The real file and every negative control below run
 * through it, so the controls exercise the guard itself rather than a lookalike of it.
 */
export function keyFieldOfSurfaceElement(source: string): string | null {
  const element = strippedSource(source).match(/<Surface\b[^>]*\/>/);
  if (!element) return null;

  const key = element[0].match(/\bkey=\{task\.([A-Za-z_][A-Za-z0-9_]*)\}/);
  return key ? key[1] : null;
}

// Fields that are present on a task but provably REPEAT across consecutive tasks, so a key bound to
// one of them would not change between questions and would therefore not remount -- the exact bug
// this batch fixes, reintroduced under the appearance of a key. A template id in particular repeats
// for every task drawn from the same template.
const NON_IDENTIFYING_FIELDS = [
  'game_task_template_id',
  'game_family_id',
  'skill_id',
  'representation_mode',
  'scaffold_state',
  'prompt_text',
];

test('the Surface element carries a key bound to a task field', () => {
  const field = keyFieldOfSurfaceElement(readFileSync(screenPath, 'utf8'));
  assert.notEqual(field, null, 'c-session-screen.tsx renders <Surface> with no task-bound key');
});

test('the key is bound to a field that actually exists on the wire response', () => {
  const field = keyFieldOfSurfaceElement(readFileSync(screenPath, 'utf8'));
  const generated = readFileSync(generatedTypesPath, 'utf8');
  // Declared as a required string in the generated contract types -- so the key is bound to a real
  // registry field, not to a name invented in the screen.
  assert.match(
    generated,
    new RegExp(`"${field}":\\s*string;`),
    `${field} is not a required string on the generated contract types`,
  );
});

test('the key is not bound to a field that repeats across tasks', () => {
  const field = keyFieldOfSurfaceElement(readFileSync(screenPath, 'utf8'));
  assert.ok(
    field !== null && !NON_IDENTIFYING_FIELDS.includes(field),
    `${field} repeats across consecutive tasks, so keying on it would not remount the surface`,
  );
});

// ---------------------------------------------------------------------------
// Negative controls. The guard must go RED on each of these, or it proves nothing about the real
// file. A guard exercised in only the passing direction is not a guard.
// ---------------------------------------------------------------------------

test('the guard fires on a Surface element with no key at all -- the pre-fix shape', () => {
  assert.equal(
    keyFieldOfSurfaceElement('<Surface onSubmit={submitFromSurface} task={task} />'),
    null,
  );
});

test('the guard fires on a key bound to a constant, an index, or a call', () => {
  assert.equal(keyFieldOfSurfaceElement('<Surface key="surface" task={task} />'), null);
  assert.equal(keyFieldOfSurfaceElement('<Surface key={0} task={task} />'), null);
  assert.equal(keyFieldOfSurfaceElement('<Surface key={index} task={task} />'), null);
  assert.equal(keyFieldOfSurfaceElement('<Surface key={"literal"} task={task} />'), null);
  assert.equal(keyFieldOfSurfaceElement('<Surface key={makeKey(task)} task={task} />'), null);
});

test('the guard fires when a comment merely discusses the key but the element carries none', () => {
  const commentOnly = [
    '/* keyed on key={task.c_task_instance_id} so the surface remounts */',
    '// key={task.c_task_instance_id}',
    '<Surface onSubmit={submitFromSurface} task={task} />',
  ].join('\n');
  assert.equal(keyFieldOfSurfaceElement(commentOnly), null);
});

test('the guard fires when there is no Surface element at all', () => {
  assert.equal(keyFieldOfSurfaceElement('const a = 1;'), null);
});

// The positive control: the same predicate must RECOGNISE a correctly keyed element. Without this,
// a predicate that returned null unconditionally would satisfy every control above.
test('the guard recognises a correctly keyed element, so it is not vacuously null', () => {
  assert.equal(
    keyFieldOfSurfaceElement('<Surface key={task.c_task_instance_id} onSubmit={s} task={task} />'),
    'c_task_instance_id',
  );
});

test('the guard rejects a key bound to a repeating field, through the real predicate', () => {
  const field = keyFieldOfSurfaceElement('<Surface key={task.game_task_template_id} task={task} />');
  assert.equal(field, 'game_task_template_id');
  assert.ok(NON_IDENTIFYING_FIELDS.includes(field), 'the repeating-field list would not catch it');
});
