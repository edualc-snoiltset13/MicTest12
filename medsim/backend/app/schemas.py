"""Pydantic v2 request/response contracts.

Every model that crosses the API boundary is declared here. The frontend's
TypeScript types (``frontend/src/api/types.ts``) are a hand-maintained mirror of
these; the contract test in ``tests/test_schema_contract.py`` fails if a field
is added here without being mirrored there.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import CaseStatus, Certainty, Discipline, ResultFlag, Sex

SUPPORTED_LOCALES = ("en", "de", "es", "nl", "ru")
LocaleMap = dict[str, str]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


def _validate_locale_keys(value: dict[str, str] | None) -> dict[str, str]:
    if not value:
        return {}
    unknown = sorted(set(value) - set(SUPPORTED_LOCALES))
    if unknown:
        raise ValueError(
            f"unsupported locale key(s): {unknown}; supported: {list(SUPPORTED_LOCALES)}"
        )
    return value


# ---------------------------------------------------------------------------
# Leaf entities
# ---------------------------------------------------------------------------


class PatientBase(BaseModel):
    pseudonym: str = Field(..., min_length=1, max_length=64)
    age_years: int = Field(..., ge=0, le=120)
    sex: Sex
    weight_kg: float | None = Field(default=None, gt=0, le=400)
    height_cm: float | None = Field(default=None, gt=0, le=260)
    ancestry: str | None = None
    pregnancy_status: str | None = None
    occupation: str | None = None
    region: str | None = None


class PatientRead(PatientBase, ORMModel):
    id: int
    bmi: float | None = None


class PresentationBase(BaseModel):
    chief_complaint: str = Field(..., min_length=1)
    chief_complaint_i18n: LocaleMap = Field(default_factory=dict)
    history_of_present_illness: str = ""
    past_medical_history: list[str] = Field(default_factory=list)
    medications: list[dict[str, Any]] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    family_history: list[str] = Field(default_factory=list)
    social_history: str = ""
    review_of_systems: dict[str, Any] = Field(default_factory=dict)
    vitals: dict[str, Any] = Field(default_factory=dict)
    examination_findings: list[str] = Field(default_factory=list)

    @field_validator("chief_complaint_i18n")
    @classmethod
    def _locales(cls, v: LocaleMap) -> LocaleMap:
        return _validate_locale_keys(v)


class PresentationRead(PresentationBase, ORMModel):
    id: int


class LabResultBase(BaseModel):
    analyte_code: str = Field(..., min_length=1, max_length=64)
    analyte_name: str = Field(..., min_length=1, max_length=128)
    loinc_code: str | None = None
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None
    ref_low: float | None = None
    ref_high: float | None = None
    ref_text: str | None = None
    flag: ResultFlag = ResultFlag.NORMAL
    method: str | None = None
    interference_note: str | None = None
    is_critical: bool = False

    @model_validator(mode="after")
    def _needs_a_value(self) -> "LabResultBase":
        if self.value_numeric is None and not self.value_text:
            raise ValueError("a lab result needs either value_numeric or value_text")
        if (
            self.ref_low is not None
            and self.ref_high is not None
            and self.ref_low > self.ref_high
        ):
            raise ValueError("ref_low must not exceed ref_high")
        return self


class LabResultRead(LabResultBase, ORMModel):
    id: int


class LabPanelBase(BaseModel):
    panel_code: str = Field(..., min_length=1, max_length=64)
    panel_name: str = Field(..., min_length=1, max_length=128)
    collected_at: datetime
    day_offset: int = 0
    specimen: str = "serum"
    laboratory: str = "Central Laboratory"
    analyser: str | None = None
    comment: str = ""


class LabPanelCreate(LabPanelBase):
    results: list[LabResultBase] = Field(default_factory=list)


class LabPanelRead(LabPanelBase, ORMModel):
    id: int
    results: list[LabResultRead] = Field(default_factory=list)


class PeripheralSmearBase(BaseModel):
    collected_at: datetime
    day_offset: int = 0
    stain: str = "May-Grunwald-Giemsa"
    red_cell_morphology: list[str] = Field(default_factory=list)
    white_cell_morphology: list[str] = Field(default_factory=list)
    platelet_morphology: list[str] = Field(default_factory=list)
    narrative: str = ""
    narrative_i18n: LocaleMap = Field(default_factory=dict)
    schistocyte_percent: float | None = Field(default=None, ge=0, le=100)
    reported_by: str | None = None

    @field_validator("narrative_i18n")
    @classmethod
    def _locales(cls, v: LocaleMap) -> LocaleMap:
        return _validate_locale_keys(v)


class PeripheralSmearRead(PeripheralSmearBase, ORMModel):
    id: int


class MicrobiologyReportBase(BaseModel):
    collected_at: datetime
    day_offset: int = 0
    specimen_type: str
    site: str | None = None
    organism: str | None = None
    microscopy: str = ""
    bacterial_index: float | None = Field(default=None, ge=0, le=6)
    morphological_index: float | None = Field(default=None, ge=0, le=100)
    molecular_findings: list[dict[str, Any]] = Field(default_factory=list)
    susceptibility: list[dict[str, Any]] = Field(default_factory=list)
    interpretation: str = ""


class MicrobiologyReportRead(MicrobiologyReportBase, ORMModel):
    id: int


class TreatmentProtocolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    name_i18n: LocaleMap = Field(default_factory=dict)
    guideline_source: str | None = None
    indication: str = ""
    duration_months: int | None = Field(default=None, ge=0, le=360)
    regimen: list[dict[str, Any]] = Field(default_factory=list)
    monitoring: list[str] = Field(default_factory=list)
    contraindications: list[str] = Field(default_factory=list)
    adverse_effects: list[str] = Field(default_factory=list)
    notes: str = ""

    @field_validator("name_i18n")
    @classmethod
    def _locales(cls, v: LocaleMap) -> LocaleMap:
        return _validate_locale_keys(v)


class TreatmentProtocolRead(TreatmentProtocolBase, ORMModel):
    id: int


class DiagnosisBase(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    label_i18n: LocaleMap = Field(default_factory=dict)
    is_primary: bool = False
    certainty: Certainty = Certainty.PROBABLE
    likelihood: float | None = Field(default=None, ge=0, le=1)
    icd10: str | None = None
    discriminator: str = ""
    supporting_evidence: list[str] = Field(default_factory=list)
    refuting_evidence: list[str] = Field(default_factory=list)

    @field_validator("label_i18n")
    @classmethod
    def _locales(cls, v: LocaleMap) -> LocaleMap:
        return _validate_locale_keys(v)


class DiagnosisRead(DiagnosisBase, ORMModel):
    id: int


class ImagingStudyBase(BaseModel):
    modality: str
    region: str
    day_offset: int = 0
    findings: str = ""
    impression: str = ""


class ImagingStudyRead(ImagingStudyBase, ORMModel):
    id: int


# ---------------------------------------------------------------------------
# Case aggregate
# ---------------------------------------------------------------------------


class CaseBase(BaseModel):
    case_code: str = Field(..., pattern=r"^[A-Z]{3}-\d{3}$")
    title: str = Field(..., min_length=3, max_length=255)
    title_i18n: LocaleMap = Field(default_factory=dict)
    summary: str = ""
    summary_i18n: LocaleMap = Field(default_factory=dict)
    discipline: Discipline
    subspecialty: str = Field(..., min_length=2, max_length=64)
    status: CaseStatus = CaseStatus.PUBLISHED
    difficulty: int = Field(default=3, ge=1, le=5)
    version: str = "1.0.0"
    tags: list[str] = Field(default_factory=list)
    icd10_codes: list[str] = Field(default_factory=list)
    snomed_codes: list[str] = Field(default_factory=list)
    teaching_points: list[str] = Field(default_factory=list)
    references: list[dict[str, Any]] = Field(default_factory=list)
    reasoning_key: dict[str, Any] = Field(default_factory=dict)
    author: str = "MedSimQA Editorial"
    reviewed_by: str | None = None

    @field_validator("title_i18n", "summary_i18n")
    @classmethod
    def _locales(cls, v: LocaleMap) -> LocaleMap:
        return _validate_locale_keys(v)


class CaseCreate(CaseBase):
    patient: PatientBase
    presentation: PresentationBase
    lab_panels: list[LabPanelCreate] = Field(default_factory=list)
    smears: list[PeripheralSmearBase] = Field(default_factory=list)
    microbiology: list[MicrobiologyReportBase] = Field(default_factory=list)
    protocols: list[TreatmentProtocolBase] = Field(default_factory=list)
    diagnoses: list[DiagnosisBase] = Field(default_factory=list)
    imaging: list[ImagingStudyBase] = Field(default_factory=list)

    @model_validator(mode="after")
    def _at_most_one_primary_diagnosis(self) -> "CaseCreate":
        primaries = [d for d in self.diagnoses if d.is_primary]
        if len(primaries) > 1:
            raise ValueError("a case may declare at most one primary diagnosis")
        return self


class CaseUpdate(BaseModel):
    """PATCH payload. Every field optional; nested collections, when supplied,
    replace the existing collection wholesale (documented in the ADR as
    'replace-not-merge')."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=255)
    title_i18n: LocaleMap | None = None
    summary: str | None = None
    summary_i18n: LocaleMap | None = None
    discipline: Discipline | None = None
    subspecialty: str | None = None
    status: CaseStatus | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    version: str | None = None
    tags: list[str] | None = None
    icd10_codes: list[str] | None = None
    snomed_codes: list[str] | None = None
    teaching_points: list[str] | None = None
    references: list[dict[str, Any]] | None = None
    reasoning_key: dict[str, Any] | None = None
    author: str | None = None
    reviewed_by: str | None = None
    patient: PatientBase | None = None
    presentation: PresentationBase | None = None
    lab_panels: list[LabPanelCreate] | None = None
    smears: list[PeripheralSmearBase] | None = None
    microbiology: list[MicrobiologyReportBase] | None = None
    protocols: list[TreatmentProtocolBase] | None = None
    diagnoses: list[DiagnosisBase] | None = None
    imaging: list[ImagingStudyBase] | None = None

    @field_validator("title_i18n", "summary_i18n")
    @classmethod
    def _locales(cls, v: LocaleMap | None) -> LocaleMap | None:
        return None if v is None else _validate_locale_keys(v)


class CaseSummaryRead(ORMModel):
    """Light projection used by the case list. Deliberately excludes the lab
    timeline: a 25-case list with full timelines is ~1.4 MB, which is the
    difference between a 90 ms and a 2 s dashboard load on 3G."""

    id: int
    case_code: str
    title: str
    title_i18n: LocaleMap = Field(default_factory=dict)
    summary: str = ""
    summary_i18n: LocaleMap = Field(default_factory=dict)
    discipline: Discipline
    subspecialty: str
    status: CaseStatus
    difficulty: int
    version: str
    tags: list[str] = Field(default_factory=list)
    updated_at: datetime
    patient: PatientRead | None = None


class CaseRead(CaseBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime
    patient: PatientRead | None = None
    presentation: PresentationRead | None = None
    lab_panels: list[LabPanelRead] = Field(default_factory=list)
    smears: list[PeripheralSmearRead] = Field(default_factory=list)
    microbiology: list[MicrobiologyReportRead] = Field(default_factory=list)
    protocols: list[TreatmentProtocolRead] = Field(default_factory=list)
    diagnoses: list[DiagnosisRead] = Field(default_factory=list)
    imaging: list[ImagingStudyRead] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Reference intervals, trends, collections, errors
# ---------------------------------------------------------------------------


class ReferenceIntervalRead(ORMModel):
    id: int
    analyte_code: str
    analyte_name: str
    analyte_name_i18n: LocaleMap = Field(default_factory=dict)
    loinc_code: str | None = None
    unit: str
    si_unit: str | None = None
    si_conversion_factor: float | None = None
    population: str
    ref_low: float | None = None
    ref_high: float | None = None
    critical_low: float | None = None
    critical_high: float | None = None
    decimals: int
    category: str
    notes: str = ""


class TrendPoint(BaseModel):
    collected_at: datetime
    day_offset: int
    value: float
    unit: str | None = None
    flag: ResultFlag
    panel_code: str
    is_critical: bool = False


class AnalyteTrend(BaseModel):
    analyte_code: str
    analyte_name: str
    unit: str | None = None
    ref_low: float | None = None
    ref_high: float | None = None
    critical_low: float | None = None
    critical_high: float | None = None
    decimals: int = 2
    points: list[TrendPoint] = Field(default_factory=list)

    @property
    def delta(self) -> float | None:
        if len(self.points) < 2:
            return None
        return self.points[-1].value - self.points[0].value


class CaseTrendsRead(BaseModel):
    case_id: int
    case_code: str
    series: list[AnalyteTrend] = Field(default_factory=list)


class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int
    returned: int
    has_more: bool


class CaseListResponse(BaseModel):
    meta: PageMeta
    items: list[CaseSummaryRead]


class StatsResponse(BaseModel):
    total_cases: int
    by_discipline: dict[str, int]
    by_subspecialty: dict[str, int]
    by_difficulty: dict[str, int]
    by_status: dict[str, int]
    total_lab_results: int
    total_panels: int
    generated_at: datetime


class ErrorDetail(BaseModel):
    """RFC-7807-flavoured error body. Every non-2xx response uses this shape so
    the frontend has exactly one error branch to render."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str = ""
    instance: str | None = None
    errors: list[dict[str, Any]] = Field(default_factory=list)
    request_id: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"]
    version: str
    environment: str
    database: str
    case_count: int
    uptime_seconds: float
    checks: dict[str, str] = Field(default_factory=dict)


SortField = Annotated[
    Literal["case_code", "title", "difficulty", "updated_at", "created_at", "discipline"],
    Field(description="Field to sort the case list by"),
]
