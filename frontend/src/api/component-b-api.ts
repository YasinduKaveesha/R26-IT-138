import type { HealthReadyResponse, SessionCommandResponse } from '@/src/api/contracts';
import { requestJson } from '@/src/api/client';
import { ApiClientError } from '@/src/api/errors';
import { isHealthReadyResponse, isSessionCommandResponse } from '@/src/api/runtime-validation';
import type { PublicConfig } from '@/src/config/env';

type ComponentBApi = {
  checkReadiness: () => Promise<HealthReadyResponse>;
  startSession: (idempotencyKey: string, accessToken: string) => Promise<SessionCommandResponse>;
};

const fixtureFailures = new Set<string>();

function getDevelopmentFixture(): string | null {
  if (process.env.EXPO_PUBLIC_APP_ENV !== 'development') return null;
  const fixture = process.env.EXPO_PUBLIC_COMPONENT_B_DEV_FIXTURE?.trim();
  return fixture || null;
}

async function fixtureDelay() {
  await new Promise((resolve) => setTimeout(resolve, 650));
}

function createFixtureApi(fixture: string): ComponentBApi {
  return {
    async checkReadiness() {
      await fixtureDelay();
      if (fixture === 'readiness-failure') {
        throw new ApiClientError('unavailable', 'Development readiness fixture is unavailable.', 503, 'dev-ready-503');
      }
      return {
        status: 'ready',
        stage: 'infrastructure',
        request_id: 'dev-ready-ok',
        checks: {
          api_process: 'ok',
          database_connection: 'ok',
          generator: 'not_checked',
          catalogue: 'not_checked',
          runtime_bundle: 'not_checked',
          migrations: 'not_checked',
          authentication: 'not_checked',
        },
      };
    },
    async startSession(idempotencyKey) {
      await fixtureDelay();
      if (fixture === 'network-failure-once' && !fixtureFailures.has(idempotencyKey)) {
        fixtureFailures.add(idempotencyKey);
        throw new ApiClientError('network', 'Development fixture dropped the response.');
      }
      if (fixture === 'access-denied') {
        throw new ApiClientError('forbidden', 'Development access fixture denied the request.', 403, 'dev-forbidden');
      }
      return {
        created_at_utc: '2026-07-22T12:00:00Z',
        request_id: 'dev-start-ok',
        row_version: 1,
        runtime_bundle_version: 'development-fixture-only',
        session_id: 'dev-session-new-opaque',
        state: 'active',
      };
    },
  };
}

export function createComponentBApi(config?: PublicConfig): ComponentBApi {
  const fixture = getDevelopmentFixture();
  if (fixture) return createFixtureApi(fixture);
  if (!config) {
    throw new ApiClientError('unavailable', 'The Component B API is not configured.');
  }

  return {
    checkReadiness: () => requestJson(config, { method: 'GET', path: '/health/ready', validate: isHealthReadyResponse }),
    startSession: (idempotencyKey, accessToken) =>
      requestJson(config, {
        accessToken,
        idempotencyKey,
        method: 'POST',
        path: '/api/v1/b/sessions',
        validate: isSessionCommandResponse,
      }),
  };
}

export function getComponentBDevelopmentFixture() {
  return getDevelopmentFixture();
}
