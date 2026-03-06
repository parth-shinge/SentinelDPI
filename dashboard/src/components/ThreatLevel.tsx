interface ThreatLevelProps {
    level: "LOW" | "MEDIUM" | "HIGH";
}

const CONFIG: Record<
    string,
    { label: string; color: string; bg: string; glow: string; icon: string }
> = {
    LOW: {
        label: "LOW",
        color: "text-emerald-400",
        bg: "bg-emerald-500/15 border-emerald-500/30",
        glow: "shadow-[0_0_12px_2px_rgba(16,185,129,0.25)]",
        icon: "🟢",
    },
    MEDIUM: {
        label: "MEDIUM",
        color: "text-amber-400",
        bg: "bg-amber-500/15 border-amber-500/30",
        glow: "shadow-[0_0_12px_2px_rgba(245,158,11,0.25)]",
        icon: "🟡",
    },
    HIGH: {
        label: "HIGH",
        color: "text-red-400",
        bg: "bg-red-500/15 border-red-500/30",
        glow: "shadow-[0_0_12px_2px_rgba(239,68,68,0.35)]",
        icon: "🔴",
    },
};

export default function ThreatLevel({ level }: ThreatLevelProps) {
    const cfg = CONFIG[level] ?? CONFIG.LOW;

    return (
        <div
            className={`dashboard-card flex items-center gap-3 px-5 py-4 border ${cfg.bg} ${cfg.glow} transition-all duration-500`}
        >
            <span className="text-lg">{cfg.icon}</span>
            <div>
                <p className="text-[10px] uppercase tracking-widest text-gray-500 font-medium">
                    Threat Level
                </p>
                <p className={`text-lg font-bold tracking-wide ${cfg.color}`}>
                    {cfg.label}
                </p>
            </div>
        </div>
    );
}
