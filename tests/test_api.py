"""HTTP layer tests via FastAPI's TestClient (in-process, no real network)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from kosma.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_version(client: TestClient) -> None:
    r = client.get("/version")
    assert r.status_code == 200
    body = r.json()
    assert body["app"] == "KOSMA"
    assert "version" in body


def test_index_renders_brand_and_security_headers(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "KOSMA" in r.text
    # Security headers
    headers = {k.lower(): v for k, v in r.headers.items()}
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert "default-src 'self'" in headers["content-security-policy"]
    assert "frame-ancestors 'none'" in headers["content-security-policy"]
    assert "no-store" in headers["cache-control"]


def test_docs_endpoints_disabled(client: TestClient) -> None:
    """We deliberately disable /docs, /redoc, /openapi.json to shrink surface."""
    for path in ("/docs", "/redoc", "/openapi.json"):
        r = client.get(path)
        assert r.status_code == 404, f"{path} should be 404, got {r.status_code}"


def test_generate_pdf_via_city(client: TestClient) -> None:
    r = client.post(
        "/generate",
        data={
            "name": "Synthetic Subject",
            "birth_date": "2000-01-01",
            "birth_time": "12:00",
            "city": "London, UK",
        },
    )
    assert r.status_code == 200, r.text[:300]
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF-")
    assert "attachment" in r.headers["content-disposition"]
    assert r.headers["cache-control"].startswith("no-store")


def test_generate_pdf_via_manual_coords(client: TestClient) -> None:
    r = client.post(
        "/generate",
        data={
            "name": "Manual",
            "birth_date": "1990-06-15",
            "birth_time": "14:30",
            "manual_label": "Some Town",
            "manual_lat": "28.61",
            "manual_lon": "77.21",
            "manual_tz": "5.5",
        },
    )
    assert r.status_code == 200
    assert r.content.startswith(b"%PDF-")


@pytest.mark.parametrize(
    "data,expected_substr",
    [
        # Bad date format
        (
            {"birth_date": "notadate", "birth_time": "12:00", "city": "Mumbai, India"},
            "Invalid birth date",
        ),
        # Bad time
        (
            {"birth_date": "1990-01-01", "birth_time": "26:99", "city": "Mumbai, India"},
            "Invalid birth time",
        ),
        # Missing place entirely
        ({"birth_date": "1990-01-01", "birth_time": "12:00"}, "Choose a city"),
        # Latitude out of range
        (
            {
                "birth_date": "1990-01-01",
                "birth_time": "12:00",
                "manual_lat": "120",
                "manual_lon": "0",
                "manual_tz": "0",
            },
            "Latitude must be between",
        ),
        # Longitude out of range
        (
            {
                "birth_date": "1990-01-01",
                "birth_time": "12:00",
                "manual_lat": "0",
                "manual_lon": "999",
                "manual_tz": "0",
            },
            "Longitude must be between",
        ),
        # Timezone out of range
        (
            {
                "birth_date": "1990-01-01",
                "birth_time": "12:00",
                "manual_lat": "0",
                "manual_lon": "0",
                "manual_tz": "20",
            },
            "Timezone offset must be between",
        ),
        # Year too old
        (
            {"birth_date": "1850-01-01", "birth_time": "12:00", "city": "Mumbai, India"},
            "Birth year out of range",
        ),
    ],
)
def test_generate_validation_errors(client: TestClient, data: dict, expected_substr: str) -> None:
    r = client.post("/generate", data=data)
    assert r.status_code == 400
    assert expected_substr in r.json()["detail"]


# ── grounding endpoint ────────────────────────────────────────────────

GROUNDING_FORM = {
    "name": "Epoch J2000",
    "birth_date": "2000-01-01",
    "birth_time": "12:00",
    "city": "London, UK",
}


def test_grounding_returns_a_computed_pack(client: TestClient) -> None:
    r = client.post("/api/grounding", data=GROUNDING_FORM)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")
    pack = r.json()
    assert pack["ascendant"]["sign"] == "Aries"
    assert pack["meta"]["zodiac"] == "sidereal"
    assert pack["evidence"]["gate"]
    assert pack["constraints"]


def test_grounding_is_never_cached(client: TestClient) -> None:
    r = client.post("/api/grounding", data=GROUNDING_FORM)
    assert r.headers["cache-control"] == "no-store, max-age=0"
    assert r.headers["x-frame-options"] == "DENY"


def test_grounding_rejects_a_bad_date(client: TestClient) -> None:
    bad = {**GROUNDING_FORM, "birth_date": "not-a-date"}
    r = client.post("/api/grounding", data=bad)
    assert r.status_code == 400


def test_grounding_does_not_echo_input_on_error(client: TestClient) -> None:
    bad = {**GROUNDING_FORM, "birth_time": "99:99", "name": "Sensitive Name"}
    r = client.post("/api/grounding", data=bad)
    assert r.status_code == 400
    assert "Sensitive Name" not in r.text


def test_grounding_clamps_the_horizon(client: TestClient) -> None:
    r = client.post("/api/grounding", data={**GROUNDING_FORM, "horizon_years": "999"})
    assert r.status_code == 200
    assert r.json()["activation_windows"]["horizon_years"] <= 30.0


def test_openapi_surface_stays_disabled(client: TestClient) -> None:
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404


# ── compatibility ─────────────────────────────────────────────────────

PAIR_FORM = {
    "mode": "relationship",
    "include_third": "no",
    "a_name": "Epoch A",
    "a_date": "2000-01-01",
    "a_time": "12:00",
    "a_city": "London, UK",
    "b_name": "Epoch B",
    "b_date": "2010-06-21",
    "b_time": "06:00",
    "b_city": "Indore, India",
}
TRIO_FORM = {
    **PAIR_FORM,
    "mode": "friendship",
    "include_third": "yes",
    "c_name": "Epoch C",
    "c_date": "1995-03-21",
    "c_time": "18:00",
    "c_city": "Delhi, India",
}


def test_compatibility_form_renders(client: TestClient) -> None:
    r = client.get("/compatibility")
    assert r.status_code == 200
    assert "Compatibility" in r.text
    assert "birth caste" in r.text, "the varna framing must be on the page"


def test_compatibility_pair(client: TestClient) -> None:
    r = client.post("/compatibility", data=PAIR_FORM)
    assert r.status_code == 200
    assert "Epoch A" in r.text and "Epoch B" in r.text
    assert "Findings" in r.text
    assert "Ashtakoota" in r.text
    assert r.headers["cache-control"] == "no-store, max-age=0"


def test_compatibility_leads_with_findings_not_the_score(client: TestClient) -> None:
    """Evidence first was a deliberate call; keep it that way."""
    body = client.post("/compatibility", data=PAIR_FORM).text
    assert body.index("Findings") < body.index("Ashtakoota")


def test_compatibility_trio_is_pairwise(client: TestClient) -> None:
    r = client.post("/compatibility", data=TRIO_FORM)
    assert r.status_code == 200
    for pair in ("Epoch A &amp; Epoch B", "Epoch A &amp; Epoch C", "Epoch B &amp; Epoch C"):
        assert pair in r.text


def test_friendship_mode_hides_the_marriage_kootas(client: TestClient) -> None:
    body = client.post("/compatibility", data=TRIO_FORM).text
    assert "Maitri factors" in body
    assert "not a classical named scheme" in body


def test_compatibility_error_is_html_and_does_not_echo_input(client: TestClient) -> None:
    bad = {**PAIR_FORM, "a_date": "not-a-date"}
    r = client.post("/compatibility", data=bad)
    assert r.status_code == 400
    assert r.headers["content-type"].startswith("text/html")
    assert "Epoch A" not in r.text
    assert "London" not in r.text
    assert "First person" in r.text


def test_compatibility_rejects_unknown_mode(client: TestClient) -> None:
    r = client.post("/compatibility", data={**PAIR_FORM, "mode": "soulmate"})
    assert r.status_code == 400


def test_duplicate_names_stay_addressable(client: TestClient) -> None:
    same = {**PAIR_FORM, "a_name": "Sam", "b_name": "Sam"}
    r = client.post("/compatibility", data=same)
    assert r.status_code == 200
    assert "Sam (2)" in r.text


# ── chart contract endpoint ───────────────────────────────────────────

CHART_FORM = {
    "name": "Epoch J2000",
    "birth_date": "2000-01-01",
    "birth_time": "12:00",
    "city": "London, UK",
}


def test_api_chart_returns_the_contract(client: TestClient) -> None:
    r = client.post("/api/chart", data=CHART_FORM)
    assert r.status_code == 200
    body = r.json()
    assert body["contract_version"]
    assert body["ascendant"]["sign"] == "Aries"
    assert len(body["planets"]) == 9
    assert r.headers["cache-control"] == "no-store, max-age=0"


def test_api_chart_rejects_bad_input(client: TestClient) -> None:
    r = client.post("/api/chart", data={**CHART_FORM, "birth_time": "25:00"})
    assert r.status_code == 400


def test_cors_allows_only_the_configured_origins(client: TestClient) -> None:
    ok = client.options(
        "/api/chart",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"

    blocked = client.options(
        "/api/chart",
        headers={
            "Origin": "https://not-our-frontend.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert blocked.headers.get("access-control-allow-origin") is None


def test_cors_never_allows_credentials(client: TestClient) -> None:
    r = client.options(
        "/api/chart",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert r.headers.get("access-control-allow-credentials") is None


def test_api_compatibility_pair(client: TestClient) -> None:
    r = client.post("/api/compatibility", data=PAIR_FORM)
    assert r.status_code == 200
    body = r.json()
    assert len(body["pairs"]) == 1
    assert body["pairs"][0]["milan"]["maximum"] == 36.0
    assert r.headers["cache-control"] == "no-store, max-age=0"


def test_api_compatibility_trio(client: TestClient) -> None:
    body = client.post("/api/compatibility", data=TRIO_FORM).json()
    assert len(body["pairs"]) == 3
    assert body["mode"] == "friendship"


def test_api_compatibility_rejects_bad_mode(client: TestClient) -> None:
    r = client.post("/api/compatibility", data={**PAIR_FORM, "mode": "soulmate"})
    assert r.status_code == 400


def test_api_compatibility_does_not_echo_input(client: TestClient) -> None:
    r = client.post("/api/compatibility", data={**PAIR_FORM, "a_date": "nope"})
    assert r.status_code == 400
    assert "Epoch A" not in r.text
    assert "First person" in r.text


def test_api_chart_exposes_vargas_and_dossiers(client: TestClient) -> None:
    body = client.post("/api/chart", data=CHART_FORM).json()
    assert len(body["vargas"]) == 16
    assert all(h["governs"] for h in body["houses"])
