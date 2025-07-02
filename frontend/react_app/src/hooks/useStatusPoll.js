// src/hooks/useStatusPoll.js
import { useState, useEffect } from "react";

export const useStatusPoll = (intervalMs = 5000, endpoint = "http://localhost:8000/status") => {
  const [status, setStatus] = useState("DISCONNECTED");

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000); // 2s timeout

        const response = await fetch(endpoint, { signal: controller.signal });
        clearTimeout(timeoutId);

        if (!response.ok) throw new Error("Status check failed");

        const data = await response.json();
        setStatus(data.status.toUpperCase());
      } catch (error) {
        setStatus("DISCONNECTED");
        console.warn("⚠️ Status poll error:", error.message);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, intervalMs);
    return () => clearInterval(interval);
  }, [intervalMs, endpoint]);

  return status;
};
