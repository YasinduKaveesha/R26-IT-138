import type { MeResponse } from '@/src/api/contracts';
import { ApiClientError } from '@/src/api/errors';
import { isApiErrorEnvelope, isMeResponse } from '@/src/api/runtime-validation';
import type { PublicConfig } from '@/src/config/env';

const REQUEST_TIMEOUT_MS = 10_000;
const SAFE_GET_RETRY_DELAY_MS = 300;

type RefreshAccessToken = () => Promise<string | null>;

async function wait(milliseconds: number) {
  await new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function requestMeOnce(config: PublicConfig, accessToken: string): Promise<MeResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let response: Response;

  try {
    response = await fetch(`${config.apiBaseUrl}/api/v1/me`, {
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        'X-Mobile-App-Version': '1.0.0',
      },
      method: 'GET',
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiClientError('timeout', 'The server took too long to respond.');
    }
    throw new ApiClientError('network', 'The server could not be reached.');
  } finally {
    clearTimeout(timeout);
  }

  const requestId = response.headers.get('x-request-id') ?? undefined;
  let body: unknown;

  try {
    body = JSON.parse(await response.text()) as unknown;
  } catch {
    throw new ApiClientError(
      'invalid-response',
      'The server returned an unsupported response.',
      response.status,
      requestId,
    );
  }

  if (!response.ok) {
    const envelope = isApiErrorEnvelope(body) ? body : undefined;
    const resolvedRequestId = envelope?.request_id ?? requestId;

    if (response.status === 401) {
      throw new ApiClientError(
        'unauthenticated',
        'The session is no longer valid.',
        response.status,
        resolvedRequestId,
        envelope,
      );
    }
    if (response.status === 403) {
      throw new ApiClientError(
        'forbidden',
        'This account is not approved for learner access.',
        response.status,
        resolvedRequestId,
        envelope,
      );
    }
    throw new ApiClientError(
      'server',
      'The server could not complete the request.',
      response.status,
      resolvedRequestId,
      envelope,
    );
  }

  if (!isMeResponse(body)) {
    throw new ApiClientError(
      'invalid-response',
      'The server returned an unsupported response.',
      response.status,
      requestId,
    );
  }

  return body;
}

export async function getAuthorizedLearner(
  config: PublicConfig,
  accessToken: string,
  refreshAccessToken: RefreshAccessToken,
) {
  try {
    return await requestMeOnce(config, accessToken);
  } catch (error) {
    if (!(error instanceof ApiClientError)) throw error;

    if (error.kind === 'unauthenticated') {
      const refreshedAccessToken = await refreshAccessToken();
      if (!refreshedAccessToken) throw error;
      return requestMeOnce(config, refreshedAccessToken);
    }

    if (
      error.kind === 'network' ||
      error.kind === 'timeout' ||
      (error.kind === 'server' && (error.status ?? 0) >= 500)
    ) {
      await wait(SAFE_GET_RETRY_DELAY_MS);
      return requestMeOnce(config, accessToken);
    }

    throw error;
  }
}
