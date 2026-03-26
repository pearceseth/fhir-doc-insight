interface CompletenessScoreProps {
  hasObservations: boolean;
  hasDocuments: boolean;
  hasMedicationRequests: boolean;
  hasMedicationAdministrations: boolean;
}

export function CompletenessScore({
  hasObservations,
  hasDocuments,
  hasMedicationRequests,
  hasMedicationAdministrations,
}: CompletenessScoreProps) {
  const categories = [
    { name: "Observations", present: hasObservations },
    { name: "Documents", present: hasDocuments },
    { name: "Medication Requests", present: hasMedicationRequests },
    { name: "Medication Administrations", present: hasMedicationAdministrations },
  ];

  const presentCount = categories.filter((c) => c.present).length;
  const totalCount = categories.length;
  const percentage = Math.round((presentCount / totalCount) * 100);

  return (
    <div className="flex items-center gap-4">
      <span className="text-sm text-muted-foreground">
        Documentation Completeness:
      </span>
      <span className="font-semibold">
        {percentage}% ({presentCount}/{totalCount} categories)
      </span>
      <div className="flex gap-1">
        {categories.map((category) => (
          <span
            key={category.name}
            className={`text-xs px-2 py-1 rounded ${
              category.present
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}
            title={category.name}
          >
            {category.present ? "✓" : "✗"} {category.name}
          </span>
        ))}
      </div>
    </div>
  );
}
