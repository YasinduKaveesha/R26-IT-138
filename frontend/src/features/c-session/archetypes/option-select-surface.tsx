// The `option-select` archetype surface (10d). Renders `task.prompt_text` verbatim, the task's
// `prompt_payload` numbers as read-only tokens (both real templates on this path -- `left_count`/
// `right_count`, `value_a`/`value_b` -- are given operands the child compares, never the answer
// itself; see option-select-logic.ts's own header for why the OTHER option source, where a payload
// number IS the answer, is refused rather than rendered this way), and an `OptionChoiceRow` bound to
// the pipe-string's own parsed alternatives. `null` resolution renders `FailClosedFrame`, matching
// c-session-screen.tsx's own convention (support code = `task.request_id`). `onSubmit` receives the
// raw per-key values object -- `handleSubmit` (c-session-screen.tsx) already runs
// `encodeActionPayload` on it; this file does not duplicate that step and does not modify
// `handleSubmit`.
//
// Visual design is reused, not reinvented (10d work order, owner ruling 2026-08-25): the screen
// chrome, question rendering, payload-token shape and SUBMIT button below are reproduced from
// `value-report-surface.tsx`'s own `styles`/`SubmitButton` (neither is exported from that file, so
// this file reproduces their exact shape rather than importing a private symbol) -- not a redesign.
// There is no separate "answer" token column the way `value-report-surface.tsx` has one: the answer
// here is which option the child picked, shown by `OptionChoiceRow`'s own selected state, not typed
// into a digit token.

import { useMemo, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/src/components/app-text';
import type { ArchetypeSurfaceProps } from '@/src/features/c-session/archetype-surfaces';
import { resolveOptionSelectSpec } from '@/src/features/c-session/archetypes/option-select-logic';
import { FailClosedFrame } from '@/src/features/c-session/fail-closed-frame';
import { accentForGameFamily } from '@/src/features/c-session/game-family-accents';
import { HIT_SLOP, TOKEN_SPACING, TOKEN_TOUCH_TARGET_SIZE } from '@/src/features/c-session/motor-constants';
import { BooleanToggle } from '@/src/features/c-session/primitives/boolean-toggle';
import { OptionChoiceRow } from '@/src/features/c-session/primitives/option-choice-row';
import { colors, radius, spacing, typography } from '@/src/theme/tokens';

// Matches value-report-surface.tsx's own payload-token sizing exactly (2026-08-26 user request:
// token 60% larger, label 50% larger than the shared TOKEN_* constants) -- reused for visual
// consistency across archetypes built against the same read-only-token shape, not re-derived.
const PAYLOAD_TOKEN_SIZE = Math.round(TOKEN_TOUCH_TARGET_SIZE * 1.6);
const PAYLOAD_LABEL_FONT_SIZE = Math.round(typography.fontSize.sm * 1.5);
const PAYLOAD_LABEL_LINE_HEIGHT = Math.round(typography.lineHeight.sm * 1.5);
const PAYLOAD_LABEL_BLOCK_HEIGHT = PAYLOAD_LABEL_LINE_HEIGHT * 2;

export function OptionSelectSurface({ onSubmit, task }: ArchetypeSurfaceProps) {
  const spec = useMemo(() => resolveOptionSelectSpec(task), [task]);

  if (spec === null) {
    return <FailClosedFrame onExit={() => {}} supportCode={task.request_id} />;
  }

  // The family's own accent (game-family-accents.ts) -- read from the wire, never chosen per
  // archetype or per template, matching value-report-surface.tsx's own precedent.
  const accent = accentForGameFamily(task.game_family_id);

  return <OptionSelectScene accent={accent} onSubmit={onSubmit} spec={spec} />;
}

type OptionSelectSceneProps = {
  accent: string;
  spec: NonNullable<ReturnType<typeof resolveOptionSelectSpec>>;
  onSubmit: (payload: Record<string, unknown>) => void | Promise<void>;
};

function OptionSelectScene({ accent, onSubmit, spec }: OptionSelectSceneProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [extraValues, setExtraValues] = useState<Record<string, unknown>>({});

  const canSubmit =
    selected !== null &&
    spec.extraFields.every((field) => Object.prototype.hasOwnProperty.call(extraValues, field.key));

  const handleSubmitPress = () => {
    if (!canSubmit) return;
    void onSubmit({
      [spec.scoreKey]: selected,
      ...extraValues,
    });
  };

  return (
    <View style={styles.container}>
      <AppText style={styles.promptText} variant="title">
        {spec.promptText}
      </AppText>
      {spec.payloadValues.length > 0 ? (
        <View style={styles.payloadRow}>
          {spec.payloadValues.map((payloadValue, index) => (
            <View key={`${payloadValue.key}-${index}`} style={styles.payloadColumn}>
              <View style={styles.payloadLabelBlock}>
                <AppText style={[styles.payloadLabel, { color: accent }]}>{payloadValue.label}</AppText>
              </View>
              <View style={styles.payloadToken}>
                <AppText style={styles.payloadTokenText}>{payloadValue.value}</AppText>
              </View>
            </View>
          ))}
        </View>
      ) : null}
      <OptionChoiceRow onSelect={setSelected} options={spec.alternatives} value={selected} />
      {spec.extraFields.map((field) => (
        <BooleanToggle
          fieldKey={field.key}
          key={field.key}
          onChange={(value) => setExtraValues((prev) => ({ ...prev, [field.key]: value }))}
          value={extraValues[field.key]}
        />
      ))}
      <SubmitButton disabled={!canSubmit} onPress={handleSubmitPress} />
    </View>
  );
}

function SubmitButton({ disabled, onPress }: { disabled: boolean; onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled }}
      disabled={disabled}
      hitSlop={HIT_SLOP}
      onPress={onPress}
      style={({ pressed }) => [
        styles.submitButton,
        disabled && styles.submitButtonDisabled,
        pressed && !disabled && styles.pressed,
      ]}>
      <AppText style={styles.submitButtonText}>SUBMIT</AppText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    gap: spacing.lg,
    justifyContent: 'space-between',
    padding: spacing.lg,
  },
  payloadColumn: {
    alignItems: 'center',
    flex: 1,
    gap: 4,
  },
  payloadLabel: {
    fontFamily: typography.fonts.bold,
    fontSize: PAYLOAD_LABEL_FONT_SIZE,
    lineHeight: PAYLOAD_LABEL_LINE_HEIGHT,
    textAlign: 'center',
  },
  payloadLabelBlock: {
    height: PAYLOAD_LABEL_BLOCK_HEIGHT,
    justifyContent: 'flex-end',
  },
  payloadRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: TOKEN_SPACING * 2,
    justifyContent: 'center',
  },
  payloadToken: {
    alignItems: 'center',
    backgroundColor: colors.surface1,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 2,
    height: PAYLOAD_TOKEN_SIZE,
    justifyContent: 'center',
    width: PAYLOAD_TOKEN_SIZE,
  },
  payloadTokenText: {
    fontFamily: typography.fonts.bold,
    fontSize: typography.fontSize.lg,
  },
  pressed: { opacity: 0.72 },
  promptText: { color: colors.textPrimary, fontSize: 20, lineHeight: 23 },
  submitButton: {
    alignItems: 'center',
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    justifyContent: 'center',
    minHeight: 56,
    paddingHorizontal: spacing.lg,
  },
  submitButtonDisabled: { opacity: 0.5 },
  submitButtonText: {
    color: colors.surface1,
    fontFamily: typography.fonts.bold,
    fontSize: typography.fontSize.lg,
  },
});
