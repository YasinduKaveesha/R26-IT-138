import { Ionicons } from '@expo/vector-icons';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/src/components/app-text';
import type {
  CountSelectionAnswerState,
  CountSelectionRendererSpec,
} from '@/src/features/session/renderers/types';
import { colors, radius, spacing, typography } from '@/src/theme/tokens';

// The count-selection surface (interactive_set_selection). The child builds a count; the encoder
// turns it into `String(count)`.
//
// No maximum is imposed. A ceiling would be a client-side rule about what counts are legitimate
// for an item — the server owns that — and the prompt keys that describe the underlying set are
// out of scope this batch (only `prompt.stem` is rendered). The floor is 0 because a count cannot
// be negative; 0 itself is a real, submittable answer.
//
// A count of -1 is the "not chosen yet" seed from `initialAnswerState`, which the encoder already
// rejects, so submit stays unavailable until the child actually interacts. It renders as a dash,
// and the first "+" tap lands on 0 so that zero stays reachable in one tap.

type CountSelectionProps = {
  spec: CountSelectionRendererSpec;
  state: CountSelectionAnswerState;
  disabled?: boolean;
  onChange: (next: CountSelectionAnswerState) => void;
};

export function CountSelection({ disabled = false, onChange, state }: CountSelectionProps) {
  const chosen = state.count >= 0;
  const canDecrement = !disabled && state.count > 0;

  return (
    <View style={styles.wrapper}>
      <AppText style={styles.label}>Choose how many</AppText>
      <View style={styles.stepper}>
        <Pressable
          accessibilityLabel="One fewer"
          accessibilityRole="button"
          accessibilityState={{ disabled: !canDecrement }}
          disabled={!canDecrement}
          onPress={() => onChange({ kind: 'count-selection', count: Math.max(0, state.count - 1) })}
          style={({ pressed }) => [
            styles.stepButton,
            !canDecrement && styles.stepButtonDisabled,
            pressed && canDecrement && styles.pressed,
          ]}>
          <Ionicons color={colors.primaryShadow} name="remove" size={30} />
        </Pressable>

        <View accessibilityRole="text" style={styles.readout}>
          <AppText align="center" style={styles.readoutText}>
            {chosen ? String(state.count) : '—'}
          </AppText>
        </View>

        <Pressable
          accessibilityLabel="One more"
          accessibilityRole="button"
          accessibilityState={{ disabled }}
          disabled={disabled}
          onPress={() => onChange({ kind: 'count-selection', count: chosen ? state.count + 1 : 0 })}
          style={({ pressed }) => [
            styles.stepButton,
            disabled && styles.stepButtonDisabled,
            pressed && !disabled && styles.pressed,
          ]}>
          <Ionicons color={colors.primaryShadow} name="add" size={30} />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  label: {
    color: colors.textSecondary,
    fontSize: typography.fontSize.sm,
    lineHeight: typography.lineHeight.sm,
  },
  pressed: { opacity: 0.72 },
  readout: {
    alignItems: 'center',
    backgroundColor: colors.surface1,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 2,
    flex: 1,
    justifyContent: 'center',
    minHeight: 68,
  },
  readoutText: {
    fontFamily: typography.fonts.heavy,
    fontSize: 34,
    lineHeight: 42,
  },
  stepButton: {
    alignItems: 'center',
    backgroundColor: colors.primarySoft,
    borderBottomColor: colors.primaryShadow,
    borderBottomWidth: 3,
    borderColor: colors.primary,
    borderRadius: radius.md,
    borderWidth: 2,
    height: 68,
    justifyContent: 'center',
    width: 68,
  },
  stepButtonDisabled: { opacity: 0.45 },
  stepper: { alignItems: 'center', flexDirection: 'row', gap: spacing.smPlus },
  wrapper: { gap: spacing.sm },
});
