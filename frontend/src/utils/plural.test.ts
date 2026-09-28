import { describe, expect, it } from "vitest";

import { plural } from "./plural";

describe("plural", () => {
  it("uses the singular form for numbers ending in 1", () => {
    expect(plural(1, "просмотр", "просмотра", "просмотров")).toBe("просмотр");
    expect(plural(21, "просмотр", "просмотра", "просмотров")).toBe("просмотр");
    expect(plural(101, "просмотр", "просмотра", "просмотров")).toBe("просмотр");
  });

  it("uses the few form for numbers ending in 2-4", () => {
    expect(plural(2, "просмотр", "просмотра", "просмотров")).toBe("просмотра");
    expect(plural(3, "просмотр", "просмотра", "просмотров")).toBe("просмотра");
    expect(plural(24, "просмотр", "просмотра", "просмотров")).toBe("просмотра");
  });

  it("uses the many form for 0, 5-20 and teens", () => {
    expect(plural(0, "просмотр", "просмотра", "просмотров")).toBe("просмотров");
    expect(plural(5, "просмотр", "просмотра", "просмотров")).toBe("просмотров");
    expect(plural(11, "просмотр", "просмотра", "просмотров")).toBe("просмотров");
    // 12 and 14 look like 2 and 4 but sit in the teens range.
    expect(plural(12, "просмотр", "просмотра", "просмотров")).toBe("просмотров");
    expect(plural(14, "просмотр", "просмотра", "просмотров")).toBe("просмотров");
  });
});
