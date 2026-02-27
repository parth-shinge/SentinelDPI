import type { Alert } from "../types/alerts";

interface ThreatFeedProps {
    alerts: Alert[];
}

function timeAgo(timestamp: number): string {
    const now = Date.now() / 1000;
    const diff = Math.max(0, now - timestamp);
    if (diff < 60) return `${Math.round(diff)}s ago`;
    if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
    return `${Math.round(diff / 3600)}h ago`;
}

const SEVERITY_DOT: Record<string, string> = {
    HIGH: "bg-red-500",
    MEDIUM: "bg-amber-500",
    LOW: "bg-blue-500",
};

const TYPE_ICON: Record<string, string> = {
    PORT_SCAN: "🔍",
    HIGH_TRAFFIC: "📈",
};

export default function ThreatFeed({ alerts }: ThreatFeedProps) {
    // Show last 20 alerts, newest first.
    const recent = [...alerts].reverse().slice(0, 20);

    return (
        <div className="dashboard-card p-5 h-full">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">
                Threat Feed
            </h2>

            {recent.length === 0 ? (
                <p className="text-gray-600 text-xs text-center py-8">
                    No threats detected
                </p>
            ) : (
                <div className="space-y-2 overflow-y-auto max-h-[calc(100vh-200px)] pr-1">
                    {recent.map((alert) => (
                        <div
                            key={alert.id}
                            className="flex items-start gap-3 rounded-lg bg-gray-800/40 px-3.5 py-2.5 hover:bg-gray-800/60 transition-colors duration-150"
                        >
                            <span className="text-sm mt-0.5">
                                {TYPE_ICON[alert.type] ?? "⚠"}
                            </span>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className="text-xs font-mono text-gray-300 truncate">
                                        {alert.type}
                                    </span>
                                    <span
                                        className={`inline-block h-1.5 w-1.5 rounded-full ${SEVERITY_DOT[alert.severity] ?? "bg-gray-500"}`}
                                    />
                                </div>
                                <p className="text-[11px] text-gray-500 mt-0.5">
                                    {alert.source_ip ?? "N/A"} · {timeAgo(alert.timestamp)}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
