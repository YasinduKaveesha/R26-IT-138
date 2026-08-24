// The shared token-row primitive (Phase 10 Sub-Phase Sequence v1.1 §3.2): "ordered/reorderable
// integer tokens", bound to `list[int]`. Two modes, selected by the caller, never inferred here:
//   - `display-with-entry`: fixed, read-only tokens from the server's `shown_sequence`, followed by
//     `blanks` editable slots the child fills via `DigitKeypad`. Used by `ordered-value-sequence`'s
//     entry scene (NP-01/02/03).
//   - `reorder`: every token is the same draggable control, and the child's on-screen order IS the
//     value. Used by `ordered-value-sequence`'s arrangement scene (NP-04).
//
// Built only for what `ordered-value-sequence` needs. `partition-allocation` (10g/10h) reuses this
// component unmodified per the sequence doc; no partition-allocation-specific behaviour (bin
// labels, totals, etc.) lives here.
//
// Motor constancy: every token's size and spacing is TOKEN_TOUCH_TARGET_SIZE / TOKEN_SPACING
// (motor-constants.ts) -- module-level constants, never a function of how many tokens this row
// happens to render. When a row would overflow the available width it scrolls horizontally; it
// never shrinks a token to fit more of them, mirroring section 5.1's line-archetype ruling and B's
// prompt-visual registry's own layout-bound doctrine.

import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, {
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';

import { AppText } from '@/src/components/app-text';
import { DigitKeypad } from '@/src/features/c-session/primitives/digit-keypad';
import {
  ANIMATION_DURATION_MS,
  GESTURE_LONG_PRESS_MS,
  HIT_SLOP,
  TOKEN_SPACING,
  TOKEN_TOUCH_TARGET_SIZE,
} from '@/src/features/c-session/motor-constants';
import { colors, radius, typography } from '@/src/theme/tokens';

const TOKEN_STRIDE = TOKEN_TOUCH_TARGET_SIZE + TOKEN_SPACING;

type DisplayWithEntryProps = {
  mode: 'display-with-entry';
  shownSequence: readonly number[];
  blanks: number;
  disabled?: boolean;
  // One entry per blank slot: the integer the child has composed there, or `null` while empty.
  // The caller (the surface) owns this state; this component reports composition, it does not
  // decide submittability.
  entryValues: readonly (number | null)[];
  onChangeEntryValues: (next: readonly (number | null)[]) => void;
};

type ReorderProps = {
  mode: 'reorder';
  values: readonly number[];
  disabled?: boolean;
  onChangeOrder: (next: readonly number[]) => void;
};

export type ValueTokenRowProps = DisplayWithEntryProps | ReorderProps;

export function ValueTokenRow(props: ValueTokenRowProps) {
  if (props.mode === 'display-with-entry') return <DisplayWithEntryRow {...props} />;
  return <ReorderRow {...props} />;
}

// --- display-with-entry -----------------------------------------------------------------------

function DisplayWithEntryRow({
  blanks,
  disabled = false,
  entryValues,
  onChangeEntryValues,
  shownSequence,
}: DisplayWithEntryProps) {
  const [focusedSlot, setFocusedSlot] = useState(0);
  // Per-slot digit buffer, independent of the parsed integer the caller holds -- this is what
  // lets "12" render as "12" while it is being typed rather than re-deriving digits from a number
  // (which would silently eat a leading zero the child may still be about to correct).
  const [buffers, setBuffers] = useState<string[]>(() => Array.from({ length: blanks }, () => ''));

  const commit = (nextBuffers: string[]) => {
    setBuffers(nextBuffers);
    onChangeEntryValues(nextBuffers.map((buffer) => (buffer.length === 0 ? null : Number.parseInt(buffer, 10))));
  };

  const handleDigit = (digit: string) => {
    if (disabled) return;
    const next = [...buffers];
    next[focusedSlot] = (next[focusedSlot] ?? '') + digit;
    commit(next);
  };

  const handleDelete = () => {
    if (disabled) return;
    const next = [...buffers];
    next[focusedSlot] = (next[focusedSlot] ?? '').slice(0, -1);
    commit(next);
  };

  void entryValues; // Reported upward via onChangeEntryValues; the buffer, not this prop, drives display.

  return (
    <View>
      <ScrollView contentContainerStyle={styles.row} horizontal showsHorizontalScrollIndicator={false}>
        {shownSequence.map((value, index) => (
          <View key={`shown-${index}`} style={styles.token}>
            <AppText style={styles.tokenText}>{value}</AppText>
          </View>
        ))}
        {buffers.map((buffer, slotIndex) => (
          <Pressable
            accessibilityLabel={`entry slot ${slotIndex + 1}`}
            accessibilityRole="button"
            disabled={disabled}
            hitSlop={HIT_SLOP}
            key={`slot-${slotIndex}`}
            onPress={() => setFocusedSlot(slotIndex)}
            style={[
              styles.token,
              styles.entrySlot,
              focusedSlot === slotIndex && styles.entrySlotFocused,
            ]}>
            <AppText style={styles.tokenText}>{buffer.length === 0 ? '' : buffer}</AppText>
          </Pressable>
        ))}
      </ScrollView>
      <View style={styles.keypadSpacer}>
        <DigitKeypad disabled={disabled} onDelete={handleDelete} onDigit={handleDigit} />
      </View>
    </View>
  );
}

// --- reorder -----------------------------------------------------------------------------------

function ReorderRow({ disabled = false, onChangeOrder, values }: ReorderProps) {
  return (
    <ScrollView contentContainerStyle={styles.row} horizontal showsHorizontalScrollIndicator={false}>
      {values.map((value, index) => (
        <DraggableToken
          disabled={disabled}
          index={index}
          key={`${index}-${value}`}
          onDrop={(fromIndex, toIndex) => {
            if (fromIndex === toIndex) return;
            const next = [...values];
            const [moved] = next.splice(fromIndex, 1);
            next.splice(toIndex, 0, moved);
            onChangeOrder(next);
          }}
          total={values.length}
          value={value}
        />
      ))}
    </ScrollView>
  );
}

type DraggableTokenProps = {
  value: number;
  index: number;
  total: number;
  disabled: boolean;
  onDrop: (fromIndex: number, toIndex: number) => void;
};

// One token, draggable via a long-press-then-pan gesture (GESTURE_LONG_PRESS_MS activation, per
// the sequence doc's ruling that the line/token archetypes use a discrete, deliberate gesture
// rather than an immediate drag that could be triggered by an accidental touch). Position resets
// to its slot on drop; the reported order comes from which slot the drop landed nearest, not from
// the token's own transient pixel position, so a partial or cancelled drag never desyncs the
// visual order from the value the surface will submit.
function DraggableToken({ disabled, index, onDrop, total, value }: DraggableTokenProps) {
  const translateX = useSharedValue(0);
  const isDragging = useSharedValue(false);

  const dropAt = (toIndexRaw: number) => {
    const toIndex = Math.max(0, Math.min(total - 1, toIndexRaw));
    onDrop(index, toIndex);
  };

  const pan = Gesture.Pan()
    .enabled(!disabled)
    .activateAfterLongPress(GESTURE_LONG_PRESS_MS)
    .onUpdate((event) => {
      translateX.value = event.translationX;
    })
    .onEnd((event) => {
      const slotsMoved = Math.round(event.translationX / TOKEN_STRIDE);
      translateX.value = withTiming(0, { duration: ANIMATION_DURATION_MS });
      isDragging.value = false;
      runOnJS(dropAt)(index + slotsMoved);
    })
    .onStart(() => {
      isDragging.value = true;
    });

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
    zIndex: isDragging.value ? 1 : 0,
  }));

  return (
    <GestureDetector gesture={pan}>
      <Animated.View
        accessibilityLabel={`value ${value}, position ${index + 1} of ${total}`}
        accessibilityRole="adjustable"
        style={[styles.token, styles.reorderToken, animatedStyle]}>
        <AppText style={styles.tokenText}>{value}</AppText>
      </Animated.View>
    </GestureDetector>
  );
}

const styles = StyleSheet.create({
  entrySlot: {
    backgroundColor: colors.surface1,
    borderColor: colors.border,
    borderStyle: 'dashed',
  },
  entrySlotFocused: {
    borderColor: colors.primary,
    borderStyle: 'solid',
  },
  keypadSpacer: {
    marginTop: TOKEN_SPACING,
  },
  reorderToken: {
    backgroundColor: colors.primarySoft,
    borderColor: colors.primary,
  },
  row: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: TOKEN_SPACING,
    paddingVertical: TOKEN_SPACING,
  },
  token: {
    alignItems: 'center',
    borderRadius: radius.md,
    borderWidth: 2,
    height: TOKEN_TOUCH_TARGET_SIZE,
    justifyContent: 'center',
    width: TOKEN_TOUCH_TARGET_SIZE,
  },
  tokenText: {
    fontFamily: typography.fonts.bold,
    fontSize: typography.fontSize.lg,
  },
});
