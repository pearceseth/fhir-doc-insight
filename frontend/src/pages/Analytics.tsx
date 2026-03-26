import { useEffect, useState } from "react";
import { ChartCard } from "@/components/dashboard/ChartCard";
import { CompletenessChart } from "@/components/charts/CompletenessChart";
import { ObservationDensityChart } from "@/components/charts/ObservationDensityChart";
import { MedicationRecChart } from "@/components/charts/MedicationRecChart";
import { CompletenessGauge } from "@/components/charts/CompletenessGauge";
import {
  fetchDocumentationCompleteness,
  fetchObservationDensity,
  fetchMedicationReconciliation,
  type CompletenessScore,
  type EncounterTypeDensity,
  type MedicationReconciliation,
} from "@/api/analytics";

export function Analytics() {
  const [completeness, setCompleteness] = useState<CompletenessScore[]>([]);
  const [density, setDensity] = useState<EncounterTypeDensity[]>([]);
  const [reconciliation, setReconciliation] = useState<MedicationReconciliation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        const [completenessData, densityData, reconciliationData] = await Promise.all([
          fetchDocumentationCompleteness(),
          fetchObservationDensity(),
          fetchMedicationReconciliation(),
        ]);
        setCompleteness(completenessData.completeness);
        setDensity(densityData.density);
        setReconciliation(reconciliationData.reconciliation);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analytics");
      } finally {
        setLoading(false);
      }
    }
    loadAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">Loading analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-destructive">Error: {error}</p>
      </div>
    );
  }

  const averageCompleteness = completeness.length > 0
    ? completeness.reduce((sum, item) => sum + item.score, 0) / completeness.length
    : 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Analytics Dashboard</h1>

      {/* Charts Row 1 - 2 columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ChartCard title="Documentation Completeness">
          {completeness.length > 0 ? (
            <CompletenessChart data={completeness} />
          ) : (
            <p className="text-muted-foreground text-center py-8">
              No completeness data available
            </p>
          )}
        </ChartCard>

        <ChartCard title="Observation Density">
          {density.length > 0 ? (
            <ObservationDensityChart data={density} />
          ) : (
            <p className="text-muted-foreground text-center py-8">
              No observation density data available
            </p>
          )}
        </ChartCard>
      </div>

      {/* Charts Row 2 - 2 columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ChartCard title="Medication Reconciliation">
          {reconciliation.length > 0 ? (
            <MedicationRecChart data={reconciliation} />
          ) : (
            <p className="text-muted-foreground text-center py-8">
              No medication reconciliation data available
            </p>
          )}
        </ChartCard>

        <ChartCard title="Overall Completeness">
          <CompletenessGauge value={averageCompleteness} />
        </ChartCard>
      </div>
    </div>
  );
}
