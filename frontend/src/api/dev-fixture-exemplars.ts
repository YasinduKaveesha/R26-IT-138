// Development-fixture-only. Reads the frozen prompt-exemplar artefact directly off disk, via the
// same `node:fs` + `import.meta.url`-relative resolution c-prompt-exemplars-freeze.test.ts uses,
// so the dev fixture's nextTask can relay a real generator-produced task rather than inventing
// content -- per owner ruling (10.0-work-order.md §3, "Owner rulings applied, 2026-08-24").
//
// ARCHITECTURAL RISK, disclosed rather than silently assumed working: this module is reached only
// from createFixtureApi's nextTask in component-c-api.ts, itself reachable only when
// EXPO_PUBLIC_APP_ENV=development and EXPO_PUBLIC_COMPONENT_C_DEV_FIXTURE is set. It has been
// exercised only under `npm run test:contract` (plain Node via the `tsx` loader -- see
// package.json's script), which is this whole batch's stated verification surface ("provable by
// npm run test:contract alone"). It has NOT been verified to survive Metro bundling for a real
// `expo start` or build: Node's `fs` module has no React Native / Hermes equivalent, and if Metro
// statically resolves this import at bundle time rather than only at the point nextTask actually
// runs, bundling could fail even for builds that never activate the fixture. This batch does not
// run expo or any build (out of scope), so that risk is recorded here rather than tested. It
// belongs on the register as the first thing to check before anyone runs the dev-gated app
// against a served task.

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

export type ExemplarEntry = {
  game_task_template_id: string;
  difficulty_level: number;
  prompt_payload: Record<string, unknown>;
  interactive_assets: Record<string, unknown>;
  valid_action_space: Record<string, string>;
};

type RegistryEntry = { template_id: string; valid_action_space: Record<string, string> };

const here = dirname(fileURLToPath(import.meta.url));
// frontend/src/api -> frontend/src -> frontend -> Dev (repo root), matching the freeze tests'
// own resolution one directory shallower (they resolve from frontend/src/api/__tests__).
const repoRoot = resolve(here, '..', '..', '..');
const exemplarsPath = resolve(repoRoot, 'backend', 'contract', 'c-prompt-exemplars.json');
const registryPath = resolve(repoRoot, 'backend', 'contract', 'c-template-registry.json');

/**
 * Deterministic, artefact-driven pick of exactly one exemplar: the alphabetically-first template
 * id in the registry, at difficulty_level 1. Never a hardcoded template id -- if a future
 * registry regeneration changes which id sorts first, this fixture moves with it rather than
 * silently serving a stale choice. No new fixture-scenario string is introduced; nothing
 * configures which task is served.
 */
export function loadFixtureTaskExemplar(): ExemplarEntry {
  const registry: RegistryEntry[] = JSON.parse(readFileSync(registryPath, 'utf-8'));
  const exemplars: { entries: ExemplarEntry[] } = JSON.parse(readFileSync(exemplarsPath, 'utf-8'));

  const sortedIds = registry.map((entry) => entry.template_id).sort();
  const firstTemplateId = sortedIds[0];

  const entry = exemplars.entries.find(
    (candidate) => candidate.game_task_template_id === firstTemplateId && candidate.difficulty_level === 1,
  );
  if (!entry) {
    throw new Error(
      `Development fixture: no exemplar entry found for ${firstTemplateId} at difficulty_level 1.`,
    );
  }
  return entry;
}
