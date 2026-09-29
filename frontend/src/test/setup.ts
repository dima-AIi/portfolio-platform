import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// useSeo rewrites document.title, which would otherwise leak between files.
const INITIAL_TITLE = document.title;

afterEach(() => {
  cleanup();
  localStorage.clear();
  // The static tags from index.html carry data-static, so this removes exactly
  // what the app injected and leaves the document as it was found.
  document
    .head
    .querySelectorAll("meta[property], meta[name], link[rel='canonical']")
    .forEach((el) => {
      if (!el.hasAttribute("data-static")) el.remove();
    });
  document.title = INITIAL_TITLE;
});