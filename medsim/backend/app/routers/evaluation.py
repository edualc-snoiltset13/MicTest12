"""Endpoints that expose the Phase 4 grading machinery over HTTP.

The scoring logic itself lives in ``ml/evaluate_llm.py`` so that it can be run
offline over a JSONL corpus of thousands of model outputs without a server. This
router imports that module and wraps it, keeping exactly one implementation of
the rubric.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from .. import crud
from ..database import get_db

# ml/ is a sibling of backend/ in the repository layout.
_ML_DIR = Path(__file__).resolve().parents[3] / "ml"
if str(_ML_DIR) not in sys.path:
    sys.path.insert(0, str(_ML_DIR))

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

DbSession = Annotated[Session, Depends(get_db)]


class LLMSubmission(BaseModel):
    """A single model response to be graded against a case."""

    # ``model_id`` collides with Pydantic's protected ``model_`` namespace; the
    # field name is part of the published API contract, so we disable the guard
    # rather than rename it.
    model_config = ConfigDict(protected_namespaces=())

    case_code: str = Field(..., pattern=r"^[A-Z]{3}-\d{3}$")
    model_id: str = Field(default="unknown-model", max_length=128)
    primary_diagnosis: str = Field(default="", max_length=512)
    differential: list[str] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    interpretation: str = Field(default="", max_length=8000)
    recommended_tests: list[str] = Field(default_factory=list)
    recommended_management: list[str] = Field(default_factory=list)
    flagged_critical_values: list[str] = Field(default_factory=list)
    raw_response: str | None = None


class ScoreBreakdown(BaseModel):
    dimension: str
    score: float
    max_score: float
    weight: float
    matched: list[str] = Field(default_factory=list)
    missed: list[str] = Field(default_factory=list)
    notes: str = ""


class EvaluationResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    case_code: str
    model_id: str
    total_score: float
    max_score: float
    percentage: float
    grade: str
    passed: bool
    breakdown: list[ScoreBreakdown]
    safety_violations: list[str] = Field(default_factory=list)
    hallucinations: list[str] = Field(default_factory=list)


def _load_scorer() -> Any:
    try:
        import evaluate_llm  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - misconfigured deployment
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Evaluation module unavailable; ml/evaluate_llm.py is not importable.",
        ) from exc
    return evaluate_llm


@router.get("/rubric", summary="The scoring rubric and its weights")
def get_rubric() -> dict[str, Any]:
    scorer = _load_scorer()
    return scorer.rubric_manifest()


@router.post(
    "/score",
    response_model=EvaluationResult,
    summary="Score one LLM response against a case's reasoning key",
)
def score_submission(submission: LLMSubmission, db: DbSession) -> EvaluationResult:
    try:
        case = crud.get_case_by_code(db, submission.case_code)
    except crud.CaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No case matching {submission.case_code!r}.",
        ) from exc

    scorer = _load_scorer()
    case_payload = scorer.case_to_grading_payload(
        case_code=case.case_code,
        reasoning_key=case.reasoning_key,
        diagnoses=[
            {
                "label": d.label,
                "is_primary": d.is_primary,
                "likelihood": d.likelihood,
                "discriminator": d.discriminator,
            }
            for d in case.diagnoses
        ],
        lab_panels=[
            {
                "panel_code": p.panel_code,
                "day_offset": p.day_offset,
                "results": [
                    {
                        "analyte_code": r.analyte_code,
                        "analyte_name": r.analyte_name,
                        "value_numeric": r.value_numeric,
                        "value_text": r.value_text,
                        "unit": r.unit,
                        "flag": r.flag.value,
                        "is_critical": r.is_critical,
                    }
                    for r in p.results
                ],
            }
            for p in case.lab_panels
        ],
    )
    report = scorer.score_response(case_payload, submission.model_dump())
    return EvaluationResult(**report)


@router.post(
    "/score/batch",
    response_model=list[EvaluationResult],
    summary="Score a batch of LLM responses",
)
def score_batch(submissions: list[LLMSubmission], db: DbSession) -> list[EvaluationResult]:
    if len(submissions) > 500:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Batch limit is 500 submissions; use the offline runner for larger corpora.",
        )
    return [score_submission(submission, db) for submission in submissions]


@router.get("/annotation-schema", summary="JSON Schema for video/audio annotation")
def annotation_schema() -> dict[str, Any]:
    schema_path = _ML_DIR / "schemas" / "clinical_media_annotation.schema.json"
    if not schema_path.exists():  # pragma: no cover - packaging error
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Annotation schema file is missing from the deployment.",
        )
    import json

    return json.loads(schema_path.read_text(encoding="utf-8"))
