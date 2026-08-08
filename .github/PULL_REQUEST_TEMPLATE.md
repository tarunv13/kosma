<!--
Thanks for your contribution. Please fill the sections below so reviewers
can move quickly.
-->

## What does this change do?

<!-- One or two sentences. Reviewers should understand the intent without
needing to read the diff first. -->

## Why?

<!-- The problem you're solving, with a link to an issue if there is one. -->

## How was it tested?

- [ ] `ruff check .` passes
- [ ] `ruff format --check .` passes
- [ ] `mypy kosma` passes
- [ ] `pytest` passes locally
- [ ] `python scripts/smoke_test.py` passes (if engine touched)
- [ ] `python scripts/smoke_http.py` passes (if HTTP layer touched)

## Privacy / Security checklist

- [ ] No new persistence of birth data (no DB, files, or external API calls).
- [ ] No new logging of form contents or PII.
- [ ] Security headers and rate limits unchanged (or strengthened).

## Astrology checklist (engine changes only)

- [ ] Updated or added a deterministic test in `tests/`.
- [ ] Cited the rule (Parashari, BPHS, KP literature) in code or commit.

## Screenshots / sample PDFs

<!-- Drag images here, if relevant. -->
