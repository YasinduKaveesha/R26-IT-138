// The ruled entry control for `ordered-value-sequence`'s ordered-integer-collection blanks
// (10a-builder-prompt.md, "RULING -- THE ENTRY CONTROL IS A DIGIT KEYPAD, NOT A STEPPER").
//
// A per-slot +/- stepper was the original plan and was overruled: NP-01 at difficulty 4 and NP-02
// at difficulty 5 both ask for two-digit answers in the 60s-70s range, and a stepper from zero
// needs dozens of taps for those -- tap count would scale with the magnitude of the number, and
// magnitude rises with difficulty, so effort would track difficulty. That is the SPEC section 10
// confound touch-target SIZE constancy alone does not catch: a stepper keeps every size constant
// while making the interaction cost track difficulty regardless.
//
// This is not a free-text field (section 5.2 still holds, and this is explicitly not
// free-entry.tsx's TextInput): the child can only ever compose a value from a fixed, constant-size
// key set. Tap count then equals the number of digits typed, which is mathematical demand, not
// motor demand -- and digit count does not itself track difficulty level in this archetype's data,
// only the values being entered do, which is exactly the axis SPEC section 10 permits to vary.
//
// One shared keypad drives whichever entry slot currently has focus; it holds no state of its own
// about which slot that is -- the caller passes `onDigit` / `onDelete` and decides what they mean.

import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/src/components/app-text';
import { GESTURE_LONG_PRESS_MS, HIT_SLOP, KEYPAD_KEY_SIZE, KEYPAD_KEY_SPACING } from '@/src/features/c-session/motor-constants';
import { colors, radius, typography } from '@/src/theme/tokens';

const DIGIT_KEYS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'] as const;

export type DigitKeypadProps = {
  disabled?: boolean;
  onDigit: (digit: string) => void;
  onDelete: () => void;
};

export function DigitKeypad({ disabled = false, onDelete, onDigit }: DigitKeypadProps) {
  return (
    <View accessibilityRole="none" style={styles.grid}>
      {DIGIT_KEYS.map((digit) => (
        <Pressable
          accessibilityLabel={`digit ${digit}`}
          accessibilityRole="button"
          accessibilityState={{ disabled }}
          delayLongPress={GESTURE_LONG_PRESS_MS}
          disabled={disabled}
          hitSlop={HIT_SLOP}
          key={digit}
          onPress={() => onDigit(digit)}
          style={({ pressed }) => [styles.key, disabled && styles.keyDisabled, pressed && !disabled && styles.pressed]}>
          <AppText style={styles.keyText}>{digit}</AppText>
        </Pressable>
      ))}
      <Pressable
        accessibilityLabel="delete digit"
        accessibilityRole="button"
        accessibilityState={{ disabled }}
        delayLongPress={GESTURE_LONG_PRESS_MS}
        disabled={disabled}
        hitSlop={HIT_SLOP}
        onPress={onDelete}
        style={({ pressed }) => [styles.key, disabled && styles.keyDisabled, pressed && !disabled && styles.pressed]}>
        <AppText style={styles.keyText}>{'⌫'}</AppText>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: KEYPAD_KEY_SPACING,
  },
  key: {
    alignItems: 'center',
    backgroundColor: colors.surface1,
    borderBottomColor: colors.borderStrong,
    borderBottomWidth: 3,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 2,
    height: KEYPAD_KEY_SIZE,
    justifyContent: 'center',
    width: KEYPAD_KEY_SIZE,
  },
  keyDisabled: { opacity: 0.55 },
  keyText: {
    fontFamily: typography.fonts.bold,
    fontSize: typography.fontSize.lg,
  },
  pressed: { opacity: 0.72 },
});
