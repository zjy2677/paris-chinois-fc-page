# Backend and ETL v1

FastAPI serves PostgreSQL records. SQLAlchemy models define tables; Alembic owns schema
changes. `app/routers.py` handles HTTP, `app/schemas.py` defines public payloads,
`app/services.py` contains queries, and `app/database.py` supplies a session per request.
These small modules can become feature folders when their size warrants it.

## Local setup (from repository root)

```sh
python3 -m venv backend/.venv
backend/.venv/bin/pip install -e './backend[dev]'
# Existing local container: paris-fc-v1-postgres, port 55432.
# On a new machine, start a development PostgreSQL instance, then:
cp backend/.env.example backend/.env
# Set DATABASE_URL to that database; never commit .env.
backend/.venv/bin/alembic -c backend/alembic.ini upgrade head
backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs. GET `/api/health` checks the server and GET `/api/ready`
checks the database. App import never migrates. The Render startup script explicitly runs migrations before Uvicorn; see [deployment setup](../docs/deployment.md).

## Manual import

```sh
backend/.venv/bin/python -m etl.main
backend/.venv/bin/python -m etl.main --write
# Reproducible offline import from saved source excerpts:
backend/.venv/bin/python -m etl.main --standings-file etl/tests/fixtures/standings.html --fixtures-file etl/tests/fixtures/fixtures.html
```

The default is a dry run. Live fetches check robots directives, use request timeouts,
a response-size limit and bounded network retries. Review source terms/permission before
unattended operation; robots directives alone do not establish reuse permission.
Source configuration and reviewed aliases live in `etl/config.py`.

Both sources must validate before a write. One transaction publishes fixtures and a full
standings snapshot; a failed import retains previous data. Identical standings do not create
another snapshot. A separate sync log records success/failure. PostgreSQL advisory locking
prevents concurrent writes. Existing fixtures are updated, never deleted. Source identity
includes teams, round and leg, but not kickoff: round/opponent corrections require manual
reconciliation. The configured Friday cup is imported alongside league fixtures. Cup source IDs are
kept separate from championship IDs; group-stage fixtures have no invented matchday. The V/N/D result marker resolves
club-relative scores; ambiguous results fail closed. Recorded fixture excerpts contain
public football data only and are for regression tests, not a production data seed.

## Available endpoints

- `GET /api/matches`: optional team_id, competition_season_id, status; offset/limit (max 100).
- `GET /api/matches/{uuid}`: match detail; only ready video metadata, no storage keys.
- `GET /api/standings`: optional competition_season_id; source URL and sync timestamps.
- `GET /api/players?season=2026/2027`: verified active squad records; empty until populated.
- `POST /api/contact-messages`: validated storage, disabled by default. Add spam protection
  before setting CONTACT_ENABLED=true on a public deployment. No public inbox or email delivery.

Authentication routes are enabled. Upload routes remain pending. Playback URLs, object storage, admin workflows, scheduling are subsequent steps. Home, League and match detail pages read the API. League sample data has been removed;
squad records remain illustrative until verified player data is supplied.

## Validation

Use a separate migrated PostgreSQL database whose name ends in `_test`:

```sh
DATABASE_URL="$TEST_DATABASE_URL" backend/.venv/bin/alembic -c backend/alembic.ini upgrade head
backend/.venv/bin/python -m pytest backend/tests -q
backend/.venv/bin/ruff check --config backend/pyproject.toml backend etl
backend/.venv/bin/ruff format --config backend/pyproject.toml --check backend etl
backend/.venv/bin/alembic -c backend/alembic.ini check
```

Export TEST_DATABASE_URL first. Database tests skip if it is unset. Tests exercise real
PostgreSQL constraints, repeated imports, reschedules/results, transactional rollback,
parser rejection and API pagination/404/empty responses. Use only the disposable test DB
for migration downgrade/upgrade checks; downgrade removes tables and their data.

## Frontend connection

Vite proxies `/api` to `http://127.0.0.1:8003` during local development. Run the API
on port 8003 when using the frontend. For deployment, leave VITE_API_BASE_URL empty and configure the Vercel API_ORIGIN
proxy; add the frontend origin to backend CORS_ORIGINS.
League data has no mock fallback. React Query caches responses for one minute; refresh
or revisit after an ETL run to see new data. Match links use stable database UUIDs.

## Accounts and JWT authentication

- POST `/api/auth/register`: first_name, last_name, age (integer 1–120), email,
  password and confirm_password (matching, 12–256 characters).
  Always creates `user`; a role field is rejected. Returns the account and signs in
  immediately through the HttpOnly session cookie. No confirmation email is sent.
- POST `/api/auth/login`: email and password.
- GET `/api/auth/me`: current ID, email, role, first/last name and age_at_registration, or 401.
- POST `/api/auth/logout`: revokes the server session and clears the cookie.

Passwords are Argon2id hashes. JWTs use HS256 with fixed issuer/audience, issued/expiry
claims and a random session ID. The browser receives the JWT only in an HttpOnly,
SameSite=Lax cookie scoped to `/api`; it is never put in localStorage or response JSON.
The database stores only its hash, and validates active users, session expiry and revocation
on each request. Default session duration is eight hours; users log in again after expiry.
Roles are read from the database, not trusted from browser input or cached JWT claims.

Set JWT_SECRET to a cryptographically random value of at least 32 characters. Keep it in
backend/.env locally or provider secrets in deployment. Never commit it. Set
AUTH_COOKIE_SECURE=true on HTTPS. Local HTTP development uses false. CORS_ORIGINS must
list the exact frontend origins; every authentication POST requires a matching Origin
header to prevent cross-site cookie mutations. For command-line API tests include
`Origin: http://localhost:4173`. The intended deployed frontend/API subdomains must share
the same site for SameSite=Lax; cross-site provider preview domains need a same-origin proxy.

### Owner-controlled role grants

The person operating the server/database can grant roles with this command, from repository
root, after the account is registered:

```sh
backend/.venv/bin/python -m app.auth.manage person@example.com player
backend/.venv/bin/python -m app.auth.manage owner@example.com admin
# Revoke an elevated role:
backend/.venv/bin/python -m app.auth.manage person@example.com user
```

Role changes revoke existing sessions, requiring a fresh login. No public HTTP endpoint,
registration selector or account menu can grant roles. Access to this command is controlled
by access to the server and database credentials; keep that access with the owner.
Future protected endpoints use `Depends(require_role("admin"))` or an explicit list of allowed
roles. An admin role does not currently add an admin dashboard or upload controls.

### MVP boundaries

Email verification is currently disabled. Registration and login require no email provider.
Email ownership is not checked; do not treat an email address as proof of identity.
The nullable email_verified_at field is retained for future verification and is not
populated by registration or login. Existing accounts retain passwords and roles.
Age is stored as age_at_registration, not represented as a forever-current age.
Passwords and confirmation text are never stored in plaintext.

Deploy the profile migration with the backend before deploying the registration UI.

Password-reset email delivery remains unavailable. Rate limiting allows
10 auth mutation attempts per IP per minute per process, using bounded memory. Before
multiple workers or public deployment, use a shared/edge rate limiter and configure trusted
proxy addresses. HTTPS, restricted database access and a production secret are required.
