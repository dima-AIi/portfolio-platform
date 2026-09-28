import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
  localStorage.clear();
  document.head.querySelectorAll("meta[property], meta[name], link[rel='canonical']").forEach((el) => {
    // Keep the static tags from index.html; drop everything the app injected.
    if (!el.getAttribute("data-static")) el.remove();
  });
});