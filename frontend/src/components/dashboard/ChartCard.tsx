import { Card, CardContent, CardHeader, CardTitle, CardAction } from "@/components/ui/card";

interface ChartCardProps {
  title: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}

export function ChartCard({ title, action, children }: ChartCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {action && <CardAction>{action}</CardAction>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
