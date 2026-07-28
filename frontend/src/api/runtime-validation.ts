import type {
  ApiErrorEnvelope,
  AuthenticatedPrincipal,
  HealthReadyResponse,
  LearnerProfileResponse,
  PendingStartSessionCommand,
  SessionCommandResponse,
} from '@/src/api/contracts';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

export function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (!isRecord(value)) return false;

  const detailsAreValid =
    value.details === undefined ||
    (Array.isArray(value.details) &&
      value.details.every(
        (issue) =>
          isRecord(issue) && isNonEmptyString(issue.field) && isNonEmptyString(issue.code),
      ));

  return (
    isNonEmptyString(value.code) &&
    isNonEmptyString(value.message) &&
    isNonEmptyString(value.request_id) &&
    typeof value.retryable === 'boolean' &&
    detailsAreValid
  );
}

export function isAuthenticatedPrincipal(value: unknown): value is AuthenticatedPrincipal {
  if (!isRecord(value)) return false;
  return (
    isNonEmptyString(value.user_id) &&
    (value.email === undefined || value.email === null || typeof value.email === 'string')
  );
}

export function isLearnerProfileResponse(value: unknown): value is LearnerProfileResponse {
  if (!isRecord(value)) return false;
  return (
    isNonEmptyString(value.learner_id) &&
    isNonEmptyString(value.user_id) &&
    isNonEmptyString(value.name) &&
    (value.email === null || typeof value.email === 'string') &&
    value.profile_type === 'LEARNER' &&
    isNonEmptyString(value.created_at_utc) &&
    isNonEmptyString(value.request_id)
  );
}

const sessionCommandStates = new Set(['active', 'completed', 'abandoned']);

export function isHealthReadyResponse(value: unknown): value is HealthReadyResponse {
  const checksAreValid =
    isRecord(value) &&
    isRecord(value.checks) &&
    Object.values(value.checks).every((entry) => typeof entry === 'string');

  return (
    isRecord(value) &&
    value.status === 'ready' &&
    value.stage === 'infrastructure' &&
    isNonEmptyString(value.request_id) &&
    checksAreValid
  );
}

export function isSessionCommandResponse(value: unknown): value is SessionCommandResponse {
  return (
    isRecord(value) &&
    isNonEmptyString(value.session_id) &&
    typeof value.state === 'string' &&
    sessionCommandStates.has(value.state) &&
    isNonEmptyString(value.runtime_bundle_version) &&
    isNonEmptyString(value.created_at_utc) &&
    Number.isInteger(value.row_version) &&
    isNonEmptyString(value.request_id)
  );
}

export function isPendingStartSessionCommand(value: unknown): value is PendingStartSessionCommand {
  if (!isRecord(value)) return false;
  return (
    value.kind === 'start_session' &&
    value.endpoint === '/api/v1/b/sessions' &&
    isNonEmptyString(value.idempotencyKey) &&
    isNonEmptyString(value.createdAt)
  );
}
