export interface CompletenessScore {
  encounterId: string;
  encounterType: string;
  patientId: string;
  score: number;
  missing_categories: string[];
  present_categories: string[];
}

export interface CompletenessResponse {
  completeness: CompletenessScore[];
  count: number;
}

export interface CategoryCounts {
  vital_signs: number;
  survey: number;
  laboratory: number;
  procedure: number;
  other: number;
}

export interface EncounterTypeDensity {
  encounter_type: string;
  counts: CategoryCounts;
  total: number;
}

export interface DensityResponse {
  density: EncounterTypeDensity[];
  count: number;
}

export interface MedicationReconciliation {
  encounterId: string;
  encounterType: string;
  patientId: string;
  total_requests: number;
  administered: number;
  status: "complete" | "incomplete";
}

export interface ReconciliationResponse {
  reconciliation: MedicationReconciliation[];
  count: number;
}

export async function fetchDocumentationCompleteness(): Promise<CompletenessResponse> {
  const response = await fetch("/api/analytics/documentation-completeness");
  if (!response.ok) {
    throw new Error(`Failed to fetch completeness: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchObservationDensity(): Promise<DensityResponse> {
  const response = await fetch("/api/analytics/observation-density");
  if (!response.ok) {
    throw new Error(`Failed to fetch density: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchMedicationReconciliation(): Promise<ReconciliationResponse> {
  const response = await fetch("/api/analytics/medication-reconciliation");
  if (!response.ok) {
    throw new Error(`Failed to fetch reconciliation: ${response.statusText}`);
  }
  return response.json();
}
