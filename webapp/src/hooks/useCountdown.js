import { useEffect, useMemo, useState } from "react";

function formatDuration(totalSeconds) {
  const safe = Math.max(0, Number(totalSeconds) || 0);
  const hours = Math.floor(safe / 3600);
  const minutes = Math.floor((safe % 3600) / 60);
  const seconds = safe % 60;

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export function useCountdown(initialSeconds) {
  const [secondsLeft, setSecondsLeft] = useState(Math.max(0, Number(initialSeconds) || 0));

  useEffect(() => {
    setSecondsLeft(Math.max(0, Number(initialSeconds) || 0));
  }, [initialSeconds]);

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const id = setInterval(() => {
      setSecondsLeft((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(id);
  }, [secondsLeft]);

  const formatted = useMemo(() => formatDuration(secondsLeft), [secondsLeft]);

  return { secondsLeft, formatted };
}
