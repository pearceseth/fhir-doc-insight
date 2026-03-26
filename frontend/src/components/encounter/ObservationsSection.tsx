import type { Observation } from "@/api/fhir";

interface ObservationsSectionProps {
  observations: Observation[];
}

function getCategoryDisplay(observation: Observation): string {
  if (observation.category && observation.category.length > 0) {
    const cat = observation.category[0];
    if (cat.text) return cat.text;
    if (cat.coding && cat.coding.length > 0) {
      return cat.coding[0].display || cat.coding[0].code || "Other";
    }
  }
  return "Other";
}

function getCodeDisplay(observation: Observation): string {
  if (observation.code.text) return observation.code.text;
  if (observation.code.coding && observation.code.coding.length > 0) {
    return observation.code.coding[0].display || observation.code.coding[0].code || "Unknown";
  }
  return "Unknown";
}

function getValueDisplay(observation: Observation): string {
  if (observation.valueQuantity) {
    const { value, unit } = observation.valueQuantity;
    return `${value ?? ""} ${unit ?? ""}`.trim();
  }
  if (observation.valueString) {
    return observation.valueString;
  }
  if (observation.valueCodeableConcept) {
    if (observation.valueCodeableConcept.text) {
      return observation.valueCodeableConcept.text;
    }
    if (observation.valueCodeableConcept.coding && observation.valueCodeableConcept.coding.length > 0) {
      return observation.valueCodeableConcept.coding[0].display || "";
    }
  }
  return "—";
}

export function ObservationsSection({ observations }: ObservationsSectionProps) {
  if (observations.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">No observations recorded</div>
    );
  }

  const groupedByCategory = observations.reduce((acc, obs) => {
    const category = getCategoryDisplay(obs);
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(obs);
    return acc;
  }, {} as Record<string, Observation[]>);

  return (
    <div className="space-y-4">
      {Object.entries(groupedByCategory).map(([category, obs]) => (
        <div key={category}>
          <h4 className="font-medium text-sm mb-2">
            {category} ({obs.length})
          </h4>
          <ul className="space-y-1 pl-4">
            {obs.map((o) => (
              <li key={o.id} className="text-sm">
                <span className="text-muted-foreground">{getCodeDisplay(o)}:</span>{" "}
                <span className="font-medium">{getValueDisplay(o)}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
