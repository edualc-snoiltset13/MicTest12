"""API-level tests covering CRUD, filtering, derived reads, errors and chaos."""

from __future__ import annotations

import pytest

API = "/api/v1"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_healthz_does_not_touch_the_database(client):
    body = client.get("/healthz").json()
    assert body["status"] == "ok"
    assert "uptime_seconds" in body


def test_readyz_reports_a_fully_seeded_corpus(client):
    body = client.get("/readyz").json()
    assert body["status"] == "ok"
    assert body["case_count"] == 25
    assert body["checks"]["database"] == "ok"


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def test_case_list_is_paginated_and_reports_totals(client):
    body = client.get(f"{API}/cases", params={"limit": 5}).json()
    assert body["meta"]["total"] == 25
    assert body["meta"]["returned"] == 5
    assert body["meta"]["has_more"] is True
    assert len(body["items"]) == 5


def test_case_list_omits_the_lab_timeline(client):
    """The summary projection is what keeps the dashboard load small."""
    item = client.get(f"{API}/cases", params={"limit": 1}).json()["items"][0]
    assert "lab_panels" not in item
    assert "patient" in item


@pytest.mark.parametrize(
    ("discipline", "expected"),
    [("chemical_pathology", 9), ("hematology", 9), ("microbiology", 4), ("pharmacology", 3)],
)
def test_discipline_filter_partitions_the_corpus(client, discipline, expected):
    body = client.get(f"{API}/cases", params={"discipline": discipline, "limit": 200}).json()
    assert body["meta"]["total"] == expected


def test_subspecialty_filter(client):
    body = client.get(f"{API}/cases", params={"subspecialty": "thyroid", "limit": 200}).json()
    assert body["meta"]["total"] == 9
    assert all(i["case_code"].startswith("THY") for i in body["items"])


def test_search_matches_title_and_code(client):
    assert client.get(f"{API}/cases", params={"search": "THY-001"}).json()["meta"]["total"] == 1
    assert client.get(f"{API}/cases", params={"search": "haemoglobin"}).json()["meta"]["total"] >= 1


def test_tag_filter_does_not_match_substrings(client):
    """A tag search for 'immune' must not sweep in 'non-immune'."""
    body = client.get(f"{API}/cases", params={"tag": "immune", "limit": 200}).json()
    codes = {i["case_code"] for i in body["items"]}
    assert "HEM-001" in codes  # tagged "immune"
    assert "HEM-005" not in codes  # tagged "non-immune" only


def test_difficulty_range_filter(client):
    body = client.get(f"{API}/cases", params={"difficulty_min": 5, "limit": 200}).json()
    assert body["meta"]["total"] >= 4
    assert all(i["difficulty"] == 5 for i in body["items"])


def test_inverted_difficulty_range_is_rejected(client):
    r = client.get(f"{API}/cases", params={"difficulty_min": 4, "difficulty_max": 2})
    assert r.status_code == 422
    assert "difficulty_min" in r.json()["detail"]


def test_sorting_is_applied(client):
    asc = client.get(f"{API}/cases", params={"sort_by": "case_code", "sort_dir": "asc"}).json()
    desc = client.get(f"{API}/cases", params={"sort_by": "case_code", "sort_dir": "desc"}).json()
    assert asc["items"][0]["case_code"] < desc["items"][0]["case_code"]


def test_case_fetch_by_code_and_by_id_agree(client):
    by_code = client.get(f"{API}/cases/THY-001").json()
    by_id = client.get(f"{API}/cases/{by_code['id']}").json()
    assert by_code == by_id


def test_full_case_carries_every_child_collection(client):
    case = client.get(f"{API}/cases/HEM-001").json()
    assert case["patient"]["age_years"] == 68
    assert case["presentation"]["chief_complaint"]
    assert len(case["lab_panels"]) >= 5
    assert len(case["smears"]) >= 1
    assert len(case["diagnoses"]) >= 4
    assert len(case["protocols"]) >= 1
    assert case["reasoning_key"]["primary_diagnosis"]


def test_missing_case_returns_rfc7807_style_body(client):
    r = client.get(f"{API}/cases/NOPE-123")
    assert r.status_code == 404
    body = r.json()
    assert body["status"] == 404
    assert body["title"] == "Not found"
    assert body["request_id"]


# ---------------------------------------------------------------------------
# Derived reads
# ---------------------------------------------------------------------------


def test_trends_pivot_the_timeline_in_chronological_order(client):
    body = client.get(f"{API}/cases/THY-003/trends", params={"analytes": "TSH"}).json()
    series = body["series"][0]
    assert series["analyte_code"] == "TSH"
    offsets = [p["day_offset"] for p in series["points"]]
    assert offsets == sorted(offsets)
    # The monotonic rise is the clinical point of this case.
    values = [p["value"] for p in series["points"][:5]]
    assert values == sorted(values)


def test_trends_exclude_qualitative_results(client):
    """A DAT reported as 'Positive 4+' has no place on a line chart."""
    body = client.get(f"{API}/cases/HEM-001/trends").json()
    codes = {s["analyte_code"] for s in body["series"]}
    assert "HB" in codes
    assert "DAT_POLY" not in codes


def test_trends_carry_reference_bands_for_shading(client):
    series = client.get(f"{API}/cases/THY-001/trends", params={"analytes": "TSH"}).json()["series"][0]
    assert series["ref_low"] == 0.4
    assert series["ref_high"] == 4.0
    assert series["unit"] == "mIU/L"


def test_diagnoses_are_ordered_primary_first(client):
    diagnoses = client.get(f"{API}/cases/HEM-005/diagnoses").json()
    assert diagnoses[0]["is_primary"] is True
    likelihoods = [d["likelihood"] or 0 for d in diagnoses[1:]]
    assert likelihoods == sorted(likelihoods, reverse=True)


def test_lab_panels_can_be_filtered_by_panel_code(client):
    panels = client.get(f"{API}/cases/THY-001/labs", params={"panel_code": "TFT"}).json()
    assert panels
    assert all(p["panel_code"] == "TFT" for p in panels)


def test_microbiology_subresource(client):
    reports = client.get(f"{API}/cases/LEP-001/microbiology").json()
    assert reports
    assert reports[0]["bacterial_index"] == 4.6
    assert any(m["target"] == "rpoB" for m in reports[0]["molecular_findings"])


def test_stats_endpoint(client):
    body = client.get(f"{API}/cases/stats").json()
    assert body["total_cases"] == 25
    assert sum(body["by_discipline"].values()) == 25
    assert body["total_lab_results"] > 400


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------


def test_reference_intervals_are_served(client):
    intervals = client.get(f"{API}/reference/intervals", params={"category": "thyroid"}).json()
    assert intervals
    assert all(i["category"] == "thyroid" for i in intervals)


def test_enums_drive_frontend_dropdowns(client):
    body = client.get(f"{API}/reference/enums").json()
    assert set(body["locales"]) == {"en", "de", "es", "nl", "ru"}
    assert "chemical_pathology" in body["disciplines"]


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------


def test_create_read_update_delete_round_trip(client, sample_case_payload):
    created = client.post(f"{API}/cases", json=sample_case_payload)
    assert created.status_code == 201
    assert created.headers["Location"].endswith("TST-001")
    case_id = created.json()["id"]

    fetched = client.get(f"{API}/cases/TST-001").json()
    assert fetched["title"] == sample_case_payload["title"]
    assert len(fetched["lab_panels"]) == 1

    patched = client.patch(f"{API}/cases/TST-001", json={"difficulty": 5, "tags": ["updated"]})
    assert patched.status_code == 200
    assert patched.json()["difficulty"] == 5
    assert patched.json()["tags"] == ["updated"]
    # Omitted collections are left untouched.
    assert len(patched.json()["lab_panels"]) == 1

    assert client.delete(f"{API}/cases/{case_id}").status_code == 204
    assert client.get(f"{API}/cases/TST-001").status_code == 404


def test_duplicate_case_code_conflicts(client, sample_case_payload):
    first = client.post(f"{API}/cases", json=sample_case_payload)
    assert first.status_code == 201
    try:
        clash = client.post(f"{API}/cases", json=sample_case_payload)
        assert clash.status_code == 409
        assert "already in use" in clash.json()["detail"]
    finally:
        client.delete(f"{API}/cases/TST-001")


def test_patch_replaces_lab_panels_wholesale(client, sample_case_payload):
    client.post(f"{API}/cases", json=sample_case_payload)
    try:
        replaced = client.patch(f"{API}/cases/TST-001", json={"lab_panels": []}).json()
        assert replaced["lab_panels"] == []
    finally:
        client.delete(f"{API}/cases/TST-001")


def test_empty_patch_is_rejected(client, sample_case_payload):
    client.post(f"{API}/cases", json=sample_case_payload)
    try:
        assert client.patch(f"{API}/cases/TST-001", json={}).status_code == 422
    finally:
        client.delete(f"{API}/cases/TST-001")


def test_patch_rejects_unknown_fields(client, sample_case_payload):
    client.post(f"{API}/cases", json=sample_case_payload)
    try:
        r = client.patch(f"{API}/cases/TST-001", json={"nonsense_field": 1})
        assert r.status_code == 422
    finally:
        client.delete(f"{API}/cases/TST-001")


def test_delete_cascades_to_children(client, sample_case_payload, db_session):
    from sqlalchemy import func, select

    from app import models

    created = client.post(f"{API}/cases", json=sample_case_payload).json()
    client.delete(f"{API}/cases/{created['id']}")

    orphan_panels = db_session.execute(
        select(func.count(models.LabPanel.id)).where(models.LabPanel.case_id == created["id"])
    ).scalar_one()
    assert orphan_panels == 0


def test_mutations_are_audited(client, sample_case_payload):
    client.post(f"{API}/cases", json=sample_case_payload, headers={"X-Actor": "pytest"})
    try:
        events = client.get(f"{API}/reference/audit", params={"limit": 20}).json()
        created = [e for e in events if e["entity_id"] == "TST-001" and e["action"] == "create"]
        assert created
        assert created[0]["actor"] == "pytest"
        assert created[0]["request_id"]
    finally:
        client.delete(f"{API}/cases/TST-001")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_malformed_case_code_is_rejected(client, sample_case_payload):
    sample_case_payload["case_code"] = "bad code"
    r = client.post(f"{API}/cases", json=sample_case_payload)
    assert r.status_code == 422
    assert any("case_code" in e["location"] for e in r.json()["errors"])


def test_unsupported_locale_key_is_rejected(client, sample_case_payload):
    sample_case_payload["title_i18n"] = {"en": "ok", "fr": "non pris en charge"}
    r = client.post(f"{API}/cases", json=sample_case_payload)
    assert r.status_code == 422
    assert "unsupported locale" in str(r.json()["errors"]).lower()


def test_lab_result_requires_a_value(client, sample_case_payload):
    sample_case_payload["lab_panels"][0]["results"][0].pop("value_numeric")
    r = client.post(f"{API}/cases", json=sample_case_payload)
    assert r.status_code == 422


def test_inverted_reference_interval_is_rejected(client, sample_case_payload):
    result = sample_case_payload["lab_panels"][0]["results"][0]
    result["ref_low"], result["ref_high"] = 10.0, 1.0
    r = client.post(f"{API}/cases", json=sample_case_payload)
    assert r.status_code == 422


def test_multiple_primary_diagnoses_are_rejected(client, sample_case_payload):
    sample_case_payload["diagnoses"].append(
        {"label": "Second primary", "is_primary": True, "certainty": "probable"}
    )
    r = client.post(f"{API}/cases", json=sample_case_payload)
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Cross-cutting concerns
# ---------------------------------------------------------------------------


def test_request_id_is_echoed_when_supplied(client):
    r = client.get("/healthz", headers={"X-Request-ID": "trace-me-123"})
    assert r.headers["X-Request-ID"] == "trace-me-123"


def test_request_id_is_generated_when_absent(client):
    assert client.get("/healthz").headers["X-Request-ID"]


def test_security_headers_are_applied(client):
    headers = client.get("/healthz").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in headers["Content-Security-Policy"]


def test_server_timing_header_supports_frontend_assertions(client):
    assert client.get("/healthz").headers["Server-Timing"].startswith("app;dur=")


def test_total_count_header_matches_meta(client):
    r = client.get(f"{API}/cases", params={"limit": 2})
    assert r.headers["X-Total-Count"] == str(r.json()["meta"]["total"])


# ---------------------------------------------------------------------------
# Chaos middleware (the backend half of the Phase 3 network tests)
# ---------------------------------------------------------------------------


def test_chaos_forces_a_status_code(client):
    r = client.get(f"{API}/cases", headers={"X-Chaos-Status": "503"})
    assert r.status_code == 503
    assert r.json()["title"] == "Injected fault"


def test_chaos_produces_malformed_json(client):
    import json

    r = client.get(f"{API}/cases/THY-001", headers={"X-Chaos-Malformed": "1"})
    assert r.status_code == 200
    with pytest.raises(json.JSONDecodeError):
        json.loads(r.text)


def test_chaos_truncates_the_body(client):
    r = client.get(f"{API}/cases/THY-001", headers={"X-Chaos-Truncate": "40"})
    assert len(r.content) == 40


def test_chaos_returns_an_empty_body(client):
    r = client.get(f"{API}/cases/THY-001", headers={"X-Chaos-Empty": "1"})
    assert r.content == b""


def test_chaos_overrides_content_type(client):
    r = client.get(f"{API}/cases/THY-001", headers={"X-Chaos-Content-Type": "text/html"})
    assert r.headers["content-type"].startswith("text/html")


def test_normal_requests_are_unaffected_by_the_chaos_layer(client):
    """Chaos is enabled in this test session; without headers nothing changes."""
    assert client.get(f"{API}/cases/THY-001").status_code == 200
