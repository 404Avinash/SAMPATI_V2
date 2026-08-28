import { useEffect, useRef, useState, useCallback } from "react";

/**
 * Derives dynamic WebSocket URL based on window location or custom host.
 */
export function getWsUrl(protocol, host) {
  const isSecure = protocol === "https:" || protocol === "wss:";
  const wsProto = isSecure ? "wss:" : "ws:";
  const targetHost = host || (typeof window !== "undefined" ? window.location.host : "localhost:8000");
  return `${wsProto}//${targetHost}/ws/feed`;
}

/**
 * Calculates exponential backoff reconnect interval.
 * Min 1.0s, Max 30.0s, multiplier 1.5.
 */
export function calculateBackoff(attempt) {
  const base = 1.0 * Math.pow(1.5, Math.max(0, attempt));
  return Math.min(30.0, base);
}

/**
 * Self-healing WebSocket hook with auto-reconnect, JSON parsing,
 * and event dispatching for SAMPATI V2 live streams.
 */
export function useWebSocket({
  onNewCase,
  onStatsUpdate,
  onOpen,
  onClose,
  onError,
  enabled = true,
} = {}) {
  const [connected, setConnected] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const isMountedRef = useRef(true);

  // Keep callback refs fresh
  const onNewCaseRef = useRef(onNewCase);
  const onStatsUpdateRef = useRef(onStatsUpdate);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onNewCaseRef.current = onNewCase;
    onStatsUpdateRef.current = onStatsUpdate;
    onOpenRef.current = onOpen;
    onCloseRef.current = onClose;
    onErrorRef.current = onError;
  });

  const connect = useCallback(() => {
    if (!enabled || typeof window === "undefined") return;

    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      const url = getWsUrl(window.location.protocol, window.location.host);
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = (event) => {
        if (!isMountedRef.current) return;
        setConnected(true);
        setReconnectAttempt(0);
        if (onOpenRef.current) {
          onOpenRef.current(event);
        }
      };

      ws.onmessage = (event) => {
        if (!isMountedRef.current) return;
        try {
          const payload = JSON.parse(event.data);
          const eventType = payload.event || payload.type;
          const data = payload.data || payload.payload || payload;

          if (eventType === "new_case" || eventType === "UPI_CASE_OPENED") {
            if (onNewCaseRef.current) {
              onNewCaseRef.current(data, payload.stats);
            }
          } else if (eventType === "stats_update" || eventType === "UPI_EVALUATED") {
            if (onStatsUpdateRef.current) {
              onStatsUpdateRef.current(data);
            }
          }
        } catch (err) {
          console.warn("[useWebSocket] Message parse error:", err);
        }
      };

      ws.onclose = (event) => {
        if (!isMountedRef.current) return;
        setConnected(false);
        if (onCloseRef.current) {
          onCloseRef.current(event);
        }

        if (enabled) {
          setReconnectAttempt((prev) => {
            const nextAttempt = prev + 1;
            const delaySec = calculateBackoff(prev);
            reconnectTimerRef.current = setTimeout(() => {
              connect();
            }, delaySec * 1000);
            return nextAttempt;
          });
        }
      };

      ws.onerror = (event) => {
        if (onErrorRef.current) {
          onErrorRef.current(event);
        }
      };
    } catch (err) {
      console.error("[useWebSocket] Connection initialization failed:", err);
    }
  }, [enabled]);

  useEffect(() => {
    isMountedRef.current = true;
    connect();

    return () => {
      isMountedRef.current = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    connected,
    reconnectAttempt,
    reconnect: connect,
  };
}

export default useWebSocket;
