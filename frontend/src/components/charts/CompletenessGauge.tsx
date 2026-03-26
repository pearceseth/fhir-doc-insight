import { RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis } from "recharts";

interface CompletenessGaugeProps {
  value: number; // 0-1 scale
}

export function CompletenessGauge({ value }: CompletenessGaugeProps) {
  const percentage = Math.round(value * 100);
  const data = [{ name: "Completeness", value: percentage, fill: "var(--color-chart-1)" }];

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={300}>
        <RadialBarChart
          cx="50%"
          cy="50%"
          innerRadius="60%"
          outerRadius="90%"
          barSize={20}
          data={data}
          startAngle={180}
          endAngle={0}
        >
          <PolarAngleAxis
            type="number"
            domain={[0, 100]}
            angleAxisId={0}
            tick={false}
          />
          <RadialBar
            background={{ fill: "var(--color-muted)" }}
            dataKey="value"
            cornerRadius={10}
            angleAxisId={0}
          />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-bold">{percentage}%</span>
        <span className="text-sm text-muted-foreground">Complete</span>
      </div>
    </div>
  );
}
