import type {
  ApiErrorEnvelope,
  AuthenticatedPrincipal,
  HealthReadyResponse,
  InviteResolveResponse,
  InviteTokenRequest,
  LearnerMembershipListItem,
  LearnerMembershipListResponse,
  LearnerProfileResponse,
  MembershipRequestResponse,
  PendingStartSessionCommand,
  ProfileCreateRequest,
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

export function isProfileCreateRequest(value: unknown): value is ProfileCreateRequest {
  return isRecord(value) && isNonEmptyString(value.name);
}

export function isInviteTokenRequest(value: unknown): value is InviteTokenRequest {
  return isRecord(value) && isNonEmptyString(value.invite_token);
}

const classroomGrades = new Set(['GRADE_2', 'GRADE_3']);
const membershipStates = new Set(['PENDING', 'APPROVED', 'REJECTED']);

export function isInviteResolveResponse(value: unknown): value is InviteResolveResponse {
  if (!isRecord(value)) return false;
  return (
    isNonEmptyString(value.invite_resolution_id) &&
    (value.classroom_name === null || typeof value.classroom_name === 'string') &&
    typeof value.grade === 'string' &&
    classroomGrades.has(value.grade) &&
    isNonEmptyString(value.request_id)
  );
}

export function isMembershipRequestResponse(value: unknown): value is MembershipRequestResponse {
  if (!isRecord(value)) return false;
  return (
    isNonEmptyString(value.classroom_membership_id) &&
    isNonEmptyString(value.classroom_id) &&
    (value.classroom_name === null || typeof value.classroom_name === 'string') &&
    typeof value.grade === 'string' &&
    classroomGrades.has(value.grade) &&
    typeof value.state === 'string' &&
    membershipStates.has(value.state) &&
    isNonEmptyString(value.requested_at_utc) &&
    isNonEmptyString(value.request_id)
  );
}

function isLearnerMembershipListItem(value: unknown): value is LearnerMembershipListItem {
  if (!isRecord(value)) return false;
  return (
    isNonEmptyString(value.membership_id) &&
    isNonEmptyString(value.classroom_id) &&
    (value.classroom_name === null || typeof value.classroom_name === 'string') &&
    typeof value.grade === 'string' &&
    classroomGrades.has(value.grade) &&
    typeof value.state === 'string' &&
    membershipStates.has(value.state) &&
    isNonEmptyString(value.requested_at_utc) &&
    (value.decided_at_utc === null || typeof value.decided_at_utc === 'string')
  );
}

export function isLearnerMembershipListResponse(
  value: unknown,
): value is LearnerMembershipListResponse {
  return (
    isRecord(value) &&
    Array.isArray(value.memberships) &&
    value.memberships.every(isLearnerMembershipListItem) &&
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
