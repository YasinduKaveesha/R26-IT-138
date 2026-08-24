// The archetype -> surface lookup. 10.0b-ii shipped no archetype surface -- the eight identifiers
// registry.ts resolves name components that belong to 10a...10h -- so this module returned `null`
// for every archetype id. 10a populates the first entry.
//
// It exists so the task loop (c-session-screen.tsx) can be built once: a later sub-phase populates
// one entry here and the loop does not change, because the loop already treats "resolved
// archetype, no surface registered" as a first-class case distinct from "unresolvable template"
// (c-session-logic.ts's `planTask` returns `{kind:'archetype'}` vs `{kind:'fail-closed'}` for
// exactly that reason).

import type { ComponentType } from 'react';

import type { CNextTaskResponse } from '@/src/api/generated/openapi-types';
import type { ArchetypeId } from '@/src/features/c-session/archetypes/registry';
import { OrderedValueSequenceSurface } from '@/src/features/c-session/archetypes/ordered-value-sequence-surface';

export type ArchetypeSurfaceProps = {
  task: CNextTaskResponse;
  onSubmit: (payload: Record<string, unknown>) => void | Promise<void>;
};

const SURFACE_TABLE: Partial<Record<ArchetypeId, ComponentType<ArchetypeSurfaceProps>>> = {
  'ordered-value-sequence': OrderedValueSequenceSurface,
};

/**
 * Resolve the rendering surface for one archetype id, or `null` if none is registered yet.
 * `null` here is what makes the task loop fall back to `FailClosedFrame` -- never a guessed or
 * partial rendering. Own-property lookup against a fixed, closed union of eight ids: `archetypeId`
 * is a value this codebase produces (ArchetypeId), never a wire string, but the same discipline is
 * kept here rather than relying on that.
 */
export function resolveArchetypeSurface(
  archetypeId: ArchetypeId,
): ComponentType<ArchetypeSurfaceProps> | null {
  if (!Object.prototype.hasOwnProperty.call(SURFACE_TABLE, archetypeId)) return null;
  return SURFACE_TABLE[archetypeId] ?? null;
}
