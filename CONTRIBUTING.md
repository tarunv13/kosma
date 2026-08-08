# Contributing to KOSMA

Thanks for considering a contribution. KOSMA is small, focused, and tries
hard to keep birth data private. The bar for changes is correctness,
clarity, and not regressing the privacy posture.

## Development setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# install pre-commit hooks
pre-commit install
```

## Useful commands

```bash
ruff check .            # lint
ruff format .           # format
mypy kosma              # type check
pytest                  # run tests
pytest --cov=kosma      # with coverage

# end-to-end smoke checks
python scripts/smoke_test.py
python scripts/smoke_http.py

# run the dev server
uvicorn kosma.main:app --reload --port 8000
```

## Branching

- Branch from `main`. Use a descriptive name like `feat/d9-chart-svg` or
  `fix/dst-edge-case`.
- One logical change per PR. Refactors are welcome but should not ride
  inside a feature commit.
- Keep commit messages in the imperative mood ("add D9 chart", not
  "added D9 chart").

## What we will and will not accept

We will gladly review:

- Astrological correctness fixes (with a reference to the calculation rule
  or a known-good chart).
- Privacy or security hardening.
- Tests, type hints, and documentation.
- Performance work that is measured.

We will close without merging:

- Any change that adds analytics, tracking, third-party calls, or persistence
  of birth data without an explicit opt-in.
- Code that increases the runtime attack surface (e.g. enabling `/docs`
  in production, dropping security headers).
- Style-only churn against currently passing `ruff format`.

## Astrology checklist for engine changes

When you change `kosma/vedic_engine.py`:

- Add or update a test in `tests/test_engine.py` that asserts a known-good
  chart placement to within 0.1 degree.
- Cite the rule (Parashari, BPHS chapter, KP literature, etc.) in the
  commit message or docstring.
- If the change shifts existing positions, regenerate
  `scripts/smoke_test.py` expectations.

## Privacy checklist for HTTP changes

When you change `kosma/main.py`:

- Confirm form contents are not logged (no `logger.info(form)` etc.).
- Confirm exception messages do not echo birth data.
- Confirm `Cache-Control: no-store` is set on form and PDF responses.
- Confirm CSP, `X-Frame-Options`, and `Referrer-Policy: no-referrer` are
  still emitted.

## Releasing

Maintainers tag a release after merging:

1. Bump `__version__` in `kosma/__init__.py` and the `version` in
   `pyproject.toml`.
2. Update `CHANGELOG.md` (Keep a Changelog format, Semantic Versioning).
3. Tag `vMAJOR.MINOR.PATCH`, push, and let CI build.

## Branch safety

GitHub does not enforce branch protection or rulesets on a **private**
repository under a free personal account — both settings pages say so
outright. Configuring a rule there would look like protection while doing
nothing, so this repository ships a local guard instead:

```bash
git config core.hooksPath scripts/githooks
```

`scripts/githooks/pre-push` refuses a force-push or a delete of the default
branch. It is not a server-side guarantee — `--no-verify` skips it and it does
not apply to anyone else's clone — but it stops the realistic failure for a
solo maintainer, which is force-pushing the default branch by accident.

For real enforcement you need either GitHub Pro (protection on private repos)
or a public repository (protection is free there).

## Privacy checks

`tests/test_privacy.py` fails the build if a personal reading is committed to
`docs/`, if real birth data reappears in tracked source, if the rate limiter
starts keying on raw IP addresses again, or if generated PDFs regain an
embedded timestamp. Those were all real leaks once; the tests exist so they
cannot come back quietly.
