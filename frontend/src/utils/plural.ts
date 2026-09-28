/**
 * Russian plural forms. Picks one of three endings for a count, which plain
 * string interpolation gets wrong for every number between 5 and 20 —
 * "5 проектов" instead of "5 проектов" is fine, but "1 проектов" is not.
 */
export function plural(count: number, one: string, few: string, many: string): string {
  const abs = Math.abs(count) % 100;
  const last = abs % 10;
  if (abs > 10 && abs < 20) return many;
  if (last > 1 && last < 5) return few;
  if (last === 1) return one;
  return many;
}
