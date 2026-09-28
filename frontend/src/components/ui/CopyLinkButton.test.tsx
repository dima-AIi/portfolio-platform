import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CopyLinkButton } from "./CopyLinkButton";

describe("CopyLinkButton", () => {
  const writeText = vi.fn().mockResolvedValue(undefined);

  beforeEach(() => {
    writeText.mockClear();
    vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("copies the absolute URL, not the path", async () => {
    render(<CopyLinkButton to="/dmitriy" />);

    await userEvent.click(screen.getByRole("button", { name: /скопировать ссылку/i }));

    await waitFor(() => expect(writeText).toHaveBeenCalledTimes(1));
    expect(writeText).toHaveBeenCalledWith(`${window.location.origin}/dmitriy`);
  });

  it("confirms success once the link is on the clipboard", async () => {
    render(<CopyLinkButton to="/dmitriy" />);

    await userEvent.click(screen.getByRole("button", { name: /скопировать ссылку/i }));

    expect(await screen.findByRole("button", { name: /скопировано/i })).toBeInTheDocument();
  });

  it("falls back to execCommand when the Clipboard API is blocked", async () => {
    vi.stubGlobal("navigator", {
      ...navigator,
      clipboard: { writeText: vi.fn().mockRejectedValue(new Error("not allowed")) },
    });
    // Stub only the method: replacing the whole document object would detach
    // createElement results from the real DOM the component renders into.
    const execCommand = vi.fn().mockReturnValue(true);
    Object.defineProperty(document, "execCommand", {
      value: execCommand,
      configurable: true,
    });

    render(<CopyLinkButton to="/dmitriy" />);

    await userEvent.click(screen.getByRole("button", { name: /скопировать ссылку/i }));

    await waitFor(() => expect(execCommand).toHaveBeenCalledWith("copy"));
    // The temporary textarea used for the fallback must not stay in the DOM.
    expect(document.querySelectorAll("textarea")).toHaveLength(0);

    delete (document as Document & { execCommand?: unknown }).execCommand;
  });
});
