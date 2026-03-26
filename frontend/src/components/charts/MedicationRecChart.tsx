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
import type { MedicationReconciliation } from "@/api/analytics";

interface MedicationRecChartProps {
  data: MedicationReconciliation[];
}

export function MedicationRecChart({ data }: MedicationRecChartProps) {
  const chartData = data.map((item) => ({
    name: item.encounterId.slice(0, 8),
    Requested: item.total_requests,
    Administered: item.administered,
    status: item.status,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Legend />
        <Bar dataKey="Requested" fill="var(--color-muted-foreground)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="Administered" fill="var(--color-positive)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
