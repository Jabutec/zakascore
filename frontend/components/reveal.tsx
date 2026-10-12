"use client";

import { useEffect, useRef, useState, type ElementType, type ReactNode } from "react";

type RevealState = "idle" | "hidden" | "shown";

/*
  Fades and lifts its content in the first time it scrolls into view.

  - Content is visible in the server-rendered HTML, so nothing is hidden if JavaScript
    is slow or off. Only blocks that start below the fold get hidden, and only after load.
  - Respects "reduce motion": those users just see the content.
  - Use `delay` to stagger a list: delay={index * 90}.
  - Use `as="li"` (or any tag) when the wrapper must be a list item, section, etc.
*/
export function Reveal({
  children,
  className = "",
  delay = 0,
  as: Tag = "div",
}: {
  children: ReactNode;
  className?: string;
  /** Milliseconds to wait before animating in */
  delay?: number;
  as?: ElementType;
}) {
  const ref = useRef<HTMLElement | null>(null);
  const [state, setState] = useState<RevealState>("idle");

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!("IntersectionObserver" in window)) return;

    // Already on screen (or above it) at load: leave it visible, no animation.
    if (element.getBoundingClientRect().top < window.innerHeight * 0.92) return;

    setState("hidden");
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setState("shown");
          observer.disconnect();
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -6% 0px" },
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  // Tailwind v4 moves elements with the `translate` property, so that's what we transition.
  const motion =
    state === "idle"
      ? ""
      : `transition-[opacity,translate] duration-700 ease-out ${
          state === "hidden" ? "translate-y-6 opacity-0" : "translate-y-0 opacity-100"
        }`;

  return (
    <Tag
      ref={ref}
      className={`${className} ${motion}`.trim()}
      style={state === "idle" ? undefined : { transitionDelay: `${delay}ms` }}
    >
      {children}
    </Tag>
  );
}