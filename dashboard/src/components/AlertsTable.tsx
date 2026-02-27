import { useEffect, useRef } from "react";
import type { Alert } from "../types/alerts";

interface AlertsTableProps {
  alerts: Alert[];
}

const SEVERITY_STYLES: Record<string, string> = {
  HIGH: "bg-red-500/15 text-red-400 border-red-500/40 shadow-glowRed",
  MEDIUM: "bg-amber-500/15 text-amber-400 border-amber-500/40",
  LOW: "bg-blue-500/15 text-blue-400 border-blue-500/30",
};

function severityBadge(severity: string) {
  const style =
    SEVERITY_STYLES[severity] ??
    "bg-gray-500/15 text-gray-400 border-gray-500/30";
  return (
    <span
      className={`inline-block rounded-full border px-3 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${style}`}
    >
      {severity}
    </span>
  );
}

function formatTimestamp(ts: number): string {
  return new Date(ts * 1000).toLocaleTimeString();
}

export default function AlertsTable({ alerts }: AlertsTableProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new alerts arrive.
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [alerts.length]);

  if (alerts.length === 0) {
    return (
      <div className="dashboard-card p-6 min-h-[200px] flex items-center justify-center">
        <span className="text-gray-600 text-sm">No alerts</span>
      </div>
    );
  }

  return (
    <div className="dashboard-card p-6">
      <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-5">
        Recent Alerts
      </h2>
      <div
        ref={scrollRef}
        className="overflow-x-auto max-h-[320px] overflow-y-auto"
      >
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 bg-gray-900/95 backdrop-blur-sm">
            <tr className="border-b border-gray-800/80 text-[11px] uppercase tracking-widest text-gray-500">
              <th className="pb-3 pr-4 font-semibold">Type</th>
              <th className="pb-3 pr-4 font-semibold">Source IP</th>
              <th className="pb-3 pr-4 font-semibold">Severity</th>
              <th className="pb-3 font-semibold">Time</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert) => (
              <tr
                key={alert.id}
                className="border-b border-gray-800/40 hover:bg-accent/5 transition-colors duration-200"
              >
                <td className="py-3 pr-4 font-mono text-gray-300 text-xs">
                  {alert.type}
                </td>
                <td className="py-3 pr-4 text-gray-400">
                  {alert.source_ip ?? "—"}
                </td>
                <td className="py-3 pr-4">{severityBadge(alert.severity)}</td>
                <td className="py-3 text-gray-500 tabular-nums">
                  {formatTimestamp(alert.timestamp)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
