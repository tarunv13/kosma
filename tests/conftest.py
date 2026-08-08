"""Shared pytest fixtures.

Every chart here is a synthetic astronomical epoch, never a person. That is
deliberate: a test suite pinned to somebody's real birth data publishes their
birth data, which would contradict the whole privacy posture of this project.

    reference_chart   J2000 epoch  — 1 Jan 2000, 12:00, London
    second_chart      June solstice — 21 Jun 2010, 06:00, Indore
    third_chart       March equinox — 21 Mar 1995, 18:00, Delhi

Each is still independently re-verifiable in any Vedic software with Lahiri
ayanamsa, which is all the reference chart was ever for.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kosma import vedic_engine as ve

# The J2000.0 epoch at the prime meridian. Not a birth.
REFERENCE_BIRTH = {
    "year": 2000,
    "month": 1,
    "day": 1,
    "hour": 12,
    "minute": 0,
    "lat": 51.5074,
    "lon": -0.1278,
    "tz": 0.0,
}


@pytest.fixture(scope="session")
def reference_chart() -> ve.Chart:
    """The J2000 epoch chart, used to pin the engine against regressions."""
    return ve.build_chart(
        label="Reference",
        year=REFERENCE_BIRTH["year"],
        month=REFERENCE_BIRTH["month"],
        day=REFERENCE_BIRTH["day"],
        hour=REFERENCE_BIRTH["hour"],
        minute=REFERENCE_BIRTH["minute"],
        lat=REFERENCE_BIRTH["lat"],
        lon_geo=REFERENCE_BIRTH["lon"],
        tz=REFERENCE_BIRTH["tz"],
    )


# Anything touching dashas or transits has to be pinned to a fixed moment,
# or the suite would quietly change meaning every day it runs.
PINNED_NOW = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)


@pytest.fixture(scope="session")
def pinned_now() -> datetime:
    return PINNED_NOW


@pytest.fixture(scope="session")
def pinned_now_jd() -> float:
    return ve.local_to_ut(
        PINNED_NOW.year, PINNED_NOW.month, PINNED_NOW.day, PINNED_NOW.hour, PINNED_NOW.minute, 0.0
    )


# A second epoch, so tests can tell "correct" apart from "constant".
SECOND_BIRTH = {
    "year": 2010,
    "month": 6,
    "day": 21,
    "hour": 6,
    "minute": 0,
    "lat": 22.7196,
    "lon": 75.8577,
    "tz": 5.5,
}


@pytest.fixture(scope="session")
def second_chart() -> ve.Chart:
    """The 2010 June solstice at Indore. Gemini rising; a contrasting sky."""
    return ve.build_chart(
        label="Second",
        year=SECOND_BIRTH["year"],
        month=SECOND_BIRTH["month"],
        day=SECOND_BIRTH["day"],
        hour=SECOND_BIRTH["hour"],
        minute=SECOND_BIRTH["minute"],
        lat=SECOND_BIRTH["lat"],
        lon_geo=SECOND_BIRTH["lon"],
        tz=SECOND_BIRTH["tz"],
    )


@pytest.fixture(scope="session")
def reference_birth_input():
    from kosma.grounding import BirthInput

    return BirthInput(
        name="Epoch J2000",
        year=REFERENCE_BIRTH["year"],
        month=REFERENCE_BIRTH["month"],
        day=REFERENCE_BIRTH["day"],
        hour=REFERENCE_BIRTH["hour"],
        minute=REFERENCE_BIRTH["minute"],
        lat=REFERENCE_BIRTH["lat"],
        lon=REFERENCE_BIRTH["lon"],
        tz=REFERENCE_BIRTH["tz"],
        place="London, UK",
    )


@pytest.fixture(scope="session")
def reference_pack(reference_birth_input, pinned_now):
    from kosma import grounding

    return grounding.build_pack(reference_birth_input, now=pinned_now)
