# Agent toolchain

The tools an AI agent working on this repository is expected to have, what
each is for, and the order they take precedence in when more than one has an
opinion. Everything here is installed globally, so it applies to other
projects too; only `kosma-voice` and the Playwright workspace are specific to
this one.

## What is installed

| Tool | Kind | Scope | Use it for |
| --- | --- | --- | --- |
| `playwright-cli` | CLI + skill | global and project | Driving a real browser: page snapshots, console and network capture, interaction |
| `context7` | MCP server | global | Current library and framework documentation, instead of recalling an API from memory |
| `skillui` | CLI | global | Extracting a design system from a site, repo or local directory |
| Supabase plugin | plugin | global | Supabase projects. Not this one, see below |
| `strix` | 4 skills | global | Pentesting, remediation, CI security scanning |
| `humanizer` | skill | global | Removing AI writing patterns from any prose |
| `kosma-voice` | skill | project | How reader-facing text in KOSMA has to read |
| `emilkowal-animations` | skill | global | Interface animation: easing, transitions, gestures |
| `impeccable-design-polish` | skill | global | Auditing and polishing a page that already exists |
| `design-with-taste` | skill | global | Simplicity, fluidity and delight as design principles |

## Precedence

Five of these will happily give advice about the same paragraph or the same
component. Without an order they argue, and the result is text that has been
rewritten four times and reads worse than the first draft.

**Prose.** `kosma-voice` wins, then `humanizer`. The project skill sets the
information order and the honesty rules, and the humanizer removes AI tells
from whatever the project skill produced. If they disagree, the project skill
is more specific and is right. Both ban em dashes, so that never comes up.

**Interface.** `design-with-taste` for what to build, `emilkowal-animations`
for how it moves, `impeccable-design-polish` for the pass after it exists.
They apply at different stages, so run them in that order rather than all at
once.

**Nothing overrides the gate.** No design or writing skill may soften what
`kosma/evidence.py` refuses to claim, move a withheld house into a reading, or
turn a citation into a flourish. A prettier sentence that asserts more than
the chart supports is a defect, not an improvement.

## Credentials

None of these have credentials stored in the repository, and none should.

- **Strix** needs `STRIX_LLM` and `LLM_API_KEY` in the environment before it
  will run. Set them in your shell, never in a tracked file.
- **Context7** is authenticated already; the key lives in `~/.claude.json`,
  outside this repository.
- **Supabase** needs a project ref and access token when it is first used
  against a real project.

## Supabase is installed but does not apply here

KOSMA has no database, and that is a stated privacy guarantee rather than an
omission: birth data is computed in memory and discarded, and `SECURITY.md`
commits to the server having nowhere to put it. Adding a database to this
project would break that promise, so the Supabase plugin is present for other
work and should not be used to add persistence here.

## Playwright earned its place immediately

The first run against a local instance reported one console error on a page
that had already passed a manual review: `/favicon.ico` returned 404. Nothing
linked to it, so it was invisible in the source, but browsers request it
unprompted and every visitor was logging an error before they had done
anything.

Fixing it surfaced a worse bug. The route added to serve root-level files from
the exported bundle used a single-segment path parameter, and FastAPI matches
in definition order, so `/{filename}` swallowed `/healthz` and `/version`.
That is the path Render polls to decide whether a deploy is live, so the
deploy would have come up and been marked unhealthy. Both the ordering and the
traversal refusal are now asserted in `tests/test_privacy.py`.

Use it before calling a page finished:

```bash
playwright-cli -s=kosma open http://127.0.0.1:8000/
cat .playwright-cli/console-*.log
```

Session artefacts land in `.playwright-cli/`, which is git-ignored.
