// Rendered in place of the archetype surface, inside `c-session-screen.tsx`'s existing task card,
// after a submission -- never alongside it. That "instead of, not over" placement is a correctness
// requirement, not a layout choice: while this panel is showing, no archetype surface is mounted
// and so no `onSubmit` can fire, which is what structurally prevents a second submission on the
// same task instance. That matters concretely: a CORRECT answer writes the one terminal event a
// task instance may ever have (`task_service.py`'s `has_terminal_for_instance` guard), and
// resubmitting a completed instance is refused with `task_already_terminal`
// (`task_service.py:573-576`) -- a 409 `classifySessionFailure` routes to the technical-block
// screen. A child seeing that would read it as the app breaking, not as "you already answered
// this". This panel existing at all is what keeps that path unreachable.
//
// Two states, one action each, both child-initiated:
//   - not matched -> "Try again": clears the panel and lets the same task remount for a fresh
//     attempt. The backend allows unlimited retries on a wrong answer (no terminal event is
//     written on that path) and escalates `scaffold_level` each time -- this panel displays that
//     escalation, never computes or overrides it.
//   - matched -> "Next": advances to the next task via the caller's own `loadNextTask`.
// Advancing is never automatic. An auto-advance timer would introduce a new timing constant, and
// SPEC section 10 / `motor-constants.ts` own every timing constant in this codebase; a button sidesteps
// that question entirely and lets the child set their own pace, matching every other advance-only
// control here (SubmitButton, NeutralMessageScreen's exit button).
//
// THE WORDING BELOW IS FLAGGED, NOT SETTLED (`ESCALATIONS.md`). Component B's own results view
// documents that its copy is "identical for every possible outcome history" and "contains nothing
// evaluative" -- a per-task correct/incorrect panel is a deliberate departure from that house
// precedent, and whether immediate correct/incorrect framing is right for this population is a
// pedagogical question this file does not answer. The copy here is neutral and non-punitive on the
// not-matched path (no "wrong", no "incorrect", no score) precisely so shipping it does not
// pre-empt that ruling by accident.
//
// This component computes nothing about correctness. It takes the server's own verdict as a prop
// and renders one of two fixed states; it holds no state of its own about the task, the payload,
// or scoring, matching `DigitKeypad`'s and `UnitStepper`'s own "holds no state of its own" doctrine
// for a stateless, caller-driven primitive.

import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/src/components/app-text';
import { HIT_SLOP } from '@/src/features/c-session/motor-constants';
import { colors, radius, spacing, typography } from '@/src/theme/tokens';

export type AnswerFeedbackPanelProps = {
  matched: boolean;
  /** The server's own `scaffold_level`, relayed verbatim -- never interpreted by this file. */
  scaffoldLevel: string;
  onTryAgain: () => void;
  onNext: () => void;
};

export function AnswerFeedbackPanel({ matched, onNext, onTryAgain, scaffoldLevel }: AnswerFeedbackPanelProps) {
  return (
    <View style={styles.container}>
      <View style={styles.messageBlock}>
        <AppText style={styles.messageText} variant="title">
          {matched ? 'Nice work!' : "Let's try that again."}
        </AppText>
        {!matched ? (
          <AppText style={styles.scaffoldText}>{`Support level: ${scaffoldLevel}`}</AppText>
        ) : null}
      </View>
      <Pressable
        accessibilityLabel={matched ? 'Next question' : 'Try again'}
        accessibilityRole="button"
        hitSlop={HIT_SLOP}
        onPress={matched ? onNext : onTryAgain}
        style={({ pressed }) => [styles.actionButton, pressed && styles.pressed]}>
        <AppText style={styles.actionButtonText}>{matched ? 'NEXT' : 'TRY AGAIN'}</AppText>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  actionButton: {
    alignItems: 'center',
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    justifyContent: 'center',
    minHeight: 56,
    paddingHorizontal: spacing.lg,
  },
  actionButtonText: {
    color: colors.surface1,
    fontFamily: typography.fonts.bold,
    fontSize: typography.fontSize.lg,
  },
  // Mirrors every archetype surface's own `container` shape (e.g.
  // `ordered-value-sequence-surface.tsx`'s `styles.container`): `flex:1`,
  // `justifyContent:'space-between'`, `padding: spacing.lg` -- the message pinned to the top of the
  // card's own content area, the action button pinned to the bottom, matching where the question
  // and SUBMIT sit on every surface this panel replaces.
  container: {
    flex: 1,
    justifyContent: 'space-between',
    padding: spacing.lg,
  },
  messageBlock: { gap: spacing.smPlus },
  // Half of typography.fontSize.title / lineHeight.title, matching every surface's own promptText
  // sizing exactly (e.g. `value-report-surface.tsx:223`) -- this panel occupies the same visual
  // role a question does, so it uses the same size rather than inventing a new one.
  messageText: { color: colors.textPrimary, fontSize: 20, lineHeight: 23 },
  pressed: { opacity: 0.85 },
  scaffoldText: { color: colors.textSecondary, fontFamily: typography.fonts.body, fontSize: typography.fontSize.sm },
});
