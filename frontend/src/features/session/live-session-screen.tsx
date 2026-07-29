import { Ionicons } from '@expo/vector-icons';
import * as Crypto from 'expo-crypto';
import { router } from 'expo-router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import type { PendingSubmitResponseCommand } from '@/src/api/contracts';
import { createComponentBApi } from '@/src/api/component-b-api';
import { ApiClientError } from '@/src/api/errors';
import type { AttemptResponse } from '@/src/api/generated/openapi-types';
import { useAuth } from '@/src/auth/auth-context';
import { AppText } from '@/src/components/app-text';
import { readPublicConfig } from '@/src/config/env';
import {
  classifyAttemptOutcome,
  classifyFailure,
  failureRequestId,
  initialAnswerState,
  isAnswerSurfaceDisabled,
  isDeadlinePassed,
  outcomeView,
  planPresentation,
  decidePendingReplay,
  type AttemptOutcome,
  type SessionFailure,
  type SessionPlan,
} from '@/src/features/session/live-session-logic';
import {
  clearPendingCommand,
  loadPendingCommand,
  savePendingCommand,
} from '@/src/features/session/session-command-store';
import { encodeSubmittedValue } from '@/src/features/session/renderers/encode';
import { ChoiceGrid } from '@/src/features/session/renderers/choice-grid';
import { CountSelection } from '@/src/features/session/renderers/count-selection';
import { FreeEntry } from '@/src/features/session/renderers/free-entry';
import type { AnswerState } from '@/src/features/session/renderers/types';
import { colors, radius, spacing, typography } from '@/src/theme/tokens';

// FE-3b: select the question, render it, accept an answer, submit it, show the outcome.
//
// Deliberately absent, each owned by a later batch: the countdown UI (FE-3c), hints (FE-3d),
// advancing to the next question (FE-3e) and results (FE-3f). After an attempt is recorded the
// child sees the outcome and the existing "Back to home" affordance. There is no next-question
// button here on purpose — inventing one would front-run FE-3e's completion call.

type RenderPlan = Extract<SessionPlan, { kind: 'render' }>;

type Phase =
  | { kind: 'loading' }
  | { kind: 'question'; plan: RenderPlan }
  | { kind: 'unrenderable'; requestId: string }
  | { kind: 'failure'; failure: SessionFailure; requestId: string | null };

const failureCopy: Record<SessionFailure, { title: string; detail: string }> = {
  authentication: { title: 'Sign-in needed', detail: 'Ask a grown-up to help you sign in again.' },
  conflict: { title: 'One moment', detail: "Something changed — let's take another look." },
  network: { title: 'No connection', detail: 'Check the internet and try again in a moment.' },
  technical: { title: 'Something went wrong', detail: 'Try again in a little while.' },
};

export function LiveSessionScreen({ sessionId }: { sessionId: string }) {
  const { getAccessToken } = useAuth();
  const configResult = useMemo(() => readPublicConfig(), []);
  const api = useMemo(
    () => (configResult.config ? createComponentBApi(configResult.config) : null),
    [configResult.config],
  );

  const [phase, setPhase] = useState<Phase>({ kind: 'loading' });
  const [answer, setAnswer] = useState<AnswerState | null>(null);
  const [outcome, setOutcome] = useState<AttemptOutcome | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const mountedRef = useRef(true);
  const runningRef = useRef(false);
  // client_elapsed_ms is telemetry only and is never read for correctness (server timestamps are
  // authoritative). Measured from the moment the question surface becomes answerable — which is
  // also reset when the child chooses to try again — to the submit tap.
  const shownAtRef = useRef<number>(Date.now());

  /**
   * Runs an authenticated call, refreshing the token once on an `unauthenticated` failure. The
   * refresh is a retry of the *same* call with the *same* arguments — for submits that means the
   * same idempotency key and the same body, so a retry can never record a second attempt.
   */
  const withToken = useCallback(
    async <T,>(call: (accessToken: string) => Promise<T>): Promise<T> => {
      const accessToken = await getAccessToken();
      if (!accessToken) throw new ApiClientError('unauthenticated', 'No access token is available.');
      try {
        return await call(accessToken);
      } catch (error) {
        if (!(error instanceof ApiClientError) || error.kind !== 'unauthenticated') throw error;
        const refreshed = await getAccessToken(true);
        if (!refreshed) throw error;
        return await call(refreshed);
      }
    },
    [getAccessToken],
  );

  const applyAttempt = useCallback(async (attempt: AttemptResponse) => {
    // The attempt is recorded server-side; the local recovery record has done its job.
    await clearPendingCommand();
    if (!mountedRef.current) return;
    setOutcome(classifyAttemptOutcome(attempt));
  }, []);

  /**
   * Mount (and post-409 resync) path.
   *
   * POST /opportunities takes no idempotency key and no body by design: it re-issues the session's
   * already-open question rather than minting a new one, which is exactly what makes it the
   * crash-recovery entry point. Calling it after a relaunch returns the same item_opportunity_id.
   */
  const presentOpportunity = useCallback(async () => {
    if (!api || runningRef.current) return;
    runningRef.current = true;
    setPhase({ kind: 'loading' });
    setOutcome(null);
    setSubmitting(false);
    try {
      const presentation = await withToken((token) => api.selectOpportunity(sessionId, token));
      if (!mountedRef.current) return;
      const plan = planPresentation(presentation);
      if (plan.kind !== 'render') {
        setPhase({ kind: 'unrenderable', requestId: plan.requestId });
        return;
      }
      setAnswer(initialAnswerState(plan.spec));
      shownAtRef.current = Date.now();
      setPhase({ kind: 'question', plan });

      // Offline-recovery replay. A saved submit for *this* opportunity is resent verbatim — same
      // key, same body — so the server returns the original attempt instead of recording a second
      // one. A saved submit for a different opportunity belongs to a question that has already
      // moved on, so it is discarded rather than sent.
      const decision = decidePendingReplay(await loadPendingCommand(), sessionId, plan.itemOpportunityId);
      if (decision.action === 'discard') {
        await clearPendingCommand();
        return;
      }
      if (decision.action === 'replay') {
        await sendSubmit(decision.command);
      }
    } catch (error) {
      if (!mountedRef.current) return;
      setPhase({
        kind: 'failure',
        failure: classifyFailure(error),
        requestId: failureRequestId(error),
      });
    } finally {
      runningRef.current = false;
    }
    // sendSubmit is declared below and is stable for the same reasons `api`/`withToken` are; the
    // mutual reference is broken with a ref-free forward declaration.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api, sessionId, withToken]);

  const sendSubmit = useCallback(
    async (command: PendingSubmitResponseCommand) => {
      if (!api) return;
      setSubmitting(true);
      try {
        const attempt = await withToken((token) =>
          api.submitResponse(
            command.sessionId,
            command.itemOpportunityId,
            command.idempotencyKey,
            command.body,
            token,
          ),
        );
        await applyAttempt(attempt);
      } catch (error) {
        if (!mountedRef.current) return;
        const failure = classifyFailure(error);
        if (failure === 'conflict') {
          // 409 means the server's view of this opportunity has moved on. Re-ask it what to show
          // and render whatever comes back — never a client-side rule about what "should" have
          // happened.
          await clearPendingCommand();
          if (mountedRef.current) await presentOpportunity();
          return;
        }
        // Anything else leaves the pending command persisted on purpose: it is the record that
        // lets the next mount replay this exact key and body instead of losing the attempt.
        setPhase({ kind: 'failure', failure, requestId: failureRequestId(error) });
      } finally {
        if (mountedRef.current) setSubmitting(false);
      }
    },
    [api, applyAttempt, presentOpportunity, withToken],
  );

  const submitAnswer = useCallback(async () => {
    if (phase.kind !== 'question' || !answer || submitting) return;
    const submittedValue = encodeSubmittedValue(phase.plan.spec, answer);
    // Unreachable via the button (it is disabled in exactly this case); kept because "no
    // submittable value" must never become "send something anyway".
    if (submittedValue === null) return;

    const command: PendingSubmitResponseCommand = {
      body: {
        client_elapsed_ms: Math.max(0, Date.now() - shownAtRef.current),
        submitted_value: submittedValue,
      },
      createdAt: new Date().toISOString(),
      endpoint: '/api/v1/b/sessions/{sessionId}/opportunities/{itemOpportunityId}/responses',
      idempotencyKey: Crypto.randomUUID(),
      itemOpportunityId: phase.plan.itemOpportunityId,
      kind: 'submit_response',
      sessionId,
    };
    // Persisted *before* the request, never after: if the response is lost, the key and the exact
    // body survive. The server fingerprints the body into the idempotency record, so a replay must
    // resend the saved body — one reconstructed later would fail the fingerprint check, and
    // client_elapsed_ms is unrecoverable after a relaunch.
    await savePendingCommand(command);
    await sendSubmit(command);
  }, [answer, phase, sendSubmit, sessionId, submitting]);

  const tryAgain = useCallback(() => {
    if (phase.kind !== 'question') return;
    setOutcome(null);
    setAnswer(initialAnswerState(phase.plan.spec));
    shownAtRef.current = Date.now();
  }, [phase]);

  useEffect(() => {
    mountedRef.current = true;
    if (!api) {
      setPhase({ kind: 'failure', failure: 'technical', requestId: null });
    } else {
      void presentOpportunity();
    }
    return () => {
      mountedRef.current = false;
    };
  }, [api, presentOpportunity]);

  const goHome = useCallback(() => router.replace('/(learner)/home'), []);

  if (phase.kind === 'loading') {
    return (
      <SessionFrame>
        <View style={styles.centered}>
          <ActivityIndicator color={colors.primary} size="large" />
          <AppText align="center" style={styles.muted}>
            Getting your question ready…
          </AppText>
        </View>
      </SessionFrame>
    );
  }

  if (phase.kind === 'unrenderable' || phase.kind === 'failure') {
    // The fail-closed screen. Neutral, child-appropriate, one way forward, and a support code a
    // grown-up can quote. Never a free-text box: a text input shown against a question whose
    // answer surface could not be resolved lets a child submit something the item cannot accept
    // and then be told they were wrong.
    const copy =
      phase.kind === 'unrenderable'
        ? { title: "This one isn't ready", detail: "Let's head back and try again soon." }
        : failureCopy[phase.failure];
    const supportCode = phase.requestId;
    return (
      <SessionFrame>
        <View style={styles.centered}>
          <View style={styles.iconCircle}>
            <Ionicons color={colors.primary} name="alert-circle-outline" size={44} />
          </View>
          <AppText align="center" variant="title">
            {copy.title}
          </AppText>
          <AppText align="center" style={styles.muted}>
            {copy.detail}
          </AppText>
          {supportCode ? (
            <AppText align="center" style={styles.supportCode}>
              Support code: {supportCode}
            </AppText>
          ) : null}
          <PrimaryButton label="BACK TO HOME" onPress={goHome} />
        </View>
      </SessionFrame>
    );
  }

  const { plan } = phase;
  const encoded = answer ? encodeSubmittedValue(plan.spec, answer) : null;
  const view = outcome ? outcomeView(outcome) : null;
  // The deadline is read, and then deliberately does not gate anything (see
  // isAnswerSurfaceDisabled for the soft-lock reasoning). There is no countdown and no "time is
  // running out" warning: a ticking clock in front of a seven-year-old is an anxiety device, and
  // it would be counting down to something the client cannot enforce anyway. The child answers,
  // the server rules TIMEOUT, and the neutral outcome copy tells them.
  const answeringDisabled = isAnswerSurfaceDisabled({
    deadlinePassed: isDeadlinePassed(plan.timeoutDeadlineUtc, Date.now()),
    hasOutcome: outcome !== null,
    submitting,
  });
  // Submit is unavailable precisely when there is nothing submittable: no selection yet, a blank
  // expanded_form, an unset count. That mirrors the server's own min_length=1, so the disabled
  // state prevents a guaranteed 422 — it is not a correctness judgement about the answer. It is
  // never unavailable because time has run out; that submit is what records the TIMEOUT.
  const canSubmit = encoded !== null && !answeringDisabled;

  return (
    <SessionFrame>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.skillPill}>
          <Ionicons color={colors.primaryShadow} name="sparkles" size={16} />
          <AppText style={styles.skillText}>{plan.skillLabel || 'Maths'}</AppText>
        </View>

        <View style={styles.promptCard}>
          <AppText style={styles.stem}>{plan.stem}</AppText>
        </View>

        {answer?.kind === 'choice' && plan.spec.kind === 'choice' ? (
          <ChoiceGrid
            disabled={answeringDisabled}
            onChange={setAnswer}
            spec={plan.spec}
            state={answer}
          />
        ) : null}
        {answer?.kind === 'free-entry' && plan.spec.kind === 'free-entry' ? (
          <FreeEntry
            disabled={answeringDisabled}
            onChange={setAnswer}
            spec={plan.spec}
            state={answer}
          />
        ) : null}
        {answer?.kind === 'count-selection' && plan.spec.kind === 'count-selection' ? (
          <CountSelection
            disabled={answeringDisabled}
            onChange={setAnswer}
            spec={plan.spec}
            state={answer}
          />
        ) : null}

        {view ? (
          <View
            style={[
              styles.outcomeCard,
              outcome === 'correct' && styles.outcomeCorrect,
              outcome === 'incorrect' && styles.outcomeIncorrect,
            ]}>
            <AppText style={styles.outcomeTitle}>{view.title}</AppText>
            <AppText style={styles.muted}>{view.detail}</AppText>
          </View>
        ) : null}

        {view?.canTryAgain ? <PrimaryButton label="TRY AGAIN" onPress={tryAgain} /> : null}
        {view && !view.canTryAgain ? <PrimaryButton label="BACK TO HOME" onPress={goHome} /> : null}
        {!view ? (
          <PrimaryButton
            busy={submitting}
            disabled={!canSubmit}
            label="CHECK MY ANSWER"
            onPress={() => void submitAnswer()}
          />
        ) : null}
      </ScrollView>
    </SessionFrame>
  );
}

function SessionFrame({ children }: { children: React.ReactNode }) {
  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.canvas}>{children}</View>
    </SafeAreaView>
  );
}

function PrimaryButton({
  busy = false,
  disabled = false,
  label,
  onPress,
}: {
  busy?: boolean;
  disabled?: boolean;
  label: string;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || busy }}
      disabled={disabled || busy}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        (disabled || busy) && styles.buttonDisabled,
        pressed && !disabled && !busy && styles.pressed,
      ]}>
      {busy ? (
        <ActivityIndicator color={colors.primaryForeground} size="small" />
      ) : (
        <AppText style={styles.buttonText}>{label}</AppText>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    alignSelf: 'stretch',
    backgroundColor: colors.primary,
    borderColor: colors.surface1,
    borderRadius: radius.md,
    borderWidth: 2,
    justifyContent: 'center',
    minHeight: 62,
    paddingHorizontal: spacing.lg,
  },
  buttonDisabled: { opacity: 0.5 },
  buttonText: {
    color: colors.primaryForeground,
    fontFamily: typography.fonts.bold,
    fontSize: 17,
    letterSpacing: typography.letterSpacing.button,
  },
  canvas: { alignSelf: 'center', backgroundColor: colors.background, flex: 1, maxWidth: 500, width: '100%' },
  centered: { alignItems: 'center', flex: 1, gap: spacing.md, justifyContent: 'center', padding: spacing.lg },
  iconCircle: {
    alignItems: 'center',
    backgroundColor: colors.primarySoft,
    borderRadius: radius.xl,
    height: 88,
    justifyContent: 'center',
    width: 88,
  },
  muted: { color: colors.textSecondary },
  outcomeCard: {
    backgroundColor: colors.surface2,
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderWidth: 2,
    gap: spacing.xs,
    padding: spacing.md,
  },
  outcomeCorrect: { backgroundColor: '#e9f8f1', borderColor: colors.success },
  outcomeIncorrect: { backgroundColor: colors.secondarySoft, borderColor: colors.secondary },
  outcomeTitle: {
    fontFamily: typography.fonts.display,
    fontSize: typography.fontSize.subtitle,
    lineHeight: typography.lineHeight.subtitle,
  },
  pressed: { opacity: 0.85 },
  promptCard: {
    backgroundColor: colors.surface1,
    borderBottomColor: colors.borderStrong,
    borderBottomWidth: 3,
    borderColor: colors.border,
    borderRadius: radius.lg,
    borderWidth: 2,
    padding: spacing.md,
  },
  safeArea: { backgroundColor: colors.background, flex: 1 },
  scroll: { gap: spacing.md, padding: spacing.md, paddingBottom: spacing.xl },
  skillPill: {
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: colors.primarySoft,
    borderRadius: radius.pill,
    flexDirection: 'row',
    gap: spacing.xs,
    paddingHorizontal: spacing.smPlus,
    paddingVertical: spacing.xs,
  },
  skillText: {
    color: colors.primaryShadow,
    fontFamily: typography.fonts.bold,
    fontSize: typography.fontSize.sm,
    letterSpacing: typography.letterSpacing.label,
  },
  stem: {
    fontFamily: typography.fonts.display,
    fontSize: typography.fontSize.subtitle,
    lineHeight: typography.lineHeight.subtitle,
    maxWidth: '100%',
  },
  supportCode: { color: colors.textMuted, fontSize: typography.fontSize.xs },
});
