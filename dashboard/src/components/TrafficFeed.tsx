import { useRef, useEffect } from "react";
import type { TrafficFeedEntry } from "../types/metrics";

interface TrafficFeedProps {
    feed: TrafficFeedEntry[];
}

const PROTOCOL_COLOR: Record<string, string> = {
    TCP: "text-blue-400",
    UDP: "text-violet-400",
    DNS: "text-cyan-400",
    ICMP: "text-amber-400",
};

function formatTime(ts: number): string {
    const d = new Date(ts * 1000);
    return d.toLocaleTimeString([], { hour12: false });
}

export default function TrafficFeed({ feed }: TrafficFeedProps) {
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom on new entries.
    useEffect(() => {
        const el = scrollRef.current;
        if (el) el.scrollTop = el.scrollHeight;
    }, [feed.length]);

    return (
        <div className="dashboard-card p-5 flex flex-col">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-3">
                Live Traffic Feed
            </h2>

            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto max-h-64 space-y-0.5 pr-1"
            >
                {feed.length === 0 ? (
                    <p className="text-gray-600 text-xs text-center py-6">
                        Awaiting traffic…
                    </p>
                ) : (
                    feed.map((entry, i) => (
                        <div
                            key={`${entry.timestamp}-${i}`}
                            className="flex items-center gap-2 rounded px-2.5 py-1.5 text-xs font-mono hover:bg-gray-800/50 transition-colors duration-100"
                        >
                            <span className="text-gray-600 tabular-nums shrink-0">
                                {formatTime(entry.timestamp)}
                            </span>
                            <span className="text-gray-300 truncate">{entry.src_ip}</span>
                            <span className="text-gray-600">→</span>
                            <span className="text-gray-300 truncate">{entry.dst_ip}</span>
                            <span
                                className={`ml-auto shrink-0 ${PROTOCOL_COLOR[entry.protocol] ?? "text-gray-500"
                                    }`}
                            >
                                {entry.protocol}
                            </span>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
