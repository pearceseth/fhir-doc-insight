import type { MedicationRequest, MedicationAdministration } from "@/api/fhir";

interface MedicationsSectionProps {
  requests: MedicationRequest[];
  administrations: MedicationAdministration[];
}

function getMedicationName(
  med: MedicationRequest | MedicationAdministration
): string {
  if (med.medicationCodeableConcept?.text) {
    return med.medicationCodeableConcept.text;
  }
  if (med.medicationCodeableConcept?.coding && med.medicationCodeableConcept.coding.length > 0) {
    return med.medicationCodeableConcept.coding[0].display ||
           med.medicationCodeableConcept.coding[0].code ||
           "Unknown";
  }
  if (med.medicationReference?.display) {
    return med.medicationReference.display;
  }
  return "Unknown medication";
}

function getDosageText(request: MedicationRequest): string {
  if (request.dosageInstruction && request.dosageInstruction.length > 0) {
    const dosage = request.dosageInstruction[0];
    if (dosage.text) return dosage.text;
    if (dosage.doseAndRate && dosage.doseAndRate.length > 0) {
      const dose = dosage.doseAndRate[0].doseQuantity;
      if (dose) {
        return `${dose.value ?? ""} ${dose.unit ?? ""}`.trim();
      }
    }
  }
  return "";
}

export function MedicationsSection({ requests, administrations }: MedicationsSectionProps) {
  const hasRequests = requests.length > 0;
  const hasAdministrations = administrations.length > 0;

  if (!hasRequests && !hasAdministrations) {
    return (
      <div className="text-sm text-muted-foreground">No medications recorded</div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-6">
      <div>
        <h4 className="font-medium text-sm mb-2">Medication Requests ({requests.length})</h4>
        {hasRequests ? (
          <ul className="space-y-2">
            {requests.map((req) => (
              <li key={req.id} className="text-sm">
                <div className="font-medium">{getMedicationName(req)}</div>
                {getDosageText(req) && (
                  <div className="text-muted-foreground text-xs">{getDosageText(req)}</div>
                )}
                <div className="text-xs text-muted-foreground capitalize">
                  {req.status} • {req.intent}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-sm text-muted-foreground">None</div>
        )}
      </div>

      <div>
        <h4 className="font-medium text-sm mb-2">Administrations ({administrations.length})</h4>
        {hasAdministrations ? (
          <ul className="space-y-2">
            {administrations.map((admin) => (
              <li key={admin.id} className="text-sm">
                <div className="font-medium">{getMedicationName(admin)}</div>
                <div className="text-xs text-muted-foreground capitalize">
                  {admin.status}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-sm text-muted-foreground">None</div>
        )}
      </div>
    </div>
  );
}
