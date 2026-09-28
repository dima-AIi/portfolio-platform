import { renderHook, act } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { useUiTheme } from "./useUiTheme";

describe("useUiTheme", () => {
  beforeEach(() => {
    window.localStorage.clear();
    delete document.documentElement.dataset.theme;
  });

  it("remembers an explicit choice across mounts", () => {
    window.localStorage.setItem("pp-ui-theme", "dark");
    const { result } = renderHook(() => useUiTheme());
    expect(result.current.theme).toBe("dark");
  });

  it("toggles and persists the new value", () => {
    window.localStorage.setItem("pp-ui-theme", "light");
    const { result } = renderHook(() => useUiTheme());

    act(() => result.current.toggle());

    expect(result.current.theme).toBe("dark");
    expect(window.localStorage.getItem("pp-ui-theme")).toBe("dark");
    // The attribute is what the CSS keys off, so it must follow the state.
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("falls back to a light theme when nothing is stored", () => {
    const { result } = renderHook(() => useUiTheme());
    expect(result.current.theme).toBe("light");
  });
});
