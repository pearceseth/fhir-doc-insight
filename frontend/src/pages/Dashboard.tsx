import { useEffect, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { fetchEncounters, type Encounter, type EncounterFilters } from "@/api/fhir";

interface DashboardProps {
  onSelectEncounter: (encounterId: string) => void;
}

const PAGE_SIZE = 20;

export function Dashboard({ onSelectEncounter }: DashboardProps) {
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState<number | null>(null);
  const [total, setTotal] = useState<number | null>(null);
  const [filters, setFilters] = useState<EncounterFilters>({});

  useEffect(() => {
    async function loadEncounters() {
      setLoading(true);
      try {
        const data = await fetchEncounters(page, PAGE_SIZE, filters);
        setEncounters(data.encounters);
        setTotalPages(data.totalPages);
        setTotal(data.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load encounters");
      } finally {
        setLoading(false);
      }
    }
    loadEncounters();
  }, [page, filters]);

  function toggleFilter(key: keyof EncounterFilters) {
    setFilters((prev) => ({ ...prev, [key]: !prev[key] }));
    setPage(1);
  }

  function getEncounterType(encounter: Encounter): string {
    if (encounter.type && encounter.type.length > 0) {
      const type = encounter.type[0];
      if (type.text) return type.text;
      if (type.coding && type.coding.length > 0) {
        return type.coding[0].display || type.coding[0].code || "Unknown";
      }
    }
    if (encounter.class) {
      return encounter.class.display || encounter.class.code || "Unknown";
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

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-destructive">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Recent Encounters</h1>
      <div className="flex flex-wrap gap-2 mb-4">
        <Button
          variant={filters.missingDiagnosis ? "default" : "outline"}
          size="sm"
          onClick={() => toggleFilter("missingDiagnosis")}
        >
          Missing Diagnosis
        </Button>
        <Button
          variant={filters.missingParticipant ? "default" : "outline"}
          size="sm"
          onClick={() => toggleFilter("missingParticipant")}
        >
          Missing Provider
        </Button>
        <Button
          variant={filters.missingReason ? "default" : "outline"}
          size="sm"
          onClick={() => toggleFilter("missingReason")}
        >
          Missing Reason
        </Button>
        <Button
          variant={filters.missingType ? "default" : "outline"}
          size="sm"
          onClick={() => toggleFilter("missingType")}
        >
          Missing Type
        </Button>
        <Button
          variant={filters.missingClass ? "default" : "outline"}
          size="sm"
          onClick={() => toggleFilter("missingClass")}
        >
          Missing Class
        </Button>
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Patient</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  Loading encounters...
                </TableCell>
              </TableRow>
            ) : encounters.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  No encounters found
                </TableCell>
              </TableRow>
            ) : (
              encounters.map((encounter) => (
                <TableRow
                  key={encounter.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => onSelectEncounter(encounter.id)}
                >
                  <TableCell>{encounter._patient_name || "Unknown"}</TableCell>
                  <TableCell>{getEncounterType(encounter)}</TableCell>
                  <TableCell className="capitalize">{encounter.status}</TableCell>
                  <TableCell>{formatDate(encounter.period?.start)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-between mt-4">
        <p className="text-sm text-muted-foreground">
          {total !== null ? `Total encounters: ${total}` : ""}
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1 || loading}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} {totalPages !== null ? `of ${totalPages}` : ""}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => p + 1)}
            disabled={(totalPages !== null && page >= totalPages) || loading}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
