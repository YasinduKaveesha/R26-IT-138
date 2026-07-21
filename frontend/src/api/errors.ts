import type { ApiErrorEnvelope } from '@/src/api/contracts';

export type ApiErrorKind =
  | 'forbidden'
  | 'invalid-response'
  | 'network'
  | 'server'
  | 'timeout'
  | 'unauthenticated';

export class ApiClientError extends Error {
  constructor(
    public readonly kind: ApiErrorKind,
    message: string,
    public readonly status?: number,
    public readonly requestId?: string,
    public readonly envelope?: ApiErrorEnvelope,
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}
