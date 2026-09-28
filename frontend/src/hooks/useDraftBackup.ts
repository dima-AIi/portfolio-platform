import { useCallback, useEffect, useRef, useState } from "react";

const STORAGE_PREFIX = "pp-draft:";

/**
 * Keeps a local copy of unsaved form edits so a closed tab or a crashed
 * session does not lose the case text an author just wrote.
 *
 * Deliberately localStorage rather than an autosave API: this must work
 * offline, must not publish anything without an explicit "Save", and must
 * never race with the editor's own save. clear() runs once the server has
 * the same data.
 */
export function useDraftBackup<T>(key: string, _value?: T) {
  const storageKey = `${STORAGE_PREFIX}${key}`;
  const [restored, setRestored] = useState<T | null>(null);

  // Read once on mount: this is a recovery offer, not a live sync.
  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (raw) setRestored(JSON.parse(raw) as T);
    } catch {
      // A corrupted entry should never block the editor from opening.
      window.localStorage.removeItem(storageKey);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storageKey]);

  const save = useCallback(
    (next: T) => {
      try {
        window.localStorage.setItem(storageKey, JSON.stringify(next));
      } catch {
        // Quota exceeded: losing the backup is acceptable, losing the
        // editor is not.
      }
    },
    [storageKey],
  );

  const clear = useCallback(() => {
    try {
      window.localStorage.removeItem(storageKey);
    } catch {
      /* nothing to do */
    }
  }, [storageKey]);

  return { restored, save, clear };
}

/** Debounced writer: fires save() only after the value stops changing. */
export function useDebouncedEffect(fn: () => void, delay: number) {
  const timer = useRef<number | null>(null);
  useEffect(() => {
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(fn, delay);
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, [fn, delay]);
}
