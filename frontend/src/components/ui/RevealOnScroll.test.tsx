import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RevealOnScroll } from "./RevealOnScroll";

describe("RevealOnScroll", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("reveals content when it scrolls into view", () => {
    let trigger: (entries: Array<{ isIntersecting: boolean }>) => void = () => {};
    const disconnect = vi.fn();
    vi.stubGlobal(
      "IntersectionObserver",
      class {
        constructor(callback: typeof trigger) {
          trigger = callback as typeof trigger;
        }
        observe() {}
        disconnect = disconnect;
        unobserve() {}
        takeRecords() {
          return [];
        }
      },
    );

    const { container } = render(
      <RevealOnScroll className="pf-section">Контент</RevealOnScroll>,
    );

    const wrapper = container.firstElementChild!;
    expect(wrapper.className).toContain("reveal");
    expect(wrapper.className).not.toContain("is-visible");

    act(() => {
      trigger([{ isIntersecting: true }]);
    });

    expect(wrapper.className).toContain("is-visible");
    // One-shot: the observer is released once the section is shown.
    expect(disconnect).toHaveBeenCalled();
  });

  it("shows content immediately when IntersectionObserver is missing", () => {
    vi.stubGlobal("IntersectionObserver", undefined);

    const { container } = render(<RevealOnScroll>Контент</RevealOnScroll>);

    // Never leave content hidden behind an observer the browser lacks.
    expect(container.firstElementChild!.className).toContain("is-visible");
  });

  it("renders its children so screen readers always find the text", () => {
    render(<RevealOnScroll>Текст кейса</RevealOnScroll>);
    expect(screen.getByText("Текст кейса")).toBeInTheDocument();
  });
});
