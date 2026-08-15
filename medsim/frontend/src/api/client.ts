/**
 * HTTP client.
 *
 * The interesting behaviour here is failure handling, because this application
 * is explicitly a QA target: the Phase 3 suite drives it through SSL errors,
 * dropped connections, truncated bodies and malformed JSON, and the client has
 * to turn each of those into a distinguishable, renderable error rather than an
 * unhandled promise rejection.
 *
 * The five failure classes the UI distinguishes:
 *
 *   ApiNetworkError  - the request never completed (DNS, TLS, reset, offline).
 *                      A `fetch` rejection, which is all the browser tells us;
 *                      an untrusted proxy certificate is indistinguishable from
 *                      a pulled cable at this layer, which is itself worth
 *                      surfacing honestly rather than guessing.
 *   ApiTimeoutError  - we gave up (AbortController), distinct from a reset.
 *   ApiParseError    - a 2xx whose body is not the JSON it claimed to be. This
 *                      is the signature of a rewriting proxy and is the one
 *                      most applications crash on.
 *   ApiStatusError   - a well-formed non-2xx carrying the RFC-7807 body.
 *   ApiAbortError    - we cancelled deliberately (component unmounted, the
 *                      user typed another character). Never shown to the user.
 */

import type {
  ApiErrorBody,
  CaseDetail,
  CaseListResponse,
  CaseQuery,
  CaseTrends,
  ReferenceInterval,
  StatsResponse,
} from './types';

const BASE = import.meta.env.VITE_API_BASE ?? '/api/v1';
const DEFAULT_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS ?? 15_000);

export class ApiError extends Error {
  readonly requestId: string | null;
  constructor(message: string, requestId: string | null = null) {
    super(message);
    this.name = new.target.name;
    this.requestId = requestId;
  }
}

export class ApiNetworkError extends ApiError {
  readonly cause?: unknown;
  constructor(message: string, cause?: unknown) {
    super(message);
    this.cause = cause;
  }
}

export class ApiTimeoutError extends ApiError {}

export class ApiAbortError extends ApiError {}

export class ApiParseError extends ApiError {
  /** The first 500 characters of the body, for the console and bug reports. */
  readonly rawBody: string;
  readonly contentType: string | null;
  constructor(message: string, rawBody: string, contentType: string | null, requestId: string | null) {
    super(message, requestId);
    this.rawBody = rawBody.slice(0, 500);
    this.contentType = contentType;
  }
}

export class ApiStatusError extends ApiError {
  readonly status: number;
  readonly body: ApiErrorBody | null;
  constructor(status: number, body: ApiErrorBody | null, requestId: string | null) {
    super(body?.detail || body?.title || `Request failed with status ${status}`, requestId);
    this.status = status;
    this.body = body;
  }
  get isNotFound(): boolean {
    return this.status === 404;
  }
  get isServer(): boolean {
    return this.status >= 500;
  }
}

export interface RequestOptions {
  signal?: AbortSignal;
  timeoutMs?: number;
  /**
   * Chaos headers, forwarded verbatim. Only the QA suite sets these; the
   * backend ignores them entirely when MEDSIM_CHAOS_ENABLED is false, and it
   * refuses to boot with chaos enabled in production.
   */
  headers?: Record<string, string>;
}

function buildQuery(params: Record<string, unknown> | undefined): string {
  if (!params) return '';
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue;
    if (Array.isArray(value)) {
      value.forEach((v) => search.append(key, String(v)));
    } else {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : '';
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { signal, timeoutMs = DEFAULT_TIMEOUT_MS, headers = {} } = options;

  // Compose the caller's signal with our timeout so either can abort the call.
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(new DOMException('timeout', 'TimeoutError')), timeoutMs);
  const onExternalAbort = () => controller.abort(signal?.reason);
  signal?.addEventListener('abort', onExternalAbort, { once: true });

  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      signal: controller.signal,
      headers: { Accept: 'application/json', ...headers },
      credentials: 'same-origin',
    });
  } catch (error) {
    // Distinguish "we cancelled", "we timed out" and "the network failed".
    if (signal?.aborted) {
      throw new ApiAbortError('Request cancelled');
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiTimeoutError(`Request timed out after ${timeoutMs} ms`);
    }
    // A TypeError from fetch covers DNS failure, connection reset, an untrusted
    // TLS certificate (an intercepting proxy without its CA installed), CORS
    // rejection and offline. The browser deliberately does not tell us which,
    // so we must not claim to know.
    throw new ApiNetworkError('Network request failed', error);
  } finally {
    window.clearTimeout(timeoutId);
    signal?.removeEventListener('abort', onExternalAbort);
  }

  const requestId = response.headers.get('X-Request-ID');
  const contentType = response.headers.get('Content-Type');

  // Read the body as text FIRST. `response.json()` throws a SyntaxError that
  // discards the body, and the body is exactly what a bug report about a
  // rewriting proxy needs.
  const text = await response.text().catch(() => '');

  if (!response.ok) {
    let body: ApiErrorBody | null = null;
    try {
      body = text ? (JSON.parse(text) as ApiErrorBody) : null;
    } catch {
      // A non-2xx whose body is also unparseable - an appliance error page
      // rather than our API. Still a status error; the body is just unusable.
      body = null;
    }
    throw new ApiStatusError(response.status, body, requestId);
  }

  if (response.status === 204 || text.length === 0) {
    return undefined as T;
  }

  try {
    return JSON.parse(text) as T;
  } catch (error) {
    if (import.meta.env.DEV || import.meta.env.VITE_LOG_RAW_BODIES === 'true') {
      console.error('[api] unparseable 2xx response', {
        path,
        status: response.status,
        contentType,
        requestId,
        rawBody: text.slice(0, 2000),
        error,
      });
    }
    throw new ApiParseError(
      'Response body was not valid JSON',
      text,
      contentType,
      requestId,
    );
  }
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

export const api = {
  listCases(query: CaseQuery = {}, options?: RequestOptions): Promise<CaseListResponse> {
    return request<CaseListResponse>(`/cases${buildQuery(query as Record<string, unknown>)}`, options);
  },

  getCase(identifier: string, options?: RequestOptions): Promise<CaseDetail> {
    return request<CaseDetail>(`/cases/${encodeURIComponent(identifier)}`, options);
  },

  getTrends(identifier: string, analytes?: string[], options?: RequestOptions): Promise<CaseTrends> {
    return request<CaseTrends>(
      `/cases/${encodeURIComponent(identifier)}/trends${buildQuery({ analytes })}`,
      options,
    );
  },

  getStats(options?: RequestOptions): Promise<StatsResponse> {
    return request<StatsResponse>('/cases/stats', options);
  },

  getReferenceIntervals(category?: string, options?: RequestOptions): Promise<ReferenceInterval[]> {
    return request<ReferenceInterval[]>(`/reference/intervals${buildQuery({ category })}`, options);
  },

  getEnums(options?: RequestOptions): Promise<Record<string, string[]>> {
    return request<Record<string, string[]>>('/reference/enums', options);
  },
};

/**
 * Maps any thrown value to the i18n key describing it. Centralised so every
 * error surface in the app describes the same failure the same way.
 */
export function errorMessageKey(error: unknown): string {
  if (error instanceof ApiTimeoutError) return 'errors.timeout';
  if (error instanceof ApiNetworkError) return 'errors.network';
  if (error instanceof ApiParseError) return 'errors.parse';
  if (error instanceof ApiStatusError) {
    if (error.isNotFound) return 'errors.notFound';
    if (error.isServer) return 'errors.server';
  }
  return 'errors.generic';
}

export function errorRequestId(error: unknown): string | null {
  return error instanceof ApiError ? error.requestId : null;
}
