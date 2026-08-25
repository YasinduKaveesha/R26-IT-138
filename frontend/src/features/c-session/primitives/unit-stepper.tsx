// The shared discrete position control (10c), built once for both `line-traversal` (this
// sub-phase) and 10d's `line-position` to compose over unmodified (master work order §5A: "Build
// the stepping primitive once; `line-position` and `line-traversal` are two thin compositions over
// it, not two separate designs").
//
// RULING 6.3, not a builder's choice: discrete integer stepping, never continuous drag. One step is
// one unit at every difficulty; the per-step touch target is a constant (STEP_TOUCH_TARGET_SIZE /
// STEP_SPACING, motor-constants.ts); when a line has more ticks than fit on screen, it scrolls --
// it never compresses a tick to fit more of them. This mirrors `value-token-row.tsx`'s own
// `reorder` mode, which scrolls horizontally rather than shrinking a token, and
// `digit-keypad.tsx`'s stepper-vs-keypad ruling: interaction COST (here, step count) is allowed to
// track the task's own magnitude; interaction SIZE never is.
//
// Stateless: the caller (the archetype surface) owns `position`; this component only ever reports
// "step forward" / "step back" intents and renders whatever position it is given. It holds no
// state of its own about the line's origin or the child's progress, matching `DigitKeypad`'s own
// "holds no state of its own" doctrine.
//
// The line itself is DISPLAY ONLY -- individual ticks are not pressable. Making a tick itself the
// tap target would let a child jump straight to any position rather than making the successive
// unit jumps `jump-accumulator.tsx` needs to record one by one, and would reopen exactly the
// imprecise-placement question ruling 6.3 already closed for continuous drag.

import { useEffect, useRef } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';

import { AppText } from '@/src/components/app-text';
import { GESTURE_LONG_PRESS_MS, HIT_SLOP, STEP_SPACING, STEP_TOUCH_TARGET_SIZE } from '@/src/features/c-session/motor-constants';
import { colors, radius, typography } from '@/src/theme/tokens';

const TICK_STRIDE = STEP_TOUCH_TARGET_SIZE + STEP_SPACING;

// A LAYOUT bound on how many forward ticks the line ever renders, not a catalogue constraint and
// never derived from any payload value (deriving it from the addends would make the line's own
// extent leak the answer -- see line-traversal-logic.ts's header). The generator's real maximum
// forward-jump count across every difficulty level of C-JB-02 is `min(addend_a, addend_b)`, which
// tops out at 18 (magnitude_a_by_level's own difficulty-5 bound in generation_config.py). 30 is
// comfortably above that while still catching a materially corrupted `position` before it renders
// an unbounded number of ticks.
const MAX_LINE_FORWARD_STEPS = 30;

export type UnitStepperProps = {
  /** Where the line begins. Rendered as the first tick, never itself steppable past backward. */
  originValue: number;
  /** How many forward unit steps have been taken so far -- the caller's own state, not derived. */
  forwardSteps: number;
  disabled?: boolean;
  onStepForward: () => void;
  onStepBack: () => void;
};

export function UnitStepper({ disabled = false, forwardSteps, onStepBack, onStepForward, originValue }: UnitStepperProps) {
  const scrollRef = useRef<ScrollView>(null);
  const position = originValue + forwardSteps;

  // Keeps the marker on screen as it advances -- the direct lesson of the entry-slot-off-screen
  // finding this project already hit once (10a, difficulty 5): a control that can grow past the
  // visible area must actively keep its own moving part in view, not rely on the child to notice
  // and scroll manually.
  useEffect(() => {
    const targetX = Math.max(0, forwardSteps * TICK_STRIDE - TICK_STRIDE);
    scrollRef.current?.scrollTo({ x: targetX, animated: true });
  }, [forwardSteps]);

  const canStepBack = forwardSteps > 0 && !disabled;
  const canStepForward = forwardSteps < MAX_LINE_FORWARD_STEPS && !disabled;

  return (
    <View>
      <ScrollView
        horizontal
        ref={scrollRef}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.line}>
        {Array.from({ length: MAX_LINE_FORWARD_STEPS + 1 }, (_, tickIndex) => {
          const tickValue = originValue + tickIndex;
          const isMarker = tickIndex === forwardSteps;
          return (
            <View key={tickIndex} style={styles.tickColumn}>
              <View style={[styles.tick, isMarker && styles.tickMarked]}>
                {isMarker ? <View style={styles.marker} /> : null}
              </View>
              <AppText style={styles.tickLabel}>{tickValue}</AppText>
            </View>
          );
        })}
      </ScrollView>
      <View style={styles.controls}>
        <Pressable
          accessibilityLabel="jump forward one"
          accessibilityRole="button"
          accessibilityState={{ disabled: !canStepForward }}
          delayLongPress={GESTURE_LONG_PRESS_MS}
          disabled={!canStepForward}
          hitSlop={HIT_SLOP}
          onPress={onStepForward}
          style={({ pressed }) => [
            styles.controlButton,
            !canStepForward && styles.controlButtonDisabled,
            pressed && canStepForward && styles.pressed,
          ]}>
          <AppText style={styles.controlButtonText}>▲ jump +1</AppText>
        </Pressable>
        <Pressable
          accessibilityLabel="step back one"
          accessibilityRole="button"
          accessibilityState={{ disabled: !canStepBack }}
          delayLongPress={GESTURE_LONG_PRESS_MS}
          disabled={!canStepBack}
          hitSlop={HIT_SLOP}
          onPress={onStepBack}
          style={({ pressed }) => [
            styles.controlButton,
            !canStepBack && styles.controlButtonDisabled,
            pressed && canStepBack && styles.pressed,
          ]}>
          <AppText style={styles.controlButtonText}>▼ back</AppText>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  controlButton: {
    alignItems: 'center',
    backgroundColor: colors.accentGreen,
    borderColor: colors.accentGreen,
    borderRadius: radius.md,
    borderWidth: 2,
    justifyContent: 'center',
    minHeight: STEP_TOUCH_TARGET_SIZE,
  },
  controlButtonDisabled: { opacity: 0.5 },
  controlButtonText: {
    color: colors.surface1,
    fontFamily: typography.fonts.bold,
    fontSize: typography.fontSize.body,
  },
  // Stacked vertically -- jump forward above, back below (2026-08-26 request) -- rather than
  // side-by-side, with up/down arrows matching that stacking direction.
  controls: {
    flexDirection: 'column',
    gap: STEP_SPACING,
    marginTop: STEP_SPACING,
  },
  line: {
    alignItems: 'center',
    gap: STEP_SPACING,
    paddingVertical: STEP_SPACING,
  },
  marker: {
    backgroundColor: colors.primary,
    borderRadius: radius.pill,
    height: STEP_TOUCH_TARGET_SIZE * 0.5,
    width: STEP_TOUCH_TARGET_SIZE * 0.5,
  },
  pressed: { opacity: 0.72 },
  tick: {
    alignItems: 'center',
    backgroundColor: colors.surface1,
    borderColor: colors.border,
    borderRadius: radius.pill,
    borderWidth: 2,
    height: STEP_TOUCH_TARGET_SIZE,
    justifyContent: 'center',
    width: STEP_TOUCH_TARGET_SIZE,
  },
  tickColumn: {
    alignItems: 'center',
    gap: 4,
  },
  tickLabel: {
    color: colors.textSecondary,
    fontFamily: typography.fonts.body,
    fontSize: typography.fontSize.xs,
  },
  tickMarked: {
    borderColor: colors.primary,
  },
});
