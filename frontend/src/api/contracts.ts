export type MeResponse = {
  user_id: string;
  roles: ('learner' | 'supervisor' | 'operator')[];
  learner: {
    learner_id: string;
    grade: 2 | 3;
    active: boolean;
    display_name?: string;
  } | null;
  request_id: string;
};

export type ApiFieldIssue = { field: string; code: string };

export type ApiErrorEnvelope = {
  code: string;
  message: string;
  request_id: string;
  retryable: boolean;
  details?: ApiFieldIssue[];
};
