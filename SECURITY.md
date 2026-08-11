# Security Policy

KOSMA handles birth data, which many users consider sensitive. We treat
security and privacy as first-class concerns. This document explains how to
report a vulnerability and what we promise in return.

## Supported versions

Only the `main` branch and the latest tagged release receive security fixes.

## Reporting a vulnerability

**Please do not open a public GitHub issue for a security report.**

Use **GitHub Private Vulnerability Reporting**: open the `Security` tab on
this repository and choose `Report a vulnerability`. The thread stays private
between you and the maintainers until a fix ships, and it needs no account
beyond the GitHub one you are already using.

There is deliberately no email address here. This file previously listed
`security@kosma.invalid`, a placeholder that survived into the public
repository, so anyone who followed it would have reported a vulnerability into
a mailbox that does not exist. A single working channel is better than two
where one is a dead end.

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

## Accepted findings

Findings that a scanner will report and that we have examined and chosen not
to act on. Each is recorded here so the decision is reviewable rather than
forgotten.

### `sharp` (GHSA-f88m-g3jw-g9cj, 3 high): not exposed

`npm audit` reports libvips CVEs in `sharp`, reachable only as a transitive
dependency of `next`. Remediation requires `next@16`, a breaking major
upgrade.

The vulnerable code cannot execute in this deployment:

- `sharp` backs Next's image optimiser, and `next.config.mjs` sets
  `images: { unoptimized: true }`, so it is not invoked during the build.
- The client is a static export. The runtime container copies only
  `web/out`, which contains HTML, CSS, JS, text and a font, with no native
  binaries. There is no Node runtime and no `node_modules` in the final
  image at all.

Exploiting it would require the ability to influence the build, which means
write access to the repository. Anyone with that can do considerably worse
than reach an image decoder.

This is reassessed whenever the frontend moves off a static export, or
whenever `images.unoptimized` is turned off. Either change makes the finding
live and the upgrade necessary.

## Verified posture

Checked against a running instance rather than read off the source, most
recently on 11 August 2026:

- One `Server: kosma` header and no version banner. uvicorn writes its own
  banner beneath ASGI, where middleware cannot replace it, so the container
  also runs with `--no-server-header`.
- `Strict-Transport-Security: max-age=31536000`, without `preload` or
  `includeSubDomains`. Both are hard to reverse and neither is safe to assert
  for a custom domain that does not exist yet.
- CSP with `object-src 'none'`, `frame-ancestors 'none'`, `base-uri 'self'`
  and `connect-src 'self'`. `script-src` carries per-file SHA-256 hashes for
  the exported bundle's inline scripts and never `'unsafe-inline'`.
  `'unsafe-inline'` appears only under `style-src-attr`, which cannot execute
  script.
- Rate limiting enforced: 13 requests to `/generate` returned ten 200s
  followed by three 429s, against a declared limit of 10/hour.
- Validation errors do not echo the submitted value. A script tag sent as a
  name, a date and a city produced `{"detail":"Invalid birth date."}`, and the
  server-rendered error path likewise reflected nothing.
- Rate-limit buckets are keyed by a salted BLAKE2b digest, so the client
  address is not retained in process memory.
- `/docs`, `/redoc` and `/openapi.json` all return 404.
- No known vulnerabilities in the Python runtime dependencies.

Each of these is pinned by a test in `tests/test_privacy.py`, so the posture
fails the build rather than eroding quietly.
