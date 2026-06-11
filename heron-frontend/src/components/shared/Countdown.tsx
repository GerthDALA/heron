"use client";

import { useEffect, useState } from "react";
import { EMPCO_DEADLINE } from "@/lib/constants";
import { cn } from "@/lib/utils";

function diff() {
  const ms = EMPCO_DEADLINE.getTime() - Date.now();
  const days = Math.max(0, Math.floor(ms / 86400000));
  const hours = Math.max(0, Math.floor((ms % 86400000) / 3600000));
  const minutes = Math.max(0, Math.floor((ms % 3600000) / 60000));
  return { days, hours, minutes };
}

export function Countdown({ detailed = false }: { detailed?: boolean }) {
  const [time, setTime] = useState<ReturnType<typeof diff> | null>(null);

  useEffect(() => {
    setTime(diff());
    const interval = setInterval(() => setTime(diff()), 1000);
    return () => clearInterval(interval);
  }, []);

  if (time === null) {
    return <span className="font-mono text-heron-danger">… jours avant le 27 septembre 2026</span>;
  }

  const urgent = time.days < 30;
  return (
    <span className={cn("font-mono", urgent ? "text-heron-danger font-bold" : "text-heron-danger")}>
      {detailed
        ? `${time.days} jours ${time.hours} h ${time.minutes} min avant le 27 septembre 2026`
        : `${time.days} jours avant le 27 septembre 2026`}
    </span>
  );
}
