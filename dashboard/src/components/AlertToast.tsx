import { useEffect, useState } from "react";
import type { Alert } from "../types/alerts";

interface ToastItem {
    id: string;
    alert: Alert;
    exiting: boolean;
}

const MAX_TOASTS = 5;
const AUTO_DISMISS_MS = 5000;

interface AlertToastProps {
    alerts: Alert[];
}

export default function AlertToast({ alerts }: AlertToastProps) {
    const [toasts, setToasts] = useState<ToastItem[]>([]);

    // Watch for new alerts appended to the array.
    useEffect(() => {
        if (alerts.length === 0) return;
        const latest = alerts[alerts.length - 1];

        setToasts((prev) => {
            // Prevent duplicates.
            if (prev.some((t) => t.id === latest.id)) return prev;

            const next = [...prev, { id: latest.id, alert: latest, exiting: false }];
            // Cap at MAX_TOASTS.
            return next.length > MAX_TOASTS ? next.slice(next.length - MAX_TOASTS) : next;
        });
    }, [alerts]);

    // Auto-dismiss timer for each toast.
    useEffect(() => {
        if (toasts.length === 0) return;
        const oldest = toasts.find((t) => !t.exiting);
        if (!oldest) return;

        const timer = setTimeout(() => {
            dismiss(oldest.id);
        }, AUTO_DISMISS_MS);

        return () => clearTimeout(timer);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [toasts]);

    function dismiss(id: string) {
        // Mark as exiting for slide-out animation.
        setToasts((prev) =>
            prev.map((t) => (t.id === id ? { ...t, exiting: true } : t))
        );
        // Remove after animation.
        setTimeout(() => {
            setToasts((prev) => prev.filter((t) => t.id !== id));
        }, 300);
    }

    if (toasts.length === 0) return null;

    const severityColor: Record<string, string> = {
        HIGH: "border-red-500/60 bg-red-500/10 text-red-400",
        MEDIUM: "border-amber-500/60 bg-amber-500/10 text-amber-400",
        LOW: "border-blue-500/60 bg-blue-500/10 text-blue-400",
    };

    return (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none">
            {toasts.map((toast) => {
                const color =
                    severityColor[toast.alert.severity] ??
                    "border-gray-500/60 bg-gray-500/10 text-gray-400";
                const animClass = toast.exiting
                    ? "animate-toast-out"
                    : "animate-toast-in";

                return (
                    <div
                        key={toast.id}
                        className={`pointer-events-auto rounded-xl border backdrop-blur-md px-5 py-3.5 shadow-lg max-w-xs ${color} ${animClass}`}
                    >
                        <div className="flex items-center justify-between gap-4">
                            <div>
                                <p className="text-xs font-bold uppercase tracking-wider">
                                    {toast.alert.type}
                                </p>
                                <p className="text-[11px] mt-0.5 opacity-70">
                                    {toast.alert.source_ip ?? "N/A"} · {toast.alert.severity}
                                </p>
                            </div>
                            <button
                                onClick={() => dismiss(toast.id)}
                                className="text-gray-500 hover:text-gray-300 transition-colors text-lg leading-none"
                                aria-label="Dismiss"
                            >
                                ×
                            </button>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
