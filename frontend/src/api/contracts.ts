import type {
  AuthenticatedPrincipal,
  InviteResolveResponse,
  InviteTokenRequest,
  LearnerMembershipListItem,
  LearnerMembershipListResponse,
  LearnerProfileResponse,
  MembershipRequestResponse,
  ProfileCreateRequest,
  ReadinessResponse,
  SessionCommandResponse,
} from '@/src/api/generated/openapi-types';

export type {
  AuthenticatedPrincipal,
  InviteResolveResponse,
  InviteTokenRequest,
  LearnerMembershipListItem,
  LearnerMembershipListResponse,
  LearnerProfileResponse,
  MembershipRequestResponse,
  ProfileCreateRequest,
  SessionCommandResponse,
};

// GET /api/v1/me returns only the bare principal. Role/profile resolution is a separate call
// (GET /api/v1/learner/profile); this app is child-facing only, so a null learnerProfile means
// "no learner profile yet" (onboarding), never a teacher/operator role check. classroomMembership
// is the most relevant membership (see pickMembership) from GET /api/v1/learner/classrooms; null
// means no membership has been requested yet. 'authorized' status requires both a profile and an
// APPROVED membership — see auth-context.tsx's authorizeSession.
export type AuthorizedLearner = {
  principal: AuthenticatedPrincipal;
  learnerProfile: LearnerProfileResponse | null;
  classroomMembership: LearnerMembershipListItem | null;
};

export type ApiFieldIssue = { field: string; code: string };

// The live error envelope is `{ schema_version, error: { code, message, request_id, details } }`
// (app/core/errors.py ErrorResponse/ErrorBody) — nested, and without a `retryable` field.
// FastAPI does not auto-register custom-exception-handler responses in the generated OpenAPI, so
// that true shape has no component schema to freeze/reconcile against yet (BEplan §10 step 10
// needs a shared frozen artefact for both sides to check against). Tracked as a follow-up to add
// explicit `responses=` schema annotations on every route; left unchanged for this batch.
export type ApiErrorEnvelope = {
  code: string;
  message: string;
  request_id: string;
  retryable: boolean;
  details?: ApiFieldIssue[];
};

// Matches the live `/health/ready` contract exactly (generated from the frozen OpenAPI).
export type HealthReadyResponse = ReadinessResponse;

export type PendingStartSessionCommand = {
  kind: 'start_session';
  endpoint: '/api/v1/b/sessions';
  idempotencyKey: string;
  createdAt: string;
};
