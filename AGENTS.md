<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

- Keep TanStack route files thin and put page implementations under `src/features/`; the fixed framework owns routing while feature modules remain replaceable.
- Keep illustrative fixtures, standings, players and news in `src/data/` with explicit types; the prototype stays coherent and API-ready without a backend.
- Centralize replaceable editorial images in `src/config/assets.ts`; approved club photography can swap in without changing page layouts.

## CI safety checks

- Before handing off or committing changes, run the CI checks affected by the work. For frontend changes, run from `frontend/`: `bun run format:check`, `bun run typecheck`, `bun run lint`, `bun run test`, and `bun run build`. For backend, ETL, or script changes, run the Ruff checks and relevant pytest suites using the same commands as `.github/workflows/ci.yml`. Do not claim a check passed if its runtime or dependencies were unavailable.
- After merging or updating from the target branch, rerun the affected checks; a previously green feature commit does not guarantee that the combined migration graph or formatting still passes.
- Alembic migrations must leave exactly one head. Before creating a migration, determine the current head and set `down_revision` to it. After adding a migration or incorporating target-branch migrations, run `python scripts/check_alembic_heads.py` and verify `python -m alembic -c backend/alembic.ini upgrade head` against a disposable database. Never deploy or hand off a branch with multiple heads.
- If another migration was added to the target branch after the feature migration was created, update an unmerged/unreleased feature migration to follow the new head, or add an explicit Alembic merge revision when existing migration history must remain immutable. Never rewrite a migration that has already been deployed.
- Formatting and lint are required checks, not optional cleanup. Run the formatter on files reported by `format:check`, then rerun both formatting and lint before handoff.
