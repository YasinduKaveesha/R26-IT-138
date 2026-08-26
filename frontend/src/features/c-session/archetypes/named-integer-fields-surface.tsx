// The `named-integer-fields` archetype surface (10f, C-BT-01..04). Renders `task.prompt_text`
// verbatim, the task's `prompt_payload` numbers as read-only labelled tokens (every one of these
// four templates' `prompt_text` points at a quantity it never states -- "Show THIS NUMBER using tens
// and ones", "Trade ten ones for one ten" against a starting state -- and `interactive_assets` is
// `{}` on all twenty exemplars, so the tokens are the only place those numbers are visible at all),
// and one entry box per `integer-field` key `resolveNamedIntegerFieldsSpec` finds in
// `valid_action_space`, one shared `DigitKeypad` below. `null` resolution renders
// `FailClosedFrame`, matching c-session-screen.tsx's own convention (support code =
// `task.request_id`). `onSubmit` receives the raw per-key values object -- `handleSubmit`
// (c-session-screen.tsx) already runs `encodeActionPayload` on it; this file does not duplicate that
// step and does not modify `handleSubmit`.
//
// TWO ROWS, SAME BOX STYLE. The GIVEN payload value(s) (`target_number`, or `pre_tens`/`pre_ones`)
// render alone in their own row directly under the prompt (tight `promptBlock` gap, halved from the
// container's own -- 2026-08-26 request); the entry fields render as their own row below that. Both
// rows share one box style (`payloadToken`/`payloadColumn`/`payloadLabel`, reproduced from
// `value-report-surface.tsx` exactly, not a redesign) so a given value and an entry field still read
// as the same kind of thing, without forcing every column onto one combined line -- an earlier
// single-row version (2026-08-26) put all of C-BT-02's four columns (Number + Hundreds + Tens +
// Ones) in one row, which the owner rejected as "not like that": splitting into two rows is what
// lets both rows share one comfortable box size without wrapping or squeezing.
//
// DISPLAY ORDER IS A COSMETIC REORDERING, NEVER A CHANGE TO WHAT IS SUBMITTED. `spec.fields` stays in
// the wire's own key order (named-integer-fields-logic.ts's own contract, unchanged); this file
// alone reorders the ON-SCREEN boxes by `PLACE_VALUE_RANK` so "Hundreds, Tens, Ones" reads
// left-to-right in descending place value (2026-08-26 correction: the wire's own alphabetical key
// order put "Ones" before "Tens", which reads backwards against the prompt text and against how a
// child is taught to write place value). `useNamedFieldEntry` keys its state by field KEY, not by
// display position, so this reordering can never misattribute a value to the wrong submitted key --
// see named-field-row.tsx's own header. A field name outside the known place-value vocabulary sorts
// to the end, stable, rather than crashing or silently misplacing itself -- this is a display-only
// convenience over a known, small, real vocabulary (hundreds/tens/ones and their pre_/post_
// variants), not a second labelling table: it never changes what text a field shows, only where it
// sits in the row.
//
// ONE SCENE, TWO AND THREE FIELDS ALIKE, WITH NO BRANCH BETWEEN THEM. C-BT-02 declares three action
// keys and the other three templates declare two; nothing in this file distinguishes those cases --
// `spec.fields` is mapped, not counted. There is no `game_task_template_id` read anywhere here, and
// no `C-BT-*` literal; `c-named-integer-fields-no-template-branch.test.ts` holds that line.
//
// NO AUTO-CARRY, NO AUTO-BORROW, NO PRE-FILL (master work order §10f row, verbatim). Fields start
// empty and are never seeded from `target_number` or `pre_tens`/`pre_ones`; no field's value is
// computed from another's; and SUBMIT is NOT gated on the fields decomposing `target_number` or
// correctly effecting the trade. `c-named-integer-fields-no-client-arithmetic.test.ts` holds that
// line.

import { useMemo } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/src/components/app-text';
import type { ArchetypeSurfaceProps } from '@/src/features/c-session/archetype-surfaces';
import { resolveNamedIntegerFieldsSpec } from '@/src/features/c-session/archetypes/named-integer-fields-logic';
import { FailClosedFrame } from '@/src/features/c-session/fail-closed-frame';
import { accentForGameFamily } from '@/src/features/c-session/game-family-accents';
import { TOKEN_SPACING, TOKEN_TOUCH_TARGET_SIZE, HIT_SLOP } from '@/src/features/c-session/motor-constants';
import { DigitKeypad } from '@/src/features/c-session/primitives/digit-keypad';
import {
  NamedFieldBox,
  useNamedFieldEntry,
  type NamedField,
} from '@/src/features/c-session/primitives/named-field-row';
import { colors, radius, spacing, typography } from '@/src/theme/tokens';

// A SMALLER, FIXED SIZE THAN `value-report-surface.tsx`'s own payload token, DELIBERATELY (2026-08-26
// correction, found by the owner testing C-BT-02: the wider `* 1.6` size wraps a 4-column row --
// Number + Hundreds + Tens + Ones, this scene's own maximum -- onto two lines on a typical phone
// width, which the owner rejected: "they all should be at the same level"). `TOKEN_TOUCH_TARGET_SIZE`
// itself, with NO multiplier, is what fits all four columns on one row while staying at or above
// SPEC §10's 48px floor -- and because the field boxes ARE real touch targets (unlike
// `value-report`'s read-only tokens), that floor genuinely governs here, so this could not have
// shrunk further than this constant regardless. A single fixed constant, never a function of field
// count or `difficulty_level`: C-BT-01/03/04's 3-column row (Number + 2 fields) uses the exact same
// size as C-BT-02's 4-column row, so motor constancy holds across every template and level alike --
// only the WIDTH OF THE ROW increases with column count, never the size of any one target.
// `named-field-row.tsx`'s own `FIELD_BOX_SIZE` matches this value exactly (see that file's header)
// so payload tokens and entry fields still sit level, at one shared size, in one row.
const PAYLOAD_TOKEN_SIZE = TOKEN_TOUCH_TARGET_SIZE;
const PAYLOAD_LABEL_FONT_SIZE = Math.round(typography.fontSize.sm * 1.5);
const PAYLOAD_LABEL_LINE_HEIGHT = Math.round(typography.lineHeight.sm * 1.5);
const PAYLOAD_LABEL_BLOCK_HEIGHT = PAYLOAD_LABEL_LINE_HEIGHT * 2;

// See the header's "DISPLAY ORDER IS A COSMETIC REORDERING" paragraph. A field key outside this
// table (a future template's genuinely new key) sorts to the end, stable -- never a crash, never a
// misattributed value, since sorting never touches `field.key` itself.
const PLACE_VALUE_RANK: Record<string, number> = {
  hundreds: 0,
  tens: 1,
  ones: 2,
  pre_hundreds: 0,
  pre_tens: 1,
  pre_ones: 2,
  post_hundreds: 0,
  post_tens: 1,
  post_ones: 2,
};

// Generic over anything keyed like a field or a payload value (2026-08-26 extension: the GIVEN
// row -- `pre_tens`/`pre_ones` -- needed the identical reordering once the owner pointed out its
// wire-alphabetical order ("Ones to start" before "Tens to start") no longer lined up, column for
// column, with the entry row beneath it once THAT row got reordered. One rank table, applied to
// both rows, is what keeps a place-value column (e.g. "Tens") stacked directly under its own given
// value rather than under an unrelated one.
function displayOrder<T extends { key: string }>(items: readonly T[]): readonly T[] {
  return [...items].sort((a, b) => {
    const rankA = PLACE_VALUE_RANK[a.key] ?? Number.MAX_SAFE_INTEGER;
    const rankB = PLACE_VALUE_RANK[b.key] ?? Number.MAX_SAFE_INTEGER;
    return rankA - rankB;
  });
}

export function NamedIntegerFieldsSurface({ onSubmit, task }: ArchetypeSurfaceProps) {
  const spec = useMemo(() => resolveNamedIntegerFieldsSpec(task), [task]);

  if (spec === null) {
    return <FailClosedFrame onExit={() => {}} supportCode={task.request_id} />;
  }

  // The family's own accent, read from the wire -- never a colour chosen per archetype or per
  // template. game-family-accents.ts is the one place this colour is written.
  const accent = accentForGameFamily(task.game_family_id);

  return <NamedIntegerFieldsScene accent={accent} onSubmit={onSubmit} spec={spec} />;
}

type NamedIntegerFieldsSceneProps = {
  accent: string;
  spec: NonNullable<ReturnType<typeof resolveNamedIntegerFieldsSpec>>;
  onSubmit: (payload: Record<string, unknown>) => void | Promise<void>;
};

function NamedIntegerFieldsScene({ accent, onSubmit, spec }: NamedIntegerFieldsSceneProps) {
  const orderedFields = useMemo(() => displayOrder(spec.fields), [spec.fields]);
  const orderedPayloadValues = useMemo(() => displayOrder(spec.payloadValues), [spec.payloadValues]);
  const entry = useNamedFieldEntry(spec.fields);

  // Not a correctness condition -- see the header. `encodeActionPayload` requires a value for every
  // declared key, so a partially-filled submission could not be encoded at all.
  const canSubmit = entry.values.every((value) => value !== null);

  const handleSubmitPress = () => {
    if (!canSubmit) return;
    const payload: Record<string, unknown> = {};
    spec.fields.forEach((field, fieldIndex) => {
      payload[field.key] = entry.values[fieldIndex];
    });
    void onSubmit(payload);
  };

  return (
    <View style={styles.container}>
      <View style={styles.promptAndFieldsGroup}>
        <View style={styles.promptBlock}>
          <AppText style={styles.promptText} variant="title">
            {spec.promptText}
          </AppText>
          <View style={styles.payloadRow}>
            {orderedPayloadValues.map((payloadValue, index) => (
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
        </View>
        <View style={styles.fieldsRow}>
          {orderedFields.map((field) => (
            <View key={field.key} style={styles.payloadColumn}>
              <NamedFieldBox
                accent={accent}
                field={field}
                focused={entry.focusedKey === field.key}
                onPress={() => entry.setFocusedKey(field.key)}
                value={entry.buffers[field.key] ?? ''}
              />
              <View style={styles.payloadLabelBlockBelow}>
                <AppText style={[styles.payloadLabel, { color: accent }]}>{field.label}</AppText>
              </View>
            </View>
          ))}
        </View>
      </View>
      <View style={styles.keypadWrapper}>
        <DigitKeypad onDelete={entry.handleDelete} onDigit={entry.handleDigit} />
      </View>
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
  // Same row shape as `payloadRow` below -- kept as its own name only so this file's JSX reads
  // clearly ("the fields row"), not because the styling itself differs.
  fieldsRow: {
    alignItems: 'center',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: TOKEN_SPACING,
    justifyContent: 'center',
    rowGap: TOKEN_SPACING * 1.5,
  },
  // Groups the prompt block and the fields row at half the container's own gap (2026-08-26
  // request), so the fields sit close under the given number rather than at the container's normal
  // spacing (which still separates this whole group from the keypad and SUBMIT below it).
  promptAndFieldsGroup: {
    gap: spacing.lg / 2,
  },
  // Pulls the keypad up to half the container's own gap below the fields row (2026-08-26 request) --
  // `marginTop` set to the negative of the difference (container gap minus the wanted half-gap),
  // rather than moving the gap declaration itself, so the gap between the keypad and SUBMIT below it
  // (also `container`'s own spacing) is untouched.
  keypadWrapper: {
    marginTop: -(spacing.lg / 2),
  },
  // Deliberately NOT `flex: 1` (2026-08-26 correction, found by the owner testing C-BT-02: with
  // `flex: 1` inside a `flexWrap: 'wrap'` row, RN Web's flex-shrink default lets every column
  // compress to fit ONE line rather than actually wrapping -- the same pitfall object-pool.tsx's own
  // header already documents for a ScrollView. `minWidth` pinned to the box's own size is what makes
  // a column refuse to shrink below its content, so a 4-column row (Number + Hundreds + Tens + Ones,
  // C-BT-02's own shape) genuinely wraps onto a second line instead of squeezing every label into
  // illegibility. The box size itself -- and therefore every column's `minWidth` -- stays IDENTICAL
  // regardless of field count or `difficulty_level`, so this is a wrap, never a per-level resize.
  payloadColumn: {
    alignItems: 'center',
    gap: 4,
    minWidth: PAYLOAD_TOKEN_SIZE,
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
  // The fields row's own label placement: BELOW its box (2026-08-26 request), the mirror image of
  // `payloadLabelBlock` above (which sits ABOVE its box, for the given-value row) -- `flex-start`
  // rather than `flex-end` is the only difference, so a wrapped two-line label still starts
  // immediately under the box instead of floating away from it.
  payloadLabelBlockBelow: {
    height: PAYLOAD_LABEL_BLOCK_HEIGHT,
    justifyContent: 'flex-start',
  },
  payloadRow: {
    alignItems: 'center',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: TOKEN_SPACING,
    justifyContent: 'center',
    rowGap: TOKEN_SPACING * 1.5,
  },
  // Groups the prompt and the GIVEN value(s) alone, at half the container's own gap (2026-08-26
  // request), separate from the entry-fields row below -- see the header's "TWO ROWS" note.
  promptBlock: {
    gap: spacing.lg / 2,
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
