import type { ConnectionStatus } from "../hooks/useWebSocket";
import type { SystemStatusData } from "../types/metrics";

interface SystemStatusProps {
    wsStatus: ConnectionStatus;
    backendStatus: SystemStatusData | null;
}

interface StatusRow {
    label: string;
    value: string;
    ok: boolean;
}

export default function SystemStatus({
    wsStatus,
    backendStatus,
}: SystemStatusProps) {
    const isConnected = wsStatus === "connected";

    const rows: StatusRow[] = [
        {
            label: "Capture Engine",
            value: backendStatus?.capture_engine === "running" ? "Running" : "Stopped",
            ok: backendStatus?.capture_engine === "running",
        },
        {
            label: "Packet Processor",
            value: backendStatus?.packet_processor === "running" ? "Running" : "Stopped",
            ok: backendStatus?.packet_processor === "running",
        },
        {
            label: "WebSocket",
            value: isConnected
                ? "Connected"
                : wsStatus === "connecting"
                    ? "Connecting…"
                    : "Disconnected",
            ok: isConnected,
        },
        {
            label: "Active Detectors",
            value: String(backendStatus?.detectors_loaded ?? 0),
            ok: (backendStatus?.detectors_loaded ?? 0) > 0,
        },
    ];

    return (
        <div className="dashboard-card p-5">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">
                System Status
            </h2>

            <div className="space-y-2.5">
                {rows.map((row) => (
                    <div
                        key={row.label}
                        className="flex items-center justify-between text-xs"
                    >
                        <span className="text-gray-400">{row.label}</span>
                        <div className="flex items-center gap-2">
                            <span
                                className={`h-1.5 w-1.5 rounded-full ${row.ok ? "bg-emerald-500" : "bg-red-500"
                                    }`}
                            />
                            <span
                                className={`font-mono ${row.ok ? "text-emerald-400" : "text-red-400"
                                    }`}
                            >
                                {row.value}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
