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
