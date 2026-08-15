"""Content tests over the seeded corpus.

These assert clinical and editorial invariants rather than API behaviour. They
exist because the expensive failure mode for a training corpus is not a 500 -
it is a case that is quietly internally inconsistent, or a grading key that no
correct answer could satisfy.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.schemas import SUPPORTED_LOCALES

API = "/api/v1"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

REQUIRED_SUBSPECIALTY_COVERAGE = {
    "thyroid": 9,
    "haemolytic_anaemia": 9,
    "mycobacteriology": 4,
    "antimicrobial_chemotherapy": 3,
}


@pytest.fixture(scope="module")
def all_cases(client) -> list[dict]:
    return client.get(f"{API}/cases/export").json()


# ---------------------------------------------------------------------------
# Coverage of the commissioned subject matter
# ---------------------------------------------------------------------------


def test_corpus_has_at_least_twenty_five_cases(all_cases):
    assert len(all_cases) >= 25


def test_required_subspecialties_are_covered(all_cases):
    counts: dict[str, int] = {}
    for case in all_cases:
        counts[case["subspecialty"]] = counts.get(case["subspecialty"], 0) + 1
    for subspecialty, expected in REQUIRED_SUBSPECIALTY_COVERAGE.items():
        assert counts.get(subspecialty, 0) >= expected, f"{subspecialty} under-represented"


def test_thyroid_cases_cover_the_full_analyte_set(all_cases):
    """The brief requires nuanced TSH, T3, T4 and autoantibody values."""
    thyroid = [c for c in all_cases if c["subspecialty"] == "thyroid"]
    analytes = {
        r["analyte_code"]
        for case in thyroid
        for panel in case["lab_panels"]
        for r in panel["results"]
    }
    for required in ("TSH", "FT4", "FT3", "TT4", "TT3", "TPOAB", "TRAB", "TG"):
        assert required in analytes, f"no thyroid case reports {required}"


def test_haemolysis_cases_split_immune_and_non_immune(all_cases):
    """The brief requires differentiating immune from non-immune causes."""
    heme = [c for c in all_cases if c["subspecialty"] == "haemolytic_anaemia"]
    immune = [c for c in heme if "immune" in c["tags"]]
    non_immune = [c for c in heme if "non-immune" in c["tags"]]
    assert len(immune) >= 4
    assert len(non_immune) >= 4
    assert not ({c["case_code"] for c in immune} & {c["case_code"] for c in non_immune})


def test_every_haemolysis_case_reports_a_direct_antiglobulin_test(all_cases):
    """The DAT is the fork in the road between immune and non-immune; a case
    that omits it cannot teach the distinction."""
    for case in (c for c in all_cases if c["subspecialty"] == "haemolytic_anaemia"):
        codes = {
            r["analyte_code"]
            for panel in case["lab_panels"]
            for r in panel["results"]
        }
        assert any(c.startswith("DAT") for c in codes), f"{case['case_code']} has no DAT"


def test_every_haemolysis_case_has_a_peripheral_smear_description(all_cases):
    for case in (c for c in all_cases if c["subspecialty"] == "haemolytic_anaemia"):
        assert case["smears"], f"{case['case_code']} has no smear"
        smear = case["smears"][0]
        assert smear["red_cell_morphology"], f"{case['case_code']} smear has no red cell findings"
        assert len(smear["narrative"]) > 200, f"{case['case_code']} smear narrative is too thin"


def test_leprosy_cases_report_bacterial_and_morphological_indices(all_cases):
    leprosy = [c for c in all_cases if c["case_code"].startswith("LEP")]
    assert len(leprosy) >= 7
    with_indices = [
        c
        for c in leprosy
        if any(r["bacterial_index"] is not None for r in c["microbiology"])
    ]
    assert len(with_indices) >= 6


def test_mdr_leprosy_cases_carry_molecular_resistance_data(all_cases):
    """Multi-drug resistance must be evidenced by genotype, not asserted."""
    mdr = [c for c in all_cases if "MDR" in c["tags"]]
    assert len(mdr) >= 2
    for case in mdr:
        targets = {
            finding["target"]
            for report in case["microbiology"]
            for finding in report["molecular_findings"]
        }
        assert {"rpoB", "folP1", "gyrA"} & targets, f"{case['case_code']} lacks resistance genotyping"


def test_leprosy_cases_define_a_treatment_protocol_with_a_regimen(all_cases):
    for case in (c for c in all_cases if c["case_code"].startswith("LEP")):
        assert case["protocols"], f"{case['case_code']} has no protocol"
        protocol = case["protocols"][0]
        assert len(protocol["regimen"]) >= 3, f"{case['case_code']} regimen is too thin"
        assert protocol["monitoring"], f"{case['case_code']} protocol has no monitoring plan"
        for step in protocol["regimen"]:
            assert "agent" in step and "dose" in step


# ---------------------------------------------------------------------------
# Internal consistency
# ---------------------------------------------------------------------------


def test_every_case_has_exactly_one_primary_diagnosis(all_cases):
    for case in all_cases:
        primaries = [d for d in case["diagnoses"] if d["is_primary"]]
        assert len(primaries) == 1, f"{case['case_code']} has {len(primaries)} primary diagnoses"


def test_every_case_offers_a_differential(all_cases):
    for case in all_cases:
        assert len(case["diagnoses"]) >= 3, f"{case['case_code']} has no meaningful differential"


def test_result_flags_agree_with_reference_intervals(all_cases):
    """An author-supplied flag must not contradict the interval on the same row.
    Deliberate 'inappropriately normal' values are flagged N and are consistent
    by construction, so this check is safe to apply corpus-wide."""
    for case in all_cases:
        for panel in case["lab_panels"]:
            for r in panel["results"]:
                value, low, high, flag = (
                    r["value_numeric"],
                    r["ref_low"],
                    r["ref_high"],
                    r["flag"],
                )
                if value is None or flag in {"A"}:
                    continue
                where = f"{case['case_code']}/{panel['panel_code']}/{r['analyte_code']}"
                if high is not None and value > high:
                    assert flag in {"H", "HH"}, f"{where}: {value} > {high} but flagged {flag}"
                elif low is not None and value < low:
                    assert flag in {"L", "LL"}, f"{where}: {value} < {low} but flagged {flag}"
                elif low is not None and high is not None:
                    assert flag == "N", f"{where}: {value} in [{low},{high}] but flagged {flag}"


def test_lab_timelines_are_chronologically_ordered(all_cases):
    for case in all_cases:
        offsets = [p["day_offset"] for p in case["lab_panels"]]
        assert offsets == sorted(offsets), f"{case['code'] if 'code' in case else case['case_code']}"


def test_critical_results_are_flagged_critical(all_cases):
    """Anything marked is_critical must carry a critical flag, and vice versa."""
    for case in all_cases:
        for panel in case["lab_panels"]:
            for r in panel["results"]:
                if r["is_critical"]:
                    assert r["flag"] in {"HH", "LL"}, (
                        f"{case['case_code']}/{r['analyte_code']} critical but flagged {r['flag']}"
                    )


def test_no_duplicate_case_codes(all_cases):
    codes = [c["case_code"] for c in all_cases]
    assert len(codes) == len(set(codes))


def test_difficulty_spread_is_pedagogically_useful(all_cases):
    """A corpus that is all level 3 cannot stratify a learner."""
    difficulties = {c["difficulty"] for c in all_cases}
    assert len(difficulties) >= 4
    assert max(difficulties) == 5


# ---------------------------------------------------------------------------
# Localisation
# ---------------------------------------------------------------------------


def test_every_case_title_is_translated_into_all_five_locales(all_cases):
    for case in all_cases:
        missing = set(SUPPORTED_LOCALES) - set(case["title_i18n"])
        assert not missing, f"{case['case_code']} title missing {sorted(missing)}"


def test_every_case_summary_is_translated_into_all_five_locales(all_cases):
    for case in all_cases:
        missing = set(SUPPORTED_LOCALES) - set(case["summary_i18n"])
        assert not missing, f"{case['case_code']} summary missing {sorted(missing)}"


def test_translations_are_not_copies_of_the_english(all_cases):
    """Guards against a placeholder translation pass that duplicated English."""
    for case in all_cases:
        english = case["title_i18n"]["en"]
        for locale in ("de", "es", "nl", "ru"):
            assert case["title_i18n"][locale] != english, (
                f"{case['case_code']} {locale} title is a copy of the English"
            )


def test_russian_titles_use_cyrillic(all_cases):
    """A Latin-only 'Russian' string is an untranslated placeholder."""
    for case in all_cases:
        russian = case["title_i18n"]["ru"]
        assert any("Ѐ" <= ch <= "ӿ" for ch in russian), (
            f"{case['case_code']} has no Cyrillic in its Russian title"
        )


def test_german_titles_are_long_enough_to_stress_layouts(all_cases):
    """German is the layout-stress locale for the dashboard; if the corpus does
    not contain any long German strings, the Cypress layout tests are vacuous."""
    longest = max(len(c["title_i18n"]["de"]) for c in all_cases)
    assert longest >= 60


# ---------------------------------------------------------------------------
# Grading keys (consumed by Phase 4)
# ---------------------------------------------------------------------------


def test_every_case_has_a_usable_reasoning_key(all_cases):
    for case in all_cases:
        key = case["reasoning_key"]
        code = case["case_code"]
        assert key.get("primary_diagnosis"), f"{code} has no primary diagnosis in its key"
        assert key.get("accepted_diagnosis_terms"), f"{code} has no accepted terms"
        assert len(key.get("must_include_findings", [])) >= 3, f"{code} has too few findings"
        assert key.get("expected_differential"), f"{code} has no expected differential"
        assert key.get("expected_management"), f"{code} has no expected management"


def test_reasoning_key_findings_are_well_formed(all_cases):
    for case in all_cases:
        for finding in case["reasoning_key"]["must_include_findings"]:
            assert finding.get("label")
            assert finding.get("synonyms"), f"{case['case_code']}: {finding['label']} has no synonyms"
            assert isinstance(finding.get("weight", 1.0), (int, float))


def test_accepted_diagnosis_terms_are_lowercase_for_matching(all_cases):
    for case in all_cases:
        for term in case["reasoning_key"]["accepted_diagnosis_terms"]:
            assert term == term.lower(), f"{case['case_code']}: '{term}' is not lowercased"


def test_safety_rules_are_well_formed(all_cases):
    with_rules = 0
    for case in all_cases:
        rules = case["reasoning_key"].get("safety_rules", [])
        for rule in rules:
            assert rule.get("id"), f"{case['case_code']} has an unnamed safety rule"
            assert rule.get("description")
            assert rule.get("required_terms") or rule.get("forbidden_patterns"), (
                f"{case['case_code']}/{rule['id']} constrains nothing"
            )
        if rules:
            with_rules += 1
    assert with_rules >= 20, "most cases should carry at least one safety rule"


def test_primary_diagnosis_is_matchable_by_its_own_accepted_terms(all_cases):
    """The grading key must accept the case's own answer, or nothing can pass."""
    for case in all_cases:
        key = case["reasoning_key"]
        primary = key["primary_diagnosis"].lower()
        terms = key["accepted_diagnosis_terms"]
        assert any(t in primary or primary in t for t in terms), (
            f"{case['case_code']}: primary diagnosis '{primary}' matches none of its own terms"
        )


# ---------------------------------------------------------------------------
# Editorial quality
# ---------------------------------------------------------------------------


def test_every_case_carries_teaching_points(all_cases):
    for case in all_cases:
        assert len(case["teaching_points"]) >= 4, f"{case['case_code']} has too few teaching points"


def test_every_case_cites_a_reference(all_cases):
    for case in all_cases:
        assert case["references"], f"{case['case_code']} cites nothing"
        assert all("citation" in r for r in case["references"])


def test_seed_files_are_valid_json_and_declare_a_schema_version():
    files = sorted(DATA_DIR.glob("cases_*.json"))
    assert files
    for path in files:
        document = json.loads(path.read_text(encoding="utf-8"))
        assert document.get("schema_version") == "1.0", f"{path.name} has no schema_version"
        assert document.get("cases"), f"{path.name} contains no cases"
