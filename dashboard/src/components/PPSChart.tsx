import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

export interface PPSDataPoint {
  time: string;
  pps: number;
}

interface PPSChartProps {
  data: PPSDataPoint[];
}

export default function PPSChart({ data }: PPSChartProps) {
  if (data.length === 0) {
    return (
      <div className="dashboard-card p-6 min-h-[300px] flex items-center justify-center">
        <span className="text-gray-600 text-sm">Collecting PPS data…</span>
      </div>
    );
  }

  return (
    <div className="dashboard-card p-6 min-h-[300px]">
      <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-5">
        Packets per Second (30 s)
      </h2>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255,255,255,0.04)"
            vertical={false}
          />
          <XAxis
            dataKey="time"
            tick={{ fill: "#6b7280", fontSize: 11 }}
            axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#6b7280", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={40}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "rgba(17,24,39,0.95)",
              border: "1px solid rgba(59,130,246,0.25)",
              borderRadius: "0.75rem",
              color: "#f3f4f6",
              fontSize: "0.75rem",
              boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
              backdropFilter: "blur(8px)",
            }}
          />
          <Line
            type="monotone"
            dataKey="pps"
            stroke="#3b82f6"
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 4, fill: "#3b82f6", stroke: "#60a5fa", strokeWidth: 2 }}
            animationDuration={600}
            animationEasing="ease-in-out"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
