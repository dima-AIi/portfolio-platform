import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api } from "./api";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("api client", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns parsed JSON on success", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: "1", title: "CRM" }));

    await expect(api.get<{ id: string }>("/projects/1")).resolves.toEqual({
      id: "1",
      title: "CRM",
    });
  });

  it("sends cookies so the httpOnly session is included", async () => {
    fetchMock.mockResolvedValue(jsonResponse({}));

    await api.get("/auth/me");

    const [, init] = fetchMock.mock.calls[0];
    expect(init.credentials).toBe("include");
  });

  it("does not read or write a token in localStorage", async () => {
    fetchMock.mockResolvedValue(jsonResponse({}));

    await api.get("/public/dmitriy");

    // The JWT lives in an httpOnly cookie; nothing may be persisted client-side.
    expect(localStorage.length).toBe(0);
    expect(document.cookie).not.toContain("jwt");
  });

  it("sets a JSON content type for plain bodies only", async () => {
    fetchMock.mockResolvedValue(jsonResponse({}));
    await api.post("/projects", { title: "CRM" });
    expect(fetchMock.mock.calls[0][1].headers["Content-Type"]).toBe("application/json");

    fetchMock.mockReset();
    fetchMock.mockResolvedValue(jsonResponse({}));
    const form = new FormData();
    await api.upload("/projects/1/images", form);
    expect(fetchMock.mock.calls[0][1].headers["Content-Type"]).toBeUndefined();
  });

  it("throws ApiError with the backend error code and message", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ error: { code: "PROJECT_NOT_FOUND", message: "Проект не найден." } }, 404),
    );

    await expect(api.get("/projects/x")).rejects.toMatchObject({
      code: "PROJECT_NOT_FOUND",
      message: "Проект не найден.",
      status: 404,
    });
  });

  it("falls back to a readable message on a non-JSON error", async () => {
    fetchMock.mockResolvedValue(new Response("<html>502</html>", { status: 502 }));

    const error = await api.get("/projects").catch((err: unknown) => err);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe("REQUEST_FAILED");
    expect((error as ApiError).message).toBeTruthy();
  });

  it("notifies the app on 401 so the session is treated as expired", async () => {
    const expired = vi.fn();
    window.addEventListener("auth:expired", expired);
    fetchMock.mockResolvedValue(jsonResponse({ error: { code: "HTTP_ERROR", message: "no" } }, 401));

    await expect(api.get("/auth/me")).rejects.toBeInstanceOf(ApiError);

    expect(expired).toHaveBeenCalledTimes(1);
    window.removeEventListener("auth:expired", expired);
  });

  it("resolves 204 responses to undefined", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));
    await expect(api.delete("/projects/1")).resolves.toBeUndefined();
  });

  it("sends the body on a DELETE request", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

    await api.deleteWithBody("/auth/account", { password: "secret" });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe("DELETE");
    expect(init.body).toBe(JSON.stringify({ password: "secret" }));
  });
});