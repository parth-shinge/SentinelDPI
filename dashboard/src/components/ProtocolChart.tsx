import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const COLORS = [
  "#3b82f6", // blue (accent)
  "#22d3ee", // cyan
  "#f59e0b", // amber
  "#10b981", // emerald
  "#f43f5e", // rose
  "#a78bfa", // violet
  "#fb923c", // orange
  "#2dd4bf", // teal
];

interface ProtocolChartProps {
  data: Record<string, number>;
}

interface SliceEntry {
  name: string;
  value: number;
}

export default function ProtocolChart({ data }: ProtocolChartProps) {
  const slices: SliceEntry[] = Object.entries(data).map(([name, value]) => ({
    name,
    value,
  }));

  if (slices.length === 0) {
    return (
      <div className="dashboard-card p-6 min-h-[300px] flex items-center justify-center">
        <span className="text-gray-600 text-sm">No protocol data</span>
      </div>
    );
  }

  return (
    <div className="dashboard-card p-6 min-h-[300px]">
      <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-5">
        Protocol Distribution
      </h2>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={slices}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={90}
            innerRadius={50}
            paddingAngle={3}
            stroke="none"
            animationDuration={800}
            animationEasing="ease-out"
          >
            {slices.map((_entry, idx) => (
              <Cell
                key={`cell-${idx}`}
                fill={COLORS[idx % COLORS.length]}
              />
            ))}
          </Pie>
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
          <Legend
            wrapperStyle={{ fontSize: "0.75rem", color: "#9ca3af" }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
