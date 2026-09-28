const STORAGE_KEY = "pp-ui-theme";

export type Theme = "light" | "dark";

export function readStoredTheme(): Theme {
  // The dashboard is where people spend their time, so the UI theme follows
  // the OS preference by default and is remembered once chosen.
  if (typeof window === "undefined") return "light";
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}
