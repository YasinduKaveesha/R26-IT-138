import { requestJson } from '@/src/api/client';
import { ApiClientError } from '@/src/api/errors';
import {
  isCActiveSessionResponse,
  isCNextTaskResponse,
  isCSessionCommandResponse,
  isCSubmitActionResult,
} from '@/src/api/runtime-validation';
import type {
  CActiveSessionResponse,
  CNextTaskResponse,
  CompleteCSessionRequest,
  CreateCSessionRequest,
  CSessionCommandResponse,
  CSubmitActionRequest,
  CSubmitActionResult,
} from '@/src/api/generated/openapi-types';
import type { PublicConfig } from '@/src/config/env';

// None of the six Component C routes take an Idempotency-Key header. This is a deliberate
// backend divergence from Component B, not an omission to fix here — see
// backend/app/api/routes/c_session.py's module docstring: "no idempotency-key header (Phase
// 4a/4b ruling: v3.0 says only 'idempotent by learner state', which
// find_starting_or_active_for_learner already satisfies -- B's fuller idempotency-key/audit-
// event machinery is a scope expansion beyond that text, not built here)." Every C route file
// was checked; none declares one. No call below sends one.
type ComponentCApi = {
  createSession: (body: CreateCSessionRequest, accessToken: string) => Promise<CSessionCommandResponse>;
  getActiveSession: (accessToken: string) => Promise<CActiveSessionResponse>;
  abandonSession: (cSessionId: string, accessToken: string) => Promise<CSessionCommandResponse>;
  completeSession: (
    cSessionId: string,
    body: CompleteCSessionRequest,
    accessToken: string,
  ) => Promise<CSessionCommandResponse>;
  nextTask: (cSessionId: string, accessToken: string) => Promise<CNextTaskResponse>;
  submitAction: (
    cSessionId: string,
    cTaskInstanceId: string,
    body: CSubmitActionRequest,
    accessToken: string,
  ) => Promise<CSubmitActionResult>;
};

function getDevelopmentFixture(): string | null {
  if (process.env.EXPO_PUBLIC_APP_ENV !== 'development') return null;
  const fixture = process.env.EXPO_PUBLIC_COMPONENT_C_DEV_FIXTURE?.trim();
  return fixture || null;
}

function createFixtureApi(fixture: string): ComponentCApi {
  return {
    async createSession() {
      return {
        c_session_id: 'dev-c-session-new-opaque',
        state: 'active',
        session_mode: 'c_only',
        session_phase: 'development-fixture-only',
        grade: 3,
        started_at_utc: '2026-08-23T12:00:00Z',
        row_version: 1,
        request_id: 'dev-c-create-ok',
      };
    },
    // The fixture covers session creation and resumption only. The task loop — serving a
    // task, submitting an action, completing or abandoning a session — is deliberately left
    // unimplemented — an immediate throw, no delay, no fake payload — so a fixture run can
    // never masquerade as a real session past session creation. Restates Component B's own
    // fixture doctrine (see component-b-api.ts's createFixtureApi): whether the task loop's
    // prompt_payload can ever come from this fixture is an open follow-up outside this batch's
    // scope, not a seam left here to fill in later.
    async getActiveSession() {
      return {
        session: null,
        request_id: 'dev-c-active-ok',
      };
    },
    async abandonSession() {
      throw new ApiClientError('unavailable', 'The development fixture does not implement session abandonment.');
    },
    async completeSession() {
      throw new ApiClientError('unavailable', 'The development fixture does not implement session completion.');
    },
    async nextTask() {
      throw new ApiClientError('unavailable', 'The development fixture does not implement task serving.');
    },
    async submitAction() {
      throw new ApiClientError('unavailable', 'The development fixture does not implement action submission.');
    },
  };
}

export function createComponentCApi(config?: PublicConfig): ComponentCApi {
  const fixture = getDevelopmentFixture();
  if (fixture) return createFixtureApi(fixture);
  if (!config) {
    throw new ApiClientError('unavailable', 'The Component C API is not configured.');
  }

  return {
    createSession: (body, accessToken) =>
      requestJson(config, {
        accessToken,
        body,
        method: 'POST',
        path: '/api/v1/c/sessions',
        validate: isCSessionCommandResponse,
      }),
    getActiveSession: (accessToken) =>
      requestJson(config, {
        accessToken,
        method: 'GET',
        path: '/api/v1/c/sessions/active',
        validate: isCActiveSessionResponse,
      }),
    abandonSession: (cSessionId, accessToken) =>
      requestJson(config, {
        accessToken,
        method: 'POST',
        path: `/api/v1/c/sessions/${cSessionId}/abandon`,
        validate: isCSessionCommandResponse,
      }),
    completeSession: (cSessionId, body, accessToken) =>
      requestJson(config, {
        accessToken,
        body,
        method: 'POST',
        path: `/api/v1/c/sessions/${cSessionId}/complete`,
        validate: isCSessionCommandResponse,
      }),
    nextTask: (cSessionId, accessToken) =>
      requestJson(config, {
        accessToken,
        method: 'POST',
        path: `/api/v1/c/sessions/${cSessionId}/tasks/next`,
        validate: isCNextTaskResponse,
      }),
    submitAction: (cSessionId, cTaskInstanceId, body, accessToken) =>
      requestJson(config, {
        accessToken,
        body,
        method: 'POST',
        path: `/api/v1/c/sessions/${cSessionId}/tasks/${cTaskInstanceId}/actions`,
        validate: isCSubmitActionResult,
      }),
  };
}

export function getComponentCDevelopmentFixture() {
  return getDevelopmentFixture();
}
