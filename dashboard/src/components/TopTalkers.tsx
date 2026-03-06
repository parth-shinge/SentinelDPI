import type { TopTalkerEntry } from "../types/metrics";

interface TopTalkersProps {
    talkers: TopTalkerEntry[];
}

export default function TopTalkers({ talkers }: TopTalkersProps) {
    const maxPackets = talkers.length > 0 ? talkers[0].packets : 1;

    return (
        <div className="dashboard-card p-5">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">
                Top Talkers
            </h2>

            {talkers.length === 0 ? (
                <p className="text-gray-600 text-xs text-center py-6">
                    No traffic recorded
                </p>
            ) : (
                <div className="space-y-3">
                    {talkers.map((t, i) => {
                        const pct = Math.round((t.packets / maxPackets) * 100);
                        return (
                            <div key={t.ip} className="group">
                                <div className="flex items-center justify-between mb-1">
                                    <div className="flex items-center gap-2 min-w-0">
                                        <span className="text-[10px] text-gray-600 font-mono w-4 shrink-0">
                                            {i + 1}.
                                        </span>
                                        <span className="text-sm font-mono text-gray-200 truncate">
                                            {t.ip}
                                        </span>
                                    </div>
                                    <span className="text-xs tabular-nums text-gray-400 ml-3 shrink-0">
                                        {t.packets.toLocaleString()}
                                    </span>
                                </div>
                                <div className="ml-6 h-1.5 rounded-full bg-gray-800 overflow-hidden">
                                    <div
                                        className="h-full rounded-full transition-all duration-500 ease-out"
                                        style={{
                                            width: `${pct}%`,
                                            background:
                                                i === 0
                                                    ? "linear-gradient(90deg, #3b82f6, #60a5fa)"
                                                    : i === 1
                                                        ? "linear-gradient(90deg, #6366f1, #818cf8)"
                                                        : "linear-gradient(90deg, #475569, #64748b)",
                                        }}
                                    />
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
