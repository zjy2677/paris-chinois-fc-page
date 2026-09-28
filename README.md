# Paris Chinois FC

Football club website with English, French and Chinese interfaces.

## Repository layout

- `frontend/`: existing React + TypeScript app, using TanStack Start, Vite and Tailwind CSS.
- `backend/`: FastAPI API, SQLAlchemy models, Alembic migrations and tests.
- `etl/`: manually runnable FLA extraction, validation and transactional imports.
- `docs/`: shared project documentation and photography credits.
- `.lovable/`: existing Lovable project association, retained at repository root.

## Frontend development

Run commands from `frontend/`:

```sh
cd frontend
bun run dev --host 0.0.0.0 --port 4173
```

Existing dependencies and the lockfile were moved with the app. For a fresh checkout,
install from that lockfile with `bun install --frozen-lockfile`.

Validation:

```sh
bunx tsc --noEmit
bun test tests/about.test.tsx tests/i18n.test.tsx
bun run build:dev
```

The active pages are Home, FLA League, Team, About Us and Contact.
Registration, JWT login and logout are connected. Contact submission and password-reset email remain unavailable.
Matches and standings are loaded from FastAPI; squad sample data remains in `frontend/src/data/`.
Images are mapped in `frontend/src/config/assets.ts`.
Source translations are in `frontend/src/i18n/locales/`.

## Deployment status

Nothing has been deployed as part of this reorganization. Configure future build services
with `frontend` as their root directory. The existing build includes TanStack Start SSR
and a Nitro Cloudflare worker; serving only its public asset folder is not equivalent to
deploying the app. Lovable editor/build compatibility with a nested app has not been verified.

## Backend planning

Start with [the minimal implementation plan](docs/backend-implementation-plan.md).
It supersedes the larger initial schema in [the design exploration](docs/backend-design.md).
Backend/ETL v1 is implemented locally. See [setup and validation commands](backend/README.md).
Matches and standings are connected to the frontend. Account authentication is implemented; video storage,
scheduling and deployment remain pending.

## Deployment

See [Vercel + Render + Neon setup](docs/deployment.md) for production environment variables, migrations, API proxy, data import, and launch checks.
