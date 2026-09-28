import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { useDraftBackup } from "./useDraftBackup";

describe("useDraftBackup", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("persists the value under a namespaced key", () => {
    const { result } = renderHook(() => useDraftBackup("project-1", { title: "ELORA" }));

    act(() => result.current.save({ title: "ELORA" }));

    expect(window.localStorage.getItem("pp-draft:project-1")).toBe(
      JSON.stringify({ title: "ELORA" }),
    );
  });

  it("offers a previously stored copy back on the next mount", () => {
    window.localStorage.setItem("pp-draft:project-1", JSON.stringify({ title: "Сохранённый" }));
    const { result } = renderHook(() => useDraftBackup("project-1", { title: "" }));
    expect(result.current.restored).toEqual({ title: "Сохранённый" });
  });

  it("clears the copy so a stale backup is not offered again", () => {
    const { result } = renderHook(() => useDraftBackup("project-1", { title: "x" }));
    act(() => result.current.save({ title: "x" }));

    act(() => result.current.clear());

    expect(window.localStorage.getItem("pp-draft:project-1")).toBeNull();
  });

  it("recovers from a corrupted entry instead of throwing", () => {
    window.localStorage.setItem("pp-draft:project-1", "{not json");
    const { result } = renderHook(() => useDraftBackup("project-1", { title: "x" }));
    // The editor must still open; the bad entry is discarded.
    expect(result.current.restored).toBeNull();
    expect(window.localStorage.getItem("pp-draft:project-1")).toBeNull();
  });

  it("keeps drafts for different projects separate", () => {
    const a = renderHook(() => useDraftBackup("project-1", { title: "A" }));
    const b = renderHook(() => useDraftBackup("project-2", { title: "B" }));

    act(() => a.result.current.save({ title: "A" }));
    act(() => b.result.current.save({ title: "B" }));

    expect(window.localStorage.getItem("pp-draft:project-1")).toContain("A");
    expect(window.localStorage.getItem("pp-draft:project-2")).toContain("B");
  });
});
