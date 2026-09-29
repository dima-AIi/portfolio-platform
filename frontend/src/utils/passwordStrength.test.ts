import { describe, expect, it } from "vitest";

import { PASSWORD_MAX_BYTES, scorePassword } from "./passwordStrength";

describe("scorePassword", () => {
  it("rejects an empty password", () => {
    expect(scorePassword("").ok).toBe(false);
    expect(scorePassword("").score).toBe(0);
  });

  it("rejects passwords shorter than 8 characters", () => {
    expect(scorePassword("Ab1!").hint).toBe("Минимум 8 символов.");
  });

  it("rejects a password longer than bcrypt can hash", () => {
    // The API answers 422 here; catching it client-side avoids the round trip.
    expect(scorePassword("Aa1!" + "x".repeat(100)).ok).toBe(false);
    expect(scorePassword("Aa1!" + "x".repeat(100)).hint).toContain("72");
  });

  it("measures the limit in bytes, not characters", () => {
    // 40 Cyrillic letters = 80 UTF-8 bytes, already over the 72-byte limit,
    // even though it is only 44 characters. Escapes keep the test independent
    // of how the source file itself is encoded on disk.
    const cyrillic = "\u041f" + "\u044f".repeat(39);
    const password = `${cyrillic}aA1!`;
    expect(new TextEncoder().encode(password).length).toBeGreaterThan(PASSWORD_MAX_BYTES);
    expect(scorePassword(password).ok).toBe(false);
  });

  it("accepts a strong password of exactly the byte limit", () => {
    expect(scorePassword("Aa1!" + "x".repeat(68)).ok).toBe(true);
  });

  it("rejects common passwords", () => {
    expect(scorePassword("password123").ok).toBe(false);
    expect(scorePassword("qwerty123").ok).toBe(false);
  });

  it("is case-insensitive about common passwords", () => {
    expect(scorePassword("PassWord123").ok).toBe(false);
  });

  it("rejects a single character class", () => {
    // 10 lowercase letters: long enough, but only one class.
    expect(scorePassword("abcdefghij").ok).toBe(false);
  });

  it("accepts a mixed-class password", () => {
    const result = scorePassword("strongpass123");
    expect(result.ok).toBe(true);
    expect(result.score).toBeGreaterThanOrEqual(2);
  });

  it("scores a long diverse password highest", () => {
    expect(scorePassword("Str0ng!Passw0rd#2024").score).toBe(4);
  });

  it("treats Cyrillic letters as letters", () => {
    // Only lower+upper Cyrillic = 2 classes -> acceptable, digits not required.
    expect(scorePassword("ПарольТест").ok).toBe(true);
  });

  it("never reports an empty label for a non-empty password", () => {
    for (const pw of ["a", "password", "abcdefghij", "strongpass123"]) {
      expect(scorePassword(pw).label).not.toBe("");
    }
  });
});