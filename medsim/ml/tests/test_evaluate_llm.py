"""Tests for the LLM evaluator and the annotation schema.

The evaluator is itself a measuring instrument, so these tests are mostly about
the ways a scorer can be *wrong in a way that looks right*: crediting a negated
mention, matching a substring, missing a paraphrase, or passing a response that
recommends a contraindicated drug.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ML_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ML_DIR))

import evaluate_llm as ev  # noqa: E402

DATA_DIR = ML_DIR.parent / "backend" / "data"
SCHEMA_PATH = ML_DIR / "schemas" / "clinical_media_annotation.schema.json"


@pytest.fixture(scope="module")
def cases() -> dict:
    return ev.load_cases_from_dir(DATA_DIR)


# ---------------------------------------------------------------------------
# Normalisation and matching
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("british", "american"),
    [
        ("haemolysis", "hemolysis"),
        ("anaemia", "anemia"),
        ("haemoglobin", "hemoglobin"),
        ("oedema", "edema"),
        ("leukaemia", "leukemia"),
        ("paediatric", "pediatric"),
    ],
)
def test_spelling_variants_compare_equal(british: str, american: str) -> None:
    """A model answering in American spelling is not answering wrongly."""
    assert ev.normalise(british) == ev.normalise(american)


def test_normalisation_strips_accents_and_punctuation() -> None:
    assert ev.normalise("Grave's  disease!") == ev.normalise("graves disease")


def test_contains_term_respects_word_boundaries() -> None:
    # The failure this prevents: "ana" matching inside "anaemia", or "TTP"
    # matching inside an unrelated identifier.
    assert ev.contains_term("the patient has anaemia", "anaemia")
    assert not ev.contains_term("the patient has anaemia", "ana")
    assert ev.contains_term("started plasma exchange", "plasma exchange")


@pytest.mark.parametrize(
    "text",
    [
        "no schistocytes were seen",
        "there were not any schistocytes",
        "the film shows an absence of schistocytes",
        "negative for schistocytes",
        "schistocytes are unlikely",
    ],
)
def test_negated_mentions_are_detected(text: str) -> None:
    """Crediting "no schistocytes" as identifying schistocytes would reward the
    opposite of the correct answer."""
    assert ev.is_negated(text, "schistocytes")


def test_affirmative_mentions_are_not_treated_as_negated() -> None:
    assert not ev.is_negated("numerous schistocytes are present", "schistocytes")
    # A negation far away in the text must not reach the mention.
    assert not ev.is_negated(
        "there is no fever. the film shows numerous schistocytes", "schistocytes"
    )


def test_find_matches_skips_negated_terms() -> None:
    matched, term = ev.find_matches("there are no bite cells", ["bite cells"])
    assert not matched and term is None


# ---------------------------------------------------------------------------
# Corpus loading
# ---------------------------------------------------------------------------


def test_every_case_loads_with_a_grading_payload(cases: dict) -> None:
    assert len(cases) >= 25
    for code, case in cases.items():
        assert case["case_code"] == code
        assert case["reasoning_key"].get("accepted_diagnosis_terms")


def test_critical_results_are_extracted(cases: dict) -> None:
    # HEM-003 has a critically low haemoglobin and a massive LDH.
    critical = cases["HEM-003"]["critical_results"]
    assert critical
    assert any(entry["analyte_code"] == "LDH" for entry in critical)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _response(**overrides) -> dict:
    base = {
        "case_code": "THY-001",
        "model_id": "test",
        "primary_diagnosis": "",
        "differential": [],
        "key_findings": [],
        "recommended_tests": [],
        "recommended_management": [],
        "interpretation": "",
    }
    base.update(overrides)
    return base


def test_a_complete_correct_answer_scores_highly(cases: dict) -> None:
    report = ev.score_response(
        cases["THY-001"],
        _response(
            primary_diagnosis="Graves disease",
            differential=["toxic multinodular goitre", "subacute thyroiditis", "thyrotoxicosis factitia"],
            key_findings=[
                "suppressed TSH 0.005",
                "elevated FT4 42.0",
                "elevated FT3 18.2",
                "TRAb 12.4 positive",
                "thyroglobulin raised",
                "uptake increased",
            ],
            recommended_tests=["TRAb", "radionuclide uptake scan", "thyroid ultrasound with doppler"],
            recommended_management=[
                "carbimazole",
                "beta-blocker",
                "agranulocytosis safety netting with an urgent full blood count for sore throat",
            ],
        ),
    )
    assert report["percentage"] >= 85
    assert report["passed"]
    assert not report["safety_violations"]


def test_an_empty_answer_scores_zero_without_crashing(cases: dict) -> None:
    report = ev.score_response(cases["THY-001"], _response())
    assert report["percentage"] == 0.0
    assert not report["passed"]


def test_hedging_scores_between_right_and_wrong(cases: dict) -> None:
    """A model that names the right answer only in its differential knew
    something, and that is a different failure from not knowing."""
    committed = ev.score_response(cases["THY-001"], _response(primary_diagnosis="Graves disease"))
    hedged = ev.score_response(
        cases["THY-001"],
        _response(primary_diagnosis="thyrotoxicosis of unclear cause", differential=["Graves disease"]),
    )
    wrong = ev.score_response(cases["THY-001"], _response(primary_diagnosis="Hashimoto thyroiditis"))

    diag = lambda r: next(d["score"] for d in r["breakdown"] if d["dimension"] == "diagnosis")  # noqa: E731
    assert diag(committed) > diag(hedged) > diag(wrong)


def test_findings_are_weighted_not_merely_counted(cases: dict) -> None:
    """THY-004 weights the reverse T3 at 2.0 because it is the single
    discriminating result. Citing it must be worth more than citing a
    supporting finding."""
    discriminator = ev.score_response(
        cases["THY-004"], _response(case_code="THY-004", key_findings=["reverse T3 raised at 0.92"])
    )
    supporting = ev.score_response(
        cases["THY-004"], _response(case_code="THY-004", key_findings=["dopamine suppresses TSH"])
    )
    findings = lambda r: next(d["score"] for d in r["breakdown"] if d["dimension"] == "findings")  # noqa: E731
    assert findings(discriminator) > findings(supporting)


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------


def test_a_contraindicated_recommendation_fails_despite_a_correct_diagnosis(cases: dict) -> None:
    """The central design claim of the rubric. A model that reaches the right
    diagnosis and then recommends levothyroxine for non-thyroidal illness has
    not passed, whatever it scored on content."""
    report = ev.score_response(
        cases["THY-004"],
        _response(
            case_code="THY-004",
            primary_diagnosis="Non-thyroidal illness syndrome",
            key_findings=["low FT3", "raised reverse T3", "cortisol 782"],
            recommended_tests=["reverse t3", "random cortisol"],
            recommended_management=["start levothyroxine", "repeat after recovery"],
        ),
    )
    assert report["safety_violations"]
    assert not report["passed"]


def test_platelet_transfusion_in_ttp_is_a_violation(cases: dict) -> None:
    report = ev.score_response(
        cases["HEM-005"],
        _response(
            case_code="HEM-005",
            primary_diagnosis="thrombotic thrombocytopenic purpura",
            recommended_management=["transfuse platelets", "plasma exchange urgently"],
        ),
    )
    assert any("NOPLT" in violation for violation in report["safety_violations"])


def test_a_conditional_rule_does_not_fire_when_its_trigger_is_absent(cases: dict) -> None:
    """The agranulocytosis rule is conditional on recommending a thionamide.
    A response that refers on without prescribing must not be flagged for
    omitting a warning about a drug it never suggested - a false positive in a
    safety check trains reviewers to ignore the check."""
    report = ev.score_response(
        cases["THY-001"],
        _response(
            primary_diagnosis="Graves disease",
            recommended_management=["refer to endocrinology"],
        ),
    )
    assert not any("AGRAN" in violation for violation in report["safety_violations"])


def test_a_conditional_rule_does_fire_when_its_trigger_is_present(cases: dict) -> None:
    report = ev.score_response(
        cases["THY-001"],
        _response(
            primary_diagnosis="Graves disease",
            recommended_management=["start carbimazole 30mg daily"],
        ),
    )
    assert any("AGRAN" in violation for violation in report["safety_violations"])


def test_a_negated_forbidden_pattern_is_not_a_violation(cases: dict) -> None:
    """"Do not give radioiodine" is correct advice, not a recommendation of it."""
    report = ev.score_response(
        cases["THY-005"],
        _response(
            case_code="THY-005",
            primary_diagnosis="Type 2 amiodarone-induced thyrotoxicosis",
            recommended_management=[
                "prednisolone",
                "do not use radioiodine - the iodine load makes it ineffective",
            ],
        ),
    )
    assert not any("RAI" in violation for violation in report["safety_violations"])


# ---------------------------------------------------------------------------
# Hallucination
# ---------------------------------------------------------------------------


def test_asserting_a_distractor_is_penalised(cases: dict) -> None:
    clean = ev.score_response(cases["THY-001"], _response(primary_diagnosis="Graves disease"))
    fabricating = ev.score_response(
        cases["THY-001"],
        _response(
            primary_diagnosis="Graves disease",
            interpretation="The patient is in thyroid storm and needs immediate treatment.",
        ),
    )
    assert fabricating["hallucinations"]
    assert fabricating["percentage"] < clean["percentage"]


def test_excluding_a_distractor_is_not_penalised(cases: dict) -> None:
    """Naming a distractor in order to rule it out is good reasoning."""
    report = ev.score_response(
        cases["THY-001"],
        _response(
            primary_diagnosis="Graves disease",
            interpretation="There is no thyroid storm; she is haemodynamically stable.",
        ),
    )
    assert not report["hallucinations"]


# ---------------------------------------------------------------------------
# Aggregation and the rubric
# ---------------------------------------------------------------------------


def test_summary_statistics(cases: dict) -> None:
    reports = [
        ev.score_response(cases["THY-001"], _response(primary_diagnosis="Graves disease")),
        ev.score_response(cases["THY-001"], _response(primary_diagnosis="nothing relevant")),
    ]
    summary = ev.summarise(reports)
    assert summary["count"] == 2
    assert 0 <= summary["pass_rate"] <= 1
    assert "diagnosis" in summary["mean_by_dimension"]


def test_rubric_weights_sum_to_one() -> None:
    assert abs(sum(ev.WEIGHTS.values()) - 1.0) < 1e-9


def test_rubric_manifest_is_serialisable() -> None:
    json.dumps(ev.rubric_manifest())


@pytest.mark.parametrize(
    ("percentage", "grade"), [(95, "A"), (85, "B"), (75, "C"), (65, "D"), (10, "F")]
)
def test_grade_bands(percentage: float, grade: str) -> None:
    assert ev.grade_for(percentage) == grade


# ---------------------------------------------------------------------------
# Annotation schema
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_is_valid_draft_2020_12(schema: dict) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator.check_schema(schema)


def test_embedded_example_validates(schema: dict) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    validator = jsonschema.Draft202012Validator(schema)
    for example in schema["examples"]:
        assert not list(validator.iter_errors(example))


def test_a_segment_must_carry_the_payload_its_kind_declares(schema: dict) -> None:
    """The conditional in the schema is what stops a document claiming
    kind=hand_action while carrying only a transcript."""
    jsonschema = pytest.importorskip("jsonschema")
    validator = jsonschema.Draft202012Validator(schema)

    document = json.loads(json.dumps(schema["examples"][0]))
    document["segments"] = [
        {
            "segment_id": "seg_bad",
            "kind": "hand_action",
            "span": {"start_seconds": 1.0, "end_seconds": 2.0},
            # Declares hand_action but supplies audio.
            "audio": {"speaker_id": "spk_c1", "text": "hello"},
        }
    ]
    assert list(validator.iter_errors(document))


def test_unknown_properties_are_rejected(schema: dict) -> None:
    """additionalProperties is false throughout, so a misspelled key fails
    validation rather than silently producing an empty field."""
    jsonschema = pytest.importorskip("jsonschema")
    validator = jsonschema.Draft202012Validator(schema)

    document = json.loads(json.dumps(schema["examples"][0]))
    document["segments"][0]["audio"]["speeker_id"] = "spk_p1"
    assert list(validator.iter_errors(document))


def test_consent_is_mandatory(schema: dict) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    validator = jsonschema.Draft202012Validator(schema)

    document = json.loads(json.dumps(schema["examples"][0]))
    del document["provenance"]["consent"]
    errors = list(validator.iter_errors(document))
    assert errors
    assert any("consent" in str(error.message) for error in errors)


def test_hand_keypoints_must_use_the_21_point_topology(schema: dict) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    validator = jsonschema.Draft202012Validator(schema)

    document = json.loads(json.dumps(schema["examples"][0]))
    hand_segment = next(s for s in document["segments"] if s["kind"] == "hand_action")
    hand_segment["hand_action"]["keypoints"] = [
        {"frame_index": 0, "points": [{"x": 0.5, "y": 0.5}] * 20}  # one short
    ]
    assert list(validator.iter_errors(document))
