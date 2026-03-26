import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { CompletenessScore } from "@/api/analytics";

interface CompletenessChartProps {
  data: CompletenessScore[];
}

export function CompletenessChart({ data }: CompletenessChartProps) {
  const chartData = data.map((item) => ({
    name: item.encounterId.slice(0, 8),
    score: Math.round(item.score * 100),
    encounterType: item.encounterType,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis
          domain={[0, 100]}
          tickFormatter={(value) => `${value}%`}
          tick={{ fontSize: 12 }}
        />
        <Tooltip
          formatter={(value) => [`${value}%`, "Completeness"]}
          labelFormatter={(label) => `Encounter: ${label}`}
        />
        <Bar dataKey="score" fill="var(--color-chart-1)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
