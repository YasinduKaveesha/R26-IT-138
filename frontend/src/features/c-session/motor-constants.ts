// Motor-constancy layout constants (SPEC section 10; Component C Phase 10 Sub-Phase Sequence v1.1
// section 5.1). These are the touch-target sizes, hit-slop, gesture thresholds and animation
// durations every archetype surface (10a...10h) must build against, and the guarantee is
// structural rather than measured: this module takes no input of any kind, so the mathematical
// level a task is set at cannot influence a touch target, because the level is not in scope where
// touch targets are defined. There is no function here to call with a level and no branch that
// could read one.
//
// The two line archetypes (line-position, line-traversal) are named in the sequence doc as where
// this would break by default: a fixed-width line rendered at a growing step count makes a later
// level a finer motor act than an earlier one. The fix is architectural, not tunable -- a constant
// per-step touch target, with the line scrolling or paginating rather than compressing -- and nothing
// below varies by any external input.
//
// c-motor-constants.test.ts asserts two things: every export here is a plain value, never a
// function; and this file's own source, with comments stripped, contains no reference to the level
// concept at all. The comment-stripping matters -- an earlier guard in this codebase
// (no-node-builtins-outside-tests-and-scripts.test.ts) was first written as a bare substring match
// and failed on its own explanatory comments, which is exactly the trap this paragraph is written
// to survive.

export const TOUCH_TARGET_MIN_SIZE = 48;

export const HIT_SLOP = { top: 8, bottom: 8, left: 8, right: 8 } as const;

// The unit-stepper's per-step control. Constant regardless of how many steps a task needs; when a
// line has more steps than fit at this size, it scrolls or paginates -- it never shrinks the step.
export const STEP_TOUCH_TARGET_SIZE = 56;

export const STEP_SPACING = 12;

export const GESTURE_LONG_PRESS_MS = 400;

export const ANIMATION_DURATION_MS = 200;
