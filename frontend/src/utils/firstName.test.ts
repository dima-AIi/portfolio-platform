import { describe, expect, it } from "vitest";

import { firstName } from "./firstName";

describe("firstName", () => {
  it("keeps only the first word of a full name", () => {
    expect(firstName("Дмитрий Кузнецов")).toBe("Дмитрий");
  });

  it("drops a trailing initial so the greeting reads naturally", () => {
    expect(firstName("Дмитрий К.")).toBe("Дмитрий");
  });

  it("handles a plain first name and extra whitespace", () => {
    expect(firstName("Дмитрий")).toBe("Дмитрий");
    expect(firstName("  Дмитрий   К.  ")).toBe("Дмитрий");
  });

  it("returns null when there is no usable name", () => {
    expect(firstName(null)).toBeNull();
    expect(firstName("")).toBeNull();
    expect(firstName("   ")).toBeNull();
    // A bare initial is not a name to greet someone by.
    expect(firstName("К.")).toBeNull();
  });
});
