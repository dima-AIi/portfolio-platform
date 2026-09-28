import type { ApiErrorPayload } from "../types";

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

/**
 * Base URL for every API call.
 *
 * Vite inlines `import.meta.env.VITE_API_BASE_URL` at build time. An empty
 * variable in the hosting dashboard is substituted as "", and `??` only falls
 * back on null/undefined — so `env.X ?? "/api/v1"` silently produced "" and
 * every request went to the SPA routes instead of the API. `||` treats the
 * empty string as "not configured" and keeps the default.
 */
export const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    // The session lives in an httpOnly cookie, so the browser must be told to
    // send it. Same-origin requests include cookies by default, but VITE_API_BASE_URL
    // may point at a different host in development.
    credentials: "include",
    headers: {
      ...(options.body && !(options.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...options.headers,
    },
  });

  if (response.status === 204) {
    return undefined as T;
  }

  let data: unknown = null;
  try {
    data = await response.json();
  } catch {
    /* non-JSON response */
  }

  if (!response.ok) {
    const payload = data as ApiErrorPayload | null;
    if (response.status === 401) {
      window.dispatchEvent(new Event("auth:expired"));
    }
    throw new ApiError(
      payload?.error?.code ?? "REQUEST_FAILED",
      payload?.error?.message ?? "Что-то пошло не так. Попробуйте ещё раз.",
      response.status,
    );
  }

  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: body !== undefined ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  deleteWithBody: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "DELETE", body: JSON.stringify(body) }),
  upload: <T>(path: string, formData: FormData) =>
    request<T>(path, { method: "POST", body: formData }),
};
