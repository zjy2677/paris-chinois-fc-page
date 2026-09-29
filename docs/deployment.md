# First deployment: Vercel + Render + Neon

## Architecture

Browser → Vercel (`paris-chinois-fc.com`) → `/api/*` CDN rewrite → Render FastAPI → Neon PostgreSQL.

The frontend is TanStack Start with SSR, not a static Vite SPA. Vercel must use
`frontend/` as its root and the TanStack Start preset. Nitro emits the function and
API rewrite under `.vercel/output/`. Do not set the output directory to `dist` and
do not add a catch-all rewrite to index.html.

The browser always calls its own `/api` origin. This keeps JWT cookies first-party
(HttpOnly, Secure, SameSite=Lax). Setting VITE_API_BASE_URL to an onrender.com host
would make authentication cross-site and break this cookie setup. API_ORIGIN is a
build-time setting: changing the Render address requires a new frontend deployment.

## 1. Neon

Create a project near Render's Frankfurt region. Use a dedicated production database;
never point test jobs at it. Save two connection strings privately:

- Pooled connection → Render `DATABASE_URL`.
- Direct connection → Render `DATABASE_MIGRATION_URL` and GitHub `ETL_DATABASE_URL`.

Keep `sslmode=require` (and any Neon-supplied channel-binding parameter). Standard
`postgresql://` strings are accepted and normalized to the installed psycopg driver.
Alembic uses the direct URL to avoid transaction-pool migration issues. The ETL uses
a direct connection because its import takes a PostgreSQL advisory lock.

## 2. Render

Create a Blueprint from repository-root `render.yaml`. Keep the service root at the
repository root: startup and ETL need both `backend/` and `etl/` available.

| Setting | Value |
| --- | --- |
| Plan / region | Free / Frankfurt |
| Python | 3.12.12 |
| Build | `pip install -r backend/requirements.lock && pip install --no-deps ./backend` |
| Start | `sh backend/start.sh` |
| Health check | `/api/health` |
| APP_ENV | `production` |
| DATABASE_URL | Neon pooled URL, secret |
| DATABASE_MIGRATION_URL | Neon direct URL, secret |
| JWT_SECRET | Blueprint-generated random value; retain across deployments |
| AUTH_COOKIE_SECURE | `true` |
| AUTH_TTL_SECONDS | `28800` |
| CONTACT_ENABLED | `false` |
| CORS_ORIGINS | JSON array of exact frontend HTTPS origins |

Example CORS_ORIGINS after choosing the actual Vercel project URL:

```json
["https://paris-chinois-fc.com", "https://www.paris-chinois-fc.com", "https://YOUR-PROJECT.vercel.app"]
```

Replace YOUR-PROJECT before saving. No trailing slashes or wildcard preview domains.
Unlisted previews can read public data but authentication mutations return 403.
For preview authentication, explicitly authorize that preview and preferably use a
separate test backend/database. Do not trust arbitrary *.vercel.app origins.

Render Free has no pre-deploy hook. `start.sh` validates configuration, applies
Alembic migrations, then starts one worker on `$PORT`. Failed migrations stop startup.
This is a first-deployment shortcut; use a dedicated migration step before scaling
beyond one instance. App import itself never migrates. `/api/health` is intentionally
DB-independent so repeated host health checks don't keep Neon's compute awake.
Manually check `/api/ready` after deployment for actual database connectivity.

## 3. Vercel

Import the GitHub repository. Root Directory: **frontend**. Framework: **TanStack Start**.
Node.js: **22.x**. Frozen Bun install/build commands are in `frontend/vercel.json`.
Keep the existing Bun lockfile; use Bun 1.3.14 or compatible.

| Environment variable | Value |
| --- | --- |
| API_ORIGIN | Actual `https://YOUR-SERVICE.onrender.com`, without `/api` |
| VITE_API_BASE_URL | Omit or leave empty |

Never put DATABASE_URL or JWT_SECRET in Vercel or any VITE_ variable. API_ORIGIN is
not a secret. Production builds reject a missing origin or a cross-site API base.
Set API_ORIGIN in both Production and any Preview environment you intend to use.

Verify the Vercel subdomain before adding the custom domain. Then add
`paris-chinois-fc.com` and `www.paris-chinois-fc.com` in Vercel, copy the exact DNS
records Vercel displays into your domain registrar, and choose a canonical domain
(the other redirects). Keep HTTPS enabled. Do not alter email/MX records.

## 4. Populate production data

An empty Neon DB receives the schema, not your local data. After Render successfully
migrates it, add the direct Neon URL as the GitHub **production environment** secret
`ETL_DATABASE_URL`, then manually run **Import FLA data** in Actions. Protect this
environment if approval before data imports is desired. The job validates TLS and
runs the existing transactional ETL; no JWT secret is required because it starts no
web server. It does not run schema migrations or create users.

GitHub Actions owns ETL execution; Render only serves the API and runs migrations.
The workflow is currently manual for first launch; no periodic schedule is active.
Enable a schedule only after the live import and source access have been verified.
The source season/team settings are in `etl/config.py`.

ETL imports fixtures and standings only. Existing local highlight links, users, and
player/editorial data do not migrate automatically. Transfer the reviewed match
highlight record explicitly after resolving the new production match UUID; never
reuse a development UUID or copy development sessions into production. Users should
register anew. Owner role grants run with the production database URL through
`python -m app.auth.manage EMAIL player` (or `admin`). Render Free has no interactive
shell: use your local backend environment with the production URL securely exported.

## Verification before announcing launch

1. Render `/api/health` and `/api/ready` return success.
2. Website `/api/matches` and `/api/standings` return imported FLA data, not HTML.
3. Directly open `/league`, `/team`, `/contact`, and a production `/matches/{id}` URL.
4. Register, refresh, log out, then log in on the HTTPS website. Confirm Secure,
   HttpOnly cookies, generic wrong-password feedback, and registration role `user`.
5. Check French/English/Chinese and a mobile viewport.
6. Confirm the known YouTube highlight in Chrome once transferred. Codex's embedded
   browser previously could not play it even though Chrome worked.

Do not migrate local test accounts or commit `.env`, `.vercel`, dumps, or build output.
Run tests only with a disposable database ending `_test`.

## Free-tier limits and remaining work

Render Free sleeps after 15 minutes without traffic, so a first visit may wait or
need a retry while the API wakes. Neon may also cold-start. These tiers cannot
promise instant responses. Vercel Hobby is restricted to eligible non-commercial
use; confirm that the club site's actual use qualifies. Domain registration is
separate from free hosting. Email verification is disabled; password-reset delivery and contact submissions
remain unavailable. Auth throttling is per-process; add a shared limiter before
multiple workers/instances, and verify client IP forwarding on the live proxy path.

References checked for this setup:
- https://vercel.com/kb/guide/deploy-a-tanstack-start-app-to-vercel
- https://vercel.com/docs/routing/rewrites
- https://render.com/docs/free
- https://render.com/docs/deploys
- https://render.com/docs/blueprint-spec
- https://neon.com/docs/connect/connection-pooling
- https://vercel.com/docs/plans/hobby

## Registration without email verification

No RESEND_API_KEY, EMAIL_FROM or PUBLIC_SITE_URL setting is required. Any previously
added email settings can be removed from Render. Keep JWT_SECRET and CORS_ORIGINS.
Deploy the profile migration with the backend first, then deploy the frontend.
Registration collects first name, last name, age, email and matching passwords,
and signs the member in immediately. Existing accounts can also sign in without
confirmation. Email ownership is not checked; password-reset email is unavailable.
After deployment, test registration, refresh, logout and login on the real site.
