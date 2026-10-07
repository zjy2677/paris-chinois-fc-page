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

## CI-aware authoring

- Write changes with the checks in `.github/workflows/` in mind, especially Ruff, Prettier, ESLint, TypeScript, tests, builds, and the single-head Alembic requirement. Format touched frontend files with the project formatter and keep Python changes compatible with the configured Ruff rules.
- Do not proactively duplicate the full CI pipeline locally. Leave the complete check suite to GitHub Actions unless the user explicitly asks for local validation or asks to diagnose a failing pipeline. Targeted checks needed to develop or confirm a specific risky change are still appropriate; report only checks that were actually run.
- Alembic migrations must preserve exactly one head. Before creating or editing a migration, inspect the current migration chain and set `down_revision` to the current head. Recheck the chain whenever target-branch migrations are incorporated.
- If another migration was added to the target branch after the feature migration was created, update an unmerged and unreleased feature migration to follow the new head, or add an explicit Alembic merge revision when existing migration history must remain immutable. Never rewrite a migration that has already been deployed.
- Treat pipeline failures as actionable. When asked to diagnose one, fix the underlying issue and run only the failed or directly related checks locally; let the pipeline perform the final complete verification.
