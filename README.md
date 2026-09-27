# Paris Chinois FC frontend prototype

Six primary pages: Home, FLA League, Team, About Us, News / Media, Contact. Article details live under `/news/:id`. This is a frontend-only prototype; no accounts, emails, database or public publishing are configured.

## Replacing sample content

- Editorial images are mapped in `src/config/assets.ts`; replace imports with approved photography. The generated images are illustrative, not photographs of actual club members. `logo`, `playerPortraits`, `stadium`, and `sponsors` are explicit replacement slots. The red/gold shield and sponsor-free presentation are placeholders, not official artwork or endorsements.
- Sample teams, fixtures, standings, players and stories are in `src/data/`. Dates display in the `Europe/Paris` timezone. Replace with verified club information before publishing.
- The contact address, location and timeline are placeholders. The login and contact forms validate locally and display demo-only feedback; they do not send data or authenticate.

Built with React, TypeScript, TanStack Start, Vite and Tailwind CSS v4. Feature implementations live in `src/features/`; thin route declarations live in `src/routes/`.
