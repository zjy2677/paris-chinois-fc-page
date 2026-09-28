# Minimal backend implementation plan

Status: backend/ETL v1 implemented locally (2026-09-28). SQLAlchemy, one initial
Alembic migration, public read endpoints, gated contact storage, and manual FLA imports
are available. Storage uploads,
scheduling and deployment remain pending. See backend/README.md for commands.

This plan is the current MVP scope. The larger schema in backend-design.md is an earlier
design exploration, not a requirement to create all of those tables.

## Goal and data flow

Build one Python FastAPI API, one PostgreSQL database, and one independent Python ETL job.

FLA pages -> ETL -> PostgreSQL <- FastAPI <- frontend
Admin browser -> signed upload -> object storage
FastAPI verifies the upload -> publishes video metadata in PostgreSQL
Public match page -> ready video playback

The ETL writes league records directly to PostgreSQL. FastAPI serves stored data to the
frontend; it does not fetch FLA when a visitor opens a page.

Sources:
- Fixtures/results: https://football-loisir-amateur.fr/teams/322
- Standings: https://football-loisir-amateur.fr/championships/14?season=2

Keep source team 322, championship 14 and season 2 in configuration.
The source season ID is not the human-readable season label.

## Repository responsibilities

- frontend/: existing website.
- backend/: API, database models, migrations and API tests.
- etl/: source download, parsing, validation, database loading and ETL tests.
- docs/: design and implementation instructions.

Target layout (larger feature modules can be split when needed):

    backend/
      pyproject.toml
      .env.example
      app/
        __init__.py
        main.py
        config.py
        database.py
        models.py
        dependencies.py
        storage.py
        routers/
          league.py
          squad.py
          contact.py
          auth.py
          videos.py
        schemas/
          league.py
          squad.py
          contact.py
          auth.py
          videos.py
        services/
          league.py
          squad.py
          contact.py
          auth.py
          videos.py
      alembic.ini
      migrations/
      tests/
    etl/
      __init__.py
      main.py
      config.py
      fetch.py
      parse_fixtures.py
      parse_standings.py
      load.py
      tests/
        fixtures/

Use one Python dependency manifest initially in backend/ for API and ETL dependencies.
Run ETL from repository root as python -m etl.main in the same environment.
Install the backend package in that environment so ETL can reuse its database models;
do not maintain a second ORM schema or modify sys.path to make imports work.
Alembic under backend/ is the only owner of database schema changes.

Start with synchronous SQLAlchemy and psycopg. Use normal def FastAPI handlers for blocking
database calls. Async engines, repository abstractions and background queues are unnecessary.

## Database scope: 14 tables, introduced incrementally

| Table | Minimum fields |
| --- | --- |
| teams | id, fla_team_id (unique), name, short_name, logo_url |
| competition_seasons | id, fla_championship_id, fla_season_id, competition_name, division, season_label |
| venues | id, fla_venue_id (nullable), name, address, timezone |
| matches | id, fla_match_id (unique when available), competition_season_id, home_team_id, away_team_id, venue_id, matchday, kickoff_at, status, home_score, away_score, source_url, last_synced_at |
| standings_snapshots | id, competition_season_id, sync_run_id, source_url, fetched_at, content_hash |
| standings_rows | snapshot_id, team_id, position, played, wins, draws, losses, goal_difference, points |
| players | id, display_name, photo_url, active |
| squad_memberships | id, player_id, season_label, shirt_number, position |
| contact_messages | id, name, email, subject, message, status, created_at |
| users | id, normalized_email (unique), password_hash, role (admin), active, created_at |
| sessions | id, user_id, token_hash (unique), expires_at, revoked_at |
| account_tokens | id, user_id, purpose (reset_password), token_hash (unique), expires_at, used_at |
| match_videos | id, match_id, uploaded_by, object_key (unique), title, content_type, size_bytes, status (pending/ready/failed), created_at, published_at |
| sync_runs | id, dataset (fixtures/standings), source_url, started_at, finished_at, status, inserted_count, updated_count, error_summary |

Use UUID primary keys and timezone-aware timestamps. Add created_at/updated_at where useful.
Use foreign keys for references. Add unique constraints for competition + source season,
snapshot + team, player + season, and shirt number + season when the number is supplied.
Validate different home/away teams and nonnegative scores; final matches need both scores.
Unplayed scores are null, not zero. Index match kickoff/competition and foreign keys used in reads.
matches.id remains stable across ETL updates and is used in public detail URLs.
match_videos.match_id references matches.id with ON DELETE RESTRICT; uploaded_by references
users.id with ON DELETE RESTRICT. Deactivate admin accounts instead of deleting provenance.
Require positive size_bytes, an allowed status and a unique server-generated object_key.
Index match_videos(match_id, status, created_at). Only ready videos are returned publicly.
Use unique hashed session/reset tokens, expiry times and foreign keys to users.
Never store plaintext passwords, bearer tokens, video bytes or expiring signed URLs in tables.

Original incremental migration proposal (v1 uses one initial migration for all 14 tables):
1. Seven league/ETL tables.
2. players and squad_memberships (nine total).
3. contact_messages (ten).
4. users, sessions and account_tokens (thirteen).
5. match_videos (fourteen); depends on matches and users.
Test upgrade from an empty database and from each previous migration.
Keep table creation in migrations, not server startup or ETL code.

MVP simplifications:
- One club squad, so squad memberships use a season label; separate seasons/competitions and
  competition entries are deferred until needed. Validate season labels against configured seasons.
- FLA is the only source, so configuration plus sync_runs replaces a data_sources table.
- Store official goal difference directly; the source table does not supply goals for/against.
- Keep public copy, honours and translations in frontend files.
- No news, chat, payments or public member registration. Admin match-highlight uploads are in scope.
- Login stays explicitly unavailable until authentication is implemented.

## Step 1 — minimal FastAPI server

Build: main.py, config.py, pyproject.toml and a non-secret .env.example.
Endpoint: GET /api/health returns a small status object.
Why: confirm Python server and routing before adding persistence.
Manual check: start Uvicorn, open /docs and /api/health.
Learning: a router maps an HTTP request to a Python function; configuration reads environment
variables. No real secrets belong in source control.

## Step 2 — PostgreSQL connection and league migration

Build: database.py, models.py, Alembic setup and the first migration.
Create only the seven league/ETL tables first: teams, competition_seasons, venues, matches,
standings_snapshots, standings_rows and sync_runs. Add squad/contact tables in their steps.
Why: establish one versioned schema before importing data.
Manual check: migrate an empty development database and inspect the tables/constraints;
verify duplicate source IDs are rejected.
Learning: SQLAlchemy models describe stored rows; Alembic migrations change the schema;
a database dependency opens/closes one session per API request.

## Step 3 — standings ETL, manually invoked

Build: etl config, fetch, parse_standings, load and a small command entry point.
Why first: the complete standings table is a bounded source and exercises most import mechanics.
Download with explicit timeout, bounded retries and a modest request rate.
Validate source access terms before unattended collection; use an official export/API if available.
Parse team IDs from links, not names. The inspected table had 14 teams, but do not permanently
hard-code that number across seasons. First three rank cells may use decorative graphics:
preserve source order and validate ranks. All-zero preseason rows are valid.
Publish teams and a complete snapshot in one transaction; skip unchanged snapshots.
Record failed syncs separately so a rollback does not erase the failure log.
Manual check: import twice without duplicate records; a malformed/missing table preserves
the previous snapshot. Use saved HTML fixtures for parser tests rather than live-site unit tests.

## Step 4 — fixtures/results ETL

Build: parse_fixtures and extend load/main.
Use stable FLA match IDs where available. Do not identify a match by kickoff time.
If IDs are absent, agree and test a competition/team/round/leg identity before importing.
Map local kickoff dates using Europe/Paris, including daylight saving.
Update changed scores, venues and kickoff times. Keep unknown statuses explicit.
Do not infer a final score from an elapsed date or cancel a match because it disappears.
Manual check: rerun idempotently, move a fixture without duplicating it, and apply a corrected result.
Learning: an upsert inserts new records or updates an existing record with the same source identity.

## Step 5 — league API and frontend integration

Build: routers/league.py, schemas/league.py, services/league.py and a small frontend API client.
Endpoints:
- GET /api/matches?team_id=...&competition_season_id=...&status=...
- GET /api/standings?competition_season_id=...
- GET /api/matches/{id}

Use bounded pagination for matches and deterministic ordering.
Return source URL and last successful sync time with results; return an explicit empty state
before the first import, not fictional scores. Home and League use the same endpoints.
Match detail responses include an empty videos list initially, then ready videos after step 9.
Replace mock m1/m2 IDs with stable database UUIDs in frontend links when switching to API data.
Unknown match IDs return 404. Test direct navigation and refresh at /matches/:id.
Manual check: compare API values with imported rows; verify frontend loading, error and empty states.
Learning: Pydantic schemas define the public response, services perform queries,
and routers handle HTTP. The browser never connects directly to PostgreSQL.

## Step 6 — squad API

Build: players/squad_memberships migration and squad router, schemas and service.
Endpoint: GET /api/players?season=2026/2027.
Seed verified club player data manually; FLA ETL does not overwrite squad records.
Manual check: shirt number/position filters display correctly and only the selected season appears.
Keep mock players explicitly marked until real data is supplied.

## Step 7 — contact storage

Build: contact_messages migration and contact router, schema and service.
Endpoint: POST /api/contact-messages.
Validate email, required fields and length limits. Add spam/rate protection before exposing publicly.
Return only an acknowledgement. No public inbox or message-list endpoint.
Manual check: a valid submission is stored, invalid data is rejected, and data is not publicly readable.
Storing a message and sending email are separate features; email notifications are deferred.

## Step 8 — admin authentication

Build: auth migration, routers/auth.py, schemas/auth.py, services/auth.py, dependencies.py.
Use Argon2id password hashes and random, revocable sessions stored as token hashes.
Send session tokens only in Secure, HttpOnly cookies; configure SameSite deliberately,
exact credentialed CORS origins and CSRF protection for mutations.
Create the first admin with a local management command; never provide public admin registration.
Endpoints: POST /api/auth/login, POST /api/auth/logout, GET /api/auth/me.
For password reset, add POST /api/auth/forgot-password and POST /api/auth/reset-password
when an HTTPS email provider is configured. Reset tokens expire and are consumed once.
Use generic reset responses, login throttling and invalidate sessions after password reset.
Hide unavailable Create account/reset actions until implemented.

Manual check: login/logout, session expiry/revocation, invalid credentials, CSRF rejection,
and 401/403 for anonymous/non-admin callers of every upload mutation.
Learning: authentication identifies the caller; authorization separately grants upload permission.

## Step 9 — match video uploads and playback

Build: match_videos migration, storage.py and video router/schema/service.
One match can have many videos. Admin authentication is required before enabling uploads.
Choose object storage, allowed file types, maximum size and delivery budget before this step.
Use a private bucket with short-lived signed upload/read URLs initially; only ready objects
get public playback URLs from the API. Do not store signed URLs in the database.

Endpoints:
- POST /api/admin/matches/{id}/videos/upload-url
- POST /api/admin/matches/{id}/videos/{video_id}/complete
- DELETE /api/admin/matches/{id}/videos/{video_id}
- GET /api/matches/{id} includes ready video metadata and playable URLs.

Flow:
1. Check admin permission and match existence; create pending metadata with a generated key.
2. Issue a short-lived upload authorization bound to that key and enforce size limits where
   supported by storage. Configure storage CORS for the frontend origin.
3. Browser uploads directly to storage, displaying progress and retry/error states.
4. Completion checks the video belongs to the route's match and authorized uploader,
   checks actual stored size/type, and validates the file container/codec before publication.
   Do not trust a client MIME label or extension. Initially support one browser-compatible
   format (MP4 with H.264/AAC); do not add a transcoding service to the MVP.
5. Mark ready atomically only after validation; repeated completion is safe.
6. Match page uses a native player with controls, no autoplay and no preload of full videos.
   Refresh expired playback URLs on demand; never expose pending/failed videos.
7. Failed/missing objects stay unpublished. Retry must use controlled keys; clean up stale
   pending records and orphaned objects with a documented retention rule.
8. Deletion hides the record first, then removes the object; failures remain retryable.

ETL must not update match_videos or delete referenced matches. A score correction or reschedule
must keep the same match UUID and its videos.

Manual check: upload/playback, reload, multiple videos per match, unauthorized uploads,
oversized/invalid files, interrupted upload, repeated completion, cross-match video IDs,
expired URLs, deletion retry, and an ETL correction preserving the video relationship.
Use an isolated test bucket; never make the ETL role able to upload/delete videos.

## Step 10 — schedule and deploy

Only after manual imports and parser tests pass:
- Put a cron-style GitHub Actions workflow in root .github/workflows/, with manual dispatch too.
- Start daily; agree additional post-match refresh frequency separately.
- Prevent concurrent runs using workflow concurrency and a PostgreSQL lock.
- Use a dedicated ETL database role, limited to league writes and sync logs.
- Store DATABASE_URL in scheduler/provider secrets. API role needs league reads, contact writes, auth/session operations and video metadata writes.
  Storage credentials belong to the API only; the ETL role cannot modify auth or videos.
- Add failure reporting, retention for snapshots/logs and last-sync visibility.
- Scheduled jobs may be delayed; public-repository schedules can disable after inactivity.
- Do not run cron inside a sleeping Render free API process.

Deployment proposal: frontend on Cloudflare Workers, FastAPI on Render, PostgreSQL on Neon.
Root domain serves the website; api.paris-chinois-fc.com serves FastAPI.
Configure exact CORS origins and HTTPS. Validate SSR runtime limits before frontend deployment.
Free-tier limits and domain-renewal costs are recorded in backend-design.md.

## Implementation boundary and remaining decisions

Admin authentication is in scope because uploads require it. Public member accounts remain
out of scope. Select storage limits/provider and reset-email delivery before their steps.
Confirm captions/subtitles needs before publishing spoken videos; do not invent transcripts.
No admin accounts, scheduler, storage bucket or upload backend have been created.
The initial migration creates the reserved authentication and video tables.

The frontend already has /matches/$id with match details and an empty highlights state.
The actual upload UI and playback integration are step 9 deliverables.

## Next implementation step

Frontend league queries use the read API. JWT registration/login/logout and owner-controlled
role grants are implemented. Select object storage before enabling video uploads. The current v1 stores no videos.

### Source identity decision

The inspected team cards expose no match identifier. V1 uses championship, source season,
home/away source team IDs, matchday and leg as the unique source key; kickoff time is
excluded. Rescheduling and score corrections preserve the internal UUID. A source edit
to opponent, round or leg requires manual reconciliation; do not silently remove old matches.
Friday cup cards are now included under their own competition-season record. Result orientation uses the club's
V/N/D marker; malformed or ambiguous results fail the import atomically.

## Authentication implementation update

Public registration creates only the user role. Player and admin roles are assigned through
`python -m app.auth.manage EMAIL ROLE` by the trusted database operator. JWTs use HttpOnly
cookies backed by revocable session hashes. See backend/README.md for setup, protection
dependencies, and email-verification/reset and distributed rate-limiting limitations.
