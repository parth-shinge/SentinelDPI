import { useState, useCallback, useEffect } from "react";
import type { MetricsSnapshot } from "../types/metrics";
import type { Alert } from "../types/alerts";
import StatCard from "../components/StatCard";
import ProtocolChart from "../components/ProtocolChart";
import PPSChart from "../components/PPSChart";
import type { PPSDataPoint } from "../components/PPSChart";
import AlertsTable from "../components/AlertsTable";
import AlertToast from "../components/AlertToast";
import ThreatFeed from "../components/ThreatFeed";
import { useWebSocket, type ConnectionStatus } from "../hooks/useWebSocket";

const WS_URL = "ws://127.0.0.1:8000/ws";
const PPS_HISTORY_SIZE = 30; // 30 ticks × 1 s = 30 s

// ------------------------------------------------------------------ //
// Sub-components
// ------------------------------------------------------------------ //

function LiveClock() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <span className="text-sm font-medium tabular-nums text-gray-400">
      {time.toLocaleTimeString()}
    </span>
  );
}

function StatusDot({ status }: { status: ConnectionStatus }) {
  const isConnected = status === "connected";
  const dotColor = isConnected ? "bg-emerald-500" : "bg-red-500";
  const pingColor = isConnected ? "bg-emerald-400" : "bg-red-400";
  const label = status === "connecting" ? "Connecting…" : isConnected ? "Live" : "Disconnected";

  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-2.5 w-2.5">
        {isConnected && (
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${pingColor} opacity-75`} />
        )}
        <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${dotColor} transition-colors duration-300`} />
      </span>
      <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
    </div>
  );
}

// ------------------------------------------------------------------ //
// Dashboard
// ------------------------------------------------------------------ //

/** WebSocket message envelope from the backend. */
interface WsMessage {
  event: "metrics" | "alert";
  data: MetricsSnapshot | Alert;
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<MetricsSnapshot | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [totalAlerts, setTotalAlerts] = useState(0);
  const [ppsHistory, setPpsHistory] = useState<PPSDataPoint[]>([]);

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const msg: WsMessage = JSON.parse(event.data as string);

      if (msg.event === "metrics") {
        const m = msg.data as MetricsSnapshot;
        setMetrics(m);

        // Append to rolling PPS history.
        setPpsHistory((prev) => {
          const next: PPSDataPoint = {
            time: new Date().toLocaleTimeString(),
            pps: m.packets_per_second,
          };
          const updated = [...prev, next];
          return updated.length > PPS_HISTORY_SIZE
            ? updated.slice(updated.length - PPS_HISTORY_SIZE)
            : updated;
        });
      } else if (msg.event === "alert") {
        const alert = msg.data as Alert;
        setAlerts((prev) => [...prev, alert]);
        setTotalAlerts((n) => n + 1);
      }
    } catch {
      // Malformed messages are silently ignored.
    }
  }, []);

  const connectionStatus = useWebSocket({
    url: WS_URL,
    onMessage: handleMessage,
  });

  return (
    <div className="min-h-screen text-gray-100 px-6 py-8 md:px-10">
      {/* Header */}
      <header className="mb-10 flex items-end justify-between">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-white">
            Sentinel<span className="text-accent">DPI</span>
          </h1>
          <p className="text-sm text-gray-500 mt-1.5 tracking-wide">
            Network Monitoring Dashboard
          </p>
        </div>
        <div className="flex items-center gap-4">
          <StatusDot status={connectionStatus} />
          <LiveClock />
        </div>
      </header>

      {/* Disconnected banner */}
      {connectionStatus === "disconnected" && (
        <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-5 py-3.5 text-sm text-red-400 shadow-glowRed">
          ⚠ WebSocket disconnected — reconnecting…
        </div>
      )}

      {/* Main content + Threat feed sidebar */}
      <div className="flex gap-5">
        {/* Main content */}
        <div className="flex-1 min-w-0">
          {/* Stat cards */}
          <section className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
            <StatCard
              label="Total Packets"
              value={metrics?.total_packets.toLocaleString() ?? "—"}
            />
            <StatCard
              label="Packets / sec"
              value={metrics?.packets_per_second.toFixed(1) ?? "—"}
            />
            <StatCard
              label="Total Alerts"
              value={totalAlerts.toLocaleString()}
            />
          </section>

          {/* Charts row */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
            <ProtocolChart data={metrics?.packets_per_protocol ?? {}} />
            <PPSChart data={ppsHistory} />
          </section>

          {/* Alerts table */}
          <section>
            <AlertsTable alerts={alerts} />
          </section>
        </div>

        {/* Threat Feed sidebar — hidden on small screens */}
        <aside className="hidden xl:block w-80 shrink-0">
          <ThreatFeed alerts={alerts} />
        </aside>
      </div>

      {/* Alert toast popups */}
      <AlertToast alerts={alerts} />
    </div>
  );
}
