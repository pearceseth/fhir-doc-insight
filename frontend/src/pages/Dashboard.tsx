import { useEffect, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { fetchEncounters, type Encounter } from "@/api/fhir";

export function Dashboard() {
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadEncounters() {
      try {
        const data = await fetchEncounters();
        setEncounters(data.encounters);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load encounters");
      } finally {
        setLoading(false);
      }
    }
    loadEncounters();
  }, []);

  function getEncounterType(encounter: Encounter): string {
    if (encounter.type && encounter.type.length > 0) {
      const type = encounter.type[0];
      return type.text || type.coding?.[0]?.display || "Unknown";
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
        <p className="text-muted-foreground">Loading encounters...</p>
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

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Encounters</h1>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Patient Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Class</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Start Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {encounters.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground">
                  No encounters found
                </TableCell>
              </TableRow>
            ) : (
              encounters.map((encounter) => (
                <TableRow key={encounter.id}>
                  <TableCell className="font-mono text-sm">{encounter.id}</TableCell>
                  <TableCell>{encounter._patient_name || "Unknown"}</TableCell>
                  <TableCell>
                    <span className="capitalize">{encounter.status}</span>
                  </TableCell>
                  <TableCell>{encounter.class?.display || encounter.class?.code || "N/A"}</TableCell>
                  <TableCell>{getEncounterType(encounter)}</TableCell>
                  <TableCell>{formatDate(encounter.period?.start)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      <p className="text-sm text-muted-foreground mt-4">
        Total encounters: {encounters.length}
      </p>
    </div>
  );
}
