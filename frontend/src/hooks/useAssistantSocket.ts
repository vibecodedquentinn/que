import { useCallback, useEffect, useRef, useState } from "react";
import type { WsEvent } from "../types";

function wsUrl(): string {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  return `${proto}//${host}/ws/chat`;
}

export function useAssistantSocket(
  onEvent: (event: WsEvent) => void,
): {
  connected: boolean;
  sendMessage: (text: string) => void;
  clearSession: () => void;
} {
  const wsRef = useRef<WebSocket | null>(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let closed = false;
    let retryMs = 500;

    const connect = () => {
      if (closed) return;
      const ws = new WebSocket(wsUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        retryMs = 500;
      };

      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data) as WsEvent;
          onEventRef.current(data);
        } catch {
          /* ignore */
        }
      };

      ws.onclose = () => {
        setConnected(false);
        if (!closed) {
          window.setTimeout(connect, retryMs);
          retryMs = Math.min(retryMs * 2, 8000);
        }
      };

      ws.onerror = () => ws.close();
    };

    connect();

    const ping = window.setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 25000);

    return () => {
      closed = true;
      window.clearInterval(ping);
      wsRef.current?.close();
    };
  }, []);

  const sendMessage = useCallback((text: string) => {
    wsRef.current?.send(JSON.stringify({ type: "message", message: text }));
  }, []);

  const clearSession = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ type: "clear" }));
  }, []);

  return { connected, sendMessage, clearSession };
}
