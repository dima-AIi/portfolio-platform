import { useEffect, useRef, useState } from "react";

/**
 * Reveals its children once they scroll into view.
 *
 * Purely decorative: when IntersectionObserver is unavailable the content
 * renders immediately, and the CSS reduced-motion query collapses the
 * animation, so nothing is ever trapped behind a failed observer.
 */
export function RevealOnScroll({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (typeof IntersectionObserver === "undefined") {
      setShown(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        // One-way reveal: once visible, stop observing so scrolling back
        // does not replay the animation.
        if (entries.some((e) => e.isIntersecting)) {
          setShown(true);
          observer.disconnect();
        }
      },
      { rootMargin: "0px 0px -40px 0px", threshold: 0.05 },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} className={`reveal ${shown ? "is-visible" : ""} ${className}`.trim()}>
      {children}
    </div>
  );
}
