import React, { useEffect, useState } from "react";
import { Clock } from "lucide-react";

interface TimerProps {
  phaseEndTime: bigint | number;
}

export const Timer: React.FC<TimerProps> = ({ phaseEndTime }) => {
  const [timeLeftSec, setTimeLeftSec] = useState<number>(0);

  useEffect(() => {
    const endMs = Number(phaseEndTime);

    const updateTimer = () => {
      const nowMs = Date.now();
      const diffSec = Math.max(0, Math.floor((endMs - nowMs) / 1000));
      setTimeLeftSec(diffSec);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [phaseEndTime]);

  const mins = Math.floor(timeLeftSec / 60);
  const secs = timeLeftSec % 60;
  const formatted = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  const isUrgent = timeLeftSec > 0 && timeLeftSec <= 60;

  if (Number(phaseEndTime) <= 0) return null;

  return (
    <div className={`timer-pill ${isUrgent ? "urgent" : ""}`}>
      <Clock size={16} />
      <span>{formatted}</span>
    </div>
  );
};
