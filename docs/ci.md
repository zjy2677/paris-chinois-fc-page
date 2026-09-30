# Pull request checks

CI runs on every pull request targeting `main` or `dev`, on pushes to those branches,
and through manual dispatch. There are no path filters: required checks always report.
Newer runs cancel superseded runs for the same PR. These workflows validate only; they
never format, auto-fix, deploy, or access production secrets.

## Repository tools

- Backend: `backend/`, FastAPI/SQLAlchemy/Alembic, Python 3.12.
- ETL: `etl/`; parser/load regression tests live in `backend/tests/test_v1.py`.
- Python packages: pip, `backend/pyproject.toml`, production `requirements.lock`, and
  `requirements-ci.lock` for pinned test/lint tooling. No Poetry or uv lockfile.
- Frontend: `frontend/`, TypeScript/React/TanStack Start, Node 22.x, Bun 1.3.14.
- JavaScript packages: existing `frontend/bun.lock`, always installed frozen.
- Python formatting/linting: existing Ruff configuration in `backend/pyproject.toml`.
- Frontend formatting: existing Prettier configuration and `format:check` script.
  dprint is not configured or installed, so CI does not introduce a second formatter.
- Frontend tests: existing Bun-compatible `node:test` suites in `frontend/tests`.
- Existing workflows retained: Alembic graph validation, CodeRabbit review-label gate,
  and the production FLA import. The latter two are not CI quality requirements.

## Required status checks

After pushing this branch and running a PR, select the following exact check names in
GitHub Rulesets -> Require status checks to pass before merging, for both `main` and `dev`.
Use GitHub Actions as the expected source where the UI offers that choice.

| Check name | Command (repository root unless noted) |
| --- | --- |
| `Ruff lint` | `python -m ruff check --config backend/pyproject.toml backend etl scripts` |
| `Ruff format` | `python -m ruff format --config backend/pyproject.toml --check backend etl scripts` |
| `Backend tests` | `python -m pytest backend/tests scripts/tests -q` |
| `alembic-head` | `python scripts/check_alembic_heads.py` and its subprocess regression test |
| `Frontend format` | `cd frontend && bun run format:check` |
| `TypeScript` | `cd frontend && bun run typecheck` |
| `ESLint` | `cd frontend && bun run lint` |
| `Frontend tests` | `cd frontend && bun run test` |
| `Frontend build` | `cd frontend && bun run build` |

`alembic-head` keeps its previous name for existing branch protection rules. The
remaining names come from the explicit job/matrix names, not workflow titles.
Do not require the ETL `import` or CodeRabbit `review-label` jobs: they have different
triggers and responsibilities. Ruleset changes must be made separately in GitHub;
committing this configuration does not alter repository protection settings.

## Database isolation and migration validation

The test job starts an ephemeral PostgreSQL 16 service with the database `paris_ci_test`.
Its trust authentication is restricted to the disposable CI environment. No Neon URL,
production password, JWT signing secret, or GitHub environment is used. Auth fixtures
set their own test-only JWT keys. Both database variables target the temporary service;
the `_test` suffix satisfies existing destructive-test guards.

The job applies `alembic upgrade head` before pytest. Tests run sequentially because
some ETL cases intentionally persist fixtures across assertions. The graph check uses
Alembic's `ScriptDirectory.get_heads()` and exits 1 unless there is exactly one head;
it needs no database. Its regression test creates temporary empty, single-head,
two-head, and merged graphs and verifies actual subprocess exit codes.

## Dependency installation and speed

Python jobs cache pip downloads. Ruff jobs install only pinned Ruff; the graph job
installs Alembic constrained by the existing runtime lock; only the test job installs
the full backend. Frontend jobs share a Bun download cache keyed by the lockfile and
manifest and use `bun install --frozen-lockfile`. Each isolated runner still installs
its own dependencies; no mutable virtualenv or platform-specific node_modules archive
is shared between runners. Matrix jobs use `fail-fast: false` so one failure does not
hide other results. All jobs have timeouts and read-only repository permissions.

## Local verification of the initial setup

Validated with Python 3.12.13, Node 22.23.3, Bun 1.3.14, and a fresh local PostgreSQL
database: Ruff lint and format, 60 pytest tests (none skipped), single-head validation
including the multiple-head failure case, Prettier, TypeScript, ESLint, 13 frontend
tests, and the production frontend build. actionlint 1.7.7 validates both changed
workflow files; optional ShellCheck integration was disabled because it is not installed.

Existing style-only violations were normalized locally so the new checks start green.
No application behavior was changed. Existing non-failing warnings remain: React Fast
Refresh export warnings and Starlette's test-client deprecation warning.

A hosted GitHub Actions run and Linux-specific dependency installation remain to be
verified after pushing/opening a PR. The CI branch has not been merged or deployed.
