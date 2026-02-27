import { useEffect, useRef, useState } from "react";

/**
 * Animates a numeric value from its previous state to the current value
 * over ~400ms using requestAnimationFrame with easeOut.
 */
function useAnimatedValue(target: number): number {
  const [display, setDisplay] = useState(target);
  const prevRef = useRef(target);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const from = prevRef.current;
    const to = target;
    prevRef.current = to;

    if (from === to) return;

    const duration = 400;
    const start = performance.now();

    const tick = (now: number) => {
      const elapsed = now - start;
      const t = Math.min(elapsed / duration, 1);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(from + (to - from) * eased);

      if (t < 1) {
        rafRef.current = requestAnimationFrame(tick);
      }
    };

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [target]);

  return display;
}

interface StatCardProps {
  label: string;
  value: string;
}

export default function StatCard({ label, value }: StatCardProps) {
  // Try to parse numeric value for animation.
  const raw = value.replace(/,/g, "");
  const numericTarget = Number(raw);
  const isNumeric = !isNaN(numericTarget) && raw !== "" && value !== "—";

  const animated = useAnimatedValue(isNumeric ? numericTarget : 0);

  // Format the animated number to match the original style.
  const displayValue = isNumeric
    ? value.includes(".")
      ? animated.toFixed(1)
      : Math.round(animated).toLocaleString()
    : value;

  return (
    <div className="dashboard-card p-6 group">
      <p className="text-[11px] uppercase tracking-widest text-gray-500 font-medium">
        {label}
      </p>
      <p className="stat-value mt-3 text-3xl font-bold text-white leading-none">
        {displayValue}
      </p>
    </div>
  );
}
