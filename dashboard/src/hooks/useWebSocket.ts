import { useEffect, useRef, useState, useCallback } from "react";

const INITIAL_DELAY_MS = 1000;
const MAX_DELAY_MS = 30000;
const JITTER_FACTOR = 0.2; // ±20%

export type ConnectionStatus = "connected" | "disconnected" | "connecting";

interface UseWebSocketOptions {
    url: string;
    onMessage: (event: MessageEvent) => void;
}

/**
 * Manages a WebSocket connection with exponential backoff reconnect.
 *
 * Delay formula: min(1000 × 2^attempt, 30000) ± 20% jitter.
 * Resets on successful connection.
 */
export function useWebSocket({ url, onMessage }: UseWebSocketOptions): ConnectionStatus {
    const [status, setStatus] = useState<ConnectionStatus>("connecting");
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const attemptRef = useRef(0);

    // Stable reference to the latest onMessage callback.
    const onMessageRef = useRef(onMessage);
    onMessageRef.current = onMessage;

    const connect = useCallback(() => {
        // Guard against duplicate connections.
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        setStatus("connecting");
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
            setStatus("connected");
            attemptRef.current = 0; // reset backoff on success
        };

        ws.onmessage = (event) => {
            onMessageRef.current(event);
        };

        ws.onclose = () => {
            setStatus("disconnected");
            wsRef.current = null;

            // Exponential backoff with jitter.
            const base = Math.min(
                INITIAL_DELAY_MS * Math.pow(2, attemptRef.current),
                MAX_DELAY_MS,
            );
            const jitter = base * JITTER_FACTOR * (Math.random() * 2 - 1);
            const delay = Math.round(base + jitter);

            attemptRef.current += 1;

            reconnectTimer.current = setTimeout(() => {
                connect();
            }, delay);
        };

        ws.onerror = () => {
            // onclose will fire after onerror — reconnect is handled there.
            ws.close();
        };
    }, [url]);

    useEffect(() => {
        connect();

        return () => {
            // Cleanup on unmount.
            if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
            if (wsRef.current) {
                wsRef.current.onclose = null; // prevent reconnect loop
                wsRef.current.close();
            }
        };
    }, [connect]);

    return status;
}
