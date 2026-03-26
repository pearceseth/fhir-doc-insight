import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchEncounters,
  fetchEncounterDetails,
  type Encounter,
  type Observation,
  type DocumentReference,
  type MedicationRequest,
  type MedicationAdministration,
} from "@/api/fhir";
import { ObservationsSection } from "@/components/encounter/ObservationsSection";
import { DocumentsSection } from "@/components/encounter/DocumentsSection";
import { MedicationsSection } from "@/components/encounter/MedicationsSection";
import { CompletenessScore } from "@/components/encounter/CompletenessScore";

interface EncounterDetailProps {
  encounterId: string;
  onBack: () => void;
}

export function EncounterDetail({ encounterId, onBack }: EncounterDetailProps) {
  const [encounter, setEncounter] = useState<Encounter | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [documents, setDocuments] = useState<DocumentReference[]>([]);
  const [medicationRequests, setMedicationRequests] = useState<MedicationRequest[]>([]);
  const [medicationAdministrations, setMedicationAdministrations] = useState<MedicationAdministration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [encountersRes, detailsRes] = await Promise.all([
          fetchEncounters(),
          fetchEncounterDetails(encounterId),
        ]);

        const found = encountersRes.encounters.find((e) => e.id === encounterId);
        setEncounter(found || null);
        setObservations(detailsRes.observations);
        setDocuments(detailsRes.documentReferences);
        setMedicationRequests(detailsRes.medicationRequests);
        setMedicationAdministrations(detailsRes.medicationAdministrations);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load encounter details");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [encounterId]);

  function getEncounterType(enc: Encounter): string {
    if (enc.type && enc.type.length > 0) {
      const type = enc.type[0];
      if (type.text) return type.text;
      if (type.coding && type.coding.length > 0) {
        return type.coding[0].display || type.coding[0].code || "Unknown";
      }
    }
    if (enc.class) {
      return enc.class.display || enc.class.code || "Unknown";
    }
    return "Unknown";
  }

  function formatDate(dateString?: string): string {
    if (!dateString) return "N/A";
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">Loading encounter details...</p>
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

  if (!encounter) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Button variant="ghost" onClick={onBack} className="mb-4">
          ← Back to Encounters
        </Button>
        <p className="text-muted-foreground">Encounter not found</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <Button variant="ghost" onClick={onBack} className="mb-4">
        ← Back to Encounters
      </Button>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Encounter Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Patient</span>
              <p className="font-medium">{encounter._patient_name || "Unknown"}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Type</span>
              <p className="font-medium">{getEncounterType(encounter)}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Status</span>
              <p className="font-medium capitalize">{encounter.status}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Date</span>
              <p className="font-medium">
                {formatDate(encounter.period?.start)}
                {encounter.period?.end && ` - ${formatDate(encounter.period.end)}`}
              </p>
            </div>
          </div>
          <CompletenessScore
            hasObservations={observations.length > 0}
            hasDocuments={documents.length > 0}
            hasMedicationRequests={medicationRequests.length > 0}
            hasMedicationAdministrations={medicationAdministrations.length > 0}
          />
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Observations</CardTitle>
          </CardHeader>
          <CardContent>
            <ObservationsSection observations={observations} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Documents</CardTitle>
          </CardHeader>
          <CardContent>
            <DocumentsSection documents={documents} />
          </CardContent>
        </Card>

        <Card className="col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Medications</CardTitle>
          </CardHeader>
          <CardContent>
            <MedicationsSection
              requests={medicationRequests}
              administrations={medicationAdministrations}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
