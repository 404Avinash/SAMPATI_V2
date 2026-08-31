import { useEffect, useRef, useState } from "react";

/** Animates a number from its previous value (starting at 0 on mount) to a new target over `duration` ms. */
export function useCountUp(target, duration = 700) {
  const numTarget = typeof target === "number" && !isNaN(target) ? target : 0;
  const [value, setValue] = useState(0);
  const fromRef = useRef(0);
  const rafRef = useRef(null);

  useEffect(() => {
    const from = fromRef.current;
    const to = numTarget;
    if (from === to) return undefined;
    const start = performance.now();

    function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      const current = Math.round(from + (to - from) * eased);
      setValue(current);
      fromRef.current = current;
      if (t < 1) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        fromRef.current = to;
        setValue(to);
      }
    }

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [numTarget, duration]);

  return value;
}

export default useCountUp;
