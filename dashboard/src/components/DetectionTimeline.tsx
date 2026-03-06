import type { Alert } from "../types/alerts";

interface DetectionTimelineProps {
    alerts: Alert[];
}

const TYPE_ICON: Record<string, string> = {
    PORT_SCAN: "🔍",
    HIGH_TRAFFIC: "📈",
};

const SEVERITY_COLOR: Record<string, string> = {
    HIGH: "border-red-500 bg-red-500",
    MEDIUM: "border-amber-500 bg-amber-500",
    LOW: "border-blue-500 bg-blue-500",
};

function formatTimestamp(ts: number): string {
    const d = new Date(ts * 1000);
    return d.toLocaleTimeString([], { hour12: false });
}

export default function DetectionTimeline({ alerts }: DetectionTimelineProps) {
    // Show last 10 alerts, newest first.
    const recent = [...alerts].reverse().slice(0, 10);

    return (
        <div className="dashboard-card p-5 flex flex-col">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">
                Detection Timeline
            </h2>

            {recent.length === 0 ? (
                <p className="text-gray-600 text-xs text-center py-6">
                    No detections yet
                </p>
            ) : (
                <div className="relative overflow-y-auto max-h-64 pr-1">
                    {/* Vertical line */}
                    <div className="absolute left-[7px] top-2 bottom-2 w-px bg-gray-800" />

                    <div className="space-y-3 pl-6">
                        {recent.map((alert) => {
                            const dotColor =
                                SEVERITY_COLOR[alert.severity] ?? "border-gray-500 bg-gray-500";
                            return (
                                <div key={alert.id} className="relative flex items-start gap-3">
                                    {/* Timeline dot */}
                                    <span
                                        className={`absolute -left-6 top-1 h-3.5 w-3.5 rounded-full border-2 ${dotColor}/30 ${dotColor}/80`}
                                        style={{ marginLeft: "1px" }}
                                    />
                                    <div className="min-w-0">
                                        <div className="flex items-center gap-2">
                                            <span className="text-sm">
                                                {TYPE_ICON[alert.type] ?? "⚠"}
                                            </span>
                                            <span className="text-xs font-mono text-gray-300">
                                                {alert.type}
                                            </span>
                                        </div>
                                        <p className="text-[11px] text-gray-600 mt-0.5">
                                            {formatTimestamp(alert.timestamp)}
                                            {alert.source_ip && ` · ${alert.source_ip}`}
                                        </p>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}
