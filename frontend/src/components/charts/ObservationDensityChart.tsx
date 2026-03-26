import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { EncounterTypeDensity } from "@/api/analytics";

interface ObservationDensityChartProps {
  data: EncounterTypeDensity[];
}

export function ObservationDensityChart({ data }: ObservationDensityChartProps) {
  const chartData = data.map((item) => ({
    name: item.encounter_type,
    "Vital Signs": item.counts.vital_signs,
    Survey: item.counts.survey,
    Laboratory: item.counts.laboratory,
    Procedure: item.counts.procedure,
    Other: item.counts.other,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Legend />
        <Bar dataKey="Vital Signs" stackId="a" fill="var(--color-chart-2)" />
        <Bar dataKey="Survey" stackId="a" fill="var(--color-chart-1)" />
        <Bar dataKey="Laboratory" stackId="a" fill="var(--color-chart-4)" />
        <Bar dataKey="Procedure" stackId="a" fill="var(--color-chart-3)" />
        <Bar dataKey="Other" stackId="a" fill="var(--color-chart-5)" />
      </BarChart>
    </ResponsiveContainer>
  );
}
