/**
 * TypeScript mirror of the backend's Pydantic contracts
 * (`backend/app/schemas.py`).
 *
 * These are hand-maintained rather than generated, because generation from
 * OpenAPI produces names and optionality that read badly in components. The
 * contract test in `backend/tests/test_schema_contract.py` fails if a field is
 * added server-side without being mirrored here, so drift is caught in CI
 * rather than at runtime in a clinician's browser.
 */

export type Locale = 'en' | 'de' | 'es' | 'nl' | 'ru';
export type LocaleMap = Partial<Record<Locale, string>>;

export type Discipline = 'chemical_pathology' | 'microbiology' | 'hematology' | 'pharmacology';
export type CaseStatus = 'draft' | 'in_review' | 'published' | 'retired';
export type Sex = 'female' | 'male' | 'intersex' | 'unspecified';
export type ResultFlag = 'N' | 'H' | 'L' | 'HH' | 'LL' | 'A';
export type Certainty = 'confirmed' | 'probable' | 'possible' | 'excluded';

export type SortField =
  | 'case_code'
  | 'title'
  | 'difficulty'
  | 'updated_at'
  | 'created_at'
  | 'discipline';

export interface Patient {
  id: number;
  pseudonym: string;
  age_years: number;
  sex: Sex;
  weight_kg: number | null;
  height_cm: number | null;
  ancestry: string | null;
  pregnancy_status: string | null;
  occupation: string | null;
  region: string | null;
  bmi: number | null;
}

export interface Medication {
  name: string;
  dose?: string;
  route?: string;
  frequency?: string;
  indication?: string;
  notes?: string;
}

export interface Presentation {
  id: number;
  chief_complaint: string;
  chief_complaint_i18n: LocaleMap;
  history_of_present_illness: string;
  past_medical_history: string[];
  medications: Medication[];
  allergies: string[];
  family_history: string[];
  social_history: string;
  review_of_systems: Record<string, string>;
  vitals: Record<string, string | number>;
  examination_findings: string[];
}

export interface LabResult {
  id: number;
  analyte_code: string;
  analyte_name: string;
  loinc_code: string | null;
  value_numeric: number | null;
  value_text: string | null;
  unit: string | null;
  ref_low: number | null;
  ref_high: number | null;
  ref_text: string | null;
  flag: ResultFlag;
  method: string | null;
  interference_note: string | null;
  is_critical: boolean;
}

export interface LabPanel {
  id: number;
  panel_code: string;
  panel_name: string;
  collected_at: string;
  day_offset: number;
  specimen: string;
  laboratory: string;
  analyser: string | null;
  comment: string;
  results: LabResult[];
}

export interface PeripheralSmear {
  id: number;
  collected_at: string;
  day_offset: number;
  stain: string;
  red_cell_morphology: string[];
  white_cell_morphology: string[];
  platelet_morphology: string[];
  narrative: string;
  narrative_i18n: LocaleMap;
  schistocyte_percent: number | null;
  reported_by: string | null;
}

export interface MolecularFinding {
  target: string;
  method: string;
  result: string;
  interpretation?: string;
}

export interface SusceptibilityResult {
  agent: string;
  method: string;
  result: string;
  mic: number | null;
  note?: string;
}

export interface MicrobiologyReport {
  id: number;
  collected_at: string;
  day_offset: number;
  specimen_type: string;
  site: string | null;
  organism: string | null;
  microscopy: string;
  bacterial_index: number | null;
  morphological_index: number | null;
  molecular_findings: MolecularFinding[];
  susceptibility: SusceptibilityResult[];
  interpretation: string;
}

export interface RegimenStep {
  agent: string;
  dose: string;
  route: string;
  frequency: string;
  duration?: string;
  notes?: string;
}

export interface TreatmentProtocol {
  id: number;
  name: string;
  name_i18n: LocaleMap;
  guideline_source: string | null;
  indication: string;
  duration_months: number | null;
  regimen: RegimenStep[];
  monitoring: string[];
  contraindications: string[];
  adverse_effects: string[];
  notes: string;
}

export interface Diagnosis {
  id: number;
  label: string;
  label_i18n: LocaleMap;
  is_primary: boolean;
  certainty: Certainty;
  likelihood: number | null;
  icd10: string | null;
  discriminator: string;
  supporting_evidence: string[];
  refuting_evidence: string[];
}

export interface ImagingStudy {
  id: number;
  modality: string;
  region: string;
  day_offset: number;
  findings: string;
  impression: string;
}

export interface Reference {
  citation: string;
  type?: string;
}

export interface ReasoningKeyFinding {
  label: string;
  synonyms: string[];
  weight?: number;
}

export interface SafetyRule {
  id: string;
  description: string;
  required_terms?: string[];
  forbidden_patterns?: string[];
}

export interface ReasoningKey {
  primary_diagnosis: string;
  accepted_diagnosis_terms: string[];
  must_include_findings: ReasoningKeyFinding[];
  expected_differential: string[];
  expected_next_tests: string[];
  expected_management: string[];
  critical_values: { analyte: string; value: number; reason: string }[];
  safety_rules: SafetyRule[];
  distractor_terms: string[];
}

export interface CaseSummary {
  id: number;
  case_code: string;
  title: string;
  title_i18n: LocaleMap;
  summary: string;
  summary_i18n: LocaleMap;
  discipline: Discipline;
  subspecialty: string;
  status: CaseStatus;
  difficulty: number;
  version: string;
  tags: string[];
  updated_at: string;
  patient: Patient | null;
}

export interface CaseDetail extends Omit<CaseSummary, 'patient'> {
  created_at: string;
  icd10_codes: string[];
  snomed_codes: string[];
  teaching_points: string[];
  references: Reference[];
  reasoning_key: ReasoningKey;
  author: string;
  reviewed_by: string | null;
  patient: Patient | null;
  presentation: Presentation | null;
  lab_panels: LabPanel[];
  smears: PeripheralSmear[];
  microbiology: MicrobiologyReport[];
  protocols: TreatmentProtocol[];
  diagnoses: Diagnosis[];
  imaging: ImagingStudy[];
}

export interface PageMeta {
  total: number;
  limit: number;
  offset: number;
  returned: number;
  has_more: boolean;
}

export interface CaseListResponse {
  meta: PageMeta;
  items: CaseSummary[];
}

export interface TrendPoint {
  collected_at: string;
  day_offset: number;
  value: number;
  unit: string | null;
  flag: ResultFlag;
  panel_code: string;
  is_critical: boolean;
}

export interface AnalyteTrend {
  analyte_code: string;
  analyte_name: string;
  unit: string | null;
  ref_low: number | null;
  ref_high: number | null;
  critical_low: number | null;
  critical_high: number | null;
  decimals: number;
  points: TrendPoint[];
}

export interface CaseTrends {
  case_id: number;
  case_code: string;
  series: AnalyteTrend[];
}

export interface StatsResponse {
  total_cases: number;
  by_discipline: Record<string, number>;
  by_subspecialty: Record<string, number>;
  by_difficulty: Record<string, number>;
  by_status: Record<string, number>;
  total_lab_results: number;
  total_panels: number;
  generated_at: string;
}

export interface ReferenceInterval {
  id: number;
  analyte_code: string;
  analyte_name: string;
  analyte_name_i18n: LocaleMap;
  loinc_code: string | null;
  unit: string;
  si_unit: string | null;
  si_conversion_factor: number | null;
  population: string;
  ref_low: number | null;
  ref_high: number | null;
  critical_low: number | null;
  critical_high: number | null;
  decimals: number;
  category: string;
  notes: string;
}

/** The RFC-7807-flavoured error body every non-2xx response uses. */
export interface ApiErrorBody {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string | null;
  errors: { location: string; message: string; type: string }[];
  request_id: string | null;
}

export interface CaseQuery {
  limit?: number;
  offset?: number;
  discipline?: Discipline | '';
  subspecialty?: string;
  status?: CaseStatus | '';
  difficulty?: number | '';
  difficulty_min?: number;
  difficulty_max?: number;
  tag?: string;
  search?: string;
  sort_by?: SortField;
  sort_dir?: 'asc' | 'desc';
}
