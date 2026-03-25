export interface HumanName {
  family?: string;
  given?: string[];
  use?: string;
}

export interface Patient {
  id: string;
  resourceType: "Patient";
  name?: HumanName[];
  gender?: string;
  birthDate?: string;
}

export interface Coding {
  system?: string;
  code?: string;
  display?: string;
}

export interface CodeableConcept {
  coding?: Coding[];
  text?: string;
}

export interface Period {
  start?: string;
  end?: string;
}

export interface Encounter {
  id: string;
  resourceType: "Encounter";
  status: string;
  class?: Coding;
  type?: CodeableConcept[];
  subject?: {
    reference?: string;
    display?: string;
  };
  period?: Period;
  _patient_name?: string;
}

export interface PatientsResponse {
  patients: Patient[];
  count: number;
}

export interface EncountersResponse {
  encounters: Encounter[];
  count: number;
}

export async function fetchPatients(): Promise<PatientsResponse> {
  const response = await fetch("/api/patients");
  if (!response.ok) {
    throw new Error(`Failed to fetch patients: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchPatient(id: string): Promise<Patient> {
  const response = await fetch(`/api/patients/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch patient: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchPatientEncounters(patientId: string): Promise<EncountersResponse> {
  const response = await fetch(`/api/patients/${patientId}/encounters`);
  if (!response.ok) {
    throw new Error(`Failed to fetch encounters: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchEncounters(): Promise<EncountersResponse> {
  const response = await fetch("/api/encounters");
  if (!response.ok) {
    throw new Error(`Failed to fetch encounters: ${response.statusText}`);
  }
  return response.json();
}
