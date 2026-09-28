/**
 * First name for a friendly greeting.
 *
 * A display name is often stored as "Дмитрий К." or "Дмитрий Кузнецов" for
 * the public page, which reads badly in a salutation — "Здравствуйте,
 * Дмитрий Кузнецов!" is a form letter, not a greeting. Keeps the first
 * token only, and drops a trailing initial so "Дмитрий К." becomes
 * "Дмитрий". Returns null when there is nothing usable to show.
 */
export function firstName(displayName: string | null | undefined): string | null {
  if (!displayName) return null;
  const first = displayName.trim().split(/\s+/)[0] ?? "";
  if (!first) return null;
  // A lone initial ("К." or "K") is not a name.
  if (first.length <= 2 && /^[^\p{L}]*[.\p{L}]/u.test(first)) {
    const letters = first.replace(/[^\p{L}]/gu, "");
    if (letters.length <= 1) return null;
  }
  return first;
}
