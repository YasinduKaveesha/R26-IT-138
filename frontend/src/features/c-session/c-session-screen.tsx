// The C session shell: state wiring and the actual network calls only. Every decision lives in
// c-session-logic.ts, mirroring live-session-screen.tsx / live-session-logic.ts's split for
// Component B.
//
// The loop is create/resume -> nextTask -> resolveArchetype (via planTask) -> (surface, which does
// not exist yet in this batch) -> submitAction. Every task renders FailClosedFrame today, because
// archetype-surfaces.ts returns `null` for all eight archetype ids -- 10a...10h populate it. The
// submit wiring below (`handleSubmit`) is built now so a later surface plugs in without this file
// changing: nothing calls it yet, because there is no interactive surface capable of producing a
// payload to submit.
//
// This file does not implement Component B's refresh-on-401 retry (`withToken` in
// live-session-screen.tsx). That is a deliberate simplification, not a hidden gap: the C API client
// has never issued a live request in this project (session creation refuses while seven parameter
// families are unsigned), so there is nothing yet to exercise a refresh against, and adding it
// speculatively would be more than this batch's own loop needs. Recorded in the register entry.
//
// `api` is resolved the same null-safe way Component B's screen resolves it
// (live-session-screen.tsx:87-90): `readPublicConfig()` first, and `createComponentCApi` is called
// only when there is a config to give it OR the development fixture is active (which needs no
// config). Calling `createComponentCApi()` unconditionally with no config, as an earlier draft of
// this file did, throws inside `useMemo` during render whenever neither is true -- a render-time
// throw the component's own failure path can never catch, since it never runs. `api` can therefore
// be `null`, and every function below checks for that before using it.

import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, AppState, Pressable, StyleSheet, View } from 'react-native';

import { createComponentCApi, getComponentCDevelopmentFixture } from '@/src/api/component-c-api';
import { ApiClientError } from '@/src/api/errors';
import type { CNextTaskResponse, CreateCSessionRequest } from '@/src/api/generated/openapi-types';
import { useAuth } from '@/src/auth/auth-context';
import { AppText } from '@/src/components/app-text';
import { ScreenShell } from '@/src/components/screen-shell';
import { readPublicConfig } from '@/src/config/env';
import { resolveArchetypeSurface } from '@/src/features/c-session/archetype-surfaces';
import { encodeActionPayload } from '@/src/features/c-session/archetypes/encode-action-payload';
import {
  classifySessionFailure,
  decideSessionBootstrap,
  planTask,
} from '@/src/features/c-session/c-session-logic';
import { FailClosedFrame } from '@/src/features/c-session/fail-closed-frame';
import { NeutralMessageScreen } from '@/src/features/c-session/neutral-message-screen';
import { TechnicalBlockScreen } from '@/src/features/c-session/technical-block-screen';
import {
  recordActionSubmitted,
  recordBackgrounded,
  recordForegrounded,
  recordTaskOffered,
  recordTaskStarted,
  recordTechnicalIssue,
} from '@/src/features/c-session/telemetry';
import { colors, radius, spacing, typography } from '@/src/theme/tokens';

export type CSessionScreenProps = {
  // Not decided or invented by this screen -- see c-session-logic.ts's decideSessionBootstrap
  // doc comment. Optional and, in this batch, ordinarily absent: nothing upstream supplies them
  // yet, so the create path fails closed to the "not ready" screen rather than fabricating either
  // value.
  grade?: number;
  sessionMode?: CreateCSessionRequest['session_mode'];
};

type Phase =
  | { kind: 'loading' }
  | { kind: 'task'; task: CNextTaskResponse }
  | { kind: 'fail-closed'; supportCode: string | null }
  | { kind: 'technical-block'; supportCode: string | null }
  | { kind: 'failure'; supportCode: string | null; copy: { title: string; detail: string } }
  | { kind: 'not-ready' };

const FAILURE_COPY: Record<'authentication' | 'network' | 'technical', { title: string; detail: string }> = {
  authentication: { title: 'Sign-in needed', detail: 'Ask a grown-up to help you sign in again.' },
  network: { title: 'No connection', detail: 'Check the internet and try again in a moment.' },
  technical: { title: 'Something went wrong', detail: 'Try again in a little while.' },
};

export function CSessionScreen({ grade, sessionMode }: CSessionScreenProps) {
  const { getAccessToken } = useAuth();
  const configResult = useMemo(() => readPublicConfig(), []);
  // Null-safe by construction: createComponentCApi() with no config and no active fixture throws
  // (component-c-api.ts:145-147), and calling that inside useMemo during render would crash the
  // component tree rather than route through this screen's own failure path. The fixture check
  // needs no config at all, so it is tried before treating a missing config as fatal.
  const api = useMemo(() => {
    if (configResult.config) return createComponentCApi(configResult.config);
    if (getComponentCDevelopmentFixture()) return createComponentCApi();
    return null;
  }, [configResult.config]);
  const [phase, setPhase] = useState<Phase>({ kind: 'loading' });
  const cSessionIdRef = useRef<string | null>(null);
  const mountedRef = useRef(true);
  const backgroundedRef = useRef(false);

  const goHome = useCallback(() => router.replace('/(learner)/home'), []);

  const routeFailure = useCallback((error: unknown) => {
    if (!mountedRef.current) return;
    const supportCode = error instanceof ApiClientError ? error.requestId ?? null : null;
    const kind = classifySessionFailure(error);
    if (kind === 'network') {
      recordTechnicalIssue(
        error instanceof ApiClientError && error.kind === 'timeout' ? 'timeout' : 'network',
      );
    }
    if (kind === 'technical-block') {
      setPhase({ kind: 'technical-block', supportCode });
      return;
    }
    setPhase({ kind: 'failure', supportCode, copy: FAILURE_COPY[kind] });
  }, []);

  const loadNextTask = useCallback(
    async (cSessionId: string, accessToken: string) => {
      if (!api) return;
      try {
        const task = await api.nextTask(cSessionId, accessToken);
        if (!mountedRef.current) return;
        recordTaskOffered();
        const plan = planTask(task);
        if (plan.kind === 'fail-closed') {
          setPhase({ kind: 'fail-closed', supportCode: task.request_id });
          return;
        }
        const Surface = resolveArchetypeSurface(plan.archetypeId);
        if (!Surface) {
          // Resolved to a real archetype, but no surface is registered for it yet -- still
          // fail-closed, never a guessed rendering, but structurally a different reason than an
          // unresolvable template (see planTask's own doc comment).
          setPhase({ kind: 'fail-closed', supportCode: task.request_id });
          return;
        }
        recordTaskStarted();
        setPhase({ kind: 'task', task });
      } catch (error) {
        routeFailure(error);
      }
    },
    [api, routeFailure],
  );

  // Reserved for the surface that will eventually plug into archetype-surfaces.ts. Nothing calls
  // this in the current batch -- there is no rendered surface capable of producing a payload -- but
  // it is wired now so a later archetype lands without this file changing.
  const handleSubmit = useCallback(
    async (
      cSessionId: string,
      task: CNextTaskResponse,
      accessToken: string,
      values: Record<string, unknown>,
    ) => {
      if (!api) return;
      const payload = encodeActionPayload(task.valid_action_space, values);
      if (payload === null) return;
      try {
        await api.submitAction(
          cSessionId,
          task.c_task_instance_id,
          { action_payload: payload },
          accessToken,
        );
        recordActionSubmitted();
        await loadNextTask(cSessionId, accessToken);
      } catch (error) {
        routeFailure(error);
      }
    },
    [api, loadNextTask, routeFailure],
  );
  void handleSubmit;

  const bootstrap = useCallback(async () => {
    if (!api) return;
    setPhase({ kind: 'loading' });
    try {
      const accessToken = await getAccessToken();
      if (!accessToken) throw new ApiClientError('unauthenticated', 'No access token is available.');
      const active = await api.getActiveSession(accessToken);
      const decision = decideSessionBootstrap(active, grade, sessionMode);
      if (decision.action === 'not-ready') {
        if (!mountedRef.current) return;
        setPhase({ kind: 'not-ready' });
        return;
      }
      if (decision.action === 'resume') {
        cSessionIdRef.current = decision.cSessionId;
        await loadNextTask(decision.cSessionId, accessToken);
        return;
      }
      const created = await api.createSession(decision.body, accessToken);
      cSessionIdRef.current = created.c_session_id;
      await loadNextTask(created.c_session_id, accessToken);
    } catch (error) {
      routeFailure(error);
    }
  }, [api, getAccessToken, grade, loadNextTask, routeFailure, sessionMode]);

  const leaveSession = useCallback(async () => {
    const cSessionId = cSessionIdRef.current;
    if (!cSessionId) {
      goHome();
      return;
    }
    if (!api) {
      goHome();
      return;
    }
    try {
      const accessToken = await getAccessToken();
      if (!accessToken) throw new ApiClientError('unauthenticated', 'No access token is available.');
      await api.abandonSession(cSessionId, accessToken);
      goHome();
    } catch (error) {
      // Under the development fixture abandonSession always throws by design (10.0b-i/-fix; not
      // widened here) -- that surfaces as an ordinary routed failure below, which is correct
      // behaviour for this batch, not a defect.
      routeFailure(error);
    }
  }, [api, getAccessToken, goHome, routeFailure]);

  useEffect(() => {
    mountedRef.current = true;
    if (!api) {
      // No config and no active fixture -- the same "technical" bucket an unconfigured B screen
      // routes to (live-session-screen.tsx:425-427), reached through this screen's own failure
      // path rather than a render-time throw.
      setPhase({ kind: 'failure', supportCode: null, copy: FAILURE_COPY.technical });
    } else {
      void bootstrap();
    }
    return () => {
      mountedRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api]);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'active' && backgroundedRef.current) {
        backgroundedRef.current = false;
        recordForegrounded();
      } else if (state !== 'active' && !backgroundedRef.current) {
        backgroundedRef.current = true;
        recordBackgrounded();
      }
    });
    return () => subscription.remove();
  }, []);

  if (phase.kind === 'loading') {
    return (
      <ScreenShell centered>
        <ActivityIndicator color={colors.primary} size="large" />
        <AppText align="center" style={styles.muted}>
          Getting your session ready…
        </AppText>
      </ScreenShell>
    );
  }

  if (phase.kind === 'not-ready') {
    return (
      <NeutralMessageScreen
        detail="This session isn't ready yet. Please check back soon."
        onExit={goHome}
        supportCode={null}
        title="Not ready yet"
      />
    );
  }

  if (phase.kind === 'fail-closed') {
    return <FailClosedFrame onExit={goHome} supportCode={phase.supportCode} />;
  }

  if (phase.kind === 'technical-block') {
    return <TechnicalBlockScreen onExit={goHome} supportCode={phase.supportCode} />;
  }

  if (phase.kind === 'failure') {
    return (
      <NeutralMessageScreen
        detail={phase.copy.detail}
        onExit={goHome}
        supportCode={phase.supportCode}
        title={phase.copy.title}
      />
    );
  }

  // phase.kind === 'task'. No archetype surface exists in this batch, so this branch is currently
  // unreachable in practice (loadNextTask only sets it once resolveArchetypeSurface returns a
  // component) -- kept because the loop must already know how to render one when 10a...10h land.
  return (
    <ScreenShell centered>
      <View style={styles.iconCircle}>
        <Ionicons color={colors.primary} name="hourglass-outline" size={44} />
      </View>
      <AppText align="center" variant="title">
        Getting ready…
      </AppText>
      <Pressable
        accessibilityRole="button"
        onPress={() => void leaveSession()}
        style={({ pressed }) => [styles.leaveButton, pressed && styles.pressed]}>
        <AppText style={styles.leaveButtonText}>LEAVE SESSION</AppText>
      </Pressable>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  iconCircle: {
    alignItems: 'center',
    backgroundColor: colors.primarySoft,
    borderRadius: radius.xl,
    height: 88,
    justifyContent: 'center',
    width: 88,
  },
  leaveButton: {
    alignItems: 'center',
    alignSelf: 'stretch',
    backgroundColor: colors.surface1,
    borderColor: colors.border,
    borderRadius: radius.md,
    borderWidth: 2,
    justifyContent: 'center',
    minHeight: 56,
    paddingHorizontal: spacing.lg,
  },
  leaveButtonText: {
    fontFamily: typography.fonts.bold,
    fontSize: 15,
    letterSpacing: typography.letterSpacing.button,
  },
  muted: { color: colors.textSecondary },
  pressed: { opacity: 0.85 },
});
