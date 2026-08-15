"""ORM models for the MedSimQA case repository.

Design notes
------------
* A ``Case`` is the aggregate root. Everything else cascades from it, so a
  DELETE of a case is a single statement and leaves no orphans.
* Clinical free text that must be shown to the clinician in five languages is
  stored as a JSON map ``{"en": "...", "de": "..."}`` rather than as separate
  rows. Translations are versioned with the case, not independently, which
  keeps a case's German text from silently describing a different revision of
  the English text.
* Numeric lab results are stored as floats with the reference interval that was
  in force *at the time of collection*. Reference intervals drift between
  analysers and populations; recomputing a flag from today's interval would
  silently rewrite history.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Discipline(str, enum.Enum):
    CHEMICAL_PATHOLOGY = "chemical_pathology"
    MICROBIOLOGY = "microbiology"
    HEMATOLOGY = "hematology"
    PHARMACOLOGY = "pharmacology"


class Sex(str, enum.Enum):
    FEMALE = "female"
    MALE = "male"
    INTERSEX = "intersex"
    UNSPECIFIED = "unspecified"


class ResultFlag(str, enum.Enum):
    NORMAL = "N"
    HIGH = "H"
    LOW = "L"
    CRITICAL_HIGH = "HH"
    CRITICAL_LOW = "LL"
    ABNORMAL = "A"  # qualitative abnormal (e.g. positive autoantibody)


class CaseStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    RETIRED = "retired"


class Certainty(str, enum.Enum):
    CONFIRMED = "confirmed"
    PROBABLE = "probable"
    POSSIBLE = "possible"
    EXCLUDED = "excluded"


# ---------------------------------------------------------------------------
# Aggregate root
# ---------------------------------------------------------------------------


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (
        UniqueConstraint("case_code", name="uq_cases_case_code"),
        CheckConstraint("difficulty BETWEEN 1 AND 5", name="ck_cases_difficulty_range"),
        Index("ix_cases_discipline_status", "discipline", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    title_i18n: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    summary_i18n: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    discipline: Mapped[Discipline] = mapped_column(Enum(Discipline), nullable=False, index=True)
    subspecialty: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus), default=CaseStatus.PUBLISHED, nullable=False
    )
    difficulty: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    version: Mapped[str] = mapped_column(String(16), default="1.0.0", nullable=False)

    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    icd10_codes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    snomed_codes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    teaching_points: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    references: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Denormalised grading key consumed by the Phase 4 evaluator.
    reasoning_key: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    author: Mapped[str] = mapped_column(String(128), default="MedSimQA Editorial", nullable=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    patient: Mapped["Patient"] = relationship(
        back_populates="case", cascade="all, delete-orphan", uselist=False, lazy="joined"
    )
    presentation: Mapped["Presentation"] = relationship(
        back_populates="case", cascade="all, delete-orphan", uselist=False, lazy="joined"
    )
    lab_panels: Mapped[list["LabPanel"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="LabPanel.collected_at",
        lazy="selectin",
    )
    smears: Mapped[list["PeripheralSmear"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )
    microbiology: Mapped[list["MicrobiologyReport"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )
    protocols: Mapped[list["TreatmentProtocol"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )
    diagnoses: Mapped[list["Diagnosis"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )
    imaging: Mapped[list["ImagingStudy"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Case {self.case_code} {self.title!r}>"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    pseudonym: Mapped[str] = mapped_column(String(64), nullable=False)
    age_years: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[Sex] = mapped_column(Enum(Sex), nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    ancestry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pregnancy_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(128), nullable=True)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)

    case: Mapped[Case] = relationship(back_populates="patient")

    @property
    def bmi(self) -> float | None:
        if not self.weight_kg or not self.height_cm:
            return None
        metres = self.height_cm / 100.0
        return round(self.weight_kg / (metres * metres), 1)


class Presentation(Base):
    __tablename__ = "presentations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    chief_complaint: Mapped[str] = mapped_column(Text, nullable=False)
    chief_complaint_i18n: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    history_of_present_illness: Mapped[str] = mapped_column(Text, default="", nullable=False)
    past_medical_history: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    medications: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    allergies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    family_history: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    social_history: Mapped[str] = mapped_column(Text, default="", nullable=False)
    review_of_systems: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    vitals: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    examination_findings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    case: Mapped[Case] = relationship(back_populates="presentation")


class LabPanel(Base):
    __tablename__ = "lab_panels"
    __table_args__ = (Index("ix_lab_panels_case_collected", "case_id", "collected_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    panel_code: Mapped[str] = mapped_column(String(64), nullable=False)
    panel_name: Mapped[str] = mapped_column(String(128), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    day_offset: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    specimen: Mapped[str] = mapped_column(String(64), default="serum", nullable=False)
    laboratory: Mapped[str] = mapped_column(String(128), default="Central Laboratory", nullable=False)
    analyser: Mapped[str | None] = mapped_column(String(128), nullable=True)
    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)

    case: Mapped[Case] = relationship(back_populates="lab_panels")
    results: Mapped[list["LabResult"]] = relationship(
        back_populates="panel", cascade="all, delete-orphan", lazy="selectin"
    )


class LabResult(Base):
    __tablename__ = "lab_results"
    __table_args__ = (Index("ix_lab_results_analyte", "analyte_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    panel_id: Mapped[int] = mapped_column(
        ForeignKey("lab_panels.id", ondelete="CASCADE"), nullable=False
    )
    analyte_code: Mapped[str] = mapped_column(String(64), nullable=False)
    analyte_name: Mapped[str] = mapped_column(String(128), nullable=False)
    loinc_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ref_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    ref_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    ref_text: Mapped[str | None] = mapped_column(String(128), nullable=True)
    flag: Mapped[ResultFlag] = mapped_column(Enum(ResultFlag), default=ResultFlag.NORMAL, nullable=False)
    method: Mapped[str | None] = mapped_column(String(128), nullable=True)
    interference_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    panel: Mapped[LabPanel] = relationship(back_populates="results")


class PeripheralSmear(Base):
    """Morphology report. Central to the haemolysis cases: the smear is usually
    what separates immune from non-immune destruction before any antibody
    testing returns."""

    __tablename__ = "peripheral_smears"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    day_offset: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stain: Mapped[str] = mapped_column(String(64), default="May-Grunwald-Giemsa", nullable=False)
    red_cell_morphology: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    white_cell_morphology: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    platelet_morphology: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    narrative: Mapped[str] = mapped_column(Text, default="", nullable=False)
    narrative_i18n: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    schistocyte_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    reported_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    case: Mapped[Case] = relationship(back_populates="smears")


class MicrobiologyReport(Base):
    __tablename__ = "microbiology_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    day_offset: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    specimen_type: Mapped[str] = mapped_column(String(128), nullable=False)
    site: Mapped[str | None] = mapped_column(String(128), nullable=True)
    organism: Mapped[str | None] = mapped_column(String(128), nullable=True)
    microscopy: Mapped[str] = mapped_column(Text, default="", nullable=False)
    bacterial_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    morphological_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    molecular_findings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    susceptibility: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    interpretation: Mapped[str] = mapped_column(Text, default="", nullable=False)

    case: Mapped[Case] = relationship(back_populates="microbiology")


class TreatmentProtocol(Base):
    __tablename__ = "treatment_protocols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    name_i18n: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    guideline_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    indication: Mapped[str] = mapped_column(Text, default="", nullable=False)
    duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    regimen: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    monitoring: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    contraindications: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    adverse_effects: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    case: Mapped[Case] = relationship(back_populates="protocols")


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    label_i18n: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    certainty: Mapped[Certainty] = mapped_column(
        Enum(Certainty), default=Certainty.PROBABLE, nullable=False
    )
    likelihood: Mapped[float | None] = mapped_column(Float, nullable=True)
    icd10: Mapped[str | None] = mapped_column(String(16), nullable=True)
    discriminator: Mapped[str] = mapped_column(Text, default="", nullable=False)
    supporting_evidence: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    refuting_evidence: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    case: Mapped[Case] = relationship(back_populates="diagnoses")


class ImagingStudy(Base):
    __tablename__ = "imaging_studies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    modality: Mapped[str] = mapped_column(String(64), nullable=False)
    region: Mapped[str] = mapped_column(String(128), nullable=False)
    day_offset: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    findings: Mapped[str] = mapped_column(Text, default="", nullable=False)
    impression: Mapped[str] = mapped_column(Text, default="", nullable=False)

    case: Mapped[Case] = relationship(back_populates="imaging")


class ReferenceInterval(Base):
    """Analyte metadata + population reference intervals, used by the frontend
    charts to draw shaded normal bands and by the evaluator to bucket values."""

    __tablename__ = "reference_intervals"
    __table_args__ = (
        UniqueConstraint("analyte_code", "population", name="uq_refint_analyte_population"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analyte_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    analyte_name: Mapped[str] = mapped_column(String(128), nullable=False)
    analyte_name_i18n: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    loinc_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    si_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    si_conversion_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    population: Mapped[str] = mapped_column(String(64), default="adult", nullable=False)
    ref_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    ref_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    critical_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    critical_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    decimals: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="general", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class AuditEvent(Base):
    """Append-only audit trail. Every mutating API call writes one row."""

    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_entity", "entity_type", "entity_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
    actor: Mapped[str] = mapped_column(String(128), default="anonymous", nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
