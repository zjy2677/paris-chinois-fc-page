# Backend proposal — discussion only

The current MVP scope and implementation order are in [backend-implementation-plan.md](backend-implementation-plan.md).
The expanded schema below is retained as design context, not the initial implementation target.

No backend implementation, migration, provider account, or deployment has been created.
Scope: Paris Chinois FC, not the separate chatbot learning project.

## Architecture

Browser -> React/TanStack frontend -> FastAPI -> PostgreSQL.
Scheduled Python ETL -> FLA source -> validation -> PostgreSQL (independent of HTTP requests).
Use SQLAlchemy for persistence, Pydantic for API contracts, and Alembic for schema migrations.
Keep routers thin, business rules in services, and database models separate from API schemas.
Start with one API and one database. No microservices, queues, or CMS required.

Public reads: fixtures, results, standings and squad. ETL owns league data; admin-only writes manage squad records.
Contact submission is public but validated and rate-limited; inbox reads are admin-only.
Admin authentication is required for planned highlight uploads. Public member registration is deferred.
A player profile does not require a login account.

## Proposed relational schema

All primary keys UUID unless stated otherwise. Mutable records have created_at and updated_at
as timestamptz. Foreign keys enforce relationships; archive historical records instead of
cascading deletes through seasons/results.

| Table | Main columns and purpose |
| --- | --- |
| teams | id, name, short_name, crest_url, is_our_club |
| competitions | id, name, format (7 or 11), division_label |
| seasons | id, label, starts_on, ends_on |
| competition_seasons | id, competition_id, season_id, win_points, draw_points, loss_points, standings_source |
| competition_teams | id, competition_season_id, team_id |
| venues | id, name, address, city, timezone (Europe/Paris by default) |
| matches | id, competition_season_id, home_entry_id, away_entry_id, venue_id, matchday, kickoff_at (nullable for TBD), status, home_score, away_score |
| standings_snapshots | id, competition_season_id, source_url, as_of, imported_by |
| standings_rows | snapshot_id, entry_id, position, played, wins, draws, losses, goal_difference, goals_for (nullable), goals_against (nullable), points |
| players | id, display_name, photo_url, active |
| squad_memberships | id, player_id, team_id, season_id, shirt_number, position |
| contact_messages | id, name, email, subject, message, status (new/read/closed), handled_by |
| match_videos | id, match_id, uploaded_by, object_key, title, content_type, size_bytes, status, created_at, published_at |
| users (when enabling auth) | id, normalized_email, password_hash, role (admin/member), active, email_verified_at |
| sessions (when enabling auth) | id, user_id, token_hash, expires_at, revoked_at |
| account_tokens (when enabling auth) | id, user_id, purpose (verify_email/reset_password), token_hash, expires_at, used_at |

Constraints:
- Unique (competition_id, season_id), unique competition entry per team/competition-season.
- Home and away entries must differ and belong to the match's competition-season:
  enforce using composite foreign keys, not only application validation.
- Final results require both nonnegative scores. Unplayed matches have null scores, never 0-0.
- Unique (team_id, season_id, player_id); unique shirt number per team/season when supplied.
- Unique standings entry and rank within a snapshot; all rows must match its competition-season.
- Normalized email is unique; store only password hashes and hashed session/reset tokens.
- Index fixtures by (competition_season_id, kickoff_at); sessions/tokens by token hash;
  contact inbox by (status, created_at). PostgreSQL does not automatically index all foreign keys.

## FLA ETL — confirmed source decision

User-selected sources:
- Fixtures/results: https://football-loisir-amateur.fr/teams/322
- Complete standings: https://football-loisir-amateur.fr/championships/14?season=2
- External identifiers: team 322, championship 14, season 2. Preserve these separately
  from local UUIDs and human-readable season labels.
A read-only fetch returned server-rendered content naming PARIS CHINOIS FC, Foot à 7,
Vendredi, 1ère division Elite, and dated fixtures with opponents and venues.
A read-only standings fetch also returned a server-rendered table with 14 team rows,
including a link to team 322. Columns: Pos, Équipe, Pts, J, G, N, P, Diff.
Team links supply stable IDs; do not join by display names, which vary between pages.
The first three positions have no numeric text in the fetched table; account for decorative
rank cells and preserve source row order. Confirm that mapping in parser fixtures.
All observed rows currently have zero games/points: this is valid pre-season data.
The table supplies goal difference, not separate goals for/against: keep those nullable;
do not invent them or derive them from goal difference alone.
A production extractor and stable API contract have not been implemented or verified.
Review published access terms and prefer an official API/export or permitted public-page import.

The ETL owns fixtures, results and official standings. FastAPI reads stored data;
page views must not fetch FLA on demand. No admin import UI is necessary for the initial slice.

Add:
- data_sources: id, name, base_url, team_external_id (322), championship_external_id (14),
  season_external_id (2), fixtures_url, standings_url, enabled.
- sync_runs: id, source_id, started_at, finished_at, status, parser_version,
  fetched_count, inserted_count, updated_count, error_summary.
- source_id, external_id, source_url, last_seen_at, last_synced_at on imported entities.
  Unique (source_id, external_id) for each entity type.
- source_id, sync_run_id, fetched_at, content_hash on standings_snapshots;
  retain source as_of only if actually supplied.
- Match status must support scheduled, postponed, cancelled, final and unknown;
  retain source status when no safe mapping exists.

Pipeline:
1. Fetch fixtures/results from the team URL and standings from the separate championship URL.
   Always preserve the explicit season=2 query parameter; change the source-season mapping
   deliberately on rollover. Verify both sources refer to the same competition-season.
2. Extract source IDs; do not use kickoff time as identity because fixtures can move.
   If stable fixture IDs are absent, agree a composite identity including competition-season,
   home/away entries and leg/round; quarantine ambiguous matches instead of duplicating.
3. Normalize dates with Europe/Paris DST rules, team IDs, venues, statuses and scores.
   A passed kickoff date is not proof a match is final.
4. Validate relationships, duplicate IDs, row completeness and score formats.
5. Acquire a database lock so overlapping runs do not publish concurrently.
6. Upsert matches/teams/venues, including corrections to old results.
   Publish a complete standings snapshot atomically; never publish a partial table.
   Skip unchanged snapshots by content hash.
7. Record success/failure and counts; retain last good data on network/parser failure.
   A missing row is not a deletion or cancellation.
8. Expose last successful sync time through the API and display stale-data status if needed.
   Cap retained snapshots/logs to protect the free database quota.

The scheduler uses a dedicated PostgreSQL role limited to imported league tables and sync logs.
Credentials live in scheduler secrets, never in frontend variables or logged connection strings.
Do not overwrite manually managed squad data. Do not recompute official points or ranks from
our club's matches alone.

Suggested initial cadence: daily, with additional refreshes after Friday games if needed.
Cadence is a proposal, not a configured schedule. Delayed score entry requires later rechecks.

For zero-cost scheduling, use a Python GitHub Actions scheduled workflow on standard runners
(subject to repository/account quotas), plus workflow_dispatch for recovery.
Public repo schedules can disable after 60 days without repository activity; runs can be delayed.
An OS crontab on an already available always-on machine is another option, but a sleeping
laptop is unreliable. Do not put cron inside Render's sleeping free web service.
Render managed cron has a minimum $1/month charge, so it is not free.
Nothing is scheduled yet.

## Content and images

Keep static About copy, honours and interface translations in frontend i18n for now.
Store stable codes for match status and player position; translate labels in the frontend.
Use translated-content tables only if editors later need to manage multilingual prose.
No news tables: that feature was removed.

Keep existing approved images as frontend assets. If uploads are introduced, store the files
in object storage and only their URL/object key in PostgreSQL. Render's local disk is ephemeral.
Avoid collecting birth dates, addresses or other player personal data without a concrete need.
Contact message retention and who can access the inbox must be agreed.

## Authentication and email

Recommend admin-only authentication first. No player/account coupling is needed for the public site.
For self-managed FastAPI auth, use Argon2id password hashes and secure HttpOnly cookies backed
by revocable sessions; protect state-changing requests against CSRF.
If a hosted auth service is chosen instead, use its subject identifier and do not keep a second
password store. Do not build both approaches.

Email delivery (password reset, email verification, contact notifications) is separate from
database storage and requires a provider. Render free blocks common SMTP ports, so use HTTPS
email APIs if needed. Storing a contact message is the first useful step; notification is optional.

## Hosting proposal

- Frontend: Cloudflare Workers, custom domain paris-chinois-fc.com.
  The existing TanStack Start/Nitro build already targets a Cloudflare worker.
  Build from frontend/. Do not upload only .output/public and assume SSR will work.
  Deployment configuration and runtime compatibility still require verification.
- API: Render free Python web service, root directory backend/, api.paris-chinois-fc.com.
  Later start with uvicorn app.main:app --host 0.0.0.0 --port $PORT.
- Database: Neon PostgreSQL in a European region close to the API.
  Only FastAPI receives DATABASE_URL; no database credentials belong in VITE_* variables.
- DNS: Cloudflare DNS, HTTPS on both hosts; redirect www to the canonical frontend host.
  Configure exact frontend CORS origins. Credentialed requests must not use wildcard CORS.
  If /api under the apex is desired, add an explicit reverse proxy later.

Free tier tradeoffs verified from provider sources:
- Cloudflare Workers Free: 100,000 dynamic requests/day, 10 ms CPU per invocation.
  Test SSR CPU use before committing to this plan; prerender public pages if necessary.
- Render: custom domains/TLS supported, 750 free service hours/month per workspace;
  sleeps after 15 minutes idle and can take about a minute to wake. No durable local disk.
  Free Render PostgreSQL expires after 30 days, so it is not the proposed database.
- Neon: free PostgreSQL with 0.5 GB storage/project and 100 CU-hours/month/project,
  scale-to-zero. Enough for a small text-based club dataset, subject to quotas.
- Alternative Supabase: free PostgreSQL, 500 MB database and integrated auth/storage,
  but free projects pause after one week of inactivity. Prefer it if managed auth/uploads
  become the priority rather than implementing those parts in FastAPI.
- Domain purchase/renewal is not free. Hosting can be zero-cost only within current quotas.
  Free tiers are a prototype/low-traffic compromise, not an always-on availability guarantee.

Sources:
- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/workers/configuration/routing/custom-domains/
- https://render.com/docs/free
- https://render.com/docs/custom-domains
- https://neon.com/blog/how-to-make-the-most-of-neons-free-plan
- https://neon.com/pricing
- https://supabase.com/pricing

## Decisions before coding

1. Admin-only authentication is planned for video uploads; member accounts are deferred.
2. Which scheduler and refresh cadence should run the confirmed FLA ETL?
3. Does Contact only store messages, or also email notifications?

Then implement one slice at a time: database connection and migrations, public fixtures API,
frontend integration, squad and standings, contact, then admin authentication and video uploads.
Follow the current 14-table migration sequence in backend-implementation-plan.md.

Additional sources:
- https://football-loisir-amateur.fr/teams/322
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://render.com/docs/cronjobs

- Standings source: https://football-loisir-amateur.fr/championships/14?season=2
