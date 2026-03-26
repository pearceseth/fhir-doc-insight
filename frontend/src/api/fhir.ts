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
  total: number | null;
  page: number;
  pageSize: number;
  totalPages: number | null;
}

export interface Reference {
  reference?: string;
  display?: string;
}

export interface Quantity {
  value?: number;
  unit?: string;
  system?: string;
  code?: string;
}

export interface Observation {
  id: string;
  resourceType: "Observation";
  status: string;
  category?: CodeableConcept[];
  code: CodeableConcept;
  subject?: Reference;
  encounter?: Reference;
  effectiveDateTime?: string;
  valueQuantity?: Quantity;
  valueString?: string;
  valueCodeableConcept?: CodeableConcept;
}

export interface ObservationsResponse {
  observations: Observation[];
  count: number;
}

export interface Attachment {
  contentType?: string;
  url?: string;
  title?: string;
}

export interface DocumentReferenceContent {
  attachment?: Attachment;
}

export interface DocumentReference {
  id: string;
  resourceType: "DocumentReference";
  status: string;
  type?: CodeableConcept;
  subject?: Reference;
  date?: string;
  content?: DocumentReferenceContent[];
}

export interface DocumentReferencesResponse {
  documentReferences: DocumentReference[];
  count: number;
}

export interface Dosage {
  text?: string;
  timing?: {
    code?: CodeableConcept;
  };
  doseAndRate?: Array<{
    doseQuantity?: Quantity;
  }>;
}

export interface MedicationRequest {
  id: string;
  resourceType: "MedicationRequest";
  status: string;
  intent: string;
  medicationCodeableConcept?: CodeableConcept;
  medicationReference?: Reference;
  subject?: Reference;
  encounter?: Reference;
  authoredOn?: string;
  dosageInstruction?: Dosage[];
}

export interface MedicationRequestsResponse {
  medicationRequests: MedicationRequest[];
  count: number;
}

export interface MedicationAdministration {
  id: string;
  resourceType: "MedicationAdministration";
  status: string;
  medicationCodeableConcept?: CodeableConcept;
  medicationReference?: Reference;
  subject?: Reference;
  context?: Reference;
  effectiveDateTime?: string;
  effectivePeriod?: Period;
}

export interface MedicationAdministrationsResponse {
  medicationAdministrations: MedicationAdministration[];
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

export interface EncounterFilters {
  missingDiagnosis?: boolean;
  missingParticipant?: boolean;
  missingReason?: boolean;
  missingType?: boolean;
  missingClass?: boolean;
}

export async function fetchEncounters(
  page = 1,
  pageSize = 20,
  filters?: EncounterFilters
): Promise<EncountersResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (filters?.missingDiagnosis) {
    params.set("missing_diagnosis", "true");
  }
  if (filters?.missingParticipant) {
    params.set("missing_participant", "true");
  }
  if (filters?.missingReason) {
    params.set("missing_reason", "true");
  }
  if (filters?.missingType) {
    params.set("missing_type", "true");
  }
  if (filters?.missingClass) {
    params.set("missing_class", "true");
  }
  const response = await fetch(`/api/encounters?${params}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch encounters: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchEncounterObservations(encounterId: string): Promise<ObservationsResponse> {
  const response = await fetch(`/api/encounters/${encounterId}/observations`);
  if (!response.ok) {
    throw new Error(`Failed to fetch observations: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchEncounterDocumentReferences(encounterId: string): Promise<DocumentReferencesResponse> {
  const response = await fetch(`/api/encounters/${encounterId}/document-references`);
  if (!response.ok) {
    throw new Error(`Failed to fetch document references: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchEncounterMedicationRequests(encounterId: string): Promise<MedicationRequestsResponse> {
  const response = await fetch(`/api/encounters/${encounterId}/medication-requests`);
  if (!response.ok) {
    throw new Error(`Failed to fetch medication requests: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchEncounterMedicationAdministrations(encounterId: string): Promise<MedicationAdministrationsResponse> {
  const response = await fetch(`/api/encounters/${encounterId}/medication-administrations`);
  if (!response.ok) {
    throw new Error(`Failed to fetch medication administrations: ${response.statusText}`);
  }
  return response.json();
}

export interface EncounterDetailsResponse {
  observations: Observation[];
  documentReferences: DocumentReference[];
  medicationRequests: MedicationRequest[];
  medicationAdministrations: MedicationAdministration[];
}

export async function fetchEncounterDetails(encounterId: string): Promise<EncounterDetailsResponse> {
  const response = await fetch(`/api/encounters/${encounterId}/details`);
  if (!response.ok) {
    throw new Error(`Failed to fetch encounter details: ${response.statusText}`);
  }
  return response.json();
}
