import axios, { isAxiosError } from "axios";
import type { JobStatusResponse, JobSummary, SearchRequest, SearchResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const SESSION_KEY = "pi_session_id";

const client = axios.create({ baseURL: API_URL, timeout: 20000 });

/**
 * Anonymous per-browser id sent as X-Session-ID so the backend only lists
 * and deletes this visitor's own searches. Falls back to a throw-away id
 * when localStorage is unavailable (SSR, private mode).
 */
function getSessionId(): string {
  const generate = () =>
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `s${Date.now().toString(36)}${Math.random().toString(36).slice(2, 12)}`;
  try {
    let id = window.localStorage.getItem(SESSION_KEY);
    if (!id) {
      id = generate();
      window.localStorage.setItem(SESSION_KEY, id);
    }
    return id;
  } catch {
    return generate();
  }
}

client.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    config.headers.set("X-Session-ID", getSessionId());
  }
  return config;
});

/** A failed API call, with a message that is safe to show to the user. */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number | null
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Turns an axios failure into a specific, user-readable ApiError. */
export function toApiError(err: unknown): ApiError {
  if (!isAxiosError(err)) return new ApiError("Something went wrong. Please try again.", null);

  const status = err.response?.status ?? null;
  if (status === null) {
    return new ApiError("Couldn't reach the server. Is the backend running?", null);
  }
  if (status === 429) {
    return new ApiError("Too many requests — please wait a minute and try again.", status);
  }
  if (status === 404) {
    return new ApiError("Not found.", status);
  }

  const detail = err.response?.data?.detail;
  if (status === 422 && Array.isArray(detail)) {
    // FastAPI validation errors: [{ loc: [...], msg: "Value error, ..." }]
    const messages = detail.map((d: { msg?: string }) =>
      String(d.msg ?? "Invalid input").replace(/^Value error, /, "")
    );
    return new ApiError(messages.join(" "), status);
  }
  if (typeof detail === "string") return new ApiError(detail, status);

  return new ApiError(`The server returned an error (${status}).`, status);
}

async function request<T>(call: () => Promise<{ data: T }>): Promise<T> {
  try {
    return (await call()).data;
  } catch (err) {
    throw toApiError(err);
  }
}

export function submitSearch(payload: SearchRequest): Promise<SearchResponse> {
  return request(() => client.post<SearchResponse>("/api/search", payload));
}

export function getResults(jobId: string): Promise<JobStatusResponse> {
  return request(() => client.get<JobStatusResponse>(`/api/results/${jobId}`));
}

export function listJobs(): Promise<JobSummary[]> {
  return request(() => client.get<JobSummary[]>("/api/jobs"));
}

/** Permanently deletes one of the caller's searches and all of its results. */
export function deleteJob(jobId: string): Promise<void> {
  return request(() => client.delete<void>(`/api/jobs/${jobId}`));
}
