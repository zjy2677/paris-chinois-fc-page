# Backend and ETL v1

## R2 photo cleanup and rollback

Uploads use a new object key for every version. The database commits the new photo
reference before the previous object is removed. Failed database writes compensate
by deleting the new upload. Failed object deletions remain in `storage_deletions`,
including when R2 is temporarily disabled and an upload falls back to database bytes.
Changing a player's photo to an external URL uses the same cleanup queue.

After restoring R2 access, run from the repository root with the backend environment:

```sh
backend/.venv/bin/python -m app.photo_storage
```

This retries up to 100 pending deletions; repeat until `storage_deletions` is empty.
Normal requests attempt only their own cleanup, and do not scan unrelated bucket objects.
If both the database and R2 are unavailable during upload compensation, the exact orphan
keys are logged for manual cleanup. A process crash between PUT and commit can also leave
an orphan; reconcile bucket inventory against all three photo tables before removing it.

### R2 rollback

Pause photo writes and back up the database before downgrading. Restore every photo's
`data` bytes from its `storage_key` in R2 for `media_assets`, `player_photos`, and
`user_avatars`, verifying content type, image integrity, and size before committing.
Keep the R2 objects until the restored application is verified. Drain pending deletions
before downgrading the cleanup migration. The R2 migration deliberately refuses to
downgrade while any photo has NULL `data`; it never silently drops R2-only photos.

Production `R2_ENDPOINT_URL` must use HTTPS. Storage credentials remain backend-only.

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

Authentication and protected upload routes are enabled. Image uploads use Cloudflare R2 when all
R2 variables are configured; existing database-backed image rows remain readable as a migration
fallback. Without R2 configuration, local development keeps storing image bytes in PostgreSQL.
Playback URLs, object storage for uploaded videos, admin workflows and scheduling are subsequent
steps. Home, League and match detail pages read the API. League sample data has been removed;
squad records remain illustrative until verified player data is supplied.

### Cloudflare R2 image storage

Create a bucket-scoped R2 API token with Object Read and Write access, then set these Render
environment variables. Keep the access key and secret on the backend only; they must never be
prefixed with `VITE_` or committed:

```text
R2_ENDPOINT_URL=https://ACCOUNT_ID.r2.cloudflarestorage.com
R2_BUCKET_NAME=your-bucket-name
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
```

The API stores only an object key for new media, player photos and avatars. Public response URLs
still go through the existing API authorization checks, while legacy rows with `data` continue to
serve directly from PostgreSQL. Apply the R2 migration before enabling the variables:

```sh
backend/.venv/bin/alembic -c backend/alembic.ini upgrade head
```

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

## Match goals and assists

`match_goals` stores one row per goal, linked to `matches`, the credited `teams` row,
and optional scorer/assist `players` rows. Player references are not user accounts.
Players with historical goals should be marked inactive rather than deleted; the foreign
keys restrict deletion. Deleting a match also deletes its goal records.

Run `alembic upgrade head` from `backend/` before starting the updated API. The new
revision is `f0ad5f64a5bd`, following `1a2b3c4d5e6f`.

| Method | Endpoint | Access |
| --- | --- | --- |
| GET | `/api/matches/{match_id}/goals` | Public |
| POST | `/api/matches/{match_id}/goals` | Admin |
| PATCH | `/api/matches/{match_id}/goals/{goal_id}` | Admin |
| DELETE | `/api/matches/{match_id}/goals/{goal_id}` | Admin |

`GET /api/matches/{match_id}` also includes `goals`, with nested `scorer` and
`assist_player` objects containing each player's ID and display name. Known times sort
first, with unknown times last. Existing match and video fields are unchanged.

Example POST body (replace placeholders with existing UUIDs):

```json
{
  "team_id": "credited-team-uuid",
  "scorer_id": "player-uuid",
  "assist_player_id": "another-player-uuid",
  "minute": 45,
  "stoppage_minute": 2,
  "goal_type": "regular"
}
```

Only `team_id` is required. `goal_type` defaults to `regular`; other supported values are
`penalty` and `own_goal` (penalty shootouts are not included). The team must be one of the
match's two teams. For an own goal, `team_id` is the team awarded the goal and `scorer_id`
is the player who scored against their own team, if known; assists are forbidden.
A scorer cannot assist their own goal. Unknown scorers, assists, and times can remain null.
There is no player-to-team roster validation yet because the current player/squad schema
does not associate players with team IDs.

PATCH accepts only fields being changed; explicit null clears an optional field. For
example, `{"assist_player_id": null}` removes an assist. `team_id` and `goal_type` cannot
be cleared. Partial updates validate the resulting complete record. A goal ID belonging
to another match returns 404.

Manual check: log in as an admin, send POST from the allowed frontend origin with the
session cookie, check the goal in GET match details, PATCH its minute or assist, then
DELETE it. Repeat writes as a `user` or `player` to verify 403; signed-out requests return
401. Browser writes require `credentials: "include"` and the existing trusted-origin
protection. No frontend editing controls are added in this backend step.

FLA imports continue to own match scores; they do not modify goal records. Recorded
goals may be incomplete and are not required to equal the official score. Future player
goal totals must exclude `own_goal` rows.

Regression tests against a migrated disposable PostgreSQL database:

```sh
TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost/club_test \
  .venv/bin/pytest -q tests/test_goals.py
```

## Squad player management

The Team page reads `GET /api/players?season=2026/2027` rather than bundled sample
players. It shows an empty state until real players are added. Sign in as an admin and
open `/team` to add, edit, deactivate, or restore players. All form text is available in
French, English, and Chinese.

| Method | Endpoint | Access |
| --- | --- | --- |
| GET | `/api/players?season=2026/2027` | Public, active players only |
| GET | `/api/admin/players?season=2026/2027` | Admin, includes inactive players |
| POST | `/api/players` | Admin |
| PATCH | `/api/players/{player_id}?season=2026/2027` | Admin |
| DELETE | `/api/players/{player_id}` | Admin, deactivates the player |

Example POST body:

```json
{
  "display_name": "Zhang Wei",
  "chinese_name": "张伟",
  "season": "2026/2027",
  "position": "Midfielders",
  "shirt_number": 8,
  "photo_url": "https://your-image-host.example/player.jpg"
}
```

Both `display_name` (English name) and `chinese_name` are required when creating a
player. Names are trimmed, must not be blank, and are limited to 150 characters.
The Chinese interface uses `chinese_name`; French and English use `display_name`.
Legacy players without a Chinese name fall back to their existing English name.
Admins can add the missing name through the player form. Existing players without a
Chinese name can still have other details edited; leaving that field blank preserves
the missing name. New players require both names, and an existing Chinese name cannot
be cleared.

`photo_url` and `shirt_number` are optional. Photos must use a public HTTPS image link
without embedded credentials; the frontend displays a silhouette if absent or broken.
This feature stores a link, not an uploaded image. Positions are `Goalkeepers`,
`Defenders`, `Midfielders`, or `Forwards`. A shirt number must be a positive integer
and unique within the season, including inactive players; conflicts return 409.

PATCH accepts only changed fields. Use null to clear the photo or shirt number, or
`{"active": true}` to restore a player. Either name can be updated independently;
explicit null or blank names are rejected. The names, photo, and active status belong
to the permanent `players` record; position and shirt number belong to that season's
`squad_memberships` record. Deactivation applies across seasons and preserves historical
goals and assists. User accounts and player records remain separate; adding a player
does not grant an account the player role. Migration `d4e5f6a7b8c9` adds the nullable
`players.chinese_name` column after `c3d4e5f6a7b8`, preserving existing English names.
Deploy the backend migration before the frontend that submits both names.

Writes use the existing admin dependency, trusted-origin check, session cookie, and
rate limit. Test manually by adding a player as an admin, refreshing the public Team
page, editing their number/photo, deactivating them, then enabling Show inactive players
to restore them. Regular users and players cannot access management endpoints (403);
signed-out requests return 401.

Run `tests/test_players.py` against a migrated disposable PostgreSQL database using
`TEST_DATABASE_URL` as shown above. Tests cover CRUD, preserved history, role and origin
checks, season filtering, optional-field clearing, invalid input, and shirt conflicts.

## Individual player profiles

`/team/player_<UUID>` is a public frontend route linked from each squad card.
`GET /api/players/{player_id}` returns public player fields, description, all season
memberships (newest first), and recorded career goal/assist counts. Inactive players
remain accessible through their permanent profile links so historical records still
make sense. No account email, password, or other private user information is returned.

Goal totals count regular and penalty goal events, excluding own goals. Assist totals
count the associated assist events. Totals span all recorded matches and seasons and
update when goal events are edited or deleted. They are not inferred from match scores;
incomplete club-entered events produce incomplete totals. Membership joins do not
multiply event counts.

Admins can set or clear `description` through the existing POST/PATCH player endpoints
and player form. It is optional plain text, limited to 2,000 characters and rendered
without HTML. Interface labels are translated in all three languages; the description
is displayed as entered by the club.

Run `alembic upgrade head` before deploying this change. Revision `b7c8d9e0f123` adds
the nullable `players.description` column after `f0ad5f64a5bd`, retaining a single head.

### Rolling back manual match records

Migration `ef4050607080` cannot be downgraded while manual matches, source-free
competition seasons, or teams without FLA IDs exist. It checks this before dropping
records and refuses with an actionable error. Export and reconcile these rows and
their dependent data explicitly before retrying. The downgrade does not silently
delete manual matches or teams. As with other schema rollbacks, export match reports
and events before dropping their tables.

## Private API documentation

`/docs`, `/redoc`, and `/openapi.json` require HTTP Basic authentication using an
existing active admin account's email (the browser's username field) and password.
Use HTTPS in deployment. Regular users and players cannot access documentation.
Responses are not cached; login attempts share the existing per-process throttle.
No additional secret or migration is required. Browser Basic credentials may remain
cached until the browser session is closed; use a private window on shared devices.

This protects documentation only. Public data endpoints remain public, and existing
API authorization is unchanged. Documentation login does not create an API session
or grant Swagger's requests permission to perform admin mutations.
