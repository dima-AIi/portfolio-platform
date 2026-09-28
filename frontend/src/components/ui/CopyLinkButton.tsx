import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Copies a shareable absolute link, the way the profile and project pages
 * expose one. Falls back to a hidden textarea when the Clipboard API is
 * unavailable or blocked (http origins, older browsers).
 */
export function CopyLinkButton({
  to,
  label = "Скопировать ссылку",
  copiedLabel = "Скопировано",
  className = "btn btn-secondary btn-sm",
}: {
  /** Path such as /username — expanded to an absolute URL on click. */
  to: string;
  label?: string;
  copiedLabel?: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);
  const timer = useRef<number | null>(null);

  useEffect(
    () => () => {
      if (timer.current) window.clearTimeout(timer.current);
    },
    [],
  );

  const flash = useCallback(() => {
    setCopied(true);
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setCopied(false), 2000);
  }, []);

  const copy = useCallback(async () => {
    const url = `${window.location.origin}${to}`;
    try {
      await navigator.clipboard.writeText(url);
      flash();
    } catch {
      // Clipboard API is unavailable outside secure contexts; fall back.
      const area = document.createElement("textarea");
      area.value = url;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      const ok = document.execCommand("copy");
      document.body.removeChild(area);
      if (ok) flash();
    }
  }, [to, flash]);

  return (
    <button type="button" className={className} onClick={() => void copy()}>
      {copied ? `✓ ${copiedLabel}` : label}
    </button>
  );
}
