// src/hooks/useStatusPoll.js
import { useState, useEffect } from "react";

export const useStatusPoll = (intervalMs = 5000, endpoint = "http://localhost:8000/health") => {
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
        // New logic: only show CONNECTED if both API and market_data are connected
        if (data.status === "ok" && data.market_data === "connected") {
          setStatus("CONNECTED");
        } else {
          setStatus("DISCONNECTED");
        }
      } catch (error) {
        setStatus("DISCONNECTED");
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, intervalMs);
    return () => clearInterval(interval);
  }, [intervalMs, endpoint]);

  return status;
};
