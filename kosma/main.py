"""
FastAPI front-end for KOSMA.

Privacy posture:
  * Birth data is accepted only as a POST form, validated, used to render a
    PDF in memory, then discarded. Nothing is written to disk and nothing is
    logged about the contents of the request.
  * No cookies, no session, no analytics, no third-party calls.
  * Rate-limited per-IP to discourage scraping/abuse.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import re
import secrets
import sys
import traceback
from datetime import UTC, date, datetime

from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from . import __version__, api_contract, cities, compatibility, grounding, pdf_generator
from . import vedic_engine as ve

# Tracebacks and verbose errors are opt-in, never the default.
DEBUG = os.environ.get("KOSMA_DEBUG", "").lower() in {"1", "true", "yes"}

# ── Logging: silence access logs of payload bodies; never log form data ──

logger = logging.getLogger("kosma")
logger.setLevel(logging.INFO)

# ── App + rate limiter ───────────────────────────────────────────────
#
# slowapi keys its buckets by whatever `key_func` returns and holds those keys
# in memory for the window. `get_remote_address` returns the raw client IP,
# which in most jurisdictions is personal data — so the process would be
# retaining a list of everyone who visited.
#
# Hashing it with a salt generated fresh at startup keeps the bucket working
# exactly as before while making the stored key unlinkable to an address and
# useless to anyone who reads the process memory or a heap dump. The salt is
# never persisted, so the mapping dies with the process.

_RATE_SALT = secrets.token_bytes(32)


def _anonymous_rate_key(request: Request) -> str:
    """A stable per-window bucket id that is not the caller's IP."""
    raw = get_remote_address(request) or "unknown"
    return hashlib.blake2b(raw.encode("utf-8"), key=_RATE_SALT, digest_size=16).hexdigest()


limiter = Limiter(key_func=_anonymous_rate_key, default_limits=["60/hour"])

app = FastAPI(
    title="KOSMA",
    description="Privacy-first Vedic Soul Blueprint generator.",
    version=__version__,
    docs_url=None,  # no /docs
    redoc_url=None,  # no /redoc
    openapi_url=None,  # no /openapi.json — minimise attack surface
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# ── CORS, narrowly ────────────────────────────────────────────────────
#
# The React client runs on its own origin in development, so the JSON routes
# need CORS. This is scoped deliberately: an explicit origin allowlist (never
# a wildcard), only the two API routes' methods, and credentials off, since
# nothing here uses cookies. Set KOSMA_CORS_ORIGINS to a comma-separated list
# to serve a frontend from somewhere else; the default only covers localhost
# development and is inert in production.
_DEFAULT_CORS = "http://localhost:3000,http://127.0.0.1:3000"
_CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("KOSMA_CORS_ORIGINS", _DEFAULT_CORS).split(",")
    if origin.strip()
]
if _CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
        max_age=600,
    )

# Static + templates
_HERE = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(_HERE, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(_HERE, "templates"))

# ── The React client, served as a static bundle ───────────────────────
#
# `next build` with output: "export" writes plain HTML/JS/CSS to web/out.
# Serving it from this process rather than a second Node service means one
# origin, so the client's fetch("/api/chart") is same-origin and CORS never
# applies in production; one deploy; and no server-side rendering to pay for.
#
# If the directory is absent -- a source checkout where nobody has run the
# frontend build -- every route below still works and "/" falls back to the
# server-rendered Jinja form. The app must not require a Node toolchain to
# start.
_WEB_OUT = os.environ.get("KOSMA_WEB_OUT") or os.path.join(os.path.dirname(_HERE), "web", "out")
_HAS_SPA = os.path.isdir(_WEB_OUT) and os.path.isfile(os.path.join(_WEB_OUT, "index.html"))


# Matches <script> blocks with no src= attribute, i.e. ones with a body.
_INLINE_SCRIPT_RE = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S)

# Route -> (mtime the hashes were derived from, the hashes).
_SPA_CSP_HASHES: dict[str, tuple[float, str]] = {}

_SPA_PAGES: dict[str, str] = {
    "/": "index.html",
    "/compare": os.path.join("compare", "index.html"),
}


def _inline_script_hashes(route: str) -> str:
    """CSP source-expressions for the inline scripts in one exported page.

    Next.js streams its payload through inline <script> blocks, which
    `script-src 'self'` refuses. The usual escapes are a nonce -- impossible
    without a server rendering each response -- or 'unsafe-inline', which
    switches the protection off for every script on the page.

    A static bundle has a third option the other two do not: the scripts are
    fixed bytes on disk, so their hashes can be computed and allowlisted
    exactly. Anything injected later hashes differently and is refused.

    Keyed on the file's mtime rather than computed once at import. Deriving
    the policy from a page and then serving a different page is a silent
    failure -- the browser refuses every script and the screen simply stays
    blank, with the reason buried in a console nobody has open. Restating the
    hashes whenever the file changes costs one stat() per page request and
    makes the failure impossible.
    """
    page = _SPA_PAGES.get(route)
    if page is None:
        return ""
    path = os.path.join(_WEB_OUT, page)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return ""
    cached = _SPA_CSP_HASHES.get(route)
    if cached and cached[0] == mtime:
        return cached[1]
    try:
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
    except OSError:
        return ""
    out = []
    for match in _INLINE_SCRIPT_RE.finditer(html):
        digest = hashlib.sha256(match.group(1).encode("utf-8")).digest()
        out.append(f"'sha256-{base64.b64encode(digest).decode('ascii')}'")
    joined = " ".join(out)
    _SPA_CSP_HASHES[route] = (mtime, joined)
    return joined


if _HAS_SPA:
    # The bundle's own JS and CSS. Everything under /_next/static carries a
    # content hash in its filename, so it is safe to cache hard and for a
    # long time -- a rebuild changes the name rather than the contents at a
    # name. This is the one part of the site that should be cached; the pages
    # and the API are all no-store.
    app.mount(
        "/_next",
        StaticFiles(directory=os.path.join(_WEB_OUT, "_next")),
        name="next-assets",
    )


# ── Security headers middleware ───────────────────────────────────────


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    # Version banners help nobody but a scanner.
    response.headers["Server"] = "kosma"
    script_src = "'self'"
    if _HAS_SPA:
        extra = _inline_script_hashes(request.url.path.rstrip("/") or "/")
        if extra:
            script_src = f"{script_src} {extra}"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self'; "
        # React prerenders Framer Motion's opening state as a style attribute,
        # so the markup carries style="opacity:0;transform:...". Allowing
        # attributes is a much narrower grant than 'unsafe-inline' on
        # style-src, which this deliberately leaves alone: <style> blocks and
        # stylesheets from anywhere but this origin are still refused, and a
        # style attribute cannot execute script.
        "style-src-attr 'unsafe-inline'; "
        f"script-src {script_src}; "
        "connect-src 'self'; "
        "form-action 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none';"
    )
    # Cache: never cache the form or generated PDFs
    if request.url.path in (
        "/",
        "/compare",
        "/generate",
        "/legacy",
        "/legacy/compatibility",
        "/api/chart",
        "/api/compatibility",
        "/api/grounding",
    ):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


# ── Routes ────────────────────────────────────────────────────────────


def _spa(page: str) -> FileResponse:
    """Return one of the exported React pages."""
    return FileResponse(os.path.join(_WEB_OUT, page), media_type="text/html")


@app.get("/", response_class=HTMLResponse)
@limiter.limit("120/hour")
async def index(request: Request):
    # The React client when it has been built, the server-rendered form when
    # it has not. Both talk to the same engine.
    if _HAS_SPA:
        return _spa("index.html")
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "cities": cities.city_names(),
            "year": datetime.now(UTC).year,
        },
    )


@app.get("/compare", response_class=HTMLResponse)
@limiter.limit("120/hour")
async def compare_page(request: Request):
    """The relationship comparison view of the React client."""
    if not _HAS_SPA:
        # Without the bundle this is the server-rendered equivalent.
        return RedirectResponse("/legacy/compatibility", status_code=307)
    return _spa(os.path.join("compare", "index.html"))


@app.get("/legacy", response_class=HTMLResponse)
@limiter.limit("120/hour")
async def legacy_index(request: Request):
    """The no-JavaScript form.

    Kept as a real route, not a relic: it is the only way to use KOSMA with
    scripting disabled, and it is what answers when the frontend has not been
    built. The engine, the gate and the PDF are identical -- only the surface
    differs.
    """
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "cities": cities.city_names(),
            "year": datetime.now(UTC).year,
        },
    )


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.get("/version")
async def version():
    """Public version endpoint for monitoring/uptime checks."""
    return {"app": "KOSMA", "version": __version__}


_GENDERS = frozenset({"female", "male", "other", "unspecified"})


def _validate_gender(value: str) -> str:
    """Constrain gender to a closed set.

    Several kootas are stated in the classical texts as a rule about the
    bride's position relative to the groom's, so the two roles genuinely
    change a compatibility score. Anything outside the set becomes
    "unspecified", which falls back to entry order and says so rather than
    guessing a role for someone.

    Unrecognised input is normalised rather than rejected: this is a field
    about a person, and failing their form because they typed something the
    enum did not anticipate would be the wrong trade.
    """
    v = (value or "").strip().lower()
    return v if v in _GENDERS else "unspecified"


def _validate_birth(birth_date: str, birth_time: str) -> tuple[int, int, int, int, int]:
    try:
        d = date.fromisoformat(birth_date)
    except ValueError:
        raise HTTPException(400, "Invalid birth date.") from None
    try:
        h_str, m_str = birth_time.split(":")
        h, m = int(h_str), int(m_str)
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
    except Exception:
        raise HTTPException(400, "Invalid birth time (expected HH:MM, 24-hour).") from None

    if d.year < 1900 or d.year > datetime.now(UTC).year:
        raise HTTPException(400, "Birth year out of range (1900 to today).")
    return d.year, d.month, d.day, h, m


def _resolve_place(
    city: str | None,
    manual_lat: str | None,
    manual_lon: str | None,
    manual_tz: str | None,
    manual_label: str | None,
) -> tuple[float, float, float, str]:
    if city:
        coords = cities.lookup(city)
        if coords:
            lat, lon, tz = coords
            return lat, lon, tz, city
        # Fall through to manual if dropdown value isn't recognised
    # Manual entry path
    try:
        lat_v: float | None = float(manual_lat) if manual_lat else None
        lon_v: float | None = float(manual_lon) if manual_lon else None
        tz_v: float | None = float(manual_tz) if manual_tz else None
    except ValueError:
        raise HTTPException(400, "Latitude, longitude, and timezone must be numbers.") from None
    if lat_v is None or lon_v is None or tz_v is None:
        raise HTTPException(400, "Choose a city or provide latitude, longitude, and timezone.")
    if not (-90.0 <= lat_v <= 90.0):
        raise HTTPException(400, "Latitude must be between -90 and 90.")
    if not (-180.0 <= lon_v <= 180.0):
        raise HTTPException(400, "Longitude must be between -180 and 180.")
    if not (-14.0 <= tz_v <= 14.0):
        raise HTTPException(400, "Timezone offset must be between -14 and 14 hours.")
    label = (manual_label or "Custom location").strip()[:80]
    return lat_v, lon_v, tz_v, label


def _safe_filename(name: str) -> str:
    base = "".join(
        c for c in (name or "soul-blueprint") if c.isalnum() or c in (" ", "-", "_")
    ).strip()
    base = base.replace(" ", "-").lower() or "soul-blueprint"
    return f"{base[:40]}-blueprint.pdf"


@app.post("/generate")
@limiter.limit("10/hour")
async def generate(
    request: Request,
    name: str = Form("", max_length=80),
    birth_date: str = Form(...),
    birth_time: str = Form(...),
    gender: str = Form("unspecified", max_length=16),
    city: str = Form(""),
    manual_lat: str = Form(""),
    manual_lon: str = Form(""),
    manual_tz: str = Form(""),
    manual_label: str = Form(""),
):
    # Validate inputs (raises HTTPException on failure)
    y, mo, d, h, mn = _validate_birth(birth_date, birth_time)
    name = (name or "").strip()[:80]
    gender = _validate_gender(gender)
    lat, lon, tz, place_label = _resolve_place(
        city.strip() or None,
        manual_lat.strip() or None,
        manual_lon.strip() or None,
        manual_tz.strip() or None,
        manual_label.strip() or None,
    )

    try:
        pdf_bytes = pdf_generator.generate_pdf(
            name=name,
            year=y,
            month=mo,
            day=d,
            hour=h,
            minute=mn,
            lat=lat,
            lon=lon,
            tz=tz,
            place=place_label,
        )
    except Exception:
        # Deliberately *not* logging the exception args — they may include
        # PII from formatting. Log only the type for debugging.
        exc_class = sys.exc_info()[0]
        etype = exc_class.__name__ if exc_class is not None else "Unknown"
        logger.error("pdf_generation_failed type=%s", etype)
        # A traceback carries the exception's own message, and an exception
        # raised while formatting birth data can carry that data in its args.
        # Printing it unconditionally sends that to the platform's log
        # collector. Off unless KOSMA_DEBUG is set.
        if DEBUG:
            traceback.print_exc()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Could not generate the report. Please double-check the birth details.",
        ) from None

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{_safe_filename(name)}"',
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
        },
    )


# ── Compatibility ─────────────────────────────────────────────────────

_MONTHS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def _html_error(request: Request, message: str, back: str) -> HTMLResponse:
    """Render a form error as a page rather than raw JSON.

    The message never contains anything the user typed.
    """
    return templates.TemplateResponse(
        request,
        "error.html",
        {"message": message, "back": back, "year": datetime.now(UTC).year},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def _person_from_form(form, tag: str, index: int) -> tuple[compatibility.Person, dict[str, str]]:
    """Build one Person plus its display row from the submitted form."""
    fallback = f"Person {chr(ord('A') + index)}"
    label = str(form.get(f"{tag}_name") or "").strip()[:60] or fallback
    # Errors name the block by position, never by the name that was typed
    # into it: validation messages must not echo user input back.
    position = ("First", "Second", "Third")[index] if index < 3 else f"Person {index + 1}"

    try:
        y, mo, d, h, mn = _validate_birth(
            str(form.get(f"{tag}_date") or ""),
            str(form.get(f"{tag}_time") or ""),
        )
        lat, lon, tz, place = _resolve_place(
            str(form.get(f"{tag}_city") or "").strip() or None,
            str(form.get(f"{tag}_lat") or "").strip() or None,
            str(form.get(f"{tag}_lon") or "").strip() or None,
            str(form.get(f"{tag}_tz") or "").strip() or None,
            str(form.get(f"{tag}_label") or "").strip() or None,
        )
    except HTTPException as exc:
        raise HTTPException(exc.status_code, f"{position} person — {exc.detail}") from None

    chart = ve.build_chart(
        label=label,
        year=y,
        month=mo,
        day=d,
        hour=h,
        minute=mn,
        lat=lat,
        lon_geo=lon,
        tz=tz,
    )
    moon = chart.planets["Moon"]
    view = {
        "label": label,
        "when": f"{d} {_MONTHS[mo - 1]} {y} · {h:02d}:{mn:02d}",
        "place": place,
        "ascendant": f"{chart.ascendant_sign} {ve.degrees_to_dms(chart.ascendant_deg)}",
        "moon": f"{moon.sign} {ve.degrees_to_dms(moon.deg_in_sign)}",
        "nakshatra": f"{moon.nakshatra} pada {moon.pada}",
    }
    return compatibility.Person(label=label, chart=chart), view


def _dedupe(labels: list[str]) -> list[str]:
    """Make labels unique so pairs stay addressable when names collide."""
    seen: dict[str, int] = {}
    out: list[str] = []
    for label in labels:
        if label in seen:
            seen[label] += 1
            out.append(f"{label} ({seen[label]})")
        else:
            seen[label] = 1
            out.append(label)
    return out


@app.get("/legacy/compatibility", response_class=HTMLResponse)
@limiter.limit("120/hour")
async def compatibility_form(request: Request):
    return templates.TemplateResponse(
        request,
        "compatibility.html",
        {"cities": cities.city_names(), "year": datetime.now(UTC).year},
    )


@app.post("/legacy/compatibility", response_class=HTMLResponse)
@limiter.limit("10/hour")
async def compatibility_compare(request: Request):
    """Compare two or three charts. Same posture as everything else here:
    computed in memory, nothing stored, nothing about the input logged."""
    form = await request.form()

    mode = str(form.get("mode") or "relationship")
    if mode not in compatibility.MODES:
        return _html_error(request, "Unknown comparison mode.", "/compatibility")

    tags = ["a", "b"]
    if str(form.get("include_third") or "no") == "yes":
        tags.append("c")

    try:
        built = [_person_from_form(form, tag, i) for i, tag in enumerate(tags)]
    except HTTPException as exc:
        return _html_error(request, str(exc.detail), "/compatibility")

    labels = _dedupe([p.label for p, _ in built])
    people = [
        compatibility.Person(label=label, chart=person.chart)
        for label, (person, _) in zip(labels, built, strict=True)
    ]
    charts = [dict(view, label=label) for label, (_, view) in zip(labels, built, strict=True)]

    now = datetime.now(UTC)
    now_jd = ve.local_to_ut(now.year, now.month, now.day, now.hour, now.minute, 0.0)

    try:
        if len(people) == 2:
            pairs = [compatibility.compare(people[0], people[1], now_jd, mode)]
        else:
            pairs = compatibility.compare_group(people, now_jd, mode).pairs
    except Exception:
        exc_class = sys.exc_info()[0]
        etype = exc_class.__name__ if exc_class is not None else "Unknown"
        logger.error("compatibility_failed type=%s", etype)
        return _html_error(
            request,
            "Could not compute the comparison. Please double-check the birth details.",
            "/compatibility",
        )

    return templates.TemplateResponse(
        request,
        "compatibility_result.html",
        {
            "pairs": pairs,
            "charts": charts,
            "mode": mode,
            "headline": " · ".join(labels),
            "computed_at": now.strftime("%Y-%m-%d %H:%MZ"),
            "year": now.year,
        },
        headers={"Cache-Control": "no-store, max-age=0", "Pragma": "no-cache"},
    )


@app.post("/api/chart")
@limiter.limit("30/hour")
async def api_chart(
    request: Request,
    name: str = Form("", max_length=80),
    birth_date: str = Form(...),
    birth_time: str = Form(...),
    gender: str = Form("unspecified", max_length=16),
    city: str = Form(""),
    manual_lat: str = Form(""),
    manual_lon: str = Form(""),
    manual_tz: str = Form(""),
    manual_label: str = Form(""),
):
    """The wire contract for a frontend: everything needed to draw the chart.

    Narrower than /api/grounding on purpose. That route exists to hand a model
    the whole evidence picture; this one exists to draw a screen, and keeping
    them apart means the visual layer never pressures the evidence layer.
    """
    y, mo, d, h, mn = _validate_birth(birth_date, birth_time)
    name = (name or "").strip()[:80]
    gender = _validate_gender(gender)
    lat, lon, tz, place_label = _resolve_place(
        city.strip() or None,
        manual_lat.strip() or None,
        manual_lon.strip() or None,
        manual_tz.strip() or None,
        manual_label.strip() or None,
    )

    try:
        payload = api_contract.build_chart_payload(
            name=name,
            year=y,
            month=mo,
            day=d,
            hour=h,
            minute=mn,
            lat=lat,
            lon=lon,
            tz=tz,
            place=place_label,
            gender=gender,
        )
    except Exception:
        exc_class = sys.exc_info()[0]
        etype = exc_class.__name__ if exc_class is not None else "Unknown"
        logger.error("chart_payload_failed type=%s", etype)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Could not compute the chart. Please double-check the birth details.",
        ) from None

    return JSONResponse(
        content=payload,
        headers={"Cache-Control": "no-store, max-age=0", "Pragma": "no-cache"},
    )


@app.post("/api/compatibility")
@limiter.limit("20/hour")
async def api_compatibility(request: Request):
    """Pairwise comparison across two or three charts, as JSON.

    Same posture as every other route here: computed in memory, nothing stored,
    nothing about the input logged.
    """
    form = await request.form()

    mode = str(form.get("mode") or "relationship")
    if mode not in compatibility.MODES:
        raise HTTPException(400, "Unknown comparison mode.")

    tags = ["a", "b"]
    if str(form.get("include_third") or "no") == "yes":
        tags.append("c")

    people: list[dict] = []
    for index, tag in enumerate(tags):
        position = ("First", "Second", "Third")[index]
        label = str(form.get(f"{tag}_name") or "").strip()[:60] or f"Person {chr(65 + index)}"
        try:
            y, mo, d, h, mn = _validate_birth(
                str(form.get(f"{tag}_date") or ""),
                str(form.get(f"{tag}_time") or ""),
            )
            lat, lon, tz, place = _resolve_place(
                str(form.get(f"{tag}_city") or "").strip() or None,
                str(form.get(f"{tag}_lat") or "").strip() or None,
                str(form.get(f"{tag}_lon") or "").strip() or None,
                str(form.get(f"{tag}_tz") or "").strip() or None,
                str(form.get(f"{tag}_label") or "").strip() or None,
            )
        except HTTPException as exc:
            raise HTTPException(exc.status_code, f"{position} person — {exc.detail}") from None
        people.append(
            {
                "label": label,
                "year": y,
                "month": mo,
                "day": d,
                "hour": h,
                "minute": mn,
                "lat": lat,
                "lon": lon,
                "tz": tz,
                "place": place,
            }
        )

    labels = _dedupe([p["label"] for p in people])
    for person, label in zip(people, labels, strict=True):
        person["label"] = label

    try:
        payload = api_contract.build_compatibility_payload(people, mode=mode)
    except Exception:
        exc_class = sys.exc_info()[0]
        etype = exc_class.__name__ if exc_class is not None else "Unknown"
        logger.error("compatibility_payload_failed type=%s", etype)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Could not compute the comparison. Please double-check the birth details.",
        ) from None

    return JSONResponse(
        content=payload,
        headers={"Cache-Control": "no-store, max-age=0", "Pragma": "no-cache"},
    )


@app.post("/api/grounding")
@limiter.limit("10/hour")
async def api_grounding(
    request: Request,
    name: str = Form("", max_length=80),
    birth_date: str = Form(...),
    birth_time: str = Form(...),
    city: str = Form(""),
    manual_lat: str = Form(""),
    manual_lon: str = Form(""),
    manual_tz: str = Form(""),
    manual_label: str = Form(""),
    horizon_years: float = Form(8.0),
):
    """Return the computed grounding pack as JSON.

    This is the interface for an AI layer: it hands over every position,
    dignity, yoga, dasha date, transit window and piece of evidence already
    resolved, so the model interprets rather than calculates. Same privacy
    posture as the PDF route — computed in memory, nothing stored, nothing
    logged.
    """
    y, mo, d, h, mn = _validate_birth(birth_date, birth_time)
    name = (name or "").strip()[:80]
    lat, lon, tz, place_label = _resolve_place(
        city.strip() or None,
        manual_lat.strip() or None,
        manual_lon.strip() or None,
        manual_tz.strip() or None,
        manual_label.strip() or None,
    )
    horizon = max(1.0, min(30.0, float(horizon_years)))

    try:
        pack = grounding.build_pack(
            grounding.BirthInput(
                name=name,
                year=y,
                month=mo,
                day=d,
                hour=h,
                minute=mn,
                lat=lat,
                lon=lon,
                tz=tz,
                place=place_label,
            ),
            activation_years=horizon,
        )
    except Exception:
        exc_class = sys.exc_info()[0]
        etype = exc_class.__name__ if exc_class is not None else "Unknown"
        logger.error("grounding_failed type=%s", etype)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Could not compute the chart. Please double-check the birth details.",
        ) from None

    return Response(
        content=grounding.to_json(pack),
        media_type="application/json",
        headers={"Cache-Control": "no-store, max-age=0", "Pragma": "no-cache"},
    )
