# Security Policy

KOSMA handles birth data, which many users consider sensitive. We treat
security and privacy as first-class concerns. This document explains how to
report a vulnerability and what we promise in return.

## Supported versions

Only the `main` branch and the latest tagged release receive security fixes.

## Reporting a vulnerability

**Please do not open a public GitHub issue for a security report.**

Use one of:

1. **GitHub Private Vulnerability Reporting**:
   open `Security` -> `Report a vulnerability` on this repository.
2. **Email**: `security@kosma.invalid` (replace with a real address before
   you publish the project).

Include:

- A description of the issue and the impact you have demonstrated.
- A minimal reproduction (request body, command, or PoC).
- Any relevant logs, screenshots, or stack traces (scrubbed of personal data).
- Your name and how you would like to be credited, if at all.

## What we promise

- We will acknowledge your report within **72 hours**.
- We will publish a fix as a release within **30 days** of confirmation, or
  a public mitigation if a full fix needs longer.
- Researchers reporting in good faith are welcome to credit in the
  `CHANGELOG.md` and the release notes.
- We will not pursue legal action against good-faith research that:
  - Stays within the scope of the public, hosted KOSMA service or this
    source code.
  - Avoids exfiltrating, storing, or sharing any personal data of other
    users.
  - Avoids degrading service for other users.

## Threat model summary

What KOSMA tries hard to prevent:

- **Persistence of birth data.** The server has no database. Birth data
  flows through one request handler, into a PDF in memory, and out as the
  HTTP response body. Nothing is written to disk.
- **Disclosure of birth data via logs.** Form contents and exception
  arguments are not logged. Only request method, path, status, and
  exception type may be visible.
- **Accidental exposure via auto-generated docs.** `/docs`, `/redoc`, and
  `/openapi.json` are disabled.
- **Cross-frame embedding.** `X-Frame-Options: DENY` and CSP
  `frame-ancestors 'none'` block clickjacking.
- **External resource loading.** CSP `default-src 'self'` blocks
  third-party scripts, styles, fonts, and images.
- **Birth-location leakage to third parties.** The city -> coordinates
  table is embedded; no geocoding API is contacted.

What KOSMA does **not** protect against (and you must handle in your
deployment):

- Network observers between the client and the KOSMA server. **Always**
  terminate TLS at your reverse proxy or platform; the app does not.
- A malicious or compromised KOSMA host that records traffic out of band.
- Misconfigured access logs at the platform level. Pass
  `--no-access-log` to uvicorn or scrub IPs at the platform if you treat
  IPs as personal data.
- Side-channels like timing attacks against the rate limiter.
