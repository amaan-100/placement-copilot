import type {
  ApiErrorBody,
  Application,
  ApplicationList,
  ApplicationUpdate,
  ApproveResponse,
  Dashboard,
  DraftResponse,
  Health,
  InterviewEvaluation,
  InterviewStart,
  JobSearchResponse,
  LlmStatus,
  ResumeInfo,
  ResumeUpload,
  SessionInfo,
  Trace,
} from './types';

const API_BASE = (import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api').replace(
  /\/$/,
  '',
);
const SESSION_KEY = 'placement_copilot_session_id';
const SESSION_HEADER = 'X-Session-Id';
const REQUEST_TIMEOUT_MS = 180_000;
const WAKING_CODES = new Set([502, 503, 504]);

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId?: string;
  readonly details?: unknown;
  readonly retryable: boolean;

  constructor(
    message: string,
    status = 0,
    code = 'unknown_error',
    requestId?: string,
    details?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.requestId = requestId;
    this.details = details;
    this.retryable =
      code === 'network_error' ||
      code === 'server_waking' ||
      WAKING_CODES.has(status);
  }
}

function createId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (char) => {
    const random = (Math.random() * 16) | 0;
    const value = char === 'x' ? random : (random & 0x3) | 0x8;
    return value.toString(16);
  });
}

export function getSessionId(): string {
  const existing = localStorage.getItem(SESSION_KEY);
  if (existing) {
    return existing;
  }
  const generated = createId();
  localStorage.setItem(SESSION_KEY, generated);
  return generated;
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

async function readJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

async function doRequest<T>(path: string, init: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const headers = new Headers(init.headers);
  headers.set(SESSION_HEADER, getSessionId());
  headers.set('Accept', 'application/json');
  if (init.body && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
      credentials: 'include',
      signal: controller.signal,
    });

    const sessionId = response.headers.get(SESSION_HEADER);
    if (sessionId) {
      localStorage.setItem(SESSION_KEY, sessionId);
    }

    const payload = await readJson(response);
    const waking = WAKING_CODES.has(response.status);
    if (!response.ok) {
      const body = (payload ?? {}) as ApiErrorBody;
      const message = waking
        ? 'The workspace is waking up. Wait a moment and try again.'
        : body.error?.message ??
          body.detail ??
          `Request failed with status ${response.status}.`;
      throw new ApiError(
        message,
        response.status,
        waking ? 'server_waking' : body.error?.code ?? 'http_error',
        body.request_id,
        body.error?.details,
      );
    }

    if (payload === null) {
      throw new ApiError(
        'The workspace is still starting. Wait a moment and try again.',
        503,
        'server_waking',
      );
    }

    return payload as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(
        'The request timed out. The workspace may still be waking; wait a moment and try again.',
        0,
        'timeout',
      );
    }
    throw new ApiError(
      'Cannot reach the API. The workspace may be waking up; try again in a moment.',
      0,
      'network_error',
    );
  } finally {
    window.clearTimeout(timeout);
  }
}

async function request<T>(path: string, init: RequestInit = {}, retries = 1): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      return await doRequest<T>(path, init);
    } catch (error) {
      lastError = error;
      const canRetry =
        error instanceof ApiError && error.retryable && attempt < retries;
      if (!canRetry) {
        throw error;
      }
      const slowRecovery =
        error instanceof ApiError &&
        (error.code === 'server_waking' || error.status >= 500);
      await delay((slowRecovery ? 1_000 : 250) * (attempt + 1));
    }
  }
  throw lastError;
}

export const api = {
  getHealth: () => request<Health>('/health', {}, 1),
  getSession: () => request<SessionInfo>('/session', {}, 0),
  getLatestResume: () => request<ResumeInfo>('/resume/latest'),
  uploadResume: (file: File) => {
    const body = new FormData();
    body.append('file', file);
    return request<ResumeUpload>('/resume/upload', { method: 'POST', body }, 0);
  },
  deleteResume: () =>
    request<{ deleted: number }>('/resume/current', { method: 'DELETE' }, 0),
  searchJobs: (query: string) =>
    request<JobSearchResponse>(
      '/jobs/search',
      { method: 'POST', body: JSON.stringify({ query }) },
      0,
    ),
  draftApplication: (jobId: number) =>
    request<DraftResponse>(
      '/applications/draft',
      { method: 'POST', body: JSON.stringify({ job_id: jobId }) },
      0,
    ),
  getApplications: () => request<ApplicationList>('/applications'),
  updateApplication: (applicationId: number, draft: ApplicationUpdate) =>
    request<Application>(
      `/applications/${applicationId}`,
      { method: 'PATCH', body: JSON.stringify(draft) },
      0,
    ),
  approveApplication: (applicationId: number) =>
    request<ApproveResponse>(
      `/applications/${applicationId}/approve`,
      { method: 'POST' },
      0,
    ),
  startInterview: (goal: string) =>
    request<InterviewStart>(
      '/interviews',
      { method: 'POST', body: JSON.stringify({ goal }) },
      0,
    ),
  evaluateInterview: (interviewId: number, answer: string) =>
    request<InterviewEvaluation>(
      `/interviews/${interviewId}/evaluate`,
      { method: 'POST', body: JSON.stringify({ interview_id: interviewId, answer }) },
      0,
    ),
  getDashboard: () => request<Dashboard>('/dashboard'),
  getTraces: () => request<Trace[]>('/traces'),
  getLlmStatus: () => request<LlmStatus>('/llm/status', {}, 0),
};
