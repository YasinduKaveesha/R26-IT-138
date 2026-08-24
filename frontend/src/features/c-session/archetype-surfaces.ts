// The archetype -> surface lookup. 10.0b-ii ships no archetype surface -- the eight identifiers
// registry.ts resolves name components that belong to 10a...10h -- so this module returns `null`
// for every archetype id today, unconditionally.
//
// It exists so the task loop (c-session-screen.tsx) can be built once, now: a later sub-phase
// populates one entry here and the loop does not change, because the loop already treats
// "resolved archetype, no surface registered" as a first-class case distinct from "unresolvable
// template" (c-session-logic.ts's `planTask` returns `{kind:'archetype'}` vs `{kind:'fail-closed'}`
// for exactly that reason). This file is an addition beyond 10.0b-ii's named file list; it is what
// makes that distinction real rather than a comment, and is called out as such in this batch's
// register entry.

import type { ComponentType } from 'react';

import type { CNextTaskResponse } from '@/src/api/generated/openapi-types';
import type { ArchetypeId } from '@/src/features/c-session/archetypes/registry';

export type ArchetypeSurfaceProps = {
  task: CNextTaskResponse;
  onSubmit: (payload: Record<string, unknown>) => void | Promise<void>;
};

/**
 * Resolve the rendering surface for one archetype id, or `null` if none is registered yet.
 * `null` here is what makes the task loop fall back to `FailClosedFrame` -- never a guessed or
 * partial rendering. Own-property-free by construction: this is a plain switch-less table lookup
 * against a fixed, closed union of eight ids, so there is no dynamic key and nothing for a
 * drifted or hostile id to resolve against.
 */
export function resolveArchetypeSurface(
  archetypeId: ArchetypeId,
): ComponentType<ArchetypeSurfaceProps> | null {
  void archetypeId;
  return null;
}
