"""In-process smoke test for the FastAPI app (no real network)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from kosma.main import app


def main() -> int:
    client = TestClient(app)

    # /healthz
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json() == {"ok": True}, r.text
    print("healthz: ok")

    # GET /
    r = client.get("/")
    assert r.status_code == 200, r.status_code
    assert "KOSMA" in r.text, "wordmark missing"
    # Security headers
    for hdr in [
        "x-content-type-options",
        "x-frame-options",
        "referrer-policy",
        "content-security-policy",
        "permissions-policy",
        "cache-control",
    ]:
        assert hdr in (h.lower() for h in r.headers), f"missing {hdr}"
    print("index + security headers: ok")

    # POST /generate (city path)
    r = client.post(
        "/generate",
        data={
            "name": "Test Subject",
            "birth_date": "2000-01-01",
            "birth_time": "12:00",
            "city": "London, UK",
        },
    )
    assert r.status_code == 200, (r.status_code, r.text[:300])
    assert r.headers.get("content-type") == "application/pdf", r.headers
    assert r.content.startswith(b"%PDF-"), "not a PDF"
    assert "attachment" in r.headers.get("content-disposition", ""), r.headers
    print(f"generate (city): ok, {len(r.content):,} bytes PDF")

    # POST /generate (manual coords path)
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
    assert r.status_code == 200, (r.status_code, r.text[:300])
    assert r.content.startswith(b"%PDF-"), "manual PDF invalid"
    print(f"generate (manual): ok, {len(r.content):,} bytes PDF")

    # Validation: bad date
    r = client.post(
        "/generate",
        data={
            "birth_date": "notadate",
            "birth_time": "12:00",
            "city": "Mumbai, India",
        },
    )
    assert r.status_code == 400, (r.status_code, r.text)
    print(f"bad date: 400 ok ({r.json()['detail']!r})")

    # Validation: bad time
    r = client.post(
        "/generate",
        data={
            "birth_date": "1990-01-01",
            "birth_time": "26:99",
            "city": "Mumbai, India",
        },
    )
    assert r.status_code == 400
    print(f"bad time: 400 ok ({r.json()['detail']!r})")

    # Validation: missing place
    r = client.post(
        "/generate",
        data={
            "birth_date": "1990-01-01",
            "birth_time": "12:00",
        },
    )
    assert r.status_code == 400
    print(f"missing place: 400 ok ({r.json()['detail']!r})")

    # Validation: out-of-range latitude
    r = client.post(
        "/generate",
        data={
            "birth_date": "1990-01-01",
            "birth_time": "12:00",
            "manual_lat": "120",
            "manual_lon": "0",
            "manual_tz": "0",
        },
    )
    assert r.status_code == 400
    print(f"bad lat: 400 ok ({r.json()['detail']!r})")

    # Year out of range
    r = client.post(
        "/generate",
        data={
            "birth_date": "1850-01-01",
            "birth_time": "12:00",
            "city": "Mumbai, India",
        },
    )
    assert r.status_code == 400
    print(f"old year: 400 ok ({r.json()['detail']!r})")

    print("\nAll HTTP smoke checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
