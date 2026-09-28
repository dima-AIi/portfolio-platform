import { useCallback, useEffect, useState } from "react";

import { readStoredTheme, type Theme } from "./uiTheme";

const STORAGE_KEY = "pp-ui-theme";

export function useUiTheme() {
  const [theme, setTheme] = useState<Theme>(readStoredTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const toggle = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), []);

  return { theme, toggle };
}