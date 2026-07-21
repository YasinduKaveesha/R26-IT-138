import type { ApiErrorEnvelope, MeResponse } from '@/src/api/contracts';

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

export function isMeResponse(value: unknown): value is MeResponse {
  if (!isRecord(value)) return false;

  const validRoles = new Set(['learner', 'supervisor', 'operator']);
  const rolesAreValid =
    Array.isArray(value.roles) &&
    value.roles.every((role) => typeof role === 'string' && validRoles.has(role));

  const learner = value.learner;
  const learnerIsValid =
    learner === null ||
    (isRecord(learner) &&
      isNonEmptyString(learner.learner_id) &&
      (learner.grade === 2 || learner.grade === 3) &&
      typeof learner.active === 'boolean' &&
      (learner.display_name === undefined || typeof learner.display_name === 'string'));

  return (
    isNonEmptyString(value.user_id) &&
    rolesAreValid &&
    learnerIsValid &&
    isNonEmptyString(value.request_id)
  );
}
